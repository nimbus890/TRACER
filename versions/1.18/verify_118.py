"""1.18 regression checks with synthetic media and isolated state."""
import copy
import json
import os
from pathlib import Path
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPoint
from PySide6.QtTest import QTest
import app
import core

core.DATA = core.ROOT / 'verification' / 'regression-118-data'
core.DATA.mkdir(parents=True, exist_ok=True)
qt = QApplication([])
qt.setStyle('Fusion')
qt.setStyleSheet(app.STYLE)
record = json.loads((core.ROOT / 'verification' / 'gpu-verification.json').read_text(encoding='utf-8'))
record['id'] = 'visual-regression'
frame = {'time': 8., 'file': record['frames'][0]['file'],
         'detections': [{'label': 'car', 'confidence': .9, 'layer': 'foreground'}],
         'search_words': ['car'], 'keywords': {'foreground': ['car']}}
record['visual_index'] = {'frames': [frame], 'interval': 5}
video = dict(path=record['source'], name=Path(record['source']).name, duration=15.3,
             audio=True, status='Ready', selected=True)
folder = dict(id='queue-regression', name='Test footage', path=str(Path(record['source']).parent), files=[video, {**video, 'path': 'second.mp4', 'name': 'second.mp4'}])
state = dict(folders=[folder], projects=[], results=[record], settings=core.DEFAULTS.copy(), paper_edits=[])
with patch.object(core, 'load_state', return_value=state), patch.object(app.Window, 'first_setup', lambda self: None):
    win = app.Window()
win.show()
QTest.qWait(100)
win.tree.setCurrentItem(win.tree.topLevelItem(0).child(0))
win.refresh_tree()
assert win.tree.currentItem().data(0, Qt.UserRole)[1] == video['path']
win.remove.click()
assert len(state['folders'][0]['files']) == 1
assert Path(video['path']).is_file(), 'Queue removal must preserve the source'
win.remove.click()
assert not state['folders']

slider = app.MarkedSlider()
slider.setRange(0, 100)
slider.resize(216, 30)
slider.show()
QTest.mouseClick(slider, Qt.LeftButton, pos=QPoint(158, 15))
assert 74 <= slider.value() <= 76, slider.value()
slider.close()

win.navigate(1)
library = win.results
library.audio_scope.setChecked(False)
library.visual_scope.setChecked(True)
library.search.setText('cars')
assert library.list.count() == 1
assert 'indirect' not in library.list.item(0).data(Qt.UserRole + 1)['hits']
library.select(library.list.item(0))
QTest.qWait(800)
assert library.player.source().toLocalFile() == str(Path(record['source'])).replace('\\', '/'), library.player.source()
assert abs(library.player.position() - 8000) < 100, library.player.position()
assert abs(library.seek.value() - 8000) < 100, library.seek.value()
library.player.play()
QTest.qWait(150)
library.player.pause()
assert library.player.position() >= 8000
assert library.video.videoSink().videoFrame().isValid(), 'Preview must decode an actual image'
win.grab().save(str(core.ROOT / 'verification' / 'library-1.18-visual.png'))

win.navigate(3)
story = win.projects_page
assert story.editor_stack.currentIndex() == 1, 'An empty sequence must expose editing controls'
before = len(story.current()['sequences'])
story.new_sequence()
assert len(story.current()['sequences']) == before + 1
story.set_story_orientation('Portrait')
assert story.desk.panels['preview'].isVisible()
story.desk.hide_panel('preview')
assert story.desk.panels['preview'].isHidden()
story.set_story_orientation('Landscape')
assert story.desk.panels['preview'].isVisible()
for task in list(win.tasks):
    task.wait(5000)
win.close()
assert not win.isVisible()
print('1.18 regression passed: queue deletion, retained selection, slider jump, visual timestamp and playback, empty sequence, preview collapse/recovery.')
