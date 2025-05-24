"""PocketFlow nodes for the semantic search indexing and query flows.

Each node focuses on a single responsibility and is heavily commented to
help developers familiar with TypeScript learn how Python and PocketFlow
work together.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List
import logging
from pathlib import Path

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

class QueryRouterNode(Node):
    """Analyze incoming queries and route to appropriate processing flow."""
    
    def prep(self, shared: Dict[str, Any]):
        query = shared.get("query", {}).get("query", "")
        return query
    
    def exec(self, query: str):
        query_type = query_utils.classify_query(query)
        logger.info(f"Classified query as: {query_type}")
        return query_type
    
    def post(self, shared, prep_res, exec_res):
        shared.setdefault("query", {})["query_type"] = exec_res
        return exec_res  # Route based on query type


class SemanticSearchNode(Node):
    """Perform vector similarity search against indexed documents."""
    
    def prep(self, shared: Dict[str, Any]):
        query = shared.get("query", {}).get("query", "")
        config = shared.get("config", {})
        index_path = config.get("index_path", "semantic_index.pkl")
        model = config.get("embedding_model", "nomic-embed-text")
        k = config.get("search_k", 5)
        return query, index_path, model, k
    
    def exec(self, prep_res):
        query, index_path, model, k = prep_res
        
        # Generate query embedding
        query_embedding = embedding_utils.generate_embeddings([query], model=model)[0]
        
        # Load and search index
        if not Path(index_path).exists():
            logger.warning(f"Index not found at {index_path}")
            return []
        
        index = faiss_manager.load_index(index_path)
        ids, scores = faiss_manager.search(index, query_embedding, k=k)
        
        return list(zip(ids, scores))
    
    def post(self, shared, prep_res, exec_res):
        shared["query"]["search_results"] = exec_res
        return "default"


class TemporalMapperNode(Node):
    """Handle time-based queries by filtering documents by date."""
    
    def prep(self, shared: Dict[str, Any]):
        query = shared.get("query", {}).get("query", "")
        config = shared.get("config", {})
        db_path = config.get("metadata_path", "metadata.db")
        return query, db_path
    
    def exec(self, prep_res):
        query, db_path = prep_res
        
        # Extract temporal information
        filters = query_utils.build_metadata_filters(query)
        
        if not filters.get("start_date"):
            logger.info("No temporal markers found, proceeding with regular search")
            return []
        
        # Query database for files in date range
        conn = metadata_db.init_db(db_path)
        try:
            from datetime import datetime
            start = datetime.fromisoformat(filters["start_date"])
            end = datetime.fromisoformat(filters.get("end_date", filters["start_date"]))
            files = metadata_db.query_by_date_range(conn, start, end)
            return files
        finally:
            conn.close()
    
    def post(self, shared, prep_res, exec_res):
        shared["query"]["temporal_files"] = exec_res
        return "default"


class LLMProcessorNode(Node):
    """Process search results through LLM to generate natural language response."""
    
    def prep(self, shared: Dict[str, Any]):
        query = shared.get("query", {}).get("query", "")
        search_results = shared.get("query", {}).get("search_results", [])
        temporal_files = shared.get("query", {}).get("temporal_files", [])
        config = shared.get("config", {})
        
        # Get chunk texts for search results
        context_chunks = []
        if search_results:
            db_path = config.get("metadata_path", "metadata.db")
            conn = metadata_db.init_db(db_path)
            try:
                for chunk_id, score in search_results:
                    text = metadata_db.get_chunk_by_id(conn, chunk_id)
                    if text:
                        context_chunks.append(text)
            finally:
                conn.close()
        
        provider_info = llm_utils.route_to_provider("medium", config.get("llm_preference", "local"))
        return query, context_chunks, provider_info
    
    def exec(self, prep_res):
        query, context_chunks, provider_info = prep_res
        
        # Format context
        context = llm_utils.format_context(context_chunks)
        
        # Create prompt
        prompt = f"""Based on the following context from my business documents, please answer this question: {query}

Context:
{context}

Please provide a helpful and accurate response based on the available information."""
        
        # Call LLM
        response = llm_utils.call_llm(
            prompt, 
            provider_info["model"], 
            provider_info["provider"]
        )
        
        return response
    
    def post(self, shared, prep_res, exec_res):
        shared["query"]["llm_response"] = exec_res
        return "default"


class OutputFormatterNode(Node):
    """Format the final response for the requested output method."""
    
    def prep(self, shared: Dict[str, Any]):
        response = shared.get("query", {}).get("llm_response", "")
        config = shared.get("config", {})
        output_format = config.get("output_format", "chat")
        output_path = shared.get("query", {}).get("output_path", "")
        return response, output_format, output_path
    
    def exec(self, prep_res):
        response, output_format, output_path = prep_res
        
        if output_format == "file" and output_path:
            # Write to file
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(output_path).write_text(response)
            return f"Response written to: {output_path}"
        else:
            # Return for chat/console output
            return response
    
    def post(self, shared, prep_res, exec_res):
        shared["query"]["final_output"] = exec_res
        return "default"
