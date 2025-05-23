"""Core PocketFlow nodes used in the query flow.

Each node mirrors a step in the semantic search process described in
``docs/design.md``.  Extensive comments are provided so a developer with a
TypeScript background can understand both Python and PocketFlow concepts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from pocketflow import Node

from .utils.query_utils import classify_query, extract_temporal_markers
from .utils.embedding_utils import generate_embeddings
from .utils.llm_utils import format_context, call_llm, route_to_provider
from .storage.faiss_manager import search
from .storage.metadata_db import query_by_date_range, get_chunk_by_id


class QueryRouterNode(Node):
    """Classify the user query and route the flow accordingly."""

    def prep(self, shared: Dict[str, Any]) -> str:
        return shared.get("query", {}).get("query", "")

    def exec(self, query: str) -> str:
        return classify_query(query)

    def post(self, shared: Dict[str, Any], prep_res: str, exec_res: str) -> str:
        shared.setdefault("query", {})["query_type"] = exec_res
        return exec_res


class SemanticSearchNode(Node):
    """Perform a vector search against the FAISS index."""

    def prep(self, shared: Dict[str, Any]) -> tuple[str, Any, str]:
        query = shared.get("query", {}).get("query", "")
        index = shared.get("index")
        config = shared.get("config", {})
        model = config.get("embedding_model", "nomic-embed-text")
        return query, index, model

    def exec(self, data: tuple[str, Any, str]) -> List[int]:
        query, index, model = data
        if not index:
            return []
        vector = generate_embeddings([query], model=model)[0]
        ids, _ = search(index, vector, k=5)
        return ids

    def post(
        self,
        shared: Dict[str, Any],
        prep_res: tuple[str, Any, str],
        exec_res: List[int],
    ) -> str:
        shared.setdefault("query", {})["search_results"] = exec_res
        return "default"


class TemporalMapperNode(Node):
    """Map temporal terms in the query to files modified in that range."""

    def prep(self, shared: Dict[str, Any]) -> tuple[str, Any]:
        query = shared.get("query", {}).get("query", "")
        conn = shared.get("metadata_conn")
        return query, conn

    def exec(self, data: tuple[str, Any]) -> List[Dict[str, Any]]:
        query, conn = data
        if not conn:
            return []
        markers = extract_temporal_markers(query)
        start = markers.get("start")
        end = markers.get("end") or start
        if not start or not end:
            return []
        return query_by_date_range(conn, start, end)

    def post(
        self,
        shared: Dict[str, Any],
        prep_res: tuple[str, Any],
        exec_res: List[Dict[str, Any]],
    ) -> str:
        shared.setdefault("query", {})["temporal_files"] = exec_res
        return "default"


class AgentOrchestratorNode(Node):
    """Simplified agent that plans a multi-step retrieval strategy."""

    def prep(self, shared: Dict[str, Any]) -> tuple[str, Any, Any]:
        query = shared.get("query", {}).get("query", "")
        index = shared.get("index")
        conn = shared.get("metadata_conn")
        return query, index, conn

    def exec(self, data: tuple[str, Any, Any]) -> List[int]:
        query, index, conn = data
        results: List[int] = []
        if index:
            vector = generate_embeddings([query])[0]
            ids, _ = search(index, vector, k=5)
            results.extend(ids)
        return results

    def post(
        self,
        shared: Dict[str, Any],
        prep_res: tuple[str, Any, Any],
        exec_res: List[int],
    ) -> str:
        shared.setdefault("query", {})["agent_results"] = exec_res
        return "default"


class LLMProcessorNode(Node):
    """Format retrieved text and send it to the chosen language model."""

    def prep(self, shared: Dict[str, Any]) -> tuple[str, List[str], Dict[str, str]]:
        query_data = shared.setdefault("query", {})
        ids = (
            query_data.get("search_results")
            or query_data.get("agent_results")
            or []
        )
        conn = shared.get("metadata_conn")
        chunks: List[str] = []
        for cid in ids:
            if conn:
                text = get_chunk_by_id(conn, cid)
                if text:
                    chunks.append(text)
        context = format_context(chunks)
        config = shared.get("config", {})
        provider = route_to_provider("low", config.get("llm_provider", "local"))
        prompt = context + "\n\n" + query_data.get("query", "")
        return prompt, chunks, provider

    def exec(self, data: tuple[str, List[str], Dict[str, str]]) -> str:
        prompt, _chunks, provider = data
        return call_llm(prompt, provider.get("model", "llama2"), provider=provider.get("provider", "ollama"))

    def post(
        self,
        shared: Dict[str, Any],
        prep_res: tuple[str, List[str], Dict[str, str]],
        exec_res: str,
    ) -> str:
        shared.setdefault("query", {})["llm_response"] = exec_res
        return "default"


class OutputFormatterNode(Node):
    """Return or save the LLM response depending on configuration."""

    def prep(self, shared: Dict[str, Any]) -> tuple[str, str, Optional[str]]:
        response = shared.get("query", {}).get("llm_response", "")
        config = shared.get("config", {})
        output_format = config.get("output_format", "chat")
        output_path = shared.get("query", {}).get("output_path")
        return response, output_format, output_path

    def exec(self, data: tuple[str, str, Optional[str]]) -> str:
        response, output_format, output_path = data
        if output_format == "file" and output_path:
            Path(output_path).write_text(response)
            return output_path
        return response

    def post(
        self,
        shared: Dict[str, Any],
        prep_res: tuple[str, str, Optional[str]],
        exec_res: str,
    ) -> str:
        return exec_res

