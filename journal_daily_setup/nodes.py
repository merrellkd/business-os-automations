from pathlib import Path
from datetime import datetime
import subprocess
import shutil

from pocketflow import Node
from journal_daily_setup.utils.fs_utils import ensure_dir, move_folder, create_file

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
        repo_root = Path(shared.get('repo_root', '.')) if shared.get('repo_root') else None
        return file_path, date_str, repo_root

    def exec(self, data):
        file_path, date_str, repo_root = data
        create_file(file_path, JOURNAL_TEMPLATE.format(date=date_str))
        if repo_root and (repo_root / '.last_pr_url').exists():
            url = (repo_root / '.last_pr_url').read_text().strip()
            content = file_path.read_text()
            new_line = f"### - Review yesterday's PR: {url}\n"
            content = content.replace('### - 1)', new_line + '### - 1)')
            file_path.write_text(content)
        return file_path


class CommitChanges(Node):
    def prep(self, shared):
        return shared.get('repo_root'), shared.get('today_path')

    def exec(self, data):
        repo_root, today_path = data
        if not repo_root:
            return 'default'
        repo = Path(repo_root)
        if not (repo / '.git').exists():
            return 'default'
        subprocess.run(['git', 'add', 'archive'], cwd=repo)
        if today_path:
            subprocess.run(['git', 'reset', '--', today_path], cwd=repo)
        result = subprocess.run(['git', 'diff', '--cached', '--quiet'], cwd=repo)
        if result.returncode == 1:
            subprocess.run(['git', 'commit', '-m', 'Archive journal folders'], cwd=repo)
        return 'default'


class CreatePullRequest(Node):
    def prep(self, shared):
        return shared.get('repo_root')

    def exec(self, repo_root):
        if not repo_root:
            return 'default'
        repo = Path(repo_root)
        if not (repo / '.git').exists() or shutil.which('gh') is None:
            return 'default'
        branch = f"journal-{datetime.now().strftime('%Y%m%d')}"
        subprocess.run(['git', 'checkout', '-b', branch], cwd=repo)
        subprocess.run(['git', 'push', '-u', 'origin', branch], cwd=repo)
        result = subprocess.run(['gh', 'pr', 'create', '--fill'], cwd=repo, capture_output=True, text=True)
        if result.returncode == 0:
            url = result.stdout.strip().splitlines()[-1]
            (repo / '.last_pr_url').write_text(url)
        return 'default'

