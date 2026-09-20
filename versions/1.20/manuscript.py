"""Continuous manuscript with persistent source provenance in text formats."""
import copy
import uuid
import json
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QTextCursor, QTextCharFormat, QTextFormat, QFont
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextEdit, QMenu
import paper_edit

SOURCE_ID = int(QTextFormat.UserProperty) + 120


class ManuscriptEditor(QTextEdit):
    def insertPlainText(self, text):
        cursor = self.textCursor()
        start = QTextCursor(self.document())
        start.setPosition(cursor.selectionStart())
        start.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
        cursor.insertText(text, start.charFormat())
        self.setTextCursor(cursor)

    def keyPressEvent(self, event):
        if event.text() and event.text().isprintable() and not event.modifiers() & (Qt.ControlModifier | Qt.MetaModifier):
            self.insertPlainText(event.text())
        else:
            super().keyPressEvent(event)

    def createMimeDataFromSelection(self):
        mime = super().createMimeDataFromSelection()
        selection = self.textCursor()
        parts = []
        cursor = QTextCursor(self.document())
        for position in range(selection.selectionStart(), selection.selectionEnd()):
            cursor.setPosition(position)
            cursor.movePosition(QTextCursor.NextCharacter, QTextCursor.KeepAnchor)
            sid = cursor.charFormat().property(SOURCE_ID)
            text = cursor.selectedText().replace('\u2029', '\n')
            if parts and parts[-1][0] == sid:
                parts[-1][1] += text
            else:
                parts.append([sid, text])
        mime.setData('application/x-tracer-passages', json.dumps(parts).encode('utf-8'))
        return mime

    def insertFromMimeData(self, mime):
        if mime.hasFormat('application/x-tracer-passages'):
            parts = json.loads(bytes(mime.data('application/x-tracer-passages')))
            cursor = self.textCursor()
            cursor.beginEditBlock()
            for sid, text in parts:
                fmt = QTextCharFormat()
                if sid:
                    fmt.setProperty(SOURCE_ID, sid)
                cursor.insertText(text, fmt)
            cursor.endEditBlock()
            self.setTextCursor(cursor)
        else:
            self.insertPlainText(mime.text())


class Manuscript(QWidget):
    changed = Signal()
    seekRequested = Signal(float)

    def __init__(self, ink_factory, parent=None):
        super().__init__(parent)
        self.document = None
        self.loading = False
        self.rows = []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        self.title = QLabel('Start with a transcript')
        self.title.setStyleSheet('font-size: 22px; font-weight: 600;')
        layout.addWidget(self.title)
        self.editor = ManuscriptEditor()
        self.editor.setAcceptRichText(False)
        self.editor.setPlaceholderText('Add footage to begin writing. Your words keep their source timing.')
        self.editor.setStyleSheet('QTextEdit { background: #141414; border: 0; color: #eeeeec; padding: 18px; font-family: Georgia; font-size: 18px; selection-background-color: #31545a; }')
        self.editor.setContextMenuPolicy(Qt.CustomContextMenu)
        self.editor.customContextMenuRequested.connect(self.context_menu)
        self.editor.textChanged.connect(self.commit)
        layout.addWidget(self.editor, 1)
        self.hint = QLabel('Edit normally • delete passages to exclude them • Ctrl+Z to undo')
        self.hint.setWordWrap(True)
        self.hint.setStyleSheet('color: #999999; font-size: 11px;')
        layout.addWidget(self.hint)
        self.ink = ink_factory(self)
        self.ink.changed.connect(self.changed)

    def set_document(self, document):
        self.loading = True
        self.document = document
        self.editor.clear()
        self.title.setText(document.get('title', 'Manuscript') if document else 'Start with a transcript')
        self.editor.setEnabled(document is not None)
        if document:
            cursor = self.editor.textCursor()
            for index, segment in enumerate(paper_edit.ordered_segments(document, True)):
                if index:
                    cursor.insertBlock()
                fmt = QTextCharFormat()
                fmt.setProperty(SOURCE_ID, segment['id'])
                cursor.insertText(segment.get('text', ''), fmt)
                block = cursor.blockFormat()
                block.setBottomMargin(14)
                block.setLineHeight(150, 1)
                cursor.setBlockFormat(block)
            self.editor.document().clearUndoRedoStacks()
        self.ink.set_document(document)
        self.loading = False
        QTimer.singleShot(0, self.fit_ink)

    def commit(self):
        if self.loading or self.document is None:
            return
        known = {s['id']: s for s in self.document['segments']}
        runs = []
        block = self.editor.document().begin()
        previous = next(iter(known), None)
        while block.isValid():
            it = block.begin()
            while not it.atEnd():
                fragment = it.fragment()
                sid = fragment.charFormat().property(SOURCE_ID) or previous
                if sid in known:
                    if runs and runs[-1][0] == sid:
                        runs[-1][1] += fragment.text()
                    else:
                        runs.append([sid, fragment.text()])
                    previous = sid
                it += 1
            if runs:
                runs[-1][1] += '\n'
            block = block.next()
        for segment in known.values():
            segment['included'] = False
        order, used = [], set()
        for sid, text in runs:
            if not text.strip():
                continue
            segment = known[sid]
            if sid in used:
                segment = copy.deepcopy(segment)
                segment['id'] = uuid.uuid4().hex
                self.document['segments'].append(segment)
            segment.update(text=text.strip(), included=True)
            order.append(segment['id'])
            used.add(sid)
        self.document['order'] = order + [s['id'] for s in self.document['segments'] if s['id'] not in order]
        self.changed.emit()

    def context_menu(self, point):
        menu = self.editor.createStandardContextMenu()
        cursor = self.editor.cursorForPosition(point)
        sid = cursor.charFormat().property(SOURCE_ID)
        segment = next((s for s in (self.document or {}).get('segments', []) if s['id'] == sid), None)
        if segment:
            menu.addSeparator()
            menu.addAction('Play this source passage', lambda: self.seekRequested.emit(float(segment.get('start', 0))))
            detail = menu.addAction(f"Source {segment.get('start', 0):.2f}–{segment.get('end', 0):.2f}s · {segment.get('speaker') or 'No speaker label'}")
            detail.setEnabled(False)
        menu.exec(self.editor.mapToGlobal(point))

    def apply_search(self, query):
        selections = []
        if query:
            cursor = self.editor.document().find(query)
            while not cursor.isNull():
                selection = QTextEdit.ExtraSelection()
                selection.cursor = cursor
                selection.format.setBackground(QColor('#655124'))
                selections.append(selection)
                cursor = self.editor.document().find(query, cursor)
        self.editor.setExtraSelections(selections)

    def fit_ink(self):
        self.ink.setGeometry(self.rect())
        self.ink.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fit_ink()
