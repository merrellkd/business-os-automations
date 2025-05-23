from __future__ import annotations

"""File system utilities for the semantic search project.

This module focuses on scanning directories, reading files, and extracting
basic metadata.  Each function contains detailed comments aimed at developers
coming from a TypeScript background who may be new to Python.
"""

from pathlib import Path
import subprocess
from typing import Dict, List, Iterable


def apply_gitignore(files: Iterable[Path], root_path: Path) -> List[Path]:
    """Filter out files ignored by git.

    Parameters
    ----------
    files:
        An iterable of ``Path`` objects to check.
    root_path:
        The root of the project containing the ``.git`` directory.

    Returns
    -------
    List[Path]
        Only files that are not ignored by git.
    """
    filtered: List[Path] = []
    for file in files:
        try:
            # ``git check-ignore`` exits with code 0 when the file is ignored.
            subprocess.run(
                ["git", "check-ignore", str(file)],
                cwd=root_path,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            # If the command succeeded, the file is ignored.
        except subprocess.CalledProcessError:
            # Non-zero exit means the file is *not* ignored.
            filtered.append(file)
        except FileNotFoundError:
            # Git is not installed or repo not initialised; include file anyway.
            filtered.append(file)
    return filtered


def scan_directory(root_path: str, extensions: List[str]) -> List[Path]:
    """Recursively scan ``root_path`` for files matching ``extensions``.

    Parameters
    ----------
    root_path:
        Directory to search.
    extensions:
        List of file extensions to include, e.g. ``['.md', '.py']``.
    Returns
    -------
    List[Path]
        Absolute paths of discovered files.
    """
    root = Path(root_path)
    all_files = [p for p in root.rglob("*") if p.suffix in extensions and p.is_file()]
    return apply_gitignore(all_files, root)


def get_file_metadata(file_path: str) -> Dict[str, object]:
    """Collect basic metadata for a file including git information."""
    p = Path(file_path)
    stat = p.stat()
    metadata = {
        "path": str(p),
        "size": stat.st_size,
        "modified": stat.st_mtime,
    }
    try:
        last_commit = subprocess.check_output(
            ["git", "log", "-1", "--format=%cI", str(p)],
            cwd=p.parent,
            text=True,
        ).strip()
        metadata["git_last_commit"] = last_commit
    except Exception:
        # File may not be tracked or git unavailable.
        metadata["git_last_commit"] = None
    return metadata


def read_file_content(file_path: str) -> str:
    """Read text from ``file_path`` with UTF-8 fallback."""
    p = Path(file_path)
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # For encodings other than UTF-8 we ignore errors rather than fail.
        return p.read_text(encoding="utf-8", errors="ignore")

