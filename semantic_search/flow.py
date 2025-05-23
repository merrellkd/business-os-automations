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


# ---------------------------------------------------------------------------
# Query flow builders
# ---------------------------------------------------------------------------


def create_simple_search_flow() -> Flow:
    """Return a flow performing semantic retrieval followed by LLM processing."""

    search = nodes.SemanticSearchNode()
    llm = nodes.LLMProcessorNode()
    out = nodes.OutputFormatterNode()

    search >> llm >> out
    return Flow(search)


def create_temporal_flow() -> Flow:
    """Flow for queries with temporal components."""

    temporal = nodes.TemporalMapperNode()
    llm = nodes.LLMProcessorNode()
    out = nodes.OutputFormatterNode()

    temporal >> llm >> out
    return Flow(temporal)


def create_agent_flow() -> Flow:
    """Flow that delegates reasoning to an orchestrated agent."""

    agent = nodes.AgentOrchestratorNode()
    llm = nodes.LLMProcessorNode()
    out = nodes.OutputFormatterNode()

    agent >> llm >> out
    return Flow(agent)


def create_query_flow() -> Flow:
    """Top-level flow that routes the query to one of the specialised flows."""

    router = nodes.QueryRouterNode()

    simple = create_simple_search_flow()
    temporal = create_temporal_flow()
    agent = create_agent_flow()

    router - "simple" >> simple
    router - "temporal" >> temporal
    router - "summary" >> temporal
    router - "agent" >> agent

    router >> simple  # default route

    return Flow(router)


