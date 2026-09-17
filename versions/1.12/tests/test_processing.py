import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import core
import av
import numpy as np


def make_video(path, seconds=3, fps=10):
    with av.open(str(path), 'w') as output:
        stream = output.add_stream('mpeg4', rate=fps)
        stream.width = 320
        stream.height = 180
        stream.pix_fmt = 'yuv420p'
        for i in range(round(seconds * fps)):
            pixels = np.full((180, 320, 3), 0 if i < fps else 255, dtype=np.uint8)
            frame = av.VideoFrame.from_ndarray(pixels, format='rgb24')
            for packet in stream.encode(frame):
                output.mux(packet)
        for packet in stream.encode():
            output.mux(packet)


class ProcessingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.previous_analytics = os.environ.get('TRANSPRO_ANALYTICS_FILE')
        os.environ['TRANSPRO_ANALYTICS_FILE'] = str(self.root / 'processing-history.jsonl')
        self.path = self.root / 'sample.mp4'
        make_video(self.path)
        self.video = core.scan_folder(self.root)['files'][0]

    def tearDown(self):
        if self.previous_analytics is None:
            os.environ.pop('TRANSPRO_ANALYTICS_FILE', None)
        else:
            os.environ['TRANSPRO_ANALYTICS_FILE'] = self.previous_analytics
        self.temp.cleanup()

    def process(self, **kwargs):
        options = {**core.DEFAULTS, 'transcribe': False, 'interval': 0.5, **kwargs}
        return core.process_video(self.root, self.video, options, core.Control(), core.Transcriber(), lambda *_: None)

    def test_interval_extract_export_and_reuse(self):
        result = self.process(transcribe=True)
        self.assertEqual(result['status'], 'Completed')
        self.assertEqual([round(f['time'], 2) for f in result['frames']], [0, .5, 1, 1.5, 2, 2.5])
        self.assertEqual(result['segments'], [])
        self.assertTrue(Path(result['output'], 'transcript.srt').exists())
        self.assertEqual(self.process(transcribe=True)['id'], result['id'])
        self.assertEqual(len(core.scan_folder(self.root)['files']), 1)

    def test_missing_image_invalidates_duplicate(self):
        first = self.process()
        Path(first['output'], first['frames'][0]['file']).unlink()
        self.assertNotEqual(first['id'], self.process()['id'])

    def test_scene_detection(self):
        result = self.process(mode='scene')
        self.assertEqual([round(f['time'], 1) for f in result['frames']], [0, 1])

    def test_png_screenshots_are_lossless_files(self):
        result = self.process(image_format='png', visual_index=False)
        self.assertTrue(result['frames'])
        self.assertTrue(all(frame['file'].endswith('.png') for frame in result['frames']))
        self.assertTrue(all(Path(result['output'], frame['file']).is_file() for frame in result['frames']))

    def test_local_processing_analytics_records_metrics_without_transcript_text(self):
        result = self.process(visual_index=False, skip_existing=False)
        events = [json.loads(line) for line in Path(os.environ['TRANSPRO_ANALYTICS_FILE']).read_text(encoding='utf-8').splitlines()]
        event = events[-1]
        self.assertEqual(event['outcome'], 'Completed')
        self.assertEqual(event['app_version'], '1.12.0')
        self.assertEqual(event['result']['screenshot_count'], len(result['frames']))
        self.assertIn('processing_seconds', event['performance'])
        self.assertNotIn('segments', event['result'])

    def test_settings_and_input_invalidate_signature(self):
        first = core.signature(self.path, core.DEFAULTS)
        self.assertNotEqual(first, core.signature(self.path, {**core.DEFAULTS, 'interval': 2}))
        stat = self.path.stat()
        os.utime(self.path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1000000000))
        self.assertNotEqual(first, core.signature(self.path, core.DEFAULTS))

    def test_scan_recursive_and_bad_video(self):
        sub = self.root / 'child'
        sub.mkdir()
        make_video(sub / 'nested.mp4')
        (self.root / 'broken.mp4').write_bytes(b'not a video')
        self.assertEqual(len(core.scan_folder(self.root, False)['files']), 2)
        scanned = core.scan_folder(self.root, True)['files']
        self.assertEqual(len(scanned), 3)
        self.assertFalse(next(v for v in scanned if v['name'] == 'broken.mp4')['selected'])

    def test_cancel_while_paused(self):
        control = core.Control()
        control.running.clear()
        stopped = []
        def work():
            try:
                control.checkpoint()
            except core.Cancelled:
                stopped.append(True)
        thread = threading.Thread(target=work)
        thread.start()
        time.sleep(.05)
        control.cancel.set()
        thread.join(1)
        self.assertFalse(thread.is_alive())
        self.assertTrue(stopped)

    def test_outputs_and_subtitle_timestamps(self):
        segments = [dict(start=1.25, end=61.007, text=' Hello, world. ')]
        core.export_transcript(self.root, segments)
        self.assertIn('00:00:01,250 --> 00:01:01,007', (self.root / 'transcript.srt').read_text())
        self.assertIn('WEBVTT', (self.root / 'transcript.vtt').read_text())
        self.assertEqual(json.loads((self.root / 'transcript.json').read_text()), segments)

    def test_estimate_and_validation(self):
        estimate = core.estimate([{**self.video, 'duration': 3600}], {**core.DEFAULTS, 'interval': .1})
        self.assertEqual(estimate['count'], 36000)
        with self.assertRaises(ValueError):
            core.validate_options({'interval': 0})
        with self.assertRaises(ValueError):
            core.validate_options({'screenshots': False, 'transcribe': False, 'visual_index': False})

    def test_duplicate_filenames_and_reruns_are_separate(self):
        first = self.process(skip_existing=False)
        second = self.process(skip_existing=False)
        self.assertNotEqual(first['output'], second['output'])
        self.assertTrue(Path(first['output']).is_dir())

    def test_transcription_only_creates_no_images_even_without_audio(self):
        result = self.process(transcribe=True, screenshots=False)
        self.assertEqual(result['frames'], [])
        self.assertFalse(Path(result['output'], 'screenshots').exists())
        for name in ('txt', 'srt', 'vtt', 'json'):
            self.assertTrue(Path(result['output'], 'transcript.' + name).exists())

    def test_secondary_branch_stops_when_transcription_fails(self):
        from unittest.mock import patch
        stopped = threading.Event()
        def long_frames(path, out, options, control, progress):
            try:
                while True:
                    control.checkpoint()
                    time.sleep(.02)
            finally:
                stopped.set()
        class BrokenTranscriber:
            def transcribe(self, *args):
                raise RuntimeError('Missing GPU library')
        with patch('core.extract_frames', long_frames):
            with self.assertRaisesRegex(RuntimeError, 'Missing GPU library'):
                core.process_video(self.root, {**self.video, 'audio': True}, core.DEFAULTS,
                                   core.Control(), BrokenTranscriber(), lambda *_: None)
        self.assertTrue(stopped.is_set())
        metadata = next((self.root / core.OUTPUT_NAME).glob('*/processing-details.json'))
        self.assertEqual(json.loads(metadata.read_text())['status'], 'Failed')


if __name__ == '__main__':
    unittest.main()
