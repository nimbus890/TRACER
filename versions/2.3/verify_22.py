import os
import sys
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPixmap

import app
import timeline

def run_verification():
    app_qt = QApplication.instance() or QApplication([])
    app_qt.setStyle('Fusion')
    app.configure_fonts()
    app_qt.setStyleSheet(app.STYLE)

    win = app.Window()
    win.resize(1400, 900)
    win.show()

    # Navigate to Storyline page
    win.navigate(3) # Storyline tab index
    app_qt.processEvents()

    # Ensure we have active project and sequence
    proj_page = win.projects_page
    proj = proj_page.current()
    if not proj:
        # If no project, select or create one in test state
        if not win.state.get('projects'):
            win.state['projects'] = [{
                'id': 'test_proj_v22',
                'name': 'Test v2.2 Project',
                'folders': [],
                'sequences': [timeline.new_sequence('Main Edit')]
            }]
        proj = win.state['projects'][0]
        proj_page.project_changed(proj)
        app_qt.processEvents()

    # Switch to grid view in Sequence Media to demonstrate generic placeholder thumbnails
    proj_page.set_media_symbol_mode(True)
    app_qt.processEvents()

    # Insert sequential media if timeline is empty
    seq = proj_page.active_sequence()
    if seq and not seq['tracks'][0]['clips']:
        clips_data = [
            {'path': 'clip_intro.mp4', 'duration': 14.5, 'name': 'Intro Scene', 'audio': True},
            {'path': 'clip_interview.mp4', 'duration': 28.0, 'name': 'Interview A', 'audio': True},
            {'path': 'clip_broll.mp4', 'duration': 12.2, 'name': 'B-Roll Montage', 'audio': True},
            {'path': 'clip_outro.mp4', 'duration': 18.0, 'name': 'Outro Credits', 'audio': True},
        ]
        proj_page.add_sequential_media_to_timeline(clips_data)
        app_qt.processEvents()

    artifact_dir = Path(r"C:\Users\praku\.gemini\antigravity\brain\2ac838d0-3caf-4692-b01e-2ebf61b96d8f")

    # Screenshot 1: Storyline page (showing plus_timeline icon and Story timeline preset)
    pix1 = win.grab()
    pix1.save(str(artifact_dir / "tracer_22_storyline_page.png"))
    print("Saved tracer_22_storyline_page.png")

    # Screenshot 2: Sidebar ambient gradient glow
    if hasattr(win, 'sidebar') and win.sidebar:
        # Advance glow phase to show rich ambient gradient
        win.sidebar._glow_phase = 1.1
        win.sidebar.update()
        app_qt.processEvents()
        pix_sb = win.sidebar.grab()
        pix_sb.save(str(artifact_dir / "tracer_22_sidebar_animated.png"))
        print("Saved tracer_22_sidebar_animated.png")

    # Screenshot 3: LibraryPickerDialog spacious resizable overlay with full-window darkening & aura
    sample_records = [
        {'id': 'v1', 'name': 'Drone_Coastline_4K.mp4', 'duration': 42.5, 'transcript': 'Sweeping aerial shot of coastal cliffs at dawn.'},
        {'id': 'v2', 'name': 'Interview_Director.mp4', 'duration': 180.2, 'transcript': 'Discussion on visual pacing and cinematography choices.'},
        {'id': 'v3', 'name': 'Broll_CityStreets.mp4', 'duration': 35.0, 'transcript': 'Neon city lights, traffic stream, pedestrian crossings.'},
    ]
    picker = app.LibraryPickerDialog(sample_records, win)
    picker.resize(win.width(), win.height())
    picker.show()
    # Simulate cursor position on backdrop outside the card to showcase the aura
    picker._cursor_point = picker.rect().topLeft() + Qt.QPoint(120, 180) if hasattr(Qt, 'QPoint') else None
    from PySide6.QtCore import QPoint
    picker._cursor_point = QPoint(140, 200)
    picker.update()
    app_qt.processEvents()

    pix_overlay = picker.grab()
    pix_overlay.save(str(artifact_dir / "tracer_22_library_overlay_spacious.png"))
    print("Saved tracer_22_library_overlay_spacious.png")
    picker.close()
    app_qt.processEvents()

    # Screenshot 4: Fit long sequence
    if seq:
        seq['tracks'][0]['clips'].append(timeline.make_clip('epic_documentary.mp4', 1200.0, 72.7))
        proj_page.fit_timeline()
        app_qt.processEvents()
        pix4 = win.grab()
        pix4.save(str(artifact_dir / "tracer_22_fit_long_sequence.png"))
        print("Saved tracer_22_fit_long_sequence.png")

    print("Verification screenshots completed successfully.")

if __name__ == '__main__':
    run_verification()
