"""
Combat Subsystem Test Runner

This module runs all tests for the combat subsystem and provides
a consolidated report of test results.
"""

import sys
import subprocess
from pathlib import Path
from tests.test_runner_common import print_subsystem_summary


def run_all_combat_tests():
    """Run all combat subsystem tests."""
    print("=" * 70)
    print("COMBAT SUBSYSTEM - FULL TEST SUITE")
    print("=" * 70)
    print()

    tests = [
        ("test_combat_narrator", "Combat Narrator Tests"),
        ("test_narrator_ai", "Narrator AI Integration Tests"),
        ("test_narrator_descriptions", "Narrator Descriptions Tests"),
        ("test_narrator_consistency", "Narrator Consistency Tests"),
        ("test_combat_conversion", "Combat Conversion Tests"),
    ]

    def run_test_file(test_file: str, test_name: str) -> bool:
        """Run a single combat test module via `python -m combat.<module>`."""
        print(f"\n{'=' * 70}")
        print(f"Running: {test_name}")
        print('=' * 70)

        try:
            result = subprocess.run(
                [sys.executable, "-m", f"combat.{test_file}"],
                cwd=Path(__file__).parent.parent,
                capture_output=False,
                check=False,
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            print(f"[ERROR] Failed to run {test_name}: {e}")
            return False

    results = {}
    for test_file, test_name in tests:
        results[test_name] = run_test_file(test_file, test_name)

    # Summary (delegate to shared helper)
    return print_subsystem_summary(results, "COMBAT SUBSYSTEM - TEST SUMMARY")


if __name__ == "__main__":
    sys.exit(run_all_combat_tests())
