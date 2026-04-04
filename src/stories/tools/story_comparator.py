"""Story comparison and diff utilities.

Provides tools for comparing story versions and tracking changes
using Python's built-in difflib module.
"""

import difflib
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from src.utils.story_file_helpers import (
    get_story_file_paths_in_series,
    read_story_lines,
)

_SECTION_HEADER = re.compile(r"^#{1,3}\s+(.+)$")
_SIGNIFICANCE_LONG_LINE = 80


class ChangeType(Enum):
    """Types of changes between story versions."""

    ADDITION = "addition"
    DELETION = "deletion"
    MODIFICATION = "modification"


@dataclass
class StoryChange:
    """Represents a single change between story versions."""

    change_type: ChangeType
    line_number: int
    old_content: str
    new_content: str
    section: str
    significance: int


@dataclass
class StoryDiff:
    """Complete diff result between two story versions."""

    source_file: str
    target_file: str
    changes: list[StoryChange] = field(default_factory=list)
    similarity_score: float = 0.0
    summary: str = ""

    @property
    def has_changes(self) -> bool:
        """Return True if there are any changes."""
        return bool(self.changes)

    @property
    def significant_changes(self) -> list[StoryChange]:
        """Return changes with significance >= 5."""
        return [c for c in self.changes if c.significance >= 5]


