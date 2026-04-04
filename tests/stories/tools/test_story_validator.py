"""Tests for src/stories/tools/story_validator.py.

Uses temporary workspaces and in-memory content for isolation.
"""

import os
import tempfile

from src.utils.path_utils import get_campaigns_dir
from src.stories.tools.story_validator import (
    StoryValidator,
    ValidationSeverity,
)


def _write_story(directory: str, filename: str, content: str) -> str:
    """Write a story file and return its path.

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


def test_validate_valid_story_returns_is_valid_true():
    """A well-formed story should validate without errors."""
    content = "## Adventure Begins\n\nAragorn rode through the forest.\n"
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_story(tmp, "001_story.md", content)
        validator = StoryValidator(tmp)
        result = validator.validate_story(path)
        assert result.is_valid
        assert result.error_count == 0


def test_validate_empty_file_returns_error():
    """An empty file should produce an ERROR-level issue."""
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_story(tmp, "001_story.md", "")
        validator = StoryValidator(tmp)
        result = validator.validate_story(path)
        assert not result.is_valid
        assert result.error_count >= 1
        rule_names = {issue.rule_name for issue in result.issues}
        assert "empty_file" in rule_names


def test_validate_very_short_story_returns_warning():
    """A very short story should produce a warning."""
    content = "Just a few words here."
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_story(tmp, "001_story.md", content)
        validator = StoryValidator(tmp)
        result = validator.validate_story(path)
        warnings = [
            i for i in result.issues if i.severity == ValidationSeverity.WARNING
        ]
        assert any(i.rule_name == "too_short" for i in warnings)


def test_validate_no_headers_produces_info():
    """A story without markdown headers should produce an INFO issue."""
    content = "The party walked through the vale.\n" * 10
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_story(tmp, "001_story.md", content)
        validator = StoryValidator(tmp)
        result = validator.validate_story(path)
        info_issues = [
            i for i in result.issues if i.severity == ValidationSeverity.INFO
        ]
        assert any(i.rule_name == "no_headers" for i in info_issues)


def test_check_links_flags_broken_relative_link():
    """A broken relative link in the story should produce a WARNING."""
    content = "See [the map](nonexistent_file.md) for details.\n"
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_story(tmp, "001_story.md", content)
        validator = StoryValidator(tmp)
        issues = validator.check_links(content, path)
        assert any(i.rule_name == "broken_link" for i in issues)


def test_check_links_ignores_external_urls():
    """External HTTP links should not be flagged as broken."""
    content = "Read more at [the wiki](https://example.com/wiki).\n"
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_story(tmp, "001_story.md", content)
        validator = StoryValidator(tmp)
        issues = validator.check_links(content, path)
        assert not any(i.rule_name == "broken_link" for i in issues)


def test_check_links_ignores_anchor_links():
    """Anchor-only links (#section) should not be flagged."""
    content = "See [this section](#section-name) for more.\n"
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_story(tmp, "001_story.md", content)
        validator = StoryValidator(tmp)
        issues = validator.check_links(content, path)
        assert not any(i.rule_name == "broken_link" for i in issues)


def test_check_style_detects_repeated_word():
    """The style checker should flag adjacent repeated words."""
    content = "The the brave knight rode forth.\n"
    with tempfile.TemporaryDirectory() as tmp:
        validator = StoryValidator(tmp)
        issues = validator.check_style(content)
        assert any(i.rule_name == "repeated_word" for i in issues)


def test_validate_series_returns_result_per_story():
    """validate_series should return one ValidationResult per story file."""
    with tempfile.TemporaryDirectory() as tmp:
        series_dir = os.path.join(get_campaigns_dir(tmp), "TestSeries")
        os.makedirs(series_dir)
        for num, content in [
            ("001", "## Part One\n\nThe adventure began.\n"),
            ("002", "## Part Two\n\nThe quest continued.\n"),
        ]:
            _write_story(series_dir, f"{num}_story.md", content)
        validator = StoryValidator(tmp)
        results = validator.validate_series("TestSeries")
        assert len(results) == 2
        assert all(isinstance(r.is_valid, bool) for r in results.values())


def test_validate_series_empty_campaign_returns_empty_dict():
    """An empty or missing series should return an empty dict."""
    with tempfile.TemporaryDirectory() as tmp:
        validator = StoryValidator(tmp)
        results = validator.validate_series("NonExistent")
        assert not results


def test_generate_validation_report_markdown_format():
    """Markdown validation report should start with level-2 heading."""
    content = "## Scene\n\nWords " * 10
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_story(tmp, "001_story.md", content)
        validator = StoryValidator(tmp)
        result = validator.validate_story(path)
        report = validator.generate_validation_report(result, "markdown")
        assert report.startswith("## Validation Report")


def test_generate_validation_report_text_format():
    """Text format report should not start with markdown heading."""
    content = "## Scene\n\n" + "Content words. " * 10
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_story(tmp, "001_story.md", content)
        validator = StoryValidator(tmp)
        result = validator.validate_story(path)
        report = validator.generate_validation_report(result, "text")
        assert not report.startswith("##")
        assert "Validation" in report


def test_strict_validation_includes_style_suggestions():
    """Strict mode should include style checks in the result."""
    content = "## Story\n\n" + ("The the knight rode. " * 5)
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_story(tmp, "001_story.md", content)
        validator = StoryValidator(tmp)
        result = validator.validate_story(path, strict=True)
        all_rule_names = {i.rule_name for i in result.issues}
        assert "repeated_word" in all_rule_names


def test_error_count_and_warning_count_properties():
    """error_count and warning_count properties should reflect issue severity."""
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_story(tmp, "001_story.md", "")
        validator = StoryValidator(tmp)
        result = validator.validate_story(path)
        assert result.error_count >= 1
        assert result.warning_count >= 0
