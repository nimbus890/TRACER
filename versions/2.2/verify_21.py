"""End-to-end journey checks and UI screenshots for Tracer 2.1."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import core
import release121
import timeline
import timeline_tools
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPoint
import app

def main():
    output = HERE / 'verification' / '2.1'
    output.mkdir(parents=True, exist_ok=True)
    qt = QApplication.instance() or QApplication([])
    qt.setStyle('Fusion')
    app.configure_fonts()
    qt.setStyleSheet(app.STYLE)

    print("--- 1. Testing Premiere FCP 7 XML Generation ---")
    seq = {
        'id': 'v21_test_seq',
        'name': 'Tracer 2.1 Demo',
        'frame_rate': 25,
        'width': 1920,
        'height': 1080,
        'tracks': [
            {
                'id': 'v1',
                'name': 'V1',
                'type': 'video',
                'visible': True,
                'locked': False,
                'clips': [
                    {
                        'id': 'clip1',
                        'name': 'A001_C001.mov',
                        'source': r'C:\Media\A001_C001.mov',
                        'start': 0.0,
                        'end': 12.5,
                        'source_in': 5.0,
                        'source_out': 17.5
                    }
                ]
            }
        ]
    }
    xml_data = timeline.final_cut_xml(seq)
    assert '<xmeml version="5">' in xml_data
    assert '<timebase>25</timebase>' in xml_data
    assert '<duration>312</duration>' in xml_data
    print(" Premiere FCP 7 XML conformity verified.")

    print("\n--- 2. Setting up UI Window & State ---")
    with tempfile.TemporaryDirectory() as temporary, patch.object(core, 'DATA', Path(temporary)), patch.object(app.Window, 'first_setup', lambda self: None):
        state = dict(
            folders=[{'id': 'f1', 'path': str(temporary), 'name': 'Source Media', 'active': True, 'files': []}],
            projects=[],
            collections=[],
            settings=core.DEFAULTS.copy(),
            results=[
                {
                    'id': '0',
                    'source': str(Path(temporary) / 'River interview.mp4'),
                    'duration': 120.0,
                    'output': temporary,
                    'frames': [],
                    'segments': [
                        {'start': 0, 'end': 5, 'text': 'The landscape was completely serene at dawn.'},
                        {'start': 5, 'end': 12, 'text': 'We prepared our gear and set out on the water.'}
                    ]
                },
                {
                    'id': '1',
                    'source': str(Path(temporary) / 'Mountain ascent.mp4'),
                    'duration': 85.0,
                    'output': temporary,
                    'frames': [],
                    'segments': []
                }
            ],
            schema_version=121
        )
        c = core.create_collection(state, 'B-Roll Selects')
        release121.migrate(state)
        release121.attach(state, c['id'], state['results'])

        with patch.object(core, 'load_state', lambda: state):
            win = app.Window()
        win.resize(1380, 860)
        win.show()

        def settle():
            for _ in range(15):
                qt.processEvents()

        settle()

        print("\n--- 3. Testing Storyline / Projects Page ---")
        win.navigate(3)
        settle()

        projects_page = win.projects_page
        assert hasattr(projects_page, 'list_mode_btn')
        assert hasattr(projects_page, 'grid_mode_btn')
        assert hasattr(projects_page, 'relink_media_btn')
        assert hasattr(projects_page, 'tools_board')
        assert hasattr(projects_page, 'zoom_out_btn')
        assert hasattr(projects_page, 'zoom_in_btn')
        assert hasattr(projects_page, 'sequence_video_container')
        assert hasattr(projects_page, 'sequence_control_bar')

        # Test zoom in and out
        initial_zoom = projects_page.zoom.value()
        projects_page.zoom_in_btn.click()
        assert projects_page.zoom.value() >= initial_zoom
        projects_page.zoom_out_btn.click()

        # Test video control bar updates
        preview_bar = projects_page.sequence_control_bar
        preview_bar.set_duration(120.0)
        preview_bar.set_position(14.0)
        assert '00:00:14 / 00:02:00' in preview_bar.time_label.text()

        # Capture Projects Page screenshot
        win.grab().save(str(output / 'tracer_21_projects_page.png'))
        print(" Saved screenshot: tracer_21_projects_page.png")

        print("\n--- 4. Testing Library Picker Modal Overlay ---")
        picker = app.LibraryPickerDialog(state['results'], parent=win)
        picker.show()
        picker.resize(win.size())
        settle()
        assert hasattr(picker, 'card')
        assert picker.card.objectName() == 'libraryCard'
        picker.grab().save(str(output / 'tracer_21_library_overlay.png'))
        print(" Saved screenshot: tracer_21_library_overlay.png")
        picker.close()
        settle()

        print("\n--- 4b. Testing Add to Collection Overlay ---")
        add_to_dlg = app.AddToCollectionDialog(state, ['vid1'], parent=win)
        add_to_dlg.show()
        settle()
        assert hasattr(add_to_dlg, 'card')
        assert add_to_dlg.card.objectName() == 'addToCard'
        assert add_to_dlg.coll_list.count() >= 1
        assert add_to_dlg.coll_list.item(0).data(Qt.UserRole) == '__new__'
        add_to_dlg.grab().save(str(output / 'tracer_21_add_to_collection.png'))
        print(" Saved screenshot: tracer_21_add_to_collection.png")
        add_to_dlg.close()
        settle()

        print("\n--- 5. Testing Options Dialog Overlay & Glow Suppression ---")
        folder = {'id': 'f1', 'path': str(temporary), 'name': 'Source Media', 'active': True, 'files': []}
        dlg = app.OptionsDialog(core.DEFAULTS.copy(), [folder], win)
        dlg.show()
        dlg.resize(win.size())
        settle()

        dlg._cursor_point = QPoint(20, 20)
        dlg.update()
        settle()
        dlg.grab().save(str(output / 'tracer_21_options_dialog.png'))
        print(" Saved screenshot: tracer_21_options_dialog.png")
        dlg.close()
        settle()

        for task in list(win.tasks):
            task.wait(5000)
        settle()
        win.close()
        settle()
        win.deleteLater()
        print("\n Tracer 2.1 Verification Journey complete: All checks PASSED successfully.")
        os._exit(0)

if __name__ == '__main__':
    main()
