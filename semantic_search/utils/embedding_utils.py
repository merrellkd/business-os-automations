"""Utility functions for working with embeddings.

These functions are part of Track C (LLM Integration) from the
semantic-search project.  The implementations are intentionally
lightweight so that the examples can run in restricted environments
while still demonstrating the expected interfaces.

The comments are verbose and try to teach Python concepts to a
TypeScript developer who may be new to Python and PocketFlow.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
from typing import List


EMBEDDING_DIMENSION = 768  # default vector size used by many models


def _hash_embedding(text: str, dimension: int = EMBEDDING_DIMENSION) -> List[float]:
    """Create a pseudo embedding by hashing the input text.

    In real usage this function would not be necessary because we would
    call an embedding model (for example via the ``ollama`` command line
    tool).  When tests run in an isolated environment we may not have
    such a model available, so this function provides deterministic
    numeric vectors based solely on the text input.
    """

    # ``hashlib.sha256`` gives us a 32 byte digest.
    digest = hashlib.sha256(text.encode("utf-8")).digest()

    # Convert bytes to integers 0-255 and repeat to fill ``dimension`` slots.
    data = list(digest)
    while len(data) < dimension:
        data.extend(digest)
    data = data[:dimension]

    # Normalise to floats between 0 and 1 so they at least look like embeddings.
    return [b / 255 for b in data]


def validate_model_availability(model_name: str) -> bool:
    """Check whether ``model_name`` is available via ``ollama``.

    This function tries to execute ``ollama list`` and searches for the
    requested model.  If the ``ollama`` command is missing or returns an
    error, ``False`` is returned.  The implementation is defensive so it
    will never raise an exception if ``ollama`` is not installed.
    """
    try:
        result = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True, check=True
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        # ``ollama`` is not installed or failed.
        return False

    return model_name in result.stdout


def init_ollama_embeddings(model_name: str = "nomic-embed-text") -> bool:
    """Prepare the local embedding model.

    The real system would ensure that ``model_name`` is downloaded and
    ready.  Here we simply verify availability so that other code can
    decide whether to use the local model or fall back to a cloud
    provider.
    """
    return validate_model_availability(model_name)


def fallback_to_cloud(texts: List[str], provider: str = "openai", model: str = "text-embedding-ada-002") -> List[List[float]]:
    """Return embeddings using a cloud provider.

    When ``ollama`` is unavailable we might call a service such as the
    OpenAI API.  Network access is disabled in the testing environment so
    this function uses ``_hash_embedding`` as a stand in for real API
    calls.  The interface mirrors what a real function might return: a
    list of embedding vectors.
    """
    return [_hash_embedding(t) for t in texts]


def generate_embeddings(texts: List[str], model: str = "nomic-embed-text", use_fallback: bool = True) -> List[List[float]]:
    """Generate embeddings for a list of text chunks.

    Parameters
    ----------
    texts:
        The pieces of text we want to embed.
    model:
        Name of the embedding model to use with ``ollama``.
    use_fallback:
        If ``True`` and the local model is unavailable we try the cloud
        fallback implementation.

    Returns
    -------
    List[List[float]]
        A list of embedding vectors, one for each text chunk.
    """

    if validate_model_availability(model):
        # A very small example of how you might call ``ollama``.  The real
        # command depends on the specific ``ollama`` version and model.  We
        # keep it simple here and fall back to hashed embeddings if the
        # command fails for any reason.
        embeddings: List[List[float]] = []
        for text in texts:
            try:
                completed = subprocess.run(
                    ["ollama", "embeddings", "--model", model],
                    input=text,
                    text=True,
                    capture_output=True,
                    check=True,
                )
                # ``ollama`` typically returns JSON.  We expect a list of
                # numbers under an ``embedding`` key.
                out = completed.stdout.strip()
                data = out.split()
                vector = [float(x) for x in data]
                embeddings.append(vector)
            except Exception:
                # If anything goes wrong we break out and use the fallback.
                embeddings = []
                break
        if embeddings:
            return embeddings

    if use_fallback:
        return fallback_to_cloud(texts)
    else:
        # Generate deterministic but fake embeddings so that downstream
        # code has something to work with.
        return [_hash_embedding(t) for t in texts]
