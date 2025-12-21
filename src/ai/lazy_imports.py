"""
Lazy loader for AI availability module.

This module defers importing the slow OpenAI library until it's actually needed,
avoiding a 140+ second startup delay. The AI availability module is imported once
and cached for subsequent access.
"""

from typing import Any, Optional, Type
import importlib


class AIImportManager:
    """Manages lazy loading of AI imports."""

    _ai_available: Any = None
    _character_ai_config: Optional[Type] = None
    _loaded: bool = False

    @classmethod
    def ensure_loaded(cls) -> None:
        """Load AI imports if not already loaded."""
        if cls._loaded:
            return

        try:
            availability_module = importlib.import_module("src.ai.availability")
            cls._ai_available = getattr(availability_module, "AI_AVAILABLE")
            cls._character_ai_config = getattr(availability_module, "CharacterAIConfig")
        except (ImportError, AttributeError):
            cls._ai_available = False
            cls._character_ai_config = None

        cls._loaded = True

    @classmethod
    def is_available(cls) -> bool:
        """Check if AI imports are available."""
        cls.ensure_loaded()
        return cls._ai_available is True

    @classmethod
    def get_ai_available(cls) -> Any:
        """Get the AI_AVAILABLE value."""
        cls.ensure_loaded()
        return cls._ai_available

    @classmethod
    def get_character_ai_config(cls) -> Optional[Type]:
        """Get the CharacterAIConfig class."""
        cls.ensure_loaded()
        return cls._character_ai_config
