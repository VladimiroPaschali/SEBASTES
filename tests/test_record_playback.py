"""Record playback saves the frame being left and pauses safely for annotation."""
import unittest
from unittest.mock import patch

import test_annotation_undo as annotation_fixture


class RecordPlaybackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        annotation_fixture.AnnotationUndoTests.setUpClass()

    tearDown = annotation_fixture.AnnotationUndoTests.tearDown
    click = annotation_fixture.AnnotationUndoTests.click
    count = annotation_fixture.AnnotationUndoTests.count

    def setUp(self):
        annotation_fixture.AnnotationUndoTests.setUp(self)
        self.window.toggleRecord()
        self.window.dtString = ''
        self.window.metadataCheckBox.setChecked(False)

    def test_record_play_saves_comment_before_changing_frame_and_stops_at_end(self):
        window = self.window
        self.assertTrue(window.playBtn.isEnabled())
        window.frameCommentDlg.commentBox.setPlainText("Fish's habitat")
        window.playBtn.click()
        self.assertTrue(window.playTimer.isActive())
        with patch.object(window, 'readImage', return_value='test-image'):
            window.moveSlider()
        self.assertEqual(window.frameText(), '1')
        self.assertEqual(list(window.dataDB.dbQuery('SELECT frame_number,comment,annotator FROM frames')),
                         [['0', "Fish's habitat", 'Test annotator']])
        window.moveSlider()
        self.assertFalse(window.playTimer.isActive())
        self.assertFalse(window.playBtn.isChecked())

    def test_marking_click_pauses_and_incomplete_stereo_target_blocks_play(self):
        window = self.window
        window.playBtn.click()
        self.click(shift=True)
        self.assertFalse(window.playTimer.isActive())
        self.assertFalse(window.playBtn.isChecked())
        self.assertEqual(window.fishStep, 1)
        window.playBtn.click()
        self.assertFalse(window.playBtn.isChecked())
        self.assertFalse(window.playTimer.isActive())
        window.moveSlider()
        self.assertEqual(window.frameText(), '0')
        self.assertEqual(len(window.pairPoints), 1)

    def test_species_stays_selected_across_frames_until_record_stops(self):
        window = self.window
        first, second = window.spcButtons[:2]
        first.setChecked(False)
        second.setText('Other fish')
        second.setStyleSheet('background-color: rgb(0, 255, 0);')
        window.spcColors.append([0, 255, 0])
        window.showSpeciesButtons(2)
        window.selectSpeciesByKey(1)
        self.click()
        with patch.object(window, 'readImage', return_value='test-image'):
            window.changeFrame(1)
            self.assertTrue(first.isChecked())
            self.click()
            window.selectSpeciesByKey(2)
            self.assertFalse(first.isChecked())
            window.changeFrame(0)
            self.assertTrue(second.isChecked())
            self.click(x=90)
        species = list(window.dataDB.dbQuery('SELECT frame_number,species_group FROM targets ORDER BY rowid'))
        self.assertEqual(species, [['0', 'Fish'], ['1', 'Fish'], ['0', 'Other fish']])
        window.recordBtn.trigger()
        self.assertFalse(second.isChecked())
        self.assertIsNone(window.spcInd)
        window.recordBtn.trigger()
        self.click(x=110)
        self.assertEqual(self.count('targets'), 3)

    def test_measure_target_pauses_play_and_timer_does_not_advance_during_measurement(self):
        window = self.window
        window.computeMatchBox.setChecked(True)
        self.click(shift=True)
        self.click(x=130)
        window.playBtn.click()
        self.assertTrue(window.playTimer.isActive())
        window.measureBtn.setChecked(True)
        window.toggleMeasure()
        self.assertTrue(window.measureBtn.isChecked())
        self.assertFalse(window.playTimer.isActive())
        window.moveSlider()
        window.playBtn.click()
        self.assertFalse(window.playTimer.isActive())
        self.assertEqual(window.frameText(), '0')
        self.assertEqual(self.count('lines'), 1)

    def test_read_only_playback_does_not_write_recorded_frames(self):
        window = self.window
        window.recordBtn.setChecked(False)
        window.toggleRecord()
        window.playBtn.click()
        with patch.object(window, 'readImage', return_value='test-image'):
            window.moveSlider()
        self.assertEqual(window.frameText(), '1')
        self.assertEqual(self.count('frames'), 0)
        window.stopPlay()


if __name__ == '__main__':
    unittest.main()
