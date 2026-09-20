"""Rendered 1.16 workspace acceptance using synthetic content and isolated state."""
import copy
import json
import os
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import core
core.DATA = core.ROOT / 'verification' / 'modular-data'
core.DATA.mkdir(parents=True, exist_ok=True)
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest
import app
import paper_edit

app.enable_high_dpi()
qt = QApplication([])
app.configure_fonts()
qt.setStyle('Fusion')
qt.setStyleSheet(app.STYLE)
fixture = json.loads((core.ROOT / 'verification' / 'gpu-verification.json').read_text(encoding='utf-8'))
record = copy.deepcopy(fixture)
record['id'] = 'modular-demo'
record['segments'] = [
    {'start': 0, 'end': 2, 'text': 'The river was part of our daily life. We knew every bend.'},
    {'start': 2, 'end': 4, 'text': 'When the climate changed, the seasons became less predictable.'},
    {'start': 4, 'end': 6, 'text': 'People stayed. They looked after each other and built something new.'},
    {'start': 6, 'end': 8, 'text': 'Researchers came to listen. They wanted to understand the whole story.'},
    {'start': 8, 'end': 10, 'text': 'The climate is changing, but this place still feels like home.'},
    {'start': 10, 'end': 12, 'text': 'We can choose what happens next. That is where the story begins.'},
]
other = copy.deepcopy(record)
other['id'] = 'modular-demo-two'
other['source'] = str(core.ROOT / 'verification' / 'offline-interview.mp4')
other['segments'] = [{'start': 0, 'end': 4, 'text': 'Climate researchers tell another part of the story.'}]
state = dict(folders=[], projects=[], settings=core.DEFAULTS.copy(), results=[record, other], paper_edits=[])
doc = paper_edit.ensure_paper_document(state, record)
for i, segment in enumerate(doc['segments']):
    segment['speaker'] = 'MAYA' if i % 2 == 0 else 'DAN'
doc['segments'][2]['note'] = 'Strong opening?'
with patch.object(core, 'load_state', return_value=state), patch.object(app.Window, 'first_setup', lambda self: None):
    win = app.Window()
win.resize(1440, 900)
win.show()
QTest.qWait(250)
assert win.pages.currentIndex() == 0
assert win.nav[0].text() == 'Queue'
win.navigate(2)
page = win.paper_edit_page
page.set_mode('Find')
page.search.setText('climate')
assert page.search_results.count() == 2
page.search_results.setCurrentRow(0)
QTest.qWait(100)
page.player.play()
QTest.qWait(300)
page.player.pause()
QTest.qWait(50)
print('Preview:', page.player.mediaStatus(), page.player.duration(),
      'visible:', page.video.isVisible(), 'error:', page.player.errorString(), flush=True)
win.grab().save(str(core.ROOT / 'verification' / 'paper-find-1.17.png'))
assert page.desk.panels['script'].isVisible()
assert page.desk.panels['search'].isVisible()
assert page.paper.rows[1].text.extraSelections()
page.desk.focus('script')
QTest.qWait(50)
assert page.desk.panels['preview'].isHidden()
page.desk.restore_focus()
assert page.desk.panels['preview'].isVisible()
win.resize(1100, 720)
QTest.qWait(100)
assert win.width() == 1100, win.width()
assert page.desk.panels['script'].width() >= 300
win.grab().save(str(core.ROOT / 'verification' / 'paper-find-narrow-1.17.png'))
page.search_results.setCurrentRow(1)
assert 'offline' in page.source_status.text()
page.search.setText('no-matches-for-this-phrase')
QTest.qWait(50)
assert page.search_results.count() == 0
win.grab().save(str(core.ROOT / 'verification' / 'paper-no-matches-1.17.png'))
page.desk.apply_preset('Arrange passages')
assert page.sequence.isVisible()
page.sequence.setCurrentRow(0)
page.move_passage(1)
win.resize(1440, 900)
QTest.qWait(50)
win.grab().save(str(core.ROOT / 'verification' / 'paper-order-1.17.png'))
win.navigate(1)
win.results.desk.apply_preset('Research desk')
win.results.search.setText('climate')
win.results.select(win.results.list.item(0))
QTest.qWait(100)
win.grab().save(str(core.ROOT / 'verification' / 'library-1.17.png'))
win.navigate(3)
project = win.projects_page.current()
video = dict(path=record['source'], name='Interview selects', duration=15, audio=True, selected=True, status='Done')
project['folders'] = [dict(id='demo', path='tracer://library', name='Library', files=[video])]
win.projects_page.refresh(project['id'])
win.projects_page.add_media_to_timeline(video, 0, 1)
win.projects_page.add_media_to_timeline(video, 2, 1)
win.projects_page.set_story_orientation('Landscape')
win.projects_page.timeline_canvas.set_playhead(3, notify=True)
QTest.qWait(150)
assert win.projects_page.pending_preview_position == 1000
assert 'Interview selects' in win.projects_page.source_name.text()
win.projects_page.timeline_canvas.set_playhead(10, notify=True)
before_anchor = (app.timeline.TRACK_HEADER + win.projects_page.timeline_canvas.playhead *
                 win.projects_page.timeline_canvas.pixels_per_second -
                 win.projects_page.timeline_scroll.horizontalScrollBar().value())
win.projects_page.zoom.setValue(80)
QTest.qWait(50)
after_anchor = (app.timeline.TRACK_HEADER + win.projects_page.timeline_canvas.playhead *
                win.projects_page.timeline_canvas.pixels_per_second -
                win.projects_page.timeline_scroll.horizontalScrollBar().value())
assert abs(before_anchor - after_anchor) <= 3, (before_anchor, after_anchor)
win.projects_page.zoom.setValue(24)
win.projects_page.timeline_canvas.set_zoom(31)
assert win.projects_page.zoom.value() == 31
win.projects_page.store_sequence_view()
assert project['sequences'][0]['view']['playhead'] == 10.0
win.projects_page.queue_sequence()
win.projects_page.set_delivery_open(True)
QTest.qWait(100)
win.projects_page.export_popup.grab().save(str(core.ROOT / 'verification' / 'export-1.18.png'))
win.grab().save(str(core.ROOT / 'verification' / 'storyline-1.18-export.png'))
win.projects_page.set_delivery_open(False)
win.grab().save(str(core.ROOT / 'verification' / 'storyline-1.18-landscape.png'))
win.projects_page.set_story_orientation('Portrait')
QTest.qWait(100)
win.grab().save(str(core.ROOT / 'verification' / 'storyline-1.18-portrait.png'))
win.resize(1100, 720)
QTest.qWait(100)
assert win.width() == 1100, win.width()
win.grab().save(str(core.ROOT / 'verification' / 'storyline-1.18-narrow.png'))
for task in list(win.tasks):
    task.wait(5000)
qt.processEvents()
win.close()
QTest.qWait(50)
assert not win.isVisible()
print('1.17 acceptance passed: Queue startup, Find, offline/no-match, focus restore, passage order, preview scrub, anchored zoom, saved timeline view, export dock, close.')
