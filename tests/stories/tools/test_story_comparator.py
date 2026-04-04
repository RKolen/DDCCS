"""Tests for src/stories/tools/story_comparator.py.

Uses temporary files and the real Example_Campaign data.
"""

import os
import shutil
import tempfile

from src.utils.path_utils import get_campaigns_dir
from src.stories.tools.story_comparator import (
    ChangeType,
    StoryComparator,
    compare_story_texts,
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
    path = os.path.join(directory, filename)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


def test_compare_identical_files_no_changes():
    """Comparing identical files should produce zero changes."""
    content = "The party set out at dawn.\nThe road was long.\n"
    with tempfile.TemporaryDirectory() as tmp:
        path_a = _write_file(tmp, "a.md", content)
        path_b = _write_file(tmp, "b.md", content)
        comp = StoryComparator(tmp)
        diff = comp.compare_stories(path_a, path_b)
        assert not diff.has_changes
        assert diff.similarity_score == 1.0


def test_compare_different_files_has_changes():
    """Comparing different files should detect changes."""
    with tempfile.TemporaryDirectory() as tmp:
        path_a = _write_file(tmp, "a.md", "Aragorn stood firm.\n")
        path_b = _write_file(tmp, "b.md", "Frodo stepped forward.\n")
        comp = StoryComparator(tmp)
        diff = comp.compare_stories(path_a, path_b)
        assert diff.has_changes
        assert diff.similarity_score < 1.0


def test_compare_stories_similarity_is_between_zero_and_one():
    """Similarity score should always be in [0, 1] range."""
    with tempfile.TemporaryDirectory() as tmp:
        path_a = _write_file(tmp, "a.md", "Alpha beta gamma.")
        path_b = _write_file(tmp, "b.md", "Delta epsilon zeta.")
        comp = StoryComparator(tmp)
        diff = comp.compare_stories(path_a, path_b)
        assert 0.0 <= diff.similarity_score <= 1.0


def test_compare_stories_addition_detected():
    """Adding new lines should result in ADDITION change type."""
    with tempfile.TemporaryDirectory() as tmp:
        path_a = _write_file(tmp, "a.md", "Line one.\n")
        path_b = _write_file(tmp, "b.md", "Line one.\nLine two.\n")
        comp = StoryComparator(tmp)
        diff = comp.compare_stories(path_a, path_b)
        change_types = {c.change_type for c in diff.changes}
        assert ChangeType.ADDITION in change_types


def test_compare_stories_deletion_detected():
    """Removing lines should result in DELETION change type."""
    with tempfile.TemporaryDirectory() as tmp:
        path_a = _write_file(tmp, "a.md", "Line one.\nLine two.\n")
        path_b = _write_file(tmp, "b.md", "Line one.\n")
        comp = StoryComparator(tmp)
        diff = comp.compare_stories(path_a, path_b)
        change_types = {c.change_type for c in diff.changes}
        assert ChangeType.DELETION in change_types


def test_significant_changes_filters_low_significance():
    """significant_changes should only include changes with significance >= 5."""
    with tempfile.TemporaryDirectory() as tmp:
        path_a = _write_file(tmp, "a.md", "a\n")
        path_b = _write_file(tmp, "b.md", "b\n")
        comp = StoryComparator(tmp)
        diff = comp.compare_stories(path_a, path_b)
        for change in diff.significant_changes:
            assert change.significance >= 5


def test_find_narrative_changes_excludes_headers():
    """Narrative filter should exclude markdown header-only changes."""
    with tempfile.TemporaryDirectory() as tmp:
        path_a = _write_file(tmp, "a.md", "## Old Title\n")
        path_b = _write_file(tmp, "b.md", "## New Title\n")
        comp = StoryComparator(tmp)
        diff = comp.compare_stories(path_a, path_b)
        narrative = comp.find_narrative_changes(diff)
        # Headers should not count as narrative
        for change in narrative:
            assert not change.old_content.strip().startswith("#")
            assert not change.new_content.strip().startswith("#")


def test_generate_change_report_markdown_contains_header():
    """Markdown report should start with a level-2 heading."""
    with tempfile.TemporaryDirectory() as tmp:
        path_a = _write_file(tmp, "a.md", "Once upon a time.\n")
        path_b = _write_file(tmp, "b.md", "Once upon a different time.\n")
        comp = StoryComparator(tmp)
        diff = comp.compare_stories(path_a, path_b)
        report = comp.generate_change_report(diff, "markdown")
        assert report.startswith("## Story Diff")


def test_generate_change_report_text_format():
    """Text format report should not contain markdown headings."""
    with tempfile.TemporaryDirectory() as tmp:
        path_a = _write_file(tmp, "a.md", "The knight rode.\n")
        path_b = _write_file(tmp, "b.md", "The ranger walked.\n")
        comp = StoryComparator(tmp)
        diff = comp.compare_stories(path_a, path_b)
        report = comp.generate_change_report(diff, "text")
        assert not report.startswith("##")
        assert "Story Diff" in report


def test_compare_series_returns_consecutive_diffs():
    """compare_series should return one diff per consecutive story pair."""
    tmp = tempfile.mkdtemp()
    try:
        series_dir = os.path.join(get_campaigns_dir(tmp), "MySeries")
        os.makedirs(series_dir)
        for num, content in [
            ("001", "Chapter one.\n"),
            ("002", "Chapter two.\n"),
            ("003", "Chapter three.\n"),
        ]:
            with open(
                os.path.join(series_dir, f"{num}_story.md"), "w", encoding="utf-8"
            ) as fh:
                fh.write(content)
        comp = StoryComparator(tmp)
        diffs = comp.compare_series("MySeries", 1, 3)
        assert len(diffs) == 2
    finally:
        shutil.rmtree(tmp)


def test_compare_story_texts_convenience_function():
    """compare_story_texts should return a similarity score and a diff list."""
    text_a = "The hero stood tall.\n"
    text_b = "The hero fell down.\n"
    similarity, diffs = compare_story_texts(text_a, text_b)
    assert 0.0 <= similarity <= 1.0
    assert len(diffs) > 0


def test_compare_story_texts_identical_returns_empty_diffs():
    """Identical texts should produce no diffs."""
    text = "Same line.\n"
    similarity, diffs = compare_story_texts(text, text)
    assert similarity == 1.0
    assert not diffs
