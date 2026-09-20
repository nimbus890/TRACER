import os
import time
import unittest
from types import SimpleNamespace

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QApplication, QWidget, QFrame

import app
import core
from app import (
    format_time_hms, VideoControlBar, VideoContainer,
    LibraryPickerDialog, OptionsDialog, ProjectsPage
)
from timeline import final_cut_xml

class FakeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.state = {
            'collections': [{'id': 'c1', 'name': 'Test Coll', 'video_ids': ['vid1']}],
            'projects': [{'id': 'p1', 'name': 'Proj', 'folders': []}],
            'results': [{'id': 'vid1', 'source': 'clip1.mp4', 'duration': 42}],
            'settings': {}
        }
        self.save_timer = SimpleNamespace(start=lambda ms: None)
        self.remove_project_source = lambda: None
        self.pause_batch = lambda: None
        self.cancel_batch = lambda: None
        self.process_project = lambda: None
        self.batch = False
        self.scanning = False

class TestV21Features(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def test_format_time_hms(self):
        self.assertEqual(format_time_hms(0), '00:00:00')
        self.assertEqual(format_time_hms(734), '00:12:14')
        self.assertEqual(format_time_hms(2538), '00:42:18')
        self.assertEqual(format_time_hms(3661), '01:01:01')
        self.assertEqual(format_time_hms(-5), '00:00:00')

    def test_premiere_fcp_xml_export(self):
        seq = {
            'id': 'seq_1',
            'name': 'Premiere Test',
            'frame_rate': 24,
            'tracks': [{
                'id': 'trk_1',
                'name': 'Video 1',
                'type': 'video',
                'visible': True,
                'locked': False,
                'clips': [{
                    'id': 'clip_1',
                    'name': 'sample.mp4',
                    'source': r'C:\Media\sample.mp4',
                    'start': 0.0,
                    'end': 5.0,
                    'source_in': 10.0,
                    'source_out': 15.0
                }]
            }]
        }
        xml_out = final_cut_xml(seq)
        self.assertIn('<xmeml version="5">', xml_out)
        self.assertIn('<sequence id="sequence-seq_1">', xml_out)
        self.assertIn('<rate>', xml_out)
        self.assertIn('<timebase>24</timebase>', xml_out)
        self.assertIn('<clipitem id="clip-clip_1">', xml_out)
        self.assertIn('<duration>', xml_out)
        self.assertIn('<in>240</in>', xml_out)
        self.assertIn('<out>360</out>', xml_out)
        self.assertIn('<file id="file-', xml_out)
        self.assertIn('<pathurl>', xml_out)

    def test_video_control_bar_widgets_and_actions(self):
        bar = VideoControlBar()
        self.assertIsNotNone(bar.play_btn)
        self.assertIsNotNone(bar.time_label)
        self.assertIsNotNone(bar.scrubber)
        self.assertIsNotNone(bar.cc_btn)
        self.assertIsNotNone(bar.mute_btn)
        self.assertIsNotNone(bar.volume_slider)
        self.assertIsNotNone(bar.fullscreen_btn)
        self.assertIsNotNone(bar.vol_flyout)

        bar.set_duration(2538)
        bar.set_position(734)
        self.assertEqual(bar.time_label.text(), '00:12:14 / 00:42:18')
        self.assertEqual(bar.scrubber.value(), 734 * 1000)
        self.assertEqual(bar.scrubber.maximum(), 2538 * 1000)

        # Test volume flyout toggle
        bar.vol_btn.click()
        self.assertTrue(bar.vol_flyout.isVisible())
        bar.vol_btn.click()
        self.assertFalse(bar.vol_flyout.isVisible())

        # Test mute toggling
        bar.volume_slider.setValue(80)
        bar.toggle_mute()
        self.assertTrue(bar.is_muted)
        self.assertEqual(bar.volume_slider.value(), 0)
        bar.toggle_mute()
        self.assertFalse(bar.is_muted)
        self.assertEqual(bar.volume_slider.value(), 80)

        # Test CC toggle
        self.assertFalse(bar.captions_enabled)
        bar.cc_btn.click()
        self.assertTrue(bar.captions_enabled)

    def test_video_container_captions(self):
        container = VideoContainer()
        container.show()
        self.assertIsNotNone(container.subtitle_badge)
        self.assertFalse(container.subtitle_badge.isVisible())

        # With captions enabled
        container.set_subtitles('Hello Tracer 2.1')
        self.assertTrue(container.subtitle_badge.isVisible())
        self.assertEqual(container.subtitle_badge.text(), 'Hello Tracer 2.1')

        # Clear subtitles
        container.set_subtitles('')
        self.assertFalse(container.subtitle_badge.isVisible())

    def test_sequence_media_and_timeline_tools(self):
        win = FakeWindow()
        page = ProjectsPage(win)
        self.assertIsNotNone(page.list_mode_btn)
        self.assertIsNotNone(page.grid_mode_btn)
        self.assertTrue(page.grid_mode_btn.isChecked() or page.list_mode_btn.isChecked())

        # Test proxy compatibility
        page.media_view_toggle.setChecked(True)
        self.assertTrue(page.grid_mode_btn.isChecked())
        page.media_view_toggle.setChecked(False)
        self.assertTrue(page.list_mode_btn.isChecked())

        # Relink button moved to sequence media
        self.assertTrue(hasattr(page, 'relink_media_btn'))
        self.assertIsNotNone(page.relink_media_btn)
        self.assertEqual(page.relink_media_btn.text(), 'Relink')

        # No relink button in export panel
        self.assertFalse(hasattr(page, 'relink_offline_btn'))

        # Duplicate play button unified with sequence control bar
        self.assertEqual(page.sequence_play, page.sequence_preview_bar.play_btn)

        # Tools board structure
        self.assertTrue(hasattr(page, 'tools_board'))
        self.assertFalse(hasattr(page, 'tool_toggle_track_btn'))
        self.assertFalse(hasattr(page, 'tool_lock_track_btn'))

        # Zoom +/- buttons
        self.assertTrue(hasattr(page, 'zoom_out_btn'))
        self.assertTrue(hasattr(page, 'zoom_in_btn'))
        self.assertEqual(page.zoom_out_btn.text(), '−')
        self.assertEqual(page.zoom_in_btn.text(), '+')

        # Sequence preview container
        self.assertIsInstance(page.sequence_video_container, VideoContainer)
        self.assertIsInstance(page.sequence_preview_bar, VideoControlBar)

    def test_library_picker_overlay(self):
        parent = QWidget()
        parent.resize(1000, 700)
        dlg = LibraryPickerDialog([], parent=parent)
        self.assertTrue(dlg.windowFlags() & Qt.FramelessWindowHint)
        self.assertTrue(hasattr(dlg, 'card_frame'))
        self.assertIsNotNone(dlg.card_frame)
        self.assertEqual(dlg.card_frame.objectName(), 'libraryCard')
        self.assertTrue(hasattr(dlg, 'sizegrip'))
        self.assertIsInstance(dlg.sizegrip, app.QSizeGrip)

    def test_add_to_collection_dialog(self):
        state = {
            'collections': [
                {'id': 'all', 'name': 'All Footage', 'video_ids': ['v1', 'v2']},
                {'id': 'c_old', 'name': 'Old Coll', 'video_ids': ['v1'], 'updated_at': 100},
                {'id': 'c_new', 'name': 'Interviews', 'video_ids': ['v2'], 'updated_at': 200},
            ],
            'results': [
                {'id': 'v1', 'source': 'clip1.mp4'},
                {'id': 'v2', 'source': 'clip2.mp4'}
            ]
        }
        parent = QWidget()
        parent.resize(800, 600)
        dlg = app.AddToCollectionDialog(state, ['v1'], parent=parent)
        self.assertTrue(dlg.windowFlags() & Qt.FramelessWindowHint)
        self.assertEqual(dlg.objectName(), 'addToCollectionOverlay')
        self.assertIsNotNone(dlg.card)

        # First item should be + Create New Collection
        self.assertGreater(dlg.coll_list.count(), 1)
        first_item = dlg.coll_list.item(0)
        self.assertIn('+ Create New Collection', first_item.text())
        self.assertEqual(first_item.data(Qt.UserRole), '__new__')

        # Second item should be the most recently updated collection (Interviews)
        second_item = dlg.coll_list.item(1)
        self.assertIn('Interviews', second_item.text())
        self.assertEqual(second_item.data(Qt.UserRole), 'c_new')

        # Third item should be Old Coll
        third_item = dlg.coll_list.item(2)
        self.assertIn('Old Coll', third_item.text())
        self.assertEqual(third_item.data(Qt.UserRole), 'c_old')

        # Inline creation
        dlg.new_input.setText('B-Roll Selects')
        dlg.create_and_select()
        created = next((c for c in state['collections'] if c.get('name') == 'B-Roll Selects'), None)
        self.assertIsNotNone(created)
        self.assertEqual(dlg.selected_collection_id, created['id'])
        self.assertTrue(dlg.add_btn.isEnabled())

    def test_library_add_to_button_and_table_column(self):
        win = FakeWindow()
        page = app.LibraryPage(win)
        self.assertEqual(page.add_to_btn.text(), 'Add To ▾')
        self.assertEqual(page.tree.columnWidth(0), 48)

    def test_library_checkbox_click_toggle(self):
        win = FakeWindow()
        page = app.ResultsPage(win)
        page.set_records(win.state['results'])
        page.populate()
        self.assertGreater(page.tree.topLevelItemCount(), 0)
        item = page.tree.topLevelItem(0)
        self.assertEqual(item.checkState(0), Qt.Unchecked)
        self.assertNotIn('vid1', page.checked_ids)

        # Click on column 0 toggles to checked
        page.on_table_item_clicked(item, 0)
        self.assertEqual(item.checkState(0), Qt.Checked)
        self.assertIn('vid1', page.checked_ids)

        # Wait past the debounce period (0.25s) before clicking again
        time.sleep(0.3)

        # Second click on column 0 toggles to unchecked
        page.on_table_item_clicked(item, 0)
        self.assertEqual(item.checkState(0), Qt.Unchecked)
        self.assertNotIn('vid1', page.checked_ids)

    def test_preview_captions_sync(self):
        win = FakeWindow()
        win.show()
        page = app.ResultsPage(win)
        page.show()
        test_record = {
            'id': 'vid_cap',
            'source': 'sample.mp4',
            'duration': 60,
            'segments': [
                {'start': 2.0, 'end': 5.0, 'text': 'Intro dialogue'},
                {'start': 10.0, 'end': 15.0, 'text': 'Second line of speech'}
            ]
        }
        page.record = test_record
        segments = page._get_record_segments()
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0]['text'], 'Intro dialogue')

        # When captions toggled on
        page.control_bar.captions_enabled = True
        page.on_captions_toggled(True)

        # Position at 3000 ms = 3.0 sec (within first segment: 2.0 - 5.0)
        page.position(3000)
        self.assertEqual(page.video_container.subtitle_badge.text(), 'Intro dialogue')
        self.assertTrue(page.video_container.subtitle_badge.isVisible())

        # Position at 7000 ms = 7.0 sec (between segments: 5.0 - 10.0)
        page.position(7000)
        self.assertEqual(page.video_container.subtitle_badge.text(), '')
        self.assertFalse(page.video_container.subtitle_badge.isVisible())

        # Position at 12000 ms = 12.0 sec (within second segment: 10.0 - 15.0)
        page.position(12000)
        self.assertEqual(page.video_container.subtitle_badge.text(), 'Second line of speech')
        self.assertTrue(page.video_container.subtitle_badge.isVisible())

        # Turn captions off
        page.control_bar.captions_enabled = False
        page.on_captions_toggled(False)
        self.assertFalse(page.video_container.subtitle_badge.isVisible())


if __name__ == '__main__':
    unittest.main()
