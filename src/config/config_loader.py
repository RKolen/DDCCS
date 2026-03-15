"""
Configuration Loader

Loads configuration from multiple sources with precedence:
1. CLI arguments (highest)
2. Environment variables
3. config.json file
4. Default values (lowest)
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from src.config.config_types import (
    AIConfig,
    DisplayConfig,
    DnDConfig,
    MilvusConfig,
    ModelProfile,
    ModelRegistryConfig,
    PathConfig,
    RAGConfig,
)
from src.utils.errors import display_error, FileSystemError


# Default config file location
DEFAULT_CONFIG_FILE = Path("game_data/config.json")


def load_config(
    config_path: Optional[Path] = None,
    env_prefix: str = "",
) -> DnDConfig:
    """Load configuration from all sources.

    Precedence (highest to lowest):
    1. Environment variables
    2. config.json file
    3. Default values

    Args:
        config_path: Optional path to config file
        env_prefix: Optional prefix for environment variables

    Returns:
        DnDConfig with merged settings
    """
    # Start with defaults
    config = DnDConfig()

    # Load from config file
    file_config = _load_config_file(config_path or DEFAULT_CONFIG_FILE)
    if file_config:
        config = _merge_config(config, file_config)

    # Override with environment variables
    config = _apply_env_overrides(config, env_prefix)

    # Store config file path
    config.config_file_path = config_path or DEFAULT_CONFIG_FILE

    return config


def _load_config_file(config_path: Path) -> Optional[Dict[str, Any]]:
    """Load configuration from JSON file.

    Args:
        config_path: Path to config file

    Returns:
        Configuration dict or None if file doesn't exist
    """
    if not config_path.exists():
        return None

    try:
        with open(config_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        print(f"[WARNING] Could not load config file: {error}")
        return None


def _merge_config(base: DnDConfig, override: Dict[str, Any]) -> DnDConfig:
    """Merge override dict into base config.

    Args:
        base: Base DnDConfig
        override: Override values from file

    Returns:
        New DnDConfig with merged values
    """
    # AI config
    if "ai" in override:
        ai_data = override["ai"]
        base.ai = AIConfig(
            api_key=ai_data.get("api_key", base.ai.api_key),
            base_url=ai_data.get("base_url", base.ai.base_url),
            model=ai_data.get("model", base.ai.model),
            temperature=ai_data.get("temperature", base.ai.temperature),
            max_tokens=ai_data.get("max_tokens", base.ai.max_tokens),
            enabled=ai_data.get("enabled", base.ai.enabled),
            character_overrides=ai_data.get("character_overrides", {}),
        )

    # RAG config
    if "rag" in override:
        rag_data = override["rag"]
        base.rag = RAGConfig(
            enabled=rag_data.get("enabled", base.rag.enabled),
            wiki_base_url=rag_data.get("wiki_base_url", base.rag.wiki_base_url),
            rules_base_url=rag_data.get("rules_base_url", base.rag.rules_base_url),
            cache_ttl=rag_data.get("cache_ttl", base.rag.cache_ttl),
            max_cache_size=rag_data.get("max_cache_size", base.rag.max_cache_size),
            search_depth=rag_data.get("search_depth", base.rag.search_depth),
            min_relevance=rag_data.get("min_relevance", base.rag.min_relevance),
        )

        # Backward compatibility: legacy storage keys used to live under "rag".
        legacy_cache_backend = rag_data.get("cache_backend")
        if legacy_cache_backend:
            base.paths.rag_cache_backend = str(legacy_cache_backend)

        legacy_vector_db_path = rag_data.get("vector_db_path")
        if legacy_vector_db_path:
            base.paths.rag_vector_db_path = Path(legacy_vector_db_path)

    # Display config
    if "display" in override:
        display_data = override["display"]
        base.display = DisplayConfig(
            use_rich=display_data.get("use_rich", base.display.use_rich),
            theme=display_data.get("theme", base.display.theme),
            max_line_width=display_data.get("max_line_width", base.display.max_line_width),
            enable_tts=display_data.get("enable_tts", base.display.enable_tts),
            tts_voice=display_data.get("tts_voice", base.display.tts_voice),
            tts_speed=display_data.get("tts_speed", base.display.tts_speed),
        )

    # Path config
    if "paths" in override:
        paths_data = override["paths"]
        base.paths = PathConfig(
            game_data_dir=Path(paths_data.get("game_data_dir", base.paths.game_data_dir)),
            cache_dir=Path(paths_data.get("cache_dir", base.paths.cache_dir)),
            rag_cache_backend=paths_data.get(
                "rag_cache_backend", base.paths.rag_cache_backend
            ),
            rag_vector_db_path=Path(
                paths_data.get("rag_vector_db_path", base.paths.rag_vector_db_path)
            ),
        )

    # Milvus config
    if "milvus" in override:
        milvus_data = override["milvus"]
        base.milvus = MilvusConfig(
            enabled=milvus_data.get("enabled", base.milvus.enabled),
            host=milvus_data.get("host", base.milvus.host),
            port=milvus_data.get("port", base.milvus.port),
            collection_prefix=milvus_data.get(
                "collection_prefix", base.milvus.collection_prefix
            ),
            embedding_model=milvus_data.get(
                "embedding_model", base.milvus.embedding_model
            ),
            embedding_dim=milvus_data.get("embedding_dim", base.milvus.embedding_dim),
            top_k=milvus_data.get("top_k", base.milvus.top_k),
            similarity_threshold=milvus_data.get(
                "similarity_threshold", base.milvus.similarity_threshold
            ),
        )

    # Model registry config
    if "model_registry" in override:
        base.model_registry = _parse_model_registry(override["model_registry"])

    return base


def _parse_model_registry(data: Dict[str, Any]) -> ModelRegistryConfig:
    """Parse a model_registry dict into a ModelRegistryConfig.

    Args:
        data: Raw dict from config file.

    Returns:
        Populated ModelRegistryConfig.
    """
    profiles: Dict[str, ModelProfile] = {}
    for name, profile_data in data.get("profiles", {}).items():
        profiles[name] = ModelProfile(
            name=name,
            provider=profile_data.get("provider", "openai"),
            base_url=profile_data.get("base_url", ""),
            model=profile_data.get("model", ""),
            temperature=float(profile_data.get("temperature", 0.7)),
            max_tokens=int(profile_data.get("max_tokens", 1000)),
            description=profile_data.get("description", ""),
        )
    return ModelRegistryConfig(
        active_profile=data.get("active_profile", "default"),
        profiles=profiles,
    )


def _apply_env_model_profiles(
    config: DnDConfig,
    get_env,
    get_env_float,
    get_env_int,
) -> None:
    """Apply model registry profile overrides from environment variables.

    Args:
        config: DnDConfig to update in-place.
        get_env: Callable to read a string env var.
        get_env_float: Callable to read a float env var with default.
        get_env_int: Callable to read an int env var with default.
    """
    creative_model = get_env("AI_CREATIVE_MODEL")
    creative_base_url = get_env("AI_CREATIVE_BASE_URL")
    if creative_model or creative_base_url:
        config.model_registry.profiles["creative"] = ModelProfile(
            name="creative",
            provider="openai",
            base_url=creative_base_url or "",
            model=creative_model or "",
            temperature=get_env_float("AI_CREATIVE_TEMPERATURE", 0.9),
            max_tokens=get_env_int("AI_CREATIVE_MAX_TOKENS", 2000),
            description="Creative model for story writing and combat narration",
        )

    fast_model = get_env("AI_FAST_MODEL")
    fast_base_url = get_env("AI_FAST_BASE_URL")
    if fast_model or fast_base_url:
        config.model_registry.profiles["fast"] = ModelProfile(
            name="fast",
            provider="openai",
            base_url=fast_base_url or "",
            model=fast_model or "",
            temperature=get_env_float("AI_FAST_TEMPERATURE", 0.3),
            max_tokens=get_env_int("AI_FAST_MAX_TOKENS", 500),
            description="Fast model for analysis and evaluation tasks",
        )


def _apply_env_milvus_overrides(
    config: DnDConfig,
    get_env: Any,
    get_env_bool: Any,
    get_env_int: Any,
    get_env_float: Any,
) -> None:
    """Apply Milvus configuration overrides from environment variables.

    Args:
        config: DnDConfig to update in-place.
        get_env: Callable to read a string env var.
        get_env_bool: Callable to read a bool env var with default.
        get_env_int: Callable to read an int env var with default.
        get_env_float: Callable to read a float env var with default.
    """
    config.milvus.enabled = get_env_bool("MILVUS_ENABLED", config.milvus.enabled)

    milvus_host = get_env("MILVUS_HOST")
    if milvus_host:
        config.milvus.host = milvus_host

    config.milvus.port = get_env_int("MILVUS_PORT", config.milvus.port)

    milvus_prefix = get_env("MILVUS_COLLECTION_PREFIX")
    if milvus_prefix:
        config.milvus.collection_prefix = milvus_prefix

    milvus_model = get_env("MILVUS_EMBEDDING_MODEL")
    if milvus_model:
        config.milvus.embedding_model = milvus_model

    config.milvus.embedding_dim = get_env_int(
        "MILVUS_EMBEDDING_DIM", config.milvus.embedding_dim
    )
    config.milvus.top_k = get_env_int("MILVUS_TOP_K", config.milvus.top_k)
    config.milvus.similarity_threshold = get_env_float(
        "MILVUS_SIMILARITY_THRESHOLD", config.milvus.similarity_threshold
    )


def _apply_env_overrides(config: DnDConfig, prefix: str = "") -> DnDConfig:
    """Apply environment variable overrides.

    Args:
        config: Base configuration
        prefix: Environment variable prefix

    Returns:
        Configuration with env overrides applied
    """

    def get_env(key: str, default: Any = None) -> Any:
        """Get environment variable with optional prefix."""
        full_key = f"{prefix}{key}" if prefix else key
        return os.getenv(full_key, default)

    def get_env_bool(key: str, default: bool = False) -> bool:
        """Get boolean environment variable."""
        value = get_env(key)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")

    def get_env_int(key: str, default: int) -> int:
        """Get integer environment variable."""
        value = get_env(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default

    def get_env_float(key: str, default: float) -> float:
        """Get float environment variable."""
        value = get_env(key)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            return default

    # AI configuration
    api_key = get_env("OPENAI_API_KEY")
    if api_key:
        config.ai.api_key = api_key

    base_url = get_env("OPENAI_BASE_URL")
    if base_url:
        config.ai.base_url = base_url

    model = get_env("OPENAI_MODEL")
    if model:
        config.ai.model = model

    config.ai.temperature = get_env_float("AI_TEMPERATURE", config.ai.temperature)
    config.ai.max_tokens = get_env_int("AI_MAX_TOKENS", config.ai.max_tokens)

    _apply_env_model_profiles(config, get_env, get_env_float, get_env_int)

    # RAG configuration
    config.rag.enabled = get_env_bool("RAG_ENABLED", config.rag.enabled)

    wiki_url = get_env("RAG_WIKI_BASE_URL")
    if wiki_url:
        config.rag.wiki_base_url = wiki_url

    rules_url = get_env("RAG_RULES_BASE_URL")
    if rules_url:
        config.rag.rules_base_url = rules_url

    config.rag.cache_ttl = get_env_int("RAG_CACHE_TTL", config.rag.cache_ttl)
    config.rag.max_cache_size = get_env_int("RAG_MAX_CACHE_SIZE", config.rag.max_cache_size)
    config.rag.search_depth = get_env_int("RAG_SEARCH_DEPTH", config.rag.search_depth)
    config.rag.min_relevance = get_env_float("RAG_MIN_RELEVANCE", config.rag.min_relevance)

    cache_backend = get_env("RAG_CACHE_BACKEND")
    if cache_backend:
        config.paths.rag_cache_backend = cache_backend.lower().strip()

    vector_db_path = get_env("RAG_VECTOR_DB_PATH")
    if vector_db_path:
        config.paths.rag_vector_db_path = Path(vector_db_path)

    cache_dir = get_env("RAG_CACHE_DIR")
    if cache_dir:
        config.paths.cache_dir = Path(cache_dir)

    _apply_env_milvus_overrides(config, get_env, get_env_bool, get_env_int, get_env_float)

    return config


def save_config(config: DnDConfig, path: Optional[Path] = None) -> bool:
    """Save configuration to JSON file.

    Args:
        config: Configuration to save
        path: Optional path, uses config.config_file_path if not provided

    Returns:
        True if save was successful
    """
    save_path = path or config.config_file_path or DEFAULT_CONFIG_FILE

    # Ensure parent directory exists
    save_path.parent.mkdir(parents=True, exist_ok=True)

    # Build config dict (exclude sensitive data like API keys)
    config_dict = {
        "ai": {
            "base_url": config.ai.base_url,
            "model": config.ai.model,
            "temperature": config.ai.temperature,
            "max_tokens": config.ai.max_tokens,
            "enabled": config.ai.enabled,
            # Note: api_key is NOT saved to file for security
            "character_overrides": config.ai.character_overrides,
        },
        "rag": {
            "enabled": config.rag.enabled,
            "wiki_base_url": config.rag.wiki_base_url,
            "rules_base_url": config.rag.rules_base_url,
            "cache_ttl": config.rag.cache_ttl,
            "max_cache_size": config.rag.max_cache_size,
            "search_depth": config.rag.search_depth,
            "min_relevance": config.rag.min_relevance,
        },
        "display": {
            "use_rich": config.display.use_rich,
            "theme": config.display.theme,
            "max_line_width": config.display.max_line_width,
            "enable_tts": config.display.enable_tts,
            "tts_voice": config.display.tts_voice,
            "tts_speed": config.display.tts_speed,
        },
        "paths": {
            "game_data_dir": str(config.paths.game_data_dir),
            "cache_dir": str(config.paths.cache_dir),
            "rag_cache_backend": config.paths.rag_cache_backend,
            "rag_vector_db_path": str(config.paths.rag_vector_db_path),
        },
        "milvus": {
            "enabled": config.milvus.enabled,
            "host": config.milvus.host,
            "port": config.milvus.port,
            "collection_prefix": config.milvus.collection_prefix,
            "embedding_model": config.milvus.embedding_model,
            "embedding_dim": config.milvus.embedding_dim,
            "top_k": config.milvus.top_k,
            "similarity_threshold": config.milvus.similarity_threshold,
        },
    }

    try:
        with open(save_path, "w", encoding="utf-8") as file:
            json.dump(config_dict, file, indent=2)

        config.mark_clean()
        return True

    except OSError as os_error:
        fs_error = FileSystemError(
            message=f"Failed to save config: {os_error}",
            user_guidance="Check file permissions and disk space."
        )
        display_error(fs_error)
        return False


# Convenience exports
__all__ = [
    "load_config",
    "save_config",
    "DEFAULT_CONFIG_FILE",
]
