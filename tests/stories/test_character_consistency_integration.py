"""Integration tests for character consistency via the story analysis pipeline.

These tests reuse the Frodo profile in `game_data/characters` and create
temporary story files with explicit CHARACTER/ACTION/REASONING blocks. They
verify that the story analysis pipeline (StoryManager -> StoryAnalyzer ->
consultant) detects in-character vs out-of-character actions.
"""

import os
import sys
import tempfile
from tests import test_helpers

# Prepare test environment
project_root = test_helpers.setup_test_environment()
try:
    from src.stories.story_manager import StoryManager
except ImportError as e:
    print(f"[ERROR] Failed to import required modules: {e}")
    print("[ERROR] Make sure you're running from the tests directory")
    sys.exit(1)

def _get_consultant_analysis_for(manager, story_path, character_name):
    result = manager.analyze_story_file(story_path)
    assert isinstance(result, dict)
    ca = result.get("consultant_analyses", {})
    return ca.get(character_name)


def test_character_consistency_happy_path():
    """Frodo acting in-character should score well with few/no issues."""
    manager = StoryManager(str(project_root))

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "001_frodo_happy.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("CHARACTER: Frodo Baggins\n")
            fh.write("ACTION: Resisted the Ring despite temptation.\n")
            fh.write("REASONING: Protect the Shire and his friends.\n\n")
            fh.write("CHARACTER: Frodo Baggins\n")
            fh.write("ACTION: Helped Sam when exhausted.\n")
            fh.write("REASONING: Loyalty to Sam.\n")

        analysis = _get_consultant_analysis_for(manager, path, "Frodo Baggins")
        assert analysis is not None, "No analysis for Frodo"
        assert analysis["consistency_score"] >= 0.5, f"Unexpected low score: {analysis}"
        assert isinstance(analysis["issues"], list)
        assert len(analysis["issues"]) == 0 or analysis["consistency_score"] >= 0.6


def test_character_consistency_detects_contradiction():
    """Frodo performing cruel actions should be flagged as inconsistent."""
    manager = StoryManager(str(project_root))

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "001_frodo_bad.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("CHARACTER: Frodo Baggins\n")
            fh.write("ACTION: Tortured a villager for sport.\n")
            fh.write("REASONING: He enjoyed it.\n\n")
            fh.write("CHARACTER: Frodo Baggins\n")
            fh.write("ACTION: Laughed at suffering.\n")
            fh.write("REASONING: None.\n")

        analysis = _get_consultant_analysis_for(manager, path, "Frodo Baggins")
        assert analysis is not None, "No analysis for Frodo"
        # Expect low score and at least one issue flagged
        assert analysis["consistency_score"] <= 0.5, f"Score unexpectedly high: {analysis}"
        assert len(analysis["issues"]) >= 1, f"Expected issues but got: {analysis}"
