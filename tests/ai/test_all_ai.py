
"""
AI Subsystem Test Runner

Runs all AI integration tests using the module-runner pattern (subprocess
invocation of each test module) and prints a concise summary.
"""

import sys
from tests.test_runner_common import print_subsystem_summary, run_test_file


def run_all_ai_tests():
    """Run all AI subsystem tests and summarize results."""
    print("=" * 70)
    print("AI INTEGRATION - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print()


    tests = [
        ("test_ai_env_config", "AI Environment Configuration"),
        ("test_ai_client", "AI Client Interface"),
        ("test_rag_system", "RAG System Tests"),
        ("test_behavior_generation_ai_mock", "Behavior Generation (Mock)"),
        ("test_availability", "AI Availability Tests"),
    ]


    results = {}
    for test_file, test_name in tests:
        results[test_name] = run_test_file(test_file, "ai", test_name)


    # Summary (use shared helper)
    return print_subsystem_summary(results, "AI SUBSYSTEM - TEST SUMMARY")



if __name__ == "__main__":
    sys.exit(run_all_ai_tests())
