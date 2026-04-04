"""Story import utilities.

Provides utilities for importing stories from external formats
into the campaign directory structure.
"""

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from src.utils.path_utils import get_campaigns_dir
from src.utils.story_file_helpers import next_filename_for_dir

_HEADER_RE = re.compile(r"^#{1,6}\s+(.+)$")


class ImportFormat(Enum):
    """Supported import formats."""

    MARKDOWN = "md"
    PLAIN_TEXT = "txt"
    JSON = "json"


@dataclass
class ImportResult:
    """Result of an import operation."""

    success: bool
    story_path: Optional[str] = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    characters_detected: list[str] = field(default_factory=list)
    locations_detected: list[str] = field(default_factory=list)


@dataclass
class ImportOptions:
    """Options for story import."""

    import_format: ImportFormat = ImportFormat.MARKDOWN
    auto_detect_characters: bool = True
    auto_detect_locations: bool = True
    create_missing_npcs: bool = False
    split_on_headers: bool = True
    target_series: Optional[str] = None


class StoryImportHelper:
    """Helper for importing stories from external file formats."""

    _LOCATION_KEYWORDS = re.compile(
        r"\b(Inn|Tavern|Castle|Forest|Mountain|River|City|Village|Tower|Temple|Dungeon"
        r"|Cave|Road|Bridge|Market|Harbor|Keep|Ruins|Palace|Camp|Hall)\b",
        re.IGNORECASE,
    )

    def __init__(self, workspace_path: str) -> None:
        """Initialize import helper.

        Args:
            workspace_path: Root workspace path.
        """
        self.workspace_path = workspace_path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def import_story(
        self,
        source_path: str,
        target_series: Optional[str] = None,
        options: Optional[ImportOptions] = None,
    ) -> ImportResult:
        """Import a story from an external file.

        Detects format from file extension when options.import_format is
        not explicitly set, then delegates to the appropriate importer.

        Args:
            source_path: Path to source file.
            target_series: Optional series to add story to (overrides options).
            options: Import options.

        Returns:
            ImportResult with import status and metadata.
        """
        resolved_options = options or ImportOptions()
        if target_series:
            resolved_options.target_series = target_series

        ext = os.path.splitext(source_path)[1].lower().lstrip(".")
        format_map = {f.value: f for f in ImportFormat}
        detected_format = format_map.get(ext, ImportFormat.MARKDOWN)
        resolved_options.import_format = detected_format

        if resolved_options.import_format == ImportFormat.MARKDOWN:
            return self.import_from_markdown(source_path, resolved_options)
        if resolved_options.import_format == ImportFormat.PLAIN_TEXT:
            return self.import_from_text(source_path, resolved_options)
        if resolved_options.import_format == ImportFormat.JSON:
            return self.import_from_json(source_path, resolved_options)

        result = ImportResult(success=False)
        result.errors.append(
            f"Unsupported import format: {resolved_options.import_format}"
        )
        return result

    def import_from_markdown(
        self,
        source_path: str,
        options: ImportOptions,
    ) -> ImportResult:
        """Import from a markdown file.

        Args:
            source_path: Path to markdown file.
            options: Import options.

        Returns:
            ImportResult with import status.
        """
        content, read_error = self._read_source(source_path)
        if read_error:
            result = ImportResult(success=False)
            result.errors.append(read_error)
            return result

        result = ImportResult(success=True)

        if options.auto_detect_characters:
            result.characters_detected = []

        if options.auto_detect_locations:
            result.locations_detected = self._detect_locations(content)

        story_name = os.path.splitext(os.path.basename(source_path))[0]
        dest_path = self._resolve_destination(story_name, options)
        if dest_path is None:
            result.success = False
            result.errors.append(
                "No target_series specified. Provide a series name via options."
            )
            return result

        try:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, "w", encoding="utf-8") as fh:
                fh.write(content)
            result.story_path = dest_path
        except OSError as exc:
            result.success = False
            result.errors.append(f"Failed to write imported story: {exc}")

        return result

    def import_from_text(
        self,
        source_path: str,
        options: ImportOptions,
    ) -> ImportResult:
        """Import from a plain text file.

        Wraps the text in a minimal markdown structure with a Story Content header.

        Args:
            source_path: Path to text file.
            options: Import options.

        Returns:
            ImportResult with import status.
        """
        content, read_error = self._read_source(source_path)
        if read_error:
            result = ImportResult(success=False)
            result.errors.append(read_error)
            return result

        story_name = os.path.splitext(os.path.basename(source_path))[0]
        markdown_content = f"## Story Content\n\n{content}"
        options.import_format = ImportFormat.MARKDOWN

        result = ImportResult(success=True)
        if options.auto_detect_locations:
            result.locations_detected = self._detect_locations(content)

        dest_path = self._resolve_destination(story_name, options)
        if dest_path is None:
            result.success = False
            result.errors.append(
                "No target_series specified. Provide a series name via options."
            )
            return result

        try:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, "w", encoding="utf-8") as fh:
                fh.write(markdown_content)
            result.story_path = dest_path
        except OSError as exc:
            result.success = False
            result.errors.append(f"Failed to write imported story: {exc}")

        return result

    def import_from_json(
        self,
        source_path: str,
        options: ImportOptions,
    ) -> ImportResult:
        """Import from a JSON file containing a 'content' key.

        Args:
            source_path: Path to JSON file.
            options: Import options.

        Returns:
            ImportResult with import status.
        """
        import json  # pylint: disable=import-outside-toplevel

        result = ImportResult(success=False)
        try:
            with open(source_path, encoding="utf-8") as fh:
                data = json.load(fh)
        except (OSError, json.JSONDecodeError) as exc:
            result.errors.append(f"Failed to read JSON source: {exc}")
            return result

        content = data.get("content", "")
        if not content:
            result.errors.append("JSON file has no 'content' field.")
            return result

        story_name = data.get("title", os.path.splitext(os.path.basename(source_path))[0])
        markdown_content = f"## {story_name}\n\n{content}"

        if options.auto_detect_locations:
            result.locations_detected = self._detect_locations(content)

        dest_path = self._resolve_destination(story_name, options)
        if dest_path is None:
            result.errors.append(
                "No target_series specified. Provide a series name via options."
            )
            return result

        try:
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, "w", encoding="utf-8") as fh:
                fh.write(markdown_content)
            result.story_path = dest_path
            result.success = True
        except OSError as exc:
            result.errors.append(f"Failed to write imported story: {exc}")

        return result

    def batch_import(
        self,
        source_directory: str,
        target_series: str,
        options: Optional[ImportOptions] = None,
    ) -> list[ImportResult]:
        """Import multiple stories from a directory.

        Args:
            source_directory: Directory containing source files.
            target_series: Series to add stories to.
            options: Import options.

        Returns:
            List of ImportResult objects, one per source file.
        """
        resolved_options = options or ImportOptions()
        resolved_options.target_series = target_series
        results: list[ImportResult] = []

        if not os.path.isdir(source_directory):
            result = ImportResult(success=False)
            result.errors.append(f"Source directory not found: {source_directory}")
            return [result]

        supported_extensions = {f".{fmt.value}" for fmt in ImportFormat}
        for filename in sorted(os.listdir(source_directory)):
            ext = os.path.splitext(filename)[1].lower()
            if ext not in supported_extensions:
                continue
            filepath = os.path.join(source_directory, filename)
            results.append(self.import_story(filepath, target_series, resolved_options))

        return results

    def detect_characters_in_content(
        self,
        content: str,
        known_characters: list[str],
    ) -> list[str]:
        """Detect known character names mentioned in content.

        Args:
            content: Story content to analyse.
            known_characters: List of known character names to search for.

        Returns:
            List of character names found in the content.
        """
        found: list[str] = []
        for name in known_characters:
            pattern = re.compile(r"\b" + re.escape(name) + r"\b", re.IGNORECASE)
            if pattern.search(content):
                found.append(name)
        return found

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_destination(
        self,
        story_name: str,
        options: ImportOptions,
    ) -> Optional[str]:
        """Resolve the destination file path for an import.

        Args:
            story_name: Base name for the story file.
            options: Import options containing target_series.

        Returns:
            Absolute path to destination file, or None if no series is set.
        """
        if not options.target_series:
            return None
        campaigns_dir = get_campaigns_dir(self.workspace_path)
        series_dir = os.path.join(campaigns_dir, options.target_series)
        _, filepath = next_filename_for_dir(series_dir, story_name)
        return filepath

    def _detect_locations(self, content: str) -> list[str]:
        """Detect likely location names in content using keyword matching.

        Args:
            content: Story content.

        Returns:
            Deduplicated list of detected location phrases.
        """
        found: list[str] = []
        seen: set[str] = set()
        for match in self._LOCATION_KEYWORDS.finditer(content):
            word = match.group(0).title()
            if word not in seen:
                seen.add(word)
                found.append(word)
        return found

    def _read_source(self, filepath: str) -> tuple[str, Optional[str]]:
        """Read source file content.

        Args:
            filepath: Path to source file.

        Returns:
            Tuple of (content, error_message). error_message is None on success.
        """
        try:
            with open(filepath, encoding="utf-8") as fh:
                return fh.read(), None
        except OSError as exc:
            return "", f"Failed to read source file: {exc}"
