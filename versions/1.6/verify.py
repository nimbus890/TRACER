"""Integration verification using generated fixtures, never user videos."""
import argparse
import json
import os
from pathlib import Path
import sys
import wave

import core


def video_with_audio(wav_path, target):
    import av
    import numpy as np
    with wave.open(str(wav_path)) as wav:
        rate = wav.getframerate()
        channels = wav.getnchannels()
        samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16)
        if channels > 1:
            samples = samples.reshape(-1, channels).mean(axis=1).astype(np.int16)
    length = len(samples) / rate
    with av.open(str(target), 'w') as output:
        video = output.add_stream('mpeg4', rate=10)
        video.width, video.height, video.pix_fmt = 640, 360, 'yuv420p'
        audio = output.add_stream('aac', rate=rate)
        audio.layout = 'mono'
        for i in range(int(length * 10) + 1):
            image = np.zeros((360, 640, 3), dtype=np.uint8)
            image[:, :, :] = [22, 42, 58] if i < 30 else [55, 155, 120]
            image[70:290, 30 + (i * 3) % 220:310 + (i * 3) % 220] = [100, 220, 190]
            frame = av.VideoFrame.from_ndarray(image, format='rgb24')
            for packet in video.encode(frame):
                output.mux(packet)
        for start in range(0, len(samples), 1024):
            values = samples[start:start + 1024][None, :]
            frame = av.AudioFrame.from_ndarray(values, format='s16', layout='mono')
            frame.sample_rate = rate
            frame.pts = start
            for packet in audio.encode(frame):
                output.mux(packet)
        for stream in (video, audio):
            for packet in stream.encode():
                output.mux(packet)


def integration():
    folder = core.ROOT / 'verification'
    folder.mkdir(exist_ok=True)
    video = folder / 'spoken-sample.mp4'
    video_with_audio(folder / 'speech.wav', video)
    item = next(v for v in core.scan_folder(folder)['files'] if Path(v['path']) == video)
    options = {**core.DEFAULTS, 'device': 'cuda', 'language': 'en', 'interval': .5, 'skip_existing': False}
    transcriber = core.Transcriber()
    result = core.process_video(folder, item, options, core.Control(), transcriber, lambda k, v: print(k, v, flush=True))
    assert result['device'] == 'cuda', result
    words = ' '.join(s['text'] for s in result['segments']).lower()
    assert 'video' in words and 'folder' in words, words
    assert len(result['frames']) >= 10, len(result['frames'])
    core.atomic_json(folder / 'gpu-verification.json', result)
    print(json.dumps({'device': result['device'], 'transcript': words, 'screenshots': len(result['frames']), 'output': result['output']}, indent=2))
    transcript_only = core.process_video(folder, item, {**options, 'screenshots': False, 'visual_index': False}, core.Control(), transcriber, lambda *_: None)
    assert transcript_only['segments'] and not transcript_only['frames']
    assert not Path(transcript_only['output'], 'screenshots').exists()
    core.atomic_json(folder / 'transcription-only-verification.json', transcript_only)
    print('Transcription-only GPU check passed: all transcript formats, zero screenshot files.')


