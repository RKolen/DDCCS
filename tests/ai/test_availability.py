"""Tests for centralized AI availability helper in src.ai.availability."""

from tests.test_helpers import setup_test_environment, import_module


setup_test_environment()

av = import_module("src.ai.availability")


def test_ai_availability_symbols_exist() -> None:
    """The availability module exposes AI_AVAILABLE and CharacterAIConfig."""
    assert hasattr(av, "AI_AVAILABLE")
    assert hasattr(av, "CharacterAIConfig")


def test_character_ai_config_type_or_none() -> None:
    """CharacterAIConfig is either None or a class/type when AI available."""
    if av.AI_AVAILABLE:
        # When available, CharacterAIConfig should be something importable
        assert av.CharacterAIConfig is not None
    else:
        assert av.CharacterAIConfig is None
