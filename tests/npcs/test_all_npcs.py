"""
NPC Subsystem Test Runner

This module runs all tests for the NPC subsystem and provides
a comprehensive report of test results.
"""

import sys
import subprocess
from pathlib import Path


def run_test_file(test_file: str, test_name: str) -> bool:
    """
    Run a single test file and return success status.

    Args:
        test_file: Path to the test file
        test_name: Human-readable test name

    Returns:
        True if tests passed, False otherwise
    """
    print(f"\n{'=' * 70}")
    print(f"Running: {test_name}")
    print('=' * 70)

    try:
        result = subprocess.run(
            [sys.executable, "-m", f"npcs.{test_file}"],
            cwd=Path(__file__).parent.parent,
            capture_output=False,
            check=False
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        print(f"[ERROR] Failed to run {test_name}: {e}")
        return False


def run_all_npc_tests():
    """Run all NPC subsystem tests."""
    print("=" * 70)
    print("NPC SUBSYSTEM - FULL TEST SUITE")
    print("=" * 70)
    print("\nThis test suite covers:")
    print("  - NPC Agents (agent class, loading, memory)")
    print("  - NPC Auto-Detection (pattern matching, profile generation)")

    # Define all tests to run
    tests = [
        ("test_npc_agents", "NPC Agents Tests"),
        ("test_npc_auto_detection", "NPC Auto-Detection Tests"),
    ]

    results = {}
    for test_file, test_name in tests:
        results[test_name] = run_test_file(test_file, test_name)

    # Print summary
    print("\n" + "=" * 70)
    print("NPC SUBSYSTEM - TEST SUMMARY")
    print("=" * 70)

    total_tests = len(tests)
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
        print("\n[SUCCESS] All NPC subsystem tests passed!")
        print("=" * 70)
        return 0

    print(f"\n[FAILURE] {failed_tests} test file(s) failed")
    print("=" * 70)
    return 1


if __name__ == "__main__":
    sys.exit(run_all_npc_tests())