class StoryComparator:
    """Compare story files and summarise changes."""

    def __init__(self, workspace_path: str) -> None:
        """Initialize comparator.

        Args:
            workspace_path: Root workspace path for story files.
        """
        self.workspace_path = workspace_path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compare_stories(
        self,
        source_path: str,
        target_path: str,
    ) -> StoryDiff:
        """Compare two story files line by line.

        Args:
            source_path: Path to source story file.
            target_path: Path to target story file.

        Returns:
            StoryDiff with all detected changes.
        """
        source_lines = read_story_lines(source_path) or []
        target_lines = read_story_lines(target_path) or []

        matcher = difflib.SequenceMatcher(None, source_lines, target_lines)
        similarity = round(matcher.ratio(), 4)
        changes = self._extract_changes(source_lines, target_lines)
        summary = self._build_summary(
            os.path.basename(source_path),
            os.path.basename(target_path),
            similarity,
            changes,
        )
        return StoryDiff(
            source_file=source_path,
            target_file=target_path,
            changes=changes,
            similarity_score=similarity,
            summary=summary,
        )

    def compare_series(
        self,
        series_name: str,
        from_index: int,
        to_index: int,
    ) -> list[StoryDiff]:
        """Compare stories across a series by index.

        Args:
            series_name: Name of the story series (campaign directory name).
            from_index: Starting story index (1-based).
            to_index: Ending story index (1-based).

        Returns:
            List of diffs between consecutive stories in the range.
        """
        story_files = get_story_file_paths_in_series(self.workspace_path, series_name)
        start = max(0, from_index - 1)
        end = min(len(story_files), to_index)
        window = story_files[start:end]
        return [
            self.compare_stories(window[i], window[i + 1])
            for i in range(len(window) - 1)
        ]

    def find_narrative_changes(self, diff: StoryDiff) -> list[StoryChange]:
        """Extract only narrative content changes, filtering metadata.

        Filters out changes to markdown headers, blank lines, and
        short formatting-only lines.

        Args:
            diff: StoryDiff to filter.

        Returns:
            List of narrative-focused changes.
        """
        return [
            c for c in diff.changes
            if self._is_narrative(c.old_content) or self._is_narrative(c.new_content)
        ]

    def generate_change_report(
        self,
        diff: StoryDiff,
        output_format: str = "markdown",
    ) -> str:
        """Generate a formatted change report.

        Args:
            diff: StoryDiff to report.
            output_format: Output format - 'markdown' or 'text'.

        Returns:
            Formatted change report string.
        """
        source_name = os.path.basename(diff.source_file)
        target_name = os.path.basename(diff.target_file)
        if output_format == "markdown":
            return self._markdown_report(source_name, target_name, diff)
        return self._text_report(source_name, target_name, diff)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_changes(
        self,
        source_lines: list[str],
        target_lines: list[str],
    ) -> list[StoryChange]:
        """Build StoryChange objects from a sequence-matcher diff.

        Args:
            source_lines: Lines of the source file.
            target_lines: Lines of the target file.

        Returns:
            List of StoryChange objects.
        """
        changes: list[StoryChange] = []
        opcodes = difflib.SequenceMatcher(
            None, source_lines, target_lines
        ).get_opcodes()
        current_section = ""

        for tag, src_start, src_end, tgt_start, tgt_end in opcodes:
            tgt_block = target_lines[tgt_start:tgt_end]
            current_section = self._update_section(tgt_block, current_section)
            if tag == "equal":
                continue
            src_block = source_lines[src_start:src_end]
            changes.extend(
                self._block_to_changes(
                    tag, (src_block, tgt_block), tgt_start, current_section
                )
            )
        return changes

    def _update_section(
        self,
        block: list[str],
        current_section: str,
    ) -> str:
        """Update the current section name from a block of lines.

        Args:
            block: Lines to scan for section headers.
            current_section: The previously active section name.

        Returns:
            Updated section name (unchanged if no header found).
        """
        for line in block:
            match = _SECTION_HEADER.match(line.rstrip())
            if match:
                return match.group(1)
        return current_section

    def _block_to_changes(
        self,
        tag: str,
        blocks: tuple[list[str], list[str]],
        tgt_start: int,
        section: str,
    ) -> list[StoryChange]:
        """Convert a difflib opcode block to StoryChange objects.

        Args:
            tag: Difflib opcode tag ('insert', 'delete', 'replace').
            blocks: Tuple of (src_block, tgt_block) line lists.
            tgt_start: Starting line number in the target file (0-based).
            section: Current section heading name.

        Returns:
            List of StoryChange objects for this block.
        """
        src_block, tgt_block = blocks
        change_type = self._opcode_to_change_type(tag)
        max_pairs = max(len(src_block), len(tgt_block))
        result: list[StoryChange] = []
        for i in range(max_pairs):
            old = src_block[i].rstrip() if i < len(src_block) else ""
            new = tgt_block[i].rstrip() if i < len(tgt_block) else ""
            result.append(
                StoryChange(
                    change_type=change_type,
                    line_number=tgt_start + i + 1,
                    old_content=old,
                    new_content=new,
                    section=section,
                    significance=self._rate_significance(old, new),
                )
            )
        return result

    def _opcode_to_change_type(self, tag: str) -> ChangeType:
        """Map a difflib opcode tag to a ChangeType.

        Args:
            tag: Difflib opcode tag.

        Returns:
            Corresponding ChangeType enum value.
        """
        if tag == "insert":
            return ChangeType.ADDITION
        if tag == "delete":
            return ChangeType.DELETION
        return ChangeType.MODIFICATION

    def _rate_significance(self, old: str, new: str) -> int:
        """Rate the significance of a change on a 1-10 scale.

        Args:
            old: Old line content.
            new: New line content.

        Returns:
            Integer significance score between 1 and 10.
        """
        combined_length = len(old) + len(new)
        if combined_length == 0:
            return 1
        ratio = difflib.SequenceMatcher(None, old, new).ratio()
        difference_score = int((1 - ratio) * 5)
        length_score = min(5, combined_length // _SIGNIFICANCE_LONG_LINE)
        return max(1, min(10, difference_score + length_score))

    def _is_narrative(self, content: str) -> bool:
        """Return True if content is likely narrative prose (not metadata).

        Args:
            content: Line content to check.

        Returns:
            True if line appears to be narrative text.
        """
        stripped = content.strip()
        if not stripped or _SECTION_HEADER.match(stripped) or stripped.startswith("---"):
            return False
        return len(stripped) > 10

    def _build_summary(
        self,
        source_name: str,
        target_name: str,
        similarity: float,
        changes: list[StoryChange],
    ) -> str:
        """Build a one-line human-readable summary.

        Args:
            source_name: Source file name.
            target_name: Target file name.
            similarity: Similarity ratio (0-1).
            changes: All detected changes.

        Returns:
            Summary string.
        """
        additions = sum(1 for c in changes if c.change_type == ChangeType.ADDITION)
        deletions = sum(1 for c in changes if c.change_type == ChangeType.DELETION)
        modifications = sum(
            1 for c in changes if c.change_type == ChangeType.MODIFICATION
        )
        return (
            f"{source_name} vs {target_name}: "
            f"{similarity:.1%} similar, "
            f"+{additions} -{deletions} ~{modifications} changes"
        )

    def _markdown_report(
        self,
        source_name: str,
        target_name: str,
        diff: StoryDiff,
    ) -> str:
        """Build a markdown-formatted change report.

        Args:
            source_name: Source file name.
            target_name: Target file name.
            diff: StoryDiff to report.

        Returns:
            Markdown report string.
        """
        lines: list[str] = [
            f"## Story Diff: {source_name} -> {target_name}",
            "",
            f"**Similarity:** {diff.similarity_score:.1%}",
            f"**Total changes:** {len(diff.changes)}",
            f"**Significant changes:** {len(diff.significant_changes)}",
        ]
        if diff.changes:
            lines.append("")
            lines.append("### Changes")
            for change in diff.changes:
                label = change.change_type.value.capitalize()
                note = f" (in *{change.section}*)" if change.section else ""
                lines.append(
                    f"- **{label}** line {change.line_number}{note} "
                    f"[significance: {change.significance}]"
                )
                if change.old_content.strip():
                    lines.append(f"  - Before: `{change.old_content.strip()[:80]}`")
                if change.new_content.strip():
                    lines.append(f"  - After:  `{change.new_content.strip()[:80]}`")
        else:
            lines.append("")
            lines.append("*No changes detected.*")
        return "\n".join(lines)

    def _text_report(
        self,
        source_name: str,
        target_name: str,
        diff: StoryDiff,
    ) -> str:
        """Build a plain-text change report.

        Args:
            source_name: Source file name.
            target_name: Target file name.
            diff: StoryDiff to report.

        Returns:
            Plain-text report string.
        """
        lines: list[str] = [
            f"Story Diff: {source_name} -> {target_name}",
            f"  Similarity: {diff.similarity_score:.1%}",
            f"  Total changes: {len(diff.changes)}",
        ]
        for change in diff.changes:
            lines.append(
                f"  [{change.change_type.value}] line {change.line_number}: "
                f"{change.old_content.strip()[:60]} -> {change.new_content.strip()[:60]}"
            )
        return "\n".join(lines)


def compare_story_texts(
    text_a: str,
    text_b: str,
) -> tuple[float, list[tuple[str, Optional[str], Optional[str]]]]:
    """Compare two story text strings directly.

    Convenience function for quick comparisons without file I/O.

    Args:
        text_a: First story text.
        text_b: Second story text.

    Returns:
        Tuple of (similarity_score, diff_lines) where each diff entry is
        (tag, old_text, new_text).
    """
    lines_a = text_a.splitlines(keepends=True)
    lines_b = text_b.splitlines(keepends=True)
    matcher = difflib.SequenceMatcher(None, lines_a, lines_b)
    similarity = round(matcher.ratio(), 4)
    diffs: list[tuple[str, Optional[str], Optional[str]]] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        old = "".join(lines_a[i1:i2]) if i1 < i2 else None
        new = "".join(lines_b[j1:j2]) if j1 < j2 else None
        diffs.append((tag, old, new))
    return similarity, diffs
