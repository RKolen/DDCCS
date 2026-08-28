"""Administrative helpers for a local Ollama instance."""

from typing import List

import requests


def list_loaded_models(base_url: str, timeout: float = 5.0) -> List[str]:
    """List the names of models currently resident in Ollama.

    Args:
        base_url: Native Ollama API base URL (composed from OLLAMA_HOST/PORT).
        timeout: Per-request timeout in seconds.

    Returns:
        The resident model names, or an empty list when Ollama is unreachable
        or has nothing loaded.
    """
    if not base_url:
        return []
    try:
        resp = requests.get(f"{base_url.rstrip('/')}/api/ps", timeout=timeout)
        resp.raise_for_status()
        payload = resp.json()
    except (requests.RequestException, ValueError):
        return []
    models = payload.get("models", []) if isinstance(payload, dict) else []
    names: List[str] = []
    for entry in models:
        name = entry.get("name") if isinstance(entry, dict) else None
        if isinstance(name, str) and name:
            names.append(name)
    return names


def unload_ollama_models(base_url: str, timeout: float = 30.0) -> int:
    """Unload every resident Ollama model via ``keep_alive: 0``.

    Best-effort: unreachable models are skipped, and the function never raises.
    The daemon stays up and reloads a model on the next request, so nothing
    needs restarting afterwards.

    Args:
        base_url: Native Ollama API base URL (composed from OLLAMA_HOST/PORT).
        timeout: Per-request timeout in seconds.

    Returns:
        The number of models successfully asked to unload.
    """
    if not base_url:
        return 0
    root = base_url.rstrip("/")
    unloaded = 0
    for name in list_loaded_models(root, timeout):
        try:
            resp = requests.post(
                f"{root}/api/generate",
                json={"model": name, "keep_alive": 0},
                timeout=timeout,
            )
            resp.raise_for_status()
            unloaded += 1
        except requests.RequestException:
            continue
    return unloaded
