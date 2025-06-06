from pathlib import Path
from datetime import datetime
import subprocess
import logging
import time
from pocketflow import Node
from journal_daily_setup.utils.fs_utils import (
    ensure_dir,
    move_folder,
    create_file,
    github_pr_link,
)

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
        logging.debug(f"Scanning {root} for folders to archive (excluding '{today}')")
        folders = [d for d in root.iterdir() if d.is_dir() and d.name not in ('archive', today)]
        logging.info(f"Found {len(folders)} folder(s) to archive")
        return folders

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
            logging.info(f"Archiving {folder} to {archive_path}")
            move_folder(folder, archive_path)
            moved.append(str(archive_path))
        if moved:
            shared['archived_paths'] = moved
            logging.debug(f"Archived paths: {moved}")
        return 'default'

class CreateTodayFolder(Node):
    def prep(self, shared):
        root = Path(shared['journal_root'])
        today = datetime.now()
        folder_name = today.strftime('%Y-%m-%d-%a').lower()
        shared['today_folder'] = folder_name
        logging.info(f"Today's folder: {folder_name}")
        return root / folder_name

    def exec(self, folder_path: Path):
        ensure_dir(folder_path)
        logging.debug(f"Ensured directory {folder_path}")
        return folder_path

    def post(self, shared, prep_res, exec_res):
        shared['today_path'] = str(exec_res)
        logging.info(f"Created today's folder at {exec_res}")
        return 'default'

class CreateJournalFile(Node):
    def prep(self, shared):
        date_str = shared['today_folder']
        folder_path = Path(shared['today_path'])
        file_path = folder_path / f"{date_str}.journal.md"
        pr_url = shared.get('pr_url')
        branch = shared.get('branch_name')
        repo_root = shared.get('repo_root', '.')

        # Attempt to build a direct link to the GitHub PR page if we have a
        # branch but no PR URL yet.  This mirrors TypeScript's approach of
        # gathering all necessary data up front in a "prep" step.
        pr_create_link = None
        if branch and not pr_url:
            pr_create_link = github_pr_link(Path(repo_root), branch)

        logging.debug(f"Preparing journal file {file_path}")
        return file_path, date_str, pr_url, branch, pr_create_link

    def exec(self, data):
        file_path, date_str, pr_url, branch, pr_create_link = data
        content = JOURNAL_TEMPLATE.format(date=date_str)
        if pr_url:
            content += f"\n\n## Tasks\n- [ ] Review yesterday's PR: {pr_url}\n"
        elif branch:
            # When no PR URL exists we either link directly to GitHub's
            # "new pull request" page or fall back to plain text.
            if pr_create_link:
                content += (
                    f"\n\n## Tasks\n- [ ] "
                    f"[Create PR for branch: {branch}]({pr_create_link})\n"
                )
            else:
                content += f"\n\n## Tasks\n- [ ] Create PR for branch: {branch}\n"
        create_file(file_path, content)
        logging.info(f"Created journal file at {file_path}")
        return file_path


class CommitChanges(Node):
    """Commit archived folders if Git is enabled."""

    def prep(self, shared):
        paths = shared.get('archived_paths', [])
        enable = shared.get('enable_git', False)
        repo_root = shared.get('repo_root', '.')
        branch = None
        if enable and paths:
            date_str = datetime.now().strftime('%Y-%m-%d')
            branch = f'journal-{date_str}'
            shared['branch_name'] = branch
        logging.debug(f"Paths to commit: {paths} in repo {repo_root}")
        return paths, enable, repo_root, branch

    def exec(self, data):
        paths, enable, repo_root, branch = data
        if not enable or not paths:
            logging.info("No changes to commit or git disabled")
            return None
        try:
            subprocess.run(['git', 'checkout', '-b', branch], check=True, cwd=repo_root)
            subprocess.run(['git', 'add', '--'] + paths, check=True, cwd=repo_root)
            subprocess.run(['git', 'commit', '-m', 'Archive previous journal'], check=True, cwd=repo_root)
            sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True, cwd=repo_root).strip()
            logging.info(f"Committed changes with SHA {sha} on branch {branch}")
            return sha
        except Exception:
            logging.exception("Git commit failed")
            subprocess.run(['git', 'checkout', '-'], check=False, cwd=repo_root)
            return None

    def post(self, shared, prep_res, exec_res):
        if exec_res:
            shared['commit_sha'] = exec_res
            logging.debug(f"Stored commit SHA {exec_res}")
            return 'committed'
        return 'no_changes'


class CreatePullRequest(Node):
    """Open a pull request for the archived changes."""

    def prep(self, shared):
        if not shared.get('enable_git') or not shared.get('commit_sha'):
            return None
        branch = shared.get('branch_name')
        repo_root = shared.get('repo_root', '.')
        return branch, repo_root

    def exec(self, data):
        if not data:
            logging.info("No commit found, skipping PR creation")
            return None
        branch, repo_root = data
        try:
            subprocess.run(['git', 'push', '-u', 'origin', branch], check=True, cwd=repo_root)
            
            # Small delay to let GitHub process the branch
            time.sleep(2)
            pr = subprocess.run(
                ['gh', 'pr', 'create', '--fill'],
                capture_output=True,
                text=True,
                cwd=repo_root,
            )
            output = pr.stdout.strip().splitlines()
            url = output[-1] if output else ''
            logging.info(f"Created pull request {url}")
            return url
        except Exception:
            logging.exception("Failed to create pull request")
            return None
        finally:
            subprocess.run(['git', 'checkout', '-'], check=False, cwd=repo_root)

    def post(self, shared, prep_res, exec_res):
        if exec_res:
            shared['pr_url'] = exec_res
            logging.debug(f"Stored PR URL {exec_res}")
            return 'created'
        return 'skipped'

