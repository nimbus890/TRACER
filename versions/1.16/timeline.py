from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import uuid
import xml.etree.ElementTree as ET

from PySide6.QtCore import Qt, Signal, QSize, QMimeData, QPoint
from PySide6.QtGui import QColor, QDrag, QFont, QPainter, QPen, QBrush, QKeySequence, QPixmap
from PySide6.QtWidgets import QListWidget, QTabBar, QWidget, QTreeWidget


MEDIA_MIME = 'application/x-tracer-media'
SEQUENCE_MIME = 'application/x-tracer-sequence'
TRACK_HEIGHT = 58
RULER_HEIGHT = 28
TRACK_HEADER = 116


def new_sequence(name='Sequence 1'):
    return {
        'id': uuid.uuid4().hex,
        'name': name,
        'frame_rate': 25,
        'width': 1920,
        'height': 1080,
        'tracks': [
            {'id': uuid.uuid4().hex, 'name': 'V2', 'type': 'video', 'visible': True, 'locked': False, 'clips': []},
            {'id': uuid.uuid4().hex, 'name': 'V1', 'type': 'video', 'visible': True, 'locked': False, 'clips': []},
            {'id': uuid.uuid4().hex, 'name': 'A1', 'type': 'audio', 'muted': False, 'solo': False, 'locked': False, 'clips': []},
            {'id': uuid.uuid4().hex, 'name': 'A2', 'type': 'audio', 'muted': False, 'solo': False, 'locked': False, 'clips': []},
        ],
    }


def ensure_project_editing(project):
    """Migrate a pre-1.14 project to the editing-room data model in place."""
    sequences = project.setdefault('sequences', [])
    if not sequences:
        sequences.append(new_sequence())
    for sequence in sequences:
        sequence.setdefault('id', uuid.uuid4().hex)
        sequence.setdefault('name', 'Sequence')
        sequence.setdefault('frame_rate', 25)
        sequence.setdefault('width', 1920)
        sequence.setdefault('height', 1080)
        sequence.setdefault('tracks', new_sequence()['tracks'])
        sequence.setdefault('markers', [])
        for track in sequence['tracks']:
            track.setdefault('id', uuid.uuid4().hex)
            track.setdefault('clips', [])
            track.setdefault('locked', False)
    project.setdefault('export_queue', [])
    return project


def sequence_duration(sequence):
    return max((float(clip.get('end', 0)) for track in sequence.get('tracks', [])
                for clip in track.get('clips', [])), default=0.0)


def sequence_sources(sequence):
    seen, values = set(), []
    for track in sequence.get('tracks', []):
        for clip in track.get('clips', []):
            source = str(clip.get('source', ''))
            key = source.casefold()
            if source and key not in seen:
                seen.add(key)
                values.append(source)
    return values


def offline_sources(sequence):
    return [source for source in sequence_sources(sequence) if not Path(source).is_file()]


def clip_group(sequence, clip):
    """Return a selected clip and every A/V clip linked to it."""
    if not sequence or not clip:
        return []
    linked = clip.get('linked')
    matches = []
    for track_index, track in enumerate(sequence.get('tracks', [])):
        for value in track.get('clips', []):
            if value.get('id') == clip.get('id') or (linked and value.get('linked') == linked):
                matches.append((track_index, track, value))
    return matches


def clip_group_locked(sequence, clip):
    return any(track.get('locked') for _, track, _ in clip_group(sequence, clip))


def move_clip_group(sequence, clip, original_positions, requested_start):
    """Move a linked edit as one unit while keeping every clip at or after zero."""
    group = clip_group(sequence, clip)
    if not group or clip.get('id') not in original_positions:
        return 0.0
    selected_start = original_positions[clip['id']][0]
    delta = float(requested_start) - selected_start
    delta = max(delta, -min(original_positions[value['id']][0] for _, _, value in group))
    for _, _, value in group:
        start, end = original_positions[value['id']]
        value['start'] = round(start + delta, 4)
        value['end'] = round(end + delta, 4)
    return delta


