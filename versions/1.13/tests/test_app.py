import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtCore import QItemSelectionModel
from PySide6.QtWidgets import QApplication, QFileDialog, QTreeView

import app


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

    def test_unified_picker_is_read_only_and_accepts_multiple_items(self):
        with tempfile.TemporaryDirectory() as root:
            folder = Path(root) / 'folder'
            folder.mkdir()
            video = Path(root) / 'clip.mp4'
            video.touch()
            picker = app.MediaPickerDialog()
            try:
                self.assertEqual(picker.fileMode(), QFileDialog.ExistingFiles)
                self.assertTrue(picker.testOption(QFileDialog.DontUseNativeDialog))
                self.assertTrue(picker.testOption(QFileDialog.ReadOnly))
                self.assertEqual(picker.labelText(QFileDialog.Accept), 'Add selected')
                picker.setDirectory(root)
                picker.show()
                self.application.processEvents()
                view = picker.findChild(QTreeView, 'treeView')
                model = view.model()
                flags = QItemSelectionModel.Select | QItemSelectionModel.Rows
                view.selectionModel().select(model.index(str(folder)), flags)
                view.selectionModel().select(model.index(str(video)), flags)
                self.assertEqual(
                    set(picker.selected_media_paths()),
                    {str(folder.resolve()), str(video.resolve())})
            finally:
                picker.close()

    def test_search_highlights_each_case_insensitive_occurrence(self):
        self.assertEqual(
            app.highlighted_parts('Person walks past another PERSON.', 'person'),
            [('Person', True), (' walks past another ', False), ('PERSON', True), ('.', False)])
        self.assertEqual(app.highlighted_parts('No visual match', 'chair'), [('No visual match', False)])

    def test_windows_reveals_the_exact_source_file(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / 'clip with spaces.mp4'
            source.touch()
            with patch.object(app.sys, 'platform', 'win32'), patch('app.subprocess.Popen') as launch:
                app.reveal_path(source)
            launch.assert_called_once_with(
                ['explorer.exe', '/select,' + os.path.normpath(str(source))])


if __name__ == '__main__':
    unittest.main()
