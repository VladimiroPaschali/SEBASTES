"""Apply and cancel image adjustments through the real stereo dialogs."""
import unittest

import test_annotation_undo as fixture


class ImageAdjustmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture.AnnotationUndoTests.setUpClass()

    setUp = fixture.AnnotationUndoTests.setUp
    tearDown = fixture.AnnotationUndoTests.tearDown

    def test_both_cameras_share_applied_settings_but_not_previews(self):
        window = self.window
        left, right = window.gvLeft, window.gvRight
        leftDialog, rightDialog = left.adjustmentDialog, right.adjustmentDialog
        for dialog in (leftDialog, rightDialog):
            self.addCleanup(dialog.close)

        originalRight = right.image.getParameters()
        originalPixel = right.imgPixmap.toImage().pixelColor(0, 0)
        window.adjLeftBtn.click()
        self.assertTrue(leftDialog.pbApplyBoth.isVisible())
        leftDialog.gbBrightnessContrast.setChecked(True)
        leftDialog.bcManual.click()
        leftDialog.brightnessSlider.setValue(22)
        leftDialog.contrastSlider.setValue(15)
        self.assertEqual(right.image.getParameters(), originalRight)
        leftDialog.pbApplyBoth.click()
        self.assertFalse(leftDialog.isVisible())
        self.assertEqual(left.image.getParameters(), right.image.getParameters())
        self.assertEqual(right.image.getParameters()['Brightness'], 22)
        self.assertEqual(right.imgPixmap.toImage().pixelColor(0, 0), left.imgPixmap.toImage().pixelColor(0, 0))
        self.assertNotEqual(right.imgPixmap.toImage().pixelColor(0, 0), originalPixel)

        window.adjRightBtn.click()
        self.assertEqual(rightDialog.brightnessSlider.value(), 22)
        rightDialog.brightnessSlider.setValue(-20)
        rightDialog.pbCancel.click()
        self.assertEqual(right.image.getParameters(), left.image.getParameters())

        window.adjRightBtn.click()
        rightDialog.brightnessSlider.setValue(32)
        rightDialog.pbApply.click()
        self.assertEqual(left.image.getParameters()['Brightness'], 22)
        self.assertEqual(right.image.getParameters()['Brightness'], 32)

        window.adjRightBtn.click()
        rightDialog.pbApplyBoth.click()
        self.assertEqual(left.image.getParameters(), right.image.getParameters())
        self.assertEqual(left.image.getParameters()['Brightness'], 32)
