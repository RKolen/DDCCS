"""Common helpers for per-subsystem test aggregator scripts.

This module centralizes the summary-printing logic used by many
``test_all_<subsystem>.py`` files to avoid duplicated code that triggers
Pylint R0801 (duplicate-code).
"""
from typing import Dict


def print_subsystem_summary(results: Dict[str, bool], title: str) -> int:
    """Print a compact summary for a subsystem test run.

    Args:
        results: Mapping of test name -> passed (bool)
        title: Human-readable title for the summary header

    Returns:
        0 if all passed, 1 otherwise
    """
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

    total_tests = len(results)
    passed_tests = sum(1 for passed in results.values() if passed)
    failed_tests = total_tests - passed_tests

    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test_name}")

    print("\n" + "-" * 70)
    print(f"Total: {total_tests} test files")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print("-" * 70)

    if failed_tests == 0:
        print("\n[SUCCESS] All subsystem tests passed!")
        return 0

    print(f"\n[FAILURE] {failed_tests} test file(s) failed")
    return 1
