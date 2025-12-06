"""
Story Subsystem Test Runner

This module runs all tests for the story subsystem and provides
a consolidated report of test results.
"""

import sys
from tests.test_runner_common import print_subsystem_summary, run_test_file


def run_all_story_tests():
    """Run all story subsystem tests."""
    print("=" * 70)
    print("STORY SUBSYSTEM - FULL TEST SUITE")
    print("This one may take a while...")
    print("=" * 70)
    print()

    tests = [
        ("test_story_updater", "Story Updater Tests"),
        ("test_character_loader", "Character Loader Helper Tests"),
        ("test_story_character_loader", "Story Character Loader Tests"),
        ("test_session_results_manager", "Session Results Manager Tests"),
        ("test_party_manager", "Party Manager Tests"),
        ("test_hooks_and_analysis", "Hooks and Analysis Tests"),
        ("test_character_manager", "Character Manager Integration Tests"),
        ("test_enhanced_story_manager", "Enhanced Story Manager Tests"),
        ("test_story_manager", "Story Manager Tests"),
        ("test_story_file_manager", "Story File Manager Tests"),
        ("test_story_analyzer", "Story Analyzer Tests"),
        (
            "test_character_consistency_integration",
            "Character Consistency Analysis Tests",
        ),
        ("test_story_ai_generator", "Story AI Generator Tests"),
        ("test_story_workflow_orchestrator", "Story Workflow Orchestrator Tests"),
        ("test_story_consistency_analyzer", "Story Consistency Analyzer Tests"),
        ("test_lazy_character_loading", "Lazy Character Loading Tests"),
    ]

    results = {}
    for test_file, test_name in tests:
        results[test_name] = run_test_file(test_file, "stories", test_name)

    # Summary (delegate to shared helper)
    return print_subsystem_summary(results, "STORIES SUBSYSTEM - TEST SUMMARY")


if __name__ == "__main__":
    sys.exit(run_all_story_tests())
