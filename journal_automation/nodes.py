from pathlib import Path
from datetime import datetime
from pocketflow import Node
from journal_automation.utils.fs_utils import ensure_dir, move_folder, create_file

JOURNAL_TEMPLATE = """# {date}.journal.md

## Today's Priorities

### - 1)

### - 2)

### - 3)

## Daily Review & Reflections
"""

class ArchiveOldFolders(Node):
    def prep(self, shared):
        root = Path(shared['journal_root'])
        today = shared['today_folder']
        return [d for d in root.iterdir() if d.is_dir() and d.name not in ('archive', today)]

    def exec(self, folders):
        return folders

    def post(self, shared, prep_res, exec_res):
        root = Path(shared['journal_root'])
        for folder in exec_res:
            date_str = folder.name.split('/')[0]
            try:
                date = datetime.strptime(date_str[:10], '%Y-%m-%d')
            except ValueError:
                continue
            year = str(date.year)
            month_name = date.strftime('%B').lower()
            month_code = date.strftime('%m')
            archive_path = root / 'archive' / year / f"{month_code}-{month_name}" / folder.name
            move_folder(folder, archive_path)
        return 'default'

class CreateTodayFolder(Node):
    def prep(self, shared):
        root = Path(shared['journal_root'])
        today = datetime.now()
        folder_name = today.strftime('%Y-%m-%d-%a').lower()
        shared['today_folder'] = folder_name
        return root / folder_name

    def exec(self, folder_path: Path):
        ensure_dir(folder_path)
        return folder_path

    def post(self, shared, prep_res, exec_res):
        shared['today_path'] = str(exec_res)
        return 'default'

class CreateJournalFile(Node):
    def prep(self, shared):
        date_str = shared['today_folder']
        folder_path = Path(shared['today_path'])
        file_path = folder_path / f"{date_str}.journal.md"
        return file_path, date_str

    def exec(self, data):
        file_path, date_str = data
        create_file(file_path, JOURNAL_TEMPLATE.format(date=date_str))
        return file_path

