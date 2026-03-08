"""Small helpers for optional runtime imports.

Keep optional import logic centralized to avoid small-copy duplication and
make it easier to unit-test import fallbacks.
"""

from typing import Tuple, Optional, Any, Dict
import importlib


# Rich library availability and components
rich_available = False
rich_components: Dict[str, Any] = {}

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.align import Align
    from rich.text import Text
    from rich.columns import Columns
    from rich.markdown import Markdown
    from rich.syntax import Syntax

    rich_available = True
    rich_components = {
        "Console": Console,
        "Panel": Panel,
        "Align": Align,
        "Text": Text,
        "Columns": Columns,
        "Markdown": Markdown,
        "Syntax": Syntax,
    }
except ImportError:
    pass


def get_rich_console() -> Optional[Any]:
    """Get a Rich Console instance if available.

    Returns:
        Console instance or None if rich is not available
    """
    if rich_available:
        return rich_components["Console"]()
    return None


def get_rich_component(name: str) -> Optional[Any]:
    """Get a Rich component class by name.

    Args:
        name: Component name (Console, Panel, Align, Text, Columns, Markdown, Syntax)

    Returns:
        Component class or None if not available
    """
    return rich_components.get(name)


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


# TTS narrator availability and components
# Prefer Piper TTS for multi-voice support
tts_available = False
tts_components: Dict[str, Any] = {}

try:
    from src.utils.tts_narrator import (
        narrate_file_piper,
        is_piper_available,
        MultiVoiceNarrator,
        MultiVoiceConfig
    )

    tts_available = True
    tts_components = {
        "narrate_file": narrate_file_piper,
        "is_tts_available": is_piper_available,
        "MultiVoiceNarrator": MultiVoiceNarrator,
        "MultiVoiceConfig": MultiVoiceConfig,
    }
except ImportError:
    # Fallback to pyttsx3 if Piper unavailable
    try:
        from src.utils.tts_narrator import narrate_file, is_tts_available, StoryNarrator

        tts_available = True
        tts_components = {
            "narrate_file": narrate_file,
            "is_tts_available": is_tts_available,
            "StoryNarrator": StoryNarrator,
        }
    except ImportError:
        pass


def get_tts_narrate_file():
    """Get the narrate_file function if TTS is available.

    Returns:
        narrate_file function or None
    """
    return tts_components.get("narrate_file")


def get_tts_is_available():
    """Get the is_tts_available function if TTS is available.

    Returns:
        is_tts_available function or None
    """
    return tts_components.get("is_tts_available")
