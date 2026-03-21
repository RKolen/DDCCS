"""
D&D 5e Character Profile Verifier.

Orchestrates all verification rules against a character profile and produces
a VerificationReport.  Can be invoked directly from the command line:

    python -m src.validation.profile_verifier aragorn
    python -m src.validation.profile_verifier --all
    python -m src.validation.profile_verifier aragorn --format json
    python -m src.validation.profile_verifier aragorn --auto-fix
    python -m src.validation.profile_verifier aragorn --severity warning
"""

import argparse
import copy
import json
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.file_io import load_json_file, save_json_file
from src.utils.path_utils import get_characters_dir
from src.utils.string_utils import get_timestamp
from src.utils.terminal_display import (
    print_info,
    print_success,
    print_warning,
)
from src.utils.errors import (
    display_error,
    DnDError,
    FileSystemError,
)
from src.utils.error_templates import get_error_template
from src.validation.verification_rules import (
    VerificationIssue,
    VerificationRule,
    build_rules,
)

# ---- Severity ordering used for filtering and display ----
_SEVERITY_ORDER = ("error", "warning", "suggestion")


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

@dataclass
class VerificationReport:
    """Result from running all verification rules against a character profile."""

    character_name: str
    issues: List[VerificationIssue] = field(default_factory=list)
    total_checks: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Convenience properties
    @property
    def errors(self) -> List[VerificationIssue]:
        """Return only error-severity issues."""
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[VerificationIssue]:
        """Return only warning-severity issues."""
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def suggestions(self) -> List[VerificationIssue]:
        """Return only suggestion-severity issues."""
        return [i for i in self.issues if i.severity == "suggestion"]

    @property
    def passed(self) -> int:
        """Number of checks that passed."""
        return self.total_checks - len(self.issues)

    def filter_by_severity(self, severity: str) -> "VerificationReport":
        """Return a copy of this report filtered to the given severity and above.

        Args:
            severity: Minimum severity to include ("error", "warning", "suggestion").

        Returns:
            Filtered VerificationReport.
        """
        if severity not in _SEVERITY_ORDER:
            return self
        cutoff = _SEVERITY_ORDER.index(severity)
        filtered = VerificationReport(
            character_name=self.character_name,
            total_checks=self.total_checks,
            timestamp=self.timestamp,
        )
        filtered.issues = [
            i for i in self.issues if _SEVERITY_ORDER.index(i.severity) <= cutoff
        ]
        return filtered

    def to_dict(self) -> Dict[str, Any]:
        """Serialise report to a plain dictionary.

        Returns:
            Dictionary suitable for JSON serialisation.
        """
        return {
            "character": self.character_name,
            "timestamp": self.timestamp,
            "summary": {
                "errors": len(self.errors),
                "warnings": len(self.warnings),
                "suggestions": len(self.suggestions),
                "total_checks": self.total_checks,
                "passed": self.passed,
            },
            "issues": [
                {
                    "rule_id": i.rule_id,
                    "category": i.category,
                    "severity": i.severity,
                    "field": i.field,
                    "message": i.message,
                    "suggestion": i.suggestion,
                    "auto_fixable": i.auto_fixable,
                }
                for i in self.issues
            ],
        }

    def to_terminal(self) -> str:
        """Format the report as a human-readable terminal string.

        Returns:
            Formatted multi-line string.
        """
        width = 80
        lines: List[str] = []
        lines.append("=" * width)
        lines.append(f"Profile Verification: {self.character_name}")
        lines.append("=" * width)

        # Group issues by category
        categories: Dict[str, List[VerificationIssue]] = {}
        for issue in self.issues:
            categories.setdefault(issue.category, []).append(issue)

        if not self.issues:
            lines.append("")
            lines.append("  No issues found - profile looks good!")
            lines.append("")
        else:
            for category in ("completeness", "consistency", "rules", "best_practices"):
                cat_issues = categories.get(category, [])
                if not cat_issues:
                    continue
                label = category.upper().replace("_", " ")
                lines.append(f"\n{label}")
                for issue in cat_issues:
                    tag = {
                        "error": "[ERROR]",
                        "warning": "[WARNING]",
                        "suggestion": "[SUGGESTION]",
                    }.get(issue.severity, "[?]")
                    lines.append(f"  {tag} {issue.message}")
                    if issue.suggestion:
                        lines.append(f"    Suggestion: {issue.suggestion}")

        lines.append("")
        lines.append("=" * width)
        summary_parts = [
            f"{len(self.errors)} Error(s)",
            f"{len(self.warnings)} Warning(s)",
            f"{len(self.suggestions)} Suggestion(s)",
            f"{self.passed}/{self.total_checks} checks passed",
        ]
        lines.append("Summary: " + ", ".join(summary_parts))
        lines.append("=" * width)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Verifier
# ---------------------------------------------------------------------------

