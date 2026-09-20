"""Fluid, evidence-linked exploration of Tracer's existing local index."""
from collections import Counter, defaultdict, deque
import math
from pathlib import Path
import re
import time

from PySide6.QtCore import Qt, QPointF, QRectF, QTimer, Signal
from PySide6.QtGui import (QBrush, QColor, QFont, QPainter, QPen,
                           QRadialGradient)
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QWidget

import paper_edit


COLORS = {
    'file': '#edf2f3',
    'word': '#5fdce7',
    'visual': '#91bfa0',
    'speaker': '#d0b47f',
    'collection': '#b8a7d1',
}


def build_graph(state, limit=180):
    """Build a deterministic graph and attach comparable data-derived mass."""
    nodes, edges, evidence = {}, [], defaultdict(list)
    counts = Counter()
    records = sorted(
        state.get('results', []),
        key=lambda record: (len(record.get('segments', [])) +
                            len(record.get('visual_index', {}).get('frames', []))),
        reverse=True,
    )[:90]

    for record in records:
        rid = str(record.get('id', record.get('source', '')))
        key = 'file:' + rid
        nodes[key] = {
            'id': key,
            'label': Path(record.get('source', '')).name,
            'kind': 'file',
            'weight': 1,
            'record': rid,
            'time': 0,
        }
        local = Counter()
        for segment in record.get('segments', []):
            for word in re.findall(r"\b[^\W_]{3,}\b", segment.get('text', '').casefold()):
                if word not in paper_edit.STOPWORDS:
                    token = 'word:' + word
                    local[token] += 1
                    if len(evidence[token]) < 30:
                        evidence[token].append((rid, float(segment.get('start', 0)),
                                                segment.get('text', '')[:160]))
            if segment.get('speaker'):
                local['speaker:' + segment['speaker']] += 1
        for frame in record.get('visual_index', {}).get('frames', []):
            labels = set(frame.get('search_words', []))
            labels.update(detection.get('label', '') for detection in frame.get('detections', []))
            for label in labels:
                if label:
                    token = 'visual:' + label
                    local[token] += 1
                    if len(evidence[token]) < 30:
                        evidence[token].append((rid, float(frame.get('time', 0)),
                                                'Scene signal: ' + label))
        for document in state.get('paper_edits', []):
            if document.get('result_id') == rid:
                for segment in document.get('segments', []):
                    speaker = segment.get('speaker', '').strip()
                    if speaker:
                        token = 'speaker:' + speaker
                        local[token] += 1
                        evidence[token].append((rid, float(segment.get('start', 0)),
                                                segment.get('text', '')[:160]))
        selected = [item for prefix in ('word:', 'visual:', 'speaker:')
                    for item in [(token, weight) for token, weight in local.most_common()
                                 if token.startswith(prefix)][:8]]
        for token, weight in selected:
            counts[token] += weight
            edges.append((key, token))
        nodes[key]['weight'] = 1 + sum(local.values())

    for token, weight in counts.most_common(limit):
        kind, label = token.split(':', 1)
        proof = evidence.get(token, [])
        nodes[token] = {
            'id': token,
            'label': label,
            'kind': kind,
            'weight': weight,
            'record': proof[0][0] if proof else None,
            'time': proof[0][1] if proof else 0,
            'evidence': proof,
        }

    for collection in state.get('collections', []):
        if collection.get('builtin'):
            continue
        key = 'collection:' + collection['id']
        members = ['file:' + str(value) for value in collection.get('video_ids', [])
                   if 'file:' + str(value) in nodes]
        if members:
            nodes[key] = {
                'id': key,
                'label': collection['name'],
                'kind': 'collection',
                'weight': len(members),
            }
            edges.extend((key, member) for member in members)

    edges = [(left, right) for left, right in edges if left in nodes and right in nodes]
    degree = Counter(value for edge in edges for value in edge)
    kind_max = defaultdict(lambda: 1.0)
    for node in nodes.values():
        node['degree'] = degree[node['id']]
        node['mass'] = math.log1p(max(1, node['weight'])) * (1 + .24 * math.log1p(node['degree']))
        kind_max[node['kind']] = max(kind_max[node['kind']], node['mass'])
    for node in nodes.values():
        normalized = node['mass'] / kind_max[node['kind']]
        node['radius'] = 4.5 + 22.5 * math.pow(normalized, .68)

    return sorted(nodes.values(), key=lambda node: (-node['mass'], node['id'])), edges


