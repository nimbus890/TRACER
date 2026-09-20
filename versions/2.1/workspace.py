"""Page-local native docking and layout memory. Original Qt implementation."""
from PySide6.QtCore import Qt, QByteArray, QSize, QPoint
from PySide6.QtGui import (QColor, QIcon, QPainter, QPen, QPixmap, QShortcut,
                           QKeySequence, QPolygon)
from PySide6.QtWidgets import (QWidget, QMainWindow, QDockWidget, QHBoxLayout,
    QLabel, QToolButton, QMenu, QInputDialog, QTabWidget)


def icon(name, color='#d8dfe3'):
    pix = QPixmap(40, 40)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    p.scale(2, 2)
    p.setPen(QPen(QColor(color), 1.35, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    if name in ('landscape', 'portrait'):
        p.drawRoundedRect(2 if name == 'landscape' else 5, 5 if name == 'landscape' else 2,
                          16 if name == 'landscape' else 10, 10 if name == 'landscape' else 16, 1, 1)
    elif name in ('balanced', 'left', 'right'):
        p.drawRoundedRect(2, 3, 16, 14, 1, 1)
        x = {'balanced': 10, 'left': 6, 'right': 14}[name]
        p.drawLine(x, 3, x, 17)
    elif name in ('expand', 'focus'):
        for x, y, dx, dy in ((3, 3, 1, 1), (17, 3, -1, 1), (3, 17, 1, -1), (17, 17, -1, -1)):
            p.drawLine(x, y, x + dx * 4, y)
            p.drawLine(x, y, x, y + dy * 4)
    elif name == 'more':
        p.setBrush(QColor(color))
        for x in (4, 10, 16):
            p.drawEllipse(x - 1, 9, 2, 2)
    elif name == 'grip':
        for x in (7, 12):
            for y in (5, 10, 15):
                p.drawPoint(x, y)
    elif name == 'close':
        p.drawLine(6, 6, 14, 14)
        p.drawLine(14, 6, 6, 14)
    elif name in ('undo', 'redo'):
        if name == 'redo':
            p.translate(20, 0)
            p.scale(-1, 1)
        p.drawArc(5, 6, 11, 10, -30 * 16, 230 * 16)
        p.drawLine(4, 5, 4, 10)
        p.drawLine(4, 10, 9, 10)
    elif name in ('copy', 'duplicate'):
        p.drawRoundedRect(7, 7, 10, 11, 1, 1)
        p.drawLine(3, 13, 3, 3)
        p.drawLine(3, 3, 13, 3)
    elif name == 'paste':
        p.drawRoundedRect(4, 4, 12, 14, 1, 1)
        p.drawRoundedRect(7, 2, 6, 4, 1, 1)
    elif name == 'cut':
        p.drawEllipse(2, 12, 5, 5)
        p.drawEllipse(12, 12, 5, 5)
        p.drawLine(6, 13, 15, 3)
        p.drawLine(13, 13, 5, 3)
    elif name == 'split':
        p.drawLine(10, 2, 10, 18)
        p.drawLine(3, 6, 7, 6)
        p.drawLine(3, 6, 3, 14)
        p.drawLine(3, 14, 7, 14)
        p.drawLine(13, 6, 17, 6)
        p.drawLine(17, 6, 17, 14)
        p.drawLine(13, 14, 17, 14)
    elif name == 'delete':
        p.drawLine(3, 5, 17, 5)
        p.drawLine(7, 2, 13, 2)
        p.drawRoundedRect(5, 5, 10, 12, 1, 1)
        p.drawLine(8, 8, 8, 14)
        p.drawLine(12, 8, 12, 14)
    elif name == 'select':
        p.drawPolygon(QPolygon([QPoint(4, 2), QPoint(15, 11), QPoint(10, 12),
                                QPoint(13, 18), QPoint(10, 19), QPoint(7, 13), QPoint(3, 16)]))
    elif name == 'track_select':
        p.drawLine(3, 5, 17, 5)
        p.drawLine(6, 10, 17, 10)
        p.drawLine(9, 15, 17, 15)
        p.drawLine(3, 3, 3, 17)
        p.drawLine(3, 10, 7, 7)
        p.drawLine(3, 10, 7, 13)
    elif name == 'ripple':
        p.drawLine(10, 2, 10, 18)
        p.drawLine(2, 10, 7, 10)
        p.drawLine(4, 7, 7, 10)
        p.drawLine(4, 13, 7, 10)
        p.drawLine(13, 10, 18, 10)
        p.drawLine(16, 7, 13, 10)
        p.drawLine(16, 13, 13, 10)
    elif name == 'razor':
        p.drawPolygon(QPolygon([QPoint(4, 5), QPoint(16, 3), QPoint(18, 8),
                                QPoint(7, 17), QPoint(3, 14), QPoint(8, 9)]))
        p.drawLine(8, 9, 18, 8)
        p.drawEllipse(6, 6, 2, 2)
    elif name == 'hand':
        p.drawLine(6, 9, 6, 5)
        p.drawLine(9, 9, 9, 3)
        p.drawLine(12, 9, 12, 4)
        p.drawLine(15, 10, 15, 6)
        p.drawLine(6, 9, 4, 8)
        p.drawLine(4, 8, 3, 10)
        p.drawLine(3, 10, 8, 17)
        p.drawLine(8, 17, 14, 17)
        p.drawLine(14, 17, 17, 12)
    elif name == 'zoom':
        p.drawEllipse(3, 3, 11, 11)
        p.drawLine(12, 12, 18, 18)
        p.drawLine(6, 8, 11, 8)
        p.drawLine(8, 6, 8, 11)
    elif name == 'video_track':
        p.drawRoundedRect(2, 5, 12, 10, 1, 1)
        p.drawPolygon(QPolygon([QPoint(14, 8), QPoint(18, 6), QPoint(18, 14), QPoint(14, 12)]))
        p.drawLine(8, 2, 8, 18)
        p.drawLine(5, 10, 11, 10)
    elif name == 'audio_track':
        p.drawLine(8, 5, 8, 15)
        p.drawLine(8, 5, 15, 3)
        p.drawLine(15, 3, 15, 13)
        p.drawEllipse(3, 13, 5, 4)
        p.drawEllipse(10, 11, 5, 4)
        p.drawLine(2, 4, 6, 4)
        p.drawLine(4, 2, 4, 6)
    elif name == 'toggle':
        p.drawEllipse(2, 6, 16, 9)
        p.drawEllipse(7, 7, 6, 6)
    elif name == 'lock':
        p.drawRoundedRect(4, 8, 12, 9, 1, 1)
        p.drawArc(6, 2, 8, 10, 0, 180 * 16)
    elif name == 'solo':
        p.drawEllipse(3, 3, 14, 14)
        p.drawText(7, 14, 'S')
    elif name == 'marker':
        p.drawLine(10, 4, 10, 18)
        p.drawPolygon(QPolygon([QPoint(10, 4), QPoint(17, 6), QPoint(10, 10)]))
    elif name == 'snap':
        p.drawArc(3, 3, 14, 14, 20 * 16, 140 * 16)
        p.drawLine(3, 10, 3, 16)
        p.drawLine(17, 10, 17, 16)
        p.drawLine(2, 16, 6, 16)
        p.drawLine(14, 16, 18, 16)
    elif name == 'fit':
        p.drawRoundedRect(2, 5, 16, 10, 1, 1)
        p.drawLine(5, 10, 15, 10)
        p.drawLine(5, 10, 8, 7)
        p.drawLine(5, 10, 8, 13)
        p.drawLine(15, 10, 12, 7)
        p.drawLine(15, 10, 12, 13)
    elif name == 'volume':
        p.drawPolygon(QPolygon([QPoint(3, 7), QPoint(6, 7), QPoint(10, 4),
                                QPoint(10, 16), QPoint(6, 13), QPoint(3, 13)]))
        p.drawArc(9, 6, 6, 8, -45 * 16, 90 * 16)
        p.drawArc(10, 4, 8, 12, -45 * 16, 90 * 16)
    elif name == 'mute':
        p.drawPolygon(QPolygon([QPoint(3, 7), QPoint(6, 7), QPoint(10, 4),
                                QPoint(10, 16), QPoint(6, 13), QPoint(3, 13)]))
        p.drawLine(13, 7, 17, 13)
        p.drawLine(17, 7, 13, 13)
    elif name == 'fullscreen':
        p.drawLine(3, 7, 3, 3)
        p.drawLine(3, 3, 7, 3)
        p.drawLine(13, 3, 17, 3)
        p.drawLine(17, 3, 17, 7)
        p.drawLine(3, 13, 3, 17)
        p.drawLine(3, 17, 7, 17)
        p.drawLine(13, 17, 17, 17)
        p.drawLine(17, 17, 17, 13)
    elif name == 'list':
        p.drawLine(4, 5, 6, 5)
        p.drawLine(8, 5, 16, 5)
        p.drawLine(4, 10, 6, 10)
        p.drawLine(8, 10, 16, 10)
        p.drawLine(4, 15, 6, 15)
        p.drawLine(8, 15, 16, 15)
    elif name == 'grid':
        p.drawRect(3, 3, 6, 6)
        p.drawRect(11, 3, 6, 6)
        p.drawRect(3, 11, 6, 6)
        p.drawRect(11, 11, 6, 6)
    elif name == 'relink':
        p.drawRoundedRect(3, 7, 6, 6, 2, 2)
        p.drawRoundedRect(11, 7, 6, 6, 2, 2)
        p.drawLine(8, 10, 12, 10)
    p.end()
    pix.setDevicePixelRatio(2)
    return QIcon(pix)


def tool(name, tooltip, callback=None):
    control = QToolButton()
    control.setObjectName('deskTool')
    control.setIcon(icon(name))
    control.setIconSize(QSize(18, 18))
    control.setFixedSize(30, 30)
    control.setToolTip(tooltip)
    control.setAccessibleName(tooltip)
    if callback:
        control.clicked.connect(callback)
    return control


class PanelHeader(QWidget):
    def __init__(self, workspace, key, title):
        super().__init__()
        self.setObjectName('panelHeader')
        self.setToolTip('Drag to rearrange panels · double-click to focus')
        self.workspace, self.key = workspace, key
        row = QHBoxLayout(self)
        row.setContentsMargins(7, 3, 5, 3)
        row.setSpacing(5)
        grip = QLabel()
        grip.setPixmap(icon('grip', '#7e8b94').pixmap(16, 16))
        grip.setAttribute(Qt.WA_TransparentForMouseEvents)
        row.addWidget(grip)
        title_label = QLabel(title)
        title_label.setObjectName('panelTitle')
        title_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        row.addWidget(title_label, 1)
        row.addWidget(tool('focus', 'Focus / restore ' + title, lambda: workspace.focus(key)))
        menu_button = tool('more', title + ' panel options')
        menu = QMenu(menu_button)
        menu.addAction('Focus / restore panel', lambda: workspace.focus(key))
        for label, area in (('Dock left', Qt.LeftDockWidgetArea), ('Dock right', Qt.RightDockWidgetArea),
                            ('Dock below', Qt.BottomDockWidgetArea)):
            menu.addAction(label, lambda checked=False, a=area: workspace.move_panel(key, a))
        menu.addSeparator()
        menu.addAction('Collapse panel', lambda: workspace.hide_panel(key))
        menu_button.setMenu(menu)
        menu_button.setPopupMode(QToolButton.InstantPopup)
        row.addWidget(menu_button)

    def mousePressEvent(self, event):
        event.ignore()

    def mouseMoveEvent(self, event):
        event.ignore()

    def mouseReleaseEvent(self, event):
        event.ignore()

    def mouseDoubleClickEvent(self, event):
        self.workspace.focus(self.key)
        event.accept()


class Workspace(QMainWindow):
    def __init__(self, owner, key):
        super().__init__()
        self.setWindowFlags(Qt.Widget)
        self.setObjectName('modularWorkspace')
        self.owner, self.key = owner, key
        self.panels, self.presets = {}, {}
        self.primary = None
        self.focus_snapshot = None
        self.focused_key = None
        self.setDockOptions(QMainWindow.AllowNestedDocks | QMainWindow.AllowTabbedDocks)
        self.setTabPosition(Qt.AllDockWidgetAreas, QTabWidget.South)
        self.escape_shortcut = QShortcut(QKeySequence('Escape'), self)
        self.escape_shortcut.setContext(Qt.WidgetWithChildrenShortcut)
        self.escape_shortcut.activated.connect(self.restore_focus)

    def add_panel(self, key, title, content):
        dock = QDockWidget(title, self)
        dock.setObjectName(self.key + '.' + key)
        dock.setAllowedAreas(Qt.AllDockWidgetAreas)
        dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetClosable)
        content.setMinimumWidth(0)
        dock.setWidget(content)
        dock.setTitleBarWidget(PanelHeader(self, key, title))
        self.panels[key] = dock
        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
        return dock

    def configure(self, primary, presets):
        self.primary, self.presets = primary, presets
        self.apply_preset(next(iter(presets)), remember=False)
        state = self.store().get('current')
        if state:
            self.restore_serialized(state)

    def store(self):
        return self.owner.state.setdefault('workspace_layouts', {}).setdefault(self.key, {})

    def serialized(self):
        state = self.focus_snapshot if self.focus_snapshot is not None else self.saveState(116)
        return bytes(state.toHex()).decode('ascii')

    def restore_serialized(self, state):
        try:
            return self.restoreState(QByteArray.fromHex(state.encode('ascii')), 116)
        except (ValueError, TypeError, AttributeError):
            return False

    def remember(self):
        self.store()['current'] = self.serialized()
        self.owner.save_timer.start(250)

    def apply_preset(self, name, remember=True):
        self.restore_focus()
        columns = self.presets[name]
        for dock in self.panels.values():
            self.removeDockWidget(dock)
            dock.hide()
        previous, roots = None, []
        for keys, width in columns:
            root = self.panels[keys[0]]
            self.addDockWidget(Qt.LeftDockWidgetArea, root)
            if previous:
                self.splitDockWidget(previous, root, Qt.Horizontal)
            root.show()
            last = root
            for key in keys[1:]:
                dock = self.panels[key]
                self.splitDockWidget(last, dock, Qt.Vertical)
                dock.show()
                last = dock
            if len(keys) > 1:
                self.resizeDocks([self.panels[k] for k in keys], [1] * len(keys), Qt.Vertical)
            roots.append(root)
            previous = root
        self.resizeDocks(roots, [c[1] for c in columns], Qt.Horizontal)
        shown = {key for keys, width in columns for key in keys}
        for key, dock in self.panels.items():
            if key not in shown:
                self.addDockWidget(Qt.RightDockWidgetArea, dock)
                dock.hide()
        if remember:
            self.remember()

    def focus(self, key):
        if self.focused_key == key:
            self.restore_focus()
            return
        self.restore_focus()
        self.focus_snapshot = self.saveState(116)
        self.focused_key = key
        for name, panel in self.panels.items():
            panel.setVisible(name == key)

    def restore_focus(self):
        if self.focus_snapshot is not None:
            self.restoreState(self.focus_snapshot, 116)
        self.focus_snapshot, self.focused_key = None, None

    def show_panel(self, key):
        self.restore_focus()
        if self.dockWidgetArea(self.panels[key]) == Qt.NoDockWidgetArea:
            self.addDockWidget(Qt.RightDockWidgetArea, self.panels[key])
        self.panels[key].show()
        self.panels[key].raise_()

    def hide_panel(self, key):
        self.restore_focus()
        if sum(not p.isHidden() for p in self.panels.values()) <= 1:
            return
        self.panels[key].hide()
        self.remember()

    def move_panel(self, key, area):
        self.restore_focus()
        self.addDockWidget(area, self.panels[key])
        self.panels[key].show()
        self.remember()

    def save_named(self):
        name, ok = QInputDialog.getText(self, 'Save layout', 'Layout name:')
        if ok and name.strip():
            self.store().setdefault('saved', {})[name.strip()[:60]] = self.serialized()
            self.remember()

    def restore_named(self, name):
        self.restore_focus()
        self.restore_serialized(self.store()['saved'][name])
        self.remember()

    def layout_menu(self, menu):
        menu.clear()
        for name in self.presets:
            menu.addAction(name, lambda checked=False, n=name: self.apply_preset(n))
        menu.addSeparator()
        panels = menu.addMenu('Panels')
        for key, dock in self.panels.items():
            action = panels.addAction(dock.windowTitle())
            action.setCheckable(True)
            action.setChecked(not dock.isHidden())
            action.triggered.connect(lambda checked, k=key: self.show_panel(k) if checked else self.hide_panel(k))
        menu.addAction('Save layout…', self.save_named)
        saved = menu.addMenu('Restore saved layout')
        for name in self.store().get('saved', {}):
            saved.addAction(name, lambda checked=False, n=name: self.restore_named(n))
        saved.setEnabled(bool(self.store().get('saved')))
        menu.addSeparator()
        menu.addAction('Reset this workspace', lambda: self.apply_preset(next(iter(self.presets))))


class WorkspaceBar(QWidget):
    def __init__(self, workspace, title, modes=()):
        super().__init__()
        self.setObjectName('workspaceBar')
        self.workspace = workspace
        self.row = QHBoxLayout(self)
        self.row.setContentsMargins(4, 0, 4, 0)
        self.row.setSpacing(6)
        self.mode_buttons = {}
        if modes:
            for name, callback in modes:
                b = QToolButton()
                b.setText(name)
                b.setObjectName('workspaceMode')
                b.setCheckable(True)
                b.setChecked(name == modes[0][0])
                b.setMinimumSize(66, 38)
                b.clicked.connect(callback)
                self.row.addWidget(b)
                self.mode_buttons[name] = b
        else:
            heading = QLabel(title)
            heading.setObjectName('workspaceTitle')
            self.row.addWidget(heading)
        self.row.addStretch()
        self.notice = QLabel('')
        self.notice.setObjectName('subtle')
        self.row.addWidget(self.notice)
        layout = QToolButton()
        layout.setText('Layout')
        layout.setObjectName('layoutButton')
        layout.setIcon(icon('balanced'))
        layout.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        layout.setPopupMode(QToolButton.InstantPopup)
        menu = QMenu(layout)
        menu.aboutToShow.connect(lambda: workspace.layout_menu(menu))
        layout.setMenu(menu)
        self.row.addWidget(layout)
        for name, preset in zip(('balanced', 'left', 'right'), workspace.presets):
            self.row.addWidget(tool(name, preset, lambda checked=False, n=preset: workspace.apply_preset(n)))
        self.row.addWidget(tool('expand', 'Full screen · F11', self.fullscreen))

    def select_mode(self, mode):
        for name, button in self.mode_buttons.items():
            button.setChecked(name == mode)

    def fullscreen(self):
        win = self.window()
        win.showNormal() if win.isFullScreen() else win.showFullScreen()
