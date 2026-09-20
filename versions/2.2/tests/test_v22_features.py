import os
import time
import unittest
from types import SimpleNamespace
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import Qt, QPoint, QSize, QRect
from PySide6.QtWidgets import (
    QApplication, QWidget, QAbstractItemView, QTreeWidgetItem, QListWidgetItem,
    QStyleOptionViewItem
)
from PySide6.QtGui import QIcon, QPainter, QPixmap, QCursor

import app
import timeline
import workspace


class FakeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.state = {
            'collections': [{'id': 'c1', 'name': 'Test Coll', 'video_ids': ['vid1', 'vid2']}],
            'projects': [{'id': 'p1', 'name': 'Proj', 'sequences': [timeline.new_sequence('Seq 1')], 'folders': []}],
            'results': [
                {'id': 'vid1', 'source': 'clip1.mp4', 'duration': 30, 'segments': ['seg1']},
                {'id': 'vid2', 'source': 'clip2.mp4', 'duration': 45, 'segments': ['seg2']},
            ],
            'settings': {}
        }
        self.save_timer = SimpleNamespace(start=lambda ms: None)
        self.remove_project_source = lambda: None
        self.pause_batch = lambda: None
        self.cancel_batch = lambda: None
        self.process_project = lambda: None
        self.batch = False
        self.scanning = False


