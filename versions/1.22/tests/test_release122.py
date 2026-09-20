"""Focused regression tests for the Tracer 1.22 finishing release."""
import copy
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import unittest
from types import SimpleNamespace

from PySide6.QtCore import Qt, QEvent, QTimer
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication, QLineEdit, QWidget

import app
import paper_edit
import paper_sync
import release121
import timeline
import timeline_tools
import workspace


class Release122Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def fixture(self):
        state = {
            'schema_version': 121,
            'collections': [{'id': 'all', 'name': 'All footage', 'builtin': True},
                            {'id': 'c', 'name': 'Documentary', 'video_ids': ['vid']}],
            'projects': [{'id': 'c', 'name': 'Documentary', 'video_ids': ['vid'],
                          'folders': [], 'sequences': []}],
            'results': [{'id': 'vid', 'source': 'interview.mp4', 'duration': 20.0,
                         'segments': [
                             {'start': 0.0, 'end': 5.0, 'text': 'Opening.'},
                             {'start': 5.0, 'end': 12.0, 'text': 'Second thought.'},
                         ]}],
            'paper_edits': [],
        }
        document = paper_edit.ensure_paper_document(state, state['results'][0])
        document['collection_id'] = 'c'
        state['paper_edits'].append(document)
        return state, document

    def test_repeated_sync_keeps_clip_identity_and_storyline_tracks(self):
        state, document = self.fixture()
        collection, sequence = release121.sync_paper(state, document)
        first_ids = [clip['id'] for clip in sequence['tracks'][1]['clips']]
        b_roll = timeline.make_clip('b-roll.mp4', 3.0, 1.0, name='B-roll')
        sequence['tracks'][0]['clips'].append(b_roll)

        for _ in range(3):
            collection, sequence = release121.sync_paper(state, document)

        self.assertEqual([clip['id'] for clip in sequence['tracks'][1]['clips']], first_ids)
        self.assertEqual(sequence['tracks'][0]['clips'], [b_roll])
        self.assertIs(paper_sync.linked_document(state, sequence), document)

    def test_linked_document_uses_sequence_identity_not_active_page(self):
        state, document = self.fixture()
        _, sequence = release121.sync_paper(state, document)
        other = copy.deepcopy(document)
        other['id'] = 'other-document'
        state['paper_edits'].append(other)
        self.assertEqual(paper_sync.linked_document(state, sequence)['id'], document['id'])
        self.assertIsNone(paper_sync.linked_document(state, {'paper_document_id': 'missing'}))

    def test_tool_icons_are_native_symbols(self):
        for name in ('select', 'track_select', 'ripple', 'razor', 'hand', 'zoom',
                     'video_track', 'audio_track', 'toggle', 'lock', 'solo',
                     'marker', 'snap', 'fit'):
            self.assertFalse(workspace.icon(name).isNull(), name)

    def test_shortcuts_route_commands_and_respect_text_focus(self):
        host = QWidget()
        canvas = timeline.TimelineCanvas(host)
        controller = timeline_tools.TimelineToolController(canvas)
        commands = []
        controller.commandTriggered.connect(commands.append)
        host.show()
        canvas.setFocus()
        self.qt.processEvents()

        cases = [
            (Qt.Key_Space, Qt.NoModifier, 'play_pause'),
            (Qt.Key_K, Qt.ControlModifier, 'add_edit'),
            (Qt.Key_Z, Qt.ControlModifier, 'undo'),
            (Qt.Key_Z, Qt.ControlModifier | Qt.ShiftModifier, 'redo'),
            (Qt.Key_C, Qt.ControlModifier, 'copy'),
            (Qt.Key_V, Qt.ControlModifier, 'paste'),
            (Qt.Key_Backslash, Qt.NoModifier, 'fit'),
        ]
        for key, modifiers, expected in cases:
            event = QKeyEvent(QEvent.KeyPress, key, modifiers)
            self.assertTrue(controller.handle_key_press(event), expected)
            self.assertEqual(commands[-1], expected)

        field = QLineEdit(host)
        field.show()
        field.setFocus()
        self.qt.processEvents()
        count = len(commands)
        event = QKeyEvent(QEvent.KeyPress, Qt.Key_C, Qt.NoModifier, 'c')
        self.assertFalse(controller.handle_key_press(event))
        self.assertEqual(len(commands), count)
        host.close()

    def test_status_reports_link_state_factually(self):
        state, document = self.fixture()
        self.assertTrue(paper_sync.status_badge_text(document).startswith('Not linked'))
        release121.sync_paper(state, document)
        self.assertTrue(paper_sync.status_badge_text(document).startswith('Linked'))

    def test_passage_order_can_exclude_and_restore_dialogue(self):
        state, document = self.fixture()
        owner = SimpleNamespace(state=state, save_timer=QTimer())
        page = app.PaperEditPage(owner)
        self.assertEqual(page.sequence.count(), 2)
        item = page.sequence.item(0)
        item.setCheckState(Qt.Unchecked)
        self.qt.processEvents()
        self.assertFalse(document['segments'][0]['included'])
        linked = next(sequence for sequence in state['projects'][0]['sequences']
                      if sequence.get('paper_document_id') == document['id'])
        self.assertEqual(len(linked['tracks'][1]['clips']), 1)
        item.setCheckState(Qt.Checked)
        self.qt.processEvents()
        self.assertTrue(document['segments'][0]['included'])
        self.assertEqual(len(linked['tracks'][1]['clips']), 2)
        page.close()


if __name__ == '__main__':
    unittest.main()
