"""Shared plumbing for the repository-wide gates run by `./check.sh`.

Each gate scans the tree for a list of findings, prints a report and exits
non-zero when the list is not empty. Written out per module that is an
identical block, which pylint reports as duplicate-code - correctly, since
changing how a gate reports would otherwise mean editing every one of them.
"""

from pathlib import Path
from typing import Callable, List, Sequence, TypeVar

Finding = TypeVar("Finding")


def repo_root() -> Path:
    """Return the repository root.

    Returns:
        The directory two levels above this module.
    """
    return Path(__file__).resolve().parents[2]


def run_check(
    scan: Callable[[Path], Sequence[Finding]],
    format_report: Callable[[List[Finding]], str],
) -> int:
    """Scan the repository, print the report, and report pass or fail.

    Args:
        scan: Takes the repository root and returns what it found.
        format_report: Renders those findings, including the all-clear.

    Returns:
        0 when nothing was found, 1 otherwise.
    """
    found = list(scan(repo_root()))
    print(format_report(found))
    return 1 if found else 0
