"""Continuous manuscript with persistent source provenance in text formats.
Updated for Tracer 1.21 with debounced sync, hover/focus passage feedback,
quiet timing badge, trimming, splitting, and Storyline sync status.
"""
from __future__ import annotations

import copy
import json
import uuid

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor, QTextCursor, QTextCharFormat, QTextFormat, QFont
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
                             QMenu, QDialog, QDoubleSpinBox, QDialogButtonBox, QPushButton)

import paper_edit
import paper_sync

SOURCE_ID = int(QTextFormat.UserProperty) + 120


class ManuscriptEditor(QTextEdit):
    splitRequested = Signal()

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

        # The document model updates immediately so switching sources cannot lose
        # a keystroke. PaperEditPage separately debounces the expensive sequence sync.
        self._commit_timer = QTimer(self)
        self._commit_timer.setSingleShot(True)
        self._commit_timer.setInterval(350)
        self._commit_timer.timeout.connect(self._do_commit)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 20, 28, 20)
        layout.setSpacing(6)

        # Header: Title + subtle status line
        hdr = QHBoxLayout()
        self.title = QLabel('Start with a transcript')
        self.title.setStyleSheet('font-size: 22px; font-weight: 600; color: #ededed;')
        hdr.addWidget(self.title)
        hdr.addStretch()

        self.status_line = QLabel('Not linked · 0 passages · 00:00')
        self.status_line.setStyleSheet('color: #7d9ba6; font-size: 11px; font-weight: 500;')
        hdr.addWidget(self.status_line)
        layout.addLayout(hdr)

        # Active passage info badge (revealed quietly on cursor move)
        self.badge_row = QHBoxLayout()
        self.passage_badge = QLabel('')
        self.passage_badge.setStyleSheet('color: #e59a59; font-size: 11px; font-weight: 600;')
        self.badge_row.addWidget(self.passage_badge)

        self.preview_btn = QPushButton('▶ Play source')
        self.preview_btn.setFixedHeight(22)
        self.preview_btn.setStyleSheet('QPushButton { background: #26292b; color: #d0d7de; border: 1px solid #3d444d; border-radius: 3px; font-size: 11px; padding: 2px 8px; } QPushButton:hover { background: #32383f; }')
        self.preview_btn.clicked.connect(self.play_active_passage)
        self.preview_btn.hide()
        self.badge_row.addWidget(self.preview_btn)

        self.trim_btn = QPushButton('Trim…')
        self.trim_btn.setFixedHeight(22)
        self.trim_btn.setStyleSheet('QPushButton { background: #26292b; color: #d0d7de; border: 1px solid #3d444d; border-radius: 3px; font-size: 11px; padding: 2px 8px; } QPushButton:hover { background: #32383f; }')
        self.trim_btn.clicked.connect(self.trim_active_passage)
        self.trim_btn.hide()
        self.badge_row.addWidget(self.trim_btn)

        self.badge_row.addStretch()
        layout.addLayout(self.badge_row)

        self.editor = ManuscriptEditor()
        self.editor.setAcceptRichText(False)
        self.editor.setPlaceholderText('Add footage to begin writing. Your words keep their source timing.')
        self.editor.setToolTip('Write normally. Right-click a sourced passage for preview and timing actions.')
        self.editor.setStyleSheet('QTextEdit { background: #141414; border: 0; color: #eeeeec; padding: 18px; font-family: Georgia; font-size: 18px; selection-background-color: #31545a; }')
        self.editor.setContextMenuPolicy(Qt.CustomContextMenu)
        self.editor.customContextMenuRequested.connect(self.context_menu)
        self.editor.textChanged.connect(self.schedule_commit)
        self.editor.cursorPositionChanged.connect(self.update_active_passage_badge)
        layout.addWidget(self.editor, 1)

        self.hint = QLabel('')
        self.hint.hide()

        self.ink = ink_factory(self)
        self.ink.changed.connect(self.changed)

    def set_document(self, document):
        self.loading = True
        self.document = document
        self.editor.clear()
        self.title.setText(document.get('title', 'Manuscript') if document else 'Start with a transcript')
        self.editor.setEnabled(document is not None)
        if document:
            paper_sync.ensure_passage_model(document)
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
            self.status_line.setText(paper_sync.status_badge_text(document))
        else:
            self.status_line.setText('Not linked · 0 passages · 00:00')
            self.passage_badge.setText('')
            self.preview_btn.hide()
            self.trim_btn.hide()

        self.ink.set_document(document)
        self.loading = False
        QTimer.singleShot(0, self.fit_ink)

    def schedule_commit(self):
        if self.loading or self.document is None:
            return
        self._do_commit()

    def flush_commit(self):
        if self._commit_timer.isActive():
            self._commit_timer.stop()
            self._do_commit()

    def commit(self):
        self._do_commit()

    def _do_commit(self):
        if self.loading or self.document is None:
            return
        paper_sync.ensure_passage_model(self.document)
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
                segment['passage_id'] = segment['id']
                self.document['segments'].append(segment)
            segment.update(text=text.strip(), included=True)
            order.append(segment['id'])
            used.add(sid)

        self.document['order'] = order + [s['id'] for s in self.document['segments'] if s['id'] not in order]
        self.status_line.setText(paper_sync.status_badge_text(self.document))
        self.changed.emit()

    def active_passage(self):
        cursor = self.editor.textCursor()
        sid = cursor.charFormat().property(SOURCE_ID)
        if not sid and self.document:
            block = cursor.block()
            it = block.begin()
            if not it.atEnd():
                sid = it.fragment().charFormat().property(SOURCE_ID)
        return next((s for s in (self.document or {}).get('segments', []) if s['id'] == sid), None)

    def update_active_passage_badge(self):
        passage = self.active_passage()
        if passage:
            start = float(passage.get('start', 0.0))
            end = float(passage.get('end', start))
            dur = max(0.0, end - start)
            quality = passage.get('timing_quality', 'source').capitalize()
            spk = passage.get('speaker', '').strip()
            spk_str = f" · {spk}" if spk else ""
            def clock(value):
                minutes, seconds = divmod(max(0, int(round(value))), 60)
                return f'{minutes:02d}:{seconds:02d}'
            self.passage_badge.setText(f"{clock(start)}–{clock(end)} · {dur:.1f}s · {quality}{spk_str}")
            self.preview_btn.show()
            self.trim_btn.show()
        else:
            self.passage_badge.setText('')
            self.preview_btn.hide()
            self.trim_btn.hide()

    def play_active_passage(self):
        passage = self.active_passage()
        if passage:
            self.seekRequested.emit(float(passage.get('start', 0.0)))

    def trim_active_passage(self):
        passage = self.active_passage()
        if not passage:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Trim Passage · {passage.get('speaker') or 'Passage'}")
        vl = QVBoxLayout(dlg)
        vl.setSpacing(10)

        info = QLabel(f"Source duration: {float(passage.get('original_end', passage['end'])) - float(passage.get('original_start', passage['start'])):.2f}s")
        info.setStyleSheet('color: #aaa; font-size: 11px;')
        vl.addWidget(info)

        row_in = QHBoxLayout()
        row_in.addWidget(QLabel('In (start sec):'))
        spin_in = QDoubleSpinBox()
        spin_in.setRange(0.0, 99999.0)
        spin_in.setSingleStep(0.1)
        spin_in.setValue(float(passage.get('start', 0.0)))
        row_in.addWidget(spin_in)
        vl.addLayout(row_in)

        row_out = QHBoxLayout()
        row_out.addWidget(QLabel('Out (end sec):'))
        spin_out = QDoubleSpinBox()
        spin_out.setRange(0.0, 99999.0)
        spin_out.setSingleStep(0.1)
        spin_out.setValue(float(passage.get('end', 0.0)))
        row_out.addWidget(spin_out)
        vl.addLayout(row_out)

        btn_reset = QPushButton('Reset to Transcript Original')
        btn_reset.clicked.connect(lambda: (
            spin_in.setValue(float(passage.get('original_start', passage['start']))),
            spin_out.setValue(float(passage.get('original_end', passage['end'])))
        ))
        vl.addWidget(btn_reset)

        box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        box.accepted.connect(dlg.accept)
        box.rejected.connect(dlg.reject)
        vl.addWidget(box)

        if dlg.exec() == QDialog.Accepted:
            new_in = round(spin_in.value(), 3)
            new_out = round(max(new_in + 0.04, spin_out.value()), 3)
            passage['start'] = new_in
            passage['end'] = new_out
            passage['source_in'] = new_in
            passage['source_out'] = new_out
            passage['timing_quality'] = 'manual'
            self.update_active_passage_badge()
            self._do_commit()

    def split_passage_at_cursor(self):
        cursor = self.editor.textCursor()
        passage = self.active_passage()
        if not passage or cursor.hasSelection():
            return
        # Calculate ratio of cursor within current block text
        block = cursor.block()
        pos_in_block = cursor.positionInBlock()
        total_len = max(1, len(block.text()))
        ratio = pos_in_block / total_len
        if not (0.05 <= ratio <= 0.95):
            return

        p1, p2 = paper_sync.estimate_split_timing(passage, ratio)
        idx = self.document['segments'].index(passage)
        self.document['segments'][idx] = p1
        self.document['segments'].insert(idx + 1, p2)

        # Update order
        if passage['id'] in self.document['order']:
            oidx = self.document['order'].index(passage['id'])
            self.document['order'].insert(oidx + 1, p2['id'])
        else:
            self.document['order'].append(p2['id'])

        # Split text visually
        text1 = block.text()[:pos_in_block].strip()
        text2 = block.text()[pos_in_block:].strip()
        p1['text'] = text1
        p2['text'] = text2

        # Re-set document to refresh blocks cleanly
        self.set_document(self.document)
        self._do_commit()

    def context_menu(self, point):
        menu = self.editor.createStandardContextMenu()
        cursor = self.editor.cursorForPosition(point)
        sid = cursor.charFormat().property(SOURCE_ID)
        segment = next((s for s in (self.document or {}).get('segments', []) if s['id'] == sid), None)
        if segment:
            menu.addSeparator()
            menu.addAction('▶ Play this source passage', lambda: self.seekRequested.emit(float(segment.get('start', 0))))
            menu.addAction('⏱ Trim passage in/out…', self.trim_active_passage)
            menu.addAction('✂ Split passage at caret', self.split_passage_at_cursor)
            status_text = f"Source: {segment.get('start', 0):.2f}–{segment.get('end', 0):.2f}s · {segment.get('timing_quality', 'source').capitalize()}"
            detail = menu.addAction(status_text)
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
