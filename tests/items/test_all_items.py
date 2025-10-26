"""Items Subsystem Test Runner

Runs all tests for the items subsystem and prints a concise summary.
Placed alongside other per-subsystem aggregators (e.g., tests/combat/test_all_combat.py)
so the top-level test runner can pick it up.
"""

import sys
from tests.test_runner_common import print_subsystem_summary, run_test_file


def run_all_items_tests() -> int:
    """Run all tests in the items subsystem and print a summary."""
    print("=" * 70)
    print("ITEMS SUBSYSTEM - FULL TEST SUITE")
    print("=" * 70)
    print()

    tests = [
        ("test_item_registry", "Item Registry Tests"),
        ("test_item_registry_precedence", "Item Registry Precedence Tests"),
        ("test_item_registry_fallback_only", "Item Registry Fallback-Only Tests"),
        ("test_item_registry_api", "Item Registry API Tests"),
    ]

    results = {}
    for test_file, test_name in tests:
        results[test_name] = run_test_file(test_file, "items", test_name)

    # Summary (delegate to shared helper)
    return print_subsystem_summary(results, "ITEMS SUBSYSTEM - TEST SUMMARY")


if __name__ == "__main__":
    sys.exit(run_all_items_tests())
