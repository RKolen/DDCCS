"""Common helpers for per-subsystem test aggregator scripts.

This module centralizes small helpers used by many
``test_all_<subsystem>.py`` files to avoid duplicated scaffolding that
triggers Pylint R0801 (duplicate-code).

Public utilities in this module:
- print_subsystem_summary(results: Dict[str, bool], title: str) -> int
- run_test_file(test_file: str, module_prefix: str, test_name: str) -> bool

The ``run_test_file`` helper centralizes the subprocess invocation used to
run per-file test modules (the pattern ``python -m <package>.<module>``).
Aggregator scripts should import it rather than reimplementing the same
subprocess wrapper.
"""
from typing import Dict
import sys
import subprocess
from pathlib import Path


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


def run_test_file(test_file: str, module_prefix: str, test_name: str) -> bool:
    """Run a single test module using ``python -m`` and return whether it passed.

    Args:
        test_file: Module name (without package), e.g. "test_character_profile"
        module_prefix: Package prefix to use with -m, e.g. "characters"
        test_name: Human-readable test name for logging

    Returns:
        True if the module's process returned exit code 0, False otherwise.
    """
    print(f"\n{'=' * 70}")
    print(f"Running: {test_name}")
    print('=' * 70)

    try:
        result = subprocess.run(
            [sys.executable, "-m", f"{module_prefix}.{test_file}"],
            cwd=Path(__file__).parent.parent,
            capture_output=False,
            check=False,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        print(f"[ERROR] Failed to run {test_name}: {e}")
        return False
