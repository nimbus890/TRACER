import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from PIL import Image

import core
import vision_index


def detected(label, confidence, time):
    detection = {'label': label, 'confidence': confidence, 'layer': 'foreground', 'box': [0, 0, 10, 10]}
    keywords = {'foreground': [label], 'midground': [], 'background': []}
    return {'time': time, 'detections': [detection], 'keywords': keywords,
            'search_words': vision_index.searchable_words(keywords), 'file': f'{time}.jpg'}


class VisualSearchTests(unittest.TestCase):
    def test_alias_groups_confidence_and_adjacent_moment_grouping(self):
        frames = [detected('car', .52, 1), detected('car', .81, 2), detected('car', .62, 3),
                  detected('dog', .9, 20)]
        moments = vision_index.group_moments(frames, 'vehicles', 1)
        self.assertEqual(len(moments), 1)
        self.assertEqual((moments[0]['start'], moments[0]['end']), (1.0, 3.0))
        self.assertEqual(len(moments[0]['frames']), 3)
        self.assertEqual(moments[0]['frame']['time'], 2)
        phone = detected('cell phone', .7, 4)
        self.assertGreater(vision_index.frame_match(phone, 'smartphones')[0], 0)

    def test_visual_index_samples_both_boundaries_and_uses_small_thumbnails(self):
        class Detector:
            def detect(self, image):
                return [{'label': 'person', 'confidence': .8, 'layer': 'foreground',
                         'box': [0, 0, 10, 10]}]

        with tempfile.TemporaryDirectory() as root:
            root = Path(root)
            indexer = core.VisualIndexer()
            indexer.detector = Detector()
            requested = []

            def frame_at(source, seconds):
                requested.append(seconds)
                return Image.new('RGB', (1280, 720), '#445566'), float(seconds)

            options = {**core.DEFAULTS, 'visual_interval': 30}
            with patch('core.frame_at', side_effect=frame_at):
                result = indexer.index('source.mp4', root, 10, options, core.Control(), lambda *_: None)
            self.assertEqual(requested, [0.0, 10.0])
            self.assertEqual(result['samples_analyzed'], 2)
            self.assertEqual(len(result['frames']), 2)
            with Image.open(root / result['frames'][0]['file']) as image:
                self.assertLessEqual(image.width, 320)
                self.assertLessEqual(image.height, 180)


if __name__ == '__main__':
    unittest.main()
