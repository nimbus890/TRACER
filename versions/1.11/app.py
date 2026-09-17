from __future__ import annotations

import copy
import json
import math
import os
from pathlib import Path
import sys
import time
import uuid

from PySide6.QtCore import (Qt, QThread, Signal, QTimer, QUrl, QSize, QPoint, QLockFile, QEvent,
                            QPropertyAnimation, QEasingCurve, Property)
from PySide6.QtGui import (QColor, QDesktopServices, QFont, QFontDatabase, QIcon, QPixmap,
                           QPainter, QPen, QBrush)
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTreeWidget, QTreeWidgetItem, QHeaderView, QAbstractItemView,
    QStackedWidget, QFileDialog, QMessageBox, QDialog, QFormLayout, QComboBox,
    QCheckBox, QDoubleSpinBox, QSlider, QSpinBox, QLineEdit, QProgressBar,
    QSplitter, QListWidget, QListWidgetItem, QTextBrowser, QFrame, QScrollArea,
    QInputDialog, QButtonGroup, QToolButton, QToolTip, QGraphicsBlurEffect)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

import core


STYLE = '''
QWidget { background: #151515; color: #e8e3da; font-family: 'Segoe UI'; font-size: 13px; }
QDialog#processDialog { background: #171716; border: 1px solid #4c4842; border-radius: 8px; }
QDialog#processDialog QLabel, QDialog#processDialog QCheckBox { background: transparent; }
QDialog#processDialog QLabel#processTitle { font-size: 20px; font-weight: 600; color: #ded8cf; }
QMainWindow { background: #151515; }
QLabel#title { font-size: 25px; font-weight: 600; color: #f1ece4; }
QLabel#subtle { color: #99958e; }
QLabel#brand { font-size: 22px; font-weight: 650; color: #f0ebe2; }
QLabel#eyebrow { color: #d78061; font-size: 10px; font-weight: 700; letter-spacing: 1px; }
QLabel#metric { font-size: 22px; font-weight: 600; color: #f1ece4; }
QLabel#percent { font-size: 18px; font-weight: 650; color: #e08a68; }
QLabel:disabled { color: #615e58; }
QFrame#sidebar { background: #101010; border-right: 1px solid #302e2a; }
QFrame#sidebar QLabel { background: transparent; }
QFrame#card { background: #1d1d1c; border: 1px solid #34322f; border-radius: 4px; }
QFrame#card QLabel { background: transparent; }
QFrame#modelCell { background: #181817; border: 1px solid #34312e; border-radius: 4px; }
QFrame#modelCell QLabel { background: transparent; }
QPushButton { background: #252422; border: 1px solid #403d38; padding: 8px 14px; border-radius: 3px; font-weight: 550; }
QPushButton:hover { background: #302e2b; border-color: #777067; }
QPushButton:pressed { background: #3a3732; }
QPushButton:disabled { color: #66635e; background: #1b1b1a; border-color: #2a2927; }
QPushButton#primary { background: #c86f50; color: #16120f; border: 1px solid #e08a68; }
QPushButton#primary:hover { background: #df8060; }
QPushButton#primary:disabled { background: #493127; color: #846456; border-color: #53382d; }
QPushButton#processStart { background: #b8d9c3; color: #102018; border: 0; padding: 5px 12px; border-radius: 4px; font-weight: 750; }
QPushButton#processStart:hover { background: #cce8d4; }
QPushButton#processStart:pressed { background: #8bb99f; }
QPushButton#processStart:disabled { background: #29332d; color: #68766e; border-color: #39463e; }
QPushButton#processCancel { background: transparent; color: #f40009; border: 0; padding: 0; font-size: 32px; font-weight: 500; }
QPushButton#processCancel:hover { background: transparent; color: #ff4349; }
QPushButton#libraryPrimary { background: #9bbfce; color: #102128; border: 1px solid #b8d5df; font-weight: 650; }
QPushButton#libraryPrimary:hover { background: #b2d1dd; }
QPushButton#mediaIcon { background: #232321; border: 1px solid #484640; padding: 3px; border-radius: 4px; }
QPushButton#mediaIcon:hover { background: #30302d; border-color: #858078; }
QPushButton#danger { color: #d79882; }
QPushButton#segment { padding: 6px 12px; color: #aaa69f; background: #1d1d1c; }
QPushButton#segment:checked { color: #f4e9e1; background: #493128; border-color: #c86f50; }
QPushButton#segment:disabled { color: #625f59; background: #191918; border-color: #292826; }
QPushButton#formatLeft, QPushButton#formatRight { padding: 5px 10px; color: #aaa69f; background: #171716; border: 1px solid #45423e; }
QPushButton#formatLeft { border-radius: 4px 0 0 4px; border-right: 0; }
QPushButton#formatRight { border-radius: 0 4px 4px 0; }
QPushButton#formatLeft:checked, QPushButton#formatRight:checked { color: #16120f; background: #d28a6e; border-color: #d28a6e; font-weight: 700; }
QPushButton#formatLeft:disabled, QPushButton#formatRight:disabled { color: #57544f; background: #181817; border-color: #292826; }
QPushButton#nav { text-align: left; border: 0; border-left: 2px solid transparent; background: transparent; padding: 11px 13px; color: #aaa69f; }
QPushButton#nav:checked { color: #f2ece4; background: #201c19; border-left-color: #d78061; }
QTreeWidget, QListWidget, QTextBrowser { background: #191919; border: 1px solid #34322f; border-radius: 3px; outline: none; }
QTreeWidget::item { min-height:  34px; padding: 2px; }
QTreeWidget::item:selected, QListWidget::item:selected { background: #483128; color: #fff5ee; }
QListWidget::item { padding: 9px; border-bottom: 1px solid #302e2b; }
QHeaderView::section { background: #222120; color: #aaa69f; border: 0; border-bottom: 1px solid #3b3834; padding: 9px; font-weight: 600; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background: #20201f; border: 1px solid #46423d; border-radius: 3px; padding: 7px; min-height: 18px; }
QLineEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled { background: #191918; color: #625f59; border-color: #292826; }
QComboBox QAbstractItemView { background: #20201f; selection-background-color: #483128; }
QCheckBox { spacing: 9px; padding: 4px; }
QCheckBox::indicator { width: 17px; height: 17px; }
QWidget#transparentRow, QSlider { background: transparent; }
QSlider::groove:horizontal { height: 2px; background: #45433f; border: 0; }
QSlider::sub-page:horizontal { height: 2px; background: #aaa69e; border: 0; }
QSlider::handle:horizontal { background: #e8e2d9; border: 2px solid #151515; width: 12px; height: 12px; margin: -7px 0; border-radius: 7px; }
QSlider:disabled::groove:horizontal { background: #292826; }
QSlider:disabled::sub-page:horizontal { background: #3c3a37; }
QSlider:disabled::handle:horizontal { background: #595650; border-color: #191918; }
QProgressBar { background: #292826; color: #f4e6dc; border: 1px solid #3c3935; border-radius: 3px; min-height: 18px; text-align: center; font-size: 11px; font-weight: 600; }
QProgressBar::chunk { background: #b96346; border-radius: 2px; }
QScrollBar:vertical { background: #181818; width: 10px; }
QScrollBar::handle:vertical { background: #494641; min-height: 30px; border-radius: 4px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QToolTip { color: #eee8df; background: #302e2b; border: 1px solid #68625b; }
QSplitter::handle:horizontal { background: #3b3935; width: 4px; margin: 8px 1px; border-radius: 2px; }
QSplitter::handle:horizontal:hover { background: #d78061; }
QPushButton#advancedToggle { background: #1b1b1a; border-color: #393733; padding: 3px; }
QPushButton#advancedToggle:checked { color: #f0e8df; border-color: #7a746c; background: #252422; }
QFrame#saveArea { background: #211f1c; border: 1px solid #504940; border-radius: 5px; }
QFrame#saveArea QLabel, QFrame#saveArea QWidget { background: transparent; }
'''


def label(text, kind=None):
    w = QLabel(text)
    if kind:
        w.setObjectName(kind)
    return w


def button(text, callback=None, primary=False):
    b = QPushButton(text)
    if callback:
        b.clicked.connect(callback)
    if primary:
        b.setObjectName('primary')
    return b