class TranscapeMark(QWidget):
    """Compact orbit mark occupying the same visual scale as the Tracer symbol."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(22, 22)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QPen(QColor('#ecf2f3'), 1.25, Qt.SolidLine, Qt.RoundCap))
        painter.drawArc(2, 6, 18, 10, 18 * 16, 166 * 16)
        painter.drawArc(2, 6, 18, 10, 198 * 16, 164 * 16)
        painter.drawLine(6, 6, 6, 16)
        painter.drawLine(6, 6, 11, 6)
        painter.drawLine(6, 16, 11, 16)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor('#5fdce7'))
        painter.drawEllipse(16, 4, 4, 4)
        painter.drawEllipse(2, 14, 4, 4)


class Field(QWidget):
    selected = Signal(object)
    opened = Signal(object)

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.nodes, self.edges = build_graph(state)
        self.by_id = {node['id']: node for node in self.nodes}
        self.adjacency = defaultdict(set)
        for left, right in self.edges:
            self.adjacency[left].add(right)
            self.adjacency[right].add(left)
        self.positions = {}
        self.velocities = {}
        self.cluster_for = {}
        self.cluster_centres = {}
        self.reveal_at = {}
        self.label_alpha = defaultdict(float)
        self.zoom = 1.0
        self.pan = QPointF()
        self.hover = None
        self.focus = None
        self.cursor_point = None
        self.pan_drag = None
        self.node_drag = None
        self.moved = False
        self.started = time.monotonic()
        self.last_tick = self.started
        self.motion = True
        self.fitted = False
        self.setMouseTracking(True)
        self.setMinimumSize(300, 250)
        self.seed_layout()
        self.timer = QTimer(self)
        self.timer.setInterval(33)
        self.timer.timeout.connect(self.tick)
        self.timer.start()

    def seed_layout(self):
        if not self.nodes:
            return
        seed_count = min(4, max(1, round(math.sqrt(len(self.nodes)) / 3)))
        seeds = []
        for node in self.nodes:
            if not seeds or all(node['id'] not in self.adjacency[seed] for seed in seeds):
                seeds.append(node['id'])
            if len(seeds) >= seed_count:
                break
        for node in self.nodes:
            if len(seeds) >= seed_count:
                break
            if node['id'] not in seeds:
                seeds.append(node['id'])

        queue = deque()
        depth = {}
        for index, seed in enumerate(seeds):
            angle = -math.pi / 2 + index * 2 * math.pi / len(seeds)
            radius = 155 if len(seeds) > 1 else 0
            centre = QPointF(math.cos(angle) * radius, math.sin(angle) * radius * .62)
            self.cluster_centres[seed] = centre
            self.cluster_for[seed] = seed
            depth[seed] = 0
            queue.append(seed)
        while queue:
            current = queue.popleft()
            for neighbor in sorted(self.adjacency[current]):
                if neighbor not in depth:
                    depth[neighbor] = depth[current] + 1
                    self.cluster_for[neighbor] = self.cluster_for[current]
                    queue.append(neighbor)

        cluster_counts = Counter()
        for index, node in enumerate(self.nodes):
            node_id = node['id']
            cluster = self.cluster_for.get(node_id, seeds[index % len(seeds)])
            self.cluster_for[node_id] = cluster
            local_index = cluster_counts[cluster]
            cluster_counts[cluster] += 1
            angle = local_index * 2.399963229728653
            radius = 19 * math.sqrt(local_index)
            centre = self.cluster_centres[cluster]
            self.positions[node_id] = QPointF(centre.x() + math.cos(angle) * radius,
                                               centre.y() + math.sin(angle) * radius * .72)
            self.velocities[node_id] = QPointF()
            self.reveal_at[node_id] = .16 * depth.get(node_id, 1) + .025 * local_index

    def reveal_progress(self, node_id):
        if not self.motion:
            return 1.0
        value = (time.monotonic() - self.started - self.reveal_at.get(node_id, 0)) / .72
        value = max(0.0, min(1.0, value))
        return value * value * (3 - 2 * value)

    def tick(self):
        now = time.monotonic()
        dt = min(.05, max(.012, now - self.last_tick))
        self.last_tick = now
        if self.motion:
            self.simulate(dt)
        for node_idx, node in enumerate(self.nodes):
            point = self.screen(node['id'])
            distance = (math.hypot(point.x() - self.cursor_point.x(), point.y() - self.cursor_point.y())
                        if self.cursor_point is not None else 9999)
            proximity = max(0.0, 1.0 - distance / 155.0)
            target = proximity ** 1.5
            if node['id'] in (self.hover, self.focus):
                target = 1.0
            elif self.focus and node['id'] in self.adjacency[self.focus]:
                target = max(target, .72)
            elif node_idx < 5:
                target = max(target, .22)
            self.label_alpha[node['id']] += (target - self.label_alpha[node['id']]) * .16
        self.update()

    def simulate(self, dt):
        if not self.nodes:
            return
        forces = {node['id']: QPointF() for node in self.nodes}
        visible = [node for node in self.nodes if self.reveal_progress(node['id']) > .02]

        for left, right in self.edges:
            if left not in forces or right not in forces:
                continue
            delta = self.positions[right] - self.positions[left]
            distance = max(1.0, math.hypot(delta.x(), delta.y()))
            desired = 52 + self.by_id[left]['radius'] + self.by_id[right]['radius']
            strength = (distance - desired) * .010
            direction = QPointF(delta.x() / distance, delta.y() / distance)
            pull = QPointF(direction.x() * strength, direction.y() * strength)
            forces[left] += pull
            forces[right] -= pull

        for index, first in enumerate(visible):
            first_id = first['id']
            for second in visible[index + 1:]:
                second_id = second['id']
                delta = self.positions[second_id] - self.positions[first_id]
                distance = max(1.0, math.hypot(delta.x(), delta.y()))
                reach = 34 + first['radius'] + second['radius']
                if distance > 150:
                    continue
                force = min(2.4, (reach * reach) / (distance * distance) * .38)
                direction = QPointF(delta.x() / distance, delta.y() / distance)
                push = QPointF(direction.x() * force, direction.y() * force)
                forces[first_id] -= push
                forces[second_id] += push

        cursor_world = self.world(self.cursor_point) if self.cursor_point is not None else None
        for node in visible:
            node_id = node['id']
            cluster = self.cluster_centres[self.cluster_for[node_id]]
            forces[node_id] += (cluster - self.positions[node_id]) * .0018
            forces[node_id] += QPointF(-self.positions[node_id].x() * .0007,
                                       -self.positions[node_id].y() * .0007)
            if cursor_world is not None and node_id != self.node_drag:
                delta = self.positions[node_id] - cursor_world
                distance = max(1.0, math.hypot(delta.x(), delta.y()))
                reach = 150 / max(.25, self.zoom)
                if distance < reach:
                    strength = math.pow(1 - distance / reach, 2) * (3.4 + node['radius'] * .08)
                    forces[node_id] += QPointF(delta.x() / distance * strength,
                                               delta.y() / distance * strength)

        for node in visible:
            node_id = node['id']
            if node_id == self.node_drag:
                continue
            inertia = max(1.0, node['mass'] * .7)
            velocity = self.velocities[node_id]
            velocity = QPointF((velocity.x() + forces[node_id].x() / inertia) * .88,
                               (velocity.y() + forces[node_id].y() / inertia) * .88)
            self.velocities[node_id] = velocity
            self.positions[node_id] += velocity * (dt * 36)

    def screen(self, key):
        point = self.positions[key]
        return QPointF(self.width() / 2, self.height() / 2) + self.pan + point * self.zoom

    def world(self, point):
        if point is None:
            return QPointF()
        return (point - QPointF(self.width() / 2, self.height() / 2) - self.pan) / self.zoom

    def visible_nodes(self):
        return [node for node in self.nodes if self.reveal_progress(node['id']) > 0]

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.nodes and not self.fitted:
            extent = max(180, 38 * math.sqrt(len(self.nodes)))
            self.zoom = min(1.7, max(.28, min((self.width() - 160) / (extent * 2),
                                              (self.height() - 100) / (extent * 1.35))))
            self.fitted = True

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor('#020304'))

        elapsed = time.monotonic() - self.started
        if self.motion:
            for seed, centre in self.cluster_centres.items():
                delay = self.reveal_at.get(seed, 0)
                wave = max(0.0, elapsed - delay)
                if wave <= 0:
                    continue
                screen = QPointF(self.width() / 2, self.height() / 2) + self.pan + centre * self.zoom
                radius = min(430.0, 55 + wave * 145)
                gradient = QRadialGradient(screen, radius)
                gradient.setColorAt(0, QColor(16, 35, 38, min(24, round(wave * 18))))
                gradient.setColorAt(.55, QColor(7, 17, 19, min(14, round(wave * 10))))
                gradient.setColorAt(1, QColor(0, 0, 0, 0))
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(gradient))
                painter.drawEllipse(screen, radius, radius)

        visible = self.visible_nodes()
        visible_ids = {node['id'] for node in visible}
        neighbors = {self.focus}
        if self.focus:
            neighbors.update(self.adjacency[self.focus])

        for left, right in self.edges:
            if left not in visible_ids or right not in visible_ids:
                continue
            progress = min(self.reveal_progress(left), self.reveal_progress(right))
            highlighted = self.focus and self.focus in (left, right)
            alpha = round((170 if highlighted else 52) * progress)
            if self.focus and not highlighted:
                alpha = round(alpha * .18)
            painter.setPen(QPen(QColor(104, 170, 177, alpha), 1.35 if highlighted else .72))
            painter.drawLine(self.screen(left), self.screen(right))

        if self.cursor_point is not None:
            gradient = QRadialGradient(self.cursor_point, 150)
            gradient.setColorAt(0, QColor(95, 220, 229, 18))
            gradient.setColorAt(.45, QColor(95, 220, 229, 7))
            gradient.setColorAt(1, QColor(0, 0, 0, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawEllipse(self.cursor_point, 150, 150)

        label_boxes = []
        for node in visible:
            progress = self.reveal_progress(node['id'])
            depth_scale = .28 + .72 * progress + math.sin(progress * math.pi) * .06
            point = self.screen(node['id'])
            radius = node['radius'] * depth_scale
            color = QColor(COLORS[node['kind']])
            alpha = round(255 * progress)
            if self.focus and node['id'] not in neighbors:
                alpha = round(alpha * .18)
            color.setAlpha(alpha)
            painter.setBrush(color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(point, radius, radius)
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(color.red(), color.green(), color.blue(), round(alpha * .28)), 1))
            painter.drawEllipse(point, radius + 4, radius + 4)

            label_strength = self.label_alpha[node['id']] * progress
            if label_strength < .04:
                continue
            label_color = QColor(COLORS[node['kind']])
            label_color.setAlpha(round(235 * label_strength))
            painter.setPen(label_color)
            painter.setFont(QFont('Segoe UI', 9 if node['radius'] < 18 else 10,
                                  QFont.DemiBold if node['radius'] > 20 else QFont.Normal))
            box = QRectF(point.x() + radius + 7, point.y() - 11,
                         min(230, max(42, len(node['label']) * 6.4 + 12)), 38)
            if node['id'] in (self.hover, self.focus) or not any(box.intersects(old) for old in label_boxes):
                painter.drawText(box, Qt.TextWordWrap, node['label'][:64])
                label_boxes.append(box)

        if not self.nodes:
            painter.setPen(QColor('#8d9da0'))
            painter.drawText(self.rect(), Qt.AlignCenter,
                             'Your space is waiting.\nIndex footage in Tracer to reveal its connections.')

    def hit(self, point):
        for node in reversed(self.visible_nodes()):
            delta = point - self.screen(node['id'])
            radius = max(12, node['radius'] * self.reveal_progress(node['id']) + 5)
            if math.hypot(delta.x(), delta.y()) < radius:
                return node
        return None

    def mousePressEvent(self, event):
        self.moved = False
        if event.button() == Qt.MiddleButton:
            self.pan_drag = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        if event.button() == Qt.LeftButton:
            node = self.hit(event.position())
            self.node_drag = node['id'] if node else None
            event.accept()

    def mouseMoveEvent(self, event):
        self.cursor_point = event.position()
        if self.pan_drag is not None and event.buttons() & Qt.MiddleButton:
            delta = event.position() - self.pan_drag
            self.pan += delta
            self.pan_drag = event.position()
            self.moved = self.moved or delta.manhattanLength() > 2
        elif self.node_drag and event.buttons() & Qt.LeftButton:
            target = self.world(event.position())
            delta = target - self.positions[self.node_drag]
            self.positions[self.node_drag] = target
            self.velocities[self.node_drag] = QPointF()
            self.moved = self.moved or delta.manhattanLength() > 1
        node = self.hit(event.position())
        self.hover = node['id'] if node else None
        if self.pan_drag is None:
            self.setCursor(Qt.PointingHandCursor if node else Qt.ArrowCursor)
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.pan_drag = None
        elif event.button() == Qt.LeftButton:
            if not self.moved:
                node = self.hit(event.position())
                self.focus = node['id'] if node else None
                self.selected.emit(node)
            self.node_drag = None
        self.setCursor(Qt.PointingHandCursor if self.hover else Qt.ArrowCursor)
        self.update()

    def mouseDoubleClickEvent(self, event):
        node = self.hit(event.position())
        if node and node.get('record'):
            self.opened.emit(node)

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.cursor_point = None
        self.hover = None

    def wheelEvent(self, event):
        anchor = event.position() - QPointF(self.width() / 2, self.height() / 2)
        old = self.zoom
        self.zoom = max(.22, min(4.2, old * (1.12 if event.angleDelta().y() > 0 else 1 / 1.12)))
        self.pan = anchor - (anchor - self.pan) * (self.zoom / old)
        self.update()
        event.accept()


class Transcape(QDialog):
    momentRequested = Signal(str, float)

    def __init__(self, state, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Tracer · Transcape')
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setStyleSheet('background: #020304; color: #e5eeee;')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setSpacing(9)
        lockup = QWidget()
        lockup.setFixedWidth(190)
        lockup_layout = QHBoxLayout(lockup)
        lockup_layout.setContentsMargins(0, 0, 0, 0)
        lockup_layout.setSpacing(9)
        lockup_layout.addWidget(TranscapeMark())
        logo = QLabel('TRACESCAPE')
        logo.setStyleSheet('font-size: 13px; font-weight: 700; letter-spacing: 2.2px; color: #edf2f3;')
        lockup_layout.addWidget(logo)
        lockup_layout.addStretch()
        header.addWidget(lockup)
        header.addStretch()
        layout.addLayout(header)

        self.field = Field(state)
        layout.addWidget(self.field, 1)
        self.detail = QLabel('')
        self.detail.setWordWrap(True)
        self.detail.setMaximumHeight(42)
        self.detail.setStyleSheet('color: #829296; font-size: 11px; padding-left: 4px;')
        layout.addWidget(self.detail)
        self.field.selected.connect(self.describe)
        self.field.opened.connect(self.open_moment)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
            event.accept()
            return
        super().keyPressEvent(event)

    def describe(self, node):
        if not node:
            self.detail.setText('')
            return
        evidence = node.get('evidence', [])
        excerpt = evidence[0][2] if evidence else 'Connected through indexed footage.'
        self.detail.setText(f"{node['label']}  ·  {node['weight']} observations  ·  {node['degree']} connections\n{excerpt}")

    def open_moment(self, node):
        self.accept()
        self.momentRequested.emit(node['record'], node.get('time', 0))
