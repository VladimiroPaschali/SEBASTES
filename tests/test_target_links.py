"""Exercise legacy links, cross-frame identity, and linking through Measurements."""
import unittest
from unittest.mock import patch

import test_annotation_undo as fixture
import targetlinks
from dbConnection import execute
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QMessageBox
from measurementsdock import FRAME, NAME, SPECIES


class TargetLinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.AnnotationUndoTests.setUpClass()

    def setUp(self):
        fixture.AnnotationUndoTests.setUp(self)
        self.db = self.window.dataDB.db
        self.dep = self.window.deployment
        self.dock = self.window.measurementsDock

    tearDown = fixture.AnnotationUndoTests.tearDown
    click = fixture.AnnotationUndoTests.click

    def add_fish(self, frame, target, name, parent=None):
        execute(self.db, 'INSERT INTO targets(deployment_id,frame_number,target_number,target_link) VALUES(?,?,?,?)',
                (self.dep, frame, target, parent))
        execute(self.db, 'INSERT INTO lines(deployment_id,frame_number,target_number,name,line_label) VALUES(?,?,?,?,?)',
                (self.dep, frame, target, name, 'length'))

    def rows(self, sql):
        query = execute(self.db, sql)
        result = []
        while query.next():
            result.append(tuple(None if query.isNull(i) else query.value(i) for i in range(query.record().count())))
        return result

    def test_existing_sargus_sequence_migrates_once(self):
        execute(self.db, 'ALTER TABLE targets DROP COLUMN target_link_frame')
        execute(self.db, 'ALTER TABLE targets DROP COLUMN fish_name')
        for frame in (63, 64, 65):
            self.add_fish(frame, 1, f'sargus {frame-62}', None if frame == 63 else 1)
        self.add_fish(64, 2, 'another fish')
        for _ in range(2):
            targetlinks.migrate(self.db, self.dep, range(100))
        self.assertEqual(self.rows('SELECT frame_number,target_link_frame,fish_name FROM targets ORDER BY frame_number,target_number'),
                         [(63, None, 'sargus 1'), (64, 63, 'sargus 1'), (64, None, None), (65, 64, 'sargus 1')])
        self.assertEqual(self.rows('SELECT name FROM lines ORDER BY rowid'), [('sargus 1',)]*3 + [('another fish',)])

    def test_merge_in_reverse_and_insert_in_gap_then_disconnect(self):
        for frame, target in [(63, 1), (109, 5), (80, 3), (80, 4)]:
            self.add_fish(frame, target, f'fish {frame}-{target}')
        link = lambda a, b: targetlinks.link(self.db, self.dep, a, b)
        link((109, 5), (63, 1))
        link((63, 1), (80, 3))
        with self.assertRaises(ValueError):
            link((109, 5), (80, 4))
        self.assertEqual(self.rows('SELECT target_link_frame,target_link FROM targets ORDER BY rowid'),
                         [(None,None), (80,3), (63,1), (None,None)])
        self.assertEqual(self.rows('SELECT name FROM lines ORDER BY rowid'), [('fish 109-5',)]*3 + [('fish 80-4',)])
        targetlinks.set_parent(self.db, self.dep, (109, 5), (None,None))
        targetlinks.rename(self.db, self.dep, (63, 1), "Diver's fish")
        self.assertEqual(self.rows('SELECT name FROM lines ORDER BY rowid'),
                         [("Diver's fish",), ('fish 109-5',), ("Diver's fish",), ('fish 80-4',)])

    def test_table_links_and_renames_across_sampled_frames(self):
        window = self.window
        self.add_fish(0, 1, 'First')
        self.add_fish(20, 3, 'Second')
        window.leftImageFrames = [0, 20]
        self.dock.refresh()
        table = self.dock.table
        table.setCurrentCell(0, NAME)
        self.dock.linkButton.click()
        self.assertEqual(window.linkData, [0, 1])
        with patch.object(window, 'writeFrameData'), patch.object(window, 'readImage'), patch.object(window, 'reloadData'):
            self.dock.rowClicked(1, FRAME)
        self.assertFalse(window.linkBtn.isChecked())
        self.assertEqual(self.rows('SELECT target_link_frame, target_link FROM targets WHERE frame_number=20'), [(0, 1)])
        table.item(1, NAME).setText('Renamed')
        self.assertEqual(self.rows('SELECT name FROM lines'), [('Renamed',), ('Renamed',)])
        self.assertEqual(table.item(0, NAME).text(), 'Renamed')
        with patch.object(fixture.main.QInputDialog, 'getText', side_effect=AssertionError('Asked for a linked name')):
            name = fixture.main.SEBASTES.nameMeasurement(window, 3, 'length')
            self.assertEqual(name, 'Renamed')

    def test_species_warning_is_updated_when_link_copies_an_id(self):
        self.add_fish(0, 1, 'Salpa 1')
        self.add_fish(1, 1, 'sargus 1')
        execute(self.db, "UPDATE targets SET species_group='salpa' WHERE frame_number=0")
        execute(self.db, "UPDATE targets SET species_group='Sargus' WHERE frame_number=1")
        self.dock.refresh()
        table = self.dock.table
        self.assertTrue(table.item(0, SPECIES).icon().isNull())
        self.assertTrue(table.item(1, SPECIES).icon().isNull())

        targetlinks.link(self.db, self.dep, (0, 1), (1, 1))
        self.dock.refresh()
        self.assertTrue(table.item(0, SPECIES).icon().isNull())
        mismatch = table.item(1, SPECIES)
        self.assertFalse(mismatch.icon().isNull())
        self.assertIn('Sargus', mismatch.toolTip())
        self.assertIn('Salpa 1', mismatch.toolTip())

        table.item(1, NAME).setText('Dive 1')
        self.assertTrue(table.item(1, SPECIES).icon().isNull())

    def test_new_point_links_after_jump_and_escape_cancels(self):
        window = self.window
        self.click()
        window.linkBtn.setEnabled(True)
        window.linkBtn.trigger()
        self.assertEqual(window.linkData, [0, 1])
        window.leftImageFrames = [0, 50]
        with patch.object(window, 'writeFrameData'), patch.object(window, 'readImage'):
            window.goToIndex(1)
        self.assertEqual(window.linkData, [0, 1])
        window.spcButtons[0].setChecked(True)
        self.click()
        self.assertEqual(self.rows('SELECT frame_number,target_link_frame,target_link FROM targets ORDER BY frame_number'),
                         [(0, None, None), (50, 0, 1)])
        self.assertEqual(self.rows('SELECT fish_name FROM targets'), [('Fish 1',), ('Fish 1',)])
        window.linkBtn.trigger()
        QTest.keyClick(window, Qt.Key_Escape)
        self.assertFalse(window.linkBtn.isChecked())
        self.assertEqual(window.linkData, [])

    def test_new_stereo_measurement_inherits_name_when_marked(self):
        window = self.window
        self.add_fish(0, 3, 'sargus 1')
        self.dock.refresh()
        self.dock.table.setCurrentCell(0, NAME)
        self.dock.linkButton.click()
        window.leftImageFrames = [0, 99]
        with patch.object(window, 'writeFrameData'), patch.object(window, 'readImage'), patch.object(window, 'reloadData'):
            window.goToIndex(1)
        del window.nameMeasurement  # Use the real naming dialog path from the application.
        window.spcButtons[0].setChecked(True)
        window.computeMatchBox.setChecked(True)
        with patch.object(fixture.main.QInputDialog, 'getText', side_effect=AssertionError('Unexpected name prompt')):
            self.click(shift=True)
            self.click(x=130)
        self.assertEqual(self.rows('SELECT frame_number,name FROM lines ORDER BY frame_number'), [(0,'sargus 1'), (99,'sargus 1')])
        self.assertEqual(self.rows('SELECT target_link_frame,target_link FROM targets WHERE frame_number=99'), [(0,3)])

    def test_link_uses_latest_fish_of_active_species_unless_a_source_is_selected(self):
        window = self.window
        first, second = window.spcButtons[:2]
        second.setText('Other fish')
        second.setStyleSheet('background-color: rgb(0, 255, 0);')
        window.speciesList.append(second.text())
        window.spcColors.append([0, 255, 0])
        window.linkBtn.setEnabled(True)
        self.click(x=40)
        self.click(x=70)
        first.setChecked(False)
        second.setChecked(True)
        self.click(x=100)
        second.setChecked(False)
        first.setChecked(True)
        execute(self.db, "UPDATE targets SET time_stamp = '2026-11-01 10:00:00'")

        window.showMeasurement(0, 1)
        window.linkBtn.trigger()
        self.assertEqual(window.linkData, [0, 1])
        window.linkBtn.trigger()

        with patch.object(window, 'writeFrameData'), patch.object(window, 'readImage'):
            window.goToIndex(1)
            window.goToIndex(0)
            window.linkBtn.trigger()
            self.assertEqual(window.linkData, [0, 2])
            window.goToIndex(1)
        self.click()
        self.assertEqual(self.rows('SELECT target_link_frame, target_link FROM targets WHERE frame_number=1'), [(0, 2)])

    def test_deleted_observation_id_is_reused_after_all_its_observations_are_gone(self):
        for number in range(1, 12):
            self.add_fish(0, number, f'sargus {number}')
        execute(self.db, "INSERT INTO targets(deployment_id, frame_number, target_number) VALUES(?, 1, 1)", (self.dep,))
        execute(self.db, "UPDATE targets SET species_group='sargus'")
        targetlinks.link(self.db, self.dep, (0, 10), (1, 1))

        def proposed_id():
            return targetlinks.next_name(self.db, self.dep, (0, 1))

        self.assertEqual(proposed_id(), 'sargus 12')
        rowid, = self.rows("SELECT rowid FROM lines WHERE name='sargus 10'")[0]
        with patch.object(QMessageBox, 'question', return_value=QMessageBox.Yes):
            self.window.deleteMeasurements([rowid])
        self.assertEqual(proposed_id(), 'sargus 12')

        targetlinks.delete_target(self.window.dataDB, self.dep, (1, 1))
        self.assertEqual(proposed_id(), 'sargus 10')
        self.assertEqual(self.rows("SELECT name FROM lines WHERE target_number=11"), [('sargus 11',)])

    def test_link_can_start_after_returning_to_the_only_fish_in_a_frame(self):
        window = self.window
        window.leftImageFrames = [1, 2]
        window.linkBtn.setEnabled(True)
        del window.nameMeasurement
        window.computeMatchBox.setChecked(True)
        with patch.object(fixture.main.QInputDialog, 'getText', return_value=('sargus 1', True)) as naming:
            self.click(shift=True)
            self.click(x=130)
            with patch.object(window, 'writeFrameData'), patch.object(window, 'readImage'):
                window.goToIndex(1)
                window.goToIndex(0)
                window.showViews()
                window.show()
                window.activateWindow()
                window.gvLeft.setFocus()
                self.fixture.app.processEvents()
                QTest.keyClick(window.gvLeft, Qt.Key_X, Qt.ShiftModifier)
                self.assertEqual(window.linkData, [1, 1])
                window.goToIndex(1)
            window.computeMatchBox.setChecked(False)
            self.click(shift=True)
            self.assertEqual(window.fishStep, 1)
            self.assertEqual(len(window.pairPoints), 1)
            self.click(right=True, x=55)
            self.click(x=130)
            self.click(right=True, x=125)
        naming.assert_called_once()
        self.assertEqual(self.rows('SELECT frame_number, name FROM lines ORDER BY frame_number'),
                         [(1, 'sargus 1'), (2, 'sargus 1')])
        self.assertEqual(self.rows('SELECT target_link_frame, target_link FROM targets WHERE frame_number=2'),
                         [(1, 1)])
