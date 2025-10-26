"""
Unified Test Runner for D&D Character Consultant System

Runs all test files across the modular test structure.
Can run all tests, specific categories, or individual test files.

Usage:
    python tests/run_all_tests.py                    # Run all tests
    python tests/run_all_tests.py validation         # Run validation tests only
    python tests/run_all_tests.py validation ai      # Run multiple categories
"""

import os
import sys
import subprocess
from pathlib import Path

# Test categories matching src/ structure
TEST_CATEGORIES = [
    "validators",
    "ai",
    "characters",
    "npcs",
    "stories",
    "combat",
    "items",
    "dm",
    "utils",
    "cli",
    "integration",
]


def find_test_files(categories=None):
    """
    Find all test files in specified categories.

    Args:
        categories: List of category names to test. If None, tests all categories.

    Returns:
        List of test file paths
    """
    # If no categories specified, test all
    if not categories:
        categories = TEST_CATEGORIES

    tests_dir = Path(__file__).parent
    test_files = []

    for category in categories:
        category_path = tests_dir / category

        if not category_path.exists():
            continue

        # Prefer a per-category aggregator file named test_all_<category>.py
        aggregator = category_path / f"test_all_{category}.py"
        if aggregator.exists():
            test_files.append(aggregator)
            continue

        # Fallback: if no aggregator present, include any test_*.py files
        for test_file in category_path.glob("test_*.py"):
            test_files.append(test_file)

    return sorted(test_files)


def _print_error_details(errors):
    """Print detailed error information for failed tests."""
    print()
    print("[FAILED] FAILED TESTS:")
    print("-" * 70)
    for test_name, stdout, stderr in errors:
        print(f"\n{test_name}:")
        if stdout:
            print("STDOUT:")
            print(stdout)
        if stderr:
            print("STDERR:")
            print(stderr)
    print("=" * 70)


def _run_single_test(test_file):
    """
    Run a single test file.

    Args:
        test_file: Path to test file

    Returns:
        Tuple of (passed: bool, test_name: str, stdout: str, stderr: str)
    """
    test_name = f"{test_file.parent.name}/{test_file.name}"
    print(f"Running: {test_name}")

    # Set up environment with project root in PYTHONPATH so the `tests`
    # package can be imported by subprocesses (they import
    # `tests.test_runner_common`, which requires the project root on path).
    env = os.environ.copy()
    project_root = str(Path(__file__).parent.parent)
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{project_root}{os.pathsep}{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = project_root

    result = subprocess.run(
        [sys.executable, str(test_file)],
        capture_output=True,
        text=True,
        cwd=test_file.parent.parent.parent,  # Project root
        env=env,
        check=False,
    )

    if result.returncode == 0:
        print("  [SUCCESS] PASSED")
        return True, test_name, result.stdout, result.stderr

    print("  [FAILED] FAILED")
    return False, test_name, result.stdout, result.stderr


def run_tests(categories=None):
    """
    Run tests and report results.

    Args:
        categories: List of category names to test

    Returns:
        True if all tests passed, False otherwise
    """
    print("[D&D] D&D Character Consultant System - Test Suite")
    print("=" * 70)

    if categories:
        print(f"Running tests for: {', '.join(categories)}")
    else:
        print("Running all tests")

    print()

    # Find test files
    test_files = find_test_files(categories)

    if not test_files:
        print("[WARNING] No test files found!")
        return False

    print(f"[Stats] Total test files to run: {len(test_files)}")
    print("-" * 70)
    print()

    # Run each test file
    passed = 0
    failed = 0
    errors = []

    for test_file in test_files:
        success, test_name, stdout, stderr = _run_single_test(test_file)
        if success:
            passed += 1
        else:
            failed += 1
            errors.append((test_name, stdout, stderr))
        print()

    # Print summary
    print("=" * 70)
    print("[Summary] TEST SUMMARY")
    print("-" * 70)
    print(f"Test files run: {len(test_files)}")
    print(f"Passed:         {passed}")
    print(f"Failed:         {failed}")
    print("=" * 70)

    # Print error details if any
    if errors:
        _print_error_details(errors)

    if failed == 0:
        print("\n[SUCCESS] ALL TESTS PASSED!")
        return True

    print(f"\n[FAILED] {failed} TEST FILE(S) FAILED")
    return False


def main():
    """Main entry point."""
    args = sys.argv[1:]

    # Parse arguments (categories only, verbose flag reserved for future use)
    categories = [arg for arg in args if arg not in ("--verbose", "-v")]

    # Validate categories
    if categories:
        invalid = [cat for cat in categories if cat not in TEST_CATEGORIES]
        if invalid:
            print(f"[ERROR] Invalid category(ies): {', '.join(invalid)}")
            print(f"\nValid categories: {', '.join(TEST_CATEGORIES)}")
            return 1

    # Run tests
    success = run_tests(categories if categories else None)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
