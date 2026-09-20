"""Local, evidence-linked exploration of Tracer's existing index."""
from collections import Counter, defaultdict
import math
from pathlib import Path
import re
import time

from PySide6.QtCore import Qt, QPointF, QRectF, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QIcon
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QCheckBox
import paper_edit

COLORS = {'file': '#e9edee', 'word': '#66dce4', 'visual': '#9bbf9d', 'speaker': '#d4bc91', 'collection': '#b9acce'}


def build_graph(state, limit=180):
    nodes, edges, evidence = {}, [], defaultdict(list)
    counts = Counter()
    records = state.get('results', [])
    # Bound rendering cost; show the scope instead of implying the whole index is visible.
    records = sorted(records, key=lambda r: len(r.get('segments', [])) + len(r.get('visual_index', {}).get('frames', [])), reverse=True)[:90]
    for record in records:
        rid = str(record.get('id', record.get('source', '')))
        key = 'file:' + rid
        nodes[key] = {'id': key, 'label': Path(record.get('source', '')).name, 'kind': 'file', 'weight': 1, 'record': rid, 'time': 0}
        local = Counter()
        for segment in record.get('segments', []):
            for word in re.findall(r"\b[^\W_]{3,}\b", segment.get('text', '').casefold()):
                if word not in paper_edit.STOPWORDS:
                    token = 'word:' + word
                    local[token] += 1
                    if len(evidence[token]) < 30:
                        evidence[token].append((rid, float(segment.get('start', 0)), segment.get('text', '')[:160]))
            if segment.get('speaker'):
                local['speaker:' + segment['speaker']] += 1
        for frame in record.get('visual_index', {}).get('frames', []):
            labels = set(frame.get('search_words', []))
            labels.update(d.get('label', '') for d in frame.get('detections', []))
            for label in labels:
                if label:
                    token = 'visual:' + label
                    local[token] += 1
                    if len(evidence[token]) < 30:
                        evidence[token].append((rid, float(frame.get('time', 0)), 'Detected visual label: ' + label))
        # Authored speaker labels are evidence too; no speaker identity is inferred.
        for document in state.get('paper_edits', []):
            if document.get('result_id') == rid:
                for segment in document.get('segments', []):
                    speaker = segment.get('speaker', '').strip()
                    if speaker:
                        token = 'speaker:' + speaker
                        local[token] += 1
                        evidence[token].append((rid, float(segment.get('start', 0)), segment.get('text', '')[:160]))
        selected = [item for kind in ('word:', 'visual:', 'speaker:')
                    for item in [(token, weight) for token, weight in local.most_common() if token.startswith(kind)][:8]]
        for token, weight in selected:
            counts[token] += weight
            edges.append((key, token))
        nodes[key]['weight'] = 1 + sum(local.values())
    for token, weight in counts.most_common(limit):
        kind, label = token.split(':', 1)
        proof = evidence.get(token, [])
        nodes[token] = {'id': token, 'label': label, 'kind': kind, 'weight': weight,
                        'record': proof[0][0] if proof else None, 'time': proof[0][1] if proof else 0,
                        'evidence': proof}
    for collection in state.get('collections', []):
        if collection.get('builtin'):
            continue
        key = 'collection:' + collection['id']
        members = ['file:' + str(i) for i in collection.get('video_ids', []) if 'file:' + str(i) in nodes]
        if members:
            nodes[key] = {'id': key, 'label': collection['name'], 'kind': 'collection', 'weight': len(members)}
            edges.extend((key, member) for member in members)
    edges = [(a, b) for a, b in edges if a in nodes and b in nodes]
    return sorted(nodes.values(), key=lambda n: (-n['weight'], n['id'])), edges


