from pathlib import Path
import shutil
import subprocess

def ensure_dir(path: Path) -> None:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)

def move_folder(src: Path, dst: Path) -> None:
    """Move entire folder to destination."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))

def create_file(path: Path, content: str = "") -> None:
    """Create file with given content if it does not already exist."""
    if not path.exists():
        path.write_text(content)

def github_pr_link(repo_root: Path, branch: str) -> str | None:
    """Return a web URL for creating a pull request on GitHub.

    The function inspects the Git remote named ``origin`` in ``repo_root`` and
    attempts to build a link of the form:
    ``https://github.com/<owner>/<repo>/pull/new/<branch>``.

    If the repository is not hosted on GitHub or the remote cannot be
    determined, ``None`` is returned instead.  The return type uses
    ``| None`` (Python's union syntax) which is similar to ``null`` in
    TypeScript.
    """
    try:
        # ``git remote get-url origin`` gives us the remote location
        # e.g. ``git@github.com:owner/repo.git`` or
        # ``https://github.com/owner/repo.git``.
        remote = subprocess.check_output(
            ["git", "remote", "get-url", "origin"],
            text=True,
            cwd=repo_root,
        ).strip()

        # Normalize the remote string into ``owner/repo``.  The logic is
        # intentionally verbose with comments for clarity.
        if remote.endswith(".git"):
            remote = remote[:-4]

        if remote.startswith("git@"):
            # Convert ``git@github.com:owner/repo`` into ``github.com/owner/repo``
            remote = remote[4:].replace(":", "/")
        elif remote.startswith("https://"):
            remote = remote[len("https://") :]
        elif remote.startswith("http://"):
            remote = remote[len("http://") :]

        if "github.com/" not in remote:
            return None

        slug = remote.split("github.com/")[-1]
        return f"https://github.com/{slug}/pull/new/{branch}"
    except Exception:
        # If any step fails we simply return ``None`` and the caller can
        # fall back to a non-linked task entry.
        return None
