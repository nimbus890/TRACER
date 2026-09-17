from pathlib import Path
import tempfile
import unittest

import core
import paper_edit
import timeline


class PaperEditTests(unittest.TestCase):
    def setUp(self):
        self.result = {
            'id': 'result-one',
            'source': 'interview.mp4',
            'segments': [
                {'start': 0.0, 'end': 1.5, 'text': 'The river remembers the old town.'},
                {'start': 2.0, 'end': 4.0, 'text': 'The river carries every story.'},
                {'start': 5.0, 'end': 6.0, 'text': 'A quiet closing line.'},
            ],
        }

    def test_document_preserves_writer_edits_when_library_refreshes(self):
        state = {}
        document = paper_edit.ensure_paper_document(state, self.result)
        document['segments'][0].update(text='My rewritten opening.', speaker='MAYA',
                                       note='Opening?', included=False, highlighted=True)
        again = paper_edit.ensure_paper_document(state, {
            **self.result,
            'segments': [{**segment, 'text': 'Updated machine transcript'}
                         for segment in self.result['segments']],
        })
        self.assertIs(again, document)
        self.assertEqual(again['segments'][0]['text'], 'My rewritten opening.')
        self.assertEqual(again['segments'][0]['note'], 'Opening?')
        self.assertFalse(again['segments'][0]['included'])

    def test_analysis_and_paper_order_are_honest_and_deterministic(self):
        document = paper_edit.ensure_paper_document({}, self.result)
        document['segments'][0]['speaker'] = 'Maya'
        document['segments'][1]['speaker'] = 'Dan'
        analysis = paper_edit.transcript_analysis(document)
        self.assertEqual(analysis['segments'], 3)
        self.assertEqual(analysis['speakers'], 2)
        self.assertIn(('river', 2), analysis['repeated_terms'])
        document['order'] = [document['segments'][1]['id'], document['segments'][0]['id'],
                             document['segments'][2]['id']]
        document['segments'][2]['included'] = False
        sequence = paper_edit.paper_sequence(document)
        clips = sequence['tracks'][1]['clips']
        self.assertEqual([clip['source_in'] for clip in clips], [2.0, 0.0])
        self.assertAlmostEqual(timeline.sequence_duration(sequence), 3.5)

    def test_new_machine_run_does_not_replace_authored_document(self):
        state = {}
        document = paper_edit.ensure_paper_document(state, self.result)
        document['segments'][0]['note'] = 'Keep the opening'
        newer = {**self.result, 'id': 'new-run', 'segments': []}
        self.assertIs(paper_edit.ensure_paper_document(state, newer), document)
        self.assertEqual(len(document['segments']), 3)
        self.assertEqual(document['segments'][0]['note'], 'Keep the opening')

    def test_invalid_export_does_not_create_package(self):
        document = paper_edit.ensure_paper_document({}, self.result)
        document['segments'][0]['end'] = -1
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):
                paper_edit.export_paper_package(document, root, trim=False)
            self.assertEqual(list(Path(root).iterdir()), [])

    def test_package_contains_script_manifest_and_premiere_xml(self):
        document = paper_edit.ensure_paper_document({}, self.result)
        document['segments'][0].update(speaker='Maya', note='Keep this')
        document['segments'][2]['included'] = False
        with tempfile.TemporaryDirectory() as root:
            target = paper_edit.export_paper_package(document, root, trim=False)
            self.assertTrue((target / 'script.txt').is_file())
            self.assertTrue((target / 'paper-edit.json').is_file())
            self.assertTrue((target / 'manifest.json').is_file())
            self.assertTrue((target / 'interview.xml').is_file())
            script = (target / 'script.txt').read_text(encoding='utf-8')
            self.assertIn('MAYA', script)
            self.assertIn('NOTE: Keep this', script)
            self.assertNotIn('quiet closing', script)

    def test_trimmed_media_keeps_requested_duration_when_fixture_exists(self):
        source = Path(__file__).resolve().parents[1] / 'verification' / 'spoken-sample.mp4'
        if not source.is_file():
            self.skipTest('generated verification media is not available')
        with tempfile.TemporaryDirectory() as root:
            destination = Path(root) / 'passage.mp4'
            paper_edit.trim_media(source, 0.5, 1.5, destination)
            details = core.probe(destination)
            self.assertAlmostEqual(details['duration'], 1.0, delta=0.2)
            self.assertTrue(details['audio'])


if __name__ == '__main__':
    unittest.main()
