import copy
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from app import Batch
from PySide6.QtCore import QCoreApplication
import core


class BatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def folders(self):
        return [dict(id='first', path='C:/first', files=[
                    dict(path='C:/first/a.mp4', selected=True, status='Ready'),
                    dict(path='C:/first/b.mp4', selected=False, status='Ready'),
                    dict(path='C:/first/c.mp4', selected=True, status='Ready')]),
                dict(id='second', path='C:/second', files=[
                    dict(path='C:/second/d.mp4', selected=True, status='Ready'),
                    dict(path='C:/first/a.mp4', selected=True, status='Ready')])]

    def test_folder_order_selection_failure_continuation_and_overlap(self):
        calls = []
        events = []
        def process(folder, video, *args):
            calls.append(video['path'])
            if video['path'].endswith('c.mp4'):
                raise OSError('Unreadable file')
            return {'id': video['path']}
        batch = Batch(self.folders(), core.DEFAULTS)
        batch.event.connect(lambda *args: events.append(args))
        with patch('core.process_video', process):
            batch.run()
        self.assertEqual(calls, ['C:/first/a.mp4', 'C:/first/c.mp4', 'C:/second/d.mp4'])
        self.assertTrue(any(e[2] == 'error' for e in events))
        self.assertTrue(any(e[3] == 'Duplicate in queue' for e in events))

    def test_cancel_does_not_start_next_video(self):
        calls = []
        batch = Batch(self.folders(), core.DEFAULTS)
        def process(folder, video, *args):
            calls.append(video['path'])
            batch.control.cancel.set()
            raise core.Cancelled()
        with patch('core.process_video', process):
            batch.run()
        self.assertEqual(calls, ['C:/first/a.mp4'])


if __name__ == '__main__':
    unittest.main()
