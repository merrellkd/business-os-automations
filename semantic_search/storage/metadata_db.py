import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Iterable, Tuple, List, Dict, Optional

# Schema definition for SQLite database. We store file information and text
# chunks. Each chunk references the file it belongs to.
SCHEMA = """
CREATE TABLE IF NOT EXISTS files(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE,
    size INTEGER,
    mtime REAL
);

CREATE TABLE IF NOT EXISTS chunks(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id INTEGER,
    chunk_index INTEGER,
    text TEXT,
    FOREIGN KEY(file_id) REFERENCES files(id)
);
"""


def init_db(db_path: str) -> sqlite3.Connection:
    """Create a SQLite database and required tables.

    Parameters
    ----------
    db_path: str
        Path to the SQLite database file.

    Returns
    -------
    sqlite3.Connection
        Connection object to the initialized database.
    """
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def add_file_metadata(conn: sqlite3.Connection, path: str, size: int, mtime: float) -> int:
    """Insert or update file metadata.

    The function returns the database ID for the file. If the file already
    exists in the database, its ID is returned without modification.
    """
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO files(path, size, mtime) VALUES (?, ?, ?)",
        (path, size, mtime),
    )
    conn.commit()
    cur.execute("SELECT id FROM files WHERE path = ?", (path,))
    file_id = cur.fetchone()[0]
    return file_id


def add_chunk_metadata(
    conn: sqlite3.Connection,
    file_id: int,
    chunk_index: int,
    text: str,
) -> int:
    """Store chunk text for a given file.

    Parameters
    ----------
    conn : sqlite3.Connection
        Database connection.
    file_id : int
        ID of the parent file from the `files` table.
    chunk_index : int
        Sequential index of the chunk within the file.
    text : str
        Text content of the chunk.

    Returns
    -------
    int
        ID of the inserted chunk.
    """
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO chunks(file_id, chunk_index, text) VALUES (?, ?, ?)",
        (file_id, chunk_index, text),
    )
    conn.commit()
    return cur.lastrowid


def query_by_date_range(
    conn: sqlite3.Connection,
    start: datetime,
    end: datetime,
) -> List[Dict[str, Optional[str]]]:
    """Retrieve files modified within the specified date range."""
    cur = conn.cursor()
    cur.execute(
        "SELECT id, path, size, mtime FROM files WHERE mtime BETWEEN ? AND ?",
        (start.timestamp(), end.timestamp()),
    )
    rows = cur.fetchall()
    return [
        {
            "id": r[0],
            "path": r[1],
            "size": r[2],
            "mtime": r[3],
        }
        for r in rows
    ]


def get_chunk_by_id(conn: sqlite3.Connection, chunk_id: int) -> Optional[str]:
    """Return the text of a chunk by its ID."""
    cur = conn.cursor()
    cur.execute("SELECT text FROM chunks WHERE id = ?", (chunk_id,))
    row = cur.fetchone()
    return row[0] if row else None
