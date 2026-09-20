import copy
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

    def test_results_page_visual_index_tab_and_seeking(self):
        win = app.QWidget()
        win.state = {'collections': [], 'projects': []}
        page = app.ResultsPage(win)
        try:
            record_with_vindex = {
                'id': 'v_ai_1',
                'source': 'sample_vision.mp4',
                'duration': 60,
                'visual_index': {
                    'frames': [
                        {
                            'time': 12.5,
                            'detections': [
                                {'label': 'person', 'confidence': 0.92, 'layer': 'foreground'},
                                {'label': 'car', 'confidence': 0.81, 'layer': 'background'}
                            ],
                            'keywords': {'foreground': ['person'], 'midground': [], 'background': ['car']},
                            'search_words': ['person', 'car']
                        },
                        {
                            'time': 35.0,
                            'detections': [
                                {'label': 'dog', 'confidence': 0.88, 'layer': 'midground'}
                            ],
                            'keywords': {'foreground': [], 'midground': ['dog'], 'background': []},
                            'search_words': ['dog']
                        }
                    ]
                }
            }
            page.select_record(record_with_vindex)
            self.assertEqual(page.visual_list.topLevelItemCount(), 2)
            first_item = page.visual_list.topLevelItem(0)
            self.assertIn('person', first_item.text(1))
            self.assertIn('[F]', first_item.text(1))

            # Test seeking
            self.assertEqual(first_item.data(0, app.Qt.UserRole), 12.5)
            with patch.object(page.player, 'setPosition') as mock_set_pos:
                page.seek_visual_moment(first_item)
                mock_set_pos.assert_called_once_with(12500)

            # Test filter
            page.visual_search.setText('dog')
            self.assertEqual(page.visual_list.topLevelItemCount(), 1)
            page.visual_search.setText('')
            self.assertEqual(page.visual_list.topLevelItemCount(), 2)
        finally:
            page.close()

    def test_results_page_preview_project_assignment(self):
        state = {
            'collections': [],
            'projects': [{'id': 'p1', 'name': 'Docu Series', 'folders': []}]
        }
        win = app.QWidget()
        win.state = state
        win.save = lambda: None
        page = app.ResultsPage(win)
        try:
            record = {'id': 'vid_x', 'source': 'clip_x.mp4', 'duration': 100}
            page.select_record(record)
            self.assertGreaterEqual(page.preview_project_combo.count(), 2)
            page.preview_project_combo.setCurrentIndex(1)
            page.add_current_to_project()
            self.assertEqual(record.get('project_id'), 'p1')
            self.assertEqual(record.get('project_name'), 'Docu Series')
        finally:
            page.close()

    def test_options_dialog_project_assignment(self):
        state = {
            'projects': [{'id': 'proj_alpha', 'name': 'Alpha Feature', 'created': 100, 'folders': []}],
            'settings': copy.deepcopy(core.DEFAULTS)
        }
        parent = app.QWidget()
        parent.state = state
        parent.centralWidget = lambda: None
        dialog = app.OptionsDialog(state['settings'], [], parent)
        try:
            self.assertEqual(dialog.project_combo.currentText(), 'Alpha Feature')
            vals = dialog.values()
            self.assertEqual(vals.get('project_id'), 'proj_alpha')
            self.assertEqual(vals.get('project_name'), 'Alpha Feature')
        finally:
            dialog.close()


    def test_results_page_project_bounding_box_and_export_buttons(self):
        state = {
            'collections': [],
            'projects': [{'id': 'p1', 'name': 'Docu Series', 'folders': []}],
            'results': []
        }
        win = app.QWidget()
        win.state = state
        win.save = lambda: None
        page = app.ResultsPage(win)
        try:
            # Dropdown and new project (+) button must be in the same bounding box
            self.assertIs(page.preview_project_combo.parent(), page.project_box)
            self.assertIs(page.btn_new_proj.parent(), page.project_box)
            # The add button is separate
            self.assertIsNot(page.btn_add_to_proj.parent(), page.project_box)

            # Export project and Add media buttons exist
            self.assertIsNotNone(page.export_project_btn)
            self.assertIsNotNone(page.add_media_btn)

            # Test shifting from project view to full video library
            page.set_active_collection('proj_p1')
            self.assertEqual(page.active_collection_id, 'p1')
            self.assertEqual(page.page_heading.text(), 'Docu Series')
            self.assertFalse(page.export_project_btn.isHidden())
            self.assertTrue(page.add_to_collection_btn.isHidden())
            page.set_active_collection('all')
            self.assertEqual(page.active_collection_id, 'all')
            self.assertEqual(page.page_heading.text(), 'Your footage')
            self.assertTrue(page.export_project_btn.isHidden())
        finally:
            page.close()

    def test_results_page_search_match_navigation_cycling(self):
        records = [{
            'id': 'vid_dog',
            'source': 'park_scene.mp4',
            'duration': 120,
            'segments': [{'start': 0, 'end': 10, 'text': 'Intro dialogue'}],
            'visual_index': {
                'frames': [
                    {'time': 2.5, 'detections': [{'label': 'dog', 'confidence': 0.95}], 'search_words': ['dog', 'animal']},
                    {'time': 5.0, 'detections': [{'label': 'dog', 'confidence': 0.88}], 'search_words': ['dog', 'animal']},
                    {'time': 8.0, 'detections': [{'label': 'dog', 'confidence': 0.92}], 'search_words': ['dog', 'animal']},
                ]
            }
        }]
        win = app.QWidget()
        win.state = {'collections': [], 'projects': [], 'results': records, 'settings': {'beta_features': True}}
        win.save = lambda: None
        page = app.ResultsPage(win)
        try:
            page.set_records(records)
            page.scope_filter.setCurrentIndex(2)  # Visuals only
            page.search.setText('dog')

            self.assertEqual(page.tree.topLevelItemCount(), 1)
            item = page.tree.topLevelItem(0)

            # 1st click on matching video: jumps to 1st match (2.5s -> 2500ms)
            page.on_table_item_clicked(item, 1)
            self.assertEqual(page.seek.value(), 2500)
            self.assertEqual(page.tabs.currentIndex(), 2)  # Visual Index tab
            cur_v = page.visual_list.currentItem()
            self.assertIsNotNone(cur_v)
            self.assertAlmostEqual(cur_v.data(0, app.Qt.UserRole), 2.5)

            # 2nd click on same video: advances to 2nd match (5.0s -> 5000ms)
            page.on_table_item_clicked(item, 1)
            self.assertEqual(page.seek.value(), 5000)
            cur_v2 = page.visual_list.currentItem()
            self.assertAlmostEqual(cur_v2.data(0, app.Qt.UserRole), 5.0)

            # 3rd click on same video: advances to 3rd match (8.0s -> 8000ms)
            page.on_table_item_clicked(item, 1)
            self.assertEqual(page.seek.value(), 8000)
            cur_v3 = page.visual_list.currentItem()
            self.assertAlmostEqual(cur_v3.data(0, app.Qt.UserRole), 8.0)

            # 4th click on same video: cycles back to 1st match (2.5s -> 2500ms)
            page.on_table_item_clicked(item, 1)
            self.assertEqual(page.seek.value(), 2500)
        finally:
            page.close()

    def test_paper_edit_word_document_layout(self):
        document = {
            'id': 'doc1',
            'title': 'Interview with Director',
            'source': 'director.mp4',
            'segments': [
                {'id': 's1', 'start': 0.0, 'end': 3.0, 'text': 'We started early in the morning.', 'speaker': 'DIRECTOR', 'included': True, 'highlighted': False, 'note': ''},
                {'id': 's2', 'start': 3.2, 'end': 6.0, 'text': 'The lighting was perfect.', 'speaker': 'DIRECTOR', 'included': True, 'highlighted': True, 'note': 'Key shot'},
                {'id': 's3', 'start': 6.5, 'end': 9.0, 'text': 'Cut this sentence out.', 'speaker': 'INTERVIEWER', 'included': False, 'highlighted': False, 'note': ''},
            ],
            'order': ['s1', 's2', 's3'],
            'strokes': []
        }
        paper_doc = app.PaperDocument()
        try:
            paper_doc.set_document(document)
            self.assertEqual(len(paper_doc.rows), 3)

            # First segment: standard included text
            row1 = paper_doc.rows[0]
            self.assertEqual(row1.text.toPlainText(), 'We started early in the morning.')
            self.assertTrue(row1.included.isChecked())

            # Second segment: highlighted
            row2 = paper_doc.rows[1]
            self.assertTrue(row2.highlight.isChecked())
            self.assertEqual(row2.note.text(), 'Key shot')
            self.assertIn('rgba(226, 180, 85', row2.text.styleSheet())

            # Third segment: excluded (strikethrough styling)
            row3 = paper_doc.rows[2]
            self.assertFalse(row3.included.isChecked())
            self.assertIn('line-through', row3.text.styleSheet())
        finally:
            paper_doc.close()


if __name__ == '__main__':
    unittest.main()
