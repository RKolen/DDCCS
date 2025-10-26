"""
Combat Subsystem Test Runner

This module runs all tests for the combat subsystem and provides
a consolidated report of test results.
"""

import sys
from tests.test_runner_common import print_subsystem_summary, run_test_file


def run_all_combat_tests():
    """Run all combat subsystem tests."""
    print("=" * 70)
    print("COMBAT SUBSYSTEM - FULL TEST SUITE")
    print("=" * 70)
    print()

    tests = [
        ("test_combat_narrator", "Combat Narrator Tests"),
        ("test_narrator_ai", "Narrator AI Integration Tests"),
        ("test_narrator_descriptions", "Narrator Descriptions Tests"),
        ("test_narrator_consistency", "Narrator Consistency Tests"),
        ("test_combat_conversion", "Combat Conversion Tests"),
    ]

    results = {}
    for test_file, test_name in tests:
        results[test_name] = run_test_file(test_file, "combat", test_name)

    # Summary (delegate to shared helper)
    return print_subsystem_summary(results, "COMBAT SUBSYSTEM - TEST SUMMARY")


if __name__ == "__main__":
    sys.exit(run_all_combat_tests())
