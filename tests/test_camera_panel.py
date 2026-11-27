"""Exercise the detached stereo panel without replacing the camera viewers."""
import unittest
from unittest.mock import patch

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

import test_annotation_undo as fixture


class CameraPanelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.AnnotationUndoTests.setUpClass()

    setUp = fixture.AnnotationUndoTests.setUp
    tearDown = fixture.AnnotationUndoTests.tearDown
    click = fixture.AnnotationUndoTests.click

    def test_both_views_detach_support_marking_and_return_together(self):
        window = self.window
        left, right = window.gvLeft, window.gvRight
        window.showViews()
        window.show()
        window.linkBtn.setEnabled(True)
        self.click()
        window.cameraPanelAction.trigger()
        self.fixture.app.processEvents()

        self.assertTrue(window.cameraWindow.isVisible())
        self.assertIs(left.window(), window.cameraWindow)
        self.assertIs(right.window(), window.cameraWindow)
        self.assertTrue(window.cameraWindow.windowFlags() & Qt.WindowMaximizeButtonHint)
        self.assertIs(window.navBar.window(), window)
        self.assertIs(window.measurementsDock.window(), window)
        self.assertEqual(len(window.pointMarks), 1)

        QTest.keyClick(left, Qt.Key_Z, Qt.ControlModifier)
        self.assertEqual(len(window.pointMarks), 0)
        window.computeMatchBox.setChecked(True)
        del window.nameMeasurement
        with patch.object(fixture.main.QInputDialog, 'getText', return_value=('Fish 1', True)) as naming:
            self.click(shift=True)
            self.click(x=130)
        self.assertIs(naming.call_args.args[0], window.cameraWindow)
        window.computeMatchBox.setChecked(False)
        QTest.keyClick(left, Qt.Key_X, Qt.ShiftModifier)
        self.assertEqual(window.linkData, [0, 1])
        window.sampleRateEdit.setText('1')
        with patch.object(window, 'writeFrameData'), patch.object(window, 'readImage'):
            QTest.keyClick(window.cameraWindow, Qt.Key_Right)
        self.assertEqual(window.frameText(), '1')
        self.assertIn('Frame 1', window.cameraFrameStatus.text())
        self.click(shift=True)
        self.assertEqual(window.fishStep, 1)
        self.assertIn('RIGHT', window.cameraWindow.statusBar().currentMessage())

        window.cameraWindow.close()
        self.assertFalse(window.cameraWindow.isVisible())
        self.assertIs(left.window(), window)
        self.assertIs(right.window(), window)
        self.assertEqual(window.fishStep, 1)
        self.assertEqual(window.linkData, [0, 1])
        self.assertIs(window.imageStack.currentWidget(), window.viewPage)
