"""Tracer 1.21 Storyline Timeline Tools and Shortcut Controller.

Implements the Premiere-style 6-tool dock:
- Selection (V)
- Track Select Forward (A)
- Ripple Edit (B)
- Razor (C)
- Hand (H)
- Zoom (Z)

Along with editing commands, text-focus shortcut guards, and cursor management.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import (QApplication, QLineEdit, QTextEdit,
                             QPlainTextEdit, QAbstractSpinBox, QComboBox)

TOOL_SHORTCUTS = {
    'select': 'V',
    'track_select': 'A',
    'ripple': 'B',
    'razor': 'C',
    'hand': 'H',
    'zoom': 'Z',
}

TOOL_NAMES = {
    'select': 'Selection (V)',
    'track_select': 'Track Select Forward (A)',
    'ripple': 'Ripple Edit (B)',
    'razor': 'Razor Tool (C)',
    'hand': 'Hand Tool (H)',
    'zoom': 'Zoom Tool (Z)',
}

TOOL_CURSORS = {
    'select': Qt.ArrowCursor,
    'track_select': Qt.SizeHorCursor,
    'ripple': Qt.SplitHCursor,
    'razor': Qt.CrossCursor,
    'hand': Qt.OpenHandCursor,
    'zoom': Qt.PointingHandCursor,
}


def is_text_editing_focused() -> bool:
    """Return True if any text input widget currently holds keyboard focus."""
    widget = QApplication.focusWidget()
    if widget is None:
        return False
    return isinstance(widget, (QLineEdit, QTextEdit, QPlainTextEdit, QAbstractSpinBox, QComboBox))


class TimelineToolController(QObject):
    toolChanged = Signal(str)
    commandTriggered = Signal(str)

    def __init__(self, canvas, parent=None):
        super().__init__(parent)
        self.canvas = canvas
        self.active_tool = 'select'

    def select_tool(self, name: str):
        if name not in TOOL_NAMES:
            name = 'select'
        self.active_tool = name
        cursor = TOOL_CURSORS.get(name, Qt.ArrowCursor)
        self.canvas.setCursor(cursor)
        self.canvas.tool = name
        self.toolChanged.emit(name)

    def handle_key_press(self, event) -> bool:
        """Handle timeline keyboard shortcut. Returns True if consumed."""
        if is_text_editing_focused():
            return False

        key = event.key()
        modifiers = event.modifiers()

        # Single-key tool switches (no modifiers)
        if modifiers == Qt.NoModifier:
            if key == Qt.Key_V:
                self.select_tool('select')
                return True
            elif key == Qt.Key_A:
                self.select_tool('track_select')
                return True
            elif key == Qt.Key_B:
                self.select_tool('ripple')
                return True
            elif key == Qt.Key_C:
                self.select_tool('razor')
                return True
            elif key == Qt.Key_H:
                self.select_tool('hand')
                return True
            elif key == Qt.Key_Z:
                self.select_tool('zoom')
                return True
            elif key == Qt.Key_Space:
                self.commandTriggered.emit('play_pause')
                return True
            elif key == Qt.Key_Left:
                self.commandTriggered.emit('prev_frame')
                return True
            elif key == Qt.Key_Right:
                self.commandTriggered.emit('next_frame')
                return True
            elif key == Qt.Key_Up:
                self.commandTriggered.emit('prev_edit')
                return True
            elif key == Qt.Key_Down:
                self.commandTriggered.emit('next_edit')
                return True
            elif key == Qt.Key_Delete or key == Qt.Key_Backspace:
                self.commandTriggered.emit('delete')
                return True
            elif key in (Qt.Key_Equal, Qt.Key_Plus):
                self.commandTriggered.emit('zoom_in')
                return True
            elif key in (Qt.Key_Minus, Qt.Key_Underscore):
                self.commandTriggered.emit('zoom_out')
                return True
            elif key == Qt.Key_Backslash:
                self.commandTriggered.emit('fit')
                return True

        # Modified commands
        if modifiers == (Qt.ControlModifier | Qt.ShiftModifier):
            if key == Qt.Key_Z:
                self.commandTriggered.emit('redo')
                return True

        if modifiers == Qt.ShiftModifier:
            if key in (Qt.Key_Delete, Qt.Key_Backspace):
                self.commandTriggered.emit('ripple_delete')
                return True

        if modifiers == Qt.ControlModifier:
            if key == Qt.Key_K:
                self.commandTriggered.emit('add_edit')
                return True
            elif key == Qt.Key_Z:
                self.commandTriggered.emit('undo')
                return True
            elif key == Qt.Key_Y:
                self.commandTriggered.emit('redo')
                return True
            elif key == Qt.Key_C:
                self.commandTriggered.emit('copy')
                return True
            elif key == Qt.Key_V:
                self.commandTriggered.emit('paste')
                return True
            elif key == Qt.Key_X:
                self.commandTriggered.emit('cut')
                return True

        return False
