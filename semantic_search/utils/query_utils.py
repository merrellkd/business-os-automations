"""Utility functions for processing user queries and text.

These helpers are intentionally lightweight and heavily commented so that
developers familiar with TypeScript can quickly understand the Python
implementation.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional


def chunk_text(text: str, file_type: str) -> List[Dict[str, str]]:
    """Break ``text`` into smaller pieces for embedding.

    Parameters
    ----------
    text:
        The full text of the document.
    file_type:
        A string representing the file extension (``'.md'``, ``'.py'``, etc.).

    Returns
    -------
    List[Dict[str, str]]
        Each dict contains ``id`` and ``text`` keys.
    """
    chunks: List[Dict[str, str]] = []

    if file_type in {".py", ".js", ".ts"}:
        # For code we keep line structure intact but limit to ~20 lines per chunk.
        lines = text.splitlines()
        for i in range(0, len(lines), 20):
            chunk_lines = lines[i : i + 20]
            chunk_text = "\n".join(chunk_lines)
            chunks.append({"id": str(i // 20), "text": chunk_text})
    else:
        # For markdown or plain text we split on blank lines.
        parts = re.split(r"\n{2,}", text)
        for idx, part in enumerate(parts):
            cleaned = part.strip()
            if cleaned:
                chunks.append({"id": str(idx), "text": cleaned})
    return chunks


def classify_query(query: str) -> str:
    """Very small heuristic to decide how a query should be handled."""
    q = query.lower()
    if any(word in q for word in ["yesterday", "last", "today", "days"]):
        return "temporal"
    if any(word in q for word in ["summarize", "summary"]):
        return "summary"
    return "simple"


def extract_temporal_markers(query: str) -> Dict[str, Optional[datetime]]:
    """Parse common time references from a query string."""
    now = datetime.now()
    q = query.lower()
    # Default to no restriction
    start: Optional[datetime] = None
    end: Optional[datetime] = None

    # Examples: "last 7 days", "past 3 day"
    m = re.search(r"last\s+(\d+)\s+day", q)
    if m:
        days = int(m.group(1))
        start = now - timedelta(days=days)
        end = now
    elif "yesterday" in q:
        start = now - timedelta(days=1)
        end = start
    elif "today" in q:
        start = now
        end = now

    return {"start": start, "end": end}


def build_metadata_filters(query: str) -> Dict[str, object]:
    """Convert a query into filter arguments for the metadata store."""
    temporal = extract_temporal_markers(query)
    filters: Dict[str, object] = {}
    if temporal["start"]:
        filters["start_date"] = temporal["start"].date().isoformat()
    if temporal["end"]:
        filters["end_date"] = temporal["end"].date().isoformat()
    # Additional heuristics could be added here
    return filters
