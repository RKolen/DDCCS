"""
Configuration Type Definitions

Dataclasses for type-safe configuration management.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from pathlib import Path


@dataclass
class ModelProfile:
    """A named AI model configuration profile."""

    name: str = ""
    provider: str = "openai"  # "openai", "ollama", "openrouter"
    base_url: str = ""
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 1000
    description: str = ""


@dataclass
class ModelRegistryConfig:
    """Registry of available model profiles."""

    active_profile: str = "default"
    profiles: Dict[str, ModelProfile] = field(default_factory=dict)

    def get_profile(self, name: str) -> Optional[ModelProfile]:
        """Return a profile by name, falling back to the active profile.

        Args:
            name: Profile name to look up.

        Returns:
            The matching ModelProfile, or None if not found.
        """
        return self.profiles.get(name if name else self.active_profile)

    def get_active_profile(self) -> Optional[ModelProfile]:
        """Return the currently active ModelProfile.

        Returns:
            The active ModelProfile, or None if the registry is empty.
        """
        return self.profiles.get(self.active_profile)

    def list_profile_names(self) -> List[str]:
        """Return a sorted list of available profile names.

        Returns:
            Sorted list of profile name strings.
        """
        return sorted(self.profiles.keys())


@dataclass
class AIConfig:
    """AI service configuration."""

    api_key: str = ""
    base_url: Optional[str] = None
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 1000
    enabled: bool = True

    # Per-character overrides stored separately
    character_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def get_client_config(self) -> Dict[str, Any]:
        """Get configuration dict for AIClient initialization."""
        return {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    def is_configured(self) -> bool:
        """Check if AI is properly configured."""
        return bool(self.api_key and self.api_key != "your-openai-api-key-here")

    def get_character_config(self, character_name: str) -> Dict[str, Any]:
        """Get AI config for a specific character, with overrides."""
        base_config = self.get_client_config()

        if character_name in self.character_overrides:
            base_config.update(self.character_overrides[character_name])

        return base_config


@dataclass
class RAGConfig:
    """RAG (Retrieval-Augmented Generation) configuration."""

    enabled: bool = False
    wiki_base_url: str = ""
    rules_base_url: str = ""
    cache_ttl: int = 604800  # 7 days in seconds
    max_cache_size: int = 100
    search_depth: int = 3
    min_relevance: float = 0.5

    def is_configured(self) -> bool:
        """Check if RAG is properly configured."""
        return self.enabled and bool(self.wiki_base_url)


@dataclass
class DisplayConfig:
    """Terminal display configuration."""

    use_rich: bool = True
    theme: str = ""
    max_line_width: int = 80
    enable_tts: bool = False
    tts_voice: Optional[str] = None
    tts_speed: int = 150
    # Piper-specific config stored as dict
    piper_config: Dict[str, Any] = field(default_factory=dict)

    def get_tts_config(self) -> Dict[str, Any]:
        """Get TTS configuration dict."""
        config = {
            "enabled": self.enable_tts,
            "voice": self.tts_voice,
            "speed": self.tts_speed,
        }
        config.update(self.piper_config)
        return config


@dataclass
class PathConfig:
    """File path configuration."""

    game_data_dir: Path = field(default_factory=lambda: Path("game_data"))
    cache_dir: Path = field(default_factory=lambda: Path(".rag_cache"))
    rag_cache_backend: str = "json"
    rag_vector_db_path: Path = field(
        default_factory=lambda: Path(".rag_cache") / "rag_cache.sqlite3"
    )

    @property
    def characters_dir(self) -> Path:
        """Get characters directory path."""
        return self.game_data_dir / "characters"

    @property
    def campaigns_dir(self) -> Path:
        """Get campaigns directory path."""
        return self.game_data_dir / "campaigns"

    @property
    def npcs_dir(self) -> Path:
        """Get NPCs directory path."""
        return self.game_data_dir / "npcs"

    @property
    def items_dir(self) -> Path:
        """Get items directory path."""
        return self.game_data_dir / "items"

    def validate_paths(self) -> list:
        """Validate that required paths exist."""
        errors = []

        if not self.game_data_dir.exists():
            errors.append(f"Game data directory not found: {self.game_data_dir}")

        if not self.characters_dir.exists():
            errors.append(f"Characters directory not found: {self.characters_dir}")

        return errors


@dataclass
class DnDConfig:
    """Root configuration container."""

    ai: AIConfig = field(default_factory=AIConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    model_registry: ModelRegistryConfig = field(default_factory=ModelRegistryConfig)

    # Metadata
    config_file_path: Optional[Path] = None
    _dirty: bool = field(default=False, repr=False)

    def is_dirty(self) -> bool:
        """Check if configuration has unsaved changes."""
        return self._dirty

    def mark_dirty(self) -> None:
        """Mark configuration as having unsaved changes."""
        self._dirty = True

    def mark_clean(self) -> None:
        """Mark configuration as saved."""
        self._dirty = False

    def validate(self) -> list:
        """Validate configuration and return list of errors.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []

        # Validate AI config
        if self.ai.enabled and not self.ai.api_key:
            errors.append("AI is enabled but api_key is not set")
        if self.ai.api_key and self.ai.api_key == "your-openai-api-key-here":
            errors.append("AI api_key appears to be a placeholder")

        # Validate RAG config
        if self.rag.enabled and not self.rag.wiki_base_url:
            errors.append("RAG is enabled but wiki_base_url is not set")

        rag_backend = self.paths.rag_cache_backend.lower().strip()
        if rag_backend not in ("json", "sqlite"):
            errors.append(
                "RAG cache_backend must be one of: json, sqlite"
            )

        # Validate paths
        errors.extend(self.paths.validate_paths())

        return errors

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.

        Args:
            key: Configuration key (e.g., 'ai.model', 'rag.enabled')
            default: Default value if key not found

        Returns:
            Configuration value or default.
        """
        # Handle nested keys like 'ai.model'
        parts = key.split(".")
        if not parts:
            return default

        # Navigate to the correct config section
        section = parts[0]
        obj: Optional[Union[AIConfig, RAGConfig, DisplayConfig, PathConfig]] = None
        if section == "ai":
            obj = self.ai
        elif section == "rag":
            obj = self.rag
        elif section == "display":
            obj = self.display
        elif section == "paths":
            obj = self.paths
        else:
            return default

        # Get the attribute value
        if len(parts) == 1:
            return obj

        # Handle nested attributes
        attr = parts[1]
        if hasattr(obj, attr):
            return getattr(obj, attr)
        return default

    def set(self, key: str, value: Any) -> None:
        """Set configuration value by key.

        Args:
            key: Configuration key (e.g., 'ai.model', 'rag.enabled')
            value: Value to set
        """
        # Handle nested keys like 'ai.model'
        parts = key.split(".")
        if not parts:
            return

        # Navigate to the correct config section
        section = parts[0]
        obj2: Optional[Union[AIConfig, RAGConfig, DisplayConfig, PathConfig]] = None
        if section == "ai":
            obj2 = self.ai
        elif section == "rag":
            obj2 = self.rag
        elif section == "display":
            obj2 = self.display
        elif section == "paths":
            obj2 = self.paths
        else:
            return

        # Set the attribute value
        if len(parts) == 1:
            return

        attr = parts[1]
        if hasattr(obj2, attr):
            setattr(obj2, attr, value)
            self.mark_dirty()


# Convenience exports
__all__ = [
    "AIConfig",
    "ModelProfile",
    "ModelRegistryConfig",
    "RAGConfig",
    "DisplayConfig",
    "PathConfig",
    "DnDConfig",
]
