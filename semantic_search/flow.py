"""Flow orchestration for the semantic search system.

This module defines helper functions to build PocketFlow flows.  The
functions here assemble the indexing nodes from ``nodes.py`` into a
complete process.  Everything is documented with newcomers to Python
and PocketFlow in mind.
"""

from __future__ import annotations

from typing import Any, Dict
import logging

from pocketflow import Flow

from . import nodes

logger = logging.getLogger(__name__)


def create_indexing_flow() -> Flow:
    """Return a PocketFlow ``Flow`` that performs all indexing steps."""

    scan = nodes.ScanFilesNode()
    filt = nodes.FilterRelevantNode()
    chunk = nodes.ChunkDocumentsNode()
    embed = nodes.GenerateEmbeddingsNode()
    vect = nodes.UpdateVectorDBNode()
    meta = nodes.UpdateMetadataDBNode()

    # Connect nodes in a linear sequence using PocketFlow's ``>>`` operator.
    scan >> filt >> chunk >> embed >> vect >> meta

    return Flow(scan)


def run_full_index(shared: Dict[str, Any]) -> None:
    """Convenience wrapper that executes the full indexing flow."""

    flow = create_indexing_flow()
    flow.run(shared)


def run_incremental_index(shared: Dict[str, Any]) -> None:
    """Placeholder for incremental indexing.

    A real implementation would examine which files changed since the
    last run.  Here we simply delegate to ``run_full_index`` for
    demonstration purposes.
    """

    run_full_index(shared)

