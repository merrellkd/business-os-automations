"""PocketFlow nodes for the semantic search indexing and query flows.

Each node focuses on a single responsibility and is heavily commented to
help developers familiar with TypeScript learn how Python and PocketFlow
work together.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List
import logging
from pathlib import Path
from datetime import datetime

from .utils import llm_utils

from pocketflow import Node, Flow
from semantic_search.utils import llm_utils

# Utility modules from this package
from .utils import fs_utils, embedding_utils, query_utils
from .storage import faiss_manager, metadata_db


logger = logging.getLogger(__name__)


class ScanFilesNode(Node):
    """Gather file information for indexing."""

    def prep(self, shared: Dict[str, Any]):
        config = shared.get("config", {})
        root = config.get("root_path", ".")
        exts = config.get("file_extensions", [".md", ".txt"])
        return str(root), exts

    def exec(self, prep_res):
        root, exts = prep_res
        files = fs_utils.scan_directory(root, exts)
        meta = [fs_utils.get_file_metadata(str(f)) for f in files]
        return meta

    def post(self, shared, prep_res, exec_res):
        shared.setdefault("indexing", {})["files_to_index"] = exec_res
        return "default"


class FilterRelevantNode(Node):
    """Apply simple filtering rules to discovered files."""

    def prep(self, shared):
        indexing = shared.setdefault("indexing", {})
        files: List[Dict[str, Any]] = indexing.get("files_to_index", [])
        return files

    def exec(self, files: List[Dict[str, Any]]):
        filtered: List[Dict[str, Any]] = []
        for meta in files:
            # Example rule: ignore files larger than 1MB
            if meta.get("size", 0) < 1_000_000:
                filtered.append(meta)
        return filtered

    def post(self, shared, prep_res, exec_res):
        shared["indexing"]["filtered_files"] = exec_res
        return "default"


class ChunkDocumentsNode(Node):
    """Read filtered files and split them into chunks."""

    def prep(self, shared):
        files = shared.get("indexing", {}).get("filtered_files", [])
        return files

    def exec(self, files: List[Dict[str, Any]]):
        chunks: List[Dict[str, Any]] = []
        for meta in files:
            path = meta["path"]
            text = fs_utils.read_file_content(path)
            file_chunks = query_utils.chunk_text(text, Path(path).suffix)
            for idx, ch in enumerate(file_chunks):
                chunks.append(
                    {
                        "path": path,
                        "size": meta.get("size"),
                        "mtime": meta.get("modified", meta.get("mtime")),
                        "chunk_index": idx,
                        "text": ch["text"] if isinstance(ch, dict) else ch,
                    }
                )
        return chunks

    def post(self, shared, prep_res, exec_res):
        shared["indexing"]["chunks"] = exec_res
        return "default"


class GenerateEmbeddingsNode(Node):
    """Create embeddings for each text chunk."""

    def prep(self, shared):
        config = shared.get("config", {})
        model = config.get("embedding_model", "nomic-embed-text")
        chunks = shared.get("indexing", {}).get("chunks", [])
        texts = [c["text"] for c in chunks]
        return model, texts

    def exec(self, prep_res):
        model, texts = prep_res
        vectors = embedding_utils.generate_embeddings(texts, model=model, use_fallback=True)
        return vectors

    def post(self, shared, prep_res, exec_res):
        shared["indexing"]["embeddings"] = exec_res
        return "default"


class UpdateVectorDBNode(Node):
    """Persist embeddings to the vector store."""

    def prep(self, shared):
        embeddings = shared.get("indexing", {}).get("embeddings", [])
        config = shared.get("config", {})
        index_path = config.get("index_path", "semantic_index.pkl")
        return embeddings, index_path

    def exec(self, prep_res):
        embeddings, index_path = prep_res
        if Path(index_path).exists():
            index = faiss_manager.load_index(index_path)
        else:
            index = faiss_manager.init_index(len(embeddings[0]) if embeddings else embedding_utils.EMBEDDING_DIMENSION)
        start_id = len(index.get("ids", []))
        ids = list(range(start_id, start_id + len(embeddings)))
        faiss_manager.add_vectors(index, embeddings, ids)
        faiss_manager.save_index(index, index_path)
        return True

    def post(self, shared, prep_res, exec_res):
        shared["indexing"]["index_updated"] = exec_res
        return "default"


class UpdateMetadataDBNode(Node):
    """Store file and chunk information in SQLite."""

    def prep(self, shared):
        chunks = shared.get("indexing", {}).get("chunks", [])
        config = shared.get("config", {})
        db_path = config.get("metadata_path", "metadata.db")
        return chunks, db_path

    def exec(self, prep_res):
        chunks, db_path = prep_res
        conn = metadata_db.init_db(db_path)
        for chunk in chunks:
            file_id = metadata_db.add_file_metadata(
                conn,
                chunk["path"],
                chunk.get("size", 0),
                float(chunk.get("mtime") or 0.0),
            )
            metadata_db.add_chunk_metadata(
                conn, file_id, chunk["chunk_index"], chunk["text"]
            )
        conn.close()
        return True

    def post(self, shared, prep_res, exec_res):
        shared["indexing"]["metadata_updated"] = exec_res
        return "default"

# Add these nodes to your nodes.py file


# ---------------------------------------------------------------------------
# Query flow nodes (Track E)
# ---------------------------------------------------------------------------

    

class QueryRouterNode(Node):
    """Classify the user's query and route to the appropriate sub-flow."""

    def prep(self, shared: Dict[str, Any]):
        return shared.get("query", {}).get("query", "")

    def exec(self, query: str) -> str:
        return query_utils.classify_query(query)

    def post(self, shared: Dict[str, Any], prep_res, exec_res: str) -> str:
        shared.setdefault("query", {})["query_type"] = exec_res
        # Return "default" instead of the query type to avoid routing issues
        # The query type is stored in shared state for other nodes to use
        return "default"



