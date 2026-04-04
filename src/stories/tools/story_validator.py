"""Story validation utilities.

Provides validation and quality checks for story markdown files,
including structural checks, link verification, and style hints.
"""

import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from src.utils.path_utils import get_campaigns_dir
from src.utils.story_file_helpers import STORY_PATTERN

_MARKDOWN_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_HEADER_RE = re.compile(r"^(#{1,6})\s+(.+)$")
_REPEATED_WORD = re.compile(r"\b(\w{4,})\s+\1\b", re.IGNORECASE)
_PASSIVE_VOICE = re.compile(
    r"\b(was|were|been|being|is|are)\s+([\w]+ed)\b", re.IGNORECASE
)
_MIN_STORY_WORDS = 20


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    STYLE = "style"


@dataclass
class ValidationIssue:
    """A single validation issue."""

    rule_name: str
    severity: ValidationSeverity
    message: str
    line_number: Optional[int] = None
    suggestion: str = ""
    context: str = ""


@dataclass
class ValidationResult:
    """Result of story validation."""

    story_path: str
    is_valid: bool
    issues: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)
    style_suggestions: list[ValidationIssue] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        """Return count of error-level issues."""
        return len(
            [i for i in self.issues if i.severity == ValidationSeverity.ERROR]
        )

    @property
    def warning_count(self) -> int:
        """Return count of warning-level issues."""
        return len(
            [i for i in self.issues if i.severity == ValidationSeverity.WARNING]
        )


