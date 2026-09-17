import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import unittest
from types import SimpleNamespace
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
import app
import paper_edit


class UpgradeJourneyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.qt = QApplication.instance() or QApplication([])

    def test_paper_edit_switch_edit_exclude_and_empty(self):
        state = {'results': [], 'paper_edits': []}
        result = {'id': 'a', 'source': 'missing-source.mp4',
                  'segments': [{'start': 0, 'end': 2, 'text': 'A brief opening line.'}]}
        document = paper_edit.ensure_paper_document(state, result)
        window = SimpleNamespace(state=state, save_timer=QTimer())
        page = app.PaperEditPage(window)
        page.resize(1100, 720)
        page.show()
        self.qt.processEvents()
        row = page.paper.rows[0]
        row.text.setPlainText('The revised opening.')
        self.qt.processEvents()
        self.assertEqual(document['segments'][0]['text'], 'The revised opening.')
        self.assertLess(row.text.height(), 150)
        row.included.setChecked(False)
        self.assertFalse(page.export_button.isEnabled())
        row.included.setChecked(True)
        self.assertTrue(page.export_button.isEnabled())
        page.exporting = True
        page.refresh(document['id'])
        self.assertFalse(page.export_button.isEnabled())
        state['paper_edits'] = []
        page.refresh()
        self.assertEqual(page.source_name.text(), 'Select a transcript')
        self.assertFalse(page.export_button.isEnabled())
        page.player.stop()
        page.close()


if __name__ == '__main__':
    unittest.main()
