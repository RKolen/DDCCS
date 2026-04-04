"""Tests for src/stories/tools/story_export_helpers.py.

Uses temporary workspaces for file I/O isolation.
"""

import os
import tempfile
import zipfile

from src.utils.path_utils import get_campaigns_dir
from src.stories.tools.story_export_helpers import (
    SeriesExportOptions,
    StoryExportFormat,
    StoryExportHelper,
    StoryExportOptions,
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
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


def test_export_story_markdown_creates_file():
    """Exporting a story to markdown should create a file at the output path."""
    with tempfile.TemporaryDirectory() as tmp:
        story = _write_file(tmp, "001_story.md", "## Adventure\n\nAragorn rode.\n")
        output = os.path.join(tmp, "out", "001_story.md")
        helper = StoryExportHelper(tmp)
        result = helper.export_story(story, output)
        assert os.path.isfile(result)
        assert result == output


def test_export_story_plain_text_strips_headers():
    """Plain text export should remove markdown header markers."""
    with tempfile.TemporaryDirectory() as tmp:
        story = _write_file(tmp, "001_story.md", "## Title\n\nContent here.\n")
        output = os.path.join(tmp, "story.txt")
        options = StoryExportOptions(export_format=StoryExportFormat.PLAIN_TEXT)
        helper = StoryExportHelper(tmp)
        helper.export_story(story, output, options)
        with open(output, encoding="utf-8") as fh:
            content = fh.read()
        assert "##" not in content
        assert "Title" in content


def test_export_story_html_contains_html_tags():
    """HTML export should wrap content in html/body tags."""
    with tempfile.TemporaryDirectory() as tmp:
        story = _write_file(tmp, "001_story.md", "## Chapter One\n\nA brave knight.\n")
        output = os.path.join(tmp, "story.html")
        options = StoryExportOptions(export_format=StoryExportFormat.HTML)
        helper = StoryExportHelper(tmp)
        helper.export_story(story, output, options)
        with open(output, encoding="utf-8") as fh:
            content = fh.read()
        assert "<html>" in content
        assert "<h2>" in content


def test_export_story_excludes_consultant_notes_when_disabled():
    """Exporting with include_consultant_notes=False should strip that section."""
    content = (
        "## Story Content\n\nThe story.\n\n"
        "## Consultant Notes\n\nSome notes here.\n"
    )
    with tempfile.TemporaryDirectory() as tmp:
        story = _write_file(tmp, "001_story.md", content)
        output = os.path.join(tmp, "story.md")
        options = StoryExportOptions(include_consultant_notes=False)
        helper = StoryExportHelper(tmp)
        helper.export_story(story, output, options)
        with open(output, encoding="utf-8") as fh:
            result = fh.read()
        assert "Consultant Notes" not in result
        assert "The story" in result


def test_export_series_combined_creates_single_file():
    """Series export with combine_stories=True should produce one file."""
    with tempfile.TemporaryDirectory() as tmp:
        series_dir = os.path.join(get_campaigns_dir(tmp), "TestCampaign")
        _write_file(series_dir, "001_part1.md", "## Part 1\n\nFirst chapter.\n")
        _write_file(series_dir, "002_part2.md", "## Part 2\n\nSecond chapter.\n")
        output = os.path.join(tmp, "combined.md")
        options = SeriesExportOptions(combine_stories=True)
        helper = StoryExportHelper(tmp)
        result = helper.export_series("TestCampaign", output, options)
        assert os.path.isfile(result)
        with open(result, encoding="utf-8") as fh:
            content = fh.read()
        assert "First chapter" in content
        assert "Second chapter" in content


def test_export_series_no_combine_creates_directory():
    """Series export with combine_stories=False should produce a directory."""
    with tempfile.TemporaryDirectory() as tmp:
        series_dir = os.path.join(get_campaigns_dir(tmp), "TestCampaign")
        _write_file(series_dir, "001_part1.md", "## Part 1\n\nFirst.\n")
        _write_file(series_dir, "002_part2.md", "## Part 2\n\nSecond.\n")
        output_dir = os.path.join(tmp, "exported")
        options = SeriesExportOptions(
            combine_stories=False,
            story_options=StoryExportOptions(export_format=StoryExportFormat.PLAIN_TEXT),
        )
        helper = StoryExportHelper(tmp)
        helper.export_series("TestCampaign", output_dir, options)
        assert os.path.isdir(output_dir)
        exported_files = os.listdir(output_dir)
        assert len(exported_files) == 2


def test_export_campaign_bundle_creates_zip():
    """Bundle export should create a valid zip file."""
    with tempfile.TemporaryDirectory() as tmp:
        series_dir = os.path.join(get_campaigns_dir(tmp), "TestCampaign")
        _write_file(series_dir, "001_story.md", "## Adventure\n\nContent.\n")
        output_zip = os.path.join(tmp, "bundle.zip")
        helper = StoryExportHelper(tmp)
        result = helper.export_campaign_bundle(
            "TestCampaign",
            output_zip,
            include_characters=False,
            include_npcs=False,
        )
        assert os.path.isfile(result)
        assert zipfile.is_zipfile(result)
        with zipfile.ZipFile(result) as zf:
            names = zf.namelist()
            assert any("stories" in n for n in names)


def test_export_series_includes_table_of_contents():
    """Combined series export with TOC enabled should include story names."""
    with tempfile.TemporaryDirectory() as tmp:
        series_dir = os.path.join(get_campaigns_dir(tmp), "TestCampaign")
        _write_file(series_dir, "001_intro.md", "Introduction content.\n")
        _write_file(series_dir, "002_climax.md", "Climax content.\n")
        output = os.path.join(tmp, "series.md")
        options = SeriesExportOptions(
            combine_stories=True,
            include_table_of_contents=True,
        )
        helper = StoryExportHelper(tmp)
        helper.export_series("TestCampaign", output, options)
        with open(output, encoding="utf-8") as fh:
            content = fh.read()
        assert "Table of Contents" in content


def test_prepare_story_plain_text_wraps_long_lines():
    """Plain text export should wrap lines longer than wrap_width."""
    long_line = "word " * 40
    with tempfile.TemporaryDirectory() as tmp:
        story = _write_file(tmp, "001_story.md", long_line)
        options = StoryExportOptions(
            export_format=StoryExportFormat.PLAIN_TEXT,
            wrap_width=40,
        )
        helper = StoryExportHelper(tmp)
        content = helper.prepare_story_for_export(story, options)
        for line in content.splitlines():
            assert len(line) <= 40
