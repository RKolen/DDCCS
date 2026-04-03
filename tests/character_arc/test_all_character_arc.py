"""Character Arc Analysis Subsystem Test Runner."""

import sys
from tests.test_runner_common import print_subsystem_summary, run_test_file


def run_all_character_arc_tests() -> int:
    """Run all character arc analysis tests."""
    print("=" * 70)
    print("CHARACTER ARC ANALYSIS SUBSYSTEM - FULL TEST SUITE")
    print("=" * 70)
    print()

    tests = [
        ("test_arc_criteria", "Arc Criteria and Metrics Tests"),
        ("test_arc_analyzer", "Arc Analyzer Tests"),
        ("test_arc_storage", "Arc Storage Tests"),
    ]

    results = {}
    for test_file, test_name in tests:
        results[test_name] = run_test_file(test_file, "character_arc", test_name)

    return print_subsystem_summary(
        results, "CHARACTER ARC ANALYSIS SUBSYSTEM - TEST SUMMARY"
    )


if __name__ == "__main__":
    sys.exit(run_all_character_arc_tests())