class ProfileVerifier:
    """Runs all verification rules against a character profile dict."""

    def __init__(self) -> None:
        """Initialise the verifier with the full rule set."""
        self._rules: List[VerificationRule] = build_rules()

    def verify(self, data: Dict[str, Any]) -> VerificationReport:
        """Verify a character data dictionary.

        Args:
            data: The character profile as a dictionary.

        Returns:
            A VerificationReport containing all issues found.
        """
        name = data.get("name", "Unknown")
        report = VerificationReport(character_name=name, total_checks=len(self._rules))
        for rule in self._rules:
            issue = rule.check(data)
            if issue is not None:
                report.issues.append(issue)
        return report

    def verify_file(self, filepath: str) -> Optional[VerificationReport]:
        """Load a character JSON file and verify it.

        Args:
            filepath: Absolute path to the character JSON file.

        Returns:
            A VerificationReport, or None if the file could not be loaded.
        """
        data = load_json_file(filepath)
        if data is None:
            return None
        return self.verify(data)

    def auto_fix(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply all auto-fixable rules to a copy of the data.

        Args:
            data: Original character data dictionary.

        Returns:
            A new dictionary with auto-fixable issues corrected.
        """
        fixed_data = copy.deepcopy(data)
        for rule in self._rules:
            if rule.auto_fixable and rule.auto_fix_func is not None:
                rule.auto_fix_func(fixed_data)
        return fixed_data


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_character_file(name: str) -> Optional[str]:
    """Locate a character JSON file by name (case-insensitive).

    Args:
        name: Character name or file stem.

    Returns:
        Absolute path string if found, otherwise None.
    """
    chars_dir = Path(get_characters_dir())
    lower_name = name.lower()
    for path in chars_dir.glob("*.json"):
        if path.stem.lower() == lower_name:
            return str(path)
    return None


def _list_all_character_files() -> List[str]:
    """Return paths to all JSON files in the characters directory.

    Returns:
        Sorted list of absolute path strings.
    """
    chars_dir = Path(get_characters_dir())
    return sorted(str(p) for p in chars_dir.glob("*.json"))


def _apply_auto_fix_interactive(
    filepath: str, verifier: ProfileVerifier
) -> bool:
    """Interactively apply auto-fixes to a character file.

    Creates a timestamped backup before writing changes.

    Args:
        filepath: Path to the character JSON file.
        verifier: ProfileVerifier instance.

    Returns:
        True if fixes were applied and saved, False otherwise.
    """
    data = load_json_file(filepath)
    if data is None:
        msg, guidance = get_error_template("profile_verification_load_failed", name=filepath)
        display_error(FileSystemError(message=msg, user_guidance=guidance))
        return False

    report = verifier.verify(data)
    fixable = [i for i in report.issues if i.auto_fixable]
    if not fixable:
        print_info("No auto-fixable issues found.")
        return False

    print_warning(f"Auto-fixable issues ({len(fixable)}):")
    for issue in fixable:
        print(f"  [{issue.rule_id}] {issue.message}")

    confirm = input("\nApply auto-fixes? (y/N): ").strip().lower()
    if confirm != "y":
        print_info("Auto-fix cancelled.")
        return False

    # Create backup
    ts = get_timestamp()
    backup_path = filepath + f".backup_{ts}"
    shutil.copy2(filepath, backup_path)
    print_info(f"Backup created: {backup_path}")

    fixed_data = verifier.auto_fix(data)
    save_json_file(filepath, fixed_data)
    print_success(f"Auto-fix complete. Changes saved to {filepath}")
    return True


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Verify D&D character profile quality and D&D 5e rules compliance.",
    )
    parser.add_argument(
        "character",
        nargs="?",
        help="Character name to verify (omit to use --all)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Verify all characters",
    )
    parser.add_argument(
        "--format",
        choices=["terminal", "json"],
        default="terminal",
        help="Output format (default: terminal)",
    )
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="Interactively apply auto-fixable corrections",
    )
    parser.add_argument(
        "--severity",
        choices=_SEVERITY_ORDER,
        default=None,
        help="Minimum severity to show (error < warning < suggestion)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show all checks, including passed ones (terminal format only)",
    )
    return parser


def _output_report(
    report: VerificationReport,
    output_format: str,
    severity_filter: Optional[str],
    verbose: bool,
) -> None:
    """Print a report to stdout.

    Args:
        report: The VerificationReport to display.
        output_format: "terminal" or "json".
        severity_filter: Optional minimum severity string.
        verbose: Whether to include extra context in terminal output.
    """
    display_report = report
    if severity_filter:
        display_report = report.filter_by_severity(severity_filter)

    if output_format == "json":
        print(json.dumps(display_report.to_dict(), indent=2, ensure_ascii=False))
        return

    # Terminal output
    print(display_report.to_terminal())

    if verbose and not display_report.issues:
        print_success(f"All {report.total_checks} checks passed.")


def main() -> None:
    """CLI entry point for profile verification."""
    parser = _build_arg_parser()
    args = parser.parse_args()

    if not args.character and not args.all:
        parser.print_help()
        sys.exit(1)

    verifier = ProfileVerifier()

    if args.all:
        filepaths = _list_all_character_files()
        if not filepaths:
            msg, guidance = get_error_template("data_not_found", data_type="character", name="any")
            display_error(DnDError(message="No character files found", user_guidance=guidance))
            sys.exit(1)
        had_errors = False
        for filepath in filepaths:
            report = verifier.verify_file(filepath)
            if report is None:
                msg, guidance = get_error_template(
                    "profile_verification_load_failed", name=filepath
                )
                display_error(FileSystemError(message=msg, user_guidance=guidance))
                continue
            _output_report(report, args.format, args.severity, args.verbose)
            if report.errors:
                had_errors = True
        if had_errors:
            sys.exit(2)
        return

    # Single character
    char_filepath = _find_character_file(args.character)
    if char_filepath is None:
        msg, guidance = get_error_template(
            "profile_verification_not_found", name=args.character
        )
        display_error(DnDError(message=msg, user_guidance=guidance))
        sys.exit(1)

    if args.auto_fix:
        _apply_auto_fix_interactive(char_filepath, verifier)
        return

    report = verifier.verify_file(char_filepath)
    if report is None:
        msg, guidance = get_error_template(
            "profile_verification_load_failed", name=args.character
        )
        display_error(FileSystemError(message=msg, user_guidance=guidance))
        sys.exit(1)

    _output_report(report, args.format, args.severity, args.verbose)

    if report.errors:
        sys.exit(2)


if __name__ == "__main__":
    main()