def ui():
    os.environ['QT_QPA_PLATFORM'] = 'offscreen'
    os.environ['TRANSPRO_DATA'] = str(core.ROOT / 'verification' / 'ui-data')
    # core is already imported, so isolate its state explicitly.
    core.DATA = Path(os.environ['TRANSPRO_DATA'])
    core.DATA.mkdir(parents=True, exist_ok=True)
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    import app
    application = QApplication([])
    app.configure_fonts()
    application.setStyle('Fusion')
    application.setStyleSheet(app.STYLE)
    window = app.Window()
    folder = core.scan_folder(core.ROOT / 'verification')
    window.state['folders'] = [folder]
    window.state['projects'] = [dict(id='ui-project', name='Documentary interviews', created=0,
                                     folders=[json.loads(json.dumps(folder))])]
    result_file = core.ROOT / 'verification' / 'gpu-verification.json'
    if result_file.exists():
        result = json.loads(result_file.read_text(encoding='utf-8'))
        if result.get('frames') and not result.get('visual_index'):
            coarse = {**result['frames'][0], 'keywords': {'foreground': ['person'], 'midground': ['chair'], 'background': ['tv']},
                      'search_words': ['person', 'people', 'chair', 'tv'], 'detections': []}
            result['visual_index'] = {'version': 1, 'interval': 30, 'keywords': coarse['keywords'],
                                      'search_words': coarse['search_words'], 'frames': [coarse]}
        window.state['results'] = [result]
    window.refresh_tree()
    window.projects_page.refresh('ui-project')
    window.search_page.set_records(window.state['results'])
    window.results.set_records(window.state['results'])
    window.show()
    for _ in range(20):
        application.processEvents()
    tree = window.tree.topLevelItem(0)
    tree.setExpanded(True)
    tree.setCheckState(0, Qt.Unchecked)
    application.processEvents()
    assert not any(v['selected'] for v in folder['files']), 'Folder deselection failed'
    tree.setCheckState(0, Qt.Checked)
    application.processEvents()
    assert all(v['selected'] for v in folder['files']), 'Folder selection failed'
    window.grab().save(str(core.ROOT / 'verification' / 'queue.png'))
    options = app.OptionsDialog(core.DEFAULTS, [folder], window)
    options.show()
    application.processEvents()
    options.interval.setValue(.15)
    assert options.values()['interval'] == .15
    assert not options.findChildren(app.QScrollArea)
    assert all(tile.width() <= 64 for tile in (options.transcribe, options.screenshots, options.visual_index))
    assert not options.advanced_panel.isVisible()
    options.advanced_toggle.click()
    application.processEvents()
    assert options.advanced_panel.isVisible() and options.values()['width'] == 1280
    options.grab().save(str(core.ROOT / 'verification' / 'options-advanced.png'))
    options.advanced_toggle.click()
    options.scene_mode.setChecked(True)
    application.processEvents()
    assert not options.interval_box.isEnabled()
    options.interval_mode.setChecked(True)
    application.processEvents()
    options.grab().save(str(core.ROOT / 'verification' / 'options.png'))
    options.png.setChecked(True)
    application.processEvents()
    assert options.values()['image_format'] == 'png' and not options.quality.isEnabled()
    options.language_custom.setChecked(True)
    application.processEvents()
    assert options.language.isVisible()
    options.visual_index.setChecked(False)
    application.processEvents()
    assert options.visual_interval_box.isVisible() and not options.visual_interval_box.isEnabled()
    options.transcribe.setChecked(False)
    options.screenshots.setChecked(False)
    application.processEvents()
    assert not options.model.isEnabled() and not options.language_auto.isEnabled()
    assert not options.interval_mode.isEnabled() and not options.width.isEnabled()
    options.redo.setChecked(True)
    assert not options.values()['skip_existing']
    options.grab().save(str(core.ROOT / 'verification' / 'options-disabled.png'))
    assert options.dismiss_if_outside(options.frameGeometry().topLeft() - options.rect().bottomRight())
    assert options.result() == app.QDialog.Rejected
    window.navigate(1)
    application.processEvents()
    window.grab().save(str(core.ROOT / 'verification' / 'projects.png'))
    window.navigate(2)
    application.processEvents()
    window.grab().save(str(core.ROOT / 'verification' / 'search.png'))
    window.navigate(3)
    if window.results.list.count():
        window.results.select(window.results.list.item(0))
        QTest.qWait(280)
        application.processEvents()
        assert window.results.frames.count() > 0
        assert window.results.transcript.count() > 0
        assert not window.results.search_panel.isVisible()
        assert window.results.open_original.text() == 'Open original folder'
        assert window.results.open_results.text() == 'Open results folder'
        assert window.results.play_button.text() == ''
        assert window.results.media_split.handleWidth() >= 7
    application.processEvents()
    window.grab().save(str(core.ROOT / 'verification' / 'library.png'))
    window.navigate(4)
    application.processEvents()
    window.grab().save(str(core.ROOT / 'verification' / 'settings.png'))
    for task in list(window.tasks):
        task.wait(10000)
    application.processEvents()
    window.close()
    print('UI checks passed: folder selection, projects, exact interval, library, model settings, rendered screenshots.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['gpu', 'ui'])
    args = parser.parse_args()
    integration() if args.mode == 'gpu' else ui()
