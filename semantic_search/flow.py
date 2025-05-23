"""PocketFlow flows assembling the query nodes."""

from __future__ import annotations

from pocketflow import Flow

from .nodes import (
    QueryRouterNode,
    SemanticSearchNode,
    TemporalMapperNode,
    AgentOrchestratorNode,
    LLMProcessorNode,
    OutputFormatterNode,
)


def create_simple_search_flow() -> Flow:
    """Flow for a basic semantic search query."""
    router = QueryRouterNode()
    search = SemanticSearchNode()
    llm = LLMProcessorNode()
    out = OutputFormatterNode()

    router >> search >> llm >> out
    return Flow(start=router)


def create_temporal_flow() -> Flow:
    """Flow dedicated to time-based queries."""
    router = QueryRouterNode()
    temporal = TemporalMapperNode()
    llm = LLMProcessorNode()
    out = OutputFormatterNode()

    router >> temporal >> llm >> out
    return Flow(start=router)


def create_agent_flow() -> Flow:
    """Flow that delegates retrieval planning to an agent."""
    router = QueryRouterNode()
    agent = AgentOrchestratorNode()
    llm = LLMProcessorNode()
    out = OutputFormatterNode()

    router >> agent >> llm >> out
    return Flow(start=router)


def create_query_flow() -> Flow:
    """Composite flow routing to specialised sub-flows based on the query."""
    router = QueryRouterNode()
    semantic = SemanticSearchNode()
    temporal = TemporalMapperNode()
    agent = AgentOrchestratorNode()
    llm = LLMProcessorNode()
    out = OutputFormatterNode()

    router - "simple" >> semantic
    router - "temporal" >> temporal
    router - "summary" >> agent
    router >> semantic

    semantic >> llm
    temporal >> llm
    agent >> llm
    llm >> out

    return Flow(start=router)