def make_clip(source, duration, start=0.0, source_in=0.0, name=None, linked=None):
    available = max(0.04, float(duration) - float(source_in))
    return {
        'id': uuid.uuid4().hex,
        'name': name or Path(source).name,
        'source': str(source),
        'start': round(float(start), 4),
        'end': round(float(start) + available, 4),
        'source_in': round(float(source_in), 4),
        'source_out': round(float(source_in) + available, 4),
        'linked': linked,
    }


def _rate(parent, fps):
    rate = ET.SubElement(parent, 'rate')
    ET.SubElement(rate, 'timebase').text = str(round(float(fps)))
    ET.SubElement(rate, 'ntsc').text = 'FALSE'


def final_cut_xml(sequence):
    """Return a compact FCP 7 XML timeline that Premiere can import."""
    fps = max(1, round(float(sequence.get('frame_rate', 25))))
    root = ET.Element('xmeml', version='5')
    seq = ET.SubElement(root, 'sequence', id='sequence-' + sequence['id'])
    ET.SubElement(seq, 'name').text = sequence.get('name', 'Sequence')
    ET.SubElement(seq, 'duration').text = str(round(sequence_duration(sequence) * fps))
    _rate(seq, fps)
    media = ET.SubElement(seq, 'media')
    file_ids = {}
    for kind in ('video', 'audio'):
        media_node = ET.SubElement(media, kind)
        if kind == 'video':
            fmt = ET.SubElement(media_node, 'format')
            sample = ET.SubElement(fmt, 'samplecharacteristics')
            ET.SubElement(sample, 'width').text = str(sequence.get('width', 1920))
            ET.SubElement(sample, 'height').text = str(sequence.get('height', 1080))
            _rate(sample, fps)
        for track in (t for t in sequence.get('tracks', []) if t.get('type') == kind):
            track_node = ET.SubElement(media_node, 'track')
            if kind == 'video':
                ET.SubElement(track_node, 'enabled').text = 'TRUE' if track.get('visible', True) else 'FALSE'
            else:
                ET.SubElement(track_node, 'enabled').text = 'FALSE' if track.get('muted') else 'TRUE'
            ET.SubElement(track_node, 'locked').text = 'TRUE' if track.get('locked') else 'FALSE'
            for clip in sorted(track.get('clips', []), key=lambda c: c.get('start', 0)):
                item = ET.SubElement(track_node, 'clipitem', id='clip-' + clip['id'])
                ET.SubElement(item, 'name').text = clip.get('name') or Path(clip['source']).name
                ET.SubElement(item, 'start').text = str(round(float(clip['start']) * fps))
                ET.SubElement(item, 'end').text = str(round(float(clip['end']) * fps))
                ET.SubElement(item, 'in').text = str(round(float(clip.get('source_in', 0)) * fps))
                ET.SubElement(item, 'out').text = str(round(float(clip.get('source_out', clip['end'] - clip['start'])) * fps))
                source = str(Path(clip['source']).resolve())
                file_id = file_ids.setdefault(source.casefold(), 'file-' + uuid.uuid5(uuid.NAMESPACE_URL, source).hex)
                file_node = ET.SubElement(item, 'file', id=file_id)
                if len([f for f in item.iter('pathurl')]) == 0:
                    ET.SubElement(file_node, 'name').text = Path(source).name
                    ET.SubElement(file_node, 'pathurl').text = Path(source).as_uri()
    ET.indent(root, space='  ')
    return '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE xmeml>\n' + ET.tostring(root, encoding='unicode')


def write_final_cut_xml(sequence, path):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + '.tmp')
    try:
        temporary.write_text(final_cut_xml(sequence), encoding='utf-8')
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return target


