"""Focused regression tests for the Tracer 1.23 release."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import time
import unittest
from types import SimpleNamespace

from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication, QWidget

import app
import core
import timeline
import timeline_tools
import transcape


class Release123Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def test_beta_toggle_persistence(self):
        self.assertFalse(core.DEFAULTS.get('beta_features', True))
        
        # Test persistence
        state = {'settings': core.DEFAULTS.copy()}
        state['settings']['beta_features'] = True
        self.assertTrue(state['settings']['beta_features'])
        
        state['settings']['beta_features'] = False
        self.assertFalse(state['settings']['beta_features'])

    def test_beta_text_gating(self):
        from PySide6.QtWidgets import QLabel
        # Beta off (parent=None means beta defaults to False)
        dialog_off = app.LibraryPickerDialog([], parent=None)
        subtitle_off = dialog_off.findChild(QLabel, 'subtle')
        self.assertIsNotNone(subtitle_off)
        self.assertNotIn('visual terms', subtitle_off.text())
        dialog_off.close()

        # Beta on — create a minimal QWidget parent with the expected attribute chain
        host = QWidget()
        # Real callers set self.window = Window instance, which shadows QWidget.window()
        host.window = type('FakeWindow', (), {'state': {'settings': {'beta_features': True}}})()
        dialog_on = app.LibraryPickerDialog([], parent=host)
        subtitle_on = dialog_on.findChild(QLabel, 'subtle')
        self.assertIsNotNone(subtitle_on)
        self.assertIn('visual terms', subtitle_on.text())
        dialog_on.close()
        host.close()

    def test_transcape_seed_layout_safety(self):
        state = {
            'results': [{'id': str(i), 'source': f'{i}.mp4'} for i in range(60)]
        }
        field = transcape.Field(state)
        self.assertGreaterEqual(len(field.nodes), 60)
        
        start = time.time()
        field.seed_layout()
        elapsed = time.time() - start
        
        self.assertLess(elapsed, 2.0, "seed_layout took too long, might be hanging")
        self.assertGreater(len(field.cluster_centres), 0)

    def test_transcape_build_graph(self):
        state = {
            'results': [{
                'id': 'vid1', 'source': 'interview.mp4',
                'segments': [{'start': 0.0, 'end': 5.0, 'text': 'Important message.'}],
                'visual_index': {'frames': [{'time': 1.0, 'search_words': ['person'], 'detections': []}]}
            }]
        }
        nodes, edges = transcape.build_graph(state)
        
        node_ids = {n['id'] for n in nodes}
        self.assertIn('file:vid1', node_ids)
        self.assertIn('word:important', node_ids)
        self.assertIn('word:message', node_ids)
        self.assertIn('visual:person', node_ids)
        
        self.assertGreater(len(edges), 0)

    def test_timeline_shortcuts_completeness(self):
        host = QWidget()
        canvas = timeline.TimelineCanvas(host)
        controller = timeline_tools.TimelineToolController(canvas)
        commands = []
        controller.commandTriggered.connect(commands.append)
        host.show()
        canvas.setFocus()
        self.qt.processEvents()

        cases = [
            (Qt.Key_Delete, Qt.ShiftModifier, 'ripple_delete'),
            (Qt.Key_Backspace, Qt.ShiftModifier, 'ripple_delete'),
            (Qt.Key_K, Qt.ControlModifier, 'add_edit'),
            (Qt.Key_Y, Qt.ControlModifier, 'redo'),
            (Qt.Key_Z, Qt.ControlModifier | Qt.ShiftModifier, 'redo'),
        ]
        
        for key, modifiers, expected in cases:
            event = QKeyEvent(QEvent.KeyPress, key, modifiers)
            self.assertTrue(controller.handle_key_press(event), f"Failed for {expected}")
            self.assertEqual(commands[-1], expected)

        host.close()

    def test_collection_crud(self):
        state = {'collections': [{'id': 'all', 'name': 'All footage', 'builtin': True}]}
        
        # Create
        c = core.create_collection(state, 'My Collection')
        self.assertEqual(c['name'], 'My Collection')
        self.assertEqual(len(state['collections']), 2)
        
        # Add to collection
        core.add_to_collection(state, c['id'], ['vid1', 'vid2'])
        self.assertEqual(set(c['video_ids']), {'vid1', 'vid2'})
        
        # collection_video_ids
        ids = core.collection_video_ids(state, c['id'])
        self.assertEqual(ids, {'vid1', 'vid2'})
        
        # Remove from collection
        core.remove_from_collection(state, c['id'], ['vid1'])
        self.assertEqual(set(c['video_ids']), {'vid2'})


    def test_track_header_hide_and_lock_click(self):
        host = QWidget()
        canvas = timeline.TimelineCanvas(host)
        seq = timeline.new_sequence('Test Seq')
        seq['tracks'] = [
            {'id': 'v1', 'name': 'V1', 'type': 'video', 'visible': True, 'locked': False, 'clips': []},
            {'id': 'a1', 'name': 'A1', 'type': 'audio', 'visible': True, 'muted': False, 'locked': False, 'clips': []},
        ]
        canvas.sequence = seq
        host.show()
        self.qt.processEvents()

        # Track 0: y in [28, 86]. cx=20, cy=66 (local_y=38)
        # Click hide icon on video track 0
        press_event = SimpleNamespace(position=lambda: SimpleNamespace(x=lambda: 20, y=lambda: 66),
                                      button=lambda: Qt.LeftButton)
        canvas.mousePressEvent(press_event)
        self.assertFalse(seq['tracks'][0]['visible'])

        # Click hide icon again to unhide
        canvas.mousePressEvent(press_event)
        self.assertTrue(seq['tracks'][0]['visible'])

        # Click lock icon on video track 0 (lx=44, cy=66)
        lock_event = SimpleNamespace(position=lambda: SimpleNamespace(x=lambda: 44, y=lambda: 66),
                                     button=lambda: Qt.LeftButton)
        canvas.mousePressEvent(lock_event)
        self.assertTrue(seq['tracks'][0]['locked'])

        # Track 1: y in [86, 144]. cx=20, cy=124 (local_y=38)
        # Click mute icon on audio track 1
        mute_event = SimpleNamespace(position=lambda: SimpleNamespace(x=lambda: 20, y=lambda: 124),
                                     button=lambda: Qt.LeftButton)
        canvas.mousePressEvent(mute_event)
        self.assertTrue(seq['tracks'][1]['muted'])
        host.close()

    def test_sequence_media_list_grid_toggle(self):
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

        win = FakeWindow()
        page = app.ProjectsPage(win)
        try:
            self.assertTrue(hasattr(page, 'media_view_toggle'))
            self.assertTrue(hasattr(page, 'media_grid'))
            self.assertTrue(hasattr(page, 'media_stack'))

            # Initially in list mode (tree)
            self.assertEqual(page.media_stack.currentWidget(), page.tree)

            # Toggle to grid mode
            page.media_view_toggle.setChecked(True)
            self.assertEqual(page.media_stack.currentWidget(), page.media_grid)

            # Toggle back to list mode
            page.media_view_toggle.setChecked(False)
            self.assertEqual(page.media_stack.currentWidget(), page.tree)
        finally:
            page.close()
            win.close()


if __name__ == '__main__':
    unittest.main()
