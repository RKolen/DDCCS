"""DM Subsystem Test Runner

Runs all tests for the dm subsystem and prints a concise summary. Placed
alongside other per-subsystem aggregators so the top-level test runner can pick it up.
"""

import sys
import subprocess
from pathlib import Path


def run_test_file(test_file: str, test_name: str) -> bool:
    """Run a single test file as a module and return success status."""
    print(f"\n{'=' * 70}")
    print(f"Running: {test_name}")
    print('=' * 70)

    try:
        result = subprocess.run(
            [sys.executable, "-m", f"dm.{test_file}"],
            cwd=Path(__file__).parent.parent,
            check=False,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError) as exc:
        print(f"[ERROR] Failed to run {test_name}: {exc}")
        return False


def run_all_dm_tests() -> int:
    """Run all tests in the dm subsystem and print a summary."""
    print("=" * 70)
    print("DM SUBSYSTEM - FULL TEST SUITE")
    print("=" * 70)
    print()

    tests = [
        ("test_dungeon_master", "Dungeon Master Consultant Tests"),
        ("test_history_check_helper", "History Check Helper Tests"),
        ("test_suggest_narrative_with_character_insights",
         "Suggest Narrative Character Insights Tests"),
        ("test_generate_narrative_with_ai_client_and_rag", "Generate Narrative AI+RAG Tests"),
        ("test_check_consistency_relationships", "Consistency: Relationships Tests"),
    ]

    results = {}
    for test_file, test_name in tests:
        results[test_name] = run_test_file(test_file, test_name)

    # Summary
    print("\n" + "=" * 70)
    print("DM SUBSYSTEM - TEST SUMMARY")
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
        print("\n[SUCCESS] All dm subsystem tests passed!")
        print("=" * 70)
        return 0

    print(f"\n[FAILURE] {failed} test file(s) failed")
    print("=" * 70)
    return 1


if __name__ == "__main__":
    sys.exit(run_all_dm_tests())
