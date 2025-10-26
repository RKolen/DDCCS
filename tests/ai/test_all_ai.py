
"""
AI Subsystem Test Runner

Runs all AI integration tests using the module-runner pattern (subprocess
invocation of each test module) and prints a concise summary.
"""

import sys
import subprocess
from pathlib import Path
from tests.test_runner_common import print_subsystem_summary



def run_test_file(test_file: str, test_name: str) -> bool:
    """
    Run a single AI test module via `python -m ai.<module>` and return success.
    """
    print(f"\n{'=' * 70}")
    print(f"Running: {test_name}")
    print('=' * 70)


    try:
        result = subprocess.run(
            [sys.executable, "-m", f"ai.{test_file}"],
            cwd=Path(__file__).parent.parent,
            capture_output=False,
            check=False,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        print(f"[ERROR] Failed to run {test_name}: {e}")
        return False



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
        results[test_name] = run_test_file(test_file, test_name)


    # Summary (use shared helper)
    return print_subsystem_summary(results, "AI SUBSYSTEM - TEST SUMMARY")



if __name__ == "__main__":
    sys.exit(run_all_ai_tests())
