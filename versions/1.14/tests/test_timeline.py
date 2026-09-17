from pathlib import Path
import tempfile
import unittest

import timeline


class TimelineTests(unittest.TestCase):
    def test_old_project_is_migrated_with_sequence_tracks_and_export_queue(self):
        project = {'id': 'project', 'name': 'Documentary', 'folders': []}
        timeline.ensure_project_editing(project)
        self.assertEqual(len(project['sequences']), 1)
        self.assertEqual([track['type'] for track in project['sequences'][0]['tracks']],
                         ['video', 'video', 'audio', 'audio'])
        self.assertEqual(project['export_queue'], [])

    def test_premiere_xml_contains_timed_video_and_audio_clips(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / 'interview.mp4'
            source.touch()
            sequence = timeline.new_sequence('Act One')
            sequence['tracks'][1]['clips'].append(
                timeline.make_clip(source, 12.5, start=3.0, name='Interview'))
            sequence['tracks'][2]['clips'].append(
                timeline.make_clip(source, 12.5, start=3.0, name='Interview'))
            xml = timeline.final_cut_xml(sequence)
            self.assertIn('<name>Act One</name>', xml)
            self.assertEqual(xml.count('<clipitem'), 2)
            self.assertIn(source.resolve().as_uri(), xml)

    def test_collect_media_avoids_filename_collisions_and_reports_offline_sources(self):
        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            first = root / 'card-a' / 'clip.mp4'
            second = root / 'card-b' / 'clip.mp4'
            first.parent.mkdir()
            second.parent.mkdir()
            first.write_bytes(b'first')
            second.write_bytes(b'second')
            missing = root / 'gone.mp4'
            sequence = timeline.new_sequence('Assembly')
            track = sequence['tracks'][1]
            track['clips'] = [timeline.make_clip(first, 1), timeline.make_clip(second, 1, start=1),
                              timeline.make_clip(missing, 1, start=2)]
            self.assertEqual(timeline.offline_sources(sequence), [str(missing)])
            collected = timeline.collect_sequence_media(sequence, root / 'deliveries')
            names = sorted(path.name for path in (collected / 'Media').iterdir())
            self.assertEqual(names, ['clip.mp4', 'clip_2.mp4'])
            self.assertTrue((collected / 'Assembly.xml').is_file())
            self.assertTrue((collected / 'manifest.json').is_file())
            xml = (collected / 'Assembly.xml').read_text(encoding='utf-8')
            self.assertIn((collected / 'Media' / 'clip.mp4').resolve().as_uri(), xml)
            self.assertIn((collected / 'Media' / 'clip_2.mp4').resolve().as_uri(), xml)


if __name__ == '__main__':
    unittest.main()
