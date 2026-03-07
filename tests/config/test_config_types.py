"""Unit tests for src.config.config_types."""

from pathlib import Path
from tests.test_helpers import setup_test_environment, import_module, run_test_suite


setup_test_environment()

config_types = import_module("src.config.config_types")
AIConfig = config_types.AIConfig
RAGConfig = config_types.RAGConfig
DisplayConfig = config_types.DisplayConfig
PathConfig = config_types.PathConfig
DnDConfig = config_types.DnDConfig


def test_ai_config_defaults() -> None:
    """AIConfig has correct default values."""
    print("\n[TEST] AI Config - Defaults")
    config = AIConfig()
    assert config.api_key == "", "api_key should default to empty string"
    assert config.base_url is None, "base_url should default to None"
    assert config.model == "gpt-3.5-turbo", "model should default to gpt-3.5-turbo"
    assert config.temperature == 0.7, "temperature should default to 0.7"
    assert config.max_tokens == 1000, "max_tokens should default to 1000"
    assert config.enabled is True, "enabled should default to True"
    assert config.character_overrides == {}, "character_overrides should default to empty dict"
    print("  [OK] AIConfig defaults are correct")


def test_ai_config_get_client_config() -> None:
    """AIConfig.get_client_config returns correct dict."""
    print("\n[TEST] AI Config - Get Client Config")
    config = AIConfig(
        api_key="test-key",
        base_url="https://api.example.com",
        model="gpt-4",
        temperature=0.5,
        max_tokens=2000
    )
    client_config = config.get_client_config()
    assert client_config["api_key"] == "test-key"
    assert client_config["base_url"] == "https://api.example.com"
    assert client_config["model"] == "gpt-4"
    assert client_config["default_temperature"] == 0.5
    assert client_config["default_max_tokens"] == 2000
    print("  [OK] get_client_config returns correct dict")


def test_ai_config_is_configured() -> None:
    """AIConfig.is_configured returns correct value."""
    print("\n[TEST] AI Config - Is Configured")
    # Empty API key should not be configured
    config = AIConfig(api_key="")
    assert config.is_configured() is False, "Empty API key should not be configured"

    # Placeholder should not be configured
    config = AIConfig(api_key="your-openai-api-key-here")
    assert config.is_configured() is False, "Placeholder key should not be configured"

    # Real key should be configured
    config = AIConfig(api_key="sk-real-key")
    assert config.is_configured() is True, "Real API key should be configured"
    print("  [OK] is_configured works correctly")


def test_ai_config_character_overrides() -> None:
    """AIConfig.get_character_config applies character overrides."""
    print("\n[TEST] AI Config - Character Overrides")
    config = AIConfig(
        model="gpt-3.5-turbo",
        temperature=0.7,
        character_overrides={
            "Gandalf": {"model": "gpt-4", "temperature": 0.9},
        }
    )
    # Default config
    base = config.get_client_config()
    assert base["model"] == "gpt-3.5-turbo"
    assert base["default_temperature"] == 0.7

    # Character with override
    gandalf = config.get_character_config("Gandalf")
    assert gandalf["model"] == "gpt-4", "Should use overridden model"
    assert gandalf["default_temperature"] == 0.9, "Should use overridden temperature"

    # Character without override
    aragorn = config.get_character_config("Aragorn")
    assert aragorn["model"] == "gpt-3.5-turbo", "Should use default model"
    print("  [OK] Character overrides work correctly")


def test_rag_config_defaults() -> None:
    """RAGConfig has correct default values."""
    print("\n[TEST] RAG Config - Defaults")
    config = RAGConfig()
    assert config.enabled is False, "enabled should default to False"
    assert config.wiki_base_url == "", "wiki_base_url should default to empty string"
    assert config.rules_base_url == "https://dnd5e.wikidot.com"
    assert config.cache_ttl == 604800, "cache_ttl should default to 7 days"
    assert config.max_cache_size == 100, "max_cache_size should default to 100"
    assert config.search_depth == 3, "search_depth should default to 3"
    assert config.min_relevance == 0.5, "min_relevance should default to 0.5"
    print("  [OK] RAGConfig defaults are correct")


