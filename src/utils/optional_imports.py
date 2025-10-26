"""Small helpers for optional runtime imports.

Keep optional import logic centralized to avoid small-copy duplication and
make it easier to unit-test import fallbacks.
"""
from typing import Tuple, Optional
import importlib


def import_ai_config() -> Tuple[bool, Optional[type]]:
    """Try to import CharacterAIConfig from the AI client.

    Returns a tuple (available, CharacterAIConfig-or-None).
    """
    try:
        module = importlib.import_module("src.ai.ai_client")
        return True, getattr(module, "CharacterAIConfig", None)
    except (ImportError, ModuleNotFoundError):
        return False, None


def import_validator() -> Tuple[bool, Optional[object]]:
    """Try to import the character_validator module and return (available, module_or_None).

    Returns a tuple where the second element is the module object (so callers can
    fetch `validate_character_file` if present).
    """
    try:
        module = importlib.import_module("src.validation.character_validator")
        return True, module
    except (ImportError, ModuleNotFoundError):
        return False, None
