from __future__ import annotations

import copy
import ctypes
import html
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

from PySide6.QtCore import (Qt, QThread, Signal, QTimer, QUrl, QSize, QPoint, QLockFile, QEvent,
                            QPropertyAnimation, QEasingCurve, Property)
from PySide6.QtGui import (QColor, QDesktopServices, QFont, QFontDatabase, QIcon, QPixmap, QImage,
                           QPainter, QPen, QBrush, QKeySequence, QShortcut, QTextCharFormat, QTextCursor, QTextDocument)
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTreeWidget, QTreeWidgetItem, QHeaderView, QAbstractItemView,
    QStackedWidget, QFileDialog, QMessageBox, QDialog, QFormLayout, QComboBox,
    QCheckBox, QDoubleSpinBox, QSlider, QSpinBox, QLineEdit, QProgressBar,
    QSplitter, QListWidget, QListWidgetItem, QTextBrowser, QTextEdit, QFrame, QScrollArea,
    QInputDialog, QButtonGroup, QToolButton, QToolTip, QMenu, QGraphicsBlurEffect,
    QStyledItemDelegate, QStyle, QStyleOptionViewItem, QSizePolicy)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget

import core
import paper_edit
import timeline
import workspace


def enable_high_dpi():
    """Use native pixel density on Windows and avoid rounded blurry scaling."""
    os.environ.setdefault('QT_ENABLE_HIGHDPI_SCALING', '1')
    os.environ.setdefault('QT_SCALE_FACTOR_ROUNDING_POLICY', 'PassThrough')
    if sys.platform == 'win32':
        try:
            ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        except (AttributeError, OSError):
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except (AttributeError, OSError):
                pass


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
QPushButton#queueDelete { background: #252422; border: 1px solid #514d47; border-radius: 3px; padding: 0; }
QPushButton#queueDelete:hover { background: #32191a; border-color: #8f4144; }
QPushButton#libraryPrimary { background: #9bbfce; color: #102128; border: 1px solid #b8d5df; font-weight: 650; }
QPushButton#libraryPrimary:hover { background: #b2d1dd; }
QPushButton#mediaIcon { background: #232321; border: 1px solid #484640; padding: 3px; border-radius: 4px; }
QPushButton#mediaIcon:hover { background: #30302d; border-color: #858078; }
QPushButton#danger { color: #d79882; }
QPushButton#timelineTool { padding: 6px 8px; font-size: 12px; }
QPushButton#segment { padding: 6px 12px; color: #aaa69f; background: #1d1d1c; }
QPushButton#segment:checked { color: #f4e9e1; background: #493128; border-color: #c86f50; }
QPushButton#segment:disabled { color: #625f59; background: #191918; border-color: #292826; }
QPushButton#formatLeft, QPushButton#formatRight { padding: 5px 10px; color: #aaa69f; background: #171716; border: 1px solid #45423e; }
QPushButton#formatLeft { border-radius: 4px 0 0 4px; border-right: 0; }
QPushButton#formatRight { border-radius: 0 4px 4px 0; }
QPushButton#formatLeft:checked, QPushButton#formatRight:checked { color: #16120f; background: #d28a6e; border-color: #d28a6e; font-weight: 700; }
QPushButton#formatLeft:disabled, QPushButton#formatRight:disabled { color: #57544f; background: #181817; border-color: #292826; }
QToolButton#nav { border: 0; border-left: 2px solid transparent; background: transparent; padding: 7px 3px; color: #aaa69f; font-size: 10px; }
QToolButton#nav:hover { color: #f2ece4; background: #1a1918; }
QToolButton#nav:checked { color: #f2ece4; background: #201c19; border-left-color: #d78061; }
QLabel#resourceMeter { color: rgba(255,255,255,150); font-size: 9px; font-weight: 350; padding: 1px 0; }
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
QWidget#paperPage { background: #151515; color: #e8e3da; }
QWidget#paperPage QLabel { background: transparent; color: #e8e3da; }
QWidget#paperPage QLabel#paperTitle { font-family: Georgia; font-size: 28px; font-weight: 600; color: #f1ece4; }
QWidget#paperPage QLabel#paperEmptyTitle { font-family: Georgia; font-size: 20px; font-weight: 600; color: #e8e3da; }
QWidget#paperPage QLabel#paperEyebrow { color: #d78061; font-size: 10px; font-weight: 700; letter-spacing: 1px; }
QWidget#paperPage QLabel#paperSubtle { color: #99958e; }
QWidget#paperPage QFrame#paperRail, QWidget#paperPage QFrame#paperCard,
QWidget#paperPage QWidget#paperSheet { background: #1d1d1c; border: 1px solid #34322f; }
QWidget#paperPage QFrame#paperSegment { background: transparent; border: 0; border-bottom: 1px solid #302e2b; }
QWidget#paperPage QFrame#paperSegment[highlighted="true"] { background: #443820; }
QWidget#paperPage QLineEdit, QWidget#paperPage QTextEdit, QWidget#paperPage QTextBrowser,
QWidget#paperPage QListWidget { background: #191919; color: #e8e3da; border: 1px solid #3a3733; selection-background-color: #483128; selection-color: #fff5ee; }
QWidget#paperPage QLineEdit { padding: 7px 9px; border-radius: 4px; }
QWidget#paperPage QTextEdit { background: transparent; border: 0; font-family: 'Cascadia Mono', Consolas; font-size: 14px; }
QWidget#paperPage QPushButton, QWidget#paperPage QToolButton { background: #252422; color: #e8e3da; border: 1px solid #403d38; padding: 7px 11px; border-radius: 4px; }
QWidget#paperPage QPushButton:hover, QWidget#paperPage QToolButton:hover { background: #302e2b; border-color: #777067; }
QWidget#paperPage QPushButton#paperPrimary { background: #c86f50; color: #16120f; border-color: #e08a68; font-weight: 650; }
QWidget#paperPage QPushButton#paperPrimary:hover { background: #df8060; }
QWidget#paperPage QPushButton#paperPrimary:disabled { background: #493127; color: #846456; border-color: #53382d; }
QWidget#paperPage QToolButton:checked { background: #443820; color: #f5e7bd; border-color: #b88a31; }
QWidget#paperPage QScrollArea { background: #151515; border: 0; }
QWidget#paperPage QSplitter::handle:horizontal { background: #3b3935; width: 3px; margin: 8px 2px; }
QWidget#paperPage QSplitter::handle:horizontal:hover { background: #d78061; }
QWidget#paperPage QCheckBox { color: #e8e3da; background: transparent; }
'''


# The 1.17 desk uses restrained graphite surfaces and crisp, compact controls.
STYLE += '''
QWidget { background: #14181b; color: #dce1e5; }
QMainWindow { background: #111518; }
QLabel { background: transparent; }
QLabel#subtle, QLabel#paperSubtle { color: #9aa6ae; }
QLabel#title { font-size: 22px; }
QLabel#eyebrow { color: #a9b4bc; font-size: 10px; }
QFrame#sidebar { background: #101417; border-right: 1px solid #30383e; }
QToolButton#nav { padding: 6px 1px; color: #b7c1c8; font-size: 10px; }
QToolButton#nav:checked { background: #27221e; color: #f39754; border-left: 2px solid #f18b45; }
QToolButton#nav:hover { background: #20272c; }
QFrame#card, QFrame#paperCard, QFrame#paperRail { background: #191e22; border: 1px solid #303940; border-radius: 4px; }
QPushButton { background: #22292e; border: 1px solid #38434b; padding: 6px 10px; border-radius: 4px; }
QPushButton:hover { background: #2b353c; border-color: #667986; }
QPushButton#primary, QPushButton#paperPrimary { background: #e68b4f; color: #17191b; border-color: #f49b60; }
QPushButton:focus, QToolButton:focus, QLineEdit:focus, QListWidget:focus, QTextEdit:focus { border: 1px solid #659ed3; }
QTreeWidget, QListWidget, QTextBrowser { background: #171c20; border: 1px solid #303940; }
QTreeWidget::item:selected, QListWidget::item:selected { background: #36302a; color: #fff3e7; }
QListWidget::item { border-bottom: 1px solid #293238; padding: 8px; }
QHeaderView::section { background: #20272c; color: #aeb9c1; border-bottom: 1px solid #343e46; padding: 7px; }
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox { background: #1c2328; border: 1px solid #39454e; padding: 6px 8px; color: #dce1e5; }
QMenu { background: #20272c; color: #dce1e5; border: 1px solid #45545f; padding: 5px; }
QMenu::item { padding: 7px 24px 7px 12px; }
QMenu::item:selected { background: #38434b; }
QMenu::separator { height: 1px; background: #3a444c; margin: 5px; }
QMenu::item:disabled { color: #77848e; }
QWidget#workspaceBar { background: #14191d; border-bottom: 1px solid #303940; }
QLabel#workspaceTitle { font-size: 16px; font-weight: 600; color: #e7edf1; }
QWidget#paperPage { background: #14181b; }
QWidget#paperPage QLabel { color: #dce1e5; }
QWidget#paperPage QWidget#paperSheet { background: #171c20; border: 0; }
QWidget#paperPage QTextEdit { font-family: 'Segoe UI'; font-size: 13px; background: transparent; color: #dce1e5; border: 0; }
QWidget#paperPage QLineEdit { background: #1c2328; color: #dce1e5; border: 1px solid #39454e; padding: 5px 7px; }
QWidget#paperPage QListWidget { background: #171c20; border: 0; color: #dce1e5; }
QWidget#paperPage QScrollArea { background: #171c20; border: 0; }
QWidget#paperPage QPushButton, QWidget#paperPage QToolButton { padding: 5px 7px; background: #22292e; border: 1px solid #38434b; color: #dce1e5; }
QWidget#paperPage QPushButton#paperPrimary { background: #e68b4f; color: #17191b; border-color: #f49b60; }
QWidget#paperPage QFrame#paperSegment { border: 0; border-bottom: 1px solid #2b343a; }
QWidget#paperPage QFrame#paperSegment[highlighted="true"] { background: #393322; }
QWidget#panelHeader { background: #1b2126; border-bottom: 1px solid #303940; }
QLabel#panelTitle { background: transparent; font-size: 12px; font-weight: 600; }
QDockWidget { border: 1px solid #303940; }
QMainWindow#modularWorkspace { background: #101518; }
QMainWindow::separator { width: 6px; height: 6px; background: #101518; }
QMainWindow::separator:hover { background: #db8a50; }
QToolButton#deskTool, QWidget#paperPage QToolButton#deskTool { background: transparent; border: 1px solid transparent; padding: 3px; }
QToolButton#deskTool:hover, QWidget#paperPage QToolButton#deskTool:hover { background: #303b43; border-color: #4a5b68; }
QToolButton#layoutButton { background: #232b31; border: 1px solid #3a464f; padding: 6px 10px; border-radius: 4px; }
QToolButton#workspaceMode, QWidget#paperPage QToolButton#workspaceMode { background: transparent; border: 0; border-bottom: 2px solid transparent; border-radius: 0; padding: 8px 14px; }
QToolButton#workspaceMode:checked, QWidget#paperPage QToolButton#workspaceMode:checked { color: #f49b60; background: #232321; border-bottom: 2px solid #ed8e4e; }
QToolButton#workspaceMode:hover { background: #242d33; }
QSlider::groove:horizontal { background: #3b474f; height: 3px; }
QSlider::sub-page:horizontal { background: #e38b50; }
QSlider::handle:horizontal { background: #ec945b; border: 2px solid #171c20; }
QScrollBar:horizontal { background: #161c20; height: 10px; }
QScrollBar::handle:horizontal { background: #48555f; min-width: 28px; border-radius: 4px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QScrollBar:vertical { background: #161c20; width: 9px; }
QScrollBar::handle:vertical { background: #48555f; border-radius: 4px; }
QTabBar::tab { background: #1b2227; color: #b8c2ca; padding: 7px 14px; border: 1px solid #34414a; }
QTabBar::tab:selected { color: #f3a66f; border-bottom: 2px solid #e38b50; }
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
    pixmap = QPixmap(88, 68)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    icon_colours = {'audio': '#c2addb', 'frame': '#94c1d3', 'ai': '#a7cdb5'}
    # Functional glyphs stay fully opaque white. Output-type glyphs retain their
    # distinctive colours so Transcript, Screenshots, and Visual remain scannable.
    colour = colour_override or icon_colours.get(kind, '#ffffff')
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
    elif kind == 'queue':
        painter.drawRoundedRect(7, 8, 30, 20, 3, 3)
        painter.drawLine(12, 14, 31, 14)
        painter.drawLine(12, 21, 27, 21)
        painter.drawLine(32, 18, 36, 18)
        painter.drawLine(34, 16, 34, 20)
    elif kind == 'projects':
        painter.drawRoundedRect(6, 9, 32, 20, 3, 3)
        painter.drawLine(10, 9, 15, 4)
        painter.drawLine(15, 4, 24, 4)
        painter.drawLine(24, 4, 28, 9)
        painter.drawLine(12, 17, 31, 17)
        painter.drawLine(12, 23, 27, 23)
    elif kind == 'paper':
        painter.drawRoundedRect(9, 4, 25, 27, 2, 2)
        painter.drawLine(15, 11, 29, 11)
        painter.drawLine(15, 17, 29, 17)
        painter.drawLine(15, 23, 25, 23)
        painter.drawLine(31, 25, 39, 17)
    elif kind == 'storyline':
        painter.drawLine(5, 11, 39, 11)
        painter.drawLine(5, 23, 39, 23)
        painter.drawRoundedRect(8, 7, 13, 8, 2, 2)
        painter.drawRoundedRect(22, 19, 14, 8, 2, 2)
    elif kind == 'library':
        painter.drawRoundedRect(6, 6, 32, 22, 3, 3)
        painter.drawLine(17, 11, 17, 23)
        painter.drawLine(17, 11, 28, 17)
        painter.drawLine(28, 17, 17, 23)
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
    elif kind == 'trash':
        painter.setPen(QPen(QColor(colour), 2.3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.drawRoundedRect(13, 10, 18, 20, 2, 2)
        painter.drawLine(10, 8, 34, 8)
        painter.drawLine(18, 5, 26, 5)
        painter.drawLine(18, 14, 18, 25)
        painter.drawLine(26, 14, 26, 25)
    elif kind in ('arrow_left', 'arrow_right'):
        if kind == 'arrow_left':
            painter.drawLine(28, 7, 18, 17)
            painter.drawLine(18, 17, 28, 27)
        else:
            painter.drawLine(16, 7, 26, 17)
            painter.drawLine(26, 17, 16, 27)
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


def trash_icon(colour='#ffffff'):
    """Render the queue trash glyph at display size for a sharp, opaque mark."""
    pixmap = QPixmap(48, 48)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor(colour), 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(Qt.NoBrush)
    painter.drawRoundedRect(6, 7, 12, 14, 2, 2)
    painter.drawLine(4, 5, 20, 5)
    painter.drawLine(9, 2, 15, 2)
    painter.drawLine(10, 10, 10, 17)
    painter.drawLine(14, 10, 14, 17)
    painter.end()
    return QIcon(pixmap)


def paper_icon(kind, colour='#e8e3da'):
    """High-DPI line icons for the Paper Edit visual language."""
    pixmap = QPixmap(48, 48)
    pixmap.setDevicePixelRatio(2.0)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor(colour), 1.7, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    painter.setBrush(Qt.NoBrush)
    if kind == 'pen':
        painter.drawLine(6, 18, 17, 7)
        painter.drawLine(9, 21, 20, 10)
        painter.drawLine(6, 18, 5, 22)
        painter.drawLine(5, 22, 9, 21)
    elif kind == 'marker':
        painter.drawLine(6, 17, 16, 7)
        painter.drawLine(10, 21, 20, 11)
        painter.drawLine(6, 17, 10, 21)
        painter.drawLine(5, 23, 16, 23)
    elif kind == 'library':
        painter.drawRoundedRect(4, 5, 16, 15, 2, 2)
        painter.drawLine(9, 10, 9, 16)
        painter.drawLine(9, 10, 15, 13)
        painter.drawLine(15, 13, 9, 16)
    elif kind == 'export':
        painter.drawRoundedRect(5, 10, 14, 11, 2, 2)
        painter.drawLine(12, 3, 12, 16)
        painter.drawLine(8, 7, 12, 3)
        painter.drawLine(12, 3, 16, 7)
    elif kind == 'undo':
        painter.drawArc(5, 7, 15, 13, 35 * 16, 245 * 16)
        painter.drawLine(5, 8, 5, 3)
        painter.drawLine(5, 8, 10, 8)
    elif kind == 'clear':
        painter.drawLine(6, 6, 18, 18)
        painter.drawLine(18, 6, 6, 18)
    painter.end()
    return QIcon(pixmap)


class QueueDeleteButton(QPushButton):
    """High-contrast queue removal action with an explicit danger hover."""
    def __init__(self, parent=None):
        super().__init__('', parent)
        self.setIconSize(QSize(24, 24))
        self._sync_icon()

    def _sync_icon(self):
        colour = '#ff3b45' if self.isEnabled() and self.underMouse() else '#ffffff'
        self.setIcon(trash_icon(colour))

    def enterEvent(self, event):
        super().enterEvent(event)
        self._sync_icon()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self._sync_icon()

    def changeEvent(self, event):
        super().changeEvent(event)
        if event.type() == QEvent.EnabledChange:
            self._sync_icon()


def partition_media_paths(paths):
    """Return unique existing folders and supported videos from one selection."""
    folders, videos, seen = [], [], set()
    for value in paths:
        path = Path(value)
        if not path.exists():
            continue
        resolved = str(path.resolve())
        key = resolved.casefold()
        if key in seen:
            continue
        seen.add(key)
        if path.is_dir():
            folders.append(resolved)
        elif path.is_file() and path.suffix.casefold() in core.EXTENSIONS:
            videos.append(resolved)
    return folders, videos


class MediaPickerDialog(QFileDialog):
    """One read-only picker that accepts folders and supported videos together."""
    VIDEO_FILTER = (
        'Folders and video files '
        '(*.mp4 *.mkv *.mov *.avi *.webm *.m4v *.mpeg *.mpg *.mts *.m2ts *.wmv *.flv)'
    )

    def __init__(self, parent=None):
        super().__init__(parent, 'Add media', str(Path.home()), self.VIDEO_FILTER)
        self._media_paths = []
        self.setOption(QFileDialog.DontUseNativeDialog, True)
        self.setOption(QFileDialog.ReadOnly, True)
        self.setFileMode(QFileDialog.ExistingFiles)
        self.setAcceptMode(QFileDialog.AcceptOpen)
        self.setViewMode(QFileDialog.Detail)
        self.setLabelText(QFileDialog.Accept, 'Add selected')
        self.setWindowTitle('Add media')
        self.resize(940, 620)
        QTimer.singleShot(0, self._enable_extended_selection)

    def _enable_extended_selection(self):
        for view in self.findChildren(QAbstractItemView):
            view.setSelectionMode(QAbstractItemView.ExtendedSelection)

    @staticmethod
    def _index_path(index):
        model = index.model()
        if hasattr(model, 'filePath'):
            return model.filePath(index)
        if hasattr(model, 'mapToSource') and hasattr(model, 'sourceModel'):
            source_index = model.mapToSource(index)
            source_model = model.sourceModel()
            if hasattr(source_model, 'filePath'):
                return source_model.filePath(source_index)
        return ''

    def selected_media_paths(self):
        candidates = list(self.selectedFiles())
        for view in self.findChildren(QAbstractItemView):
            selection = view.selectionModel()
            if selection is None:
                continue
            for index in selection.selectedRows(0):
                path = self._index_path(index)
                if path:
                    candidates.append(path)
        folders, videos = partition_media_paths(candidates)
        return folders + videos

    def accept(self):
        self._media_paths = self.selected_media_paths()
        if not self._media_paths:
            QMessageBox.information(
                self, 'Choose media',
                'Select one or more folders or supported video files, then choose Add selected.')
            return
        QDialog.accept(self)

    def media_paths(self):
        return list(self._media_paths)


def highlighted_parts(text, query):
    """Split text into normal/matching runs for case-insensitive result emphasis."""
    query = query.strip()
    if not query:
        return [(text, False)]
    parts, cursor = [], 0
    for match in re.finditer(re.escape(query), text, re.IGNORECASE):
        if match.start() > cursor:
            parts.append((text[cursor:match.start()], False))
        parts.append((text[match.start():match.end()], True))
        cursor = match.end()
    if cursor < len(text):
        parts.append((text[cursor:], False))
    return parts or [(text, False)]


def classified_highlighted_parts(text, query):
    """Return normal, direct-prefix, and embedded runs for search rendering."""
    query = query.strip()
    if not query:
        return [(text, None)]
    parts, cursor = [], 0
    for match in re.finditer(re.escape(query), text, re.IGNORECASE):
        if match.start() > cursor:
            parts.append((text[cursor:match.start()], None))
        previous = text[match.start() - 1] if match.start() else ''
        kind = 'embedded' if previous and (previous.isalnum() or previous == '_') else 'direct'
        parts.append((text[match.start():match.end()], kind))
        cursor = match.end()
    if cursor < len(text):
        parts.append((text[cursor:], None))
    return parts or [(text, None)]


def query_hit_counts(values, query):
    """Count query occurrences that start a token versus occur inside one."""
    direct = embedded = 0
    query = query.strip()
    if not query:
        return direct, embedded
    for value in values:
        for match in re.finditer(re.escape(query), str(value), re.IGNORECASE):
            previous = str(value)[match.start() - 1] if match.start() else ''
            if previous and (previous.isalnum() or previous == '_'):
                embedded += 1
            else:
                direct += 1
    return direct, embedded


def search_origins(record, query):
    """Describe which independent Library indexes produced a result."""
    query = query.strip()
    if not query:
        return ()
    folded = query.casefold()
    origins = []
    filename = Path(record.get('source', '')).name + ' ' + record.get('project_name', '')
    if folded in filename.casefold():
        origins.append('filename')
    if any(folded in segment.get('text', '').casefold() for segment in record.get('segments', [])):
        origins.append('transcript')
    try:
        from vision_index import frame_match
        if any(frame_match(frame, query)[0] for frame in record.get('visual_index', {}).get('frames', [])):
            origins.append('visual')
    except (ImportError, TypeError, ValueError):
        pass
    return tuple(origins)


def paint_origin_icons(painter, origins, right, top, selected=False):
    kinds = {'transcript': 'audio', 'visual': 'ai', 'filename': 'projects'}
    colours = {'transcript': '#51c8f9', 'visual': '#20d666', 'filename': '#f9cf58'}
    x = right - len(origins) * 24
    for origin in origins:
        tile_icon(kinds[origin], colours[origin]).paint(painter, x, top, 22, 20)
        x += 24


def search_origin_icon(origins):
    width = max(24, len(origins) * 24)
    pixmap = QPixmap(width, 22)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    paint_origin_icons(painter, origins, width, 1)
    painter.end()
    return QIcon(pixmap)


class SearchHighlightDelegate(QStyledItemDelegate):
    """Draw only the searched words with an opaque accent highlight."""
    def __init__(self, query, parent=None):
        super().__init__(parent)
        self.query = query

    def paint(self, painter, option, index):
        text = index.data(Qt.DisplayRole) or ''
        parts = classified_highlighted_parts(text, self.query())
        if not any(kind for _, kind in parts):
            super().paint(painter, option, index)
            return
        styled = QStyleOptionViewItem(option)
        self.initStyleOption(styled, index)
        styled.text = ''
        style = styled.widget.style() if styled.widget else QApplication.style()
        style.drawControl(QStyle.CE_ItemViewItem, styled, painter, styled.widget)
        rect = style.subElementRect(QStyle.SE_ItemViewItemText, styled, styled.widget)
        metrics = painter.fontMetrics()
        baseline = rect.top() + (rect.height() + metrics.ascent() - metrics.descent()) // 2
        normal_colour = (styled.palette.highlightedText().color()
                         if styled.state & QStyle.State_Selected else styled.palette.text().color())
        painter.save()
        painter.setClipRect(rect)
        x = rect.left()
        for part, kind in parts:
            width = metrics.horizontalAdvance(part)
            if kind == 'direct':
                painter.fillRect(x - 2, baseline - metrics.ascent() - 2,
                                 width + 4, metrics.height() + 3, QColor('#d78061'))
                painter.setPen(QColor('#151515'))
            elif kind == 'embedded':
                painter.fillRect(x - 2, baseline - metrics.ascent() - 2,
                                 width + 4, metrics.height() + 3, QColor('#493128'))
                painter.setPen(QColor('#f4ded5'))
                painter.drawLine(x, baseline + 2, x + width, baseline + 2)
            else:
                painter.setPen(normal_colour)
            painter.drawText(x, baseline, part)
            x += width
        painter.restore()


class SearchResultDelegate(QStyledItemDelegate):
    """Compact three-line search cards with deliberately quiet hit statistics."""
    def sizeHint(self, option, index):
        return QSize(option.rect.width(), 67)

    def paint(self, painter, option, index):
        data = index.data(Qt.UserRole + 1) or {}
        styled = QStyleOptionViewItem(option)
        self.initStyleOption(styled, index)
        styled.text = ''
        style = styled.widget.style() if styled.widget else QApplication.style()
        style.drawControl(QStyle.CE_ItemViewItem, styled, painter, styled.widget)
        rect = option.rect.adjusted(11, 6, -8, -5)
        selected = bool(option.state & QStyle.State_Selected)
        painter.save()
        painter.setClipRect(rect)
        painter.setPen(QColor('#fff5ee') if selected else QColor('#e8e3da'))
        painter.setFont(QFont('Segoe UI', 10, QFont.DemiBold))
        painter.drawText(rect.left(), rect.top() + 14, data.get('title', ''))
        painter.setPen(QColor('#c6beb4') if selected else QColor('#99958e'))
        painter.setFont(QFont('Segoe UI', 8))
        painter.drawText(rect.left(), rect.top() + 31, data.get('meta', ''))
        hits = data.get('hits', '')
        origins = data.get('origins', ())
        paint_origin_icons(painter, origins, rect.left() + len(origins) * 24, rect.top() + 33, selected)
        if hits:
            painter.setPen(QColor('#f0ad91') if selected else QColor('#b58c7b'))
            painter.drawText(rect.left() + len(origins) * 24 + 4, rect.top() + 48, hits)
        painter.restore()


class PreviewStillLabel(QLabel):
    def setPixmap(self, pixmap):
        self.original_frame = pixmap
        self._fit_frame()

    def _fit_frame(self):
        pixmap = getattr(self, 'original_frame', QPixmap())
        super().setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                          if not pixmap.isNull() else pixmap)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_frame()


class MarkedSlider(QSlider):
    """A clean slider with a few deliberately marked recommendation stops."""
    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.recommended = []
        self.setMinimumHeight(25)

    def set_recommended(self, values):
        self.recommended = list(values)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.isEnabled():
            self.setSliderDown(True)
            self._jump_to(event)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.isSliderDown():
            self._jump_to(event)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.isSliderDown():
            self._jump_to(event)
            self.setSliderDown(False)
            event.accept()
        else:
            super().mouseReleaseEvent(event)

    def _jump_to(self, event):
        ratio = max(0.0, min(1.0, (event.position().x() - 8) / max(1, self.width() - 16)))
        value = round(self.minimum() + ratio * (self.maximum() - self.minimum()))
        self.setValue(value)
        self.sliderMoved.emit(value)

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


def reveal_path(path):
    """Open the system file browser with the exact file or folder selected."""
    target = Path(path)
    if not target.exists():
        QMessageBox.warning(None, 'File unavailable', f'This file or folder has moved or was removed:\n{path}')
        return
    try:
        if sys.platform == 'win32':
            # Explorer requires the switch and path in the same argument,
            # especially when the filename contains spaces.
            subprocess.Popen(['explorer.exe', '/select,' + os.path.normpath(str(target))])
        elif sys.platform == 'darwin':
            subprocess.Popen(['open', '-R', str(target)])
        else:
            open_path(target if target.is_dir() else target.parent)
    except OSError:
        open_path(target if target.is_dir() else target.parent)


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

        self.capture_mode_box = QWidget()
        self.capture_mode_box.setObjectName('transparentRow')
        capture_mode_row = QHBoxLayout(self.capture_mode_box)
        capture_mode_row.setContentsMargins(0, 0, 0, 0)
        capture_mode_row.setSpacing(0)
        self.fixed_mode = button('Fixed interval')
        self.scene_mode = button('Scene changes')
        self.fixed_mode.setObjectName('formatLeft')
        self.scene_mode.setObjectName('formatRight')
        for control in (self.fixed_mode, self.scene_mode):
            control.setCheckable(True)
        self.capture_mode_group = QButtonGroup(self)
        self.capture_mode_group.setExclusive(True)
        self.capture_mode_group.addButton(self.fixed_mode)
        self.capture_mode_group.addButton(self.scene_mode)
        (self.scene_mode if options['mode'] == 'scene' else self.fixed_mode).setChecked(True)
        self.fixed_mode.setToolTip('Save a frame at the exact interval below.')
        self.scene_mode.setToolTip('Save frames at strong visual cuts instead of a fixed interval.')
        capture_mode_row.addWidget(self.fixed_mode)
        capture_mode_row.addWidget(self.scene_mode)
        self.capture_mode_title = label('Capture mode')
        main_form.addRow(self.capture_mode_title, self.capture_mode_box)

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
        self.visual_interval.setRange(1, 30)
        self.visual_interval.set_recommended((1, 5, 10, 30))
        self.visual_interval.setValue(max(1, min(30, round(options.get('visual_interval', 30)))))
        self.visual_interval_label = label('')
        self.visual_interval_label.setMinimumWidth(150)
        self.visual_interval.setToolTip('Choose 1–30 seconds. Shorter distances catch brief objects but take longer and create more index thumbnails.')
        self.visual_interval_box.setToolTip('AI does not inspect every video frame. This controls the distance between inspected frames.')
        visual_row.addWidget(self.visual_interval, 1)
        visual_row.addWidget(self.visual_interval_label)
        main_form.addRow(self.visual_interval_title, self.visual_interval_box)

        self.visual_reprocess_note = label(
            'Applies to future processing. Enable Redo existing results to update indexed footage.', 'subtle')
        self.visual_reprocess_note.setWordWrap(True)
        main_form.addRow('', self.visual_reprocess_note)

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
        for widget in (self.fixed_mode, self.scene_mode, self.jpeg, self.png,
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
        seconds = self.visual_interval.value()
        speed = 'Detailed' if seconds <= 5 else ('Balanced' if seconds <= 15 else 'Faster')
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
                'visual_index': self.visual_index.isChecked(), 'visual_interval': self.interval.value(),
                'skip_existing': not self.redo.isChecked(), 'output': self.output.text()}

    def update_estimate(self):
        o = self.values()
        enabled = (o['screenshots'] or o['visual_index']) and o['mode'] == 'interval'
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
        self.capture_mode_title.setEnabled(o['screenshots'] or o['visual_index'])
        self.capture_mode_box.setEnabled(o['screenshots'] or o['visual_index'])
        for widget in (self.fixed_mode, self.scene_mode, self.width, self.jpeg, self.png):
            widget.setEnabled(o['screenshots'])
        self.fixed_mode.setEnabled(o['screenshots'] or o['visual_index'])
        self.scene_mode.setEnabled(o['screenshots'] or o['visual_index'])
        self.quality.setEnabled(o['screenshots'] and o['image_format'] == 'jpeg')
        self.quality_label.setEnabled(o['screenshots'])
        self.width_label.setEnabled(o['screenshots'])
        self.visual_interval_title.setVisible(False)
        self.visual_interval_box.setVisible(False)
        self.visual_interval_title.setEnabled(o['visual_index'])
        self.visual_interval_box.setEnabled(o['visual_index'])
        self.visual_reprocess_note.setEnabled(o['visual_index'])
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
        ai = f"  ·  {e.get('visual_frames', 0):,} AI samples" if o['visual_index'] else ''
        self.estimate_label.setText(
            f"{e['videos']} videos  ·  {e['count']:,} screenshots{ai}  ·  Time ≈ {duration_text(runtime)}  ·  Size ≈ {size_text(e['bytes'])}")

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
        layout.addWidget(label('FOOTAGE SEARCH', 'eyebrow'))
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
        rl.addWidget(label('MATCHES · GROUPED MOMENTS', 'eyebrow'))
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
        from vision_index import frame_match
        score, _ = frame_match(frame, query, layer)
        return bool(score)

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
            from vision_index import group_moments
            all_frames = record['visual_index']['frames']
            interval = float(record['visual_index'].get('interval', 30))
            moments = group_moments(all_frames, query, interval, layer) if query else [
                {'start': float(frame.get('time', 0)), 'end': float(frame.get('time', 0)),
                 'frame': frame, 'frames': [frame], 'score': 0.0,
                 'labels': sorted({d.get('label', '') for d in frame.get('detections', []) if d.get('label')})}
                for frame in all_frames]
            name_hit = query and all(word in (record['source'] + ' ' + record.get('project_name', '')).casefold()
                                     for word in self._words(query))
            if not moments and not name_hit:
                continue
            if name_hit and not moments:
                moments = [{'start': float(frame.get('time', 0)), 'end': float(frame.get('time', 0)),
                            'frame': frame, 'frames': [frame], 'score': 0.0, 'labels': []}
                           for frame in all_frames]
            self.matches[record['id']] = moments
            project = f" · {record['project_name']}" if record.get('project_name') else ''
            keywords = ', '.join(record['visual_index'].get('search_words', [])[:8]) or 'no objects found'
            item = QListWidgetItem(f"{Path(record['source']).name}\n{len(moments)} matching moments{project}\n{keywords}")
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
        for moment in self.matches.get(self.record['id'], []):
            frame = moment['frame']
            keywords = frame.get('keywords', {})
            brief = ', '.join(dict.fromkeys(value for values in keywords.values() for value in values))[:42]
            start, end = moment['start'], moment['end']
            time_text = duration_text(start) if abs(end - start) < .05 else f'{duration_text(start)}–{duration_text(end)}'
            item = QListWidgetItem(QIcon(str(Path(self.record['output']) / frame['file'])),
                                   f"{time_text}\n{brief or 'no common objects'}")
            item.setData(Qt.UserRole, moment)
            detections = sorted(frame.get('detections', []), key=lambda value: value.get('confidence', 0), reverse=True)
            details = ' · '.join(f"{d.get('label')} {round(float(d.get('confidence', 0)) * 100)}%"
                                 for d in detections[:6])
            item.setToolTip((details + '\n' if details else '') +
                            f"{len(moment['frames'])} adjacent sample{'s' if len(moment['frames']) != 1 else ''} · double-click for detail")
            self.coarse.addItem(item)
        if self.coarse.count():
            self.coarse.setCurrentRow(0)
            self.seek_frame(self.coarse.item(0))

    def load_detail(self, item):
        if not self.record or self.loading_detail:
            return
        moment = item.data(Qt.UserRole)
        frame = moment.get('frame', moment)
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
        value = item.data(Qt.UserRole)
        frame = value.get('frame', value)
        ResultsPage.seek_to(self, round(frame['time'] * 1000))

    def apply_pending_seek(self, status):
        ResultsPage.apply_pending_seek(self, status)

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
        host_layout = QVBoxLayout(self.library_host)
        host_layout.setContentsMargins(0, 0, 0, 0)
        self.workspace_split = QSplitter(Qt.Horizontal)
        self.workspace_split.setHandleWidth(7)
        self.workspace_split.setChildrenCollapsible(True)
        self.search_panel = QFrame()
        self.search_panel.setObjectName('card')
        self.search_panel.setMinimumWidth(245)
        self.search_panel.setMaximumWidth(365)
        ll = QVBoxLayout(self.search_panel)
        ll.setContentsMargins(14, 14, 14, 14)
        search_heading = QHBoxLayout()
        self.search_heading_label = label('FIND A VIDEO', 'eyebrow')
        search_heading.addWidget(self.search_heading_label)
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
        self.list.setItemDelegate(SearchResultDelegate(self.list))
        self.list.currentItemChanged.connect(self.select)
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
        self.open_original = button('Show in Explorer', self.open_source_file)
        self.open_original.setToolTip('Open the original file location and select this video')
        toolbar.addWidget(self.open_original)
        self.preview_toggle = button('Preview', self.toggle_source_preview)
        self.preview_toggle.setToolTip('Show or hide the source preview to give the transcript more room')
        toolbar.addWidget(self.preview_toggle)
        self.open_results = button('Open results folder', self.open_result)
        self.open_results.setObjectName('libraryPrimary')
        toolbar.addWidget(self.open_results)
        rl.addLayout(toolbar)

        self.media_split = QSplitter(Qt.Horizontal)
        self.media_split.setHandleWidth(7)
        self.media_split.setChildrenCollapsible(True)
        transcript_panel = QFrame()
        transcript_panel.setObjectName('card')
        transcript_layout = QVBoxLayout(transcript_panel)
        transcript_layout.setContentsMargins(14, 12, 14, 12)
        transcript_heading = QHBoxLayout()
        transcript_heading.addWidget(label('TRANSCRIPT', 'eyebrow'))
        transcript_heading.addStretch()
        self.transcript_hit = label('—', 'subtle')
        transcript_heading.addWidget(self.transcript_hit)
        hit_previous = button('', lambda: self.page_transcript_hit(-1))
        hit_previous.setObjectName('mediaIcon')
        hit_previous.setIcon(tile_icon('arrow_left'))
        hit_previous.setFixedSize(28, 25)
        hit_previous.setToolTip('Previous transcript hit')
        transcript_heading.addWidget(hit_previous)
        hit_next = button('', lambda: self.page_transcript_hit(1))
        hit_next.setObjectName('mediaIcon')
        hit_next.setIcon(tile_icon('arrow_right'))
        hit_next.setFixedSize(28, 25)
        hit_next.setToolTip('Next transcript hit')
        transcript_heading.addWidget(hit_next)
        transcript_layout.addLayout(transcript_heading)
        self.transcript_search = QLineEdit()
        self.transcript_search.setPlaceholderText('Filter transcript · select a line to jump to that moment')
        self.transcript_search.textChanged.connect(self.fill_transcript)
        transcript_layout.addWidget(self.transcript_search)
        self.transcript = QListWidget()
        self.transcript.setMinimumHeight(170)
        self.transcript.setItemDelegate(
            SearchHighlightDelegate(lambda: self.transcript_search.text(), self.transcript))
        self.transcript.itemClicked.connect(self.seek_segment)
        transcript_layout.addWidget(self.transcript, 1)
        exports = QHBoxLayout()
        exports.addWidget(label('Open:', 'subtle'))
        for fmt in ('txt', 'srt', 'vtt', 'json'):
            exports.addWidget(button(fmt.upper(), lambda checked=False, f=fmt: self.open_export(f)))
        exports.addStretch()
        transcript_layout.addLayout(exports)
        self.media_split.addWidget(transcript_panel)

        self.video_panel = QFrame()
        self.video_panel.setObjectName('card')
        self.video_panel.setMinimumWidth(190)
        video_layout = QVBoxLayout(self.video_panel)
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
        self.media_split.addWidget(self.video_panel)
        self.media_split.setStretchFactor(0, 3)
        self.media_split.setStretchFactor(1, 1)
        self.media_split.setSizes([720, 250])
        rl.addWidget(self.media_split, 2)

        screenshots_heading = QHBoxLayout()
        screenshots_heading.addWidget(label('SCREENSHOTS', 'eyebrow'))
        self.page_label = label('', 'subtle')
        screenshots_heading.addWidget(self.page_label)
        screenshots_heading.addStretch()
        self.previous_frames = button('', lambda: self.page_frames(-1))
        self.previous_frames.setObjectName('mediaIcon')
        self.previous_frames.setIcon(tile_icon('arrow_left'))
        self.previous_frames.setIconSize(QSize(22, 18))
        self.previous_frames.setFixedSize(36, 34)
        self.previous_frames.setAccessibleName('Previous screenshots')
        self.previous_frames.setToolTip('Previous screenshots')
        screenshots_heading.addWidget(self.previous_frames)
        self.next_frames = button('', lambda: self.page_frames(1))
        self.next_frames.setObjectName('mediaIcon')
        self.next_frames.setIcon(tile_icon('arrow_right'))
        self.next_frames.setIconSize(QSize(22, 18))
        self.next_frames.setFixedSize(36, 34)
        self.next_frames.setAccessibleName('Next screenshots')
        self.next_frames.setToolTip('Next screenshots')
        screenshots_heading.addWidget(self.next_frames)
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
        self.workspace_split.addWidget(self.search_panel)
        self.workspace_split.addWidget(right)
        self.workspace_split.setStretchFactor(0, 0)
        self.workspace_split.setStretchFactor(1, 1)
        self.workspace_split.setSizes([285, 900])
        host_layout.addWidget(self.workspace_split)
        for watched in [right] + right.findChildren(QWidget):
            watched.installEventFilter(self)
        layout.addWidget(self.library_host, 1)
        self._library_right = right
        self._library_toolbar = toolbar
        self._screenshots_heading = screenshots_heading
        self.search_target = 285
        self.last_search_width = 285
        self.browse_videos.setEnabled(True)


    def install_modular_workspace(self, window):
        layout = self.layout()
        layout.setContentsMargins(8, 4, 8, 8)
        self.page_title.setStyleSheet('font-size: 16px; font-weight: 600;')
        layout.itemAt(1).widget().hide()
        self.desk = workspace.Workspace(window, 'library')
        self.search_panel.setMaximumWidth(16777215)
        transcript_panel = self.transcript.parentWidget()
        self.video.setMaximumHeight(16777215)
        self.frames.setMinimumHeight(100)
        self.frames.setIconSize(QSize(138, 78))
        self.frames.setGridSize(QSize(155, 112))
        frames_panel = QWidget()
        fl = QVBoxLayout(frames_panel)
        fl.setContentsMargins(6, 6, 6, 6)
        self._library_right.layout().removeItem(self._screenshots_heading)
        fl.addLayout(self._screenshots_heading)
        fl.addWidget(self.frames, 1)
        self.desk.add_panel('transcript', 'Transcript', transcript_panel)
        self.desk.add_panel('search', 'Search Results', self.search_panel)
        self.desk.add_panel('preview', 'Source Preview', self.video_panel)
        self.desk.add_panel('frames', 'Visual References', frames_panel)
        self.desk.configure('transcript', {
            'Research desk': [(['transcript'], 660), (['search'], 310), (['preview', 'frames'], 340)],
            'Results on the left': [(['search'], 310), (['transcript'], 660), (['preview', 'frames'], 340)],
            'Preview on the left': [(['preview', 'frames'], 340), (['transcript'], 660), (['search'], 310)],
        })
        self.workspace_bar = workspace.WorkspaceBar(self.desk, 'Video Library')
        layout.insertWidget(0, self.workspace_bar)
        self._library_right.layout().removeItem(self._library_toolbar)
        layout.addLayout(self._library_toolbar)
        self.library_host.hide()
        layout.removeWidget(self.library_host)
        layout.addWidget(self.desk, 1)
        self.find_shortcut = QShortcut(QKeySequence.Find, self)
        self.find_shortcut.setContext(Qt.WidgetWithChildrenShortcut)
        self.find_shortcut.activated.connect(self.search.setFocus)

    def set_records(self, records):
        self.records = records
        self.populate()

    def search_scope_changed(self):
        self.layer.setEnabled(self.visual_scope.isChecked())
        self.populate()

    def eventFilter(self, watched, event):
        if (event.type() == QEvent.MouseButtonPress and self.search_panel.isVisible()
                and watched is not self.search_panel and not self.search_panel.isAncestorOf(watched)):
            self.collapse_search()
        return super().eventFilter(watched, event)

    def matching_visual_frames(self, record, query=None):
        query = (self.search.text() if query is None else query).casefold().strip()
        if not query or not self.visual_scope.isChecked():
            return []
        selected_layer = self.layer.currentData()
        from vision_index import frame_match
        return [frame for frame in record.get('visual_index', {}).get('frames', [])
                if frame_match(frame, query, selected_layer)[0]]

    def populate(self):
        old = self.record.get('id') if self.record else None
        self.list.blockSignals(True)
        self.list.clear()
        query = self.search.text().casefold().strip()
        self.visual_matches = {}
        selected = None
        shown = 0
        for record in reversed(self.records):
            transcript_values = ([s['text'] for s in record.get('segments', [])]
                                 if self.audio_scope.isChecked() else [])
            visual_matches = self.matching_visual_frames(record, query)
            if visual_matches:
                self.visual_matches[record['id']] = visual_matches
            origins = list(search_origins(record, query))
            if not self.audio_scope.isChecked() and 'transcript' in origins:
                origins.remove('transcript')
            if not self.visual_scope.isChecked() and 'visual' in origins:
                origins.remove('visual')
            elif self.visual_scope.isChecked() and 'visual' in origins and not visual_matches:
                origins.remove('visual')
            if self.visual_scope.isChecked() and visual_matches and 'visual' not in origins:
                origins.append('visual')
            direct, embedded = query_hit_counts(transcript_values, query)
            if query and not origins:
                continue
            project = (' · ' + record['project_name']) if record.get('project_name') else ''
            item = QListWidgetItem()
            item.setData(Qt.UserRole, record)
            item.setData(Qt.UserRole + 1, {
                'title': Path(record['source']).name,
                'meta': f"{duration_text(record['duration'])}{project}",
                'hits': (f'{direct} direct · {embedded} indirect' if 'transcript' in origins
                         else f'{len(visual_matches)} visual matches' if visual_matches else 'File name match') if query else '',
                'origins': tuple(origins),
            })
            if origins:
                item.setToolTip('Matched by ' + ', '.join(origin.replace('filename', 'file name') for origin in origins))
            self.list.addItem(item)
            shown += 1
            if record['id'] == old:
                selected = item
        self.search_heading_label.setText(f"SEARCH RESULTS · {shown}" if query else f"VIDEO LIBRARY · {shown}")
        self.list.blockSignals(False)
        if selected:
            self.list.setCurrentItem(selected)
        if self.record:
            self.frame_offset = 0
            self.fill_frames()

    def collapse_search(self):
        if hasattr(self, 'desk'):
            self.desk.hide_panel('search')
            return
        if not self.search_panel.isVisible():
            return
        sizes = self.workspace_split.sizes()
        if sizes and sizes[0] > 0:
            self.last_search_width = sizes[0]
        self.search_target = 0
        self.search_panel.hide()
        self.workspace_split.setSizes([0, max(1, sum(sizes))])
        self.browse_videos.setEnabled(True)

    def open_search(self):
        if hasattr(self, 'desk'):
            self.desk.show_panel('search')
            return
        if self.search_panel.isVisible() and self.search_target:
            return
        self.search_panel.show()
        self.search_target = max(245, min(365, self.last_search_width))
        total = max(700, sum(self.workspace_split.sizes()))
        self.workspace_split.setSizes([self.search_target, total - self.search_target])
        self.browse_videos.setEnabled(False)

    def select(self, item, previous=None):
        if not item:
            return
        self.record = item.data(Qt.UserRole)
        self.page_title.setText(Path(self.record['source']).name)
        self.pending_seek = None
        self.player.stop()
        source_url = QUrl.fromLocalFile(self.record['source'])
        if self.player.source() != source_url:
            self.player.setSource(source_url)
        self.frame_offset = 0
        query = self.search.text().strip()
        transcript_text = ' '.join(segment['text'] for segment in self.record.get('segments', []))
        self.transcript_search.setText(query if self.audio_scope.isChecked() and query.casefold() in transcript_text.casefold() else '')
        self.fill_frames()
        self.fill_transcript()
        matches = self.visual_matches.get(self.record['id'], [])
        if matches and not self.transcript_search.text():
            self.frames.setCurrentRow(0)
            self.seek_frame(self.frames.item(0))
        elif self.transcript.count() and self.transcript_search.text():
            self.transcript.setCurrentRow(0)
            self.seek_segment(self.transcript.item(0))

    def toggle_source_preview(self):
        if hasattr(self, 'desk'):
            dock = self.desk.panels['preview']
            self.desk.show_panel('preview') if dock.isHidden() else self.desk.hide_panel('preview')
            return
        visible = self.video_panel.isVisible()
        self.video_panel.setVisible(not visible)
        self.preview_toggle.setText('Preview' if visible else 'Hide preview')
        if not visible:
            self.media_split.setSizes([720, 250])

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
        self.transcript_hit.setText(f'1 / {self.transcript.count()}' if query and self.transcript.count() else '—')

    def page_transcript_hit(self, direction):
        count = self.transcript.count()
        if not count:
            return
        row = self.transcript.currentRow()
        row = (row + direction) % count if row >= 0 else (0 if direction > 0 else count - 1)
        self.transcript.setCurrentRow(row)
        self.transcript.scrollToItem(self.transcript.item(row))
        self.seek_segment(self.transcript.item(row))
        if self.transcript_search.text():
            self.transcript_hit.setText(f'{row + 1} / {count}')

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.width() < 900 and self.search_panel.isVisible() and self.video_panel.isVisible():
            self.video_panel.hide()
            self.preview_toggle.setText('Preview')

    def seek_frame(self, item):
        if item and item.data(Qt.UserRole):
            self.seek_to(round(item.data(Qt.UserRole)['time'] * 1000))

    def seek_to(self, milliseconds):
        self.pending_seek = milliseconds
        self.position(milliseconds)
        if not getattr(self, '_seek_connected', False):
            self.player.mediaStatusChanged.connect(self.apply_pending_seek)
            self._seek_connected = True
        self.player.setPosition(milliseconds)
        self.apply_pending_seek(self.player.mediaStatus())

    def apply_pending_seek(self, status):
        if status in (QMediaPlayer.LoadedMedia, QMediaPlayer.BufferedMedia) and getattr(self, 'pending_seek', None) is not None:
            milliseconds, self.pending_seek = self.pending_seek, None
            self.player.setPosition(milliseconds)
            self.position(milliseconds)

    def seek_segment(self, item):
        segment = item.data(Qt.UserRole)
        if segment:
            self.seek_to(round(segment['start'] * 1000))
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

    def open_source_file(self):
        if self.record:
            reveal_path(self.record['source'])

    def open_export(self, fmt):
        if self.record:
            open_path(Path(self.record['output']) / ('transcript.' + fmt))


class LibraryPickerDialog(QDialog):
    """Searchable multi-select view of footage already processed into the library."""
    def __init__(self, records, parent=None):
        super().__init__(parent)
        self.records = list(records)
        self.checked_ids = set()
        self.setWindowTitle('Choose from Video Library')
        self.resize(1040, 690)
        layout = QVBoxLayout(self)
        heading = QHBoxLayout()
        words = QVBoxLayout()
        words.addWidget(label('VIDEO LIBRARY', 'eyebrow'))
        words.addWidget(label('Add library footage', 'title'))
        words.addWidget(label('Search transcript text, filenames, and indexed visual terms. Select as many videos as you need.', 'subtle'))
        heading.addLayout(words)
        heading.addStretch()
        layout.addLayout(heading)
        self.search = QLineEdit()
        self.search.setPlaceholderText('Search footage or transcript…')
        self.search.textChanged.connect(self.refresh)
        layout.addWidget(self.search)
        split = QSplitter(Qt.Horizontal)
        self.list = QTreeWidget()
        self.list.setHeaderLabels(['Video', 'Duration', 'Hits'])
        self.list.setIconSize(QSize(54, 18))
        self.list.setColumnWidth(0, 245)
        self.list.setColumnWidth(1, 78)
        self.list.itemChanged.connect(self.update_count)
        self.list.currentItemChanged.connect(self.preview)
        split.addWidget(self.list)
        preview = QSplitter(Qt.Vertical)
        self.transcript = QTextBrowser()
        self.transcript.setPlaceholderText('Choose a video to preview its transcript.')
        preview.addWidget(self.transcript)
        self.frames = QListWidget()
        self.frames.setViewMode(QListWidget.IconMode)
        self.frames.setIconSize(QSize(180, 102))
        self.frames.setResizeMode(QListWidget.Adjust)
        self.frames.setSpacing(7)
        preview.addWidget(self.frames)
        preview.setSizes([330, 220])
        split.addWidget(preview)
        split.setSizes([360, 650])
        layout.addWidget(split, 1)
        actions = QHBoxLayout()
        actions.addStretch()
        cancel = button('Cancel', self.reject)
        actions.addWidget(cancel)
        self.add_button = button('Add selected', self.accept, True)
        self.add_button.setEnabled(False)
        actions.addWidget(self.add_button)
        layout.addLayout(actions)
        self.refresh()

    def refresh(self):
        query = self.search.text().strip()
        self.remember_checks()
        self.list.blockSignals(True)
        self.list.clear()
        for record in self.records:
            origins = search_origins(record, query)
            if query and not origins:
                continue
            direct, embedded = query_hit_counts(
                [segment.get('text', '') for segment in record.get('segments', [])],
                query) if query else (0, 0)
            hits = f'{direct} direct · {embedded} embedded' if query else ''
            item = QTreeWidgetItem([Path(record.get('source', '')).name,
                                    duration_text(record.get('duration', 0)), hits])
            if origins:
                item.setIcon(0, search_origin_icon(origins))
                item.setToolTip(0, 'Matched by ' + ', '.join(
                    origin.replace('filename', 'file name') for origin in origins))
            item.setData(0, Qt.UserRole, record)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(0, Qt.Checked if record.get('id') in self.checked_ids else Qt.Unchecked)
            self.list.addTopLevelItem(item)
        self.list.blockSignals(False)
        if self.list.topLevelItemCount():
            self.list.setCurrentItem(self.list.topLevelItem(0))
        else:
            self.preview(None)
            self.transcript.setPlainText('No matching footage. Try another search; your selections are retained.')
        self.update_count()

    def remember_checks(self):
        for index in range(self.list.topLevelItemCount()):
            item = self.list.topLevelItem(index)
            key = item.data(0, Qt.UserRole).get('id')
            if item.checkState(0) == Qt.Checked:
                self.checked_ids.add(key)
            else:
                self.checked_ids.discard(key)

    def update_count(self, *args):
        self.remember_checks()
        count = len(self.selected_records())
        self.add_button.setEnabled(count > 0)
        self.add_button.setText(f'Add {count} selected' if count else 'Add selected')

    def selected_records(self):
        return [record for record in self.records if record.get('id') in self.checked_ids]

    def preview(self, item, previous=None):
        self.frames.clear()
        if not item:
            self.transcript.clear()
            return
        record = item.data(0, Qt.UserRole)
        query = self.search.text().strip()
        blocks = []
        for segment in record.get('segments', []):
            value = html.escape(segment.get('text', ''))
            if query:
                value = re.sub(f'({re.escape(query)})', r'<mark>\1</mark>', value, flags=re.IGNORECASE)
            blocks.append(f"<p><small>{duration_text(segment.get('start', 0))}</small>&nbsp;&nbsp;{value}</p>")
        self.transcript.setHtml(''.join(blocks) or '<p>No transcript available.</p>')
        for frame in record.get('frames', [])[:24]:
            path = frame.get('path') or frame.get('file')
            if not path or not Path(path).is_file():
                continue
            frame_item = QListWidgetItem(QIcon(path), duration_text(frame.get('time', 0)))
            frame_item.setData(Qt.UserRole, frame)
            self.frames.addItem(frame_item)


class InkCanvas(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.strokes = []
        self.tool = None
        self.current = None
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setStyleSheet('background: transparent;')

    def set_document(self, document):
        self.strokes = document.setdefault('strokes', []) if document else []
        self.current = None
        self.update()

    def set_tool(self, tool):
        self.tool = tool
        self.setAttribute(Qt.WA_TransparentForMouseEvents, tool is None)
        self.setCursor(Qt.CrossCursor if tool else Qt.ArrowCursor)
        self.raise_()

    def mousePressEvent(self, event):
        if self.tool and event.button() == Qt.LeftButton:
            self.current = {'tool': self.tool, 'points': [[event.position().x(), event.position().y()]]}
            self.strokes.append(self.current)
            event.accept()

    def mouseMoveEvent(self, event):
        if self.current and event.buttons() & Qt.LeftButton:
            self.current['points'].append([event.position().x(), event.position().y()])
            self.update()

    def mouseReleaseEvent(self, event):
        if self.current:
            self.current = None
            self.changed.emit()
            event.accept()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        for stroke in self.strokes:
            points = stroke.get('points', [])
            if len(points) < 2:
                continue
            if stroke.get('tool') == 'marker':
                colour, width = QColor(255, 210, 55, 92), 17
            else:
                colour, width = QColor('#d64b32'), 2.4
            painter.setPen(QPen(colour, width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            for first, second in zip(points, points[1:]):
                painter.drawLine(QPoint(round(first[0]), round(first[1])), QPoint(round(second[0]), round(second[1])))


class PaperSegmentRow(QFrame):
    changed = Signal()
    seekRequested = Signal(float)

    def __init__(self, segment, parent=None):
        super().__init__(parent)
        self.segment = segment
        self.setObjectName('paperSegment')
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Maximum)
        self.setProperty('highlighted', bool(segment.get('highlighted')))
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)
        self.included = QCheckBox()
        self.included.setChecked(segment.get('included', True))
        self.included.setToolTip('Include this passage in the paper sequence and export')
        layout.addWidget(self.included, 0, Qt.AlignTop)
        meta = QVBoxLayout()
        timestamp = QPushButton(duration_text(segment.get('start', 0)))
        timestamp.setFlat(True)
        timestamp.setToolTip('Play from this passage')
        timestamp.clicked.connect(lambda: self.seekRequested.emit(float(segment.get('start', 0))))
        meta.addWidget(timestamp)
        self.speaker = QLineEdit(segment.get('speaker', ''))
        self.speaker.setPlaceholderText('SPEAKER')
        timestamp.setFixedWidth(88)
        timestamp.setObjectName('timecodeLink')
        self.speaker.setMaximumWidth(88)
        self.speaker.setStyleSheet("font-family: 'Cascadia Mono', Consolas; font-weight: 700; text-transform: uppercase;")
        meta.addWidget(self.speaker)
        meta.addStretch()
        layout.addLayout(meta)
        body = QVBoxLayout()
        self.text = QTextEdit()
        self.text.setAcceptRichText(False)
        self.text.setPlainText(segment.get('text', ''))
        self.text.setMinimumHeight(42)
        self.text.document().contentsChanged.connect(self.fit_text)
        body.addWidget(self.text)
        self.note = QLineEdit(segment.get('note', ''))
        self.note.setPlaceholderText('Write a margin note…')
        self.note.setStyleSheet("color: #e47b61; border: 0; font-family: 'Segoe Print'; font-size: 13px;")
        body.addWidget(self.note)
        layout.addLayout(body, 1)
        self.highlight = QToolButton()
        self.highlight.setIcon(paper_icon('marker', '#a36b00'))
        self.highlight.setIconSize(QSize(16, 16))
        self.highlight.setCheckable(True)
        self.highlight.setChecked(segment.get('highlighted', False))
        self.highlight.setToolTip('Mark as a key line')
        layout.addWidget(self.highlight, 0, Qt.AlignTop)
        self.included.toggled.connect(self.sync)
        self.speaker.textChanged.connect(self.sync)
        self.text.textChanged.connect(self.sync)
        self.note.textChanged.connect(self.sync)
        self.highlight.toggled.connect(self.sync)
        QTimer.singleShot(0, self.fit_text)

    def fit_text(self):
        self.text.document().setTextWidth(max(100, self.text.viewport().width()))
        height = math.ceil(self.text.document().size().height()) + 14
        self.text.setFixedHeight(max(42, min(300, height)))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_text()

    def sync(self, *args):
        self.segment.update(included=self.included.isChecked(), speaker=self.speaker.text().strip(),
                            text=self.text.toPlainText(), note=self.note.text(),
                            highlighted=self.highlight.isChecked())
        self.setProperty('highlighted', self.highlight.isChecked())
        self.style().unpolish(self)
        self.style().polish(self)
        self.changed.emit()


class PaperDocument(QWidget):
    changed = Signal()
    seekRequested = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('paperSheet')
        self.document = None
        self.rows = []
        self.layout_box = QVBoxLayout(self)
        self.layout_box.setContentsMargins(10, 10, 10, 24)
        self.layout_box.setSpacing(0)
        self.ink = InkCanvas(self)
        self.ink.changed.connect(self.changed)

    def set_document(self, document):
        self.document = document
        while self.layout_box.count():
            item = self.layout_box.takeAt(0)
            widget = item.widget()
            if widget:
                # Remove refreshed rows from the scene immediately. deleteLater
                # alone leaves the old editors visible until Qt drains deferred
                # events, which can produce doubled text and controls.
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
        self.rows = []
        if document:
            for segment in document.get('segments', []):
                row = PaperSegmentRow(segment)
                row.changed.connect(self.changed)
                row.seekRequested.connect(self.seekRequested)
                self.rows.append(row)
                self.layout_box.addWidget(row)
        else:
            self.layout_box.addStretch()
            empty_title = label('Start with a transcript', 'paperEmptyTitle')
            empty_title.setAlignment(Qt.AlignCenter)
            self.layout_box.addWidget(empty_title)
            empty_copy = label(
                'Open the Video Library and add one or more processed interviews.', 'paperSubtle')
            empty_copy.setAlignment(Qt.AlignCenter)
            empty_copy.setWordWrap(True)
            self.layout_box.addWidget(empty_copy)
        self.layout_box.addStretch()
        self.setMinimumHeight(320 if not self.rows else 0)
        self.ink.set_document(document)
        QTimer.singleShot(0, self._fit_ink)

    def _fit_ink(self):
        self.ink.setGeometry(self.rect())
        self.ink.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_ink()

    def apply_search(self, query):
        query = query.strip().casefold()
        for row in self.rows:
            match = bool(query and query in row.segment.get('text', '').casefold())
            selections = []
            if match:
                text = row.text.toPlainText().casefold()
                offset = 0
                while query and (offset := text.find(query, offset)) >= 0:
                    selection = QTextEdit.ExtraSelection()
                    cursor = row.text.textCursor()
                    cursor.setPosition(offset)
                    cursor.setPosition(offset + len(query), QTextCursor.KeepAnchor)
                    selection.cursor = cursor
                    selection.format.setBackground(QColor('#81532c'))
                    selection.format.setForeground(QColor('#fff1db'))
                    selections.append(selection)
                    offset += len(query)
            row.text.setExtraSelections(selections)



class PaperSearchDelegate(QStyledItemDelegate):
    def __init__(self, query, parent=None):
        super().__init__(parent)
        self.query = query

    def sizeHint(self, option, index):
        return QSize(180, 124)

    def paint(self, painter, option, index):
        painter.save()
        rect = option.rect.adjusted(3, 3, -3, -3)
        selected = bool(option.state & QStyle.State_Selected)
        painter.fillRect(rect, QColor('#383028' if selected else '#1b2227'))
        if selected:
            painter.setPen(QColor('#e79455'))
            painter.drawRect(rect.adjusted(0, 0, -1, -1))
        lines = index.data(Qt.DisplayRole).split('\n')
        title, excerpt, hits = lines[0], lines[1], lines[-1]
        thumbnail = index.data(Qt.DecorationRole)
        text_left = rect.left() + 8
        if thumbnail and not thumbnail.isNull() and rect.width() >= 290:
            thumbnail.paint(painter, rect.left() + 8, rect.top() + 10, 78, 44)
            text_left += 86
        width = max(100, rect.right() - text_left - 8)
        painter.setPen(QColor('#e5ebef'))
        painter.drawText(text_left, rect.top() + 19, option.fontMetrics.elidedText(title, Qt.ElideMiddle, width))
        paint_origin_icons(painter, index.data(Qt.UserRole + 1) or ('transcript',),
                           rect.right() - 5, rect.top() + 7, selected)
        escaped = ''.join(('<span style="background:#805029;color:#fff1d9;">' + html.escape(part) + '</span>')
                          if matched else html.escape(part) for part, matched in highlighted_parts(excerpt, self.query()))
        doc = QTextDocument()
        doc.setDefaultFont(option.font)
        doc.setHtml('<div style="color:#bdc8d0;">' + escaped + '</div>')
        doc.setTextWidth(width)
        painter.translate(text_left, rect.top() + 26)
        painter.setClipRect(0, 0, width, 59)
        doc.drawContents(painter)
        painter.restore()
        painter.save()
        painter.setPen(QColor('#d6a37f'))
        painter.drawText(rect.left() + 8, rect.bottom() - 10, hits)
        painter.restore()


class PaperEditPage(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.document = None
        self.record = None
        self.exporting = False
        self.setObjectName('paperPage')
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 8)
        layout.setSpacing(6)
        self.desk = workspace.Workspace(window, 'paper')
        self.documents = QListWidget()
        self.documents.currentItemChanged.connect(self.select_document)
        sources = QWidget()
        sources_layout = QVBoxLayout(sources)
        sources_layout.setContentsMargins(8, 8, 8, 8)
        sources_layout.addWidget(self.documents, 1)
        sources_layout.addWidget(button('+ Add from Library', self.add_from_library))
        self.desk.add_panel('sources', 'Transcripts', sources)

        centre = QWidget()
        cl = QVBoxLayout(centre)
        cl.setContentsMargins(8, 8, 8, 8)
        cl.setSpacing(6)
        tools = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText('Find words across your footage…')
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.search_changed)
        tools.addWidget(self.search, 1)
        self.pen = QToolButton()
        self.pen.setIcon(paper_icon('pen', '#ed884d'))
        self.pen.setIconSize(QSize(18, 18))
        self.pen.setCheckable(True)
        self.pen.setToolTip('Pen · draw handwritten annotations')
        self.pen.setAccessibleName('Pen')
        self.pen.toggled.connect(lambda value: self.select_ink('pen', value))
        tools.addWidget(self.pen)
        self.marker = QToolButton()
        self.marker.setIcon(paper_icon('marker', '#e2b455'))
        self.marker.setIconSize(QSize(18, 18))
        self.marker.setCheckable(True)
        self.marker.setToolTip('Marker · highlight freely on the page')
        self.marker.setAccessibleName('Marker')
        self.marker.toggled.connect(lambda value: self.select_ink('marker', value))
        tools.addWidget(self.marker)
        undo_ink = QToolButton()
        undo_ink.setIcon(paper_icon('undo'))
        undo_ink.setToolTip('Undo last pen or marker stroke')
        undo_ink.clicked.connect(self.undo_ink)
        tools.addWidget(undo_ink)
        clear_ink = QToolButton()
        clear_ink.setIcon(paper_icon('clear'))
        clear_ink.setToolTip('Clear handwritten annotations')
        clear_ink.clicked.connect(self.clear_ink)
        tools.addWidget(clear_ink)
        cl.addLayout(tools)
        self.paper_scroll = QScrollArea()
        self.paper_scroll.setWidgetResizable(True)
        self.paper = PaperDocument()
        self.paper.changed.connect(self.document_changed)
        self.paper.seekRequested.connect(self.seek_source)
        self.paper_scroll.setWidget(self.paper)
        cl.addWidget(self.paper_scroll, 1)
        self.analysis = label('Choose footage from the Library', 'paperSubtle')
        cl.addWidget(self.analysis)
        self.desk.add_panel('script', 'Transcript Paper', centre)

        find_panel = QWidget()
        fl = QVBoxLayout(find_panel)
        fl.setContentsMargins(8, 8, 8, 8)
        self.search_count = label('Search your processed footage', 'subtle')
        fl.addWidget(self.search_count)
        self.search_results = QListWidget()
        self.search_results.setWordWrap(True)
        self.search_results.setItemDelegate(PaperSearchDelegate(lambda: self.search.text(), self.search_results))
        self.search_results.setIconSize(QSize(88, 50))
        self.search_results.currentItemChanged.connect(self.open_search_result)
        fl.addWidget(self.search_results, 1)
        self.desk.add_panel('search', 'Search Results', find_panel)

        preview = QWidget()
        sl = QVBoxLayout(preview)
        sl.setContentsMargins(8, 8, 8, 8)
        self.source_name = label('Select a transcript', 'paperSubtle')
        self.source_name.setWordWrap(True)
        sl.addWidget(self.source_name)
        self.video = QVideoWidget()
        self.video.setMinimumSize(160, 120)
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video)
        sl.addWidget(self.video, 1)
        controls = QHBoxLayout()
        self.play_button = QToolButton()
        self.play_button.setIcon(tile_icon('play', '#e8e3da'))
        self.play_button.setToolTip('Play / pause source')
        self.play_button.setAccessibleName('Play / pause source')
        self.play_button.clicked.connect(self.play_source)
        controls.addWidget(self.play_button)
        self.seek = MarkedSlider(Qt.Horizontal)
        self.seek.setToolTip('Scrub source video')
        self.seek.sliderMoved.connect(self.player.setPosition)
        self.player.durationChanged.connect(lambda value: self.seek.setRange(0, value))
        self.player.positionChanged.connect(self.source_position)
        self.player.playbackStateChanged.connect(lambda value: self.play_button.setIcon(
            tile_icon('pause' if value == QMediaPlayer.PlayingState else 'play')))
        controls.addWidget(self.seek, 1)
        self.clock = label('00:00:00', 'paperSubtle')
        controls.addWidget(self.clock)
        sl.addLayout(controls)
        self.source_status = label('', 'subtle')
        self.source_status.setWordWrap(True)
        sl.addWidget(self.source_status)
        self.player.errorOccurred.connect(lambda error, text: self.source_status.setText('Preview unavailable · ' + text))
        self.desk.add_panel('preview', 'Source Preview', preview)
        self.frames = QListWidget()
        self.frames.setViewMode(QListWidget.IconMode)
        self.frames.setIconSize(QSize(138, 78))
        self.frames.setGridSize(QSize(154, 112))
        self.frames.setResizeMode(QListWidget.Adjust)
        self.frames.setSpacing(4)
        self.frames.itemClicked.connect(lambda item: self.seek_source(item.data(Qt.UserRole) or 0))
        self.desk.add_panel('frames', 'Visual References', self.frames)

        # A vertical passage-order panel, never a full-width editing timeline.
        self.sequence = QListWidget()
        self.sequence.setWordWrap(True)
        self.sequence.setDragDropMode(QAbstractItemView.InternalMove)
        self.sequence.model().rowsMoved.connect(self.sequence_reordered)
        order = QWidget()
        ol = QVBoxLayout(order)
        ol.setContentsMargins(8, 8, 8, 8)
        ol.addWidget(label('Drag passages to change script order', 'subtle'))
        ol.addWidget(self.sequence, 1)
        reorder = QHBoxLayout()
        reorder.addWidget(button('Move up', lambda: self.move_passage(-1)))
        reorder.addWidget(button('Move down', lambda: self.move_passage(1)))
        ol.addLayout(reorder)
        self.desk.add_panel('order', 'Passage Order', order)
        self.desk.configure('script', {
            'Writing desk': [(['sources'], 185), (['script'], 720), (['preview', 'frames'], 330)],
            'Search beside script': [(['script'], 620), (['search'], 320), (['preview', 'frames'], 340)],
            'Preview on the left': [(['preview', 'frames'], 340), (['script'], 720), (['sources'], 185)],
            'Arrange passages': [(['script'], 740), (['order'], 290), (['preview', 'frames'], 330)],
        })
        self.workspace_bar = workspace.WorkspaceBar(self.desk, 'Paper Edit', (
            ('Write', lambda: self.set_mode('Write')),
            ('Find', lambda: self.set_mode('Find')),
            ('Build', self.open_storyline),
        ))
        layout.addWidget(self.workspace_bar)
        actions = QHBoxLayout()
        self.document_title = label('Paper Edit', 'workspaceTitle')
        actions.addWidget(self.document_title, 1)
        library_button = button('Add footage', self.add_from_library)
        library_button.setIcon(paper_icon('library'))
        actions.addWidget(library_button)
        order_button = button('Passage order', lambda: self.desk.apply_preset('Arrange passages'))
        order_button.setToolTip('Reorder selected transcript passages')
        actions.addWidget(order_button)
        self.export_button = button('Export script', self.export_script)
        self.export_button.setIcon(paper_icon('export'))
        self.export_button.setObjectName('paperPrimary')
        actions.addWidget(self.export_button)
        layout.addLayout(actions)
        layout.addWidget(self.desk, 1)
        self.find_shortcut = QShortcut(QKeySequence.Find, self)
        self.find_shortcut.setContext(Qt.WidgetWithChildrenShortcut)
        self.find_shortcut.activated.connect(lambda: self.set_mode('Find'))
        self.refresh()

    def set_mode(self, name):
        self.workspace_bar.select_mode(name)
        self.desk.apply_preset('Search beside script' if name == 'Find' else 'Writing desk')
        if name == 'Find':
            self.search.setFocus()

    def open_storyline(self):
        self.desk.remember()
        if hasattr(self.window, 'navigate'):
            self.window.navigate(3)

    def source_position(self, value):
        if not self.seek.isSliderDown():
            self.seek.setValue(value)
        self.clock.setText(duration_text(value / 1000))

    def move_passage(self, direction):
        row = self.sequence.currentRow()
        target = row + direction
        if row < 0 or not 0 <= target < self.sequence.count():
            return
        item = self.sequence.takeItem(row)
        self.sequence.insertItem(target, item)
        self.sequence.setCurrentRow(target)
        self.sequence_reordered()

    def search_changed(self, query):
        self.paper.apply_search(query)
        self.search_results.blockSignals(True)
        self.search_results.clear()
        query = query.strip()
        if query:
            if self.desk.panels['search'].isHidden():
                self.desk.apply_preset('Search beside script')
            self.workspace_bar.select_mode('Find')
            # Include authored wording when an existing paper document is present.
            for record in self.window.state.get('results', []):
                authored = next((d for d in self.window.state.get('paper_edits', [])
                                 if d.get('result_id') == record.get('id')), None)
                segments = (authored or record).get('segments', [])
                texts = [s.get('text', '') for s in segments]
                direct, indirect = query_hit_counts(texts, query)
                if not direct and not indirect:
                    continue
                first = next((s for s in segments if query.casefold() in s.get('text', '').casefold()), {})
                title = Path(record.get('source', '')).name
                item = QListWidgetItem(title + '\n' + first.get('text', '')[:145] +
                                       f'\n{direct} direct · {indirect} indirect')
                item.setData(Qt.UserRole, (record, float(first.get('start', 0))))
                item.setData(Qt.UserRole + 1, ('transcript',))
                item.setToolTip(first.get('text', ''))
                frames = record.get('frames', [])
                if frames:
                    path = self.frame_path(frames[0], record)
                    if path.is_file():
                        item.setIcon(QIcon(str(path)))
                self.search_results.addItem(item)
        count = self.search_results.count()
        self.search_count.setText(f'{count} matching videos' if count else
                                 'No matches · try another word' if query else 'Search your processed footage')
        self.search_results.blockSignals(False)

    def open_search_result(self, item, previous=None):
        if not item:
            return
        record, seconds = item.data(Qt.UserRole)
        document = paper_edit.ensure_paper_document(self.window.state, record)
        self.refresh(document['id'])
        self.paper.apply_search(self.search.text())
        matching = next((row for row in self.paper.rows if abs(row.segment.get('start', 0) - seconds) < .01), None)
        if matching:
            self.paper_scroll.ensureWidgetVisible(matching)
        self.player.setPosition(round(seconds * 1000))
        self.window.save_timer.start(150)

    @staticmethod
    def frame_path(frame, record):
        value = Path(frame.get('path') or frame.get('file') or '')
        return value if value.is_absolute() else Path(record.get('output', '')) / value

    def refresh(self, select_id=None):
        current = select_id or (self.document.get('id') if self.document else None)
        self.documents.blockSignals(True)
        self.documents.clear()
        for document in self.window.state.setdefault('paper_edits', []):
            item = QListWidgetItem(document.get('title', 'Untitled transcript'))
            item.setData(Qt.UserRole, document['id'])
            self.documents.addItem(item)
            if document['id'] == current:
                self.documents.setCurrentItem(item)
        self.documents.blockSignals(False)
        if self.documents.currentItem() is not None:
            self.select_document(self.documents.currentItem())
        elif self.documents.count():
            self.documents.setCurrentRow(0)
        elif not self.documents.count():
            self.document = None
            self.record = None
            self.player.stop()
            self.player.setSource(QUrl())
            self.paper.set_document(None)
            self.sequence.clear()
            self.frames.clear()
            self.source_name.setText('Select a transcript')
            self.document_title.setText('Paper Edit')
            self.source_status.setText('')
            self.analysis.setText('Choose footage from the Library')
            self.export_button.setEnabled(False)
            self.pen.setEnabled(False)
            self.marker.setEnabled(False)

    def add_from_library(self):
        picker = LibraryPickerDialog(self.window.state.get('results', []), self)
        if picker.exec() != QDialog.Accepted:
            return
        documents = [paper_edit.ensure_paper_document(self.window.state, record)
                     for record in picker.selected_records()]
        self.window.save_timer.start(100)
        self.refresh(documents[0]['id'] if documents else None)

    def select_document(self, item, previous=None):
        if not item:
            return
        document_id = item.data(Qt.UserRole)
        self.document = next((value for value in self.window.state.get('paper_edits', [])
                              if value['id'] == document_id), None)
        self.record = next((value for value in self.window.state.get('results', [])
                            if self.document and (value.get('id') == self.document.get('result_id') or
                            str(value.get('source', '')).casefold() == str(self.document.get('source', '')).casefold())), None)
        self.paper.set_document(self.document)
        self.paper.apply_search(self.search.text())
        self.document_title.setText(self.document.get('title', 'Paper Edit') if self.document else 'Paper Edit')
        self.export_button.setEnabled(bool(self.document))
        self.pen.setEnabled(bool(self.document))
        self.marker.setEnabled(bool(self.document))
        self.source_name.setText(Path(self.document.get('source', '')).name if self.document else 'Select a transcript')
        self.player.stop()
        self.player.setSource(QUrl())
        online = self.document and Path(self.document.get('source', '')).is_file()
        self.source_status.setText('' if online else 'Source offline · transcript remains editable')
        if online:
            self.player.setSource(QUrl.fromLocalFile(self.document['source']))
        self.populate_frames()
        self.update_analysis()
        self.update_sequence()

    def populate_frames(self):
        self.frames.clear()
        if not self.record:
            return
        for frame in self.record.get('frames', [])[:30]:
            path = self.frame_path(frame, self.record)
            if path.is_file():
                item = QListWidgetItem(QIcon(str(path)), duration_text(frame.get('time', 0)))
                item.setData(Qt.UserRole, frame.get('time', 0))
                self.frames.addItem(item)

    def document_changed(self):
        self.paper.apply_search(self.search.text())
        self.update_analysis()
        self.update_sequence()
        self.window.save_timer.start(250)

    def update_analysis(self):
        if not self.document:
            self.analysis.setText('Choose footage from the Library')
            return
        value = paper_edit.transcript_analysis(self.document)
        terms = ', '.join(term for term, count in value['repeated_terms'][:3])
        self.analysis.setText(f"{value['words']} words · {len(paper_edit.ordered_segments(self.document, True))} selected")
        self.analysis.setToolTip('Repeated terms: ' + (terms or 'None'))
        self.export_button.setEnabled(not self.exporting and bool(
            paper_edit.ordered_segments(self.document, True)))

    def update_sequence(self):
        self.sequence.blockSignals(True)
        self.sequence.clear()
        if self.document:
            for segment in paper_edit.ordered_segments(self.document, included_only=True):
                text = segment.get('text', '').strip().replace('\n', ' ')
                item = QListWidgetItem(text[:72] + ('…' if len(text) > 72 else ''))
                item.setData(Qt.UserRole, segment['id'])
                item.setToolTip(text)
                self.sequence.addItem(item)
        self.sequence.blockSignals(False)

    def sequence_reordered(self, *args):
        if not self.document:
            return
        included = [self.sequence.item(index).data(Qt.UserRole) for index in range(self.sequence.count())]
        excluded = [value['id'] for value in self.document.get('segments', []) if value['id'] not in included]
        self.document['order'] = included + excluded
        self.window.save_timer.start(150)

    def seek_source(self, seconds):
        self.player.setPosition(round(float(seconds) * 1000))
        self.player.play()

    def play_source(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        elif self.document:
            self.player.play()

    def select_ink(self, tool, enabled):
        other = self.marker if tool == 'pen' else self.pen
        if enabled:
            other.blockSignals(True)
            other.setChecked(False)
            other.blockSignals(False)
            self.paper.ink.set_tool(tool)
        elif not other.isChecked():
            self.paper.ink.set_tool(None)

    def undo_ink(self):
        if self.document and self.document.get('strokes'):
            self.document['strokes'].pop()
            self.paper.ink.update()
            self.window.save_timer.start(100)

    def clear_ink(self):
        if not self.document or not self.document.get('strokes'):
            return
        if QMessageBox.question(self, 'Clear annotations?', 'Remove every pen and marker stroke from this paper edit?') == QMessageBox.Yes:
            self.document['strokes'].clear()
            self.paper.ink.update()
            self.window.save_timer.start(100)

    def export_script(self):
        if self.exporting:
            return
        if not self.document or not paper_edit.ordered_segments(self.document, True):
            QMessageBox.information(self, 'Nothing selected', 'Include at least one transcript passage before exporting.')
            return
        if not Path(self.document.get('source', '')).is_file():
            QMessageBox.warning(self, 'Source offline', 'Relink the source video before exporting trimmed media.')
            return
        parent = QFileDialog.getExistingDirectory(self, 'Choose a folder for the Paper Edit package')
        if not parent:
            return
        self.analysis.setText('Exporting trimmed passages…')
        snapshot = copy.deepcopy(self.document)
        self.exporting = True
        self.export_button.setEnabled(False)
        task = self.window.run_task(
            lambda notify: paper_edit.export_paper_package(snapshot, parent, trim=True),
            self.export_finished)
        task.finished.connect(self.export_settled)

    def export_settled(self):
        self.exporting = False
        self.update_analysis()

    def export_finished(self, target):
        self.update_analysis()
        open_path(target)
        QMessageBox.information(self, 'Paper Edit exported', 'Created the edited script, trimmed media, manifest, and Premiere XML.')


class LegacyProjectsPage(QWidget):
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

    def populate_sequences(self, select_id=None):
        project = self.current()
        self.sequence_tabs.blockSignals(True)
        while self.sequence_tabs.count():
            self.sequence_tabs.removeTab(0)
        if project:
            timeline.ensure_project_editing(project)
            for sequence in project['sequences']:
                index = self.sequence_tabs.addTab(sequence['name'])
                self.sequence_tabs.setTabData(index, sequence['id'])
            if select_id:
                for index in range(self.sequence_tabs.count()):
                    if self.sequence_tabs.tabData(index) == select_id:
                        self.sequence_tabs.setCurrentIndex(index)
                        break
        self.sequence_tabs.blockSignals(False)
        self.sequence_changed(self.sequence_tabs.currentIndex())

    def sequence_changed(self, index):
        if hasattr(self, 'active_sequence_id'):
            self.store_sequence_view(self.active_sequence_id)
        sequence = self.active_sequence()
        self.timeline_canvas.set_media_records(self.window.state.get('results', []))
        self.timeline_canvas.set_sequence(sequence)
        if sequence:
            self.active_sequence_id = sequence['id']
            view = sequence.setdefault('view', {'playhead': 0.0, 'zoom': 10.0, 'scroll': 0})
            self.restoring_sequence_view = True
            self.timeline_canvas.set_zoom(float(view.get('zoom', 10)))
            self.timeline_canvas.set_playhead(float(view.get('playhead', 0)))
            self.sync_timeline_zoom(self.timeline_canvas.pixels_per_second)
            QTimer.singleShot(0, lambda value=int(view.get('scroll', 0)): self.restore_timeline_scroll(value))
            self.seek_sequence_preview(self.timeline_canvas.playhead)
        elif hasattr(self, 'active_sequence_id'):
            self.active_sequence_id = None
        self.update_summary()

    def sequence_by_id(self, sequence_id):
        if not sequence_id:
            return None
        return next((sequence for project in self.window.state.get('projects', [])
                     for sequence in project.get('sequences', []) if sequence.get('id') == sequence_id), None)

    def store_sequence_view(self, sequence_id=None, *args):
        if getattr(self, 'restoring_sequence_view', False):
            return
        sequence = self.sequence_by_id(sequence_id or getattr(self, 'active_sequence_id', None))
        if not sequence or not hasattr(self, 'timeline_scroll'):
            return
        sequence['view'] = {
            'playhead': round(float(self.timeline_canvas.playhead), 4),
            'zoom': round(float(self.timeline_canvas.pixels_per_second), 3),
            'scroll': int(self.timeline_scroll.horizontalScrollBar().value()),
        }
        self.window.save_timer.start(250)

    def restore_timeline_scroll(self, value):
        self.timeline_scroll.horizontalScrollBar().setValue(value)
        self.restoring_sequence_view = False

    def sequence_moved(self, old, new):
        project = self.current()
        if not project or old == new:
            return
        sequence = project['sequences'].pop(old)
        project['sequences'].insert(new, sequence)
        self.window.save_timer.start(250)

    def new_sequence(self):
        project = self.current()
        if not project:
            return
        existing = {sequence['name'].casefold() for sequence in project['sequences']}
        number = 1
        while f'sequence {number}'.casefold() in existing:
            number += 1
        sequence = timeline.new_sequence(f'Sequence {number}')
        project['sequences'].append(sequence)
        self.populate_sequences(sequence['id'])
        self.window.save_timer.start(200)

    def sequence_settings(self):
        sequence = self.active_sequence()
        if not sequence:
            return
        fps, ok = QInputDialog.getDouble(self, 'Sequence settings', 'Frame rate',
                                         float(sequence.get('frame_rate', 25)), 1, 120, 3)
        if not ok:
            return
        sizes = ('3840 × 2160', '1920 × 1080', '1280 × 720', '1080 × 1920')
        current = f"{sequence.get('width', 1920)} × {sequence.get('height', 1080)}"
        size, ok = QInputDialog.getItem(self, 'Sequence settings', 'Frame size', sizes,
                                        sizes.index(current) if current in sizes else 1, False)
        if not ok:
            return
        self.push_undo()
        width, height = (int(value.strip()) for value in size.split('×'))
        sequence.update(frame_rate=fps, width=width, height=height)
        self.status.setText(f'Sequence · {width}×{height} · {fps:g} fps')
        self.finish_sequence_edit()

    def rename_sequence(self, index=None):
        if index is not None and index >= 0:
            self.sequence_tabs.setCurrentIndex(index)
        sequence = self.active_sequence()
        if not sequence:
            return
        name, ok = QInputDialog.getText(self, 'Rename sequence', 'Sequence name', text=sequence['name'])
        if ok and name.strip():
            sequence['name'] = name.strip()
            self.sequence_tabs.setTabText(self.sequence_tabs.currentIndex(), sequence['name'])
            self.populate_export_queue()
            self.window.save_timer.start(200)

    def duplicate_sequence(self):
        project, sequence = self.current(), self.active_sequence()
        if not project or not sequence:
            return
        duplicate = copy.deepcopy(sequence)
        duplicate['id'] = uuid.uuid4().hex
        duplicate['name'] = sequence['name'] + ' copy'
        for track in duplicate.get('tracks', []):
            track['id'] = uuid.uuid4().hex
            for clip in track.get('clips', []):
                clip['id'] = uuid.uuid4().hex
        project['sequences'].append(duplicate)
        self.populate_sequences(duplicate['id'])
        self.window.save_timer.start(200)

    def close_sequence(self, index):
        project = self.current()
        if not project or len(project['sequences']) <= 1:
            self.status.setText('Every project keeps at least one sequence. Create another before closing this one.')
            return
        sequence = project['sequences'][index]
        if timeline.sequence_duration(sequence) and QMessageBox.question(
                self, 'Close sequence?', f"Close “{sequence['name']}” and remove its timeline edits?") != QMessageBox.Yes:
            return
        project['sequences'].pop(index)
        project['export_queue'] = [queued for queued in project.get('export_queue', [])
                                   if queued.get('sequence_id') != sequence['id']]
        self.populate_sequences()
        self.populate_export_queue()
        self.window.save_timer.start(200)

    def push_undo(self, snapshot=None):
        sequence = self.active_sequence()
        if not sequence:
            return
        stack = self.undo_stacks.setdefault(sequence['id'], [])
        stack.append(copy.deepcopy(snapshot or sequence))
        del stack[:-40]
        self.redo_stacks.setdefault(sequence['id'], []).clear()

    def replace_active_sequence(self, replacement):
        project, sequence = self.current(), self.active_sequence()
        if not project or not sequence:
            return
        for index, value in enumerate(project['sequences']):
            if value['id'] == sequence['id']:
                replacement['id'] = sequence['id']
                project['sequences'][index] = replacement
                break
        self.timeline_canvas.set_sequence(replacement)
        self.update_summary()
        self.window.save_timer.start(200)

    def sequence_command(self, command):
        sequence = self.active_sequence()
        if not sequence:
            return
        if command == 'play_pause':
            self.toggle_sequence_playback()
            return
        track_index, clip = self.timeline_canvas.selected_clip()
        selected_track = max(0, min(len(sequence['tracks']) - 1,
                                    self.timeline_canvas.selected_track_index))
        if command in ('toggle_track', 'lock_track', 'solo_track'):
            track = sequence['tracks'][selected_track]
            self.push_undo()
            if command == 'lock_track':
                track['locked'] = not track.get('locked', False)
            elif command == 'solo_track' and track.get('type') == 'audio':
                track['solo'] = not track.get('solo', False)
            elif track.get('type') == 'audio':
                track['muted'] = not track.get('muted', False)
            else:
                track['visible'] = not track.get('visible', True)
            self.finish_sequence_edit()
            return
        if command == 'marker':
            self.push_undo()
            markers = sequence.setdefault('markers', [])
            markers.append({'id': uuid.uuid4().hex, 'time': round(self.timeline_canvas.playhead, 4),
                            'name': f'Marker {len(markers) + 1}'})
            self.finish_sequence_edit()
            return
        if command == 'undo':
            stack = self.undo_stacks.setdefault(sequence['id'], [])
            if stack:
                self.redo_stacks.setdefault(sequence['id'], []).append(copy.deepcopy(sequence))
                self.replace_active_sequence(stack.pop())
            return
        if command == 'redo':
            stack = self.redo_stacks.setdefault(sequence['id'], [])
            if stack:
                self.undo_stacks.setdefault(sequence['id'], []).append(copy.deepcopy(sequence))
                self.replace_active_sequence(stack.pop())
            return
        if command == 'copy':
            self.clipboard = copy.deepcopy(clip) if clip else None
            return
        if command in ('cut', 'delete', 'duplicate', 'split') and clip and timeline.clip_group_locked(sequence, clip):
            self.status.setText('Unlock the linked clip tracks before changing this edit.')
            return
        if command in ('cut', 'delete') and clip:
            if command == 'cut':
                self.clipboard = copy.deepcopy(clip)
            self.push_undo()
            linked = clip.get('linked')
            for track in sequence['tracks']:
                track['clips'] = [value for value in track['clips']
                                  if value['id'] != clip['id'] and not (linked and value.get('linked') == linked)]
            self.timeline_canvas.selected_id = None
            self.finish_sequence_edit()
            return
        if command in ('paste', 'duplicate'):
            source = clip if command == 'duplicate' else self.clipboard
            if not source:
                return
            target = track_index if track_index is not None else next(
                (i for i, track in enumerate(sequence['tracks']) if track.get('type') == 'video'), 0)
            if sequence['tracks'][target].get('locked'):
                self.status.setText('Unlock the target track before pasting or duplicating a clip.')
                return
            self.push_undo()
            pasted = copy.deepcopy(source)
            pasted['id'] = uuid.uuid4().hex
            pasted['linked'] = None
            length = float(pasted['end']) - float(pasted['start'])
            pasted['start'] = float(clip['end']) if command == 'duplicate' and clip else self.timeline_canvas.playhead
            pasted['end'] = pasted['start'] + length
            sequence['tracks'][target]['clips'].append(pasted)
            self.timeline_canvas.selected_id = pasted['id']
            self.finish_sequence_edit()
            return
        if command == 'split' and clip:
            point = self.timeline_canvas.playhead
            if not float(clip['start']) < point < float(clip['end']):
                point = (float(clip['start']) + float(clip['end'])) / 2
            self.push_undo()
            linked = clip.get('linked')
            for track in sequence['tracks']:
                for value in list(track['clips']):
                    if value['id'] != clip['id'] and not (linked and value.get('linked') == linked):
                        continue
                    if not float(value['start']) < point < float(value['end']):
                        continue
                    right = copy.deepcopy(value)
                    right['id'] = uuid.uuid4().hex
                    offset = point - float(value['start'])
                    right['start'] = point
                    right['source_in'] = float(value.get('source_in', 0)) + offset
                    value['end'] = point
                    value['source_out'] = right['source_in']
                    track['clips'].append(right)
            self.finish_sequence_edit()

    def timeline_clip_selected(self, clip):
        self.pending_drag_snapshot = copy.deepcopy(self.active_sequence()) if clip and self.active_sequence() else None
        if clip:
            self.status.setText(f"Selected {clip.get('name', 'clip')} · double-click to split at the pointer")

    def timeline_drag_finished(self):
        if self.pending_drag_snapshot:
            self.push_undo(self.pending_drag_snapshot)
        self.pending_drag_snapshot = None
        self.finish_sequence_edit()

    def finish_sequence_edit(self):
        self.timeline_canvas._resize_canvas()
        self.timeline_canvas.update()
        self.update_summary()
        self.window.save_timer.start(200)

    def add_track(self, kind):
        sequence = self.active_sequence()
        if not sequence:
            return
        self.push_undo()
        count = sum(track.get('type') == kind for track in sequence['tracks']) + 1
        track = {'id': uuid.uuid4().hex, 'name': ('V' if kind == 'video' else 'A') + str(count),
                 'type': kind, 'locked': False, 'clips': []}
        track.update({'visible': True} if kind == 'video' else {'muted': False, 'solo': False})
        first_audio = next((i for i, value in enumerate(sequence['tracks'])
                            if value.get('type') == 'audio'), len(sequence['tracks']))
        sequence['tracks'].insert(first_audio if kind == 'video' else len(sequence['tracks']), track)
        self.finish_sequence_edit()

    def insert_selected_media(self):
        item = self.tree.currentItem()
        payload = item.data(0, Qt.UserRole + 1) if item else None
        if payload:
            self.add_media_to_timeline(payload)
        else:
            self.status.setText('Select a video in Project media first.')

    def add_media_to_timeline(self, video, start=None, track_index=None):
        sequence = self.active_sequence()
        if not sequence or not video:
            return
        tracks = sequence['tracks']
        if track_index is None or not 0 <= int(track_index) < len(tracks):
            track_index = next((i for i, track in enumerate(tracks)
                                if track.get('type') == 'video' and track.get('name') == 'V1'), 0)
        track_index = int(track_index)
        target = tracks[track_index]
        if target.get('type') != 'video':
            track_index = next((i for i, value in enumerate(tracks)
                                if value.get('type') == 'video'), 0)
            target = tracks[track_index]
        if target.get('locked'):
            self.status.setText('That track is locked.')
            return
        if start is None:
            start = max((float(clip.get('end', 0)) for clip in target.get('clips', [])), default=0.0)
        start = max(0.0, float(start))
        duration = max(0.01, float(video.get('duration', 0) or 0))

        def overlaps(track):
            end = start + duration
            return any(start < float(value.get('end', 0)) and
                       end > float(value.get('start', 0))
                       for value in track.get('clips', []))

        self.push_undo()
        # A drop on occupied picture creates a new layer above it. There is no
        # artificial V/A limit: each overlapping source can live on its own track.
        if overlaps(target):
            number = sum(value.get('type') == 'video' for value in tracks) + 1
            target = {'id': uuid.uuid4().hex, 'name': f'V{number}', 'type': 'video',
                      'locked': False, 'visible': True, 'clips': []}
            tracks.insert(0, target)
            track_index = 0
        linked = uuid.uuid4().hex if video.get('audio') and target.get('type') == 'video' else None
        clip = timeline.make_clip(video['path'], video.get('duration', 0), start,
                                  name=video.get('name'), linked=linked)
        target['clips'].append(clip)
        if linked:
            audio_index = next((i for i, value in enumerate(tracks)
                                if value.get('type') == 'audio' and
                                not value.get('locked') and not overlaps(value)), None)
            if audio_index is None:
                number = sum(value.get('type') == 'audio' for value in tracks) + 1
                tracks.append({'id': uuid.uuid4().hex, 'name': f'A{number}', 'type': 'audio',
                               'locked': False, 'muted': False, 'solo': False, 'clips': []})
                audio_index = len(tracks) - 1
            tracks[audio_index]['clips'].append(timeline.make_clip(
                video['path'], video.get('duration', 0), start,
                name=video.get('name'), linked=linked))
        self.timeline_canvas.selected_id = clip['id']
        self.inspect_source(video)
        self.finish_sequence_edit()

    def fit_timeline(self):
        self.timeline_canvas.fit(self.timeline_scroll.viewport().width())
        self.zoom.blockSignals(True)
        self.zoom.setValue(round(self.timeline_canvas.pixels_per_second))
        self.zoom.blockSignals(False)
        self.timeline_scroll.horizontalScrollBar().setValue(0)
        if hasattr(self, 'store_sequence_view'):
            self.store_sequence_view()

    def queue_sequence(self, sequence_id=None):
        project = self.current()
        if not project:
            return
        if isinstance(sequence_id, bool) or not sequence_id:
            sequence = self.active_sequence()
            sequence_id = sequence['id'] if sequence else None
        sequence = next((value for value in project['sequences'] if value['id'] == sequence_id), None)
        if not sequence:
            return
        if not any(item.get('sequence_id') == sequence_id for item in project['export_queue']):
            project['export_queue'].append({'id': uuid.uuid4().hex, 'sequence_id': sequence_id, 'status': 'Queued'})
        self.populate_export_queue(sequence_id)
        self.window.save_timer.start(200)

    def populate_export_queue(self, select_sequence_id=None):
        project = self.current()
        self.export_queue.clear()
        if not project:
            self.export_status.setText('Nothing queued.')
            return
        sequences = {sequence['id']: sequence for sequence in project.get('sequences', [])}
        for queued in project.get('export_queue', []):
            sequence = sequences.get(queued.get('sequence_id'))
            if not sequence:
                continue
            item = QListWidgetItem(f"{sequence['name']}\n{duration_text(timeline.sequence_duration(sequence))} · {queued.get('status', 'Queued')}")
            item.setData(Qt.UserRole, queued['id'])
            item.setData(Qt.UserRole + 1, sequence['id'])
            self.export_queue.addItem(item)
            if sequence['id'] == select_sequence_id:
                self.export_queue.setCurrentItem(item)
        count = self.export_queue.count()
        self.export_status.setText(f"{count} sequence{'s' if count != 1 else ''} queued.")

    def queued_sequence(self):
        project = self.current()
        item = self.export_queue.currentItem()
        active = self.active_sequence()
        sequence_id = item.data(Qt.UserRole + 1) if item else (active['id'] if active else None)
        return next((sequence for sequence in project.get('sequences', [])
                     if sequence['id'] == sequence_id), None) if project else None

    def export_sequence(self):
        project, sequence = self.current(), self.queued_sequence()
        if not project or not sequence:
            return
        if timeline.sequence_duration(sequence) <= 0:
            QMessageBox.information(self, 'Empty sequence', 'Add at least one clip before exporting this sequence.')
            return
        missing = timeline.offline_sources(sequence)
        if missing:
            QMessageBox.warning(self, 'Offline media',
                                'Relink offline media before exporting:\n\n' + '\n'.join(missing[:8]))
            return
        default = str(Path.home() / (sequence['name'] + '.xml'))
        path, _ = QFileDialog.getSaveFileName(
            self, 'Export Premiere-compatible timeline', default, 'XML timeline (*.xml)')
        if not path:
            return
        try:
            timeline.write_final_cut_xml(sequence, path)
            for queued in project['export_queue']:
                if queued.get('sequence_id') == sequence['id']:
                    queued['status'] = 'Exported'
            self.populate_export_queue(sequence['id'])
            self.export_status.setText('Exported timeline · ' + path)
            self.window.save()
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, 'Timeline export failed', str(exc))

    def collect_media(self):
        sequence = self.queued_sequence()
        if not sequence:
            return
        if timeline.sequence_duration(sequence) <= 0:
            QMessageBox.information(self, 'Empty sequence', 'Add at least one clip before collecting media.')
            return
        missing = timeline.offline_sources(sequence)
        parent = QFileDialog.getExistingDirectory(self, 'Choose a folder for collected sequence media')
        if not parent:
            return
        try:
            target = timeline.collect_sequence_media(sequence, parent)
            if missing:
                self.export_status.setText(
                    f'Collected available media · {len(missing)} offline source(s) listed in manifest · {target}')
            else:
                self.export_status.setText('Collected used media · ' + str(target))
            open_path(target)
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, 'Could not collect media', str(exc))

    def relink_offline_media(self):
        sequence = self.queued_sequence()
        if not sequence:
            return
        missing = timeline.offline_sources(sequence)
        if not missing:
            self.export_status.setText('Preflight passed · all sequence media is online.')
            return
        original = missing[0]
        replacement, _ = QFileDialog.getOpenFileName(
            self, 'Relink ' + Path(original).name, str(Path(original).parent),
            'Video files (*.mp4 *.mkv *.mov *.avi *.webm *.m4v *.mpeg *.mpg *.mts *.m2ts *.wmv *.flv)')
        if not replacement:
            return
        self.push_undo()
        for track in sequence.get('tracks', []):
            for clip in track.get('clips', []):
                if str(clip.get('source', '')).casefold() == original.casefold():
                    clip['source'] = replacement
                    clip['name'] = Path(replacement).name
        self.finish_sequence_edit()
        remaining = len(timeline.offline_sources(sequence))
        self.export_status.setText('Media relinked.' if not remaining else f'Media relinked · {remaining} offline source(s) remain.')

    def remove_export_item(self):
        project, item = self.current(), self.export_queue.currentItem()
        if not project or not item:
            return
        queued_id = item.data(Qt.UserRole)
        project['export_queue'] = [queued for queued in project['export_queue'] if queued['id'] != queued_id]
        self.populate_export_queue()
        self.window.save_timer.start(200)


class ProjectsPage(LegacyProjectsPage):
    """Simple stackable Storyline with Library media and a docked delivery queue."""
    def __init__(self, window):
        QWidget.__init__(self)
        self.window = window
        self.item_map = {}
        self.undo_stacks = {}
        self.redo_stacks = {}
        self.clipboard = None
        self.pending_drag_snapshot = None
        self.sequence_playing = False
        self.sequence_started = 0.0
        self.playing_clip_id = None
        self.active_sequence_id = None
        self.restoring_sequence_view = False
        self.pending_preview_position = None
        self.pending_scrub = None
        self.scrub_timer = QTimer(self)
        self.scrub_timer.setSingleShot(True)
        self.scrub_timer.setInterval(65)
        self.scrub_timer.timeout.connect(self.render_scrub_frame)
        self.sequence_timer = QTimer(self)
        self.sequence_timer.setInterval(50)
        self.sequence_timer.timeout.connect(self.sequence_tick)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(9)
        heading = QHBoxLayout()
        words = QVBoxLayout()
        self.story_eyebrow = label('STORY SEQUENCE', 'eyebrow')
        words.addWidget(self.story_eyebrow)
        self.page_title = label('Storyline', 'title')
        words.addWidget(self.page_title)
        self.page_subtitle = label('Stack footage, shape the cut, and send finished sequences to Delivery.', 'subtle')
        words.addWidget(self.page_subtitle)
        heading.addLayout(words)
        heading.addStretch()
        self.delivery_toggle = button('Delivery', self.set_delivery_open)
        self.delivery_toggle.setCheckable(True)
        self.delivery_toggle.setToolTip('Open the export queue and delivery tools')
        heading.addWidget(self.delivery_toggle)
        layout.addLayout(heading)
        self.project_workspace = QSplitter(Qt.Horizontal)
        self.project_workspace.setHandleWidth(7)
        self.project_workspace.setChildrenCollapsible(False)
        self.media_panel = self.build_media_panel()
        self.project_workspace.addWidget(self.media_panel)
        self.editor_stack = QStackedWidget()
        self.editor_stack.addWidget(self.build_empty_editor())
        self.editor_stack.addWidget(self.build_editing_panel())
        self.project_workspace.addWidget(self.editor_stack)
        self.export_panel = self.build_export_panel()
        self.project_workspace.addWidget(self.export_panel)
        self.project_workspace.setSizes([310, 875, 0])
        self.export_panel.hide()
        layout.addWidget(self.project_workspace, 1)
        self.refresh()
        self.install_modular_workspace()

    def install_modular_workspace(self):
        layout = self.layout()
        layout.setContentsMargins(8, 4, 8, 8)
        # The existing editor and empty state keep all their command wiring.
        editing = self.editor_stack.widget(1)
        editing.layout().removeWidget(self.sequence_preview)
        self.desk = workspace.Workspace(self.window, 'storyline-1.18')
        self.desk.add_panel('media', 'Sequence Media', self.media_panel)
        self.desk.add_panel('preview', 'Sequence Preview', self.sequence_preview)
        self.desk.add_panel('timeline', 'Story Timeline', self.editor_stack)
        self.desk.configure('timeline', {
            'Landscape': [(['preview', 'timeline'], 800), (['media'], 360)],
            'Portrait': [(['preview'], 300), (['media', 'timeline'], 1000)],
            'Timeline focus': [(['media'], 240), (['timeline'], 1050)],
        })
        self.workspace_bar = workspace.WorkspaceBar(self.desk, 'Storyline')
        self.landscape_button = workspace.tool('landscape', 'Landscape preview layout', lambda: self.set_story_orientation('Landscape'))
        self.portrait_button = workspace.tool('portrait', 'Portrait preview layout', lambda: self.set_story_orientation('Portrait'))
        self.workspace_bar.row.insertWidget(1, self.landscape_button)
        self.workspace_bar.row.insertWidget(2, self.portrait_button)
        self.workspace_bar.row.addWidget(button('+ Sequence', self.new_sequence))
        self.workspace_bar.row.addWidget(self.delivery_toggle)
        self.export_popup = QDialog(self, Qt.Popup)
        self.export_popup.setObjectName('exportPopup')
        self.export_popup.setMinimumSize(320, 400)
        popup_layout = QVBoxLayout(self.export_popup)
        popup_layout.addWidget(self.export_panel)
        self.export_panel.show()
        self.export_popup.finished.connect(lambda *_: self.delivery_toggle.setChecked(False))
        layout.insertWidget(0, self.workspace_bar)
        self.project_workspace.hide()
        layout.removeWidget(self.project_workspace)
        layout.addWidget(self.desk, 1)
        self.page_title.hide()
        self.story_eyebrow.hide()
        # The compact workspace bar owns all page actions.
        for index in range(layout.count()):
            item = layout.itemAt(index)
            if item.layout():
                for child_index in range(item.layout().count()):
                    child = item.layout().itemAt(child_index)
                    if child.widget():
                        child.widget().hide()
        self.page_subtitle.hide()
        self.delivery_toggle.show()
        self.page_subtitle.setText('Drag clips to stack · split at the playhead · send a sequence to Export Queue')
        self.delivery_toggle.setText('Export Queue')
        self.zoom.setFixedWidth(130)
        self.zoom.setAccessibleName('Timeline zoom')
        self.desk.resizeDocks([self.desk.panels['preview'], self.desk.panels['timeline']], [260, 510], Qt.Vertical)

    def set_story_orientation(self, name):
        self.desk.apply_preset(name)
        if name == 'Landscape':
            self.desk.resizeDocks([self.desk.panels['preview'], self.desk.panels['timeline']], [240, 520], Qt.Vertical)
        else:
            self.desk.resizeDocks([self.desk.panels['preview'], self.desk.panels['media']], [280, 950], Qt.Horizontal)
            self.desk.resizeDocks([self.desk.panels['media'], self.desk.panels['timeline']], [220, 540], Qt.Vertical)
        self.desk.remember()

    def build_empty_editor(self):
        card = QFrame()
        card.setObjectName('card')
        layout = QVBoxLayout(card)
        layout.setContentsMargins(48, 48, 48, 48)
        layout.addStretch()
        self.empty_title = label('Build your first sequence', 'title')
        self.empty_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.empty_title)
        self.empty_copy = label(
            'Search the Video Library, select one or more sources, and add them directly to this timeline.',
            'subtle')
        self.empty_copy.setAlignment(Qt.AlignCenter)
        self.empty_copy.setWordWrap(True)
        layout.addWidget(self.empty_copy)
        action_row = QHBoxLayout()
        action_row.addStretch()
        self.empty_action_button = button('+ Open Video Library', self.empty_project_action, True)
        action_row.addWidget(self.empty_action_button)
        action_row.addStretch()
        layout.addLayout(action_row)
        layout.addStretch()
        return card

    def empty_project_action(self):
        self.add_library_media()

    def set_delivery_open(self, opened):
        if hasattr(self, 'export_popup'):
            if opened:
                anchor = self.delivery_toggle.mapToGlobal(self.delivery_toggle.rect().bottomRight())
                self.export_popup.move(anchor.x() - self.export_popup.width(), anchor.y() + 4)
                self.export_popup.show()
            else:
                self.export_popup.hide()
            self.delivery_toggle.setChecked(bool(opened))
            return
        if hasattr(self, 'desk'):
            return
            self.delivery_toggle.setChecked(bool(opened))
            self.delivery_toggle.setText('Hide export queue' if opened else 'Export Queue')
            return
        project = self.current()
        has_media = bool(project and any(folder.get('files') for folder in project.get('folders', [])))
        opened = bool(opened and has_media)
        self.delivery_toggle.blockSignals(True)
        self.delivery_toggle.setChecked(opened)
        self.delivery_toggle.setText('Hide delivery' if opened else 'Delivery')
        self.delivery_toggle.blockSignals(False)
        self.export_panel.setVisible(opened)
        self.project_workspace.setSizes([280, 685, 235] if opened else [310, 890, 0])

    def build_media_panel(self):
        left = QFrame()
        left.setObjectName('card')
        ll = QVBoxLayout(left)
        ll.setContentsMargins(10, 10, 10, 10)
        ll.setSpacing(7)
        ll.addWidget(label('SEQUENCE MEDIA', 'eyebrow'))
        self.projects = QListWidget()
        self.projects.currentItemChanged.connect(self.project_changed)
        self.projects.hide()
        self.summary = label('Add media to begin.', 'subtle')
        self.summary.setWordWrap(True)
        ll.addWidget(self.summary)
        source_actions = QHBoxLayout()
        self.add_media_button = button('+ Add footage', self.add_library_media, True)
        self.add_media_button.setToolTip('Search the Video Library and add multiple videos')
        self.remove_source = button('−', self.window.remove_project_source)
        self.remove_source.setToolTip('Remove selected source from this project')
        source_actions.addWidget(self.add_media_button, 1)
        source_actions.addWidget(self.remove_source)
        ll.addLayout(source_actions)
        self.tree = timeline.ProjectMediaTree()
        self.tree.setHeaderLabels(['Project media', 'Duration', 'Status'])
        self.tree.setColumnWidth(0, 150)
        self.tree.setColumnWidth(1, 68)
        self.tree.header().setStretchLastSection(True)
        self.tree.itemChanged.connect(self.selection_changed)
        self.tree.currentItemChanged.connect(self.tree_item_changed)
        self.tree.setDragEnabled(True)
        self.tree.itemDoubleClicked.connect(
            lambda item, column: self.add_media_to_timeline(item.data(0, Qt.UserRole + 1)))
        ll.addWidget(self.tree, 1)
        self.media_hint = label('Drag a source to place it · double-click to append', 'subtle')
        self.media_hint.setWordWrap(True)
        ll.addWidget(self.media_hint)
        self.insert_media_button = button('Insert selected', self.insert_selected_media)
        ll.addWidget(self.insert_media_button)
        self.status = label('Choose footage from the Video Library.', 'subtle')
        self.status.setWordWrap(True)
        ll.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setFormat('%p% of project batch')
        ll.addWidget(self.progress)
        self.progress_detail = label('0 videos ready', 'subtle')
        ll.addWidget(self.progress_detail)
        self.processing_box = QWidget()
        processing = QHBoxLayout(self.processing_box)
        processing.setContentsMargins(0, 0, 0, 0)
        self.pause = button('Pause', self.window.pause_batch)
        self.cancel = button('Cancel', self.window.cancel_batch)
        self.process = button('Process', self.window.process_project, True)
        self.pause.setEnabled(False)
        self.cancel.setEnabled(False)
        processing.addWidget(self.pause)
        processing.addWidget(self.cancel)
        processing.addWidget(self.process)
        ll.addWidget(self.processing_box)
        self.progress.hide()
        self.progress_detail.hide()
        self.processing_box.hide()
        return left

    def build_editing_panel(self):
        center = QWidget()
        cl = QVBoxLayout(center)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(7)
        inspection = QSplitter(Qt.Horizontal)
        inspection.setHandleWidth(7)
        source_card = QFrame()
        source_card.setObjectName('card')
        source_layout = QVBoxLayout(source_card)
        source_layout.setContentsMargins(10, 8, 10, 8)
        source_layout.addWidget(label('SEQUENCE PREVIEW', 'eyebrow'))
        self.source_name = label('Select a clip or play the sequence', 'subtle')
        source_layout.addWidget(self.source_name)
        self.video = QVideoWidget()
        self.video.setMinimumSize(80, 60)
        self.video.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.audio.setVolume(0.75)
        self.player.setAudioOutput(self.audio)
        self.player.setVideoOutput(self.video)
        self.player.mediaStatusChanged.connect(self.sequence_media_status)
        self.scrub_frame = PreviewStillLabel('Move the playhead to preview the sequence')
        self.scrub_frame.setMinimumSize(80, 60)
        self.scrub_frame.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.scrub_frame.setAlignment(Qt.AlignCenter)
        self.scrub_frame.setStyleSheet('background:#080a0b; color:#7f8b93;')
        self.preview_stack = QStackedWidget()
        self.preview_stack.addWidget(self.video)
        self.preview_stack.addWidget(self.scrub_frame)
        source_layout.addWidget(self.preview_stack, 1)
        source_controls = QHBoxLayout()
        self.play_button = button('▶', self.play_source)
        self.play_button.setText('')
        self.play_button.setIcon(tile_icon('play'))
        self.play_button.setAccessibleName('Play source')
        self.play_button.setToolTip('Play source')
        self.play_button.setFixedWidth(36)
        source_controls.addWidget(self.play_button)
        self.source_seek = MarkedSlider(Qt.Horizontal)
        self.source_seek.sliderMoved.connect(self.player.setPosition)
        self.player.positionChanged.connect(self.source_position)
        self.player.durationChanged.connect(lambda value: self.source_seek.setRange(0, value))
        source_controls.addWidget(self.source_seek)
        self.source_clock = label('00:00:00', 'subtle')
        source_controls.addWidget(self.source_clock)
        source_layout.addLayout(source_controls)
        inspection.addWidget(source_card)
        self.source_transcript = QTextBrowser()
        self.source_transcript.hide()
        self.sequence_preview = inspection
        cl.addWidget(inspection, 2)
        sequence_header = QHBoxLayout()
        self.sequence_tabs = timeline.SequenceTabBar()
        self.sequence_tabs.setTabsClosable(True)
        self.sequence_tabs.currentChanged.connect(self.sequence_changed)
        self.sequence_tabs.tabCloseRequested.connect(self.close_sequence)
        self.sequence_tabs.tabBarDoubleClicked.connect(self.rename_sequence)
        self.sequence_tabs.tabMoved.connect(self.sequence_moved)
        sequence_header.addWidget(self.sequence_tabs, 1)
        self.sequence_play = button('', self.toggle_sequence_playback)
        self.sequence_play.setIcon(tile_icon('play'))
        self.sequence_play.setAccessibleName('Play sequence')
        self.sequence_play.setToolTip('Play sequence from the playhead')
        sequence_header.addWidget(self.sequence_play)
        sequence_header.addWidget(button('+ Sequence', self.new_sequence))
        sequence_header.addWidget(button('Duplicate', self.duplicate_sequence))
        sequence_header.addWidget(button('Settings', self.sequence_settings))
        cl.addLayout(sequence_header)
        tools = QHBoxLayout()
        self.edit_buttons = {}
        shortcuts = {'undo': QKeySequence.Undo, 'redo': QKeySequence.Redo, 'cut': QKeySequence.Cut,
                     'copy': QKeySequence.Copy, 'paste': QKeySequence.Paste, 'delete': QKeySequence.Delete}
        for text, command_name in (('Undo', 'undo'), ('Redo', 'redo'), ('Split', 'split'),
                                   ('Cut', 'cut'), ('Copy', 'copy'), ('Paste', 'paste'),
                                   ('Duplicate', 'duplicate'), ('Delete', 'delete')):
            action = button(text, lambda checked=False, cmd=command_name: self.sequence_command(cmd))
            explanation = 'Duplicate selected clip' if command_name == 'duplicate' else text
            action.setToolTip(explanation + (f" · {QKeySequence(shortcuts[command_name]).toString()}" if command_name in shortcuts else ''))
            action.setObjectName('timelineTool')
            if command_name in shortcuts:
                action.setShortcut(shortcuts[command_name])
            action.setText('')
            action.setIcon(workspace.icon(command_name))
            action.setIconSize(QSize(18, 18))
            action.setFixedSize(32, 30)
            action.setAccessibleName(explanation)
            self.edit_buttons[command_name] = action
            tools.addWidget(action)
        tools.addStretch()
        cl.addLayout(tools)
        track_tools = QHBoxLayout()
        track_actions = (
            ('+ V', 'Add video track', lambda: self.add_track('video')),
            ('+ A', 'Add audio track', lambda: self.add_track('audio')),
            ('On/off', 'Show/hide a video track or mute/unmute an audio track', lambda: self.sequence_command('toggle_track')),
            ('Lock', 'Lock or unlock the selected track', lambda: self.sequence_command('lock_track')),
            ('Solo', 'Solo or unsolo the selected audio track', lambda: self.sequence_command('solo_track')),
            ('Marker', 'Add a marker at the playhead', lambda: self.sequence_command('marker')),
        )
        for text, tip, callback in track_actions:
            action = button(text, callback)
            action.setObjectName('timelineTool')
            action.setToolTip(tip)
            track_tools.addWidget(action)
        track_tools.addStretch()
        self.zoom = MarkedSlider(Qt.Horizontal)
        self.zoom.setRange(2, 80)
        self.zoom.setValue(10)
        self.zoom.setFixedWidth(95)
        self.zoom.setToolTip('Timeline zoom · Ctrl + mouse wheel also works')
        self.zoom.setFocusPolicy(Qt.NoFocus)
        self.zoom.valueChanged.connect(self.set_timeline_zoom)
        track_tools.addWidget(self.zoom)
        self.snap = button('Snap')
        self.snap.setObjectName('timelineTool')
        self.snap.setCheckable(True)
        self.snap.setChecked(True)
        self.snap.setToolTip('Snap clips and the playhead to edits and markers')
        self.snap.toggled.connect(lambda enabled: setattr(self.timeline_canvas, 'snap_enabled', enabled))
        track_tools.addWidget(self.snap)
        fit = button('Fit', self.fit_timeline)
        fit.setObjectName('timelineTool')
        fit.setToolTip('Fit the complete sequence in the timeline')
        track_tools.addWidget(fit)
        cl.addLayout(track_tools)
        self.timeline_scroll = QScrollArea()
        self.timeline_scroll.setWidgetResizable(False)
        self.timeline_scroll.setFrameShape(QFrame.NoFrame)
        self.timeline_canvas = timeline.TimelineCanvas()
        self.timeline_canvas.mediaDropped.connect(self.add_media_to_timeline)
        self.timeline_canvas.clipSelected.connect(self.timeline_clip_selected)
        self.timeline_canvas.changed.connect(self.timeline_drag_finished)
        self.timeline_canvas.commandRequested.connect(self.sequence_command)
        self.timeline_canvas.editBlocked.connect(self.status.setText)
        self.timeline_canvas.zoomChanged.connect(self.sync_timeline_zoom)
        self.timeline_canvas.zoomRequested.connect(self.set_timeline_zoom)
        self.timeline_canvas.playheadChanged.connect(self.timeline_playhead_changed)
        self.timeline_scroll.setWidget(self.timeline_canvas)
        self.timeline_scroll.horizontalScrollBar().valueChanged.connect(lambda _: self.store_sequence_view())
        cl.addWidget(self.timeline_scroll, 3)
        return center

    def sync_timeline_zoom(self, value):
        self.zoom.blockSignals(True)
        self.zoom.setValue(round(value))
        self.zoom.blockSignals(False)

    def set_timeline_zoom(self, value):
        old_zoom = self.timeline_canvas.pixels_per_second
        bar = self.timeline_scroll.horizontalScrollBar()
        anchor = timeline.TRACK_HEADER + self.timeline_canvas.playhead * old_zoom - bar.value()
        self.timeline_canvas.set_zoom(value)
        target = round(timeline.TRACK_HEADER + self.timeline_canvas.playhead *
                       self.timeline_canvas.pixels_per_second - anchor)
        QTimer.singleShot(0, lambda: bar.setValue(target))
        self.store_sequence_view()

    def add_library_media(self):
        project = self.current()
        if not project:
            return
        picker = LibraryPickerDialog(self.window.state.get('results', []), self)
        if picker.exec() != QDialog.Accepted:
            return
        selected = picker.selected_records()
        if not selected:
            return
        library_folder = next((folder for folder in project.get('folders', [])
                               if folder.get('path') == 'tracer://library'), None)
        if library_folder is None:
            library_folder = {'id': uuid.uuid4().hex, 'name': 'Video Library',
                              'path': 'tracer://library', 'files': []}
            project.setdefault('folders', []).append(library_folder)
        known = {str(video.get('path', '')).casefold() for video in library_folder['files']}
        videos = []
        all_media = [video for folder in self.window.state.get('folders', []) for video in folder.get('files', [])]
        for record in selected:
            source = str(record.get('source', ''))
            video = next((copy.deepcopy(value) for value in all_media
                          if str(value.get('path', '')).casefold() == source.casefold()), None)
            if video is None:
                duration = float(record.get('duration', 0) or
                                 max((segment.get('end', 0) for segment in record.get('segments', [])), default=0))
                video = {'path': source, 'name': Path(source).name, 'duration': duration,
                         'audio': bool(record.get('segments')), 'status': 'Done', 'selected': False}
            if source.casefold() not in known:
                library_folder['files'].append(video)
                known.add(source.casefold())
            videos.append(video)
        self.refresh(project['id'])
        for video in videos:
            self.add_media_to_timeline(video)
        self.status.setText(f"Added {len(videos)} library video{'s' if len(videos) != 1 else ''} to the sequence.")
        self.window.save_timer.start(100)

    def toggle_sequence_playback(self):
        sequence = self.active_sequence()
        if not sequence or timeline.sequence_duration(sequence) <= 0:
            self.status.setText('Add footage before playing the sequence.')
            return
        if self.sequence_playing:
            self.stop_sequence_playback()
            return
        if self.timeline_canvas.playhead >= timeline.sequence_duration(sequence):
            self.timeline_canvas.playhead = 0.0
        self.sequence_playing = True
        self.sequence_started = time.monotonic() - self.timeline_canvas.playhead
        self.playing_clip_id = None
        self.preview_stack.setCurrentWidget(self.video)
        self.sequence_play.setIcon(tile_icon('pause'))
        self.sequence_play.setAccessibleName('Pause sequence')
        self.sequence_play.setToolTip('Pause sequence')
        self.sequence_timer.start()
        self.sequence_tick()

    def stop_sequence_playback(self):
        self.sequence_playing = False
        self.sequence_timer.stop()
        self.player.pause()
        self.sequence_play.setIcon(tile_icon('play'))
        self.sequence_play.setAccessibleName('Play sequence')
        self.sequence_play.setToolTip('Play sequence from the playhead')
        self.store_sequence_view()

    def active_video_clip_at(self, sequence, position):
        if not sequence:
            return None
        # Timeline track order is visual z-order: the first visible video layer
        # wins when clips overlap.
        return next((clip for track in sequence.get('tracks', [])
                     if track.get('type') == 'video' and track.get('visible', True)
                     for clip in track.get('clips', [])
                     if float(clip.get('start', 0)) <= position < float(clip.get('end', 0))), None)

    def timeline_playhead_changed(self, position):
        if self.sequence_playing:
            self.stop_sequence_playback()
        self.seek_sequence_preview(position)
        self.store_sequence_view()

    def seek_sequence_preview(self, position):
        sequence = self.active_sequence()
        if not sequence:
            return
        clip = self.active_video_clip_at(sequence, float(position))
        if not clip:
            self.playing_clip_id = None
            self.pending_preview_position = None
            self.pending_scrub = None
            self.scrub_timer.stop()
            self.scrub_frame.setPixmap(QPixmap())
            self.scrub_frame.setText(f'No video at {duration_text(position)}')
            self.preview_stack.setCurrentWidget(self.scrub_frame)
            self.source_name.setText(f'No video at {duration_text(position)}')
            self.source_clock.setText(duration_text(position))
            return
        source = Path(str(clip.get('source', '')))
        if not source.is_file():
            self.playing_clip_id = None
            self.pending_preview_position = None
            self.pending_scrub = None
            self.scrub_timer.stop()
            self.scrub_frame.setPixmap(QPixmap())
            self.scrub_frame.setText('Offline media')
            self.preview_stack.setCurrentWidget(self.scrub_frame)
            self.source_name.setText('Offline media · ' + (clip.get('name') or source.name))
            self.source_clock.setText(duration_text(position))
            return
        source_position = max(0.0, float(clip.get('source_in', 0)) +
                              float(position) - float(clip.get('start', 0)))
        self.playing_clip_id = None
        self.pending_preview_position = round(source_position * 1000)
        self.pending_scrub = (str(source), source_position, clip.get('name', source.name))
        self.scrub_timer.start()
        self.source_name.setText(clip.get('name', source.name))
        self.source_clock.setText(duration_text(position))

    def render_scrub_frame(self):
        pending = self.pending_scrub
        if not pending:
            return
        source, seconds, name = pending
        sample = core.frame_at(source, seconds)
        if not sample or self.pending_scrub != pending:
            return
        image, _ = sample
        image = image.convert('RGB')
        data = image.tobytes('raw', 'RGB')
        rendered = QImage(data, image.width, image.height, image.width * 3,
                          QImage.Format.Format_RGB888).copy()
        pixmap = QPixmap.fromImage(rendered)
        self.scrub_frame.setText('')
        self.scrub_frame.setPixmap(pixmap)
        self.scrub_frame.setToolTip(f'{name} · {duration_text(seconds)} source time')
        self.preview_stack.setCurrentWidget(self.scrub_frame)

    def sequence_media_status(self, status):
        if self.pending_preview_position is None or not self.sequence_playing:
            return
        if status in (QMediaPlayer.MediaStatus.LoadedMedia, QMediaPlayer.MediaStatus.BufferedMedia):
            self.player.setPosition(self.pending_preview_position)
            if self.sequence_playing:
                self.player.play()

    def follow_playhead(self):
        bar = self.timeline_scroll.horizontalScrollBar()
        x = timeline.TRACK_HEADER + self.timeline_canvas.playhead * self.timeline_canvas.pixels_per_second
        left, right = bar.value() + 36, bar.value() + self.timeline_scroll.viewport().width() - 36
        if x < left or x > right:
            bar.setValue(round(x - self.timeline_scroll.viewport().width() * .28))

    def sequence_tick(self):
        sequence = self.active_sequence()
        if not self.sequence_playing or not sequence:
            return
        position = time.monotonic() - self.sequence_started
        if position >= timeline.sequence_duration(sequence):
            self.timeline_canvas.set_playhead(timeline.sequence_duration(sequence))
            self.follow_playhead()
            self.store_sequence_view()
            self.stop_sequence_playback()
            return
        self.timeline_canvas.set_playhead(position)
        active_clip = self.active_video_clip_at(sequence, position)
        if active_clip and active_clip.get('id') != self.playing_clip_id:
            if not Path(str(active_clip.get('source', ''))).is_file():
                self.player.pause()
                self.player.setSource(QUrl())
                self.playing_clip_id = active_clip.get('id')
                self.source_name.setText('Offline media · ' + active_clip.get('name', 'missing source'))
                self.source_clock.setText(duration_text(position))
                self.follow_playhead()
                return
            self.playing_clip_id = active_clip.get('id')
            self.preview_stack.setCurrentWidget(self.video)
            self.player.setSource(QUrl.fromLocalFile(active_clip['source']))
            self.pending_preview_position = round((float(active_clip.get('source_in', 0)) + position -
                                                   float(active_clip['start'])) * 1000)
            self.player.setPosition(self.pending_preview_position)
            self.player.play()
            self.source_name.setText(active_clip.get('name', Path(active_clip['source']).name))
        elif not active_clip and self.playing_clip_id is not None:
            self.player.pause()
            self.player.setSource(QUrl())
            self.playing_clip_id = None
            self.source_name.setText(f'No video at {duration_text(position)}')
        self.source_clock.setText(duration_text(position))
        self.follow_playhead()

    def build_export_panel(self):
        card = QFrame()
        card.setObjectName('card')
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.addWidget(label('EXPORT QUEUE', 'eyebrow'))
        hint = label('Drag a sequence tab here to queue it for delivery.', 'subtle')
        hint.setWordWrap(True)
        layout.addWidget(hint)
        self.export_queue = timeline.ExportQueueList()
        self.export_queue.sequenceDropped.connect(self.queue_sequence)
        self.export_queue.currentItemChanged.connect(
            lambda current, previous: self.remove_export_button.setEnabled(bool(current)))
        layout.addWidget(self.export_queue, 1)
        self.queue_button = button('Queue active sequence', self.queue_sequence)
        layout.addWidget(self.queue_button)
        self.export_xml_button = button('Export Premiere XML', self.export_sequence, True)
        self.export_xml_button.setToolTip('Write an FCP 7 XML timeline for import into Premiere Pro')
        layout.addWidget(self.export_xml_button)
        self.collect_button = button('Collect used media', self.collect_media)
        layout.addWidget(self.collect_button)
        self.relink_button = button('Relink offline media', self.relink_offline_media)
        layout.addWidget(self.relink_button)
        self.remove_export_button = button('Remove from queue', self.remove_export_item)
        layout.addWidget(self.remove_export_button)
        self.export_status = label('Nothing queued.', 'subtle')
        self.export_status.setWordWrap(True)
        layout.addWidget(self.export_status)
        return card

    def current(self):
        item = self.projects.currentItem()
        project_id = item.data(Qt.UserRole) if item else None
        return next((p for p in self.window.state['projects'] if p['id'] == project_id), None)

    def active_sequence(self):
        project = self.current()
        sequence_id = self.sequence_tabs.tabData(self.sequence_tabs.currentIndex())
        return next((s for s in project.get('sequences', []) if s['id'] == sequence_id), None) if project else None

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
            timeline.ensure_project_editing(project)
            files = [v for folder in project.get('folders', []) for v in folder.get('files', [])]
            item = QListWidgetItem(f"{project['name']}\n{len(files)} media · {len(project['sequences'])} sequences")
            item.setData(Qt.UserRole, project['id'])
            self.projects.addItem(item)
        self.projects.blockSignals(False)
        if current:
            self.select_project(current)
        elif self.projects.count():
            self.projects.setCurrentRow(0)
        else:
            self.populate_tree()
            self.populate_sequences()
            self.populate_export_queue()

    def project_changed(self, current, previous=None):
        self.player.stop()
        self.populate_tree()
        self.populate_sequences()
        self.populate_export_queue()
        if self.current() and not self.window.batch:
            self.status.setText('Ready. Open the Library, then drag, stack, or split your footage.')

    def populate_tree(self):
        project = self.current()
        self.tree.blockSignals(True)
        self.tree.clear()
        self.item_map.clear()
        if not project:
            self.page_title.setText('Storyline')
            self.page_subtitle.setText('Stack footage, shape the cut, and send finished sequences to Delivery.')
            self.summary.setText('No sequence workspace available.')
        else:
            timeline.ensure_project_editing(project)
            self.page_title.setText('Storyline')
            has_files = any(folder.get('files') for folder in project.get('folders', []))
            self.page_subtitle.setText('Stack footage, shape the cut, and send finished sequences to Delivery.')
            for folder in project.get('folders', []):
                parent = QTreeWidgetItem([folder['name'], '', ''])
                parent.setData(0, Qt.UserRole, (folder['id'], None))
                parent.setToolTip(0, folder['path'])
                self.tree.addTopLevelItem(parent)
                for video in folder.get('files', []):
                    child = QTreeWidgetItem([video['name'], duration_text(video.get('duration', 0)), video.get('status', 'Ready')])
                    child.setData(0, Qt.UserRole, (folder['id'], video['path']))
                    child.setToolTip(0, video['path'])
                    child.setToolTip(2, video.get('error', ''))
                    parent.addChild(child)
                    if video.get('status') == 'Unreadable':
                        child.setDisabled(True)
                    self.item_map[(folder['id'], video['path'])] = child
                    if video.get('status') != 'Unreadable':
                        payload = {key: video.get(key) for key in ('path', 'name', 'duration', 'audio', 'status')}
                        child.setData(0, Qt.UserRole + 1, payload)
                parent.setExpanded(True)
            if not has_files:
                placeholder = QTreeWidgetItem(['No media yet', '', ''])
                placeholder.setDisabled(True)
                self.tree.addTopLevelItem(placeholder)
        self.tree.blockSignals(False)
        self.update_summary()

    def tree_item_changed(self, item, previous=None):
        self.update_summary()
        if not item:
            return
        value = item.data(0, Qt.UserRole)
        project = self.current()
        if not project or not value or not value[1]:
            return
        video = next((video for folder in project.get('folders', []) if folder['id'] == value[0]
                      for video in folder.get('files', []) if video['path'] == value[1]), None)
        if video:
            self.inspect_source(video)

    def inspect_source(self, video):
        if not video or not video.get('path'):
            return
        self.source_name.setText(video.get('name') or Path(video['path']).name)
        self.pending_scrub = None
        self.scrub_timer.stop()
        self.preview_stack.setCurrentWidget(self.video)
        self.player.stop()
        self.player.setSource(QUrl.fromLocalFile(video['path']))
        result = next((record for record in self.window.state.get('results', [])
                       if str(record.get('source', '')).casefold() == str(video['path']).casefold()), None)
        if result and result.get('segments'):
            self.source_transcript.setPlainText('\n'.join(
                f"{duration_text(segment.get('start', 0))}   {segment.get('text', '').strip()}"
                for segment in result['segments']))
        else:
            self.source_transcript.setPlainText('No processed transcript is available for this source yet.')

    def play_source(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_button.setIcon(tile_icon('play'))
            self.play_button.setAccessibleName('Play source')
            self.play_button.setToolTip('Play source')
        else:
            if self.pending_scrub:
                source, seconds, _ = self.pending_scrub
                self.player.setSource(QUrl.fromLocalFile(source))
                self.player.setPosition(round(seconds * 1000))
                self.preview_stack.setCurrentWidget(self.video)
            self.player.play()
            self.play_button.setIcon(tile_icon('pause'))
            self.play_button.setAccessibleName('Pause source')
            self.play_button.setToolTip('Pause source')

    def source_position(self, value):
        if not self.source_seek.isSliderDown():
            self.source_seek.setValue(value)
        self.source_clock.setText(duration_text(value / 1000))

    def selection_changed(self, item, column):
        if column != 0:
            return
        project = self.current()
        if not project:
            return
        for folder in project.get('folders', []):
            for video in folder.get('files', []):
                child = self.item_map.get((folder['id'], video['path']))
                video['selected'] = bool(child and child.checkState(0) == Qt.Checked and video.get('status') != 'Unreadable')
        self.update_summary()
        self.window.save_timer.start(300)

    def update_summary(self):
        project = self.current()
        files = [v for folder in project.get('folders', []) for v in folder.get('files', [])] if project else []
        if project:
            sequence = self.active_sequence()
            sequence_text = (f"\n{sequence['name']} · {duration_text(timeline.sequence_duration(sequence))}"
                             if sequence else '')
            self.summary.setText(f"{len(files)} source{'s' if len(files) != 1 else ''}{sequence_text}")
        self.process.setEnabled(False)
        can_add = bool(project) and not self.window.batch and not self.window.scanning
        self.add_media_button.setEnabled(can_add)
        self.remove_source.setEnabled(bool(project) and bool(self.tree.currentItem()) and not self.window.batch and not self.window.scanning)
        has_media = bool(files)
        self.tree.setVisible(bool(project))
        for widget in (self.media_hint, self.insert_media_button, self.status):
            widget.setVisible(has_media)
        for widget in (self.progress, self.progress_detail, self.processing_box):
            widget.hide()
        self.editor_stack.setCurrentIndex(1 if project else 0)
        self.delivery_toggle.setEnabled(has_media)
        if not has_media:
            self.set_delivery_open(False)
        self.empty_title.setText('Build your first sequence')
        self.empty_copy.setText(
            'Search the Video Library, select one or more sources, and add them directly to this timeline.')
        self.empty_action_button.setText('+ Open Video Library')
        sequence = self.active_sequence() if project else None
        has_timeline = bool(sequence and timeline.sequence_duration(sequence) > 0)
        self.queue_button.setEnabled(has_timeline)
        self.export_xml_button.setEnabled(has_timeline)
        self.collect_button.setEnabled(has_timeline)
        self.relink_button.setEnabled(has_timeline)
        self.remove_export_button.setEnabled(bool(self.export_queue.currentItem()))

    def set_busy(self, busy):
        for widget in (self.projects, self.tree, self.add_media_button, self.remove_source):
            widget.setEnabled(not busy)
        if not busy:
            self.update_summary()


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Tracer')
        self.resize(1440, 900)
        self.setMinimumSize(1020, 720)
        self.setAcceptDrops(True)
        self.state = core.load_state()
        self.state['settings'] = {**core.DEFAULTS, **self.state.get('settings', {})}
        if not self.state.get('projects'):
            self.state['projects'] = [{
                'id': uuid.uuid4().hex, 'name': 'Storyline', 'created': time.time(), 'folders': []
            }]
        timeline.ensure_project_editing(self.state['projects'][0])
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
        sidebar.setFixedWidth(76)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(4, 14, 4, 14)
        brand = QVBoxLayout()
        brand.setAlignment(Qt.AlignHCenter)
        mark = QLabel()
        asset = Path(getattr(sys, '_MEIPASS', core.ROOT)) / 'assets' / 'transpro.svg'
        mark.setPixmap(QIcon(str(asset)).pixmap(20, 20))
        mark.setAlignment(Qt.AlignCenter)
        brand.addWidget(mark)
        brand_name = label('Tracer', 'brand')
        brand_name.setAlignment(Qt.AlignCenter)
        brand_name.setStyleSheet('font-size: 15px;')
        brand.addWidget(brand_name)
        side.addLayout(brand)
        side.addSpacing(18)
        self.nav = []
        navigation = (
            ('Queue', 'queue'), ('Library', 'library'), ('Paper Edit', 'paper'),
            ('Storyline', 'storyline'), ('Settings', 'settings'))
        for i, (name, icon_name) in enumerate(navigation):
            b = QToolButton()
            b.setText(name)
            b.setIcon(tile_icon(icon_name))
            b.setIconSize(QSize(18, 18))
            b.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            b.setFixedHeight(54)
            b.clicked.connect(lambda checked=False, index=i: self.navigate(index))
            b.setObjectName('nav')
            b.setCheckable(True)
            b.setToolTip((
                'Folder processing queue', 'Searchable video library',
                'Write and shape the story from transcripts', 'Simple stackable sequence timeline', 'Settings')[i])
            b.setAccessibleName(name)
            self.nav.append(b)
            side.addWidget(b)
        side.addStretch()
        self.usage_labels = {}
        for key in ('GPU', 'VRAM', 'RAM'):
            meter = label(f'{key}  — / —', 'resourceMeter')
            meter.setAlignment(Qt.AlignCenter)
            side.addWidget(meter)
            self.usage_labels[key.casefold()] = meter
        side.addSpacing(10)
        version = label('Tracer · ' + core.APP_VERSION.rsplit('.', 1)[0], 'subtle')
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet('font-size: 9px;')
        side.addWidget(version)
        outer.addWidget(sidebar)
        self.pages = QStackedWidget()
        queue_page = self.make_queue()
        self.paper_edit_page = PaperEditPage(self)
        self.projects_page = ProjectsPage(self)
        self.results = ResultsPage()
        self.results.install_modular_workspace(self)
        self.results.set_records(self.state['results'])
        self.pages.addWidget(queue_page)
        self.pages.addWidget(self.results)
        self.pages.addWidget(self.paper_edit_page)
        self.pages.addWidget(self.projects_page)
        self.pages.addWidget(self.make_settings())
        outer.addWidget(self.pages, 1)
        self.setCentralWidget(root)
        self.navigate(0)
        self.fullscreen_shortcut = QShortcut(QKeySequence('F11'), self)
        self.fullscreen_shortcut.activated.connect(lambda: self.showNormal() if self.isFullScreen() else self.showFullScreen())
        self.refresh_tree()
        self.run_task(lambda notify: core.gpu_info(), lambda v: self.gpu.setText(v))
        self.usage_task_active = False
        self.usage_task = None
        self.usage_timer = QTimer(self)
        self.usage_timer.setInterval(3500)
        self.usage_timer.timeout.connect(self.refresh_usage_metrics)
        self.usage_timer.start()
        QTimer.singleShot(900, self.refresh_usage_metrics)
        if self.state.get('recovery'):
            self.status.setText('Library was recovered. Previous data saved at ' + self.state['recovery'])
        QTimer.singleShot(600, self.first_setup)

    def navigate(self, index):
        previous = self.pages.currentWidget()
        if hasattr(previous, 'desk'):
            previous.desk.remember()
        self.pages.setCurrentIndex(index)
        for i, b in enumerate(self.nav):
            b.setChecked(i == index)
        if index != 1 and hasattr(self, 'results'):
            self.results.player.pause()
        if index != 2 and hasattr(self, 'paper_edit_page'):
            self.paper_edit_page.player.pause()
        if index != 3 and hasattr(self, 'projects_page'):
            self.projects_page.stop_sequence_playback()

    def refresh_usage_metrics(self):
        if self.usage_task_active:
            return
        self.usage_task_active = True
        task = Task(lambda notify: core.system_usage_snapshot(os.getpid()), self)
        self.usage_task = task
        task.done.connect(self.apply_usage_metrics)
        task.finished.connect(self.usage_metrics_finished)
        task.finished.connect(task.deleteLater)
        task.start()

    def usage_metrics_finished(self):
        self.usage_task_active = False
        self.usage_task = None

    def apply_usage_metrics(self, values):
        for key, widget in self.usage_labels.items():
            app_value, system_value = values.get(key, (None, None))
            if app_value is None or system_value is None:
                widget.setText(f'{key.upper()}  — / —')
            else:
                app_text = f'{app_value:.1f}' if 0 < app_value < 10 else f'{app_value:.0f}'
                system_text = f'{system_value:.1f}' if 0 < system_value < 10 else f'{system_value:.0f}'
                widget.setText(f'{key.upper()}  {app_text} / {system_text}%')
                widget.setToolTip(f'Tracer / total system {key.upper()} usage')

    def make_queue(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(13)
        layout.addWidget(label('FOLDER QUEUE', 'eyebrow'))
        heading = QHBoxLayout()
        heading.addWidget(label('Batch workspace', 'title'))
        heading.addStretch()
        self.remove = QueueDeleteButton()
        self.remove.clicked.connect(self.remove_folder)
        self.remove.setObjectName('queueDelete')
        self.remove.setFixedSize(38, 36)
        self.remove.setAccessibleName('Remove selected item from queue')
        self.remove.setToolTip('Remove the selected folder or video from this queue. Nothing is deleted from disk.')
        heading.addWidget(self.remove)
        self.add_button = button('+ Add media', self.add_media, primary=True)
        self.add_button.setToolTip('Open the Windows video picker. You can also drag videos or folders here from Explorer.')
        heading.addWidget(self.add_button)
        layout.addLayout(heading)
        layout.addWidget(label(
            'Choose videos with the native Windows picker, or drag videos and folders here from Explorer. '
            'Folders run from top to bottom.', 'subtle'))
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
        self.rescan = button('Rescan', self.rescan_folder)
        for b in (self.up, self.down, self.rescan):
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
        self.tree.currentItemChanged.connect(lambda *_: self.update_queue_controls())
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
        storage.addWidget(button('Clear AI preview cache', self.clear_visual_detail_cache))
        storage.addStretch()
        layout.addLayout(storage)
        note = label('Automatic mode prefers the NVIDIA GPU and falls back to CPU if the GPU runtime fails.\nScene mode detects visual cuts; it may miss gradual transitions.\nPause and cancel take effect at the next decoded frame or transcript segment.', 'subtle')
        note.setWordWrap(True)
        layout.addWidget(note)
        about = QFrame()
        about.setObjectName('card')
        about_layout = QVBoxLayout(about)
        about_layout.setContentsMargins(19, 15, 19, 15)
        about_layout.setSpacing(5)
        about_layout.addWidget(label('Tracer · ' + core.APP_VERSION.rsplit('.', 1)[0], 'eyebrow'))
        about_layout.addWidget(label('Find the shot. Build the cut.'))
        about_copy = label(
            'Turns folders into searchable material, and searchable material into something resembling a story.\n'
            'Less hunting. More cutting. Fewer files named FINAL_final_v7_use-this-one.', 'subtle')
        about_copy.setWordWrap(True)
        about_layout.addWidget(about_copy)
        layout.addWidget(about)
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

    def clear_visual_detail_cache(self):
        folders = []
        for record in self.state.get('results', []):
            detail = Path(record.get('output', '')) / 'visual-index' / 'detail'
            if detail.is_dir():
                folders.append(detail)
        files = [path for folder in folders for path in folder.glob('*.jpg') if path.is_file()]
        if not files:
            QMessageBox.information(self, 'AI preview cache', 'There are no generated detail previews to clear.')
            return
        if QMessageBox.question(self, 'Clear AI preview cache?',
                                f'Remove {len(files):,} generated detail previews? Search labels and source footage are unaffected.') != QMessageBox.Yes:
            return
        freed = 0
        for path in files:
            try:
                freed += path.stat().st_size
                path.unlink()
            except OSError:
                pass
        self.download_status.setText(f'Cleared {size_text(freed)} of generated AI detail previews.')

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
            self.visual_model_state.setText(('Installed · ' if ready else 'Included · approximately ') + size_text(size))
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
        path = QFileDialog.getExistingDirectory(self, title, '', QFileDialog.ShowDirsOnly)
        return [path] if path else []

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

    def add_project_media(self):
        project = self.projects_page.current()
        if not project or self.scanning or self.batch:
            return
        picker = MediaPickerDialog(self)
        picker.setWindowTitle('Add media to ' + project['name'])
        if picker.exec() == QDialog.Accepted:
            self.scan_project_sources(project, picker.media_paths())

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
        folder_paths, video_paths = partition_media_paths(paths)
        folder_paths = list(dict.fromkeys(str(Path(path).resolve()) for path in folder_paths))
        existing = {v['path'].casefold() for f in project.get('folders', []) for v in f.get('files', [])}
        video_paths = list(dict.fromkeys(
            str(Path(path).resolve()) for path in video_paths
            if str(Path(path).resolve()).casefold() not in existing))
        if not folder_paths and not video_paths:
            self.projects_page.status.setText('Those sources are already in this project.')
            return
        self.scanning = True
        self.set_busy(True)
        self.projects_page.progress.setRange(0, 0)
        self.projects_page.status.setText('Reading project sources…')
        def scan(notify):
            folders = [core.scan_folder(path, self.state['settings']['recursive'], notify)
                       for path in folder_paths]
            if video_paths:
                folders.extend(core.scan_files(video_paths, notify))
            return folders

        fn = scan
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

    def add_media(self):
        if self.scanning or self.batch:
            return
        paths, _ = QFileDialog.getOpenFileNames(
            self, 'Add videos', '',
            'Video files (*.mp4 *.mkv *.mov *.avi *.webm *.m4v *.mpeg *.mpg *.mts *.m2ts *.wmv *.flv)')
        if paths:
            self.scan_media_paths(paths)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and not self.scanning and not self.batch:
            paths = [Path(url.toLocalFile()) for url in event.mimeData().urls() if url.isLocalFile()]
            if any(path.is_dir() or path.suffix.casefold() in core.EXTENSIONS for path in paths):
                event.acceptProposedAction()
                return
        super().dragEnterEvent(event)

    def dropEvent(self, event):
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        paths = [path for path in paths
                 if Path(path).is_dir() or Path(path).suffix.casefold() in core.EXTENSIONS]
        if paths:
            self.scan_media_paths(paths)
            event.acceptProposedAction()
            return
        super().dropEvent(event)

    def scan_media_paths(self, paths):
        if self.scanning or self.batch or not paths:
            return
        folder_paths, video_paths = partition_media_paths(paths)
        known_folders = {str(Path(folder['path']).resolve()).casefold() for folder in self.state['folders']}
        known_videos = {
            str(Path(video['path']).resolve()).casefold()
            for folder in self.state['folders'] for video in folder['files']
        }
        folder_paths = [path for path in folder_paths if path.casefold() not in known_folders]
        video_paths = [path for path in video_paths if path.casefold() not in known_videos]
        if not folder_paths and not video_paths:
            self.status.setText('Those folders and videos are already in the queue.')
            return
        recursive = self.recursive.isChecked()
        self.scanning = True
        self.set_busy(True)
        self.progress.setRange(0, 0)
        self.status.setText('Reading selected media…')

        def scan(notify):
            folders = [core.scan_folder(path, recursive, notify) for path in folder_paths]
            if video_paths:
                folders.extend(core.scan_files(video_paths, notify))
            return folders

        task = self.run_task(scan, self.video_paths_scanned,
                             lambda path: self.status.setText('Reading · ' + path))
        task.finished.connect(self.scan_finished)

    def add_folders(self):
        paths = self.choose_folders('Add folders')
        if paths:
            self.scan_paths(paths)

    def add_video_files(self):
        if self.scanning or self.batch:
            return
        paths, _ = QFileDialog.getOpenFileNames(
            self, 'Add individual videos', '',
            'Video files (*.mp4 *.mkv *.mov *.avi *.webm *.m4v *.mpeg *.mpg *.mts *.m2ts *.wmv *.flv)')
        if paths:
            self.scan_video_paths(paths)

    def scan_video_paths(self, paths):
        if self.scanning or self.batch or not paths:
            return
        known = {v['path'].casefold() for folder in self.state['folders'] for v in folder['files']}
        paths = [str(Path(p).resolve()) for p in paths if str(Path(p).resolve()).casefold() not in known]
        if not paths:
            self.status.setText('Those videos are already in the queue.')
            return
        self.scanning = True
        self.set_busy(True)
        self.progress.setRange(0, 0)
        self.status.setText('Reading selected videos…')
        task = self.run_task(lambda notify: core.scan_files(paths, notify), self.video_paths_scanned,
                             lambda p: self.status.setText('Reading · ' + p))
        task.finished.connect(self.scan_finished)

    def video_paths_scanned(self, folders):
        affected_paths = {incoming['path'].casefold() for incoming in folders}
        for incoming in folders:
            target = next((f for f in self.state['folders'] if f['path'].casefold() == incoming['path'].casefold()), None)
            if target:
                known = {v['path'].casefold() for v in target['files']}
                target['files'].extend(v for v in incoming['files'] if v['path'].casefold() not in known)
            else:
                self.state['folders'].append(incoming)
        self.refresh_tree()
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            folder = next(f for f in self.state['folders'] if f['id'] == item.data(0, Qt.UserRole)[0])
            if folder['path'].casefold() in affected_paths:
                item.setExpanded(True)
        self.save()

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
        added_ids = set()
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
            added_ids = {folder['id'] for folder in folders}
        self.refresh_tree()
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.data(0, Qt.UserRole)[0] in added_ids:
                item.setExpanded(True)
        self.save()

    def scan_finished(self):
        self.scanning = False
        self.set_busy(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.status.setText('Media scan finished. Expand a folder to review individual video selections.')

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
        item = self.tree.currentItem()
        if not item:
            return
        folder_id, video_path = item.data(0, Qt.UserRole)
        folder = next((f for f in self.state['folders'] if f['id'] == folder_id), None)
        if not folder:
            return
        if video_path:
            folder['files'] = [v for v in folder['files'] if v['path'] != video_path]
            if not folder['files']:
                self.state['folders'].remove(folder)
            message = 'Video removed from the queue.'
        else:
            self.state['folders'].remove(folder)
            message = 'Folder removed from the queue.'
        self.refresh_tree()
        self.status.setText(message + ' Nothing was deleted from disk.')
        self.save()

    def update_queue_controls(self):
        available = bool(self.tree.currentItem()) and not self.scanning and not self.batch
        folder = self.current_folder()
        self.remove.setEnabled(available)
        self.rescan.setEnabled(available and bool(folder))
        self.up.setEnabled(available and bool(folder))
        self.down.setEnabled(available and bool(folder))

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
        selected_item = self.tree.currentItem()
        selected_key = selected_item.data(0, Qt.UserRole) if selected_item else None
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
        if selected_key:
            target = self.item_map.get(tuple(selected_key))
            if target:
                self.tree.setCurrentItem(target)
            else:
                for index in range(self.tree.topLevelItemCount()):
                    parent = self.tree.topLevelItem(index)
                    if parent.data(0, Qt.UserRole)[0] == selected_key[0]:
                        self.tree.setCurrentItem(parent)
                        break
        if not self.tree.currentItem() and self.tree.topLevelItemCount():
            self.tree.setCurrentItem(self.tree.topLevelItem(0))
        self.update_stats()
        self.update_queue_controls()

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
        if not busy:
            self.update_queue_controls()
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
        if hasattr(self, 'usage_timer'):
            self.usage_timer.stop()
        if self.usage_task and self.usage_task.isRunning():
            self.usage_task.wait(6000)
        if self.batch or self.scanning or self.downloading:
            QMessageBox.information(self, 'Work is still running', 'Cancel the batch and wait for it to stop before closing. Scans and model downloads must finish first.')
            event.ignore()
            return
        if self.tasks:
            event.ignore()
            return
        self.projects_page.sequence_timer.stop()
        self.projects_page.pending_preview_position = None
        for player in (self.results.player, self.paper_edit_page.player, self.projects_page.player):
            player.blockSignals(True)
            player.deleteLater()
        for page in (self.results, self.paper_edit_page, self.projects_page):
            if hasattr(page, 'desk'):
                page.desk.remember()
        self.save_timer.stop()
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
    enable_high_dpi()
    try:
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    except AttributeError:
        pass
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