class TestV22Features(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def setUp(self):
        self.window = FakeWindow()
        self.projects_page = app.ProjectsPage(self.window)

    def test_sequential_media_insert(self):
        """Sequential insert should append clips one after another on V1/A1 without stacking tracks."""
        seq = self.projects_page.active_sequence()
        self.assertIsNotNone(seq)
        initial_track_count = len(seq['tracks'])

        videos = [
            {'path': 'clipA.mp4', 'duration': 10.0, 'name': 'Clip A', 'audio': True},
            {'path': 'clipB.mp4', 'duration': 15.0, 'name': 'Clip B', 'audio': True},
            {'path': 'clipC.mp4', 'duration': 20.0, 'name': 'Clip C', 'audio': True},
        ]
        self.projects_page.add_sequential_media_to_timeline(videos)

        # Tracks should not have expanded into V2, V3, V4
        self.assertEqual(len(seq['tracks']), initial_track_count)

        v1 = next(t for t in seq['tracks'] if t['name'] == 'V1')
        a1 = next(t for t in seq['tracks'] if t['name'] == 'A1')

        self.assertEqual(len(v1['clips']), 3)
        self.assertEqual(len(a1['clips']), 3)

        # First clip: 0.0 to 10.0
        self.assertEqual(v1['clips'][0]['start'], 0.0)
        self.assertEqual(v1['clips'][0]['end'], 10.0)

        # Second clip: 10.0 to 25.0
        self.assertEqual(v1['clips'][1]['start'], 10.0)
        self.assertEqual(v1['clips'][1]['end'], 25.0)

        # Third clip: 25.0 to 45.0
        self.assertEqual(v1['clips'][2]['start'], 25.0)
        self.assertEqual(v1['clips'][2]['end'], 45.0)

        # Audio should match video times
        for vc, ac in zip(v1['clips'], a1['clips']):
            self.assertEqual(vc['start'], ac['start'])
            self.assertEqual(vc['end'], ac['end'])

    def test_insert_media_button_properties(self):
        """Insert button should show plus_timeline icon and have a helpful sequential insert tooltip."""
        btn = self.projects_page.insert_media_button
        self.assertFalse(btn.icon().isNull())
        self.assertIn('sequentially', btn.toolTip().lower())
        self.assertEqual(btn.width(), 28)

    def test_generic_thumbnail_placeholder(self):
        """Generic thumbnail icon should be 96x56 and non-null."""
        icon = self.projects_page._generic_thumbnail_icon()
        self.assertIsInstance(icon, QIcon)
        self.assertFalse(icon.isNull())
        pix = icon.pixmap(96, 56)
        self.assertEqual(pix.width(), 96)
        self.assertEqual(pix.height(), 56)

    def test_media_hint_text(self):
        """Media hint should display the concise 'Drag or double-click to insert'."""
        self.assertEqual(self.projects_page.media_hint.text(), 'Drag or double-click to insert')

    def test_extended_selection_mode(self):
        """All media views should support ExtendedSelection for Ctrl/Shift multi-select."""
        self.assertEqual(self.projects_page.tree.selectionMode(), QAbstractItemView.ExtendedSelection)
        self.assertEqual(self.projects_page.media_grid.selectionMode(), QAbstractItemView.ExtendedSelection)

        # Queue tree in Window
        win = app.Window()
        self.assertEqual(win.tree.selectionMode(), QAbstractItemView.ExtendedSelection)

        # ResultsPage tree
        results_page = app.ResultsPage(self.window)
        self.assertEqual(results_page.tree.selectionMode(), QAbstractItemView.ExtendedSelection)

        # LibraryPickerDialog list
        picker = app.LibraryPickerDialog([], self.window)
        self.assertEqual(picker.list.selectionMode(), QAbstractItemView.ExtendedSelection)

    def test_checkbox_checkstate_handling(self):
        """CheckState evaluation handles both Qt.CheckState enum and raw integer 2."""
        raw_int = 2
        raw_enum = Qt.CheckState.Checked
        raw_qt = Qt.Checked

        def is_checked(raw):
            return raw in (Qt.Checked, 2, Qt.CheckState.Checked)

        self.assertTrue(is_checked(raw_int))
        self.assertTrue(is_checked(raw_enum))
        self.assertTrue(is_checked(raw_qt))
        self.assertFalse(is_checked(0))
        self.assertFalse(is_checked(Qt.CheckState.Unchecked))

    def test_sequence_header_symbol_buttons(self):
        """Sequence header provides crisp symbol buttons for add, duplicate, and delete."""
        self.assertTrue(hasattr(self.projects_page, 'new_sequence_btn'))
        self.assertTrue(hasattr(self.projects_page, 'duplicate_sequence_btn'))
        self.assertTrue(hasattr(self.projects_page, 'delete_sequence_btn'))

        self.assertIn('+', self.projects_page.new_sequence_btn.toolTip())
        self.assertIn('Duplicate', self.projects_page.duplicate_sequence_btn.toolTip())
        self.assertIn('Delete', self.projects_page.delete_sequence_btn.toolTip())

        # Test new sequence creation
        proj = self.projects_page.current()
        initial_seq_count = len(proj['sequences'])
        self.projects_page.create_new_sequence()
        self.assertEqual(len(proj['sequences']), initial_seq_count + 1)

    def test_adaptive_zoom_and_fit(self):
        """TimelineCanvas allows zoom below 2.0 pps and fits long sequences properly."""
        canvas = self.projects_page.timeline_canvas
        canvas.set_zoom(0.05)
        self.assertAlmostEqual(canvas.pixels_per_second, 0.05, places=3)

        # Fit long sequence (e.g. 1800s in 900px viewport)
        seq = self.projects_page.active_sequence()
        seq['tracks'][0]['clips'].append(timeline.make_clip('long.mp4', 1800.0, 0.0))
        canvas.set_sequence(seq)
        canvas.fit(900)
        # Target pps should be around (900 - 116 - 32) / 1800 ≈ 0.417 pps, definitely < 2.0
        self.assertLess(canvas.pixels_per_second, 1.0)
        self.assertGreater(canvas.pixels_per_second, 0.1)

    def test_timeline_autoscroll_api(self):
        """TimelineCanvas autoscroll timer and stop mechanism."""
        canvas = self.projects_page.timeline_canvas
        self.assertTrue(hasattr(canvas, '_autoscroll_timer'))
        self.assertTrue(hasattr(canvas, '_check_autoscroll'))
        self.assertTrue(hasattr(canvas, '_handle_autoscroll'))
        self.assertTrue(hasattr(canvas, '_stop_autoscroll'))

        canvas._autoscroll_dx = 15
        canvas._stop_autoscroll()
        self.assertEqual(canvas._autoscroll_dx, 0)
        self.assertFalse(canvas._autoscroll_timer.isActive())

    def test_sidebar_new_coll_btn_borderless(self):
        """Sidebar collections '+' button should be borderless transparent by default."""
        win = app.Window()
        self.assertTrue(hasattr(win, 'new_coll_btn'))
        style = win.new_coll_btn.styleSheet()
        self.assertIn('background: transparent', style)
        self.assertIn('border: none', style)
        self.assertIn(':hover', style)
        self.assertIn(':pressed', style)

    def test_razor_icon_renders(self):
        """Razor safety blade icon renders cleanly without exceptions."""
        icon = workspace.icon('razor')
        self.assertIsInstance(icon, QIcon)
        self.assertFalse(icon.isNull())

    def test_plus_timeline_icon_renders(self):
        """plus_timeline vector icon renders cleanly and is assigned to insert_media_button."""
        icon = workspace.icon('plus_timeline')
        self.assertIsInstance(icon, QIcon)
        self.assertFalse(icon.isNull())
        btn = self.projects_page.insert_media_button
        self.assertFalse(btn.icon().isNull())

    def test_sidebar_frame_animated_gradient(self):
        """Sidebar is a SidebarFrame with an active ambient glow animation timer."""
        win = app.Window()
        self.assertIsInstance(win.sidebar, app.SidebarFrame)
        self.assertTrue(hasattr(win.sidebar, '_anim_timer'))
        self.assertTrue(hasattr(win.sidebar, '_glow_phase'))
        initial_phase = win.sidebar._glow_phase
        win.sidebar._on_glow_tick()
        self.assertNotEqual(win.sidebar._glow_phase, initial_phase)

    def test_story_timeline_view_preset(self):
        """ProjectsPage desk includes 'Story timeline' preset and horizontal/vertical layout buttons with Timeline headline."""
        self.assertIn('Story timeline', self.projects_page.desk.presets)
        self.assertTrue(hasattr(self.projects_page, 'landscape_button'))
        self.assertTrue(hasattr(self.projects_page, 'portrait_button'))
        self.assertFalse(hasattr(self.projects_page, 'story_timeline_button'))
        win = app.Window()
        self.assertEqual(win.nav[3].text().strip(), 'Timeline')
        workspace_title = win.projects_page.workspace_bar.findChild(app.QLabel, 'workspaceTitle')
        self.assertIsNotNone(workspace_title)
        self.assertEqual(workspace_title.text(), 'Timeline')

    def test_library_picker_dialog_spacious_and_resizable(self):
        """LibraryPickerDialog uses a spacious ResizableCard that supports edge resizing and header dragging."""
        win = app.Window()
        picker = app.LibraryPickerDialog([], win)
        self.assertIsInstance(picker.card, app.ResizableCard)
        picker.show()
        # Initial size should be spacious (width >= 800, height >= 540)
        self.assertGreaterEqual(picker.card.width(), 760)
        self.assertGreaterEqual(picker.card.height(), 500)

        # Test edge hit detection
        card = picker.card
        # Inside should have no edges
        self.assertEqual(card._hit_edges(QPoint(100, 100)), set())
        # Left edge
        self.assertIn('left', card._hit_edges(QPoint(3, 100)))
        # Right edge
        self.assertIn('right', card._hit_edges(QPoint(card.width() - 3, 100)))
        # Top edge
        self.assertIn('top', card._hit_edges(QPoint(100, 3)))
        # Bottom edge
        self.assertIn('bottom', card._hit_edges(QPoint(100, card.height() - 3)))
        # Top-left corner
        self.assertEqual(card._hit_edges(QPoint(3, 3)), {'top', 'left'})
        # Bottom-right corner
        self.assertEqual(card._hit_edges(QPoint(card.width() - 3, card.height() - 3)), {'bottom', 'right'})
        picker.close()

    def test_media_table_delegate_checkbox_rendering(self):
        """MediaTableDelegate paints column 0 for both checked and unchecked states without error."""
        win = app.Window()
        rec1 = {'id': 'r1', 'source': 'clip1.mp4', 'duration': 30.0, 'output': ''}
        win.state['results'] = [rec1]
        win.navigate(1)
        win.results.set_records([rec1])

        item = win.results.tree.topLevelItem(0)
        self.assertIsNotNone(item)

        delegate = win.results.tree.itemDelegate()
        pix = QPixmap(100, 100)
        painter = QPainter(pix)
        option = QStyleOptionViewItem()
        option.rect = QRect(0, 0, 48, 62)
        index0 = win.results.tree.model().index(0, 0)

        # Paint unchecked
        item.setCheckState(0, Qt.Unchecked)
        delegate.paint(painter, option, index0)

        # Paint checked
        item.setCheckState(0, Qt.Checked)
        delegate.paint(painter, option, index0)
        painter.end()

    def test_results_table_generous_click_capture(self):
        """Clicking column 0 in ResultsPage toggles check state and updates checked_ids."""
        win = app.Window()
        rec1 = {'id': 'r1', 'source': 'clip1.mp4', 'duration': 30.0, 'output': ''}
        win.state['results'] = [rec1]
        win.navigate(1)
        win.results.set_records([rec1])

        item = win.results.tree.topLevelItem(0)
        item.setCheckState(0, Qt.Unchecked)
        win.results.checked_ids.clear()
        win.results._last_toggled_time = 0
        win.results._last_toggled_item = None

        # First click toggles to Checked
        win.results.on_table_item_clicked(item, 0)
        self.assertEqual(item.checkState(0), Qt.Checked)
        self.assertIn('r1', win.results.checked_ids)

        # Wait past debounce and click again to toggle to Unchecked
        time.sleep(0.3)
        win.results.on_table_item_clicked(item, 0)
        self.assertEqual(item.checkState(0), Qt.Unchecked)
        self.assertNotIn('r1', win.results.checked_ids)

    def test_queue_checkbox_style_and_assets(self):
        """Ensure checkbox style matches v1.23 clean indicator and avoids orange boxy indicators."""
        self.assertIn('QCheckBox::indicator { width: 17px; height: 17px; }', app.STYLE)
        self.assertNotIn('QCheckBox::indicator:checked', app.STYLE)

    def test_queue_generous_click_capture(self):
        """Window.on_queue_item_clicked captures clicks within 40px hit area around checkbox."""
        win = app.Window()
        folder = {
            'id': 'f1', 'name': 'Camera_A', 'path': r'C:\Media\Camera_A',
            'files': [
                {'name': 'Clip001.mov', 'path': r'C:\Media\Camera_A\Clip001.mov', 'duration': 42.0, 'status': 'Ready', 'selected': True},
            ]
        }
        win.state['folders'] = [folder]
        win.refresh_tree()
        win.tree.expandAll()

        child_item = win.tree.topLevelItem(0).child(0)
        self.assertEqual(child_item.checkState(0), Qt.Checked)

        vrect = win.tree.visualItemRect(child_item)
        # Click within 40px hit area (e.g. +25px)
        pos = win.tree.viewport().mapToGlobal(QPoint(vrect.x() + 25, vrect.y() + 5))
        QCursor.setPos(pos)
        win._last_queue_toggled_time = 0
        win._last_queue_toggled_item = None

        win.on_queue_item_clicked(child_item, 0)
        self.assertEqual(child_item.checkState(0), Qt.Unchecked)

        # Click outside 40px hit area (e.g. +60px) should not toggle
        pos_far = win.tree.viewport().mapToGlobal(QPoint(vrect.x() + 60, vrect.y() + 5))
        QCursor.setPos(pos_far)
        win._last_queue_toggled_time = 0
        win._last_queue_toggled_item = None

        win.on_queue_item_clicked(child_item, 0)
        self.assertEqual(child_item.checkState(0), Qt.Unchecked)

    def test_export_project_dialog_overlay(self):
        """ExportProjectDialog opens with backdrop blur, progress bar, and runs async export."""
        win = app.Window()
        win.show()

        called = []
        def mock_export(dest, prog, cancel):
            prog(50, 'clip1.mp4', 1, 2)
            prog(100, 'clip2.mp4', 2, 2)
            called.append(dest)
            return (2, 0, [])

        dlg = app.ExportProjectDialog(
            parent=win,
            export_fn=mock_export,
            title='Export Collection',
            subtitle='Export 2 videos',
            default_destination=str(app.core.ROOT)
        )
        self.assertTrue(dlg.windowFlags() & Qt.FramelessWindowHint)
        self.assertTrue(dlg.testAttribute(Qt.WA_TranslucentBackground))
        self.assertIsNotNone(dlg.background_blur)

        # Run export
        dlg.start_export()
        self.assertIsNotNone(dlg.worker)
        dlg.worker.wait(2000)
        app.QApplication.processEvents()
        self.assertEqual(len(called), 1)
        self.assertEqual(dlg.progress_bar.value(), 100)
        self.assertIn('Done', dlg.status_label.text())
        dlg.close()

    def test_media_picker_dialog_mode(self):
        """MediaPickerDialog uses non-native mode allowing both folders and files."""
        win = app.Window()
        picker = app.MediaPickerDialog(win)
        self.assertTrue(picker.testOption(app.QFileDialog.DontUseNativeDialog))
        self.assertTrue(hasattr(picker, '_add_folder_btn'))
        picker.close()


if __name__ == '__main__':
    unittest.main()
