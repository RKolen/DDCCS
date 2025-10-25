"""Tests for story file manager functions (file creation, sequencing, discovery).

These are filesystem-driven unit tests that use a temporary workspace so the
repository is not modified. They exercise deterministic behavior: series
creation, story numbering, and file content writing.
"""

import os
import re
import sys
import tempfile

import test_helpers

# Configure test environment so `src` imports work during test execution.
project_root = test_helpers.setup_test_environment()
try:
    from src.utils.path_utils import get_campaigns_dir
    from src.stories.story_file_manager import (
        create_new_story_series,
        create_story_in_series,
        get_story_series,
        get_story_files_in_series,
        create_new_story,
        create_pure_story_file,
    )
except ImportError as e:
    print(f"[ERROR] Failed to import required modules: {e}")
    print("[ERROR] Make sure you're running from the tests directory")
    sys.exit(1)

def _find_numbered_file(files, number: int):
    pattern = re.compile(rf"^{number:03d}_.*\.md$")
    for f in files:
        if pattern.match(f):
            return f
    return None


def test_create_new_story_series_and_first_file():
    """Creating a new series should create the folder and a 001_ file."""
    with tempfile.TemporaryDirectory() as tmp:
        campaigns_dir = get_campaigns_dir(tmp)
        # Create series with first story
        filepath = create_new_story_series(campaigns_dir, tmp, "MySeries", "Intro", "desc")

        # Series folder exists
        series_path = os.path.join(campaigns_dir, "MySeries")
        assert os.path.isdir(series_path)

        # There is a 001_ file inside the series
        files = os.listdir(series_path)
        first = _find_numbered_file(files, 1)
        assert first is not None
        assert filepath.endswith(first)


def test_create_story_in_series_increments_number():
    """Adding a story into a series should create the next numbered file."""
    with tempfile.TemporaryDirectory() as tmp:
        campaigns_dir = get_campaigns_dir(tmp)
        # Create series and first story
        _first_path = create_new_story_series(campaigns_dir, tmp, "S", "Start", "")

        # Add another story in same series
        new_path = create_story_in_series(campaigns_dir, tmp, "S", "Followup", "")

        series_path = os.path.join(campaigns_dir, "S")
        files = sorted(os.listdir(series_path))

        # Expect both 001_ and 002_ files
        assert _find_numbered_file(files, 1) is not None
        assert _find_numbered_file(files, 2) is not None
        assert os.path.exists(new_path)


def test_get_story_series_and_files_discovery():
    """Discover series folders and their numbered story files."""
    with tempfile.TemporaryDirectory() as tmp:
        campaigns_dir = get_campaigns_dir(tmp)

        # Create two series with numbered files
        os.makedirs(os.path.join(campaigns_dir, "Alpha"), exist_ok=True)
        os.makedirs(os.path.join(campaigns_dir, "Beta"), exist_ok=True)

        for fn in ("001_one.md", "002_two.md"):
            with open(os.path.join(campaigns_dir, "Alpha", fn), "w", encoding="utf-8") as fh:
                fh.write("# alpha\n")

        with open(os.path.join(campaigns_dir, "Beta", "001_b.md"), "w", encoding="utf-8") as fh:
            fh.write("# beta\n")

        series = get_story_series(campaigns_dir)
        assert "Alpha" in series
        assert "Beta" in series

        alpha_files = get_story_files_in_series(campaigns_dir, "Alpha")
        assert "001_one.md" in alpha_files
        assert "002_two.md" in alpha_files


def test_create_new_story_root_numbering_and_pure_file():
    """Creating root-level (legacy) story and writing a pure story file."""
    with tempfile.TemporaryDirectory() as tmp:
        campaigns_dir = get_campaigns_dir(tmp)

        # Create a root-level story
        root_path = create_new_story(campaigns_dir, tmp, "RootStory", "")
        assert os.path.exists(root_path)

        # Create a pure story file in a series path
        series_path = os.path.join(campaigns_dir, "SeriesX")
        os.makedirs(series_path, exist_ok=True)
        content = "This is a pure story."
        pure_path = create_pure_story_file(series_path, "custom.md", content)
        assert os.path.exists(pure_path)
        with open(pure_path, "r", encoding="utf-8") as fh:
            data = fh.read()
        assert content in data
