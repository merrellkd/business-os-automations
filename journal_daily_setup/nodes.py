from pathlib import Path
from datetime import datetime
import subprocess
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
        moved = []
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
            moved.append(str(archive_path))
        if moved:
            shared['archived_paths'] = moved
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
        pr_url = shared.get('pr_url')
        return file_path, date_str, pr_url

    def exec(self, data):
        file_path, date_str, pr_url = data
        content = JOURNAL_TEMPLATE.format(date=date_str)
        if pr_url:
            content += f"\n\n## Tasks\n- [ ] Review yesterday's PR: {pr_url}\n"
        create_file(file_path, content)
        return file_path


class CommitChanges(Node):
    """Commit archived folders if Git is enabled."""

    def prep(self, shared):
        paths = shared.get('archived_paths', [])
        return paths, shared.get('enable_git', False)

    def exec(self, data):
        paths, enable = data
        if not enable or not paths:
            return None
        try:
            subprocess.run(['git', 'add', '--'] + paths, check=True)
            subprocess.run(['git', 'commit', '-m', 'Archive previous journal'], check=True)
            sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
            return sha
        except Exception:
            return None

    def post(self, shared, prep_res, exec_res):
        if exec_res:
            shared['commit_sha'] = exec_res
            return 'committed'
        return 'no_changes'


class CreatePullRequest(Node):
    """Open a pull request for the archived changes."""

    def prep(self, shared):
        if not shared.get('enable_git'):
            return None
        sha = shared.get('commit_sha')
        if not sha:
            return None
        date_str = datetime.now().strftime('%Y-%m-%d')
        branch = f'journal-{date_str}'
        return branch

    def exec(self, branch):
        if not branch:
            return None
        try:
            subprocess.run(['git', 'checkout', '-b', branch], check=True)
            subprocess.run(['git', 'push', '-u', 'origin', branch], check=True)
            pr = subprocess.run(['gh', 'pr', 'create', '--fill'], capture_output=True, text=True)
            url = pr.stdout.strip()
            return url
        except Exception:
            return None
        finally:
            subprocess.run(['git', 'checkout', '-'], check=False)

    def post(self, shared, prep_res, exec_res):
        if exec_res:
            shared['pr_url'] = exec_res
            return 'created'
        return 'skipped'

