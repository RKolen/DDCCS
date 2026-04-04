"""Tests for src/stories/tools/story_import_helpers.py.

Uses temporary workspaces for file I/O isolation.
"""

import json
import os
import tempfile

from src.stories.tools.story_import_helpers import (
    ImportOptions,
    StoryImportHelper,
)


def _write_file(directory: str, filename: str, content: str) -> str:
    """Write content to a file and return its path.

    Args:
        directory: Directory to write in.
        filename: File name.
        content: Content to write.

    Returns:
        Absolute path to the written file.
    """
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, filename)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


def test_import_from_markdown_creates_numbered_file():
    """Importing a markdown file should create a numbered story in the series."""
    with tempfile.TemporaryDirectory() as tmp:
        source = _write_file(tmp, "my_story.md", "## Title\n\nContent.\n")
        options = ImportOptions(target_series="TestSeries")
        helper = StoryImportHelper(tmp)
        result = helper.import_from_markdown(source, options)
        assert result.success
        assert result.story_path is not None
        assert os.path.isfile(result.story_path)
        assert "001_" in os.path.basename(result.story_path)


def test_import_from_markdown_increments_numbering():
    """Second import should create a 002_ file when a 001_ already exists."""
    with tempfile.TemporaryDirectory() as tmp:
        from src.utils.path_utils import get_campaigns_dir  # pylint: disable=import-outside-toplevel
        series_dir = os.path.join(get_campaigns_dir(tmp), "TestSeries")
        os.makedirs(series_dir)
        existing = os.path.join(series_dir, "001_existing.md")
        with open(existing, "w", encoding="utf-8") as fh:
            fh.write("Existing story.\n")
        source = _write_file(tmp, "new_story.md", "New content.\n")
        options = ImportOptions(target_series="TestSeries")
        helper = StoryImportHelper(tmp)
        result = helper.import_from_markdown(source, options)
        assert result.success
        assert "002_" in os.path.basename(result.story_path)


def test_import_from_text_wraps_in_markdown():
    """Importing a plain text file should wrap it in a markdown header."""
    with tempfile.TemporaryDirectory() as tmp:
        source = _write_file(tmp, "tale.txt", "A long time ago in a forest far away.\n")
        options = ImportOptions(target_series="TestSeries")
        helper = StoryImportHelper(tmp)
        result = helper.import_from_text(source, options)
        assert result.success
        with open(result.story_path, encoding="utf-8") as fh:
            content = fh.read()
        assert "## Story Content" in content
        assert "A long time ago" in content


def test_import_from_json_reads_content_field():
    """Importing a JSON file should use the 'content' key as the story body."""
    with tempfile.TemporaryDirectory() as tmp:
        data = {"title": "My Tale", "content": "Once upon a time the hero ventured out."}
        source = os.path.join(tmp, "story.json")
        with open(source, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        options = ImportOptions(target_series="TestSeries")
        helper = StoryImportHelper(tmp)
        result = helper.import_from_json(source, options)
        assert result.success
        with open(result.story_path, encoding="utf-8") as fh:
            content = fh.read()
        assert "Once upon a time" in content


def test_import_from_json_missing_content_fails():
    """JSON import without a 'content' field should fail gracefully."""
    with tempfile.TemporaryDirectory() as tmp:
        data = {"title": "Empty"}
        source = os.path.join(tmp, "story.json")
        with open(source, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        options = ImportOptions(target_series="TestSeries")
        helper = StoryImportHelper(tmp)
        result = helper.import_from_json(source, options)
        assert not result.success
        assert result.errors


def test_import_story_without_series_fails():
    """Importing without a target_series should return a failure result."""
    with tempfile.TemporaryDirectory() as tmp:
        source = _write_file(tmp, "story.md", "Content.\n")
        helper = StoryImportHelper(tmp)
        result = helper.import_story(source)
        assert not result.success
        assert result.errors


def test_import_story_detects_format_from_extension():
    """import_story should auto-detect markdown format from .md extension."""
    with tempfile.TemporaryDirectory() as tmp:
        source = _write_file(tmp, "adventure.md", "## Adventure\n\nRode forth.\n")
        helper = StoryImportHelper(tmp)
        result = helper.import_story(source, target_series="Camp")
        assert result.success


def test_batch_import_imports_all_files():
    """batch_import should process all supported files in a directory."""
    with tempfile.TemporaryDirectory() as tmp:
        source_dir = os.path.join(tmp, "sources")
        _write_file(source_dir, "one.md", "Story one.\n")
        _write_file(source_dir, "two.md", "Story two.\n")
        _write_file(source_dir, "notes.txt", "Just a note.\n")
        _write_file(source_dir, "readme.pdf", "Not imported.\n")
        helper = StoryImportHelper(tmp)
        results = helper.batch_import(source_dir, "TestSeries")
        successful = [r for r in results if r.success]
        assert len(successful) == 3


def test_batch_import_missing_directory_returns_error():
    """batch_import on a missing directory should return a single failure."""
    with tempfile.TemporaryDirectory() as tmp:
        helper = StoryImportHelper(tmp)
        results = helper.batch_import("/nonexistent/path", "TestSeries")
        assert len(results) == 1
        assert not results[0].success


def test_detect_characters_in_content_finds_known_names():
    """detect_characters_in_content should find names present in content."""
    content = "Aragorn and Frodo discussed the road ahead."
    helper = StoryImportHelper("/tmp")
    found = helper.detect_characters_in_content(content, ["Aragorn", "Frodo", "Gandalf"])
    assert "Aragorn" in found
    assert "Frodo" in found
    assert "Gandalf" not in found


def test_detect_characters_case_insensitive():
    """Character detection should be case-insensitive."""
    content = "FRODO ran across the field."
    helper = StoryImportHelper("/tmp")
    found = helper.detect_characters_in_content(content, ["Frodo"])
    assert "Frodo" in found


def test_import_detects_locations():
    """Importing a story mentioning common locations should detect them."""
    with tempfile.TemporaryDirectory() as tmp:
        source = _write_file(
            tmp, "story.md", "They arrived at the Tavern near the Castle.\n"
        )
        options = ImportOptions(target_series="TestSeries", auto_detect_locations=True)
        helper = StoryImportHelper(tmp)
        result = helper.import_story(source, options=options)
        assert result.success
        assert len(result.locations_detected) > 0