def test_rag_config_is_configured() -> None:
    """RAGConfig.is_configured returns correct value."""
    print("\n[TEST] RAG Config - Is Configured")
    # Disabled should not be configured
    config = RAGConfig(enabled=False)
    assert config.is_configured() is False, "Disabled RAG should not be configured"

    # Enabled but no URL should not be configured
    config = RAGConfig(enabled=True, wiki_base_url="")
    assert config.is_configured() is False, "No URL should not be configured"

    # Enabled with URL should be configured
    config = RAGConfig(enabled=True, wiki_base_url="https://example.com")
    assert config.is_configured() is True, "Enabled with URL should be configured"
    print("  [OK] is_configured works correctly")


def test_display_config_defaults() -> None:
    """DisplayConfig has correct default values."""
    print("\n[TEST] Display Config - Defaults")
    config = DisplayConfig()
    assert config.use_rich is True, "use_rich should default to True"
    assert config.theme == "dracula", "theme should default to dracula"
    assert config.max_line_width == 80, "max_line_width should default to 80"
    assert config.enable_tts is False, "enable_tts should default to False"
    assert config.tts_voice is None, "tts_voice should default to None"
    assert config.tts_speed == 150, "tts_speed should default to 150"
    print("  [OK] DisplayConfig defaults are correct")


def test_display_config_get_tts_config() -> None:
    """DisplayConfig.get_tts_config returns correct dict."""
    print("\n[TEST] Display Config - Get TTS Config")
    config = DisplayConfig(
        enable_tts=True,
        tts_voice="voice1",
        tts_speed=200
    )
    tts_config = config.get_tts_config()
    assert tts_config["enabled"] is True
    assert tts_config["voice"] == "voice1"
    assert tts_config["speed"] == 200
    print("  [OK] get_tts_config returns correct dict")


def test_path_config_defaults() -> None:
    """PathConfig has correct default values."""
    print("\n[TEST] Path Config - Defaults")
    config = PathConfig()
    assert config.game_data_dir == Path("game_data")
    assert config.cache_dir == Path(".rag_cache")
    print("  [OK] PathConfig defaults are correct")


def test_path_config_properties() -> None:
    """PathConfig properties return correct paths."""
    print("\n[TEST] Path Config - Properties")
    config = PathConfig(game_data_dir=Path("/custom/game_data"))
    assert config.characters_dir == Path("/custom/game_data/characters")
    assert config.campaigns_dir == Path("/custom/game_data/campaigns")
    assert config.npcs_dir == Path("/custom/game_data/npcs")
    assert config.items_dir == Path("/custom/game_data/items")
    print("  [OK] PathConfig properties return correct paths")


def test_path_config_validate_paths() -> None:
    """PathConfig.validate_paths returns errors for missing directories."""
    print("\n[TEST] Path Config - Validate Paths")
    config = PathConfig(game_data_dir=Path("/nonexistent/path"))
    errors = config.validate_paths()
    assert len(errors) > 0, "Should return errors for missing paths"
    assert any("Game data directory not found" in err for err in errors)
    print("  [OK] validate_paths returns correct errors")


def test_dnd_config_defaults() -> None:
    """DnDConfig has correct default values."""
    print("\n[TEST] DnD Config - Defaults")
    config = DnDConfig()
    assert isinstance(config.ai, AIConfig), "ai should be AIConfig instance"
    assert isinstance(config.rag, RAGConfig), "rag should be RAGConfig instance"
    assert isinstance(config.display, DisplayConfig), "display should be DisplayConfig instance"
    assert isinstance(config.paths, PathConfig), "paths should be PathConfig instance"
    assert config.config_file_path is None, "config_file_path should default to None"
    assert config.is_dirty() is False, "should not be dirty by default"
    print("  [OK] DnDConfig defaults are correct")


def test_dnd_config_dirty_flag() -> None:
    """DnDConfig dirty flag works correctly."""
    print("\n[TEST] DnD Config - Dirty Flag")
    config = DnDConfig()
    assert config.is_dirty() is False
    config.mark_dirty()
    assert config.is_dirty() is True
    config.mark_clean()
    assert config.is_dirty() is False
    print("  [OK] Dirty flag works correctly")


if __name__ == "__main__":
    run_test_suite(
        "config_types",
        [
            test_ai_config_defaults,
            test_ai_config_get_client_config,
            test_ai_config_is_configured,
            test_ai_config_character_overrides,
            test_rag_config_defaults,
            test_rag_config_is_configured,
            test_display_config_defaults,
            test_display_config_get_tts_config,
            test_path_config_defaults,
            test_path_config_properties,
            test_path_config_validate_paths,
            test_dnd_config_defaults,
            test_dnd_config_dirty_flag,
        ]
    )
