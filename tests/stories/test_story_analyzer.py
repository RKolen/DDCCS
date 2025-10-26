"""Tests for StoryAnalyzer using real character JSONs present in game_data/characters.

These tests avoid writing to repository data. They instantiate the project
StoryManager (which loads consultants from the project `game_data/characters`) and
analyze temporary story files created in a tempdir.
"""

import os
import sys
import tempfile
from tests import test_helpers

# Prepare test environment and get project root
project_root = test_helpers.setup_test_environment()
try:
    from src.stories.story_manager import StoryManager
except ImportError as e:
    print(f"[ERROR] Failed to import required modules: {e}")
    print("[ERROR] Make sure you're running from the tests directory")
    sys.exit(1)


def test_analyze_missing_file_returns_error():
    """Analyzer should return an error dict for missing files."""
    manager = StoryManager(str(project_root))
    analyzer = manager.analyzer

    result = analyzer.analyze_story_file(
        os.path.join(str(project_root), "no_such_file.md")
    )
    assert isinstance(result, dict)
    assert "error" in result


def test_analyze_simple_story_returns_expected_keys():
    """Simple story with Aragorn and Gandalf yields expected structure."""
    manager = StoryManager(str(project_root))
    analyzer = manager.analyzer

    with tempfile.TemporaryDirectory() as tmp:
        story_path = os.path.join(tmp, "001_simple.md")
        with open(story_path, "w", encoding="utf-8") as fh:
            fh.write("Aragorn drew Andúril and led the charge.\n")
            fh.write("Gandalf the Grey whispered a rune and cast Fireball.\n")

        result = analyzer.analyze_story_file(story_path)

        # Basic output contract
        assert isinstance(result, dict)
        assert "story_file" in result
        assert "character_actions" in result
        assert "consultant_analyses" in result
        assert "overall_consistency" in result

        # Expect detected character actions for Aragorn and Gandalf
        ca = result["character_actions"]
        assert any(
            k.lower().startswith("aragorn") for k in ca.keys()
        ), f"character_actions keys: {list(ca.keys())}"
        assert any(
            k.lower().startswith("gandalf") for k in ca.keys()
        ), f"character_actions keys: {list(ca.keys())}"


def test_analyzer_handles_empty_file():
    """Empty story file should return empty character_actions and score 0."""
    manager = StoryManager(str(project_root))
    analyzer = manager.analyzer

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "001_empty.md")
        with open(path, "w", encoding="utf-8"):
            pass

        result = analyzer.analyze_story_file(path)
        assert isinstance(result, dict)
        assert result.get("character_actions") == {}
        overall = result.get("overall_consistency")
        assert isinstance(overall, dict)
        assert overall.get("score") == 0
