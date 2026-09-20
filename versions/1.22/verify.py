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
    import faulthandler
    faulthandler.dump_traceback_later(20, repeat=False)
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    os.environ['TRANSPRO_DATA'] = str(core.ROOT / 'verification' / 'ui-data')
    # core is already imported, so isolate its state explicitly.
    core.DATA = Path(os.environ['TRANSPRO_DATA'])
    core.DATA.mkdir(parents=True, exist_ok=True)
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    import app
    app.enable_high_dpi()
    application = QApplication([])
    app.configure_fonts()
    application.setStyle('Fusion')
    application.setStyleSheet(app.STYLE)
    window = app.Window()
    folder = core.scan_folder(core.ROOT / 'verification')
    window.state['folders'] = [folder]
    window.state['projects'] = [dict(id='ui-project', name='Documentary interviews', created=0,
                                     folders=[json.loads(json.dumps(folder))])]
    window.state['paper_edits'] = []
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
    window.projects_page.set_story_orientation('Landscape')
    window.results.set_records(window.state['results'])
    if window.state['results']:
        document = app.paper_edit.ensure_paper_document(window.state, window.state['results'][0])
        document['segments'][0]['speaker'] = 'MAYA'
        document['segments'][0]['note'] = 'Opening?'
        window.paper_edit_page.refresh(document['id'])
    window.show()
    for _ in range(20):
        application.processEvents()
    assert len(window.nav) == 5
    assert [control.text() for control in window.nav] == [
        'Queue', 'Library', 'Paper Edit', 'Storyline', 'Settings']
    assert window.pages.currentIndex() == 0
    assert window.paper_edit_page.objectName() == 'paperPage'
    assert window.nav[0].isChecked()
    window.navigate(2)
    window.paper_edit_page.desk.apply_preset('Writing desk')
    application.processEvents()
    if window.state['results']:
        assert window.paper_edit_page.paper.rows
        assert window.paper_edit_page.analysis.text().startswith(
            str(app.paper_edit.transcript_analysis(document)['words']))
        window.paper_edit_page.pen.click()
        assert window.paper_edit_page.paper.ink.tool == 'pen'
        document['strokes'].append({'tool': 'pen', 'points': [[30, 30], [100, 55]]})
        window.paper_edit_page.paper.ink.update()
        window.grab().save(str(core.ROOT / 'verification' / 'paper-edit.png'))
        window.paper_edit_page.pen.click()
        window.resize(1100, 720)
        application.processEvents()
        window.grab().save(str(core.ROOT / 'verification' / 'paper-edit-narrow.png'))
        window.resize(1440, 900)
        saved_paper_edits = window.state['paper_edits']
        window.state['paper_edits'] = []
        window.paper_edit_page.refresh()
        application.processEvents()
        assert window.paper_edit_page.document is None
        window.grab().save(str(core.ROOT / 'verification' / 'paper-edit-empty.png'))
        window.state['paper_edits'] = saved_paper_edits
        window.paper_edit_page.refresh(document['id'])
    window.navigate(0)
    application.processEvents()
    tree = window.tree.topLevelItem(0)
    tree.setExpanded(True)
    tree.setCheckState(0, Qt.Unchecked)
    application.processEvents()
    assert not any(v['selected'] for v in folder['files']), 'Folder deselection failed'
    tree.setCheckState(0, Qt.Checked)
    application.processEvents()
    assert all(v['selected'] for v in folder['files']), 'Folder selection failed'
    assert window.add_button.menu() is None
    assert window.add_button.text() == '+ Add media'
    assert 'Windows' in window.add_button.toolTip()
    assert window.remove.text() == '' and window.remove.accessibleName() == 'Remove selected item from queue'
    window.apply_usage_metrics(core.system_usage_snapshot(os.getpid()))
    application.processEvents()
    assert '—' not in window.usage_labels['ram'].text()
    window.grab().save(str(core.ROOT / 'verification' / 'queue.png'))
    options = app.OptionsDialog(core.DEFAULTS, [folder], window)
    options.show()
    application.processEvents()
    assert window.centralWidget().graphicsEffect() is not None
    options.interval.setValue(.15)
    assert options.values()['interval'] == .15
    assert not options.findChildren(app.QScrollArea)
    assert all(tile.width() <= 46 for tile in (options.transcribe, options.screenshots, options.visual_index))
    assert not options.advanced_panel.isVisible()
    assert options.advanced_toggle.text() == '' and options.advanced_toggle.toolTip() == 'Advanced settings'
    options.advanced_toggle.click()
    application.processEvents()
    assert options.advanced_panel.isVisible() and options.values()['width'] == 1280 and options.size().width() >= 1080
    options.grab().save(str(core.ROOT / 'verification' / 'options-advanced.png'))
    options.advanced_toggle.click()
    options.scene_mode.click()
    application.processEvents()
    assert not options.interval_box.isEnabled()
    options.fixed_mode.click()
    QTest.qWait(220)
    application.processEvents()
    assert options.interval_box.isEnabled() and options.values()['mode'] == 'interval'
    assert options.visual_interval_box.isHidden()
    assert options.values()['visual_interval'] == options.values()['interval']
    options.grab().save(str(core.ROOT / 'verification' / 'options.png'))
    options.png.setChecked(True)
    application.processEvents()
    assert options.values()['image_format'] == 'png' and not options.quality.isEnabled()
    options.language_custom.setChecked(True)
    application.processEvents()
    assert options.language.isVisible()
    options.visual_index.setChecked(False)
    application.processEvents()
    assert options.visual_interval_box.isHidden()
    options.transcribe.setChecked(False)
    options.screenshots.setChecked(False)
    application.processEvents()
    assert not options.model.isEnabled() and not options.language_auto.isEnabled()
    assert not options.scene_mode.isEnabled() and not options.width.isEnabled()
    assert options.start.text() == 'Start' and options.start.width() <= 84
    options.redo.setChecked(True)
    assert not options.values()['skip_existing']
    options.grab().save(str(core.ROOT / 'verification' / 'options-disabled.png'))
    assert options.dismiss_if_outside(options.frameGeometry().topLeft() - options.rect().bottomRight())
    assert options.result() == app.QDialog.Rejected
    assert window.centralWidget().graphicsEffect() is None
    window.navigate(3)
    application.processEvents()
    assert window.projects_page.sequence_tabs.count() >= 1
    assert window.projects_page.tree.topLevelItemCount() > 0
    project_video_item = window.projects_page.tree.topLevelItem(0).child(0)
    assert project_video_item is not None and project_video_item.data(0, Qt.UserRole + 1)
    window.projects_page.tree.setCurrentItem(project_video_item)
    window.projects_page.insert_selected_media()
    assert any(track.get('clips') for track in window.projects_page.active_sequence()['tracks'])
    track_count = len(window.projects_page.active_sequence()['tracks'])
    window.projects_page.add_media_to_timeline(
        project_video_item.data(0, Qt.UserRole + 1), start=0, track_index=1)
    assert len(window.projects_page.active_sequence()['tracks']) > track_count, (
        'Dropping on occupied footage must create another stack layer')
    assert window.projects_page.editor_stack.currentIndex() == 1
    assert not window.projects_page.processing_box.isVisible()
    assert not window.projects_page.export_panel.isVisible()
    project_sequence = window.projects_page.active_sequence()
    video_track_index = next(index for index, track in enumerate(project_sequence['tracks'])
                             if track.get('type') == 'video' and track.get('clips'))
    video_clip = project_sequence['tracks'][video_track_index]['clips'][0]
    audio_track_index = next(index for index, track in enumerate(project_sequence['tracks'])
                             if track.get('type') == 'audio' and
                             any(value.get('linked') == video_clip.get('linked')
                                 for value in track.get('clips', [])))
    project_sequence['tracks'][audio_track_index]['locked'] = True
    window.projects_page.timeline_canvas.selected_id = video_clip['id']
    window.projects_page.sequence_command('delete')
    assert video_clip in project_sequence['tracks'][video_track_index]['clips'], 'A locked linked track must protect the edit'
    assert 'Unlock' in window.projects_page.status.text()
    project_sequence['tracks'][audio_track_index]['locked'] = False
    window.projects_page.status.setText('Ready. Open the Library, then drag, stack, or split your footage.')
    assert window.projects_page.play_button.text() == '' and not window.projects_page.play_button.icon().isNull()
    window.projects_page.queue_sequence()
    assert window.projects_page.export_queue.count() == 1
    window.grab().save(str(core.ROOT / 'verification' / 'projects.png'))
    window.projects_page.delivery_toggle.click()
    application.processEvents()
    assert window.projects_page.export_panel.isVisible()
    window.grab().save(str(core.ROOT / 'verification' / 'projects-delivery.png'))
    window.projects_page.delivery_toggle.click()
    window.resize(1100, 720)
    application.processEvents()
    assert window.projects_page.timeline_canvas.isVisible()
    window.grab().save(str(core.ROOT / 'verification' / 'projects-narrow.png'))
    window.resize(1280, 860)
    window.state['projects'].append(dict(id='empty-project', name='Empty review', created=0, folders=[]))
    window.projects_page.refresh('empty-project')
    application.processEvents()
    assert window.projects_page.editor_stack.currentIndex() == 1
    assert not window.projects_page.delivery_toggle.isEnabled()
    assert window.projects_page.empty_action_button.text() == '+ Open Video Library'
    window.grab().save(str(core.ROOT / 'verification' / 'projects-empty.png'))
    window.projects_page.refresh('ui-project')
    window.navigate(1)
    window.results.desk.apply_preset('Research desk')
    assert len(window.nav) == 5 and all(button.text() != 'Footage search' for button in window.nav)
    window.results.search.setText('person')
    application.processEvents()
    assert window.results.list.count() > 0
    window.results.search.setText('video')
    application.processEvents()
    assert window.results.list.count() > 0
    if window.results.list.count():
        window.results.select(window.results.list.item(0))
        QTest.qWait(280)
        application.processEvents()
        assert window.results.frames.count() > 0
        assert window.results.transcript.count() > 0
        assert any(matched for item in range(window.results.transcript.count())
                   for _, matched in app.highlighted_parts(
                       window.results.transcript.item(item).text(), window.results.transcript_search.text()))
        assert window.results.search_panel.isVisible()
        assert window.results.browse_videos.text() == 'See All'
        assert window.results.audio_scope.text() == '' and window.results.visual_scope.text() == ''
        assert not hasattr(window.results, 'frame_scope')
        assert window.results.page_title.text() == app.Path(window.results.record['source']).name
        assert window.results.close_search.text() == ''
        assert window.results.open_original.text() == 'Show in Explorer'
        assert window.results.open_results.text() == 'Open results folder'
        assert window.results.play_button.text() == ''
        assert window.results.previous_frames.text() == '' and window.results.previous_frames.accessibleName() == 'Previous screenshots'
        assert window.results.next_frames.text() == '' and window.results.next_frames.accessibleName() == 'Next screenshots'
        assert window.results.media_split.handleWidth() >= 7
        open_width = window.results.desk.panels['transcript'].width()
        window.grab().save(str(core.ROOT / 'verification' / 'library-drawer.png'))
        window.results.collapse_search()
        application.processEvents()
        assert not window.results.search_panel.isVisible()
        assert window.results.media_split.width() > open_width
        window.results.open_search()
        application.processEvents()
        assert window.results.search_panel.isVisible()
        window.results.select(window.results.list.item(0))
        assert window.results.search_panel.isVisible(), 'Selecting a result must keep the result rail open'
        QTest.mouseClick(window.results.transcript.viewport(), Qt.LeftButton)
        application.processEvents()
        assert not window.results.search_panel.isVisible(), 'Clicking outside the result rail must collapse it'
    application.processEvents()
    window.grab().save(str(core.ROOT / 'verification' / 'library.png'))
    window.navigate(4)
    application.processEvents()
    window.grab().save(str(core.ROOT / 'verification' / 'settings.png'))
    for task in list(window.tasks):
        task.wait(10000)
    application.processEvents()
    QTest.qWait(500)
    window.close()
    faulthandler.cancel_dump_traceback_later()
    print('UI checks passed: Paper Edit, native queue, stackable Storyline, exact interval, Library, settings, screenshots.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['gpu', 'ui'])
    args = parser.parse_args()
    if args.mode == 'gpu':
        integration()
    else:
        from verify_122 import main
        main()
        import gc
        gc.collect()