def collect_sequence_media(sequence, parent):
    """Collect used sources without overwriting same-named media."""
    parent = Path(parent)
    stem = ''.join(ch if ch.isalnum() or ch in ' -_' else '_' for ch in sequence.get('name', 'Sequence')).strip() or 'Sequence'
    target = parent / (stem + ' - Collected Media')
    suffix = 2
    while target.exists():
        target = parent / f'{stem} - Collected Media {suffix}'
        suffix += 1
    media_dir = target / 'Media'
    media_dir.mkdir(parents=True)
    used_names, manifest, replacements = set(), [], {}
    for source in sequence_sources(sequence):
        source_path = Path(source)
        if not source_path.is_file():
            manifest.append({'source': source, 'collected': None, 'status': 'offline'})
            continue
        name, index = source_path.name, 2
        while name.casefold() in used_names:
            name = f'{source_path.stem}_{index}{source_path.suffix}'
            index += 1
        used_names.add(name.casefold())
        destination = media_dir / name
        shutil.copy2(source_path, destination)
        replacements[source.casefold()] = str(destination)
        manifest.append({'source': source, 'collected': str(Path('Media') / name), 'status': 'copied'})
    collected_sequence = copy.deepcopy(sequence)
    for track in collected_sequence.get('tracks', []):
        for clip in track.get('clips', []):
            replacement = replacements.get(str(clip.get('source', '')).casefold())
            if replacement:
                clip['source'] = replacement
                clip['name'] = Path(replacement).name
    write_final_cut_xml(collected_sequence, target / (stem + '.xml'))
    (target / 'manifest.json').write_text(json.dumps({
        'sequence': sequence.get('name'), 'duration': sequence_duration(sequence), 'media': manifest,
    }, indent=2), encoding='utf-8')
    return target


class MediaBinList(QListWidget):
    def startDrag(self, supported_actions):
        item = self.currentItem()
        payload = item.data(Qt.UserRole) if item else None
        if not payload:
            return
        mime = QMimeData()
        mime.setData(MEDIA_MIME, json.dumps(payload).encode('utf-8'))
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.CopyAction)


class ProjectMediaTree(QTreeWidget):
    """One project-media surface for selection, processing, inspection, and timeline drag."""
    def startDrag(self, supported_actions):
        item = self.currentItem()
        payload = item.data(0, Qt.UserRole + 1) if item else None
        if not payload:
            return
        mime = QMimeData()
        mime.setData(MEDIA_MIME, json.dumps(payload).encode('utf-8'))
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec(Qt.CopyAction)


class SequenceTabBar(QTabBar):
    sequenceDropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._press = None
        self.setMovable(True)
        self.setExpanding(False)
        self.setDocumentMode(True)

    def mousePressEvent(self, event):
        self._press = event.position().toPoint()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._press is not None and (event.position().toPoint() - self._press).manhattanLength() > 12:
            index = self.tabAt(self._press)
            sequence_id = self.tabData(index) if index >= 0 else None
            if sequence_id:
                mime = QMimeData()
                mime.setData(SEQUENCE_MIME, str(sequence_id).encode('utf-8'))
                drag = QDrag(self)
                drag.setMimeData(mime)
                drag.exec(Qt.CopyAction)
                self._press = None
                return
        super().mouseMoveEvent(event)


class ExportQueueList(QListWidget):
    sequenceDropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(SEQUENCE_MIME):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(SEQUENCE_MIME):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat(SEQUENCE_MIME):
            self.sequenceDropped.emit(bytes(event.mimeData().data(SEQUENCE_MIME)).decode('utf-8'))
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


