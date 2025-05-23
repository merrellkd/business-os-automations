from pathlib import Path
import pickle
import math
from typing import List, Iterable, Tuple, Dict

# In a production setting we would use the FAISS library for fast vector
# similarity search. Since this environment may not have FAISS available, this
# module provides a lightweight stand-in that mimics the basic API using pure
# Python data structures.


def init_index(dim: int) -> Dict:
    """Create an empty index structure.

    Parameters
    ----------
    dim : int
        Dimensionality of the embedding vectors.
    """
    return {"dim": dim, "vectors": [], "ids": []}


def add_vectors(index: Dict, vectors: Iterable[Iterable[float]], ids: Iterable[int]) -> None:
    """Add embeddings to the in-memory index."""
    for vec, i in zip(vectors, ids):
        index["vectors"].append(list(vec))
        index["ids"].append(i)


def search(index: Dict, vector: Iterable[float], k: int = 5) -> Tuple[List[int], List[float]]:
    """Return IDs of the closest vectors using Euclidean distance."""
    dists = []
    for idx, vec in zip(index["ids"], index["vectors"]):
        dist = math.sqrt(sum((a - b) ** 2 for a, b in zip(vec, vector)))
        dists.append((dist, idx))
    dists.sort(key=lambda x: x[0])
    top = dists[:k]
    ids = [i for _, i in top]
    scores = [d for d, _ in top]
    return ids, scores


def save_index(index: Dict, path: str) -> None:
    """Persist the index to disk using pickle."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as fh:
        pickle.dump(index, fh)


def load_index(path: str) -> Dict:
    """Load an index from disk."""
    with open(path, "rb") as fh:
        return pickle.load(fh)
