"""
Configuration Type Definitions

Dataclasses for type-safe configuration management.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from pathlib import Path


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

    def get_tts_config(self) -> Dict[str, Any]:
        """Get TTS configuration dict."""
        return {
            "enabled": self.enable_tts,
            "voice": self.tts_voice,
            "speed": self.tts_speed,
        }


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
        if section == "ai":
            obj = self.ai
        elif section == "rag":
            obj = self.rag
        elif section == "display":
            obj = self.display
        elif section == "paths":
            obj = self.paths
        else:
            return

        # Set the attribute value
        if len(parts) == 1:
            return

        attr = parts[1]
        if hasattr(obj, attr):
            setattr(obj, attr, value)
            self.mark_dirty()


# Convenience exports
__all__ = [
    "AIConfig",
    "RAGConfig",
    "DisplayConfig",
    "PathConfig",
    "DnDConfig",
]
