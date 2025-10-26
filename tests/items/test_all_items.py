"""Items Subsystem Test Runner

Runs all tests for the items subsystem and prints a concise summary.
Placed alongside other per-subsystem aggregators (e.g., tests/combat/test_all_combat.py)
so the top-level test runner can pick it up.
"""

import sys
import subprocess
from pathlib import Path
from tests.test_runner_common import print_subsystem_summary


def run_test_file(test_file: str, test_name: str) -> bool:
    """Run a single test file as a module and return success status."""
    print(f"\n{'=' * 70}")
    print(f"Running: {test_name}")
    print('=' * 70)

    try:
        result = subprocess.run(
            [sys.executable, "-m", f"items.{test_file}"],
            cwd=Path(__file__).parent.parent,
            check=False,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        print(f"[ERROR] Failed to run {test_name}: {exc}")
        return False


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
        results[test_name] = run_test_file(test_file, test_name)

        # Summary (delegate to shared helper)
        return print_subsystem_summary(results, "ITEMS SUBSYSTEM - TEST SUMMARY")


if __name__ == "__main__":
    sys.exit(run_all_items_tests())
