import copy
import json
from pathlib import Path
import tempfile
import unittest
import core
import paper_edit
import release120
import transcape
import timeline


class Release120Tests(unittest.TestCase):
    def fixture(self):
        return {'collections': [{'id': 'c', 'name': 'River', 'video_ids': ['a']}],
                'projects': [{'id': 'p', 'name': 'Old project', 'folders': [], 'sequences': [timeline.new_sequence('Existing cut')]}],
                'results': [{'id': 'a', 'source': 'river.mp4', 'duration': 8,
                             'segments': [{'start': 0, 'end': 4, 'text': 'The river connects our village.'},
                                          {'start': 4, 'end': 8, 'text': 'River boats return home.'}],
                             'visual_index': {'frames': [{'time': 3, 'search_words': ['boat']}]}}]}

    def test_migration_retains_ids_sequences_and_membership_after_reload(self):
        state = self.fixture()
        sequence_id = state['projects'][0]['sequences'][0]['id']
        release120.migrate(state)
        release120.attach(state, 'c', state['results'])
        release120.migrate(state)
        state = json.loads(json.dumps(state))
        release120.migrate(state)
        self.assertEqual(len(state['projects']), 2)
        self.assertEqual(next(p for p in state['projects'] if p['id'] == 'p')['sequences'][0]['id'], sequence_id)
        self.assertEqual([r['id'] for r in release120.collection_records(state, 'c')], ['a'])
        self.assertIs(state['projects'][0], state['collections'][1])

    def test_paper_updates_one_sequence_preserves_manually_changed_cut(self):
        state = self.fixture()
        doc = paper_edit.ensure_paper_document(state, state['results'][0])
        doc['collection_id'] = 'c'
        coll, seq = release120.sync_paper(state, doc)
        seq_id = seq['id']
        doc['segments'][1]['included'] = False
        coll, seq = release120.sync_paper(state, doc)
        self.assertEqual(seq['id'], seq_id)
        self.assertEqual(timeline.sequence_duration(seq), 4)
        seq['tracks'][1]['clips'][0]['start'] = 1
        coll, seq = release120.sync_paper(state, doc)
        self.assertTrue(any(s['name'].endswith('Storyline cut') for s in coll['sequences']))
        self.assertEqual(sum(s.get('paper_document_id') == doc['id'] for s in coll['sequences']), 1)

    def test_export_selected_deduplicates_and_reports_missing(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            a, b = root / 'a', root / 'b'
            a.mkdir(); b.mkdir()
            (a / 'clip.mp4').write_bytes(b'a')
            (b / 'clip.mp4').write_bytes(b'b')
            records = [{'id': str(i), 'source': str(path)} for i, path in enumerate(
                [a/'clip.mp4', a/'clip.mp4', b/'clip.mp4', root/'missing.mp4'])]
            self.assertEqual(core.export_collection({}, 'all', root/'out', records), (2, 1, []))
            self.assertEqual(sorted(p.read_bytes() for p in (root/'out').iterdir()), [b'a', b'b'])
            self.assertEqual(core.export_collection({'results': records}, 'all', root/'empty', []), (0, 0, []))

    def test_transcape_uses_transcript_and_visual_evidence(self):
        state = self.fixture()
        nodes, edges = transcape.build_graph(state)
        by_id = {n['id']: n for n in nodes}
        self.assertIn('word:river', by_id)
        self.assertIn('visual:boat', by_id)
        self.assertEqual(by_id['visual:boat']['time'], 3)
        self.assertIn(('file:a', 'word:river'), edges)
        self.assertEqual(transcape.build_graph(state), (nodes, edges))


if __name__ == '__main__':
    unittest.main()