class SemanticSearchNode(Node):
    """Retrieve similar chunks from the vector store."""

    def prep(self, shared: Dict[str, Any]):
        q = shared.get("query", {}).get("query", "")
        cfg = shared.get("config", {})
        index_path = cfg.get("index_path", "semantic_index.pkl")
        db_path = cfg.get("metadata_path", "metadata.db")
        model = cfg.get("embedding_model", "nomic-embed-text")
        print(f"🔍 SemanticSearch prep: query='{q}', index_path='{index_path}'")
        return q, index_path, db_path, model

    def exec(self, prep_res):
        query, index_path, db_path, model = prep_res
        print(f"🔍 SemanticSearch exec: Generating embedding for '{query[:30]}...'")
        
        # Generate an embedding for the query text.
        vec = embedding_utils.generate_embeddings([query], model=model, use_fallback=True)[0]
        print(f"🔍 SemanticSearch exec: Generated {len(vec)}-dim embedding")
        
        if not Path(index_path).exists():
            print(f"❌ SemanticSearch exec: Index file not found at {index_path}")
            return []
        
        index = faiss_manager.load_index(index_path)
        print(f"🔍 SemanticSearch exec: Loaded index with {len(index.get('ids', []))} vectors")
        
        ids, scores = faiss_manager.search(index, vec, k=5)
        print(f"🔍 SemanticSearch exec: Found {len(ids)} matches with scores {scores[:3]}...")
        
        # Retrieve the original text for each matching chunk from SQLite.
        conn = metadata_db.init_db(db_path)
        results: List[Dict[str, Any]] = []
        for idx, score in zip(ids, scores):
            # Note: FAISS returns 0-based IDs, but SQLite chunk IDs are 1-based
            chunk_id = idx + 1
            text = metadata_db.get_chunk_by_id(conn, chunk_id)
            print(f"🔍 SemanticSearch exec: Chunk {chunk_id} -> {len(text) if text else 0} chars")
            results.append({"id": idx, "score": score, "text": text})
        conn.close()
        
        print(f"🔍 SemanticSearch exec: Returning {len(results)} results")
        return results

    def post(self, shared: Dict[str, Any], prep_res, exec_res):
        shared.setdefault("query", {})["search_results"] = exec_res
        print(f"🔍 SemanticSearch post: Stored {len(exec_res)} search results")
        return "default"


