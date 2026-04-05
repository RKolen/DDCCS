"""Spells Subsystem Test Runner

Runs all tests for the spells subsystem and prints a concise summary.
"""

import sys
from tests.test_runner_common import print_subsystem_summary, run_test_file


def run_all_spells_tests() -> int:
    """Run all tests in the spells subsystem and print a summary.

    Returns:
        0 if all tests passed, 1 otherwise.
    """
    print("=" * 70)
    print("SPELLS SUBSYSTEM - FULL TEST SUITE")
    print("=" * 70)
    print()

    tests = [
        ("test_spell_registry", "Spell Registry Tests"),
        ("test_spell_import_export", "Spell Import/Export Tests"),
    ]

    results = {}
    for test_file, test_name in tests:
        results[test_name] = run_test_file(test_file, "spells", test_name)

    return print_subsystem_summary(results, "SPELLS SUBSYSTEM - TEST SUMMARY")


if __name__ == "__main__":
    sys.exit(run_all_spells_tests())
