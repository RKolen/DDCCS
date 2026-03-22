"""Sessions Subsystem Test Runner."""

import sys
from tests.test_runner_common import print_subsystem_summary, run_test_file


def run_all_sessions_tests() -> int:
    """Run all sessions subsystem tests."""
    print("=" * 70)
    print("SESSIONS SUBSYSTEM - FULL TEST SUITE")
    print("=" * 70)
    print()

    tests = [
        ("test_session_notes", "Session Notes and Manager Tests"),
    ]

    results = {}
    for test_file, test_name in tests:
        results[test_name] = run_test_file(test_file, "sessions", test_name)

    return print_subsystem_summary(results, "SESSIONS SUBSYSTEM - TEST SUMMARY")


if __name__ == "__main__":
    sys.exit(run_all_sessions_tests())
