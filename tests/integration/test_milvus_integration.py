"""Integration tests for Milvus semantic retrieval.

These tests are skipped automatically when MILVUS_ENABLED is not set to
'true' in the environment. They require a running Milvus instance and a
configured embedding model.

Usage (with Milvus running):
    MILVUS_ENABLED=true python3 tests/integration/test_milvus_integration.py
"""

import os
import unittest.mock
from typing import Optional

try:
    from src.cli.milvus_commands import run_reindex
    from src.ai.semantic_retriever import SemanticRetriever
    from src.ai.milvus_client import MilvusClient
    from src.ai.rag_system import RAGSystem
    _IMPORTS_OK = True
except ImportError:
    _IMPORTS_OK = False


def _skip_if_milvus_disabled() -> Optional[str]:
    """Return a skip reason string when Milvus is not enabled, else None."""
    if os.getenv("MILVUS_ENABLED", "false").lower() != "true":
        return "MILVUS_ENABLED is not set to 'true'"
    if not _IMPORTS_OK:
        return "Milvus source modules could not be imported"
    return None


# ---------------------------------------------------------------------------
# Reindex tests
# ---------------------------------------------------------------------------

def test_reindex_runs_without_error():
    """Run reindex and verify it completes without raising."""
    print("\n[TEST] Reindex runs without error")
    skip = _skip_if_milvus_disabled()
    if skip:
        print(f"  [SKIP] {skip}")
        return
    run_reindex()
    print("  [OK] Reindex completed")
    print("[PASS] Reindex runs without error")


def test_reindex_produces_character_hits():
    """After reindex, querying for a ranger returns at least one hit."""
    print("\n[TEST] Reindex produces character hits")
    skip = _skip_if_milvus_disabled()
    if skip:
        print(f"  [SKIP] {skip}")
        return
    run_reindex()
    retriever = SemanticRetriever()
    if not retriever.is_available():
        print("  [SKIP] Milvus not reachable after reindex")
        return
    hits = retriever.get_relevant_characters("ranger tracker outdoors")
    assert len(hits) > 0, "Expected at least one character hit after reindex"
    print("  [OK] Character hits returned")
    print("[PASS] Reindex produces character hits")


# ---------------------------------------------------------------------------
# Story context tests
# ---------------------------------------------------------------------------

def test_story_context_for_example_campaign():
    """Index Example_Campaign stories and query with a known phrase."""
    print("\n[TEST] Story context for Example_Campaign")
    skip = _skip_if_milvus_disabled()
    if skip:
        print(f"  [SKIP] {skip}")
        return
    run_reindex()
    retriever = SemanticRetriever()
    if not retriever.is_available():
        print("  [SKIP] Milvus not reachable")
        return
    results = retriever.get_relevant_story_context(
        "journey through the wilderness", "Example_Campaign"
    )
    assert isinstance(results, list)
    print("  [OK] Story context returned as list")
    print("[PASS] Story context for Example_Campaign")


def test_story_context_empty_prompt_returns_list():
    """Empty prompt returns a list without crashing."""
    print("\n[TEST] Story context empty prompt returns list")
    skip = _skip_if_milvus_disabled()
    if skip:
        print(f"  [SKIP] {skip}")
        return
    retriever = SemanticRetriever()
    if not retriever.is_available():
        print("  [SKIP] Milvus not reachable")
        return
    results = retriever.get_relevant_story_context("", "Example_Campaign")
    assert isinstance(results, list)
    print("  [OK] Empty prompt handled gracefully")
    print("[PASS] Story context empty prompt returns list")


# ---------------------------------------------------------------------------
# Fallback tests
# ---------------------------------------------------------------------------

def test_fallback_characters_returns_results():
    """SemanticRetriever returns a list fallback when Milvus is down."""
    print("\n[TEST] Fallback characters returns results")
    skip = _skip_if_milvus_disabled()
    if skip:
        print(f"  [SKIP] {skip}")
        return
    with unittest.mock.patch.object(MilvusClient, "is_healthy", return_value=False):
        retriever = SemanticRetriever()
        results = retriever.get_relevant_characters("ranger")
    assert isinstance(results, list)
    print("  [OK] Fallback list returned")
    print("[PASS] Fallback characters returns results")


def test_fallback_npcs_returns_list():
    """NPC fallback returns a list even when Milvus is unreachable."""
    print("\n[TEST] Fallback NPCs returns list")
    skip = _skip_if_milvus_disabled()
    if skip:
        print(f"  [SKIP] {skip}")
        return
    with unittest.mock.patch.object(MilvusClient, "is_healthy", return_value=False):
        retriever = SemanticRetriever()
        results = retriever.get_relevant_npcs("innkeeper at the Prancing Pony")
    assert isinstance(results, list)
    print("  [OK] Fallback NPC list returned")
    print("[PASS] Fallback NPCs returns list")


# ---------------------------------------------------------------------------
# RAGSystem integration tests
# ---------------------------------------------------------------------------

def test_get_relevant_context_returns_string():
    """get_relevant_context always returns a string."""
    print("\n[TEST] get_relevant_context returns string")
    skip = _skip_if_milvus_disabled()
    if skip:
        print(f"  [SKIP] {skip}")
        return
    rag = RAGSystem()
    result = rag.get_relevant_context("dragon attack on the village", "Example_Campaign")
    assert isinstance(result, str)
    print("  [OK] String result returned")
    print("[PASS] get_relevant_context returns string")


def test_get_relevant_context_empty_when_unavailable():
    """Returns empty string when Milvus retriever is unavailable."""
    print("\n[TEST] get_relevant_context empty when unavailable")
    skip = _skip_if_milvus_disabled()
    if skip:
        print(f"  [SKIP] {skip}")
        return
    with unittest.mock.patch.object(SemanticRetriever, "is_available", return_value=False):
        rag = RAGSystem()
        result = rag.get_relevant_context("any prompt", "AnyName_Campaign")
    assert result == ""
    print("  [OK] Empty string returned when unavailable")
    print("[PASS] get_relevant_context empty when unavailable")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all_tests():
    """Run all Milvus integration tests."""
    print("=" * 70)
    print("MILVUS INTEGRATION TESTS")
    print("=" * 70)

    test_reindex_runs_without_error()
    test_reindex_produces_character_hits()
    test_story_context_for_example_campaign()
    test_story_context_empty_prompt_returns_list()
    test_fallback_characters_returns_results()
    test_fallback_npcs_returns_list()
    test_get_relevant_context_returns_string()
    test_get_relevant_context_empty_when_unavailable()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL MILVUS INTEGRATION TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
