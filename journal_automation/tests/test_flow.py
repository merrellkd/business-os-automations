import shutil
from pathlib import Path
from datetime import datetime, timedelta
import unittest

from journal_automation.flow import create_journal_flow
from journal_automation.utils.fs_utils import ensure_dir

class TestJournalFlow(unittest.TestCase):
    def setUp(self):
        self.root = Path('tmp_journal_flow')
        shutil.rmtree(self.root, ignore_errors=True)
        ensure_dir(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_flow_archives_and_creates_today(self):
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d-%a').lower()
        old_folder = self.root / yesterday
        ensure_dir(old_folder)
        (old_folder / f"{yesterday}.journal.md").write_text('old')

        shared = {'journal_root': str(self.root), 'today_folder': '', 'today_path': ''}
        flow = create_journal_flow()
        flow.run(shared)

        today_folder = datetime.now().strftime('%Y-%m-%d-%a').lower()
        today_path = self.root / today_folder
        self.assertTrue(today_path.is_dir())
        self.assertTrue((today_path / f"{today_folder}.journal.md").exists())

        date = datetime.strptime(yesterday[:10], '%Y-%m-%d')
        year = str(date.year)
        month_code = date.strftime('%m')
        month_name = date.strftime('%B').lower()
        archive_path = self.root / 'archive' / year / f"{month_code}-{month_name}" / yesterday
        self.assertTrue(archive_path.is_dir())
        self.assertFalse(old_folder.exists())
        self.assertTrue((archive_path / f"{yesterday}.journal.md").exists())

if __name__ == '__main__':
    unittest.main()
