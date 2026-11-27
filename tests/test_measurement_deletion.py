"""Delete table rows against real SQLite data and the rendered stereo lines."""
import unittest
from unittest.mock import patch

import test_annotation_undo as annotation_fixture
import measurementsdock
from dbConnection import execute, sqlQuote
from measurementsdock import FRAME, LENGTH, MEASUREMENT_ROLE, NAME, SPECIES
from PySide6.QtCore import QItemSelectionModel, Qt
from PySide6.QtWidgets import QMessageBox


class MeasurementDeletionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        annotation_fixture.AnnotationUndoTests.setUpClass()

    setUp = annotation_fixture.AnnotationUndoTests.setUp
    tearDown = annotation_fixture.AnnotationUndoTests.tearDown
    click = annotation_fixture.AnnotationUndoTests.click
    count = annotation_fixture.AnnotationUndoTests.count

    def measuredFish(self):
        self.window.computeMatchBox.setChecked(True)
        self.click(shift=True)
        self.click(x=130)
        self.window.measurementsDock.refresh()

    def selectMeasurement(self, name):
        dock = self.window.measurementsDock
        for row in range(dock.table.rowCount()):
            if dock.table.item(row, NAME).text() == name:
                dock.table.setCurrentCell(row, NAME)
                dock.table.selectRow(row)
                return
        self.fail('Measurement not found: ' + name)

    def test_sorted_row_deletes_only_its_measurement_and_both_stereo_lines(self):
        self.measuredFish()
        self.window.dataDB.dbExec("UPDATE lines SET name='Zulu'")
        self.measuredFish()
        self.window.dataDB.dbExec("UPDATE lines SET name='Alpha' WHERE target_number=2")
        dep = sqlQuote(self.window.deployment)
        self.window.dataDB.dbExec("INSERT INTO lines (deployment_id,frame_number,target_number,line_label,name) "
            "VALUES ('" + dep + "',0,2,'width','Width'), ('" + dep + "',1,2,'length','Later'), "
            "('Other deployment',0,2,'length','Other')")
        dock = self.window.measurementsDock
        dock.refresh()
        dock.table.sortItems(NAME, Qt.SortOrder.AscendingOrder)
        self.selectMeasurement('Alpha')
        self.assertTrue(dock.deleteAction.isEnabled())
        self.assertEqual(len(self.window.lineMarks), 4)
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes):
            dock.deleteButton.click()
        remaining = list(self.window.dataDB.dbQuery('SELECT name FROM lines ORDER BY name'))
        self.assertEqual(remaining, [['Later'], ['Other'], ['Width'], ['Zulu']])
        self.assertEqual(self.count('targets'), 2)
        self.assertEqual(self.count('points'), 2)
        self.assertEqual(len(self.window.pointMarks), 4)
        self.assertEqual(len(self.window.lineMarks), 2)
        self.assertTrue(all(info[0] == 1 for info in self.window.lineMarks.values()))
        self.assertEqual(dock.table.rowCount(), 3)
        self.assertEqual(self.window.markUndoHistory, [])
        self.assertFalse(dock.deleteAction.isEnabled())

    def test_cancel_keeps_measurement_and_rendered_lines(self):
        self.measuredFish()
        dock = self.window.measurementsDock
        dock.table.selectRow(0)
        dock.table.setCurrentCell(0, NAME)
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.No):
            dock.deleteButton.click()
        self.assertEqual(self.count('lines'), 1)
        self.assertEqual(len(self.window.lineMarks), 2)

    def test_last_measurement_removes_points_labels_and_target(self):
        self.measuredFish()
        window = self.window
        marks = list(window.pointMarks) + list(window.lineMarks)
        window.linkData = [0, 1]
        window.linkBtn.setChecked(True)
        window.measurementsDock.table.setCurrentCell(0, NAME)
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes):
            window.measurementsDock.deleteButton.click()
        for table in ('lines', 'points', 'targets'):
            self.assertEqual(self.count(table), 0)
        self.assertEqual(window.pointMarks, {})
        self.assertEqual(window.lineMarks, {})
        self.assertTrue(all(mark.scene() is None for mark in marks))
        self.assertEqual(window.currentTarget, 0)
        self.assertFalse(window.pairedTarget)
        self.assertEqual(window.linkData, [])
        self.assertEqual(window.measurementsDock.table.rowCount(), 0)

    def test_failed_target_deletion_rolls_back_the_whole_batch(self):
        self.measuredFish()
        self.measuredFish()
        window = self.window
        window.measurementsDock.table.selectAll()
        window.dataDB.dbExec("CREATE TRIGGER fail_delete BEFORE DELETE ON targets WHEN OLD.target_number=2 "
                             "BEGIN SELECT RAISE(ABORT, 'Deletion failed'); END")
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes), \
                patch.object(window, 'showError') as error:
            window.measurementsDock.deleteButton.click()
        error.assert_called_once()
        for table in ('lines', 'points', 'targets'):
            self.assertEqual(self.count(table), 2)
        self.assertEqual(len(window.pointMarks), 4)
        self.assertEqual(len(window.lineMarks), 4)

    def test_nonadjacent_rows_delete_together_from_context_menu(self):
        self.measuredFish()
        self.measuredFish()
        window = self.window
        dep = sqlQuote(window.deployment)
        window.dataDB.dbExec("UPDATE lines SET name='Alpha' WHERE target_number=1")
        window.dataDB.dbExec("UPDATE lines SET name='Keep' WHERE target_number=2")
        window.dataDB.dbExec("INSERT INTO targets (deployment_id,frame_number,target_number) "
                             "VALUES ('" + dep + "',1,1)")
        window.dataDB.dbExec("INSERT INTO lines (deployment_id,frame_number,target_number,line_label,name) "
                             "VALUES ('" + dep + "',0,2,'width','Zulu'), ('" + dep + "',1,1,'length','Beta')")
        dock = window.measurementsDock
        dock.refresh()
        dock.table.sortItems(NAME, Qt.SortOrder.AscendingOrder)
        table = dock.table
        flags = QItemSelectionModel.SelectionFlag
        for row in (0, 1, 3):
            table.selectionModel().select(table.model().index(row, NAME), flags.Select | flags.Rows)
        self.assertFalse(dock.linkAction.isEnabled())
        self.assertEqual(dock.deleteAction.text(), 'Delete measurements')
        position = table.visualItemRect(table.item(1, NAME)).center()
        with patch.object(measurementsdock, 'QMenu') as menu, \
                patch.object(table, 'itemAt', return_value=table.item(1, NAME)), \
                patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes) as confirm:
            menu.return_value.exec.side_effect = lambda *_: dock.deleteAction.trigger()
            dock.showContextMenu(position)
        confirm.assert_called_once()
        self.assertIn('3 selected', confirm.call_args.args[2])
        self.assertEqual(list(window.dataDB.dbQuery('SELECT name FROM lines')), [['Keep']])
        self.assertEqual(self.count('targets'), 1)
        self.assertEqual(self.count('points'), 1)
        self.assertEqual(len(window.lineMarks), 2)
        self.assertEqual(len(window.pointMarks), 2)

    def test_read_only_and_marking_in_progress_cannot_delete(self):
        self.measuredFish()
        dock = self.window.measurementsDock
        dock.table.setCurrentCell(0, NAME)
        rowid = int(dock.table.item(0, NAME).data(Qt.ItemDataRole.UserRole))
        self.window.recordBtn.setChecked(False)
        self.assertFalse(dock.deleteAction.isEnabled())
        with patch.object(QMessageBox, 'question') as confirm:
            self.window.deleteMeasurements([rowid])
            self.window.recordBtn.setChecked(True)
            self.click(shift=True)
            self.window.deleteMeasurements([rowid])
            confirm.assert_not_called()
        self.assertEqual(self.count('lines'), 1)
        self.assertEqual(self.window.fishStep, 2)

    def test_marker_selects_length_for_the_exact_frame_and_target(self):
        self.measuredFish()
        window = self.window
        dock = window.measurementsDock
        db = window.dataDB.db
        execute(db, "UPDATE lines SET name='sargus 1'")
        execute(db, """INSERT INTO lines(deployment_id, frame_number, target_number, line_label, name, length,
                                        LX1, LY1, LX2, LY2, RX1, RY1, RX2, RY2)
            SELECT deployment_id, frame_number, target_number, 'width', name, 2,
                   LX1, LY1, LX2, LY2, RX1, RY1, RX2, RY2 FROM lines""")
        execute(db, """INSERT INTO lines(deployment_id, frame_number, target_number, line_label, name, length)
            VALUES(?, 1, 1, 'length', 'sargus 1', 20)""", (window.deployment,))
        dock.refresh()
        dock.table.sortItems(FRAME, Qt.SortOrder.DescendingOrder)
        navigation = []
        dock.goToTarget.connect(lambda *args: navigation.append(args))

        for recording in (True, False):
            window.recordBtn.setChecked(recording)
            if not recording:
                window.showAnnotations()
            mark = next(mark for mark, (_, view) in window.pointMarks.items() if view is window.gvLeft)
            self.assertEqual(window.gvLeft.filterSelectedItems([mark]), [mark])
            window.imageClick(window.gvLeft, mark.markItem.pos(), Qt.RightButton, None, [mark])
            index, = dock.visibleSelectedRows()
            self.assertEqual(dock.observationAt(index.row()), (0, 1))
            self.assertEqual(index.data(MEASUREMENT_ROLE), 'length')
        self.assertEqual(navigation, [])

    def test_filters_combine_and_keep_hidden_rows_out_of_actions(self):
        dock = self.window.measurementsDock
        db = self.window.dataDB.db
        dep = self.window.deployment
        data = [(10, 1, 'Sargus', 'sargus 2', 12.5),
                (12, 1, 'Sargus', 'sargus 1', 12.5),
                (15, 1, 'Salpa', 'sargus 3', 12.5),
                (18, 1, 'Sargus', 'sargus 4', 25),
                (19, 1, 'Sargus', 'fish 5', 12.5)]
        for frame, target, species, name, length in data:
            execute(db, 'INSERT INTO targets(deployment_id, frame_number, target_number, species_group) VALUES(?,?,?,?)',
                    (dep, frame, target, species))
            execute(db, 'INSERT INTO lines(deployment_id, frame_number, target_number, name, length) VALUES(?,?,?,?,?)',
                    (dep, frame, target, name, length))
        dock.refresh()
        table = dock.table
        self.assertEqual([table.horizontalHeaderItem(column).text() for column in range(table.columnCount())],
                         ['obs_id', 'Species', 'Length (cm)', 'Frame'])

        for column, value in [(NAME, 'SARGUS'), (SPECIES, 'Sarg'), (LENGTH, '12,5'), (FRAME, '10-18')]:
            dock.columnFilters[column].setText(value)
        table.sortItems(NAME, Qt.SortOrder.DescendingOrder)
        table.selectAll()
        self.assertEqual([table.item(index.row(), NAME).text() for index in dock.visibleSelectedRows()],
                         ['sargus 2', 'sargus 1'])
        dock.columnFilters[FRAME].setText('12')
        dock.selectTarget(12, 1)
        index, = dock.visibleSelectedRows()
        self.assertEqual(table.item(index.row(), NAME).text(), 'sargus 1')
        dock.selectTarget(10, 1)
        self.assertFalse(dock.visibleSelectedRows())
        self.assertFalse(dock.deleteAction.isEnabled())


if __name__ == '__main__':
    unittest.main()