class TimelineCanvas(QWidget):
    changed = Signal()
    clipSelected = Signal(object)
    mediaDropped = Signal(object, float, int)
    commandRequested = Signal(str)
    editBlocked = Signal(str)
    zoomChanged = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sequence = None
        self.pixels_per_second = 10.0
        self.playhead = 0.0
        self.selected_id = None
        self.selected_track_index = 0
        self._drag = None
        self._scrubbing = False
        self.thumbnail_paths = {}
        self.thumbnails = {}
        self.setAcceptDrops(True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumHeight(250)

    def set_media_records(self, records):
        self.thumbnail_paths = {}
        for record in records:
            frames = record.get('frames', [])
            if frames:
                path = Path(frames[0].get('path') or frames[0].get('file') or '')
                if not path.is_absolute():
                    path = Path(record.get('output', '')) / path
                self.thumbnail_paths[str(record.get('source', '')).casefold()] = str(path)

    def thumbnail(self, source):
        path = self.thumbnail_paths.get(str(source).casefold())
        if not path:
            return None
        if path not in self.thumbnails:
            if len(self.thumbnails) >= 128:
                self.thumbnails.clear()
            self.thumbnails[path] = QPixmap(path).scaled(84, 46, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        value = self.thumbnails[path]
        return None if value.isNull() else value

    def set_sequence(self, sequence):
        self.sequence = sequence
        self.selected_id = None
        self.selected_track_index = 0
        self._resize_canvas()
        self.update()

    def sizeHint(self):
        tracks = len(self.sequence.get('tracks', [])) if self.sequence else 4
        return QSize(900, RULER_HEIGHT + tracks * TRACK_HEIGHT + 6)

    def _resize_canvas(self):
        if self.sequence:
            width = max(self.parentWidget().width() if self.parentWidget() else 800,
                        round(TRACK_HEADER + (sequence_duration(self.sequence) + 12) * self.pixels_per_second))
            self.setMinimumWidth(width)
            self.setMinimumHeight(RULER_HEIGHT + len(self.sequence.get('tracks', [])) * TRACK_HEIGHT + 4)

    def set_zoom(self, value):
        new_value = max(2.0, min(80.0, float(value)))
        changed = abs(new_value - self.pixels_per_second) > .001
        self.pixels_per_second = new_value
        self._resize_canvas()
        self.update()
        if changed:
            self.zoomChanged.emit(self.pixels_per_second)

    def fit(self, available_width):
        duration = max(10.0, sequence_duration(self.sequence) if self.sequence else 10.0)
        self.set_zoom(max(2.0, (available_width - TRACK_HEADER - 24) / duration))

    def selected_clip(self):
        if not self.sequence or not self.selected_id:
            return None, None
        for track_index, track in enumerate(self.sequence.get('tracks', [])):
            for clip in track.get('clips', []):
                if clip.get('id') == self.selected_id:
                    return track_index, clip
        return None, None

    def _clip_rect(self, track_index, clip):
        x = TRACK_HEADER + float(clip.get('start', 0)) * self.pixels_per_second
        width = max(8.0, (float(clip.get('end', 0)) - float(clip.get('start', 0))) * self.pixels_per_second)
        y = RULER_HEIGHT + track_index * TRACK_HEIGHT + 5
        return x, y, width, TRACK_HEIGHT - 10

    def _hit(self, point):
        if not self.sequence:
            return None, None
        for index, track in enumerate(self.sequence.get('tracks', [])):
            for clip in reversed(track.get('clips', [])):
                x, y, width, height = self._clip_rect(index, clip)
                if x <= point.x() <= x + width and y <= point.y() <= y + height:
                    return index, clip
        return None, None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor('#151c21'))
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(0, 0, self.width(), RULER_HEIGHT, QColor('#212a31'))
        painter.fillRect(0, 0, TRACK_HEADER, self.height(), QColor('#1b2329'))
        if not self.sequence:
            painter.setPen(QColor('#99958e'))
            painter.drawText(self.rect(), Qt.AlignCenter, 'Create or select a sequence')
            return
        duration = max(sequence_duration(self.sequence) + 10, (self.width() - TRACK_HEADER) / self.pixels_per_second)
        step = 1 if self.pixels_per_second >= 24 else 5 if self.pixels_per_second >= 7 else 10
        painter.setFont(QFont('Segoe UI', 8))
        for second in range(0, int(duration) + step, step):
            x = round(TRACK_HEADER + second * self.pixels_per_second)
            painter.setPen(QPen(QColor('#4a4742'), 1))
            painter.drawLine(x, RULER_HEIGHT - 7, x, self.height())
            painter.setPen(QColor('#99958e'))
            painter.drawText(x + 3, 16, f'{second // 60}:{second % 60:02d}')
        for index, track in enumerate(self.sequence.get('tracks', [])):
            y = RULER_HEIGHT + index * TRACK_HEIGHT
            painter.fillRect(0, y, self.width(), TRACK_HEIGHT,
                             QColor('#192128' if index % 2 else '#161d23'))
            if index == self.selected_track_index:
                painter.fillRect(0, y, TRACK_HEADER, TRACK_HEIGHT, QColor('#2a2522'))
            painter.setPen(QPen(QColor('#302e2b'), 1))
            painter.drawLine(0, y + TRACK_HEIGHT - 1, self.width(), y + TRACK_HEIGHT - 1)
            painter.setPen(QColor('#eee8df'))
            painter.setFont(QFont('Segoe UI', 9, QFont.DemiBold))
            painter.drawText(10, y + 23, track.get('name', 'Track'))
            state = ('LOCK' if track.get('locked') else
                     'MUTE' if track.get('type') == 'audio' and track.get('muted') else
                     'HIDE' if track.get('type') == 'video' and not track.get('visible', True) else 'ON')
            painter.setFont(QFont('Segoe UI', 7))
            painter.setPen(QColor('#8f8b84'))
            painter.drawText(10, y + 41, state)
            for clip in track.get('clips', []):
                x, cy, width, height = self._clip_rect(index, clip)
                selected = clip.get('id') == self.selected_id
                offline = not Path(str(clip.get('source', ''))).is_file()
                base = QColor('#8a4549' if offline else '#55799a' if track.get('type') == 'video' else '#66806e')
                if selected:
                    base = QColor('#9b653d' if track.get('type') == 'video' else '#356f67')
                painter.setPen(QPen(QColor('#f1ece4') if selected else base.lighter(135), 2 if selected else 1))
                painter.setBrush(QBrush(base))
                painter.drawRoundedRect(round(x), round(cy), round(width), round(height), 3, 3)
                painter.setClipRect(round(x + 5), round(cy), max(0, round(width - 10)), round(height))
                thumb = self.thumbnail(clip.get('source')) if track.get('type') == 'video' else None
                text_x = x + 7
                if thumb and width > 110:
                    painter.drawPixmap(round(x + 2), round(cy + 2), thumb)
                    text_x = x + 91
                painter.setPen(QColor('#f6f2eb'))
                painter.setFont(QFont('Segoe UI', 8, QFont.DemiBold))
                painter.drawText(round(text_x), round(cy + 19), clip.get('name', 'Clip'))
                painter.setFont(QFont('Segoe UI', 7))
                painter.drawText(round(text_x), round(cy + 36),
                                 f"{float(clip.get('end', 0)) - float(clip.get('start', 0)):.1f}s")
                painter.setClipping(False)
        for marker in self.sequence.get('markers', []):
            mx = TRACK_HEADER + float(marker.get('time', 0)) * self.pixels_per_second
            painter.setPen(QPen(QColor('#d78061'), 1))
            painter.drawLine(round(mx), 0, round(mx), self.height())
            painter.setBrush(QColor('#d78061'))
            painter.drawPolygon([QPoint(round(mx) - 4, 0), QPoint(round(mx) + 4, 0), QPoint(round(mx), 7)])
        px = TRACK_HEADER + self.playhead * self.pixels_per_second
        painter.setPen(QPen(QColor('#f1ece4'), 1.5))
        painter.drawLine(round(px), 0, round(px), self.height())
        painter.setBrush(QColor('#f1ece4'))
        painter.setPen(Qt.NoPen)
        painter.drawPolygon([QPoint(round(px) - 5, 0), QPoint(round(px) + 5, 0), QPoint(round(px), 7)])

    def mousePressEvent(self, event):
        self.setFocus()
        self._scrubbing = event.button() == Qt.LeftButton and event.position().y() < RULER_HEIGHT and event.position().x() >= TRACK_HEADER
        index, clip = self._hit(event.position())
        if clip:
            self.selected_id = clip['id']
            self.selected_track_index = index
            self.clipSelected.emit(clip)
            linked_positions = {
                value['id']: (float(value.get('start', 0)), float(value.get('end', 0)))
                for _, _, value in clip_group(self.sequence, clip)
            }
            self._drag = (event.position().x(), index, clip,
                          float(clip.get('start', 0)), float(clip.get('end', 0)), linked_positions)
        else:
            self.selected_id = None
            if event.position().x() < TRACK_HEADER and event.position().y() >= RULER_HEIGHT:
                self.selected_track_index = max(0, min(len(self.sequence.get('tracks', [])) - 1,
                    int((event.position().y() - RULER_HEIGHT) // TRACK_HEIGHT)))
            else:
                self.playhead = max(0.0, (event.position().x() - TRACK_HEADER) / self.pixels_per_second)
            self.clipSelected.emit(None)
        self.update()

    def mouseMoveEvent(self, event):
        if self._scrubbing and event.buttons() & Qt.LeftButton:
            self.playhead = max(0.0, (event.position().x() - TRACK_HEADER) / self.pixels_per_second)
            self.clipSelected.emit(None)
            self.update()
            return
        if not self._drag or not (event.buttons() & Qt.LeftButton) or not self.sequence:
            return
        press_x, old_index, clip, old_start, old_end, linked_positions = self._drag
        track = self.sequence['tracks'][old_index]
        if clip_group_locked(self.sequence, clip):
            self._drag = None
            self.editBlocked.emit('Unlock the linked clip tracks before moving this edit.')
            return
        delta = (event.position().x() - press_x) / self.pixels_per_second
        move_clip_group(self.sequence, clip, linked_positions, old_start + delta)
        target = int((event.position().y() - RULER_HEIGHT) // TRACK_HEIGHT)
        if 0 <= target < len(self.sequence['tracks']) and target != old_index:
            destination = self.sequence['tracks'][target]
            if destination.get('type') == track.get('type') and not destination.get('locked'):
                track['clips'].remove(clip)
                destination['clips'].append(clip)
                self._drag = (press_x, target, clip, old_start, old_end, linked_positions)
        self._resize_canvas()
        self.update()

    def mouseReleaseEvent(self, event):
        self._scrubbing = False
        if self._drag:
            _, _, clip, old_start, _, _ = self._drag
            moved = abs(float(clip.get('start', 0)) - old_start) > 0.001
            self._drag = None
            if moved:
                self.changed.emit()

    def mouseDoubleClickEvent(self, event):
        index, clip = self._hit(event.position())
        if clip:
            self.selected_id = clip['id']
            self.playhead = max(float(clip['start']), min(float(clip['end']),
                                (event.position().x() - TRACK_HEADER) / self.pixels_per_second))
            self.commandRequested.emit('split')
        else:
            super().mouseDoubleClickEvent(event)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.ControlModifier:
            self.set_zoom(self.pixels_per_second * (1.18 if event.angleDelta().y() > 0 else 0.85))
            event.accept()
        else:
            super().wheelEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.commandRequested.emit('delete')
        elif event.matches(QKeySequence.Copy):
            self.commandRequested.emit('copy')
        elif event.matches(QKeySequence.Cut):
            self.commandRequested.emit('cut')
        elif event.matches(QKeySequence.Paste):
            self.commandRequested.emit('paste')
        elif event.matches(QKeySequence.Undo):
            self.commandRequested.emit('undo')
        elif event.matches(QKeySequence.Redo):
            self.commandRequested.emit('redo')
        else:
            super().keyPressEvent(event)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(MEDIA_MIME):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(MEDIA_MIME):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat(MEDIA_MIME):
            payload = json.loads(bytes(event.mimeData().data(MEDIA_MIME)).decode('utf-8'))
            position = max(0.0, (event.position().x() - TRACK_HEADER) / self.pixels_per_second)
            track = max(0, int((event.position().y() - RULER_HEIGHT) // TRACK_HEIGHT))
            self.mediaDropped.emit(payload, position, track)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)
