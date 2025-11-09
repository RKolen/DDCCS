"""Utils Subsystem Test Runner

Runs all tests for the utils subsystem and prints a concise summary. Placed
alongside other per-subsystem aggregators so the top-level test runner can pick it up.
"""

import sys
from typing import Dict, Tuple
from tests.test_runner_common import print_subsystem_summary, run_test_file


def run_all_utils_tests() -> int:
    """Run all tests in the utils subsystem and print a summary.

    Returns:
        Exit code 0 on success, 1 on failure (consistent with other subsystem runners).
    """
    print("=" * 70)
    print("UTILS SUBSYSTEM - FULL TEST SUITE")
    print("=" * 70)
    print()

    tests: Tuple[Tuple[str, str], ...] = (
        ("test_path_utils", "Path Utilities Tests"),
        ("test_cache_utils", "Cache Utilities Tests"),
        ("test_behaviour_generation", "Behaviour Generation Tests"),
        ("test_cli_utils", "CLI Utilities Tests"),
        ("test_dnd_rules", "DND Rules Utilities Tests"),
        ("test_file_io", "File IO Utilities Tests"),
        ("test_markdown_utils", "Markdown Utilities Tests"),
        ("test_spell_highlighter", "Spell Highlighter Tests"),
        ("test_story_formatting_utils", "Story Formatting Tests"),
        ("test_story_parsing_utils", "Story Parsing Tests"),
        ("test_string_utils", "String Utilities Tests"),
        ("test_text_formatting_utils", "Text Formatting Tests"),
        ("test_validation_helpers", "Validation Helpers Tests"),
        ("test_story_file_helpers", "Story File Helpers Tests"),
    )

    results: Dict[str, bool] = {}
    for test_file, test_name in tests:
        results[test_name] = run_test_file(test_file, "utils", test_name)

    # Summary (delegate to shared helper)
    return print_subsystem_summary(results, "UTILS SUBSYSTEM - TEST SUMMARY")


if __name__ == "__main__":
    sys.exit(run_all_utils_tests())
