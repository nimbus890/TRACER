"""Isolated 1.22 journey checks and screenshots for Tracer 1.22."""
import copy
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

# Ensure 1.22 modules are imported first
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import core
import paper_edit
import paper_sync
import release121
import timeline
import timeline_tools
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtTest import QTest
import app
from transcape import Transcape


def main():
    output = HERE / 'verification' / '1.22'
    output.mkdir(parents=True, exist_ok=True)
    qt = QApplication.instance() or QApplication([])
    qt.setStyle('Fusion')
    app.configure_fonts()
    qt.setStyleSheet(app.STYLE)

    with tempfile.TemporaryDirectory() as temporary, patch.object(core, 'DATA', Path(temporary)), patch.object(app.Window, 'first_setup', lambda self: None):
        state = dict(folders=[], projects=[], collections=[], settings=core.DEFAULTS.copy(), results=[], schema_version=121)
        state['settings']['beta_features'] = True
        for i, name in enumerate(['River interview', 'Morning boats', 'Market walk', 'Crossing', 'Village archive', 'Evening river']):
            state['results'].append({
                'id': str(i), 'source': str(Path(temporary) / (name + '.mp4')), 'duration': 30 + i * 12,
                'output': temporary, 'frames': [], 'segments': [
                    {'start': 0, 'end': 4, 'text': 'The river was the center of our lives. We crossed it every morning.'},
                    {'start': 4, 'end': 9, 'text': 'People gathered here with their boats and shared stories of the village.'},
                    {'start': 9, 'end': 14, 'text': 'Now the water has changed, but the memory remains with us.'}],
                'visual_index': {'frames': [{'time': 4, 'search_words': ['boat', 'person', 'water'],
                    'detections': [{'label': 'boat', 'confidence': .87, 'layer': 'foreground'}]}]}})

        c = core.create_collection(state, 'River Stories')
        release121.migrate(state)
        release121.attach(state, c['id'], state['results'][:4])

        with patch.object(core, 'load_state', lambda: state):
            win = app.Window()
        win.show()

        def settle():
            for _ in range(15):
                qt.processEvents()

        def shot(name, index, size=(1440, 900)):
            win.resize(*size)
            win.navigate(index)
            settle()
            assert win.width() <= size[0], (name, win.width(), size[0])
            win.grab().save(str(output / (name + '.png')))

        # 1. Queue & Library
        shot('queue', 0)
        shot('library', 1)
        assert win.results.export_project_btn.isHidden()

        # 2. Add to Collection
        win.results.checked_ids = {'0', '1'}
        win.results.refresh_preview_project_combo()
        win.results.preview_project_combo.setCurrentIndex(win.results.preview_project_combo.findData(c['id']))
        win.results.on_add_to_collection()
        win.select_collection(c['id'])
        settle()
        assert win.pages.currentIndex() == 5 and not win.nav[1].isChecked()
        assert win.collection_page.add_to_collection_btn.isHidden()
        shot('collection', 5)
        shot('library-narrow', 1, (1100, 720))

        # 3. Paper Edit linked-sequence behavior
        win.select_collection(c['id'])
        win.collection_page.open_collection_editor('paper')
        settle()
        paper = win.paper_edit_page
        editor = paper.paper.editor

        # Test manuscript editing & status line
        editor.selectAll()
        editor.insertPlainText('The river tells our story.')
        settle()
        paper.paper.flush_commit()
        paper.sync_pending_documents()
        assert 'sequence_id' in paper.document
        assert paper.document['segments'][0]['text'] == 'The river tells our story.'
        assert paper.document['segments'][0]['id'] == paper.document['segments'][0]['passage_id']
        assert 'Linked' in paper.paper.status_line.text()

        editor.undo()
        settle()
        paper.paper.flush_commit()
        paper.sync_pending_documents()
        shot('paper', 2)
        shot('paper-narrow', 2, (1100, 720))

        # 4. Storyline symbol-led tool suite
        paper.open_storyline()
        settle()
        story = win.projects_page
        seq = story.active_sequence()
        assert seq['id'] == paper.document['sequence_id']
        assert len(story.tool_buttons) == 6
        for tool_key in ('select', 'track_select', 'ripple', 'razor', 'hand', 'zoom'):
            assert tool_key in story.tool_buttons
            assert story.tool_buttons[tool_key].text() == ''
            assert not story.tool_buttons[tool_key].icon().isNull()

        # Playhead & Seek
        story.timeline_canvas.set_playhead(2, notify=True)
        assert story.source_seek.value() == 2000
        story.source_seek.sliderMoved.emit(3000)
        assert story.timeline_canvas.playhead == 3

        # Test Razor Tool (C)
        story.select_timeline_tool('razor')
        assert story.timeline_canvas.tool == 'razor'
        before = len(seq['tracks'][1]['clips'])
        x = round(timeline.TRACK_HEADER + 2 * story.timeline_canvas.pixels_per_second)
        QTest.mouseClick(story.timeline_canvas, Qt.LeftButton, pos=QPoint(x, timeline.RULER_HEIGHT + timeline.TRACK_HEIGHT + 20))
        assert len(seq['tracks'][1]['clips']) == before + 1

        story.sequence_command('undo')
        assert len(story.active_sequence()['tracks'][1]['clips']) == before

        # Test Ripple Edit Tool (B)
        story.select_timeline_tool('ripple')
        assert story.timeline_canvas.tool == 'ripple'

        # Test Track Select Forward Tool (A)
        story.select_timeline_tool('track_select')
        assert story.timeline_canvas.tool == 'track_select'

        # Return to Selection (V)
        story.select_timeline_tool('select')
        assert story.timeline_canvas.tool == 'select'

        shot('storyline', 3)
        shot('storyline-narrow', 3, (1100, 720))

        # 5. Transcape
        field = Transcape(state, win)
        field.resize(1440, 900)
        field.field.motion = False
        field.show()
        settle()
        field.grab().save(str(output / 'transcape.png'))
        field.close()

        # 6. Empty State
        state['results'] = []
        win.results.set_records([])
        shot('library-empty', 1)

        for task in list(win.tasks):
            task.wait(10000)
        settle()
        win.close()
        settle()
        field.deleteLater()
        win.deleteLater()
        QTimer.singleShot(100, qt.quit)

    print('1.22 journey checks passed. Screenshots: ' + str(output))


if __name__ == '__main__':
    main()
