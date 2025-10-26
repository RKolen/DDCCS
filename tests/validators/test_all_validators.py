"""Validators Subsystem Test Runner

Runs all validators tests (character, npc, items, party) using the
module-runner pattern (subprocess invocation of each test module) and
prints a concise summary via the shared test runner helper.

This file follows the same structure as other `test_all_*` subsystem
runners so linting and duplication checks are consistent.
"""

import sys
from typing import Dict, Tuple
from tests.test_runner_common import print_subsystem_summary, run_test_file


def run_all_validators_tests() -> int:
    """Run all validators tests and print a summary.

    Returns an exit code: 0 on success, 1 on failure.
    """
    print('=' * 70)
    print('VALIDATORS SUBSYSTEM - COMPREHENSIVE TEST SUITE')
    print('=' * 70)
    print()

    tests: Tuple[Tuple[str, str], ...] = (
        ("test_character_validator", "Character Validator Tests"),
        ("test_npc_validator", "NPC Validator Tests"),
        ("test_items_validator", "Items Validator Tests"),
        ("test_party_validator", "Party Validator Tests"),
    )

    results: Dict[str, bool] = {}
    for test_file, test_name in tests:
        results[test_name] = run_test_file(test_file, "validators", test_name)

    return print_subsystem_summary(results, "VALIDATORS SUBSYSTEM - TEST SUMMARY")


if __name__ == "__main__":
    sys.exit(run_all_validators_tests())
