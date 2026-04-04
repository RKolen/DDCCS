"""Story-specific export helpers.

Provides utilities for exporting stories to various text formats and
bundling campaign content. Integrates with existing story file utilities.
"""

import os
import re
import zipfile
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from src.utils.file_io import read_text_file
from src.utils.path_utils import get_campaigns_dir, get_characters_dir, get_npcs_dir
from src.utils.story_file_helpers import get_story_file_paths_in_series

_MARKDOWN_HEADER = re.compile(r"^#{1,6}\s+")
_MARKDOWN_BOLD = re.compile(r"\*\*(.+?)\*\*")
_MARKDOWN_ITALIC = re.compile(r"\*(.+?)\*")
_MARKDOWN_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_MARKDOWN_HR = re.compile(r"^---+$")
_SECTION_PREFIXES = (
    "## Consultant Notes",
    "## Story Hooks",
    "## Session Results",
    "## Character Development",
)


class StoryExportFormat(Enum):
    """Supported export formats for stories."""

    HTML = "html"
    MARKDOWN = "md"
    PLAIN_TEXT = "txt"
    JSON = "json"


@dataclass
class StoryExportOptions:
    """Options for story export."""

    export_format: StoryExportFormat = StoryExportFormat.MARKDOWN
    include_metadata: bool = True
    include_consultant_notes: bool = False
    include_session_results: bool = True
    include_story_hooks: bool = True
    include_character_development: bool = True
    wrap_width: int = 80


@dataclass
class SeriesExportOptions:
    """Options for series export."""

    export_format: StoryExportFormat = StoryExportFormat.PLAIN_TEXT
    combine_stories: bool = True
    include_table_of_contents: bool = True
    story_options: StoryExportOptions = field(default_factory=StoryExportOptions)


