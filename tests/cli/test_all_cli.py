"""CLI Subsystem Test Runner

Runs all tests for the CLI subsystem and prints a concise summary. Placed
alongside other per-subsystem aggregators so the top-level test runner can pick it up.
"""

import sys
from typing import Dict, Tuple
from tests.test_runner_common import print_subsystem_summary, run_test_file


def run_all_cli_tests() -> int:
    """Run all tests in the cli subsystem and print a summary.

    Returns:
        Exit code 0 on success, 1 on failure (consistent with other subsystem runners).
    """
    print("=" * 70)
    print("CLI SUBSYSTEM - FULL TEST SUITE")
    print("=" * 70)
    print()

    tests: Tuple[Tuple[str, str], ...] = (
        ("test_dnd_consultant", "DND Consultant CLI Tests"),
        ("test_setup", "CLI Setup Tests"),
        ("test_cli_character_manager", "CLI Character Manager Tests"),
        ("test_cli_story_manager", "CLI Story Manager Tests"),
        ("test_cli_consultations", "CLI Consultations Tests"),
        ("test_cli_story_analysis", "CLI Story Analysis Tests"),
        ("test_cli_story_series_party", "CLI Story Series Party Manager Tests"),
        ("test_cli_session_manager", "CLI Session Manager Tests"),
        ("test_cli_character_development_manager", "CLI Character Development Manager Tests"),
    )

    results: Dict[str, bool] = {}
    for test_file, test_name in tests:
        results[test_name] = run_test_file(test_file, "cli", test_name)

    # Summary (delegate to shared helper)
    return print_subsystem_summary(results, "CLI SUBSYSTEM - TEST SUMMARY")


if __name__ == "__main__":
    sys.exit(run_all_cli_tests())
