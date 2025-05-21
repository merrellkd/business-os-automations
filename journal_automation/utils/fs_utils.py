from pathlib import Path
import shutil

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
