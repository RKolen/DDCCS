"""Runs all calendar tests as a single suite."""

import sys

from tests.test_runner_common import print_subsystem_summary, run_test_file


def run_all_calendar_tests() -> int:
    """Run all calendar subsystem tests and summarize results.

    Returns:
        0 if all tests passed, 1 otherwise.
    """
    print("=" * 70)
    print("CALENDAR SYSTEM - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print()

    tests = [
        ("test_calendar_engine", "Calendar Engine Tests"),
        ("test_date_tracker", "Date Tracker Tests"),
    ]

    results = {}
    for test_file, test_name in tests:
        results[test_name] = run_test_file(test_file, "calendar", test_name)

    return print_subsystem_summary(results, "CALENDAR SUBSYSTEM - TEST SUMMARY")


if __name__ == "__main__":
    sys.exit(run_all_calendar_tests())
