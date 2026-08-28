"""Shared ComfyUI readiness checks for sidecar image routes."""

from typing import Optional

from fastapi import HTTPException

from src.ai.comfyui_client import ComfyUIClient
from src.config.config_types import ComfyUIConfig


def raise_unless_ready(
    blocked: Optional[str], client: Optional[ComfyUIClient]
) -> ComfyUIClient:
    """Raise 503 unless ComfyUI is ready, then return the client.

    Args:
        blocked: Detail from ``comfyui_unavailable``, or None.
        client: The client to use when ready.

    Returns:
        The client, guaranteed non-None.

    Raises:
        HTTPException: 503 when ComfyUI cannot run.
    """
    if blocked:
        raise HTTPException(status_code=503, detail=blocked)
    if client is None:
        raise HTTPException(
            status_code=503,
            detail="ComfyUI has no reachable base URL (set COMFYUI_HOST/COMFYUI_PORT)",
        )
    return client


def comfyui_unavailable(
    comfyui: ComfyUIConfig,
    client: Optional[ComfyUIClient],
    disabled_detail: str,
) -> Optional[str]:
    """Return a 503 detail when ComfyUI cannot run a generation.

    Args:
        comfyui: Loaded ComfyUI config.
        client: A client bound to the configured base URL, or None.
        disabled_detail: Message used when the feature flag is off.

    Returns:
        An error detail, or None when generation can proceed.
    """
    if not comfyui.enabled:
        return disabled_detail
    if client is None or not comfyui.get_base_url():
        return "ComfyUI has no reachable base URL (set COMFYUI_HOST/COMFYUI_PORT)"
    if not comfyui.assets.checkpoint:
        return "No Stable Diffusion checkpoint configured (set COMFYUI_CHECKPOINT)"
    if not client.is_available():
        return "ComfyUI is not reachable on the host"
    return None
