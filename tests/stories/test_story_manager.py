"""
Story Manager Tests

Tests for the `StoryManager` wrapper that coordinates file operations,
character loading, analysis and updates.
"""

import sys
import tempfile
import os
from pathlib import Path

# Ensure project root is on sys.path so src.* imports work
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from src.stories.story_manager import StoryManager
except ImportError as exc:  # pragma: no cover - import guard for test run
    print(f"[ERROR] Failed to import StoryManager: {exc}")
    print("Make sure you're running tests from project root")
    raise


def test_story_manager_initialization():
    """Ensure StoryManager initializes with empty workspace."""
    print("\n[TEST] StoryManager Initialization")

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = StoryManager(tmpdir)
        assert manager is not None, "StoryManager should be created"
        assert manager.workspace_path == tmpdir
        # No characters initially
        assert isinstance(manager.get_character_list(), list)

    print("[PASS] StoryManager Initialization")


def test_create_new_story_creates_file():
    """Creating a new root story should produce a numbered markdown file."""
    print("\n[TEST] Create New Story")

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = StoryManager(tmpdir)
        filepath = manager.create_new_story("My Test Story", "A description")

        assert os.path.exists(filepath), "Created story file should exist"
        basename = os.path.basename(filepath)
        assert basename.endswith('.md'), "Story file must be markdown"
        assert basename.startswith('001_'), "First created story should be 001_"

    print("[PASS] Create New Story")


def test_create_new_story_series_and_add_story():
    """Create a new series (valid suffix) then add another story to it."""
    print("\n[TEST] Create New Story Series and Add Story")

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = StoryManager(tmpdir)

        # Series name must end with a valid suffix (use _Quest)
        series_name = "MyCampaign_Quest"
        first_path = manager.create_new_story_series(series_name, "First Tale", "desc")
        assert os.path.exists(first_path), "First story in series should exist"

        # Ensure series is discoverable
        series_list = manager.get_story_series()
        assert series_name in series_list, "New series should appear in series list"

        # Add second story
        second_path = manager.create_story_in_series(series_name, "Second Tale", "desc2")
        assert os.path.exists(second_path), "Second story should exist"

        files = manager.get_story_files_in_series(series_name)
        assert any(f.startswith('001_') for f in files)
        assert any(f.startswith('002_') for f in files)

    print("[PASS] Create New Story Series and Add Story")


def test_create_story_in_nonexistent_series_raises():
    """Creating a story inside a non-existent series should raise ValueError."""
    print("\n[TEST] Create Story in Nonexistent Series")

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = StoryManager(tmpdir)

        try:
            manager.create_story_in_series("NoSuchSeries_Quest", "Tale")
            raised = False
        except ValueError:
            raised = True

        assert raised, "Expected ValueError for non-existent series"

    print("[PASS] Create Story in Nonexistent Series")


def test_analyze_nonexistent_and_existing_file():
    """Analyze returns an error for missing files and structured result for existing."""
    print("\n[TEST] Analyze Story File")

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = StoryManager(tmpdir)

        # Nonexistent file
        result = manager.analyze_story_file(os.path.join(tmpdir, "no-file.md"))
        assert isinstance(result, dict)
        assert result.get("error") is not None

        # Create a real story and analyze
        created = manager.create_new_story("Analysis Tale", "for analysis")
        assert os.path.exists(created)

        result2 = manager.analyze_story_file(created)
        assert isinstance(result2, dict)
        assert "story_file" in result2
        assert "character_actions" in result2
        assert "consultant_analyses" in result2
        assert "overall_consistency" in result2

    print("[PASS] Analyze Story File")


def run_all_tests():
    """Run all StoryManager tests."""
    test_story_manager_initialization()
    test_create_new_story_creates_file()
    test_create_new_story_series_and_add_story()
    test_create_story_in_nonexistent_series_raises()
    test_analyze_nonexistent_and_existing_file()


if __name__ == "__main__":
    run_all_tests()
