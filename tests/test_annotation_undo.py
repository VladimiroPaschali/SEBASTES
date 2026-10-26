"""Exercise real image-click handlers and Ctrl+Z against isolated databases."""
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from uuid import uuid4

import test_project_setup as setup
import numpy as np
from PySide6.QtCore import QPointF, QSettings, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtCore import QEvent
from PySide6.QtTest import QTest
from dbConnection import dbConnection
import MainWindow as main
import annotationundo


class StereoFixture:
    calData = dict(cameraMatrixL=np.array([[200., 0., 150.], [0., 200., 100.], [0., 0., 1.]]),
                   cameraMatrixR=np.array([[200., 0., 150.], [0., 200., 100.], [0., 0., 1.]]),
                   distCoeffsL=np.zeros(5), distCoeffsR=np.zeros(5), R=np.eye(3), T=np.array([-10., 0., 0.]))

    def triangulatePoint(self, left, right):
        points = np.vstack((left, np.full((1, left.shape[1]), 1000.0)))
        return points, points.copy()

    def projectPoint(self, points, camera):
        return points[:2]

    def computeError(self, *args):
        return 0.0

    def computeMatch(self, first, second, point):
        return True, point + np.array([[-5.0, 0.0]]), 0.0


class AnnotationUndoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        setup.ProjectSetupTests.setUpClass()

    def setUp(self):
        self.fixture = setup.ProjectSetupTests()
        self.fixture.setUp()
        self.errors = []
        settings = QSettings(str(setup.ROOT / '.venv/tmp' / ('test-' + uuid4().hex + '.ini')), QSettings.IniFormat)
        oldDirectory = os.getcwd()
        os.chdir(setup.ROOT / 'application')
        try:
            with patch.object(main.SEBASTES, 'createMissingDBFiles'), \
                    patch.object(main.QFile, 'exists', return_value=True), \
                    patch.object(main.dbConnection, 'dbConnection', return_value=self.fixture.parent.appDB), \
                    patch.object(main, 'QSettings', return_value=settings):
                self.window = main.SEBASTES()
        finally:
            os.chdir(oldDirectory)
        self.window.showError = lambda: self.errors.append(__import__('traceback').format_exc())
        self.window.dataDB = dbConnection(':memory:', '', '', label=uuid4().hex, driver='QSQLITE')
        self.window.dataDB.dbOpen()
        schema = (setup.ROOT / 'application/schema/Project.db.sql').read_text()
        for statement in schema.split(';'):
            if statement.strip():
                self.window.dataDB.dbExec(statement)
        window = self.window
        window.activeProject = "Diver's project"
        window.deployment = "Diver's deployment"
        window.annotator = 'Test annotator'
        window.currentTarget = 0
        window.settings = {'CollectMetadata': 'No'}
        window.leftImageFrames = [0, 1]
        window.imageSlider.setMaximum(1)
        window.imageSlider.setValue(0)
        window.measurementBox.clear()
        window.measurementBox.addItem('length')
        window.frameCommentDlg = type('Comments', (), {'showComment': lambda *args: None})()
        window.speciesList = ['Fish']
        window.spcColors = [[255, 0, 0]]
        window.spcButtons[0].setText('Fish')
        window.spcButtons[0].setStyleSheet('background-color: rgb(255, 0, 0);')
        window.spcButtons[0].setChecked(True)
        window.computeMatchBox.setChecked(False)
        window.stereoOnlyCheckBox.setChecked(False)
        window.gridCheck.setChecked(False)
        window.showDataCheck.setChecked(False)
        window.measureBtn.setChecked(False)
        window.recordBtn.setEnabled(True)
        window.recordBtn.setChecked(True)
        window.stereoComp = StereoFixture()
        window.mode = 'stereo'
        window.noLoad = False
        window.nameMeasurement = lambda *args: 'Fish 1'
        for view in (window.gvLeft, window.gvRight):
            view.setImageFromCvImage(np.zeros((200, 300, 3), dtype=np.uint8))
        self.fixture.app.processEvents()
        window.measurementsDock.setDeployment(window.dataDB, window.deployment)

    def tearDown(self):
        self.window.noLoad = True
        self.window.dataDB.dbClose()
        self.window.dataDB = None
        self.window.deleteLater()
        self.fixture.app.processEvents()
        self.fixture.tearDown()
        self.assertEqual(self.errors, [])

    def click(self, right=False, shift=False, x=60, y=60):
        view = self.window.gvRight if right else self.window.gvLeft
        modifiers = Qt.ShiftModifier if shift else Qt.NoModifier
        with patch.object(main.QGuiApplication, 'queryKeyboardModifiers', return_value=modifiers):
            self.window.imageClick(view, QPointF(x, y), Qt.LeftButton, modifiers, [])

    def count(self, table):
        return int(self.window.dataDB.dbQuery('SELECT COUNT(*) FROM ' + table).first()[0])

    def undoKey(self):
        event = QKeyEvent(QEvent.KeyPress, Qt.Key_Z, Qt.ControlModifier)
        self.window._SEBASTES__keyPressEvent(self.window.gvLeft, event)

    def test_plain_clicks_undo_in_reverse_order(self):
        self.click()
        self.click(x=90)
        self.assertEqual(self.count('targets'), 2)
        self.undoKey()
        self.assertEqual(self.count('targets'), 1)
        self.assertEqual(len(self.window.pointMarks), 1)
        self.undoKey()
        self.assertEqual(self.count('targets'), 0)
        self.assertEqual(self.count('points'), 0)
        self.assertEqual(len(self.window.pointMarks), 0)
        self.undoKey()
        self.assertEqual(self.count('targets'), 0)

    def test_each_manual_stereo_click_can_be_undone_and_repeated(self):
        self.click(shift=True)
        self.assertEqual(self.window.fishStep, 1)
        self.undoKey()
        self.assertEqual(self.window.fishStep, 0)
        self.assertEqual(len(self.window.pairPoints), 0)
        self.click(shift=True)
        self.click(right=True, x=55)
        self.assertEqual(self.window.fishStep, 2)
        self.assertEqual(self.count('targets'), 1)
        self.undoKey()
        self.assertEqual(self.window.fishStep, 1)
        self.assertEqual(self.count('targets'), 0)
        self.assertEqual(len(self.window.pairPoints), 1)
        self.click(right=True, x=55)
        self.click(x=130)
        self.assertEqual(self.window.fishStep, 3)
        self.undoKey()
        self.assertEqual(self.window.fishStep, 2)
        self.assertEqual(self.window.fishLines, {})
        self.click(x=130)
        self.click(right=True, x=125)
        self.assertEqual(self.count('lines'), 1)
        self.assertEqual(self.window.fishStep, 0)
        self.undoKey()
        self.assertEqual(self.count('lines'), 0)
        self.assertEqual(self.window.fishStep, 3)
        self.assertIn(self.window.gvLeft, self.window.fishLines)
        self.click(right=True, x=120)
        self.assertEqual(self.count('lines'), 1)
        self.assertEqual(self.window.fishStep, 0)
        for _ in range(4):
            self.undoKey()
        self.assertEqual(self.count('targets'), 0)
        self.assertEqual(self.count('points'), 0)
        self.assertEqual(self.count('lines'), 0)
        self.assertEqual(len(self.window.pointMarks), 0)

    def test_auto_match_undo_restores_tail_then_removes_head_pair(self):
        self.window.computeMatchBox.setChecked(True)
        self.click(shift=True)
        self.assertEqual(self.window.fishStep, 2)
        self.assertEqual(len(self.window.pointMarks), 2)
        self.click(x=130)
        self.assertEqual(self.count('lines'), 1)
        self.undoKey()
        self.assertEqual(self.count('lines'), 0)
        self.assertEqual(self.window.fishStep, 2)
        self.undoKey()
        self.assertEqual(self.count('targets'), 0)
        self.assertEqual(self.window.fishStep, 0)

    def test_read_only_and_separate_edits_are_preserved(self):
        self.click()
        self.window.recordBtn.setChecked(False)
        self.undoKey()
        self.assertEqual(self.count('targets'), 1)
        self.window.recordBtn.setChecked(True)
        self.window.dataDB.dbExec("UPDATE targets SET comment='A later edit'")
        self.undoKey()
        self.assertEqual(self.count('targets'), 1)
        self.assertEqual(self.window.markUndoHistory, [])

    def test_other_frames_are_preserved_and_mismatched_history_is_discarded(self):
        self.click()
        self.window.dataDB.dbExec("INSERT INTO targets (PROJECT, DEPLOYMENT_ID, FRAME_NUMBER, TARGET_NUMBER) "
                                 "VALUES ('Other project', 'Other deployment', 0, 1)")
        self.undoKey()
        self.assertEqual(self.count('targets'), 1)
        self.click()
        self.window.imageSlider.blockSignals(True)
        self.window.imageSlider.setValue(1)
        self.undoKey()
        self.assertEqual(self.count('targets'), 2)
        self.assertEqual(self.window.markUndoHistory, [])

    def test_ctrl_z_keeps_native_text_undo_and_works_from_image_focus(self):
        self.click()
        self.window.show()
        self.window.activateWindow()
        self.window.frameBox.setFocus()
        self.window.frameBox.setText('')
        QTest.keyClicks(self.window.frameBox, '123')
        self.fixture.app.processEvents()
        QTest.keyClick(self.window.frameBox, Qt.Key_Z, Qt.ControlModifier)
        self.assertEqual(self.window.frameBox.text(), '')
        self.assertEqual(self.count('targets'), 1)
        self.window.gvLeft.setFocus()
        self.fixture.app.processEvents()
        QTest.keyClick(self.window.gvLeft, Qt.Key_Z, Qt.ControlModifier)
        self.assertEqual(self.count('targets'), 0)

    def test_undo_preserves_grid_zoom_and_unsaved_metadata(self):
        grid = self.window.gvLeft.addDimensionLine(QPointF(0, 100), QPointF(300, 100), taillength=0)
        self.window.metadataLineEdits[0].setText('Unsaved metadata')
        self.window.gvLeft.zoomToPoint(QPointF(80, 80), 2)
        zoom = self.window.gvLeft.transform()
        self.click()
        self.undoKey()
        self.assertIsNotNone(grid.scene())
        self.assertEqual(self.window.metadataLineEdits[0].text(), 'Unsaved metadata')
        self.assertEqual(self.window.gvLeft.transform(), zoom)

    def test_failed_restore_keeps_database_and_history(self):
        self.click()
        self.click(x=90)
        original = annotationundo.execute

        def failRestore(db, statement, values=()):
            if statement.startswith('INSERT INTO points'):
                raise RuntimeError('Simulated undo failure')
            return original(db, statement, values)

        with patch.object(annotationundo, 'execute', side_effect=failRestore):
            self.undoKey()
        self.assertEqual(self.count('targets'), 2)
        self.assertEqual(self.count('points'), 2)
        self.assertEqual(len(self.window.markUndoHistory), 2)
        self.assertEqual(len(self.errors), 1)
        self.errors.clear()
        self.undoKey()
        self.assertEqual(self.count('targets'), 1)


if __name__ == '__main__':
    unittest.main()
