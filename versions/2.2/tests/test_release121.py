"""Unit tests for Tracer 1.21 finishing release.

Covers:
- Schema migration from 1.19.2/1.20 to 121
- Stable passage model and bidirectional diff synchronization
- Preservation of Storyline-only tracks (B-roll, extra audio)
- Proportional split timing estimation
- Text-focus shortcut guard
- Diagnostics logging and path redaction
"""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication, QLineEdit, QWidget

import core
import paper_edit
import paper_sync
import release121
import timeline
import timeline_tools


class Release121Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def fixture(self):
        return {
            'schema_version': 120,
            'collections': [{'id': 'c', 'name': 'Documentary', 'video_ids': ['vid1']}],
            'projects': [{'id': 'c', 'name': 'Documentary', 'folders': [], 'sequences': []}],
            'results': [{
                'id': 'vid1', 'source': 'interview.mp4', 'duration': 30.0,
                'segments': [
                    {'start': 0.0, 'end': 6.0, 'text': 'We arrived at the river at dawn.'},
                    {'start': 6.0, 'end': 14.0, 'text': 'The boats were already leaving the shore.'},
                    {'start': 14.0, 'end': 22.0, 'text': 'Nobody said a word as the mist cleared.'},
                ]
            }],
            'paper_edits': []
        }

    def test_migration_upgrades_to_schema_121_and_ensures_passages(self):
        state = self.fixture()
        doc = paper_edit.ensure_paper_document(state, state['results'][0])
        doc['collection_id'] = 'c'
        state['paper_edits'].append(doc)

        release121.migrate(state)
        self.assertEqual(state['schema_version'], 121)

        # Verify all segments now have stable passage_id and timing metadata
        migrated_doc = state['paper_edits'][0]
        for seg in migrated_doc['segments']:
            self.assertTrue(bool(seg.get('passage_id')))
            self.assertEqual(seg['id'], seg['passage_id'])
            self.assertEqual(seg.get('timing_quality'), 'source')
            self.assertIn('handle_start', seg)
            self.assertIn('handle_end', seg)

    def test_diff_sync_creates_linked_clips_and_ripples_reorders(self):
        state = self.fixture()
        doc = paper_edit.ensure_paper_document(state, state['results'][0])
        doc['collection_id'] = 'c'
        state['paper_edits'].append(doc)

        # Initial sync
        coll, seq = release121.sync_paper(state, doc)
        v1_clips = seq['tracks'][1]['clips']
        self.assertEqual(len(v1_clips), 3)
        pids = [c['passage_id'] for c in v1_clips]
        self.assertEqual(pids, [s['id'] for s in doc['segments']])

        # Check ripple timing: clip 0 starts at 0, clip 1 starts at 6, clip 2 starts at 14
        self.assertAlmostEqual(float(v1_clips[0]['start']), 0.0)
        self.assertAlmostEqual(float(v1_clips[1]['start']), 6.0)
        self.assertAlmostEqual(float(v1_clips[2]['start']), 14.0)

        # Reorder passages: move last passage to first
        doc['order'] = [doc['order'][2], doc['order'][0], doc['order'][1]]
        coll, seq = release121.sync_paper(state, doc)
        v1_reordered = seq['tracks'][1]['clips']
        self.assertEqual(v1_reordered[0]['passage_id'], doc['order'][0])
        # Duration of passage 2 is 8s, so passage 0 now starts at 8s
        self.assertAlmostEqual(float(v1_reordered[0]['start']), 0.0)
        self.assertAlmostEqual(float(v1_reordered[1]['start']), 8.0)

    def test_exclude_passage_removes_clip_and_closes_gap(self):
        state = self.fixture()
        doc = paper_edit.ensure_paper_document(state, state['results'][0])
        doc['collection_id'] = 'c'
        state['paper_edits'].append(doc)

        coll, seq = release121.sync_paper(state, doc)
        # Exclude middle passage (duration 8s: 6.0 to 14.0)
        doc['segments'][1]['included'] = False
        coll, seq = release121.sync_paper(state, doc)

        v1_clips = seq['tracks'][1]['clips']
        self.assertEqual(len(v1_clips), 2)
        # Clip 0 (dur 6s) starts at 0; Clip 2 (dur 8s) now ripples to start at 6s!
        self.assertAlmostEqual(float(v1_clips[0]['start']), 0.0)
        self.assertAlmostEqual(float(v1_clips[1]['start']), 6.0)

    def test_b_roll_and_storyline_tracks_survive_paper_edits(self):
        state = self.fixture()
        doc = paper_edit.ensure_paper_document(state, state['results'][0])
        doc['collection_id'] = 'c'
        state['paper_edits'].append(doc)

        coll, seq = release121.sync_paper(state, doc)

        # Add manual B-roll on Track V2 (index 0) and music on A2 (index 3)
        b_roll = timeline.make_clip('drone.mp4', 5.0, start=2.0, name='B-Roll Drone')
        music = timeline.make_clip('music.mp3', 20.0, start=0.0, name='Background Score')
        seq['tracks'][0]['clips'].append(b_roll)
        seq['tracks'][3]['clips'].append(music)

        # Perform multiple paper edits (reorder, exclude, re-include)
        doc['segments'][0]['included'] = False
        coll, seq = release121.sync_paper(state, doc)

        # Verify B-roll and music are completely intact!
        self.assertEqual(len(seq['tracks'][0]['clips']), 1)
        self.assertEqual(seq['tracks'][0]['clips'][0]['name'], 'B-Roll Drone')
        self.assertEqual(seq['tracks'][0]['clips'][0]['start'], 2.0)

        self.assertEqual(len(seq['tracks'][3]['clips']), 1)
        self.assertEqual(seq['tracks'][3]['clips'][0]['name'], 'Background Score')

    def test_storyline_trim_syncs_back_to_paper_edit(self):
        state = self.fixture()
        doc = paper_edit.ensure_paper_document(state, state['results'][0])
        doc['collection_id'] = 'c'
        state['paper_edits'].append(doc)

        coll, seq = release121.sync_paper(state, doc)
        v1_clip = seq['tracks'][1]['clips'][0]
        clip_id = v1_clip['id']

        # Trim the clip in Storyline: source_in moved from 0 to 1.5, source_out from 6 to 5.0
        v1_clip['source_in'] = 1.5
        v1_clip['source_out'] = 5.0

        updated = paper_sync.sync_sequence_trim_to_paper(seq, doc, clip_id)
        self.assertTrue(updated)

        passage = doc['segments'][0]
        self.assertAlmostEqual(passage['start'], 1.5)
        self.assertAlmostEqual(passage['end'], 5.0)
        self.assertEqual(passage['timing_quality'], 'manual')

    def test_proportional_split_timing(self):
        passage = {
            'id': 'p1', 'start': 10.0, 'end': 20.0, 'text': 'First half. Second half.',
            'timing_quality': 'source'
        }
        # Split in the middle (50%)
        p1, p2 = paper_sync.estimate_split_timing(passage, 0.5)
        self.assertAlmostEqual(p1['start'], 10.0)
        self.assertAlmostEqual(p1['end'], 15.0)
        self.assertAlmostEqual(p2['start'], 15.0)
        self.assertAlmostEqual(p2['end'], 20.0)
        self.assertEqual(p1['timing_quality'], 'estimated')
        self.assertEqual(p2['timing_quality'], 'estimated')
        self.assertNotEqual(p1['id'], p2['id'])

    def test_shortcut_guard_blocks_timeline_keys_when_text_focused(self):
        widget = QWidget()
        line_edit = QLineEdit(widget)
        widget.show()
        line_edit.setFocus()
        self.qt.processEvents()
        self.assertTrue(timeline_tools.is_text_editing_focused())

        canvas = timeline.TimelineCanvas()
        controller = timeline_tools.TimelineToolController(canvas)
        # With text field focused, 'C' (razor shortcut) must NOT fire
        key_event = QKeyEvent(QEvent.KeyPress, Qt.Key_C, Qt.NoModifier, 'c')
        handled = controller.handle_key_press(key_event)
        self.assertFalse(handled)
        self.assertEqual(controller.active_tool, 'select')

        # Clear focus: shortcut should now trigger
        line_edit.clearFocus()
        handled = controller.handle_key_press(key_event)
        self.assertTrue(handled)
        self.assertEqual(controller.active_tool, 'razor')

    def test_diagnostics_logging_and_path_redaction(self):
        home_path = Path.home() / 'Documents' / 'secret_video.mp4'
        redacted = core.redact_path(home_path)
        self.assertTrue(redacted.startswith('~') or redacted == 'secret_video.mp4')

        # Test logging without crash
        with tempfile.TemporaryDirectory() as temp_dir:
            orig_data = core.DATA
            try:
                core.DATA = Path(temp_dir)
                core.LOGS_DIR = core.DATA / 'logs'
                core.LOG_FILE = core.LOGS_DIR / 'tracer.log'
                core.log_diagnostic('Test diagnostic message', 'TEST')
                self.assertTrue(core.LOG_FILE.exists())
                content = core.LOG_FILE.read_text(encoding='utf-8')
                self.assertIn('[TEST] Test diagnostic message', content)

                summary = core.get_diagnostics_summary(self.fixture())
                self.assertIn('Tracer Version:', summary)
                self.assertIn('Indexed Footage:', summary)
            finally:
                core.DATA = orig_data
                core.LOGS_DIR = core.DATA / 'logs'
                core.LOG_FILE = core.LOGS_DIR / 'tracer.log'


if __name__ == '__main__':
    unittest.main()