class Field(QWidget):
    selected = Signal(object)
    opened = Signal(object)

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.nodes, self.edges = build_graph(state)
        self.positions = {}
        self.zoom = 1.0
        self.pan = QPointF()
        self.hover = None
        self.focus = None
        self.drag = None
        self.moved = False
        self.started = time.monotonic()
        self.motion = True
        self.fitted = False
        self.setMouseTracking(True)
        self.setMinimumSize(300, 250)
        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        for i, node in enumerate(self.nodes):
            angle = i * 2.399963229728653
            radius = 42 * math.sqrt(i)
            self.positions[node['id']] = QPointF(math.cos(angle) * radius, math.sin(angle) * radius * .7)

    def tick(self):
        self.update()
        if time.monotonic() - self.started > 5:
            self.timer.stop()

    def screen(self, key):
        p = self.positions[key]
        return QPointF(self.width() / 2, self.height() / 2) + self.pan + p * self.zoom

    def visible_nodes(self):
        count = len(self.nodes) if not self.motion else min(len(self.nodes), 3 + int((time.monotonic() - self.started) * 75))
        return self.nodes[:count]

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.nodes and not self.fitted:
            radius = 42 * math.sqrt(len(self.nodes))
            self.zoom = min(2.6, max(.3, min((self.width()-180)/(2*radius), (self.height()-120)/(1.4*radius))))
            self.fitted = True

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.fillRect(self.rect(), QColor('#050708'))
        visible = self.visible_nodes()
        ids = {n['id'] for n in visible}
        neighbors = {self.focus}
        if self.focus:
            for a, b in self.edges:
                if self.focus in (a, b):
                    neighbors.update((a, b))
        for a, b in self.edges:
            if a in ids and b in ids:
                highlighted = self.focus and self.focus in (a, b)
                p.setPen(QPen(QColor('#689196' if highlighted else '#202a2d'), 1.3 if highlighted else .65))
                p.drawLine(self.screen(a), self.screen(b))
        label_boxes = []
        for i, node in enumerate(visible):
            point = self.screen(node['id'])
            radius = min(17, 3 + math.log2(1 + node['weight']) * 1.7)
            color = QColor(COLORS[node['kind']])
            if self.focus and node['id'] not in neighbors:
                color.setAlpha(50)
            p.setBrush(color)
            p.setPen(Qt.NoPen)
            p.drawEllipse(point, radius, radius)
            if node['id'] in (self.hover, self.focus) or (i < 22 and not self.focus) or (self.focus and node['id'] in neighbors):
                p.setPen(color)
                p.setFont(QFont('Segoe UI', 10))
                box = QRectF(point.x()+radius+6, point.y()-10, min(210, len(node['label'])*7+10), 34)
                if node['id'] in (self.hover, self.focus) or not any(box.intersects(old) for old in label_boxes):
                    p.drawText(box, Qt.TextWordWrap, node['label'][:55])
                    label_boxes.append(box)
        if not self.nodes:
            p.setPen(QColor('#b0bfc1'))
            p.drawText(self.rect(), Qt.AlignCenter, 'Your space is waiting.\nIndex footage in Tracer to reveal its connections.')

    def hit(self, point):
        for node in reversed(self.visible_nodes()):
            delta = point - self.screen(node['id'])
            if math.hypot(delta.x(), delta.y()) < 20:
                return node
        return None

    def mousePressEvent(self, event):
        self.drag = event.position()
        self.moved = False

    def mouseMoveEvent(self, event):
        if self.drag is not None and event.buttons() & Qt.LeftButton:
            delta = event.position() - self.drag
            self.pan += delta
            self.drag = event.position()
            self.moved = self.moved or delta.manhattanLength() > 2
        node = self.hit(event.position())
        self.hover = node['id'] if node else None
        self.setCursor(Qt.PointingHandCursor if node else Qt.OpenHandCursor)
        self.setToolTip(node['label'] if node else '')
        self.update()

    def mouseReleaseEvent(self, event):
        if not self.moved:
            node = self.hit(event.position())
            self.focus = node['id'] if node else None
            self.selected.emit(node)
        self.drag = None
        self.update()

    def mouseDoubleClickEvent(self, event):
        node = self.hit(event.position())
        if node and node.get('record'):
            self.opened.emit(node)

    def wheelEvent(self, event):
        anchor = event.position() - QPointF(self.width()/2, self.height()/2)
        old = self.zoom
        self.zoom = max(.25, min(4, old * (1.12 if event.angleDelta().y() > 0 else 1/1.12)))
        self.pan = anchor - (anchor - self.pan) * (self.zoom / old)
        self.update()


class Transcape(QDialog):
    momentRequested = Signal(str, float)

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Tracer · Transcape')
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setStyleSheet('background: #050708; color: #e5eeee;')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 22, 28, 20)
        header = QHBoxLayout()
        logo = QLabel('T R A N S C A P E')
        logo.setStyleSheet('font-size: 20px; font-weight: 600; letter-spacing: 4px;')
        header.addWidget(logo)
        header.addStretch()
        motion = QCheckBox('Animate emergence')
        motion.setChecked(True)
        header.addWidget(motion)
        reset = QPushButton('Reset view')
        header.addWidget(reset)
        close = QPushButton('Back to Tracer · Esc')
        close.clicked.connect(self.reject)
        header.addWidget(close)
        layout.addLayout(header)
        self.field = Field(state)
        motion.toggled.connect(lambda enabled: (setattr(self.field, 'motion', enabled), self.field.update()))
        reset.clicked.connect(self.reset)
        layout.addWidget(self.field, 1)
        self.detail = QLabel('Select a node to follow connections. Double-click to open its source moment.')
        self.detail.setWordWrap(True)
        layout.addWidget(self.detail)
        legend = QLabel('FILES  ·  TRANSCRIPT WORDS  ·  VISUAL LABELS  ·  SPEAKERS  ·  COLLECTIONS     /     Drag to travel · Scroll to zoom')
        legend.setStyleSheet('color: #899a9d; font-size: 11px;')
        layout.addWidget(legend)
        scope = QLabel(f"{len(self.field.nodes)} nodes from up to 90 indexed files · Connections mean shared source evidence; size reflects frequency.")
        scope.setStyleSheet('color: #718083; font-size: 11px;')
        layout.addWidget(scope)
        self.field.selected.connect(self.describe)
        self.field.opened.connect(self.open_moment)

    def reset(self):
        self.field.pan = QPointF()
        self.field.zoom = 1
        self.field.focus = None
        self.field.update()

    def describe(self, node):
        if not node:
            self.detail.setText('Select a node to follow connections.')
            return
        evidence = node.get('evidence', [])
        excerpt = evidence[0][2] if evidence else 'Connected through your indexed footage.'
        self.detail.setText(f"{node['label']}  /  {node['kind']}  /  {node['weight']} observations\n{excerpt}")

    def open_moment(self, node):
        self.accept()
        self.momentRequested.emit(node['record'], node.get('time', 0))
