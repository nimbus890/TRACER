"""Small, offline visual index built on OpenCV Zoo's NanoDet model.

The model recognises the 80 COCO object classes. Tracer stores no face identity
or biometric data; it saves object labels, approximate screen-space depth, and a
small thumbnail for each sampled moment.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image


CLASSES = (
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck',
    'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
    'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra',
    'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
    'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
    'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
    'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
    'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
    'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
    'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
    'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
    'toothbrush'
)

ALIASES = {
    'person': ('people', 'human', 'man', 'woman'),
    'cell phone': ('phone', 'mobile', 'smartphone'),
    'airplane': ('plane', 'aircraft'),
    'motorcycle': ('motorbike', 'bike'),
    'bicycle': ('bike', 'cycle'),
    'couch': ('sofa',),
    'tv': ('television', 'screen', 'monitor'),
    'dining table': ('table', 'desk'),
    'potted plant': ('plant',),
    'sports ball': ('ball',),
    'refrigerator': ('fridge',),
}


def _softmax(values):
    values = values - values.max(axis=1, keepdims=True)
    values = np.exp(values)
    return values / values.sum(axis=1, keepdims=True)


def _iou(one, many):
    left = np.maximum(one[:2], many[:, :2])
    right = np.minimum(one[2:], many[:, 2:])
    wh = np.maximum(0, right - left)
    overlap = wh[:, 0] * wh[:, 1]
    area_one = max(0, one[2] - one[0]) * max(0, one[3] - one[1])
    area_many = np.maximum(0, many[:, 2] - many[:, 0]) * np.maximum(0, many[:, 3] - many[:, 1])
    return overlap / np.maximum(1e-6, area_one + area_many - overlap)


def _nms(boxes, scores, threshold):
    order = scores.argsort()[::-1]
    keep = []
    while order.size:
        current = order[0]
        keep.append(current)
        if order.size == 1:
            break
        order = order[1:][_iou(boxes[current], boxes[order[1:]]) <= threshold]
    return np.asarray(keep, dtype=np.int64)


class Detector:
    """NanoDet inference through ONNX Runtime, kept independent of OpenCV."""

    def __init__(self, model_path, confidence=.35, iou=.6):
        import onnxruntime as ort
        options = ort.SessionOptions()
        options.log_severity_level = 3
        options.intra_op_num_threads = min(8, max(1, __import__('os').cpu_count() or 4))
        self.session = ort.InferenceSession(str(model_path), sess_options=options,
                                            providers=['CPUExecutionProvider'])
        self.input_name = self.session.get_inputs()[0].name
        self.output_names = [o.name for o in self.session.get_outputs()]
        self.confidence = confidence
        self.iou = iou
        self.strides = (8, 16, 32, 64)
        self.image_size = 416
        self.reg_max = 7
        self.project = np.arange(self.reg_max + 1, dtype=np.float32)
        self.anchors = []
        for stride in self.strides:
            size = self.image_size // stride
            x, y = np.meshgrid(np.arange(size) * stride, np.arange(size) * stride)
            self.anchors.append(np.column_stack(((x.flatten() + .5 * (stride - 1)),
                                                  (y.flatten() + .5 * (stride - 1)))))

    def _prepare(self, image):
        image = image.convert('RGB')
        width, height = image.size
        scale = min(self.image_size / width, self.image_size / height)
        fitted = image.resize((max(1, round(width * scale)), max(1, round(height * scale))), Image.Resampling.BILINEAR)
        canvas = Image.new('RGB', (self.image_size, self.image_size), (0, 0, 0))
        left = (self.image_size - fitted.width) // 2
        top = (self.image_size - fitted.height) // 2
        canvas.paste(fitted, (left, top))
        data = np.asarray(canvas, dtype=np.float32)
        data = (data - np.array([103.53, 116.28, 123.675], dtype=np.float32)) / np.array([57.375, 57.12, 58.395], dtype=np.float32)
        return np.ascontiguousarray(data.transpose(2, 0, 1)[None]), (scale, left, top, width, height)

    def detect(self, image):
        blob, geometry = self._prepare(image)
        outputs = self.session.run(self.output_names, {self.input_name: blob})
        # Current ONNX model exposes three classification maps followed by three
        # distance maps. Fall back to shape-based grouping for future revisions.
        cls = [value for value in outputs if value.shape[-1] == len(CLASSES)]
        reg = [value for value in outputs if value.shape[-1] == 4 * (self.reg_max + 1)]
        boxes_all, scores_all = [], []
        for stride, scores, distances, anchors in zip(self.strides, cls, reg, self.anchors):
            scores = scores.squeeze(0)
            distances = distances.squeeze(0)
            if scores.shape[0] > 1000:
                top = scores.max(axis=1).argsort()[::-1][:1000]
                scores, distances, anchors = scores[top], distances[top], anchors[top]
            distribution = _softmax(distances.reshape(-1, self.reg_max + 1))
            distances = (distribution @ self.project).reshape(-1, 4) * stride
            boxes = np.column_stack((anchors[:, 0] - distances[:, 0], anchors[:, 1] - distances[:, 1],
                                     anchors[:, 0] + distances[:, 2], anchors[:, 1] + distances[:, 3]))
            boxes_all.append(np.clip(boxes, 0, self.image_size))
            scores_all.append(scores)
        boxes = np.concatenate(boxes_all)
        scores = np.concatenate(scores_all)
        class_ids = scores.argmax(axis=1)
        confidence = scores.max(axis=1)
        valid = confidence >= self.confidence
        boxes, confidence, class_ids = boxes[valid], confidence[valid], class_ids[valid]
        if not len(boxes):
            return []
        # Per-class NMS prevents adjacent objects of different classes suppressing
        # each other. Limit the stored set because search needs labels, not every box.
        kept = []
        for class_id in np.unique(class_ids):
            indices = np.where(class_ids == class_id)[0]
            kept.extend(indices[_nms(boxes[indices], confidence[indices], self.iou)].tolist())
        kept = sorted(kept, key=lambda i: confidence[i], reverse=True)[:30]
        scale, left, top, width, height = geometry
        detections = []
        for i in kept:
            x1, y1, x2, y2 = boxes[i]
            x1, x2 = np.clip([(x1 - left) / scale, (x2 - left) / scale], 0, width)
            y1, y2 = np.clip([(y1 - top) / scale, (y2 - top) / scale], 0, height)
            if x2 <= x1 or y2 <= y1:
                continue
            area = ((x2 - x1) * (y2 - y1)) / max(1, width * height)
            bottom = y2 / max(1, height)
            if area >= .18 or (area >= .08 and bottom >= .72):
                layer = 'foreground'
            elif area <= .035 or bottom <= .45:
                layer = 'background'
            else:
                layer = 'midground'
            detections.append({'label': CLASSES[int(class_ids[i])], 'confidence': round(float(confidence[i]), 3),
                               'layer': layer, 'box': [round(float(v), 1) for v in (x1, y1, x2, y2)]})
        return detections


def compact_keywords(detections, limit=5):
    layers = {'foreground': [], 'midground': [], 'background': []}
    for detection in sorted(detections, key=lambda d: d['confidence'], reverse=True):
        names = layers[detection['layer']]
        if detection['label'] not in names and len(names) < limit:
            names.append(detection['label'])
    return layers


def searchable_words(keyword_layers):
    words = set()
    for layer, labels in keyword_layers.items():
        words.add(layer)
        for item in labels:
            words.add(item)
            words.update(ALIASES.get(item, ()))
    return sorted(words)
