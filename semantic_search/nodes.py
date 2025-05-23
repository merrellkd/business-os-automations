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


# Placeholder classes for query flow nodes will be added in other tracks.

