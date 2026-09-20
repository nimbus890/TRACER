import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from PySide6.QtWidgets import QApplication, QLabel, QInputDialog
from PySide6.QtCore import Qt, QTimer
from PySide6.QtTest import QTest
import app
import paper_edit
import workspace


class WorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def owner(self):
        return SimpleNamespace(state={}, save_timer=QTimer())

    def desk(self, owner):
        desk = workspace.Workspace(owner, 'test')
        for key in ('script', 'preview', 'search'):
            desk.add_panel(key, key.title(), QLabel(key))
        desk.configure('script', {
            'Writing': [(['script'], 600), (['preview'], 300)],
            'Finding': [(['script'], 500), (['search'], 250), (['preview'], 250)],
        })
        desk.resize(1000, 650)
        desk.show()
        self.qt.processEvents()
        return desk

    def test_hidden_panel_reopens_and_focus_restores_arrangement(self):
        desk = self.desk(self.owner())
        self.assertTrue(desk.panels['search'].isHidden())
        desk.show_panel('search')
        self.qt.processEvents()
        self.assertTrue(desk.panels['search'].isVisible())
        self.assertNotEqual(desk.dockWidgetArea(desk.panels['search']), Qt.NoDockWidgetArea)
        before = desk.serialized()
        desk.focus('script')
        self.assertFalse(desk.panels['preview'].isVisible())
        self.assertEqual(desk.serialized(), before)
        desk.restore_focus()
        self.assertTrue(desk.panels['preview'].isVisible())
        self.assertTrue(desk.panels['search'].isVisible())
        desk.close()

    def test_named_layout_and_current_layout_survive_new_workspace(self):
        owner = self.owner()
        desk = self.desk(owner)
        desk.apply_preset('Finding')
        desk.move_panel('preview', Qt.LeftDockWidgetArea)
        with patch.object(QInputDialog, 'getText', return_value=('My desk', True)):
            desk.save_named()
        saved = desk.store()['saved']['My desk']
        desk.apply_preset('Writing')
        desk.restore_named('My desk')
        self.qt.processEvents()
        self.assertTrue(desk.panels['search'].isVisible())
        desk.remember()
        reopened = self.desk(owner)
        self.assertTrue(reopened.panels['search'].isVisible())
        self.assertEqual(reopened.store()['saved']['My desk'], saved)
        reopened.close()
        desk.close()

    def test_paper_search_browses_multiple_sources_without_covering_script(self):
        records = [
            {'id': 'one', 'source': 'offline-one.mp4',
             'segments': [{'start': 0, 'end': 3, 'text': 'An archer tells the story.'}]},
            {'id': 'two', 'source': 'offline-two.mp4',
             'segments': [{'start': 4, 'end': 8, 'text': 'Researchers record the history.'}]},
        ]
        owner = self.owner()
        owner.state.update(results=records, paper_edits=[])
        document = paper_edit.ensure_paper_document(owner.state, records[0])
        page = app.PaperEditPage(owner)
        page.resize(1280, 800)
        page.show()
        self.qt.processEvents()
        page.search.setText('archer')
        self.qt.processEvents()
        self.assertEqual(page.search_results.count(), 2)
        page.search_results.setCurrentRow(0)
        self.qt.processEvents()
        self.assertEqual(page.document['result_id'], 'one')
        self.assertTrue(page.paper.editor.extraSelections())
        page.paper.editor.selectAll()
        page.paper.editor.insertPlainText('An archer remembers home.')
        page.search_results.setCurrentRow(1)
        self.qt.processEvents()
        self.assertEqual(page.document['result_id'], 'two')
        self.assertTrue(page.desk.panels['script'].isVisible())
        self.assertTrue(page.desk.panels['search'].isVisible())
        self.assertIn('offline', page.source_status.text())
        page.search_results.setCurrentRow(0)
        self.qt.processEvents()
        self.assertEqual(page.paper.editor.toPlainText(), 'An archer remembers home.')
        page.search.setText('unfindable-phrase')
        self.assertEqual(page.search_results.count(), 0)
        self.assertIn('No matches', page.search_count.text())
        self.assertEqual(page.document['id'], document['id'])
        page.player.stop()
        page.close()

    def test_passage_order_has_keyboard_alternative(self):
        owner = self.owner()
        owner.state.update(results=[], paper_edits=[])
        result = {'id': 'a', 'source': 'offline.mp4', 'segments': [
            {'start': 0, 'end': 2, 'text': 'Opening'},
            {'start': 2, 'end': 4, 'text': 'Closing'}]}
        document = paper_edit.ensure_paper_document(owner.state, result)
        page = app.PaperEditPage(owner)
        first = page.sequence.item(0).data(Qt.UserRole)
        page.sequence.setCurrentRow(0)
        page.move_passage(1)
        self.assertEqual(document['order'][1], first)
        page.move_passage(1)
        self.assertEqual(document['order'][1], first)
        page.close()
