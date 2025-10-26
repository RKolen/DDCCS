"""CLI Subsystem Test Runner

Runs all tests for the CLI subsystem and prints a concise summary. Placed
alongside other per-subsystem aggregators so the top-level test runner can pick it up.
"""

import sys
import subprocess
from pathlib import Path
from typing import Dict, Tuple


def run_test_file(test_file: str, test_name: str) -> bool:
    """Run a single test file as a module and return success status.

    Args:
        test_file: Module name (without package prefix) under `tests/cli`.
        test_name: Human-friendly test name used in output.
    Returns:
        True if the test module exited with return code 0, False otherwise.
    """
    print(f"\n{'=' * 70}")
    print(f"Running: {test_name}")
    print('=' * 70)

    try:
        result = subprocess.run(
            [sys.executable, "-m", f"cli.{test_file}"],
            cwd=Path(__file__).parent.parent,
            check=False,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        print(f"[ERROR] Failed to run {test_name}: {exc}")
        return False


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
    )

    results: Dict[str, bool] = {}
    for test_file, test_name in tests:
        results[test_name] = run_test_file(test_file, test_name)

    # Summary
    print("\n" + "=" * 70)
    print("CLI SUBSYSTEM - TEST SUMMARY")
    print("=" * 70)

    total = len(tests)
    passed = sum(1 for ok in results.values() if ok)
    failed = total - passed

    for name, ok in results.items():
        status = "[PASS]" if ok else "[FAIL]"
        print(f"{status} {name}")

    print("\n" + "-" * 70)
    print(f"Total: {total} test files")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("-" * 70)

    if failed == 0:
        print("\n[SUCCESS] All cli subsystem tests passed!")
        print("=" * 70)
        return 0

    print(f"\n[FAILURE] {failed} test file(s) failed")
    print("=" * 70)
    return 1


if __name__ == "__main__":
    sys.exit(run_all_cli_tests())
