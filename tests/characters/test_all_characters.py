"""
Character Subsystem Test Runner

This module runs all tests for the character subsystem and provides
a comprehensive report of test results.
"""

import sys
from tests.test_runner_common import print_subsystem_summary, run_test_file


# Reuse the shared run_test_file from tests.test_runner_common


def run_all_character_tests():
    """Run all character subsystem tests."""
    print("=" * 70)
    print("CHARACTER SUBSYSTEM - FULL TEST SUITE")
    print("This one may take a while...")
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
        results[test_name] = run_test_file(test_file, "characters", test_name)

    # Summary (delegate to shared helper)
    return print_subsystem_summary(results, "CHARACTERS SUBSYSTEM - TEST SUMMARY")


if __name__ == "__main__":
    sys.exit(run_all_character_tests())
