import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import QApplication

import app
import core


class AppInteractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])

    def test_mixed_media_selection_keeps_folders_and_supported_videos(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root) / 'shoot day'
            folder.mkdir()
            video = Path(root) / 'clip with spaces.MP4'
            video.touch()
            unsupported = Path(root) / 'notes.txt'
            unsupported.touch()
            folders, videos = app.partition_media_paths(
                [folder, video, unsupported, video, Path(root) / 'missing.mov'])
            self.assertEqual(folders, [str(folder.resolve())])
            self.assertEqual(videos, [str(video.resolve())])

    def test_add_media_uses_native_windows_multi_file_picker(self):
        class Target:
            scanning = False
            batch = None

            def __init__(self):
                self.paths = None

            def scan_media_paths(self, paths):
                self.paths = paths

        target = Target()
        with patch('app.QFileDialog.getOpenFileNames',
                   return_value=(['one.mp4', 'two.mov'], 'Video files')) as picker:
            app.Window.add_media(target)
        picker.assert_called_once()
        self.assertEqual(target.paths, ['one.mp4', 'two.mov'])

    def test_library_picker_keeps_multiple_checked_results(self):
        records = [
            {'id': 'one', 'source': 'one.mp4', 'duration': 2, 'segments': [{'text': 'river'}]},
            {'id': 'two', 'source': 'two.mp4', 'duration': 3, 'segments': [{'text': 'river town'}]},
        ]
        picker = app.LibraryPickerDialog(records)
        try:
            for index in range(picker.list.topLevelItemCount()):
                picker.list.topLevelItem(index).setCheckState(0, app.Qt.Checked)
            self.assertEqual([value['id'] for value in picker.selected_records()], ['one', 'two'])
            self.assertEqual(picker.add_button.text(), 'Add 2 selected')
            picker.search.setText('town')
            self.assertEqual(len(picker.selected_records()), 2)
            picker.search.setText('missing words')
            self.assertEqual(len(picker.selected_records()), 2)
            picker.search.clear()
            self.assertEqual(len(picker.selected_records()), 2)
        finally:
            picker.close()

    def test_search_highlights_each_case_insensitive_occurrence(self):
        self.assertEqual(
            app.highlighted_parts('Person walks past another PERSON.', 'person'),
            [('Person', True), (' walks past another ', False), ('PERSON', True), ('.', False)])
        self.assertEqual(app.highlighted_parts('No visual match', 'chair'), [('No visual match', False)])

    def test_search_counts_direct_prefix_and_embedded_occurrences(self):
        direct, embedded = app.query_hit_counts(
            ['archer archers ARCHERING', 'researcher and field-rearcher'], 'archer')
        self.assertEqual((direct, embedded), (3, 2))
        self.assertEqual(
            app.classified_highlighted_parts('archers researchers', 'archer'),
            [('archer', 'direct'), ('s rese', None), ('archer', 'embedded'), ('s', None)])

    def test_windows_reveals_the_exact_source_file(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / 'clip with spaces.mp4'
            source.touch()
            with patch.object(app.sys, 'platform', 'win32'), patch('app.subprocess.Popen') as launch:
                app.reveal_path(source)
            launch.assert_called_once_with(
                ['explorer.exe', '/select,' + os.path.normpath(str(source))])

    def test_processing_modes_are_explicit_and_ai_sampling_is_one_to_thirty(self):
        folders = [{'files': [{'duration': 60, 'selected': True, 'status': 'Ready'}]}]
        with patch('core.model_ready', return_value=True), patch('core.visual_model_ready', return_value=True):
            dialog = app.OptionsDialog(dict(core.DEFAULTS), folders, None)
        try:
            self.assertTrue(dialog.fixed_mode.isChecked())
            self.assertTrue(dialog.interval.isEnabled())
            dialog.scene_mode.click()
            self.application.processEvents()
            self.assertEqual(dialog.values()['mode'], 'scene')
            self.assertFalse(dialog.interval.isEnabled())
            dialog.fixed_mode.click()
            self.application.processEvents()
            self.assertEqual(dialog.values()['mode'], 'interval')
            self.assertTrue(dialog.interval.isEnabled())
            self.assertTrue(dialog.visual_interval_box.isHidden())
            dialog.interval.setValue(.5)
            self.assertEqual(dialog.values()['visual_interval'], .5)
            dialog.interval.setValue(30)
            self.assertEqual(dialog.values()['visual_interval'], 30)
        finally:
            dialog.close()

    def test_collections_crud_and_export(self):
        state = {'collections': [{'id': 'all', 'name': 'All footage', 'builtin': True, 'video_ids': []}]}
        coll = core.create_collection(state, 'Interviews')
        self.assertEqual(coll['name'], 'Interviews')
        self.assertIn(coll, state['collections'])

        core.add_to_collection(state, coll['id'], ['v1', 'v2', 'v1'])
        self.assertEqual(core.collection_video_ids(state, coll['id']), {'v1', 'v2'})

        core.remove_from_collection(state, coll['id'], ['v1'])
        self.assertEqual(core.collection_video_ids(state, coll['id']), {'v2'})

        core.rename_collection(state, coll['id'], 'Deep Interviews')
        self.assertEqual(coll['name'], 'Deep Interviews')

        # Test export
        with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as dest_dir:
            f1 = Path(src_dir) / 'interview1.mp4'
            f1.write_bytes(b'video content')
            results = [{'id': 'v2', 'source': str(f1), 'duration': 10}]
            copied, skipped, errors = core.export_collection(state, coll['id'], dest_dir, results=results)
            self.assertEqual(copied, 1)
            self.assertTrue((Path(dest_dir) / 'interview1.mp4').is_file())

        core.delete_collection(state, coll['id'])
        self.assertEqual(len(state['collections']), 1)

    def test_results_page_table_population_and_collection_filter(self):
        state = {'collections': [
            {'id': 'all', 'name': 'All footage', 'builtin': True, 'video_ids': []},
            {'id': 'c1', 'name': 'Interviews', 'video_ids': ['vid1']}
        ]}
        class FakeWindow(app.QWidget):
            def __init__(self):
                super().__init__()
                self.state = state

        win = FakeWindow()
        page = app.ResultsPage(win)
        try:
            records = [
                {'id': 'vid1', 'source': 'clip1.mp4', 'duration': 42, 'segments': [{'text': 'hello world'}]},
                {'id': 'vid2', 'source': 'clip2.mp4', 'duration': 18, 'segments': [{'text': 'river story'}]},
            ]
            page.set_records(records)
            self.assertEqual(page.tree.topLevelItemCount(), 2)

            page.set_active_collection('c1')
            self.assertEqual(page.tree.topLevelItemCount(), 1)

            page.set_active_collection('all')
            self.assertEqual(page.tree.topLevelItemCount(), 2)

            page.search.setText('river')
            self.assertEqual(page.tree.topLevelItemCount(), 1)
        finally:
            page.close()


if __name__ == '__main__':
    unittest.main()
