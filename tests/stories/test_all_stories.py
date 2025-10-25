"""
Story Subsystem Test Runner

This module runs all tests for the story subsystem and provides
a consolidated report of test results.
"""

import sys
import subprocess
from pathlib import Path


def run_test_file(test_file: str, test_name: str) -> bool:
    """
    Run a single test file as a module and return success status.

    Args:
        test_file: Module name (without .py) under the stories package
        test_name: Human-readable test name

    Returns:
        True if tests passed, False otherwise
    """
    print(f"\n{'=' * 70}")
    print(f"Running: {test_name}")
    print('=' * 70)

    try:
        result = subprocess.run(
            [sys.executable, "-m", f"stories.{test_file}"],
            cwd=Path(__file__).parent.parent,
            capture_output=False,
            check=False,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        print(f"[ERROR] Failed to run {test_name}: {e}")
        return False


def run_all_story_tests():
    """Run all story subsystem tests."""
    print("=" * 70)
    print("STORY SUBSYSTEM - FULL TEST SUITE")
    print("=" * 70)
    print()

    tests = [
        ("test_story_updater", "Story Updater Tests"),
        ("test_story_character_loader", "Story Character Loader Tests"),
        ("test_session_results_manager", "Session Results Manager Tests"),
        ("test_party_manager", "Party Manager Tests"),
        ("test_hooks_and_analysis", "Hooks and Analysis Tests"),
        ("test_character_manager", "Character Manager Integration Tests"),
        ("test_enhanced_story_manager", "Enhanced Story Manager Tests"),
        ("test_story_manager", "Story Manager Tests"),
        ("test_story_file_manager", "Story File Manager Tests"),
        ("test_story_analyzer", "Story Analyzer Tests"),
        ("test_character_consistency_integration", "Character Consistency Analysis Tests"),
    ]

    results = {}
    for test_file, test_name in tests:
        results[test_name] = run_test_file(test_file, test_name)

    # Summary
    print("\n" + "=" * 70)
    print("STORY SUBSYSTEM - TEST SUMMARY")
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
        print("\n[SUCCESS] All story subsystem tests passed!")
        print("=" * 70)
        return 0

    print(f"\n[FAILURE] {failed_tests} test file(s) failed")
    print("=" * 70)
    return 1


if __name__ == "__main__":
    sys.exit(run_all_story_tests())
