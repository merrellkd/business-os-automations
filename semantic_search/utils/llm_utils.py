"""Utility helpers for interacting with language models.

This module provides the thin abstractions described in Track C of the
semantic-search development plan.  The goal is to offer a unified
interface for local LLMs (for example via the ``ollama`` tool) and for
cloud providers.

The implementations here are deliberately simple so they can run in a
restricted testing environment.  Extensive comments are included to help
readers who know TypeScript but are new to Python.
"""

from __future__ import annotations

import os
import subprocess
from typing import Any, Dict, Iterable, List


def init_providers(config: Dict[str, Any]) -> Dict[str, Any]:
    """Initialise connections to LLM providers.

    ``config`` is expected to contain user preferences such as the default
    provider and model names.  In a real system we might establish HTTP
    client sessions or verify that local binaries are available.  Here we
    simply gather some basic environment information and return it so
    other functions can use it.
    """
    providers = {}

    # Check for a working ``ollama`` command which indicates that local
    # models can be used.
    try:
        subprocess.run(["ollama", "--help"], capture_output=True, check=True)
        providers["ollama"] = {"available": True}
    except (FileNotFoundError, subprocess.CalledProcessError):
        providers["ollama"] = {"available": False}

    # Cloud providers would normally require API keys.  We check the
    # environment variables as a lightweight way of determining
    # availability.
    if os.environ.get("OPENAI_API_KEY"):
        providers["openai"] = {"available": True}
    else:
        providers["openai"] = {"available": False}

    # Merge with any explicit configuration the caller supplied.
    providers.update(config.get("providers", {}))
    return providers


def route_to_provider(query_complexity: str, user_preference: str = "local") -> Dict[str, str]:
    """Decide which provider should handle the request.

    Parameters
    ----------
    query_complexity:
        Simple heuristics such as ``"low"`` or ``"high"`` complexity.
    user_preference:
        Either ``"local"`` or ``"cloud"`` indicating what the user would
        prefer.
    """
    if user_preference == "cloud":
        return {"provider": "openai", "model": "gpt-3.5-turbo"}

    # If the user prefers local but the query is too complex we fall back
    # to the cloud model.
    if query_complexity == "high":
        return {"provider": "openai", "model": "gpt-3.5-turbo"}

    return {"provider": "ollama", "model": "llama2"}


def format_context(chunks: List[str]) -> str:
    """Combine retrieved chunks into a prompt string."""
    return "\n".join(chunks)


def handle_streaming(stream: Iterable[str]) -> str:
    """Consume a streaming response and return the full text."""
    return "".join(stream)


def call_llm(prompt: str, model: str, provider: str = "ollama") -> str:
    """Send ``prompt`` to the specified LLM provider and return the reply.

    The real implementation would depend heavily on the provider APIs.
    This simplified version either shells out to ``ollama`` or simply
    echoes the prompt back for cloud providers.  The goal is to keep the
    function lightweight while showing the expected structure.
    """
    if provider == "ollama":
        try:
            completed = subprocess.run(
                ["ollama", "run", model],
                input=prompt,
                text=True,
                capture_output=True,
                check=True,
            )
            return completed.stdout.strip()
        except Exception:
            # If anything goes wrong we return an empty string so callers
            # can decide how to proceed (perhaps falling back to the cloud).
            return ""
    else:
        # In lieu of real network access we simply return the first part of
        # the prompt prefixed to show that the call succeeded.
        return f"Echo: {prompt[:50]}"
