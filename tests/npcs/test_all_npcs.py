"""
NPC Subsystem Test Runner

This module runs all tests for the NPC subsystem and provides
a comprehensive report of test results.
"""

import sys
from tests.test_runner_common import print_subsystem_summary, run_test_file


def run_all_npc_tests():
    """Run all NPC subsystem tests."""
    print("=" * 70)
    print("NPC SUBSYSTEM - FULL TEST SUITE")
    print("=" * 70)
    print("\nThis test suite covers:")
    print("  - NPC Agents (agent class, loading, memory)")
    print("  - NPC Auto-Detection (pattern matching, profile generation)")

    # Define all tests to run
    tests = [
        ("test_npc_agents", "NPC Agents Tests"),
        ("test_npc_auto_detection", "NPC Auto-Detection Tests"),
    ]

    results = {}
    for test_file, test_name in tests:
        results[test_name] = run_test_file(test_file, "npcs", test_name)

    # Summary (delegate to shared helper)
    return print_subsystem_summary(results, "NPC SUBSYSTEM - TEST SUMMARY")


if __name__ == "__main__":
    sys.exit(run_all_npc_tests())
