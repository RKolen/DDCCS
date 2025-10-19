"""
Character Subsystem Test Runner

This module runs all tests for the character subsystem and provides
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
            [sys.executable, "-m", f"characters.{test_file}"],
            cwd=Path(__file__).parent.parent,
            capture_output=False,
            check=False
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        print(f"[ERROR] Failed to run {test_name}: {e}")
        return False


def run_all_character_tests():
    """Run all character subsystem tests."""
    print("=" * 70)
    print("CHARACTER SUBSYSTEM - FULL TEST SUITE")
    print("=" * 70)
    print("\nThis test suite covers:")
    print("  - Character Profile (nested dataclass structure)")
    print("  - Class Knowledge (12 D&D classes)")
    print("  - Character Sheet (enums and NPCs)")
    print("  - Character Consistency (development tracking)")
    print("  - Consultant Core (main consultant class)")
    print("  - Consultant DC (difficulty class calculations)")
    print("  - Consultant Story (story analysis)")
    print("  - Consultant AI (AI integration)")

    # Define all tests to run
    tests = [
        ("test_character_profile", "Character Profile Tests"),
        ("test_class_knowledge", "Class Knowledge Tests"),
        ("test_character_sheet", "Character Sheet Tests"),
        ("test_character_consistency", "Character Consistency Tests"),
        ("test_consultant_core", "Consultant Core Tests"),
        ("test_consultant_dc", "DC Calculator Tests"),
        ("test_consultant_story", "Story Analyzer Tests"),
        ("test_consultant_ai", "AI Consultant Tests"),
    ]

    results = {}
    for test_file, test_name in tests:
        results[test_name] = run_test_file(test_file, test_name)

    # Print summary
    print("\n" + "=" * 70)
    print("CHARACTER SUBSYSTEM - TEST SUMMARY")
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
        print("\n[SUCCESS] All character subsystem tests passed!")
        print("=" * 70)
        return 0

    print(f"\n[FAILURE] {failed_tests} test file(s) failed")
    print("=" * 70)
    return 1


if __name__ == "__main__":
    sys.exit(run_all_character_tests())
