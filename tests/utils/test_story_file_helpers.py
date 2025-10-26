"""Unit tests for `src.utils.story_file_helpers`.

These tests exercise the next-filename logic and numbered-file detection
using an isolated temporary directory.
"""
from tests.test_helpers import setup_test_environment, import_module


setup_test_environment()

sfh = import_module("src.utils.story_file_helpers")
list_story_files = sfh.list_story_files
has_numbered_story_files = sfh.has_numbered_story_files
next_filename_for_dir = sfh.next_filename_for_dir


def test_list_and_detect_numbered_files(tmp_path):
    """Listing returns only numbered story markdown files and detection is True."""
    d = tmp_path / "series"
    d.mkdir()
    # Create a mix of files
    (d / "001_intro.md").write_text("# Intro")
    (d / "notes.txt").write_text("notes")
    (d / "002_scene.md").write_text("# Scene")

    files = list_story_files(str(d))
    assert "001_intro.md" in files
    assert "002_scene.md" in files
    assert has_numbered_story_files(str(d)) is True


def test_next_filename_for_empty_and_nonempty(tmp_path):
    """next_filename_for_dir returns 001_ for empty dir and increments after files exist."""
    d = tmp_path / "series2"
    d.mkdir()
    # empty directory -> first filename
    filename, _ = next_filename_for_dir(str(d), "A New Tale")
    assert filename.startswith("001_")

    # create a file and ensure next increments
    (d / filename).write_text("# A New Tale")
    filename2, _ = next_filename_for_dir(str(d), "Another")
    assert filename2.startswith("002_")
