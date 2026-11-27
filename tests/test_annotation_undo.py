"""Exercise real image-click handlers and Ctrl+Z against isolated databases."""
import os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from uuid import uuid4

import test_project_setup as setup
import numpy as np
from PySide6.QtCore import QPoint, QPointF, QSettings, Qt
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
        self.fixture.app.removeEventFilter(self.window)
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

    def test_saved_observation_id_appears_above_both_segments(self):
        window = self.window
        window.labelCheck.setChecked(True)
        window.computeMatchBox.setChecked(True)
        del window.nameMeasurement
        with patch.object(main.QInputDialog, 'getText', return_value=('sargus 1', True)):
            self.click(shift=True, x=150)
            self.click(x=65, y=105)

        def assertLabels(obsId):
            self.assertEqual(len(window.lineMarks), 2)
            for line, (_, view, _) in window.lineMarks.items():
                label, = line.labels
                self.assertTrue(label.isVisible())
                self.assertEqual(label.text(), obsId)
                viewport = view.viewportTransform()
                bounds = label.deviceTransform(viewport).mapRect(label.boundingRect())
                midpoint = viewport.map(line.getLine().center())
                self.assertAlmostEqual(bounds.center().x(), midpoint.x())
                self.assertLess(bounds.bottom(), midpoint.y())
            self.assertTrue(all(not label.isVisible() for mark in window.pointMarks for label in mark.labels))

        assertLabels('sargus 1')
        table = window.measurementsDock.table
        self.assertEqual(table.horizontalHeaderItem(0).text(), 'obs_id')
        self.assertGreater(float(table.item(0, 2).text()), 0)
        table.item(0, 0).setText('sargus 2')
        assertLabels('sargus 2')
        window.clearMarks()
        window.reloadData(annotationsOnly=True)
        assertLabels('sargus 2')
        window.recordBtn.setChecked(False)
        window.showAnnotations()
        assertLabels('sargus 2')
        window.labelCheck.setChecked(False)
        self.assertTrue(all(not label.isVisible() for line in window.lineMarks for label in line.labels))

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

    def preparePan(self, right=False):
        self.window.showViews()
        self.window.show()
        self.window.activateWindow()
        view = self.window.gvRight if right else self.window.gvLeft
        view.setFocus()
        self.fixture.app.processEvents()
        view.zoomToPoint(QPointF(150, 100), 12)
        return view, view.viewport().rect().center()

    def test_space_drag_pans_without_creating_marks_or_undo_events(self):
        for right in (False, True):
            view, start = self.preparePan(right)
            initial = QPointF(view.centerPoint)
            QTest.keyPress(view, Qt.Key_Space)
            self.assertTrue(self.window.spacePanActive)
            self.assertEqual(view.cursor().shape(), Qt.OpenHandCursor)
            QTest.mousePress(view.viewport(), Qt.LeftButton, Qt.NoModifier, start)
            self.assertEqual(view.cursor().shape(), Qt.ClosedHandCursor)
            QTest.mouseMove(view.viewport(), start + QPoint(35, 20))
            self.assertNotEqual(view.centerPoint, initial)
            QTest.mouseRelease(view.viewport(), Qt.LeftButton, Qt.NoModifier, start + QPoint(35, 20))
            self.assertEqual(view.cursor().shape(), Qt.OpenHandCursor)
            QTest.keyRelease(view, Qt.Key_Space)
            self.assertFalse(view.panning)
            self.assertEqual(view.cursor().shape(), view.defaultCursor)
        self.assertEqual(self.count('targets'), 0)
        self.assertEqual(self.window.markUndoHistory, [])

    def test_releasing_space_before_mouse_keeps_drag_safe_then_resumes_marking(self):
        view, start = self.preparePan()
        QTest.keyPress(view, Qt.Key_Space)
        QTest.mousePress(view.viewport(), Qt.LeftButton, Qt.NoModifier, start)
        QTest.keyRelease(view, Qt.Key_Space)
        self.assertTrue(view.panDragging)
        self.assertEqual(view.cursor().shape(), Qt.ClosedHandCursor)
        QTest.mouseMove(view.viewport(), start + QPoint(30, 10))
        QTest.mouseRelease(view.viewport(), Qt.LeftButton, Qt.NoModifier, start + QPoint(30, 10))
        self.assertFalse(view.panDragging)
        self.assertEqual(self.count('targets'), 0)
        QTest.mouseClick(view.viewport(), Qt.LeftButton, Qt.NoModifier, start)
        self.assertEqual(self.count('targets'), 1)

    def test_pan_preserves_pending_fish_and_shift_click_history(self):
        self.click(shift=True)
        view, start = self.preparePan()
        QTest.keyPress(view, Qt.Key_Space)
        QTest.mousePress(view.viewport(), Qt.LeftButton, Qt.NoModifier, start)
        QTest.mouseMove(view.viewport(), start + QPoint(20, 10))
        QTest.mouseRelease(view.viewport(), Qt.LeftButton, Qt.NoModifier, start + QPoint(20, 10))
        QTest.keyRelease(view, Qt.Key_Space)
        self.assertEqual(self.window.fishStep, 1)
        self.assertEqual(len(self.window.pairPoints), 1)
        self.assertEqual(len(self.window.markUndoHistory), 1)
        self.assertEqual(self.count('targets'), 0)

    def test_space_in_text_field_keeps_normal_typing(self):
        self.preparePan()
        self.window.frameBox.setFocus()
        self.window.frameBox.setText('')
        QTest.keyClicks(self.window.frameBox, 'a b')
        self.assertEqual(self.window.frameBox.text(), 'a b')
        self.assertFalse(self.window.spacePanActive)
        self.assertFalse(self.window.gvLeft.panning)

    def test_space_pan_cleans_up_on_focus_loss_and_window_deactivation(self):
        view, start = self.preparePan()
        QTest.keyPress(view, Qt.Key_Space)
        self.window.frameBox.setFocus()
        self.fixture.app.processEvents()
        self.assertFalse(self.window.spacePanActive)
        self.assertFalse(view.panning)
        QTest.keyRelease(self.window.frameBox, Qt.Key_Space)
        view.setFocus()
        QTest.keyPress(view, Qt.Key_Space)
        QTest.mousePress(view.viewport(), Qt.LeftButton, Qt.NoModifier, start)
        self.fixture.app.sendEvent(self.window, QEvent(QEvent.WindowDeactivate))
        self.assertFalse(self.window.spacePanActive)
        self.assertFalse(view.panDragging)
        QTest.mouseRelease(view.viewport(), Qt.LeftButton, Qt.NoModifier, start)
        QTest.keyRelease(view, Qt.Key_Space)
        self.assertEqual(self.count('targets'), 0)

    def test_space_keeps_play_shortcut_outside_record(self):
        view, _ = self.preparePan()
        self.window.recordBtn.setChecked(False)
        self.window.playBtn.setEnabled(True)
        activations = []
        self.window.playBtn.clicked.connect(lambda: activations.append(self.window.playBtn.isChecked()))
        self.fixture.app.processEvents()
        QTest.keyClick(view, Qt.Key_Space)
        self.assertEqual(activations, [True])
        self.assertFalse(view.panning)
        self.window.stopPlay()

    def test_navigation_preserves_each_camera_view_even_after_a_missing_frame(self):
        window = self.window
        window.videoMode = True
        window.LPath, window.RPath = 'left/', 'right/'
        window.leftImageDict = {0: (None, 'left.mp4'), 1: (None, 'left.mp4')}
        window.rightImageDict = {0: (None, 'right.mp4'), 1: (None, 'right.mp4')}
        window.videoSources = {
            path: SimpleNamespace(fps=30, getFrame=lambda frame: np.full((200, 300, 3), frame, dtype=np.uint8))
            for path in (window.LPath, window.RPath)
        }
        left, _ = self.preparePan()
        right, _ = self.preparePan(right=True)
        left.centerOnPoint(QPointF(105, 75))
        right.centerOnPoint(QPointF(205, 130))
        expected = {view: view.viewState() for view in (left, right)}

        def assertSameView(view):
            transform, center, zoom = view.viewState()
            savedTransform, savedCenter, savedZoom = expected[view]
            self.assertEqual((transform, zoom), (savedTransform, savedZoom))
            # A layout change can resize the viewport. Qt scrolls it in whole pixels.
            displacement = transform.map(center) - transform.map(savedCenter)
            self.assertLessEqual(abs(displacement.x()), 1)
            self.assertLessEqual(abs(displacement.y()), 1)

        with patch.object(window, 'writeFrameData'):
            for index in (1, 0, 1, 0):
                window.goToIndex(index)
                self.fixture.app.processEvents()
                self.assertEqual(window.frameText(), str(index))
                for view in (left, right):
                    assertSameView(view)

            del window.rightImageDict[1]
            window.goToIndex(1)
            self.assertTrue(right.imgPixmap.isNull())
            window.goToIndex(0)
            self.assertFalse(right.imgPixmap.isNull())
            assertSameView(right)

    def test_space_double_click_fits_both_cameras(self):
        window = self.window
        window.playBtn.setEnabled(True)
        self.preparePan()
        views = (window.gvLeft, window.gvRight)
        window.fitCameraViews()
        fitted = [view.viewportTransform() for view in views]
        for recording in (True, False):
            window.recordBtn.setChecked(recording)
            for view in views:
                with self.subTest(recording=recording, camera=view.name):
                    for camera in views:
                        camera.zoomToPoint(QPointF(100, 80), 12)
                    self.assertNotEqual([camera.viewportTransform() for camera in views], fitted)
                    view.setFocus()
                    viewport = view.viewport()
                    point = viewport.rect().center()
                    QTest.keyPress(view, Qt.Key_Space)
                    QTest.mouseClick(viewport, Qt.LeftButton, Qt.NoModifier, point)
                    QTest.mouseDClick(viewport, Qt.LeftButton, Qt.NoModifier, point)
                    QTest.keyRelease(view, Qt.Key_Space)
                    QTest.mouseRelease(viewport, Qt.LeftButton, Qt.NoModifier, point)
                    self.assertEqual([camera.viewportTransform() for camera in views], fitted)
                    self.assertEqual([camera.zoomLevel for camera in views], [0, 0])
                    self.assertFalse(window.playBtn.isChecked())
                    self.assertEqual(self.count('targets'), 0)

    def test_alt_does_not_enable_panning(self):
        view, _ = self.preparePan()
        QTest.keyPress(view, Qt.Key_Alt)
        self.assertFalse(view.panning)
        self.assertNotEqual(view.cursor().shape(), Qt.OpenHandCursor)
        QTest.keyRelease(view, Qt.Key_Alt)
        self.assertFalse(view.panning)
        self.assertEqual(self.count('targets'), 0)


if __name__ == '__main__':
    unittest.main()