def tile_icon(kind, colour_override=None):
    pixmap = QPixmap(44, 34)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    icon_colours = {'audio': '#c2addb', 'frame': '#94c1d3', 'ai': '#a7cdb5'}
    colour = colour_override or icon_colours.get(kind, '#d9a68f')
    pen = QPen(QColor(colour), 2.2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    if kind == 'audio':
        for x, height in zip((7, 13, 19, 25, 31, 37), (8, 17, 27, 21, 13, 7)):
            painter.drawLine(x, 17 - height // 2, x, 17 + height // 2)
    elif kind == 'frame':
        painter.drawRoundedRect(7, 6, 30, 22, 3, 3)
        painter.drawEllipse(17, 10, 10, 10)
        painter.drawLine(12, 6, 16, 2)
        painter.drawLine(16, 2, 24, 2)
    elif kind == 'ai':
        points = ((7, 17), (15, 7), (27, 10), (24, 23), (12, 25))
        for a, b in ((0, 1), (1, 2), (2, 3), (3, 4), (4, 0), (1, 4), (1, 3)):
            painter.drawLine(*points[a], *points[b])
        painter.setBrush(QBrush(QColor(colour)))
        for x, y in points:
            painter.drawEllipse(x - 1, y - 1, 3, 3)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(27, 18, 9, 9)
        painter.drawLine(34, 25, 40, 31)
    elif kind == 'settings':
        painter.drawEllipse(13, 8, 18, 18)
        painter.drawEllipse(19, 14, 6, 6)
        for x1, y1, x2, y2 in ((22, 3, 22, 8), (22, 26, 22, 31), (8, 17, 13, 17),
                               (31, 17, 36, 17), (12, 7, 16, 11), (28, 23, 32, 27),
                               (32, 7, 28, 11), (16, 23, 12, 27)):
            painter.drawLine(x1, y1, x2, y2)
    elif kind == 'cancel':
        painter.setPen(QPen(QColor('#f40009'), 2.8, Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(13, 8, 31, 26)
        painter.drawLine(31, 8, 13, 26)
    elif kind in ('list_left', 'list_right'):
        painter.drawLine(16, 9, 34, 9)
        painter.drawLine(16, 17, 34, 17)
        painter.drawLine(16, 25, 34, 25)
        if kind == 'list_left':
            painter.drawLine(11, 12, 6, 17)
            painter.drawLine(6, 17, 11, 22)
        else:
            painter.drawLine(37, 12, 42, 17)
            painter.drawLine(42, 17, 37, 22)
    elif kind == 'interval':
        painter.drawEllipse(11, 5, 22, 22)
        painter.drawLine(22, 5, 22, 1)
        painter.drawLine(18, 1, 26, 1)
        painter.drawLine(22, 16, 28, 11)
        painter.drawLine(22, 16, 22, 9)
    elif kind == 'scene':
        painter.drawRoundedRect(4, 7, 15, 21, 2, 2)
        painter.drawRoundedRect(25, 7, 15, 21, 2, 2)
        painter.drawLine(22, 5, 22, 30)
    elif kind == 'play':
        painter.drawLine(16, 8, 16, 26)
        painter.drawLine(16, 8, 31, 17)
        painter.drawLine(31, 17, 16, 26)
    elif kind == 'pause':
        painter.drawLine(17, 8, 17, 26)
        painter.drawLine(27, 8, 27, 26)
    painter.end()
    return QIcon(pixmap)


class MarkedSlider(QSlider):
    """A clean slider with a few deliberately marked recommendation stops."""
    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.recommended = []
        self.setMinimumHeight(25)

    def set_recommended(self, values):
        self.recommended = list(values)
        self.update()

    def paintEvent(self, event):
        if self.orientation() != Qt.Horizontal:
            super().paintEvent(event)
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        left, right = 8, max(8, self.width() - 8)
        y = self.height() // 2
        span = max(1, self.maximum() - self.minimum())
        ratio = (self.value() - self.minimum()) / span
        handle_x = round(left + ratio * (right - left))
        painter.setPen(QPen(QColor('#46443f' if self.isEnabled() else '#292826'), 2,
                            Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(left, y, right, y)
        painter.setPen(QPen(QColor('#aaa69e' if self.isEnabled() else '#3c3a37'), 2,
                            Qt.SolidLine, Qt.RoundCap))
        painter.drawLine(left, y, handle_x, y)
        painter.setPen(QPen(QColor('#85817a' if self.isEnabled() else '#403e3a'), 1.2,
                            Qt.SolidLine, Qt.RoundCap))
        for value in self.recommended:
            ratio = (value - self.minimum()) / span
            x = round(left + ratio * (right - left))
            painter.drawLine(x, y + 5, x, y + 9)
        painter.setPen(QPen(QColor('#151515' if self.isEnabled() else '#191918'), 2))
        painter.setBrush(QBrush(QColor('#e8e2d9' if self.isEnabled() else '#595650')))
        painter.drawEllipse(handle_x - 6, y - 6, 12, 12)
        painter.end()


class ChoiceTile(QToolButton):
    """A checkable output tile with a restrained animated colour transition."""
    def __init__(self, icon_kind, title, caption='', compact=False, icon_only=False, parent=None):
        super().__init__(parent)
        self._hover_text = title + (f' — {caption}' if caption else '')
        self._icon_only = icon_only
        self._icon_kind = icon_kind
        self.setText('' if icon_only else title + (f'\n{caption}' if caption else ''))
        self.setIcon(tile_icon(icon_kind))
        self.setIconSize(QSize(25, 21) if compact else QSize(26, 22) if icon_only else QSize(44, 34))
        self.setToolButtonStyle(Qt.ToolButtonIconOnly if icon_only else Qt.ToolButtonTextBesideIcon if compact else Qt.ToolButtonTextUnderIcon)
        self.setAccessibleName(title)
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        if icon_only:
            self.setFixedSize(44, 34)
        elif compact:
            self.setMinimumSize(102, 40)
            self.setMaximumHeight(42)
        else:
            self.setMinimumSize(150, 92)
        self._tone = 0.0
        self._animation = QPropertyAnimation(self, b'tone', self)
        self._animation.setDuration(190)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)
        self.toggled.connect(self._animate)
        self._apply_style()

    def enterEvent(self, event):
        super().enterEvent(event)
        QTimer.singleShot(300, self._show_hover_tip)

    def leaveEvent(self, event):
        QToolTip.hideText()
        super().leaveEvent(event)

    def _show_hover_tip(self):
        if self.underMouse():
            QToolTip.showText(self.mapToGlobal(self.rect().bottomLeft()), self.toolTip() or self._hover_text, self)

    def _animate(self, checked):
        self._animation.stop()
        self._animation.setStartValue(self._tone)
        self._animation.setEndValue(1.0 if checked else 0.0)
        self._animation.start()

    def get_tone(self):
        return self._tone

    def set_tone(self, value):
        self._tone = float(value)
        self._apply_style()

    tone = Property(float, get_tone, set_tone)

    def _apply_style(self):
        def mix(a, b):
            return round(a + (b - a) * self._tone)
        palettes = {
            'audio': ((81, 200, 249), (0, 0, 0)),
            'frame': ((249, 207, 88), (0, 0, 0)),
            'ai': ((32, 214, 102), (0, 0, 0)),
        }
        selected_bg, selected_ink = palettes.get(self._icon_kind, ((226, 196, 184), (91, 50, 37)))
        if self._icon_only:
            selected_ink = (0, 0, 0)
        accent = '#%02x%02x%02x' % selected_bg
        bg = '#%02x%02x%02x' % tuple(mix(a, b) for a, b in zip((12, 12, 12), selected_bg))
        border = '#%02x%02x%02x' % tuple(mix(a, b) for a, b in zip((48, 47, 44), selected_bg))
        foreground = '#%02x%02x%02x' % tuple(mix(a, b) for a, b in zip((166, 162, 155), selected_ink))
        icon_colour = '#%02x%02x%02x' % tuple(mix(a, b) for a, b in zip((190, 186, 180), selected_ink))
        self.setIcon(tile_icon(self._icon_kind, icon_colour))
        self.setStyleSheet(
            f'QToolButton {{ background:{bg}; color:{foreground}; border:1px solid {border}; '
            f'border-radius:4px; padding:{"3px" if self._icon_only else "7px"}; font-size:11px; font-weight:600; }} '
            f'QToolButton:hover {{ border-color:{accent}; }} '
            'QToolButton:disabled { background:#1a1918; color:#5f5b55; border-color:#2b2926; }')


def size_text(n):
    for unit in ('B', 'KB', 'MB', 'GB', 'TB'):
        if n < 1024 or unit == 'TB':
            return f'{n:,.1f} {unit}'
        n /= 1024


def duration_text(n):
    return core.timestamp(n).split('.')[0]


def open_path(path):
    if Path(path).exists():
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
    else:
        QMessageBox.warning(None, 'File unavailable', f'This file or folder has moved or was removed:\n{path}')


class Task(QThread):
    done = Signal(object)
    error = Signal(str)
    message = Signal(str)

    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self.fn = fn

    def run(self):
        try:
            self.done.emit(self.fn(self.message.emit))
        except Exception as exc:
            self.error.emit(str(exc))


class Batch(QThread):
    event = Signal(str, str, str, object)

    def __init__(self, folders, options, parent=None):
        super().__init__(parent)
        self.folders = copy.deepcopy(folders)
        self.options = copy.deepcopy(options)
        self.control = core.Control()
        self.cancelled = False

    def run(self):
        transcriber = core.Transcriber()
        visual_indexer = core.VisualIndexer()
        seen = set()
        jobs = []
        for folder in self.folders:
            for video in folder['files']:
                canonical = str(Path(video['path']).resolve()).casefold()
                if video['selected'] and video['status'] != 'Unreadable' and canonical not in seen:
                    seen.add(canonical)
                    jobs.append((folder, video))
        total_weight = sum(max(.1, v.get('duration', 0)) for _, v in jobs) or 1
        finished_weight = 0.0
        done_jobs = 0
        seen.clear()
        for folder in self.folders:
            for video in folder['files']:
                if not video['selected'] or video['status'] == 'Unreadable':
                    continue
                f, p = folder['id'], video['path']
                if self.control.cancel.is_set():
                    self.cancelled = True
                    self.event.emit(f, p, 'status', 'Cancelled')
                    continue
                canonical = str(Path(p).resolve()).casefold()
                if canonical in seen:
                    self.event.emit(f, p, 'status', 'Duplicate in queue')
                    continue
                seen.add(canonical)
                self.event.emit(f, p, 'status', 'Processing')
                weight = max(.1, video.get('duration', 0))
                stage_progress = {'frames': 0.0, 'transcript': 0.0, 'visual': 0.0}
                stages = ((['frames'] if self.options.get('screenshots') else []) +
                          (['transcript'] if self.options.get('transcribe') and video.get('audio') else []) +
                          (['visual'] if self.options.get('visual_index') else []))

                def forward(kind, value):
                    if kind in stage_progress:
                        stage_progress[kind] = min(1.0, value[0] / max(.1, video.get('duration', 0)))
                        current = sum(stage_progress[s] for s in stages) / max(1, len(stages))
                        percent = round((finished_weight + weight * current) / total_weight * 100)
                        self.event.emit(f, p, 'overall', {'percent': percent, 'done': done_jobs, 'total': len(jobs)})
                    self.event.emit(f, p, kind, value)
                try:
                    result = core.process_video(folder['path'], video, self.options, self.control, transcriber,
                                                forward, visual_indexer)
                    self.event.emit(f, p, 'result', result)
                    self.event.emit(f, p, 'status', 'Completed')
                except core.Cancelled:
                    self.cancelled = True
                    self.event.emit(f, p, 'status', 'Cancelled')
                    continue
                except Exception as exc:
                    self.event.emit(f, p, 'error', str(exc))
                finished_weight += weight
                done_jobs += 1
                self.event.emit(f, p, 'overall', {'percent': round(finished_weight / total_weight * 100), 'done': done_jobs, 'total': len(jobs)})


class OptionsDialog(QDialog):
    def __init__(self, options, folders, parent, batch_name='folder batch'):
        super().__init__(parent)
        self.setObjectName('processDialog')
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setWindowTitle('Process ' + batch_name)
        self.setMinimumSize(720, 510)
        self.resize(780, 540)
        self.closed_width = 780
        self.advanced_width = 1090
        self.background_target = parent.centralWidget() if parent and hasattr(parent, 'centralWidget') else None
        self.background_blur = None
        if self.background_target and self.background_target.graphicsEffect() is None:
            self.background_blur = QGraphicsBlurEffect(self.background_target)
            self.background_blur.setBlurRadius(3.5)
            self.background_target.setGraphicsEffect(self.background_blur)
        self.options = options.copy()
        self.files = [v for f in folders for v in f['files']]
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 20, 26, 20)
        layout.setSpacing(10)

        header = QHBoxLayout()
        self.process_title = label('Process ' + batch_name)
        self.process_title.setObjectName('processTitle')
        header.addWidget(self.process_title)
        header.addStretch()
        self.advanced_toggle = button('', self.toggle_advanced)
        self.advanced_toggle.setObjectName('advancedToggle')
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.setIcon(tile_icon('settings'))
        self.advanced_toggle.setIconSize(QSize(23, 19))
        self.advanced_toggle.setFixedSize(34, 34)
        self.advanced_toggle.setAccessibleName('Advanced settings')
        self.advanced_toggle.setToolTip('Advanced settings')
        header.addWidget(self.advanced_toggle)
        layout.addLayout(header)
        layout.addWidget(label('Videos run in queue order. Each video gets its own results folder.', 'subtle'))

        self.advanced_panel = QFrame()
        self.advanced_panel.setObjectName('card')
        self.advanced_panel.setMinimumWidth(300)
        self.advanced_panel.setMaximumWidth(320)
        advanced_form = QFormLayout(self.advanced_panel)
        advanced_form.setContentsMargins(14, 10, 14, 10)
        advanced_form.setHorizontalSpacing(14)
        advanced_form.setVerticalSpacing(7)
        advanced_form.addRow(label('TRANSCRIPTION', 'eyebrow'))
        self.model = QComboBox()
        ready_models = []
        for key, info in core.MODEL_INFO.items():
            ready = core.model_ready(key)
            if ready:
                ready_models.append(key)
                self.model.addItem(info[0], key)
        if not ready_models:
            self.model.addItem(core.MODEL_INFO['tiny'][0] + ' · Install in Settings', 'tiny')
            self.model.model().item(0).setEnabled(False)
        preferred_model = options['model'] if options['model'] in ready_models else (ready_models[0] if ready_models else 'tiny')
        self.model.setCurrentIndex(max(0, self.model.findData(preferred_model)))
        self.model_title = label('Whisper model')
        advanced_form.addRow(self.model_title, self.model)
        show_model_choice = len(ready_models) > 1
        self.model_title.setVisible(show_model_choice)
        self.model.setVisible(show_model_choice)

        self.device = QComboBox()
        for text, value in [('Automatic · GPU preferred', 'auto'), ('NVIDIA GPU only', 'cuda'), ('CPU', 'cpu')]:
            self.device.addItem(text, value)
        self.device.setCurrentIndex(max(0, self.device.findData(options['device'])))
        self.device_title = label('Processing device')
        advanced_form.addRow(self.device_title, self.device)

        advanced_form.addRow(label('SCREENSHOTS', 'eyebrow'))
        self.size_box = QWidget()
        self.size_box.setObjectName('transparentRow')
        size_row = QHBoxLayout(self.size_box)
        size_row.setContentsMargins(0, 0, 0, 0)
        self.width = MarkedSlider(Qt.Horizontal)
        self.width.setRange(0, 3)
        self.width.set_recommended((0, 1, 2, 3))
        selected_width = options.get('width', 1280)
        self.width.setValue([640, 1280, 1920, 0].index(selected_width if selected_width in (640, 1280, 1920, 0) else 1280))
        self.width_label = label('')
        self.width_label.setMinimumWidth(190)
        size_row.addWidget(self.width, 1)
        size_row.addWidget(self.width_label)
        self.size_title = label('Screenshot size')
        advanced_form.addRow(self.size_title, self.size_box)
        self.advanced_panel.hide()

        settings_card = QWidget()
        settings_card.setObjectName('transparentRow')
        main_form = QFormLayout(settings_card)
        main_form.setContentsMargins(0, 5, 0, 5)
        main_form.setHorizontalSpacing(16)
        main_form.setVerticalSpacing(7)

        language_box = QWidget()
        language_box.setObjectName('transparentRow')
        language_row = QHBoxLayout(language_box)
        language_row.setContentsMargins(0, 0, 0, 0)
        self.language_auto = button('Automatic')
        self.language_custom = button('Custom')
        for control in (self.language_auto, self.language_custom):
            control.setObjectName('segment')
            control.setCheckable(True)
        self.language_group = QButtonGroup(self)
        self.language_group.addButton(self.language_auto)
        self.language_group.addButton(self.language_custom)
        (self.language_custom if options['language'] else self.language_auto).setChecked(True)
        self.language = QComboBox()
        for text, code in [('English', 'en'), ('Hindi', 'hi'), ('Tamil', 'ta'), ('Telugu', 'te'), ('Bengali', 'bn'), ('Marathi', 'mr'), ('Spanish', 'es'), ('French', 'fr'), ('German', 'de'), ('Japanese', 'ja'), ('Chinese', 'zh'), ('Arabic', 'ar')]:
            self.language.addItem(text, code)
        self.language.setCurrentIndex(max(0, self.language.findData(options['language'] or 'en')))
        language_row.addWidget(self.language_auto)
        language_row.addWidget(self.language_custom)
        language_row.addWidget(self.language, 1)
        self.language_title = label('Spoken language')
        main_form.addRow(self.language_title, language_box)

        self.interval_box = QWidget()
        self.interval_box.setObjectName('transparentRow')
        interval_row = QHBoxLayout(self.interval_box)
        interval_row.setContentsMargins(0, 0, 0, 0)
        self.slider = MarkedSlider(Qt.Horizontal)
        self.slider.setRange(1, 300)
        self.slider.set_recommended((10, 50, 100, 300))
        self.slider.setToolTip('Recommended marks: 1, 5, 10 and 30 seconds. You can still enter any value from 0.1 to 30 seconds.')
        self.interval = QDoubleSpinBox()
        self.interval.setRange(0.1, 30)
        self.interval.setDecimals(2)
        self.interval.setSingleStep(0.1)
        self.interval.setSuffix(' sec')
        self.interval.setValue(options['interval'])
        self.slider.setValue(round(options['interval'] * 10))
        self.slider.valueChanged.connect(lambda v: self.interval.setValue(v / 10))
        self.interval.valueChanged.connect(self.sync_slider)
        interval_row.addWidget(self.slider, 1)
        interval_row.addWidget(self.interval)
        self.scene_mode = button('Scene change')
        self.scene_mode.setObjectName('segment')
        self.scene_mode.setCheckable(True)
        self.scene_mode.setChecked(options['mode'] == 'scene')
        self.scene_mode.setToolTip('When active, frames are saved at strong visual cuts instead of a fixed interval.')
        interval_row.addWidget(self.scene_mode)
        self.interval_title = label('Capture every')
        main_form.addRow(self.interval_title, self.interval_box)

        quality_box = QWidget()
        quality_box.setObjectName('transparentRow')
        quality_row = QHBoxLayout(quality_box)
        quality_row.setContentsMargins(0, 0, 0, 0)
        self.quality = MarkedSlider(Qt.Horizontal)
        self.quality.setRange(40, 95)
        self.quality.set_recommended((60, 75, 85, 95))
        self.quality.setToolTip('Recommended quality marks: 60, 75, 85 and 95 percent.')
        self.quality.setValue(options['quality'])
        self.quality_label = label('')
        self.quality_label.setMinimumWidth(85)
        quality_row.addWidget(self.quality, 1)
        quality_row.addWidget(self.quality_label)
        format_segment = QWidget()
        format_segment.setObjectName('transparentRow')
        format_row = QHBoxLayout(format_segment)
        format_row.setContentsMargins(0, 0, 0, 0)
        format_row.setSpacing(0)
        self.jpeg = button('JPEG')
        self.png = button('PNG')
        self.jpeg.setObjectName('formatLeft')
        self.png.setObjectName('formatRight')
        for control in (self.jpeg, self.png):
            control.setCheckable(True)
        self.format_group = QButtonGroup(self)
        self.format_group.addButton(self.jpeg)
        self.format_group.addButton(self.png)
        (self.png if options.get('image_format') == 'png' else self.jpeg).setChecked(True)
        self.jpeg.setToolTip('JPEG — smaller files with adjustable visual quality; best for most contact sheets.')
        self.png.setToolTip('PNG — lossless images with larger files; the quality slider is not used.')
        format_row.addWidget(self.jpeg)
        format_row.addWidget(self.png)
        quality_row.addWidget(format_segment)
        self.quality_title = label('Image quality')
        main_form.addRow(self.quality_title, quality_box)

        self.visual_interval_title = label('AI sampling distance')
        self.visual_interval_box = QWidget()
        self.visual_interval_box.setObjectName('transparentRow')
        visual_row = QHBoxLayout(self.visual_interval_box)
        visual_row.setContentsMargins(0, 0, 0, 0)
        self.visual_interval = MarkedSlider(Qt.Horizontal)
        self.visual_interval.setRange(1, 24)
        self.visual_interval.set_recommended((2, 6, 12, 24))
        self.visual_interval.setValue(max(1, min(24, round(options.get('visual_interval', 30) / 5))))
        self.visual_interval_label = label('')
        self.visual_interval_label.setMinimumWidth(150)
        self.visual_interval.setToolTip('Recommended marks: 10, 30, 60 and 120 seconds. Shorter distances catch brief objects but take longer.')
        self.visual_interval_box.setToolTip('AI does not inspect every video frame. This controls the distance between inspected frames.')
        visual_row.addWidget(self.visual_interval, 1)
        visual_row.addWidget(self.visual_interval_label)
        main_form.addRow(self.visual_interval_title, self.visual_interval_box)

        self.redo = QCheckBox('Redo existing results')
        self.redo.setChecked(not options['skip_existing'])
        self.redo.setToolTip('Off: reuse a completed result when the source and settings match. On: process it again and create a fresh result.')
        main_form.addRow('', self.redo)
        self.save_area = QFrame()
        self.save_area.setObjectName('saveArea')
        location = QHBoxLayout(self.save_area)
        location.setContentsMargins(12, 9, 10, 9)
        location.setSpacing(7)
        self.output_title = label('SAVE RESULTS', 'eyebrow')
        location.addWidget(self.output_title)
        self.output = QLineEdit(options.get('output', ''))
        self.output.setReadOnly(True)
        self.output.setPlaceholderText('Inside each selected folder / Tracer Results')
        location.addWidget(self.output, 1)
        location.addWidget(button('Browse', self.choose_output))
        location.addWidget(button('Reset', self.output.clear))
        main_form.addRow(self.save_area)
        settings_row = QHBoxLayout()
        settings_row.setSpacing(12)
        settings_row.addWidget(settings_card, 1)
        settings_row.addWidget(self.advanced_panel)
        layout.addLayout(settings_row)
        layout.addStretch(1)

        self.estimate_label = label('')
        self.estimate_label.setWordWrap(False)
        layout.addWidget(self.estimate_label)

        layout.addWidget(label('CREATE', 'eyebrow'), alignment=Qt.AlignHCenter)
        tile_row = QHBoxLayout()
        tile_row.setSpacing(9)
        tile_row.addStretch()
        self.transcribe = ChoiceTile('audio', 'Transcript', 'Searchable text and subtitles', icon_only=True)
        self.screenshots = ChoiceTile('frame', 'Screenshots', 'Timed frames or scene-change stills', icon_only=True)
        self.visual_index = ChoiceTile('ai', 'AI visual index', 'Offline object keywords and footage search', icon_only=True)
        self.transcribe.setToolTip('Transcript — create TXT, SRT, VTT and JSON. Transcript search works without AI indexing.')
        self.screenshots.setToolTip('Screenshots — create full-size JPEG or PNG stills using the screenshot settings above.')
        self.visual_index.setToolTip('AI visual index — analyse sampled frames locally and save searchable object keywords and thumbnails.')
        self.transcribe.setChecked(options['transcribe'])
        self.screenshots.setChecked(options['screenshots'])
        self.visual_index.setChecked(options.get('visual_index', True))
        for tile in (self.transcribe, self.screenshots, self.visual_index):
            tile.set_tone(1 if tile.isChecked() else 0)
            tile_row.addWidget(tile)
        tile_row.addStretch()
        layout.addLayout(tile_row)

        row = QHBoxLayout()
        row.addStretch()
        self.cancel_button = button('', self.reject)
        self.cancel_button.setObjectName('processCancel')
        self.cancel_button.setIcon(tile_icon('cancel'))
        self.cancel_button.setIconSize(QSize(25, 21))
        self.cancel_button.setAccessibleName('Cancel')
        self.cancel_button.setToolTip('Cancel and return to the dashboard')
        self.cancel_button.setFixedSize(36, 36)
        row.addWidget(self.cancel_button)
        self.start = button('Start', self.submit)
        self.start.setObjectName('processStart')
        self.start.setFixedSize(82, 36)
        row.addWidget(self.start)
        layout.addLayout(row)
        self.model.currentIndexChanged.connect(self.update_estimate)
        self.width.valueChanged.connect(self.sync_width)
        self.width.valueChanged.connect(self.update_estimate)
        for widget in (self.screenshots, self.transcribe, self.visual_index):
            widget.toggled.connect(self.update_estimate)
        for widget in (self.scene_mode, self.jpeg, self.png,
                       self.language_auto, self.language_custom):
            widget.toggled.connect(self.update_estimate)
        self.interval.valueChanged.connect(self.update_estimate)
        self.visual_interval.valueChanged.connect(self.update_estimate)
        self.quality.valueChanged.connect(self.update_estimate)
        self.sync_width()
        self.sync_quality()
        self.sync_visual_interval()
        self.update_estimate()
        QApplication.instance().installEventFilter(self)

    def toggle_advanced(self, checked):
        self.advanced_panel.setVisible(checked)
        self.resize(self.advanced_width if checked else self.closed_width, self.height())

    def eventFilter(self, watched, event):
        if event.type() == QEvent.MouseButtonPress and self.isVisible():
            application = QApplication.instance()
            if application.activePopupWidget() is None and application.activeModalWidget() in (None, self):
                position = event.globalPosition().toPoint() if hasattr(event, 'globalPosition') else None
                if position is not None and self.dismiss_if_outside(position):
                    return True
        return super().eventFilter(watched, event)

    def dismiss_if_outside(self, global_position):
        if self.isVisible() and not self.frameGeometry().contains(global_position):
            self.reject()
            return True
        return False

    def done(self, result):
        application = QApplication.instance()
        if application:
            application.removeEventFilter(self)
        if self.background_target and self.background_blur:
            self.background_target.setGraphicsEffect(None)
            self.background_blur = None
        super().done(result)

    def sync_slider(self, value):
        self.slider.blockSignals(True)
        self.slider.setValue(round(value * 10))
        self.slider.blockSignals(False)

    def sync_width(self, value=None):
        descriptions = ('Compact · max 640 px wide', 'Standard · max 1280 px wide',
                        'Detailed · max 1920 px wide', 'Original source resolution')
        self.width_label.setText(descriptions[self.width.value()])
        self.width.setToolTip(descriptions[self.width.value()] + '. Smaller source videos are never enlarged.')

    def sync_quality(self, value=None):
        if self.png.isChecked():
            self.quality_label.setText('Lossless · fixed')
        else:
            self.quality_label.setText(f'{self.quality.value()}% JPEG')

    def sync_visual_interval(self, value=None):
        seconds = self.visual_interval.value() * 5
        speed = 'Detailed' if seconds <= 10 else ('Balanced' if seconds <= 30 else 'Faster')
        self.visual_interval_label.setText(f'{seconds} sec · {speed}')

    def choose_output(self):
        folder = QFileDialog.getExistingDirectory(self, 'Choose a results location')
        if folder:
            self.output.setText(folder)

    def values(self):
        return {**self.options, 'model': self.model.currentData(),
                'mode': 'scene' if self.scene_mode.isChecked() else 'interval',
                'interval': self.interval.value(), 'width': (640, 1280, 1920, 0)[self.width.value()],
                'quality': self.quality.value(), 'image_format': 'png' if self.png.isChecked() else 'jpeg',
                'language': self.language.currentData() if self.language_custom.isChecked() else '',
                'device': self.device.currentData(),
                'screenshots': self.screenshots.isChecked(), 'transcribe': self.transcribe.isChecked(),
                'visual_index': self.visual_index.isChecked(), 'visual_interval': self.visual_interval.value() * 5,
                'skip_existing': not self.redo.isChecked(), 'output': self.output.text()}

    def update_estimate(self):
        o = self.values()
        enabled = o['screenshots'] and o['mode'] == 'interval'
        self.interval_box.setEnabled(enabled)
        self.interval_title.setEnabled(enabled)
        self.slider.setEnabled(enabled)
        self.interval.setEnabled(enabled)
        self.model.setEnabled(o['transcribe'])
        self.model_title.setEnabled(o['transcribe'])
        self.language_title.setEnabled(o['transcribe'])
        self.language_auto.setEnabled(o['transcribe'])
        self.language_custom.setEnabled(o['transcribe'])
        self.language.setVisible(o['transcribe'] and self.language_custom.isChecked())
        self.language.setEnabled(o['transcribe'])
        self.device.setEnabled(o['transcribe'])
        self.device_title.setEnabled(o['transcribe'])
        for title in (self.size_title, self.quality_title):
            title.setEnabled(o['screenshots'])
        for widget in (self.scene_mode, self.width, self.jpeg, self.png):
            widget.setEnabled(o['screenshots'])
        self.quality.setEnabled(o['screenshots'] and o['image_format'] == 'jpeg')
        self.quality_label.setEnabled(o['screenshots'])
        self.width_label.setEnabled(o['screenshots'])
        self.visual_interval_title.setVisible(True)
        self.visual_interval_box.setVisible(True)
        self.visual_interval_title.setEnabled(o['visual_index'])
        self.visual_interval_box.setEnabled(o['visual_index'])
        self.sync_quality()
        self.sync_visual_interval()
        valid = ((o['screenshots'] or o['transcribe'] or o['visual_index']) and
                 (not o['transcribe'] or core.model_ready(o['model'])) and
                 (not o['visual_index'] or core.visual_model_ready()))
        self.start.setEnabled(valid)
        if not valid:
            self.estimate_label.setText('Choose at least one output · install any missing model from Settings')
            return
        e = core.estimate(self.files, o)
        runtime = core.estimate_runtime(e['duration'], o)
        self.estimate_label.setText(
            f"{e['videos']} videos  ·  {e['count']:,} screenshots  ·  Time ≈ {duration_text(runtime)}  ·  Size ≈ {size_text(e['bytes'])}")

    def submit(self):
        o = self.values()
        if o['model'] in ('medium', 'large-v3') and o['transcribe']:
            if QMessageBox.question(self, 'Larger model', 'This model uses more GPU memory and takes longer than Tiny. Other GPU apps may reduce available memory. Continue?') != QMessageBox.Yes:
                return
        e = core.estimate(self.files, o)
        if e['count'] > 10000:
            if QMessageBox.question(self, 'Large screenshot collection', f"This job may create about {e['count']:,} images ({size_text(e['bytes'])}). Continue?") != QMessageBox.Yes:
                return
        self.options = core.validate_options(o)
        self.accept()


class FootageSearchPage(QWidget):
    """Video-first search with a coarse-to-fine visual contact sheet."""
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.records = []
        self.matches = {}
        self.record = None
        self.loading_detail = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 25, 28, 22)
        layout.setSpacing(12)
        layout.addWidget(label('FOOTAGE SEARCH · OFFLINE', 'eyebrow'))
        layout.addWidget(label('Find the shot, not the filename', 'title'))
        layout.addWidget(label('Search saved object keywords. Results stay grouped by video; open a match to inspect the surrounding five-second moments.', 'subtle'))
        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText('Try: person, car, phone, chair, dog…')
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.populate)
        search_row.addWidget(self.search, 1)
        self.layer = QComboBox()
        self.layer.addItem('Any depth', '')
        self.layer.addItem('Foreground', 'foreground')
        self.layer.addItem('Midground', 'midground')
        self.layer.addItem('Background', 'background')
        self.layer.currentIndexChanged.connect(self.populate)
        search_row.addWidget(self.layer)
        layout.addLayout(search_row)
        split = QSplitter(Qt.Horizontal)
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 4, 12, 0)
        self.count = label('INDEXED VIDEOS', 'eyebrow')
        ll.addWidget(self.count)
        self.videos = QListWidget()
        self.videos.currentItemChanged.connect(self.select_video)
        ll.addWidget(self.videos, 1)
        self.empty = label('Process footage with “Build offline visual search index” enabled.', 'subtle')
        self.empty.setWordWrap(True)
        ll.addWidget(self.empty)
        split.addWidget(left)
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(8, 4, 0, 0)
        self.name = label('Choose an indexed video', 'eyebrow')
        rl.addWidget(self.name)
        self.video = QVideoWidget()
        self.video.setMinimumHeight(190)
        self.video.setMaximumHeight(285)
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.audio.setVolume(.8)
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video)
        rl.addWidget(self.video)
        controls = QHBoxLayout()
        controls.addWidget(button('Play / pause', self.play))
        self.seek = MarkedSlider(Qt.Horizontal)
        self.seek.sliderMoved.connect(self.player.setPosition)
        self.player.positionChanged.connect(self.position)
        self.player.durationChanged.connect(lambda value: self.seek.setRange(0, value))
        controls.addWidget(self.seek, 1)
        self.clock = label('00:00:00')
        controls.addWidget(self.clock)
        rl.addLayout(controls)
        self.summary = label('Keywords will appear here.', 'subtle')
        self.summary.setWordWrap(True)
        rl.addWidget(self.summary)
        rl.addWidget(label('MATCHES · COARSE 30-SECOND VIEW', 'eyebrow'))
        self.coarse = QListWidget()
        self.coarse.setViewMode(QListWidget.IconMode)
        self.coarse.setIconSize(QSize(180, 101))
        self.coarse.setGridSize(QSize(205, 146))
        self.coarse.setResizeMode(QListWidget.Adjust)
        self.coarse.setMinimumHeight(165)
        self.coarse.itemClicked.connect(self.seek_frame)
        self.coarse.itemDoubleClicked.connect(self.load_detail)
        rl.addWidget(self.coarse, 1)
        self.detail_title = label('Double-click a coarse match to reveal every 5 seconds around it.', 'subtle')
        rl.addWidget(self.detail_title)
        self.detail = QListWidget()
        self.detail.setViewMode(QListWidget.IconMode)
        self.detail.setIconSize(QSize(145, 82))
        self.detail.setGridSize(QSize(165, 116))
        self.detail.setResizeMode(QListWidget.Adjust)
        self.detail.setMinimumHeight(125)
        self.detail.itemClicked.connect(self.seek_frame)
        rl.addWidget(self.detail, 1)
        split.addWidget(right)
        split.setSizes([285, 780])
        layout.addWidget(split, 1)

    def set_records(self, records):
        self.records = records
        self.populate()

    @staticmethod
    def _words(text):
        stop = {'a', 'an', 'the', 'with', 'in', 'on', 'at', 'of', 'find', 'show', 'me',
                'shot', 'shots', 'video', 'videos', 'where', 'there', 'is', 'are',
                'has', 'have', 'containing', 'frame', 'frames', 'looking', 'for'}
        words = [word for word in ''.join(ch.casefold() if ch.isalnum() else ' ' for ch in text).split()
                 if word and word not in stop]
        return [word[:-1] if word.endswith('s') and len(word) > 3 and word not in ('glass',) else word
                for word in words]

    def frame_matches(self, frame, query, layer):
        layers = frame.get('keywords', {})
        if layer:
            values = layers.get(layer, [])
            searchable = ' '.join([layer] + values)
            from vision_index import ALIASES
            searchable += ' ' + ' '.join(alias for value in values for alias in ALIASES.get(value, ()))
        else:
            searchable = ' '.join(frame.get('search_words', []))
        haystack = searchable.casefold()
        return not query or all(word in haystack for word in self._words(query))

    def populate(self):
        previous = self.record.get('id') if self.record else None
        query = self.search.text().strip()
        layer = self.layer.currentData()
        self.videos.blockSignals(True)
        self.videos.clear()
        self.matches = {}
        selected = None
        indexed = [record for record in self.records if record.get('visual_index', {}).get('frames')]
        for record in reversed(indexed):
            frames = [frame for frame in record['visual_index']['frames'] if self.frame_matches(frame, query, layer)]
            name_hit = query and all(word in (record['source'] + ' ' + record.get('project_name', '')).casefold()
                                     for word in self._words(query))
            if not frames and not name_hit:
                continue
            if name_hit and not frames:
                frames = record['visual_index']['frames']
            self.matches[record['id']] = frames
            project = f" · {record['project_name']}" if record.get('project_name') else ''
            keywords = ', '.join(record['visual_index'].get('search_words', [])[:8]) or 'no objects found'
            item = QListWidgetItem(f"{Path(record['source']).name}\n{len(frames)} matching moments{project}\n{keywords}")
            item.setData(Qt.UserRole, record)
            self.videos.addItem(item)
            if record['id'] == previous:
                selected = item
        self.videos.blockSignals(False)
        self.count.setText(f'{self.videos.count()} VIDEO RESULTS')
        self.empty.setVisible(not indexed)
        if selected:
            self.videos.setCurrentItem(selected)
        elif self.videos.count():
            self.videos.setCurrentRow(0)
        else:
            self.record = None
            self.coarse.clear()
            self.detail.clear()
            self.name.setText('No matching indexed videos')

    def select_video(self, item, previous=None):
        if not item:
            return
        self.record = item.data(Qt.UserRole)
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(self.record['source']))
        self.name.setText(Path(self.record['source']).name)
        self.detail.clear()
        self.detail_title.setText('Double-click a coarse match to reveal every 5 seconds around it.')
        summary = self.record['visual_index'].get('keywords', {})
        parts = [f"{layer.title()}: {', '.join(values) or '—'}" for layer, values in summary.items()]
        self.summary.setText('   ·   '.join(parts))
        self.coarse.clear()
        for frame in self.matches.get(self.record['id'], []):
            keywords = frame.get('keywords', {})
            brief = ', '.join(dict.fromkeys(value for values in keywords.values() for value in values))[:42]
            item = QListWidgetItem(QIcon(str(Path(self.record['output']) / frame['file'])),
                                   f"{duration_text(frame['time'])}\n{brief or 'no common objects'}")
            item.setData(Qt.UserRole, frame)
            item.setToolTip('Double-click for the five-second view')
            self.coarse.addItem(item)

    def load_detail(self, item):
        if not self.record or self.loading_detail:
            return
        frame = item.data(Qt.UserRole)
        interval = float(self.record.get('visual_index', {}).get('interval', 30))
        start = math.floor(frame['time'] / max(1, interval)) * interval
        self.loading_detail = True
        self.detail.clear()
        self.detail_title.setText(f"Loading five-second view from {duration_text(start)}…")
        record = self.record
        task = self.window.run_task(
            lambda notify: core.extract_detail_frames(record['source'], record['output'], start, record['duration']),
            lambda frames: self.detail_loaded(record['id'], start, frames))
        task.finished.connect(lambda: setattr(self, 'loading_detail', False))

    def detail_loaded(self, record_id, start, frames):
        if not self.record or self.record['id'] != record_id:
            return
        self.detail.clear()
        self.detail_title.setText(f"DETAIL · EVERY 5 SECONDS FROM {duration_text(start)}")
        for frame in frames:
            item = QListWidgetItem(QIcon(frame['file']), duration_text(frame['time']))
            item.setData(Qt.UserRole, frame)
            self.detail.addItem(item)

    def seek_frame(self, item):
        self.player.setPosition(round(item.data(Qt.UserRole)['time'] * 1000))

    def position(self, value):
        if not self.seek.isSliderDown():
            self.seek.setValue(value)
        self.clock.setText(duration_text(value / 1000))

    def play(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        elif self.record:
            self.player.play()


class ResultsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.records = []
        self.record = None
        self.frame_offset = 0
        self.visual_matches = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 25, 28, 22)
        layout.setSpacing(10)
        self.page_title = label('Video library', 'title')
        layout.addWidget(self.page_title)
        layout.addWidget(label('Read the transcript, preview the source, and review every generated frame.', 'subtle'))

        search_bar = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText('Search dialogue, video names, or visual keywords…')
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.populate)
        self.search.textEdited.connect(lambda _: self.open_search())
        search_bar.addWidget(self.search, 1)
        self.audio_scope = ChoiceTile('audio', 'Audio', icon_only=True)
        self.visual_scope = ChoiceTile('ai', 'Visual', icon_only=True)
        for control in (self.audio_scope, self.visual_scope):
            control.setFixedSize(44, 36)
            control.setChecked(True)
            control.set_tone(1)
            control.toggled.connect(self.search_scope_changed)
            search_bar.addWidget(control)
        self.audio_scope.setToolTip('Search spoken transcript text.')
        self.visual_scope.setToolTip('Search offline visual-index keywords.')
        self.layer = QComboBox()
        self.layer.addItem('Any depth', '')
        self.layer.addItem('Foreground', 'foreground')
        self.layer.addItem('Midground', 'midground')
        self.layer.addItem('Background', 'background')
        self.layer.setFixedSize(104, 36)
        self.layer.currentIndexChanged.connect(self.populate)
        search_bar.addWidget(self.layer)
        layout.addLayout(search_bar)

        self.library_host = QWidget()
        self.library_host.installEventFilter(self)
        host_layout = QVBoxLayout(self.library_host)
        host_layout.setContentsMargins(0, 0, 0, 0)
        self.search_panel = QFrame(self.library_host)
        self.search_panel.setObjectName('card')
        self.search_panel.setFixedWidth(310)
        ll = QVBoxLayout(self.search_panel)
        ll.setContentsMargins(14, 14, 14, 14)
        search_heading = QHBoxLayout()
        search_heading.addWidget(label('FIND A VIDEO', 'eyebrow'))
        search_heading.addStretch()
        self.close_search = button('', self.collapse_search)
        self.close_search.setObjectName('mediaIcon')
        self.close_search.setIcon(tile_icon('list_left'))
        self.close_search.setIconSize(QSize(23, 19))
        self.close_search.setFixedSize(34, 32)
        self.close_search.setToolTip('Hide the video list')
        search_heading.addWidget(self.close_search)
        ll.addLayout(search_heading)
        self.list = QListWidget()
        self.list.itemClicked.connect(self.select)
        self.list.itemActivated.connect(self.select)
        ll.addWidget(self.list)
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(10)
        toolbar = QHBoxLayout()
        self.browse_videos = button('See All', self.open_search)
        self.browse_videos.setIcon(tile_icon('list_right'))
        self.browse_videos.setIconSize(QSize(22, 18))
        self.browse_videos.setToolTip('Show the complete video list')
        toolbar.addWidget(self.browse_videos)
        toolbar.addStretch()
        self.open_original = button('Open original folder', self.open_source_folder)
        toolbar.addWidget(self.open_original)
        self.open_results = button('Open results folder', self.open_result)
        self.open_results.setObjectName('libraryPrimary')
        toolbar.addWidget(self.open_results)
        rl.addLayout(toolbar)

        self.media_split = QSplitter(Qt.Horizontal)
        self.media_split.setHandleWidth(7)
        self.media_split.setChildrenCollapsible(False)
        transcript_panel = QFrame()
        transcript_panel.setObjectName('card')
        transcript_layout = QVBoxLayout(transcript_panel)
        transcript_layout.setContentsMargins(14, 12, 14, 12)
        transcript_layout.addWidget(label('TRANSCRIPT', 'eyebrow'))
        self.transcript_search = QLineEdit()
        self.transcript_search.setPlaceholderText('Filter transcript · select a line to jump to that moment')
        self.transcript_search.textChanged.connect(self.fill_transcript)
        transcript_layout.addWidget(self.transcript_search)
        self.transcript = QListWidget()
        self.transcript.setMinimumHeight(170)
        self.transcript.itemClicked.connect(self.seek_segment)
        transcript_layout.addWidget(self.transcript, 1)
        exports = QHBoxLayout()
        exports.addWidget(label('Open:', 'subtle'))
        for fmt in ('txt', 'srt', 'vtt', 'json'):
            exports.addWidget(button(fmt.upper(), lambda checked=False, f=fmt: self.open_export(f)))
        exports.addStretch()
        transcript_layout.addLayout(exports)
        self.media_split.addWidget(transcript_panel)

        video_panel = QFrame()
        video_panel.setObjectName('card')
        video_panel.setMinimumWidth(220)
        video_layout = QVBoxLayout(video_panel)
        video_layout.setContentsMargins(10, 10, 10, 10)
        video_layout.addWidget(label('SOURCE PREVIEW', 'eyebrow'))
        self.video = QVideoWidget()
        self.video.setMinimumHeight(145)
        self.video.setMaximumHeight(205)
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.audio.setVolume(0.8)
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video)
        video_layout.addWidget(self.video, 1)
        controls = QHBoxLayout()
        self.play_button = button('', self.play)
        self.play_button.setObjectName('mediaIcon')
        self.play_button.setIcon(tile_icon('play'))
        self.play_button.setIconSize(QSize(23, 20))
        self.play_button.setFixedSize(38, 34)
        self.play_button.setAccessibleName('Play or pause')
        self.play_button.setToolTip('Play')
        controls.addWidget(self.play_button)
        self.seek = MarkedSlider(Qt.Horizontal)
        self.seek.sliderMoved.connect(self.player.setPosition)
        self.player.positionChanged.connect(self.position)
        self.player.durationChanged.connect(lambda n: self.seek.setRange(0, n))
        self.player.playbackStateChanged.connect(self.sync_play_icon)
        controls.addWidget(self.seek)
        self.clock = label('00:00:00')
        controls.addWidget(self.clock)
        video_layout.addLayout(controls)
        self.media_split.addWidget(video_panel)
        self.media_split.setStretchFactor(0, 3)
        self.media_split.setStretchFactor(1, 1)
        self.media_split.setSizes([720, 250])
        rl.addWidget(self.media_split, 2)

        screenshots_heading = QHBoxLayout()
        screenshots_heading.addWidget(label('SCREENSHOTS', 'eyebrow'))
        self.page_label = label('', 'subtle')
        screenshots_heading.addWidget(self.page_label)
        screenshots_heading.addStretch()
        screenshots_heading.addWidget(button('Previous', lambda: self.page_frames(-1)))
        screenshots_heading.addWidget(button('Next', lambda: self.page_frames(1)))
        rl.addLayout(screenshots_heading)
        self.frames = QListWidget()
        self.frames.setViewMode(QListWidget.IconMode)
        self.frames.setIconSize(QSize(190, 110))
        self.frames.setGridSize(QSize(210, 145))
        self.frames.setResizeMode(QListWidget.Adjust)
        self.frames.setMinimumHeight(240)
        self.frames.itemClicked.connect(self.seek_frame)
        self.frames.itemDoubleClicked.connect(lambda item: open_path(Path(self.record['output']) / item.data(Qt.UserRole)['file']))
        rl.addWidget(self.frames, 1)
        host_layout.addWidget(right)
        layout.addWidget(self.library_host, 1)
        self.search_panel.setGeometry(0, 0, 310, max(1, self.library_host.height()))
        self.search_panel.raise_()
        self.search_animation = QPropertyAnimation(self.search_panel, b'pos', self)
        self.search_animation.setDuration(230)
        self.search_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self.search_animation.finished.connect(self.search_animation_finished)
        self.search_target = 310
        self.browse_videos.setEnabled(False)

    def set_records(self, records):
        self.records = records
        self.populate()

    def search_scope_changed(self):
        self.layer.setEnabled(self.visual_scope.isChecked())
        self.populate()

    def eventFilter(self, watched, event):
        if watched is self.library_host and event.type() == QEvent.Resize:
            self.search_panel.resize(310, event.size().height())
        return super().eventFilter(watched, event)

    def matching_visual_frames(self, record, query=None):
        query = (self.search.text() if query is None else query).casefold().strip()
        if not query or not self.visual_scope.isChecked():
            return []
        selected_layer = self.layer.currentData()
        matches = []
        for frame in record.get('visual_index', {}).get('frames', []):
            keywords = frame.get('keywords', {})
            values = keywords.get(selected_layer, []) if selected_layer else [word for words in keywords.values() for word in words]
            searchable = ' '.join(values + frame.get('search_words', [])).casefold()
            if query in searchable:
                matches.append(frame)
        return matches

    def populate(self):
        old = self.record.get('id') if self.record else None
        self.list.blockSignals(True)
        self.list.clear()
        query = self.search.text().casefold().strip()
        self.visual_matches = {}
        selected = None
        for record in reversed(self.records):
            searchable = [record['source'] + ' ' + record.get('project_name', '')]
            if self.audio_scope.isChecked():
                searchable.append(' '.join(s['text'] for s in record.get('segments', [])))
            visual_matches = self.matching_visual_frames(record, query)
            if visual_matches:
                self.visual_matches[record['id']] = visual_matches
                searchable.append(query)
            if query and not any(query in value.casefold() for value in searchable):
                continue
            project = (' · ' + record['project_name']) if record.get('project_name') else ''
            item = QListWidgetItem(f"{Path(record['source']).name}\n{duration_text(record['duration'])}{project}")
            item.setData(Qt.UserRole, record)
            self.list.addItem(item)
            if record['id'] == old:
                selected = item
        self.list.blockSignals(False)
        if selected:
            self.list.setCurrentItem(selected)
        if self.record:
            self.frame_offset = 0
            self.fill_frames()

    def collapse_search(self):
        if not self.search_panel.isVisible():
            return
        self.search_animation.stop()
        self.search_target = 0
        self.search_animation.setStartValue(self.search_panel.pos())
        self.search_animation.setEndValue(QPoint(-310, 0))
        self.search_animation.start()
        self.browse_videos.setEnabled(True)

    def open_search(self):
        if self.search_panel.isVisible() and self.search_target == 310 and self.search_panel.x() >= 0:
            return
        self.search_animation.stop()
        self.search_panel.show()
        self.search_panel.raise_()
        self.search_panel.move(-310, 0)
        self.search_target = 310
        self.search_animation.setStartValue(QPoint(-310, 0))
        self.search_animation.setEndValue(QPoint(0, 0))
        self.search_animation.start()

    def search_animation_finished(self):
        if self.search_target == 0:
            self.search_panel.hide()
        else:
            self.search_panel.move(0, 0)
            self.browse_videos.setEnabled(False)

    def select(self, item, previous=None):
        if not item:
            return
        self.record = item.data(Qt.UserRole)
        self.page_title.setText(Path(self.record['source']).name)
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(self.record['source']))
        self.frame_offset = 0
        query = self.search.text().strip()
        transcript_text = ' '.join(segment['text'] for segment in self.record.get('segments', []))
        self.transcript_search.setText(query if self.audio_scope.isChecked() and query.casefold() in transcript_text.casefold() else '')
        self.fill_frames()
        self.fill_transcript()
        self.collapse_search()

    def fill_frames(self):
        self.frames.clear()
        if not self.record:
            return
        matches = self.visual_matches.get(self.record['id'], [])
        frames = matches or self.record.get('frames', [])
        for f in frames[self.frame_offset:self.frame_offset + 60]:
            item = QListWidgetItem(QIcon(str(Path(self.record['output']) / f['file'])), core.timestamp(f['time']))
            item.setData(Qt.UserRole, f)
            self.frames.addItem(item)
        suffix = ' visual matches' if matches else ''
        self.page_label.setText(f'{self.frame_offset + 1 if frames else 0}–{min(self.frame_offset + 60, len(frames))} of {len(frames):,}{suffix}')

    def page_frames(self, direction):
        if self.record:
            n = len(self.visual_matches.get(self.record['id'], []) or self.record.get('frames', []))
            self.frame_offset = max(0, min(max(0, (n - 1) // 60 * 60), self.frame_offset + direction * 60))
            self.fill_frames()

    def fill_transcript(self):
        self.transcript.clear()
        if not self.record:
            return
        query = self.transcript_search.text().casefold()
        for segment in self.record.get('segments', []):
            if query and query not in segment['text'].casefold():
                continue
            item = QListWidgetItem(f"{duration_text(segment['start'])}   {segment['text'].strip()}")
            item.setData(Qt.UserRole, segment)
            self.transcript.addItem(item)
        if not self.record.get('segments'):
            self.transcript.addItem(self.record.get('notice', 'No transcript for this video.'))

    def seek_frame(self, item):
        self.player.setPosition(round(item.data(Qt.UserRole)['time'] * 1000))

    def seek_segment(self, item):
        segment = item.data(Qt.UserRole)
        if segment:
            self.player.setPosition(round(segment['start'] * 1000))
            frames = self.record.get('frames', [])
            if frames:
                index = min(range(len(frames)), key=lambda i: abs(frames[i]['time'] - segment['start']))
                self.frame_offset = index // 60 * 60
                self.fill_frames()
                self.frames.setCurrentRow(index % 60)

    def position(self, n):
        if not self.seek.isSliderDown():
            self.seek.setValue(n)
        self.clock.setText(duration_text(n / 1000))

    def play(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        elif self.record:
            self.player.play()

    def sync_play_icon(self, state):
        playing = state == QMediaPlayer.PlayingState
        self.play_button.setIcon(tile_icon('pause' if playing else 'play'))
        self.play_button.setToolTip('Pause' if playing else 'Play')

    def open_result(self):
        if self.record:
            open_path(self.record['output'])

    def open_source_folder(self):
        if self.record:
            open_path(Path(self.record['source']).parent)

    def open_export(self, fmt):
        if self.record:
            open_path(Path(self.record['output']) / ('transcript.' + fmt))


class ProjectsPage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.item_map = {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(13)
        heading = QHBoxLayout()
        words = QVBoxLayout()
        words.addWidget(label('PROJECT DASHBOARD', 'eyebrow'))
        words.addWidget(label('Projects', 'title'))
        words.addWidget(label('Keep interviews, dailies, research, or client footage together.', 'subtle'))
        heading.addLayout(words)
        heading.addStretch()
        heading.addWidget(button('+ New project', self.window.new_project, True))
        layout.addLayout(heading)
        split = QSplitter(Qt.Horizontal)
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 5, 10, 0)
        ll.addWidget(label('SAVED PROJECTS', 'eyebrow'))
        self.projects = QListWidget()
        self.projects.currentItemChanged.connect(self.project_changed)
        ll.addWidget(self.projects, 1)
        left_actions = QHBoxLayout()
        left_actions.addWidget(button('Rename', self.window.rename_project))
        remove = button('Remove', self.window.remove_project)
        remove.setObjectName('danger')
        left_actions.addWidget(remove)
        ll.addLayout(left_actions)
        split.addWidget(left)
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(8, 5, 0, 0)
        top = QHBoxLayout()
        self.name = label('Select or create a project', 'title')
        top.addWidget(self.name)
        top.addStretch()
        self.add_folders = button('+ Folders', self.window.add_project_folders)
        self.add_files = button('+ Videos', self.window.add_project_files)
        self.remove_source = button('Remove source', self.window.remove_project_source)
        top.addWidget(self.add_folders)
        top.addWidget(self.add_files)
        top.addWidget(self.remove_source)
        rl.addLayout(top)
        self.summary = label('A project remembers its sources, selections, and completed library items.', 'subtle')
        rl.addWidget(self.summary)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(['Source / video', 'Duration', 'Status'])
        self.tree.setColumnWidth(0, 450)
        self.tree.setColumnWidth(1, 100)
        self.tree.header().setStretchLastSection(True)
        self.tree.itemChanged.connect(self.selection_changed)
        self.tree.currentItemChanged.connect(lambda *_: self.update_summary())
        rl.addWidget(self.tree, 1)
        self.status = label('Create a project, then add folders or individual videos.', 'subtle')
        self.status.setWordWrap(True)
        rl.addWidget(self.status)
        progress_row = QHBoxLayout()
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setFormat('%p% of project batch')
        progress_row.addWidget(self.progress, 1)
        self.progress_detail = label('0 of 0 videos', 'subtle')
        progress_row.addWidget(self.progress_detail)
        rl.addLayout(progress_row)
        actions = QHBoxLayout()
        self.pause = button('Pause', self.window.pause_batch)
        self.cancel = button('Cancel batch', self.window.cancel_batch)
        self.pause.setEnabled(False)
        self.cancel.setEnabled(False)
        actions.addWidget(self.pause)
        actions.addWidget(self.cancel)
        actions.addStretch()
        self.process = button('Process project  →', self.window.process_project, True)
        actions.addWidget(self.process)
        rl.addLayout(actions)
        split.addWidget(right)
        split.setSizes([275, 780])
        layout.addWidget(split, 1)
        self.refresh()

    def current(self):
        item = self.projects.currentItem()
        project_id = item.data(Qt.UserRole) if item else None
        return next((p for p in self.window.state['projects'] if p['id'] == project_id), None)

    def select_project(self, project_id):
        for row in range(self.projects.count()):
            item = self.projects.item(row)
            if item.data(Qt.UserRole) == project_id:
                self.projects.setCurrentItem(item)
                return

    def refresh(self, select_id=None):
        current = select_id or (self.current().get('id') if self.current() else None)
        self.projects.blockSignals(True)
        self.projects.clear()
        for project in self.window.state['projects']:
            files = [v for f in project.get('folders', []) for v in f.get('files', [])]
            done = sum(v.get('status') == 'Completed' for v in files)
            item = QListWidgetItem(f"{project['name']}\n{len(files)} videos · {done} completed")
            item.setData(Qt.UserRole, project['id'])
            self.projects.addItem(item)
        self.projects.blockSignals(False)
        if current:
            self.select_project(current)
        elif self.projects.count():
            self.projects.setCurrentRow(0)
        else:
            self.populate_tree()

    def project_changed(self, current, previous=None):
        self.populate_tree()
        if self.current() and not self.window.batch:
            self.status.setText('Ready. Add more sources or process the selected videos.')

    def populate_tree(self):
        project = self.current()
        self.tree.blockSignals(True)
        self.tree.clear()
        self.item_map.clear()
        if not project:
            self.name.setText('Select or create a project')
            self.summary.setText('A project remembers its sources, selections, and completed library items.')
        else:
            self.name.setText(project['name'])
            for folder in project.get('folders', []):
                parent = QTreeWidgetItem([folder['name'], '', ''])
                parent.setData(0, Qt.UserRole, (folder['id'], None))
                parent.setToolTip(0, folder['path'])
                parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)
                self.tree.addTopLevelItem(parent)
                for video in folder.get('files', []):
                    child = QTreeWidgetItem([video['name'], duration_text(video.get('duration', 0)), video.get('status', 'Ready')])
                    child.setData(0, Qt.UserRole, (folder['id'], video['path']))
                    child.setToolTip(0, video['path'])
                    child.setToolTip(2, video.get('error', ''))
                    child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                    parent.addChild(child)
                    child.setCheckState(0, Qt.Checked if video.get('selected') else Qt.Unchecked)
                    if video.get('status') == 'Unreadable':
                        child.setDisabled(True)
                    self.item_map[(folder['id'], video['path'])] = child
                parent.setExpanded(True)
        self.tree.blockSignals(False)
        self.update_summary()

    def selection_changed(self, item, column):
        if column != 0:
            return
        project = self.current()
        if not project:
            return
        for folder in project.get('folders', []):
            for video in folder.get('files', []):
                child = self.item_map[(folder['id'], video['path'])]
                video['selected'] = child.checkState(0) == Qt.Checked and video.get('status') != 'Unreadable'
        self.update_summary()
        self.window.save_timer.start(300)

    def update_summary(self):
        project = self.current()
        files = [v for f in project.get('folders', []) for v in f.get('files', [])] if project else []
        selected = [v for v in files if v.get('selected')]
        if project:
            completed = sum(v.get('status') == 'Completed' for v in files)
            self.summary.setText(f"{len(project.get('folders', []))} source folders · {len(selected)} selected · {duration_text(sum(v.get('duration', 0) for v in selected))} · {completed} completed")
            if not self.window.batch:
                self.progress_detail.setText(f"{len(selected)} {'video' if len(selected) == 1 else 'videos'} ready")
        ready = bool(project and selected and not self.window.batch and not self.window.scanning)
        self.process.setEnabled(ready)
        self.add_folders.setEnabled(bool(project) and not self.window.batch and not self.window.scanning)
        self.add_files.setEnabled(bool(project) and not self.window.batch and not self.window.scanning)
        self.remove_source.setEnabled(bool(project) and bool(self.tree.currentItem()) and not self.window.batch and not self.window.scanning)

    def set_busy(self, busy):
        for widget in (self.projects, self.tree, self.add_folders, self.add_files, self.remove_source):
            widget.setEnabled(not busy)
        if not busy:
            self.update_summary()


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Tracer')
        self.resize(1280, 860)
        self.setMinimumSize(1020, 720)
        self.state = core.load_state()
        self.state['settings'] = {**core.DEFAULTS, **self.state.get('settings', {})}
        self.batch = None
        self.tasks = []
        self.downloading = False
        self.scanning = False
        self.item_map = {}
        self.active_progress = {'frames': 0, 'transcript': 0}
        self.batch_context = None
        self.batch_percent = 0
        self.stats = []
        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self.save)
        root = QWidget()
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName('sidebar')
        sidebar.setFixedWidth(205)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(20, 29, 20, 25)
        brand = QHBoxLayout()
        mark = QLabel()
        asset = Path(getattr(sys, '_MEIPASS', core.ROOT)) / 'assets' / 'transpro.svg'
        mark.setPixmap(QIcon(str(asset)).pixmap(30, 30))
        brand.addWidget(mark)
        brand.addWidget(label('Tracer', 'brand'))
        brand.addStretch()
        side.addLayout(brand)
        side.addWidget(label('TRANSCRIPTION DESK', 'eyebrow'))
        side.addSpacing(30)
        self.nav = []
        for i, name in enumerate(('Folder queue', 'Project dashboard', 'Video library', 'Settings')):
            b = button(name, lambda checked=False, index=i: self.navigate(index))
            b.setObjectName('nav')
            b.setCheckable(True)
            self.nav.append(b)
            side.addWidget(b)
        side.addStretch()
        side.addWidget(label('ON THIS MACHINE', 'eyebrow'))
        privacy = label('Local processing\nNo account or API fees', 'subtle')
        privacy.setWordWrap(True)
        side.addWidget(privacy)
        side.addSpacing(15)
        side.addWidget(label('Tracer · 1.11', 'subtle'))
        outer.addWidget(sidebar)
        self.pages = QStackedWidget()
        self.pages.addWidget(self.make_queue())
        self.projects_page = ProjectsPage(self)
        self.pages.addWidget(self.projects_page)
        self.results = ResultsPage()
        self.results.set_records(self.state['results'])
        self.pages.addWidget(self.results)
        self.pages.addWidget(self.make_settings())
        outer.addWidget(self.pages, 1)
        self.setCentralWidget(root)
        self.navigate(0)
        self.refresh_tree()
        self.run_task(lambda notify: core.gpu_info(), lambda v: self.gpu.setText(v))
        if self.state.get('recovery'):
            self.status.setText('Library was recovered. Previous data saved at ' + self.state['recovery'])
        QTimer.singleShot(600, self.first_setup)

    def navigate(self, index):
        self.pages.setCurrentIndex(index)
        for i, b in enumerate(self.nav):
            b.setChecked(i == index)
        if index != 2 and hasattr(self, 'results'):
            self.results.player.pause()

    def make_queue(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(13)
        layout.addWidget(label('FOLDER QUEUE', 'eyebrow'))
        heading = QHBoxLayout()
        heading.addWidget(label('Batch workspace', 'title'))
        heading.addStretch()
        self.add_button = button('+ Add folders', self.add_folders, True)
        heading.addWidget(self.add_button)
        layout.addLayout(heading)
        layout.addWidget(label('Folders run from top to bottom. Expand a folder to choose individual videos.', 'subtle'))
        cards = QHBoxLayout()
        for name in ('FOLDERS IN QUEUE', 'VIDEOS SELECTED', 'TOTAL FOOTAGE'):
            card = QFrame()
            card.setObjectName('card')
            cl = QVBoxLayout(card)
            cl.setContentsMargins(18, 14, 18, 14)
            cl.addWidget(label(name, 'subtle'))
            value = label('0', 'metric')
            self.stats.append(value)
            cl.addWidget(value)
            cards.addWidget(card)
        layout.addLayout(cards)
        toolbar = QHBoxLayout()
        toolbar.addWidget(label('PROCESSING QUEUE', 'eyebrow'))
        toolbar.addStretch()
        self.recursive = QCheckBox('Include subfolders when adding')
        self.recursive.setChecked(self.state['settings']['recursive'])
        self.recursive.toggled.connect(self.set_recursive)
        toolbar.addWidget(self.recursive)
        self.up = button('↑', lambda: self.move_folder(-1))
        self.down = button('↓', lambda: self.move_folder(1))
        self.remove = button('Remove from queue', self.remove_folder)
        self.rescan = button('Rescan', self.rescan_folder)
        for b in (self.up, self.down, self.rescan, self.remove):
            toolbar.addWidget(b)
        layout.addLayout(toolbar)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(['Folder / video', 'Duration', 'Status'])
        self.tree.setColumnWidth(0, 510)
        self.tree.setColumnWidth(1, 105)
        self.tree.header().setStretchLastSection(True)
        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree.setExpandsOnDoubleClick(True)
        self.tree.itemChanged.connect(self.selection_changed)
        layout.addWidget(self.tree, 1)
        self.empty = label('Add your first folder to get started. You can add more folders at any time.', 'subtle')
        self.empty.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.empty)
        self.status = label('Ready.', 'subtle')
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        self.progress.setFormat('%p% of total batch')
        self.progress.setValue(0)
        progress_row = QHBoxLayout()
        progress_row.addWidget(self.progress, 1)
        self.progress_detail = label('0 of 0 videos', 'subtle')
        progress_row.addWidget(self.progress_detail)
        layout.addLayout(progress_row)
        actions = QHBoxLayout()
        self.pause = button('Pause', self.pause_batch)
        self.cancel = button('Cancel batch', self.cancel_batch)
        self.pause.setEnabled(False)
        self.cancel.setEnabled(False)
        actions.addWidget(self.pause)
        actions.addWidget(self.cancel)
        actions.addStretch()
        self.process = button('Process folders  →', self.process_folders, True)
        actions.addWidget(self.process)
        layout.addLayout(actions)
        return page

    def make_settings(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 22)
        layout.setSpacing(12)
        layout.addWidget(label('Models & processing', 'title'))
        layout.addWidget(label('Install transcription models once; use them offline afterward.', 'subtle'))
        self.gpu = label('Checking your GPU…', 'eyebrow')
        layout.addWidget(self.gpu)
        layout.addWidget(label('WHISPER MODELS', 'eyebrow'))
        self.model_rows = {}
        model_card = QFrame()
        model_card.setObjectName('card')
        model_row = QHBoxLayout(model_card)
        model_row.setContentsMargins(10, 10, 10, 10)
        model_row.setSpacing(8)
        for key, info in core.MODEL_INFO.items():
            cell = QFrame()
            cell.setObjectName('modelCell')
            words = QVBoxLayout(cell)
            words.setContentsMargins(10, 9, 10, 9)
            words.setSpacing(5)
            name = label(info[0])
            words.addWidget(name)
            state = label('', 'subtle')
            state.setWordWrap(True)
            state.setMinimumHeight(34)
            words.addWidget(state)
            actions = QHBoxLayout()
            actions.setSpacing(5)
            dl = button('Download', lambda checked=False, k=key: self.download(k), key == 'tiny')
            rm = button('Remove', lambda checked=False, k=key: self.remove_model(k))
            actions.addWidget(dl)
            actions.addWidget(rm)
            words.addLayout(actions)
            self.model_rows[key] = (state, dl, rm)
            model_row.addWidget(cell, 1)
        layout.addWidget(model_card)
        self.download_status = label('Tiny is installed automatically during setup. Other models are optional.', 'subtle')
        self.download_status.setWordWrap(True)
        layout.addWidget(self.download_status)
        self.download_progress = QProgressBar()
        self.download_progress.hide()
        layout.addWidget(self.download_progress)
        visual_card = QFrame()
        visual_card.setObjectName('card')
        visual_row = QHBoxLayout(visual_card)
        visual_row.setContentsMargins(19, 16, 19, 16)
        visual_words = QVBoxLayout()
        visual_words.addWidget(label('Visual search · NanoDet'))
        self.visual_model_state = label('', 'subtle')
        visual_words.addWidget(self.visual_model_state)
        visual_row.addLayout(visual_words, 1)
        self.visual_download = button('Download', self.download_visual, True)
        visual_row.addWidget(self.visual_download)
        layout.addWidget(visual_card)
        analytics_card = QFrame()
        analytics_card.setObjectName('card')
        analytics_row = QHBoxLayout(analytics_card)
        analytics_row.setContentsMargins(19, 16, 19, 16)
        analytics_words = QVBoxLayout()
        analytics_words.addWidget(label('Local performance history'))
        self.analytics_state = label('', 'subtle')
        self.analytics_state.setWordWrap(True)
        analytics_words.addWidget(self.analytics_state)
        analytics_row.addLayout(analytics_words, 1)
        analytics_row.addWidget(button('Open performance data', self.open_analytics))
        layout.addWidget(analytics_card)
        storage = QHBoxLayout()
        storage.addWidget(button('Open app data', lambda: open_path(core.DATA)))
        storage.addWidget(button('Open recoverable model removals', self.open_removed_models))
        storage.addStretch()
        layout.addLayout(storage)
        note = label('Automatic mode prefers the NVIDIA GPU and falls back to CPU if the GPU runtime fails.\nScene mode detects visual cuts; it may miss gradual transitions.\nPause and cancel take effect at the next decoded frame or transcript segment.', 'subtle')
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch()
        self.refresh_models()
        return page

    def open_removed_models(self):
        p = core.DATA / 'removed-models'
        p.mkdir(parents=True, exist_ok=True)
        open_path(p)

    def open_analytics(self):
        target = core.analytics_file()
        target.parent.mkdir(parents=True, exist_ok=True)
        open_path(target if target.exists() else target.parent)

    def run_task(self, fn, done, message=None):
        task = Task(fn, self)
        self.tasks.append(task)
        task.done.connect(done)
        task.error.connect(lambda err: QMessageBox.warning(self, 'Could not finish', err))
        if message:
            task.message.connect(message)
        task.finished.connect(lambda: self.tasks.remove(task))
        task.finished.connect(task.deleteLater)
        task.start()
        return task

    def first_setup(self):
        if not core.model_ready('tiny'):
            self.download('tiny')
        elif not core.visual_model_ready():
            self.download_visual()

    def refresh_models(self):
        for key, (state, dl, rm) in self.model_rows.items():
            ready = core.model_ready(key)
            state.setText(('Installed · ' + size_text(core.model_bytes(key))) if ready else 'Optional download · approximately ' + core.MODEL_INFO[key][1])
            dl.setText('Installed' if ready else 'Download')
            dl.setEnabled(not ready and not self.downloading and not self.batch)
            rm.setEnabled(ready and not self.downloading and not self.batch)
        if hasattr(self, 'visual_model_state'):
            ready = core.visual_model_ready()
            size = core.visual_model_path().stat().st_size if ready else 4_000_000
            self.visual_model_state.setText(('Installed · ' if ready else 'Included with 1.11 · approximately ') + size_text(size))
            self.visual_download.setText('Installed' if ready else 'Download')
            self.visual_download.setEnabled(not ready and not self.downloading and not self.batch)
        if hasattr(self, 'analytics_state'):
            target = core.analytics_file()
            try:
                runs = sum(1 for line in target.open(encoding='utf-8') if line.strip())
                self.analytics_state.setText(f'{runs:,} processing events · {size_text(target.stat().st_size)} · stored only on this computer')
            except FileNotFoundError:
                self.analytics_state.setText('Ready · the first processing run will create the local history file')

    def download_visual(self):
        if self.downloading or self.batch:
            return
        self.downloading = True
        self.download_status.setText('Downloading the small offline visual search model…')
        self.download_progress.setRange(0, 0)
        self.download_progress.show()
        self.refresh_models()
        task = self.run_task(lambda notify: core.download_visual_model(notify), lambda _: None,
                             self.download_status.setText)
        task.error.connect(lambda err: self.download_status.setText('Visual model download failed. ' + err))
        task.finished.connect(self.download_finished)

    def download(self, key):
        if self.downloading or self.batch:
            return
        self.downloading = True
        self.download_status.setText(f'Downloading {core.MODEL_INFO[key][0]}… You can prepare your folder queue while this runs.')
        self.download_progress.setRange(0, 0)
        self.download_progress.show()
        self.refresh_models()
        task = self.run_task(lambda notify: core.download_model(key, notify), lambda _: None, self.download_status.setText)
        task.error.connect(lambda err: self.download_status.setText('Download failed. Check your connection and click Download to resume. ' + err))
        task.finished.connect(self.download_finished)

    def download_finished(self):
        self.downloading = False
        self.download_progress.hide()
        self.refresh_models()

    def remove_model(self, key):
        if QMessageBox.question(self, 'Remove downloaded model?', f'Move {key} to the recoverable removed-models folder? You can restore it manually or download it again.') == QMessageBox.Yes:
            try:
                path = core.remove_model(key)
                self.download_status.setText(f'Moved to {path}. Disk space is retained until you delete that backup.')
                self.refresh_models()
            except Exception as exc:
                QMessageBox.warning(self, 'Removal failed', str(exc))

    def set_recursive(self, enabled):
        self.state['settings']['recursive'] = enabled
        self.save_timer.start(300)

    def new_project(self):
        name, ok = QInputDialog.getText(self, 'New project', 'Project name')
        name = name.strip()
        if not ok or not name:
            return
        project = dict(id=uuid.uuid4().hex, name=name, created=time.time(), folders=[])
        self.state['projects'].append(project)
        self.projects_page.refresh(project['id'])
        self.save()

    def rename_project(self):
        project = self.projects_page.current()
        if not project:
            return
        name, ok = QInputDialog.getText(self, 'Rename project', 'Project name', text=project['name'])
        name = name.strip()
        if ok and name:
            project['name'] = name
            for result in self.state['results']:
                if result.get('project_id') == project['id']:
                    result['project_name'] = name
            self.results.set_records(self.state['results'])
            self.projects_page.refresh(project['id'])
            self.save()

    def remove_project(self):
        project = self.projects_page.current()
        if not project:
            return
        message = (f"Remove “{project['name']}” from the Project Dashboard?\n\n"
                   'Generated transcripts, screenshots, and library entries stay on disk.')
        if QMessageBox.question(self, 'Remove project from dashboard', message) == QMessageBox.Yes:
            self.state['projects'].remove(project)
            self.projects_page.refresh()
            self.save()

    def choose_folders(self, title):
        dialog = QFileDialog(self, title)
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        for view in dialog.findChildren(QAbstractItemView):
            if view.objectName() in ('listView', 'treeView'):
                view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        return dialog.selectedFiles() if dialog.exec() else []

    def add_project_folders(self):
        project = self.projects_page.current()
        if project:
            self.scan_project_sources(project, self.choose_folders('Add project source folders'), explicit=False)

    def add_project_files(self):
        project = self.projects_page.current()
        if not project or self.scanning or self.batch:
            return
        paths, _ = QFileDialog.getOpenFileNames(self, 'Add videos to project', '',
                                                'Video files (*.mp4 *.mkv *.mov *.avi *.webm *.m4v *.mpeg *.mpg *.mts *.m2ts *.wmv *.flv)')
        if paths:
            self.scan_project_sources(project, paths, explicit=True)

    def remove_project_source(self):
        project = self.projects_page.current()
        item = self.projects_page.tree.currentItem()
        if not project or not item:
            return
        folder_id, path = item.data(0, Qt.UserRole)
        folder = next(f for f in project['folders'] if f['id'] == folder_id)
        if path:
            folder['files'] = [v for v in folder['files'] if v['path'] != path]
            if not folder['files']:
                project['folders'].remove(folder)
        else:
            project['folders'].remove(folder)
        self.projects_page.populate_tree()
        self.projects_page.refresh(project['id'])
        self.projects_page.status.setText('Removed from this project. Source files and generated outputs were not deleted.')
        self.save()

    def scan_project_sources(self, project, paths, explicit=False):
        if self.scanning or self.batch or not paths:
            return
        existing = {v['path'].casefold() for f in project.get('folders', []) for v in f.get('files', [])}
        if explicit:
            paths = [p for p in paths if str(Path(p).resolve()).casefold() not in existing]
        else:
            paths = list(dict.fromkeys(str(Path(p).resolve()) for p in paths))
        if not paths:
            self.projects_page.status.setText('Those sources are already in this project.')
            return
        self.scanning = True
        self.set_busy(True)
        self.projects_page.progress.setRange(0, 0)
        self.projects_page.status.setText('Reading project sources…')
        fn = ((lambda notify: core.scan_files(paths, notify)) if explicit else
              (lambda notify: [core.scan_folder(p, self.state['settings']['recursive'], notify) for p in paths]))
        task = self.run_task(fn, lambda folders: self.project_sources_scanned(project['id'], folders),
                             lambda p: self.projects_page.status.setText('Reading · ' + p))
        task.finished.connect(self.project_scan_finished)

    def project_sources_scanned(self, project_id, folders):
        project = next((p for p in self.state['projects'] if p['id'] == project_id), None)
        if not project:
            return
        for incoming in folders:
            target = next((f for f in project['folders'] if f['path'].casefold() == incoming['path'].casefold()), None)
            if target:
                known = {v['path'].casefold() for v in target['files']}
                target['files'].extend(v for v in incoming['files'] if v['path'].casefold() not in known)
            else:
                project['folders'].append(incoming)
        self.projects_page.refresh(project_id)
        self.save()

    def project_scan_finished(self):
        self.scanning = False
        self.set_busy(False)
        self.projects_page.progress.setRange(0, 100)
        self.projects_page.progress.setValue(0)
        self.projects_page.status.setText('Sources added. Uncheck anything you do not want to process.')

    def add_folders(self):
        paths = self.choose_folders('Add folders')
        if paths:
            self.scan_paths(paths)

    def scan_paths(self, paths, replace_id=None):
        if self.scanning or self.batch:
            return
        known = {f['path'].casefold() for f in self.state['folders'] if f['id'] != replace_id}
        paths = list(dict.fromkeys(str(Path(p).resolve()) for p in paths if str(Path(p).resolve()).casefold() not in known))
        if not paths:
            return
        recursive = self.recursive.isChecked()
        self.scanning = True
        self.set_busy(True)
        self.progress.setRange(0, 0)
        task = self.run_task(lambda notify: [core.scan_folder(p, recursive, notify) for p in paths],
                             lambda folders: self.scanned(folders, replace_id),
                             lambda p: self.status.setText('Scanning · ' + p))
        task.finished.connect(self.scan_finished)

    def scanned(self, folders, replace_id):
        if replace_id:
            for i, old in enumerate(self.state['folders']):
                if old['id'] == replace_id:
                    old_files = {v['path']: v for v in old['files']}
                    new = folders[0]
                    new['id'] = replace_id
                    for v in new['files']:
                        if v['path'] in old_files and v['status'] != 'Unreadable':
                            v['selected'] = old_files[v['path']]['selected']
                    self.state['folders'][i] = new
                    break
        else:
            self.state['folders'].extend(folders)
        self.refresh_tree()
        self.save()

    def scan_finished(self):
        self.scanning = False
        self.set_busy(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.status.setText('Folder scan finished. Double-click folders to review file selections.')

    def current_folder(self):
        item = self.tree.currentItem()
        if item:
            value = item.data(0, Qt.UserRole)
            return next((f for f in self.state['folders'] if f['id'] == value[0]), None)

    def rescan_folder(self):
        folder = self.current_folder()
        if folder:
            self.scan_paths([folder['path']], folder['id'])

    def remove_folder(self):
        folder = self.current_folder()
        if folder:
            self.state['folders'].remove(folder)
            self.refresh_tree()
            self.status.setText('Removed from the queue. Source files and generated outputs were not deleted.')
            self.save()

    def move_folder(self, direction):
        folder = self.current_folder()
        if folder:
            folders = self.state['folders']
            i = folders.index(folder)
            j = i + direction
            if 0 <= j < len(folders):
                folders[i], folders[j] = folders[j], folders[i]
                self.refresh_tree()
                self.tree.setCurrentItem(self.tree.topLevelItem(j))
                self.save()

    def refresh_tree(self):
        expanded = {self.tree.topLevelItem(i).data(0, Qt.UserRole)[0] for i in range(self.tree.topLevelItemCount()) if self.tree.topLevelItem(i).isExpanded()}
        self.tree.blockSignals(True)
        self.tree.clear()
        self.item_map.clear()
        for folder in self.state['folders']:
            parent = QTreeWidgetItem([folder['name'], '', ''])
            parent.setToolTip(0, folder['path'])
            parent.setData(0, Qt.UserRole, (folder['id'], None))
            parent.setFlags(parent.flags() | Qt.ItemIsUserCheckable | Qt.ItemIsAutoTristate)
            self.tree.addTopLevelItem(parent)
            for v in folder['files']:
                child = QTreeWidgetItem([v['name'], duration_text(v['duration']), v['status']])
                child.setData(0, Qt.UserRole, (folder['id'], v['path']))
                child.setToolTip(0, v['path'])
                child.setToolTip(2, v.get('error', ''))
                child.setFlags(child.flags() | Qt.ItemIsUserCheckable)
                parent.addChild(child)
                child.setCheckState(0, Qt.Checked if v['selected'] else Qt.Unchecked)
                if v['status'] == 'Unreadable':
                    child.setDisabled(True)
                self.item_map[(folder['id'], v['path'])] = child
            parent.setExpanded(folder['id'] in expanded)
            self.update_folder_row(folder, parent)
        self.tree.blockSignals(False)
        self.update_stats()

    def update_folder_row(self, folder, parent):
        selected = [v for v in folder['files'] if v['selected']]
        completed = sum(v['status'] == 'Completed' for v in selected)
        parent.setText(1, duration_text(sum(v['duration'] for v in selected)))
        parent.setText(2, f"{len(selected)}/{len(folder['files'])} selected · {completed} done")

    def selection_changed(self, item, column):
        if column != 0:
            return
        # Qt propagates folder tri-state checkboxes to children.
        for folder in self.state['folders']:
            for v in folder['files']:
                child = self.item_map[(folder['id'], v['path'])]
                v['selected'] = child.checkState(0) == Qt.Checked and v['status'] != 'Unreadable'
        self.update_stats()
        self.save_timer.start(300)

    def update_stats(self):
        files = [v for f in self.state['folders'] for v in f['files'] if v['selected']]
        for w, text in zip(self.stats, (str(len(self.state['folders'])), str(len(files)), duration_text(sum(v['duration'] for v in files)))):
            w.setText(text)
        self.empty.setVisible(not self.state['folders'])
        if not self.batch:
            self.progress_detail.setText(f"{len(files)} {'video' if len(files) == 1 else 'videos'} ready")
        self.process.setEnabled(bool(files) and not self.batch and not self.scanning)
        self.tree.blockSignals(True)
        for i, folder in enumerate(self.state['folders']):
            self.update_folder_row(folder, self.tree.topLevelItem(i))
        self.tree.blockSignals(False)

    def set_busy(self, busy):
        for widget in (self.add_button, self.recursive, self.remove, self.rescan, self.up, self.down, self.tree):
            widget.setEnabled(not busy)
        self.process.setEnabled(not busy and any(v['selected'] for f in self.state['folders'] for v in f['files']))
        if hasattr(self, 'projects_page'):
            self.projects_page.set_busy(busy)

    def process_folders(self):
        dialog = OptionsDialog(self.state['settings'], self.state['folders'], self)
        if dialog.exec() != QDialog.Accepted:
            return
        self.state['settings'] = dialog.options
        self.start_batch(self.state['folders'], dialog.options, ('folders', None))

    def process_project(self):
        project = self.projects_page.current()
        if not project:
            return
        dialog = OptionsDialog(self.state['settings'], project['folders'], self, 'project · ' + project['name'])
        if dialog.exec() != QDialog.Accepted:
            return
        self.state['settings'] = dialog.options
        options = {**dialog.options, 'project_id': project['id'], 'project_name': project['name']}
        self.start_batch(project['folders'], options, ('project', project['id']))

    def start_batch(self, folders, options, context):
        for folder in folders:
            for video in folder['files']:
                if video['selected'] and video['status'] != 'Unreadable':
                    video.update(status='Queued', error='')
        self.batch_context = context
        self.batch_percent = 0
        if context[0] == 'folders':
            self.refresh_tree()
        else:
            self.projects_page.populate_tree()
        self.save()
        self.batch = Batch(folders, options, self)
        self.batch.event.connect(self.batch_event)
        self.batch.finished.connect(self.batch_finished)
        self.set_busy(True)
        self.pause.setEnabled(True)
        self.cancel.setEnabled(True)
        self.projects_page.pause.setEnabled(True)
        self.projects_page.cancel.setEnabled(True)
        self.progress.setValue(0)
        self.progress.setFormat('0% of total batch')
        self.progress_detail.setText('0 of 0 videos')
        self.projects_page.progress.setValue(0)
        self.projects_page.progress.setFormat('0% of project batch')
        self.projects_page.progress_detail.setText('0 of 0 videos')
        self.refresh_models()
        self.batch.start()

    def batch_event(self, folder_id, path, kind, value):
        if self.batch_context and self.batch_context[0] == 'project':
            project = next(p for p in self.state['projects'] if p['id'] == self.batch_context[1])
            folders = project['folders']
            item_map = self.projects_page.item_map
            status_label = self.projects_page.status
        else:
            project = None
            folders = self.state['folders']
            item_map = self.item_map
            status_label = self.status
        folder = next(f for f in folders if f['id'] == folder_id)
        v = next(v for v in folder['files'] if v['path'] == path)
        item = item_map[(folder_id, path)]
        if kind in ('status', 'error'):
            v['status'] = value if kind == 'status' else 'Failed'
            if kind == 'error':
                v['error'] = value
                item.setToolTip(2, value)
            item.setText(2, v['status'])
            status_label.setText(f"{folder['name']} / {v['name']} · {value}")
            if project:
                self.projects_page.update_summary()
            else:
                self.update_stats()
            self.save_timer.start(200)
        elif kind in ('frames', 'transcript', 'visual'):
            t, n = value
            what = {'frames': 'screenshots', 'transcript': 'transcript segments',
                    'visual': 'indexed moments'}[kind]
            status_label.setText(f"{folder['name']} / {v['name']} · {n:,} {what} · {duration_text(t)} / {duration_text(v['duration'])}")
        elif kind == 'overall':
            self.batch_percent = value['percent']
            progress = self.projects_page.progress if project else self.progress
            detail = self.projects_page.progress_detail if project else self.progress_detail
            progress.setValue(value['percent'])
            progress.setFormat(f"{value['percent']}% of {'project' if project else 'total'} batch")
            detail.setText(f"{value['done']} of {value['total']} videos")
        elif kind == 'notice':
            status_label.setText(f"{v['name']} · {value}")
        elif kind == 'result':
            if project:
                value['project_id'] = project['id']
                value['project_name'] = project['name']
            if not any(r['id'] == value['id'] for r in self.state['results']):
                self.state['results'].append(value)
            v['output'] = value['output']
            self.results.set_records(self.state['results'])
            self.save()

    def pause_batch(self):
        if self.batch:
            status = self.projects_page.status if self.batch_context[0] == 'project' else self.status
            if self.batch.control.running.is_set():
                self.batch.control.running.clear()
                self.pause.setText('Resume')
                self.projects_page.pause.setText('Resume')
                status.setText('Pausing at the next frame or transcript segment…')
            else:
                self.batch.control.running.set()
                self.pause.setText('Pause')
                self.projects_page.pause.setText('Pause')
                status.setText('Resuming batch…')

    def cancel_batch(self):
        if self.batch:
            self.batch.control.cancel.set()
            self.batch.control.running.set()
            self.pause.setEnabled(False)
            self.cancel.setEnabled(False)
            self.projects_page.pause.setEnabled(False)
            self.projects_page.cancel.setEnabled(False)
            status = self.projects_page.status if self.batch_context[0] == 'project' else self.status
            status.setText('Cancelling… Current model computation may need to finish its segment.')

    def batch_finished(self):
        context = self.batch_context
        cancelled_batch = self.batch.cancelled
        self.batch.deleteLater()
        self.batch = None
        self.pause.setEnabled(False)
        self.cancel.setEnabled(False)
        self.pause.setText('Pause')
        self.projects_page.pause.setEnabled(False)
        self.projects_page.cancel.setEnabled(False)
        self.projects_page.pause.setText('Pause')
        self.set_busy(False)
        if context[0] == 'project':
            project = next(p for p in self.state['projects'] if p['id'] == context[1])
            folders = project['folders']
            progress = self.projects_page.progress
            status = self.projects_page.status
            self.projects_page.refresh(project['id'])
        else:
            folders = self.state['folders']
            progress = self.progress
            status = self.status
        if not cancelled_batch:
            progress.setValue(100)
            self.batch_percent = 100
        selected = [v for f in folders for v in f['files'] if v['selected']]
        done = sum(v['status'] == 'Completed' for v in selected)
        failed = sum(v['status'] == 'Failed' for v in selected)
        cancelled = sum(v['status'] == 'Cancelled' for v in selected)
        status.setText(f'Batch finished at {self.batch_percent}% · {done} completed · {failed} failed · {cancelled} cancelled.')
        self.batch_context = None
        self.refresh_models()
        self.save()

    def save(self):
        try:
            core.atomic_json(core.DATA / 'library.json', self.state)
        except OSError as exc:
            self.status.setText('Could not save the library: ' + str(exc))

    def closeEvent(self, event):
        if self.batch or self.scanning or self.downloading:
            QMessageBox.information(self, 'Work is still running', 'Cancel the batch and wait for it to stop before closing. Scans and model downloads must finish first.')
            event.ignore()
            return
        if self.tasks:
            event.ignore()
            return
        self.results.player.stop()
        self.save()
        event.accept()


def main():
    core.DATA.mkdir(parents=True, exist_ok=True)
    if sys.stdout is None:
        sys.stdout = open(core.DATA / 'runtime.log', 'a', encoding='utf-8', buffering=1)
    if sys.stderr is None:
        sys.stderr = sys.stdout
    if '--self-check' in sys.argv:
        return packaged_check()
    app = QApplication(sys.argv)
    configure_fonts()
    app.setApplicationName('Tracer')
    app.setOrganizationName('Tracer')
    app.setWindowIcon(QIcon(str(Path(getattr(sys, '_MEIPASS', core.ROOT)) / 'assets' / 'transpro.svg')))
    lock = QLockFile(str(core.DATA / 'app.lock'))
    if not lock.tryLock(0):
        QMessageBox.information(None, 'Tracer is open', 'Tracer is already running. Switch to its existing window.')
        return 0
    app.setStyle('Fusion')
    app.setStyleSheet(STYLE)
    window = Window()
    window.show()
    return app.exec()


def configure_fonts():
    # Explicit loading also supports the headless screenshot verification platform.
    fonts = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'
    for name in ('segoeui.ttf', 'segoeuib.ttf', 'seguisb.ttf'):
        if (fonts / name).exists():
            QFontDatabase.addApplicationFont(str(fonts / name))


def packaged_check():
    """Exercise the distributed executable without opening a window."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-check', action='store_true')
    parser.add_argument('--media', required=True)
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    try:
        source = Path(args.media)
        video = {'path': str(source), 'selected': True, 'status': 'Ready', **core.probe(source)}
        options = {**core.DEFAULTS, 'device': 'cuda', 'language': 'en', 'interval': .5, 'skip_existing': False,
                   'output': str(Path(args.report).parent)}
        transcriber = core.Transcriber()
        both = core.process_video(source.parent, video, options, core.Control(), transcriber, lambda *_: None)
        only = core.process_video(source.parent, video, {**options, 'screenshots': False, 'visual_index': False}, core.Control(), transcriber, lambda *_: None)
        assert both['segments'] and both['frames'] and both['device'] == 'cuda'
        assert only['segments'] and not Path(only['output'], 'screenshots').exists()
        core.atomic_json(args.report, {'passed': True, 'gpu': core.gpu_info(), 'combined': both, 'transcription_only': only})
        return 0
    except Exception as exc:
        import traceback
        core.atomic_json(args.report, {'passed': False, 'error': str(exc), 'traceback': traceback.format_exc()})
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
