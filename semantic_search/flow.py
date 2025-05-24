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

# Add these functions to your flow.py file

def create_simple_search_flow() -> Flow:
    """Return a PocketFlow that handles basic semantic search queries."""
    
    # Skip the router for now since it's causing issues
    # router = nodes.QueryRouterNode()
    search = nodes.SemanticSearchNode()
    llm = nodes.LLMProcessorNode()
    output = nodes.OutputFormatterNode()
    
    # Simple linear flow for basic queries
    search >> llm >> output
    
    return Flow(search)


def create_temporal_flow() -> Flow:
    """Return a PocketFlow that handles time-based queries."""
    
    router = nodes.QueryRouterNode()
    temporal = nodes.TemporalMapperNode()
    search = nodes.SemanticSearchNode()
    llm = nodes.LLMProcessorNode()
    output = nodes.OutputFormatterNode()
    
    # Route through temporal mapping first
    router >> temporal >> search >> llm >> output
    
    return Flow(router)


def create_query_flow() -> Flow:
    """Return a unified query flow that routes based on query type."""
    
    # For now, use the simple search flow as the main entry point
    # In a more complex implementation, this would use conditional routing
    return create_simple_search_flow()


def run_query(shared: Dict[str, Any]) -> str:
    """Convenience wrapper that executes a query flow and returns the result."""
    
    query_type = shared.get("query", {}).get("query_type", "simple")
    
    if query_type == "temporal":
        flow = create_temporal_flow()
    else:
        flow = create_simple_search_flow()
    
    flow.run(shared)
    
    # Check multiple possible locations for the result
    result = (
        shared.get("query", {}).get("final_output") or
        shared.get("query", {}).get("result") or  # This is what OutputFormatterNode sets
        shared.get("query", {}).get("llm_response") or
        "No response generated"
    )
    
    return result


# Helper function for testing
def run_test_query(query_text: str, config: Dict[str, Any]) -> str:
    """Run a single query for testing purposes."""
    
    shared = {
        "config": config,
        "query": {
            "query": query_text
        }
    }
    
    return run_query(shared)

def run_test_query_debug(query_text: str, config: Dict[str, Any]) -> str:
    """Debug version that shows what happens at each step."""
    
    shared = {
        "config": config,
        "query": {
            "query": query_text
        }
    }
    
    print(f"\n🔍 Debug: Starting query '{query_text}'")
    print(f"📊 Initial shared state: {list(shared.keys())}")
    
    # Create and run the flow
    query_type = shared.get("query", {}).get("query_type", "simple")
    print(f"🎯 Query type: {query_type}")
    
    if query_type == "temporal":
        flow = create_temporal_flow()
    else:
        flow = create_simple_search_flow()
    
    print(f"🔧 Created flow successfully")
    
    try:
        flow.run(shared)
        print(f"✅ Flow completed")
    except Exception as e:
        print(f"❌ Flow failed: {e}")
        import traceback
        traceback.print_exc()
        return f"Flow error: {e}"
    
    # Check what we have in shared state after flow
    print(f"📊 Final shared state keys: {list(shared.keys())}")
    if "query" in shared:
        print(f"🔍 Query keys: {list(shared['query'].keys())}")
        for key, value in shared["query"].items():
            if isinstance(value, str):
                print(f"   {key}: '{value[:100]}...' (len={len(value)})")
            else:
                print(f"   {key}: {type(value)} with {len(value) if hasattr(value, '__len__') else 'N/A'} items")
    
    result = shared.get("query", {}).get("final_output", "No response generated")
    print(f"🎯 Final result: '{result}' (len={len(result)})")
    return result
