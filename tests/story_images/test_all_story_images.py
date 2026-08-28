"""Story-image subsystem test runner."""

import sys
from tests.test_runner_common import print_subsystem_summary, run_test_file


def run_all_story_images_tests():
    """Run all story-image tests and summarize results."""
    print("=" * 70)
    print("STORY IMAGES - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print()

    tests = [
        ("test_events", "Event extraction"),
        ("test_shot", "Shot analysis and scene prompt"),
        ("test_scene_workflow", "Scene workflow builders"),
    ]
    results = {}
    for test_file, test_name in tests:
        results[test_name] = run_test_file(test_file, "story_images", test_name)
    return print_subsystem_summary(results, "STORY IMAGES - TEST SUMMARY")


if __name__ == "__main__":
    sys.exit(run_all_story_images_tests())