class StoryValidator:
    """Validate story files for quality and consistency."""

    def __init__(self, workspace_path: str) -> None:
        """Initialize validator.

        Args:
            workspace_path: Root workspace path.
        """
        self.workspace_path = workspace_path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate_story(
        self,
        story_path: str,
        strict: bool = False,
    ) -> ValidationResult:
        """Validate a story file.

        Args:
            story_path: Path to story file.
            strict: Enable strict validation (includes style checks).

        Returns:
            ValidationResult with all issues found.
        """
        content = self._read_file(story_path)
        all_issues = self.check_structure(content)
        all_issues.extend(self.check_links(content, story_path))
        if strict:
            all_issues.extend(self.check_style(content))

        errors = [i for i in all_issues if i.severity == ValidationSeverity.ERROR]
        warnings = [i for i in all_issues if i.severity == ValidationSeverity.WARNING]
        style = [
            i for i in all_issues
            if i.severity in (ValidationSeverity.STYLE, ValidationSeverity.INFO)
        ]

        return ValidationResult(
            story_path=story_path,
            is_valid=not errors,
            issues=all_issues,
            warnings=warnings,
            style_suggestions=style,
        )

    def validate_series(
        self,
        series_name: str,
        strict: bool = False,
    ) -> dict[str, ValidationResult]:
        """Validate all stories in a series.

        Args:
            series_name: Name of the series (campaign directory name).
            strict: Enable strict validation mode.

        Returns:
            Dictionary mapping story paths to ValidationResults.
        """
        campaigns_dir = get_campaigns_dir(self.workspace_path)
        series_dir = os.path.join(campaigns_dir, series_name)
        results: dict[str, ValidationResult] = {}

        if not os.path.isdir(series_dir):
            return results

        for filename in sorted(os.listdir(series_dir)):
            if not STORY_PATTERN.match(filename):
                continue
            filepath = os.path.join(series_dir, filename)
            results[filepath] = self.validate_story(filepath, strict)

        return results

    def check_structure(self, content: str) -> list[ValidationIssue]:
        """Check story structure for markdown formatting and completeness.

        Args:
            content: Story content to check.

        Returns:
            List of structural ValidationIssue objects.
        """
        issues: list[ValidationIssue] = []
        lines = content.splitlines()

        if not content.strip():
            issues.append(
                ValidationIssue(
                    rule_name="empty_file",
                    severity=ValidationSeverity.ERROR,
                    message="Story file is empty.",
                    suggestion="Add narrative content to the file.",
                )
            )
            return issues

        word_count = len(content.split())
        if word_count < _MIN_STORY_WORDS:
            issues.append(
                ValidationIssue(
                    rule_name="too_short",
                    severity=ValidationSeverity.WARNING,
                    message=f"Story is very short ({word_count} words).",
                    suggestion="Consider expanding the narrative.",
                )
            )

        header_count = 0
        for idx, line in enumerate(lines):
            match = _HEADER_RE.match(line)
            if match:
                header_count += 1
                level = len(match.group(1))
                text = match.group(2).strip()
                if not text:
                    issues.append(
                        ValidationIssue(
                            rule_name="empty_header",
                            severity=ValidationSeverity.WARNING,
                            message=f"Empty header at line {idx + 1}.",
                            line_number=idx + 1,
                        )
                    )
                if level == 1 and header_count > 1:
                    issues.append(
                        ValidationIssue(
                            rule_name="multiple_h1",
                            severity=ValidationSeverity.INFO,
                            message=f"Multiple H1 headers found (line {idx + 1}).",
                            line_number=idx + 1,
                            suggestion="Story files typically use a single H1.",
                        )
                    )

        if header_count == 0:
            issues.append(
                ValidationIssue(
                    rule_name="no_headers",
                    severity=ValidationSeverity.INFO,
                    message="No markdown headers found in story.",
                    suggestion="Add section headers to organise your narrative.",
                )
            )

        return issues

    def check_links(
        self,
        content: str,
        story_path: str,
    ) -> list[ValidationIssue]:
        """Check markdown links for validity.

        Only validates relative (non-URL) links that should resolve to
        local files.

        Args:
            content: Story content to check.
            story_path: Path to story file for relative link resolution.

        Returns:
            List of link-related ValidationIssue objects.
        """
        issues: list[ValidationIssue] = []
        story_dir = os.path.dirname(story_path)

        for idx, line in enumerate(content.splitlines(), start=1):
            for match in _MARKDOWN_LINK.finditer(line):
                link_text = match.group(1)
                link_target = match.group(2)

                # Skip external URLs
                if link_target.startswith(("http://", "https://", "mailto:")):
                    continue
                # Skip anchor-only links
                if link_target.startswith("#"):
                    continue

                resolved = os.path.normpath(os.path.join(story_dir, link_target))
                if not os.path.exists(resolved):
                    issues.append(
                        ValidationIssue(
                            rule_name="broken_link",
                            severity=ValidationSeverity.WARNING,
                            message=(
                                f"Broken link to '{link_target}' "
                                f"(text: '{link_text}') at line {idx}."
                            ),
                            line_number=idx,
                            suggestion=f"Check that '{link_target}' exists.",
                            context=line.strip(),
                        )
                    )
        return issues

    def check_character_consistency(
        self,
        content: str,
        character_profiles: dict[str, object],
    ) -> list[ValidationIssue]:
        """Check that character names appear consistently in the story.

        Flags lines where a character name appears with inconsistent
        capitalisation.

        Args:
            content: Story content to check.
            character_profiles: Dictionary mapping canonical name to profile.

        Returns:
            List of character consistency ValidationIssue objects.
        """
        issues: list[ValidationIssue] = []
        for canonical_name in character_profiles:
            # Find case-insensitive matches that differ from canonical form
            pattern = re.compile(r"\b" + re.escape(canonical_name) + r"\b", re.IGNORECASE)
            exact_pattern = re.compile(r"\b" + re.escape(canonical_name) + r"\b")
            for idx, line in enumerate(content.splitlines(), start=1):
                for match in pattern.finditer(line):
                    found = match.group(0)
                    if not exact_pattern.search(found):
                        issues.append(
                            ValidationIssue(
                                rule_name="name_capitalisation",
                                severity=ValidationSeverity.STYLE,
                                message=(
                                    f"'{found}' may be a capitalisation variant "
                                    f"of '{canonical_name}' at line {idx}."
                                ),
                                line_number=idx,
                                suggestion=f"Use '{canonical_name}' consistently.",
                                context=line.strip(),
                            )
                        )
        return issues

    def check_style(self, content: str) -> list[ValidationIssue]:
        """Check writing style for common issues.

        Looks for repeated adjacent words and heavy passive-voice usage.

        Args:
            content: Story content to check.

        Returns:
            List of style ValidationIssue objects.
        """
        issues: list[ValidationIssue] = []

        for idx, line in enumerate(content.splitlines(), start=1):
            for match in _REPEATED_WORD.finditer(line):
                issues.append(
                    ValidationIssue(
                        rule_name="repeated_word",
                        severity=ValidationSeverity.STYLE,
                        message=(
                            f"Repeated word '{match.group(1)}' "
                            f"at line {idx}."
                        ),
                        line_number=idx,
                        suggestion="Consider varying your word choice.",
                        context=line.strip(),
                    )
                )

        passive_count = len(_PASSIVE_VOICE.findall(content))
        total_sentences = max(1, content.count(".") + content.count("!") + content.count("?"))
        if passive_count / total_sentences > 0.3:
            issues.append(
                ValidationIssue(
                    rule_name="heavy_passive_voice",
                    severity=ValidationSeverity.STYLE,
                    message=(
                        f"High passive voice usage: {passive_count} instances "
                        f"in {total_sentences} sentences."
                    ),
                    suggestion="Consider rewriting some sentences in active voice.",
                )
            )

        return issues

    def generate_validation_report(
        self,
        result: ValidationResult,
        output_format: str = "markdown",
    ) -> str:
        """Generate a formatted validation report.

        Args:
            result: ValidationResult to report.
            output_format: Output format - 'markdown' or 'text'.

        Returns:
            Formatted validation report string.
        """
        file_name = os.path.basename(result.story_path)
        status = "VALID" if result.is_valid else "INVALID"
        lines: list[str] = []

        if output_format == "markdown":
            lines.append(f"## Validation Report: {file_name}")
            lines.append("")
            lines.append(f"**Status:** {status}")
            lines.append(f"**Errors:** {result.error_count}")
            lines.append(f"**Warnings:** {result.warning_count}")
            if result.issues:
                lines.append("")
                lines.append("### Issues")
                for issue in result.issues:
                    loc = f" (line {issue.line_number})" if issue.line_number else ""
                    lines.append(
                        f"- **[{issue.severity.value.upper()}]** "
                        f"{issue.message}{loc}"
                    )
                    if issue.suggestion:
                        lines.append(f"  *Suggestion: {issue.suggestion}*")
        else:
            lines.append(f"Validation: {file_name} [{status}]")
            lines.append(f"  Errors: {result.error_count}")
            lines.append(f"  Warnings: {result.warning_count}")
            for issue in result.issues:
                loc = f" line {issue.line_number}" if issue.line_number else ""
                lines.append(
                    f"  [{issue.severity.value}]{loc}: {issue.message}"
                )

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _read_file(self, filepath: str) -> str:
        """Read story file content safely.

        Args:
            filepath: Path to the file.

        Returns:
            File content as string, empty string on error.
        """
        try:
            with open(filepath, encoding="utf-8") as fh:
                return fh.read()
        except OSError:
            return ""