class TemporalMapperNode(Node):
    """Find files matching temporal constraints in the query."""

    def prep(self, shared: Dict[str, Any]):
        query = shared.get("query", {}).get("query", "")
        db_path = shared.get("config", {}).get("metadata_path", "metadata.db")
        return query, db_path

    def exec(self, prep_res):
        query, db_path = prep_res
        markers = query_utils.extract_temporal_markers(query)
        start = markers.get("start") or datetime.fromtimestamp(0)
        end = markers.get("end") or datetime.now()
        conn = metadata_db.init_db(db_path)
        files = metadata_db.query_by_date_range(conn, start, end)
        conn.close()
        return files

    def post(self, shared: Dict[str, Any], prep_res, exec_res):
        shared.setdefault("query", {})["temporal_files"] = exec_res
        return "default"


class AgentOrchestratorNode(Node):
    """Simplified agent that could perform multi-step reasoning."""

    def prep(self, shared: Dict[str, Any]):
        query = shared.get("query", {}).get("query", "")
        context = shared.get("query", {}).get("search_results", [])
        return query, context

    def exec(self, prep_res):
        query, context = prep_res
        # In this simplified example we just package the context for the LLM.
        return {"query": query, "context": context}

    def post(self, shared: Dict[str, Any], prep_res, exec_res):
        shared.setdefault("query", {})["agent_results"] = exec_res
        return "default"



class LLMProcessorNode(Node):
    """Send gathered context to the language model."""

    def prep(self, shared: Dict[str, Any]):
        cfg = shared.get("config", {})
        provider = cfg.get("llm_provider", "ollama")
        model = cfg.get("llm_model", "llama2")
        results = shared.get("query", {}).get("search_results", [])
        agent = shared.get("query", {}).get("agent_results")
        query = shared.get("query", {}).get("query", "")
        
        print(f"🤖 LLMProcessor prep: provider={provider}, model={model}")
        print(f"🤖 LLMProcessor prep: {len(results)} search results")
        
        return query, results, agent, provider, model

    def exec(self, prep_res):
        query, results, agent, provider, model = prep_res
        
        # Extract text chunks
        chunks = [r.get("text", "") for r in results if r.get("text")]
        print(f"🤖 LLMProcessor exec: {len(chunks)} text chunks extracted")
        
        if agent:
            extra = agent.get("context", [])
            if isinstance(extra, list):
                chunks.extend(str(e) for e in extra)
        
        if not chunks:
            print("⚠️ LLMProcessor exec: No chunks found for context!")
            return "No relevant context found to answer the query."
        
        context = llm_utils.format_context(chunks)
        prompt = f"Question: {query}\n\nContext:\n{context}\n\nAnswer:"
        
        print(f"🤖 LLMProcessor exec: Calling {provider} with prompt length {len(prompt)}")
        print(f"🤖 LLMProcessor exec: Context preview: {context[:200]}...")
        
        response = llm_utils.call_llm(prompt, model=model, provider=provider)
        print(f"🤖 LLMProcessor exec: Got response length {len(response)}")
        print(f"🤖 LLMProcessor exec: Response preview: '{response[:100]}...'")
        
        return response

    def post(self, shared: Dict[str, Any], prep_res, exec_res):
        shared.setdefault("query", {})["llm_response"] = exec_res
        print(f"🤖 LLMProcessor post: Stored response of length {len(exec_res)}")
        return "default"
    
class OutputFormatterNode(Node):
    """Final node that formats and stores the LLM output."""

    def prep(self, shared: Dict[str, Any]):
        response = shared.get("query", {}).get("llm_response", "")
        cfg = shared.get("config", {})
        fmt = cfg.get("output_format", "chat")
        path = shared.get("query", {}).get("output_path", "output.txt")
        
        # Debug logging
        print(f"📝 OutputFormatter prep: Response length: {len(response)}")
        print(f"📝 OutputFormatter prep: Response preview: {response[:100]}...")
        
        return response, fmt, path

    def exec(self, prep_res):
        response, fmt, path = prep_res
        if fmt == "file":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_text(response)
            result = f"Response written to: {path}"
        else:
            result = response
        
        print(f"📝 OutputFormatter exec: Final result length: {len(result)}")
        print(f"📝 OutputFormatter exec: Final result preview: {result[:100]}...")
        return result

    def post(self, shared: Dict[str, Any], prep_res, exec_res):
        # Set both keys to be safe
        shared.setdefault("query", {})["result"] = exec_res
        shared.setdefault("query", {})["final_output"] = exec_res
        print(f"📝 OutputFormatter post: Stored final output of length {len(exec_res)}")
        return "default"
