"""
AI Subsystem Test Runner

Runs all AI integration tests: environment config, client interface, and RAG system.
"""

import sys
from pathlib import Path

# Ensure tests package is on sys.path so test helpers can be imported.
sys.path.insert(0, str(Path(__file__).parent.parent))



# Import test modules
try:
    import test_helpers
    import test_ai_env_config
    import test_ai_client
    import test_rag_system
    import test_behavior_generation_ai_mock
except ImportError as e:
    print(f"Error importing AI test modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

# Import and configure test environment
test_helpers.setup_test_environment()

def run_all_ai_tests():
    """Run all AI subsystem tests."""
    print("=" * 70)
    print("AI INTEGRATION - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print()

    # Track results
    all_passed = True

    # Test 1: Environment Configuration
    print("[TEST GROUP 1/4] AI Environment Configuration")
    print("-" * 70)
    try:
        test_ai_env_config.test_ollama_connection_and_model()
        print("[PASS] Environment configuration tests passed")
    except (AssertionError, RuntimeError, OSError) as e:
        print(f"[FAIL] Environment configuration tests failed: {e}")
        all_passed = False
    print()

    # Test 2: AI Client
    print("[TEST GROUP 2/4] AI Client Interface")
    print("-" * 70)
    try:
        test_ai_client.run_all_tests()
        print("[PASS] AI client tests passed")
    except (AssertionError, RuntimeError, ValueError) as e:
        print(f"[FAIL] AI client tests failed: {e}")
        all_passed = False
    print()

    # Test 3: RAG System
    print("[TEST GROUP 3/4] RAG System (Retrieval-Augmented Generation)")
    print("-" * 70)
    try:
        test_rag_system.run_all_tests()
        print("[PASS] RAG system tests passed")
    except (AssertionError, RuntimeError, OSError, ValueError) as e:
        print(f"[FAIL] RAG system tests failed: {e}")
        all_passed = False
    print()

    # Test 4: Behavior Generation
    print("[TEST GROUP 4/4] Behavior Generation")
    print("-" * 70)
    try:
        test_behavior_generation_ai_mock.run()
        print("[PASS] Behavior generation tests passed")
    except (AssertionError, RuntimeError, OSError, ValueError) as e:
        print(f"[FAIL] Behavior generation tests failed: {e}")
        all_passed = False
    print()

    # Summary
    print("=" * 70)
    if all_passed:
        print("[SUCCESS] ALL AI INTEGRATION TESTS PASSED")
        print("=" * 70)
        return 0

    print("[FAILED] SOME AI INTEGRATION TESTS FAILED")
    print("=" * 70)
    return 1


if __name__ == "__main__":
    sys.exit(run_all_ai_tests())
