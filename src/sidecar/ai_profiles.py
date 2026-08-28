"""Model-profile AI clients, shared by `app` and the sidecar route modules."""

import os
from typing import Optional

from src.ai.ai_client import AIClient
from src.config.config_loader import load_config


def build_profile_client(profile_name: str) -> Optional[AIClient]:
    """Build an AIClient for a named model profile, or None if unconfigured.

    Args:
        profile_name: The model registry profile to use ("fast" / "creative").

    Returns:
        A configured AIClient, or None when no usable profile is available.
    """
    config = load_config()
    profile = (
        config.model_registry.get_profile(profile_name)
        or config.model_registry.get_active_profile()
    )
    if profile is None or not profile.base_url or not profile.model:
        return None
    # Local inference takes minutes per call; the default 30s timeout would
    # abort every arc call. ARC_AI_TIMEOUT tunes it.
    return AIClient(
        api_key=os.getenv("OLLAMA_API_KEY", "") or config.ai.api_key,
        base_url=profile.base_url,
        model=profile.model,
        default_temperature=profile.temperature,
        default_max_tokens=max(profile.max_tokens, 2000),
        timeout=float(os.getenv("ARC_AI_TIMEOUT", "1800")),
    )