class StoryExportHelper:
    """Helper for exporting stories to various formats."""

    def __init__(self, workspace_path: str) -> None:
        """Initialize export helper.

        Args:
            workspace_path: Root workspace path.
        """
        self.workspace_path = workspace_path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def export_story(
        self,
        story_path: str,
        output_path: str,
        options: Optional[StoryExportOptions] = None,
    ) -> str:
        """Export a single story to the specified format.

        Args:
            story_path: Path to story file.
            output_path: Destination path for the exported file.
            options: Export options (defaults applied if None).

        Returns:
            Path to the exported file.
        """
        resolved_options = options or StoryExportOptions()
        content = self.prepare_story_for_export(story_path, resolved_options)
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return output_path

    def export_series(
        self,
        series_name: str,
        output_path: str,
        options: Optional[SeriesExportOptions] = None,
    ) -> str:
        """Export an entire series of stories.

        When ``combine_stories`` is True in options, all stories are merged
        into a single output file. Otherwise each story is written to its
        own file inside ``output_path`` (treated as a directory).

        Args:
            series_name: Name of the series (campaign directory name).
            output_path: Destination path (file when combining, dir otherwise).
            options: Export options.

        Returns:
            Path to the exported file or directory.
        """
        resolved_options = options or SeriesExportOptions()
        story_options = resolved_options.story_options
        story_files = get_story_file_paths_in_series(self.workspace_path, series_name)
        if resolved_options.combine_stories:
            return self._export_combined(
                series_name, story_files, output_path, resolved_options
            )
        return self._export_separate(story_files, output_path, story_options)

    def export_campaign_bundle(
        self,
        campaign_name: str,
        output_path: str,
        include_characters: bool = True,
        include_npcs: bool = True,
    ) -> str:
        """Export a complete campaign bundle as a zip archive.

        Args:
            campaign_name: Name of the campaign.
            output_path: Path for the output zip file.
            include_characters: Include character JSON files.
            include_npcs: Include NPC JSON files.

        Returns:
            Path to the exported bundle zip file.
        """
        campaigns_dir = get_campaigns_dir(self.workspace_path)
        series_dir = os.path.join(campaigns_dir, campaign_name)
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            if os.path.isdir(series_dir):
                for fname in sorted(os.listdir(series_dir)):
                    fpath = os.path.join(series_dir, fname)
                    if os.path.isfile(fpath):
                        zf.write(fpath, os.path.join("stories", fname))

            if include_characters:
                chars_dir = get_characters_dir(self.workspace_path)
                if os.path.isdir(chars_dir):
                    for fname in sorted(os.listdir(chars_dir)):
                        if fname.endswith(".json"):
                            fpath = os.path.join(chars_dir, fname)
                            zf.write(fpath, os.path.join("characters", fname))

            if include_npcs:
                npcs_dir = get_npcs_dir(self.workspace_path)
                if os.path.isdir(npcs_dir):
                    for fname in sorted(os.listdir(npcs_dir)):
                        if fname.endswith(".json"):
                            fpath = os.path.join(npcs_dir, fname)
                            zf.write(fpath, os.path.join("npcs", fname))

        return output_path

    def prepare_story_for_export(
        self,
        story_path: str,
        options: StoryExportOptions,
    ) -> str:
        """Prepare story content for export by applying options.

        Filters out sections based on options and converts the content
        to the target format.

        Args:
            story_path: Path to story file.
            options: Export options controlling which sections to include.

        Returns:
            Prepared content string ready for writing.
        """
        raw = self._read_file(story_path)
        content = self._filter_sections(raw, options)

        if options.export_format == StoryExportFormat.PLAIN_TEXT:
            content = self._to_plain_text(content, options.wrap_width)
        elif options.export_format == StoryExportFormat.HTML:
            content = self._to_html(content)

        return content

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _export_combined(
        self,
        series_name: str,
        story_files: list[str],
        output_path: str,
        series_options: SeriesExportOptions,
    ) -> str:
        """Write all stories as one combined file.

        Args:
            series_name: Series name (used for table-of-contents heading).
            story_files: Sorted list of story file paths.
            output_path: Destination file path.
            series_options: Series-level export options (contains story_options).

        Returns:
            Path to the written file.
        """
        story_options = series_options.story_options
        parts: list[str] = []
        if series_options.include_table_of_contents:
            parts.append(self._build_toc(series_name, story_files))
        for filepath in story_files:
            parts.append(self.prepare_story_for_export(filepath, story_options))
        combined = "\n\n---\n\n".join(parts)
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(combined)
        return output_path

    def _export_separate(
        self,
        story_files: list[str],
        output_path: str,
        story_options: StoryExportOptions,
    ) -> str:
        """Write each story to its own file inside output_path directory.

        Args:
            story_files: Sorted list of story file paths.
            output_path: Destination directory path.
            story_options: Per-story export options.

        Returns:
            Path to the output directory.
        """
        os.makedirs(output_path, exist_ok=True)
        for filepath in story_files:
            base = os.path.splitext(os.path.basename(filepath))[0]
            ext = story_options.export_format.value
            dest = os.path.join(output_path, f"{base}.{ext}")
            self.export_story(filepath, dest, story_options)
        return output_path

    def _filter_sections(self, content: str, options: StoryExportOptions) -> str:
        """Remove sections according to export options.

        Args:
            content: Raw story content.
            options: Export options.

        Returns:
            Filtered content string.
        """
        exclusion_map = {
            "## Consultant Notes": not options.include_consultant_notes,
            "## Session Results": not options.include_session_results,
            "## Story Hooks": not options.include_story_hooks,
            "## Character Development": not options.include_character_development,
        }

        lines = content.splitlines(keepends=True)
        result: list[str] = []
        skip = False

        for line in lines:
            stripped = line.rstrip()
            matched_prefix: Optional[str] = None
            for prefix in _SECTION_PREFIXES:
                if stripped.startswith(prefix):
                    matched_prefix = prefix
                    break

            if matched_prefix is not None:
                skip = exclusion_map.get(matched_prefix, False)

            if not skip:
                result.append(line)

        return "".join(result)

    def _to_plain_text(self, content: str, wrap_width: int) -> str:
        """Convert markdown content to plain text.

        Args:
            content: Markdown content.
            wrap_width: Target line wrap width.

        Returns:
            Plain text string.
        """
        text = _MARKDOWN_HEADER.sub("", content)
        text = _MARKDOWN_BOLD.sub(r"\1", text)
        text = _MARKDOWN_ITALIC.sub(r"\1", text)
        text = _MARKDOWN_LINK.sub(r"\1", text)
        text = _MARKDOWN_HR.sub("", text)

        if wrap_width > 0:
            wrapped_lines: list[str] = []
            for line in text.splitlines():
                if len(line) <= wrap_width:
                    wrapped_lines.append(line)
                else:
                    words = line.split()
                    current = ""
                    for word in words:
                        if current and len(current) + 1 + len(word) > wrap_width:
                            wrapped_lines.append(current)
                            current = word
                        else:
                            current = f"{current} {word}" if current else word
                    if current:
                        wrapped_lines.append(current)
            text = "\n".join(wrapped_lines)

        return text

    def _to_html(self, content: str) -> str:
        """Convert markdown content to simple HTML.

        Handles headers, bold, italic, paragraphs, and horizontal rules.

        Args:
            content: Markdown content.

        Returns:
            HTML string.
        """
        lines = content.splitlines()
        html_lines: list[str] = ["<html><body>"]
        in_paragraph = False

        for line in lines:
            stripped = line.strip()

            if not stripped:
                if in_paragraph:
                    html_lines.append("</p>")
                    in_paragraph = False
                continue

            header_match = _MARKDOWN_HEADER.match(stripped)
            if header_match:
                if in_paragraph:
                    html_lines.append("</p>")
                    in_paragraph = False
                level = len(header_match.group(0).rstrip().lstrip("#"))
                text = _MARKDOWN_HEADER.sub("", stripped).strip()
                html_lines.append(f"<h{level}>{text}</h{level}>")
                continue

            if _MARKDOWN_HR.match(stripped):
                if in_paragraph:
                    html_lines.append("</p>")
                    in_paragraph = False
                html_lines.append("<hr/>")
                continue

            inline = _MARKDOWN_BOLD.sub(r"<strong>\1</strong>", stripped)
            inline = _MARKDOWN_ITALIC.sub(r"<em>\1</em>", inline)
            inline = _MARKDOWN_LINK.sub(r'<a href="\2">\1</a>', inline)

            if not in_paragraph:
                html_lines.append("<p>")
                in_paragraph = True
            html_lines.append(inline)

        if in_paragraph:
            html_lines.append("</p>")
        html_lines.append("</body></html>")
        return "\n".join(html_lines)

    def _build_toc(self, series_name: str, story_files: list[str]) -> str:
        """Build a table of contents for a series.

        Args:
            series_name: Name of the series.
            story_files: Sorted list of story file paths.

        Returns:
            Table of contents as markdown string.
        """
        lines = [f"# {series_name}", "", "## Table of Contents", ""]
        for idx, fp in enumerate(story_files, start=1):
            name = os.path.splitext(os.path.basename(fp))[0]
            lines.append(f"{idx}. {name}")
        return "\n".join(lines)

    def _read_file(self, filepath: str) -> str:
        """Read file content, returning empty string on missing or error.

        Args:
            filepath: Path to the file.

        Returns:
            File content as string, empty string when the file is absent.
        """
        return read_text_file(filepath) or ""
