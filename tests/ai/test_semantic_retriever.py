"""
Tests for SemanticRetriever

Validates Milvus path and fallback path without a live instance.
All mocks are captured at construction time and accessed directly
so no private members of the retriever are touched.
"""

from typing import Any, Dict, List, Tuple
from unittest.mock import MagicMock, patch

from tests import test_helpers

SemanticRetriever = test_helpers.safe_from_import(
    "src.ai.semantic_retriever", "SemanticRetriever"
)

# Dummy embedding returned by all patched embed calls
_DUMMY_VEC: List[float] = [0.1] * 1536

# Sample hit from MilvusClient.search()
_CHAR_HIT: Dict[str, Any] = {
    "character_name": "Aragorn",
    "chunk_text": "A ranger of the north.",
    "chunk_type": "background",
    "source_file": "game_data/characters/aragorn.json",
    "score": 0.85,
}

_NPC_HIT: Dict[str, Any] = {
    "npc_name": "Inn Keeper",
    "location": "Bree",
    "chunk_text": "Runs the Prancing Pony tavern.",
    "source_file": "game_data/npcs/innkeeper.json",
    "score": 0.80,
}

_STORY_HIT: Dict[str, Any] = {
    "campaign_name": "Example_Campaign",
    "story_file": "story_001.md",
    "chunk_index": 3,
    "chunk_text": "The fellowship departed at dawn.",
    "score": 0.88,
}


# ---------------------------------------------------------------------------
# Helper - returns retriever AND the mock objects so tests never need
# to access private attributes of the retriever.
# ---------------------------------------------------------------------------


def _make_retriever(
    healthy: bool = True,
) -> Tuple[Any, MagicMock, MagicMock]:
    """Build a SemanticRetriever with mocked client and pipeline.

    Args:
        healthy: Whether is_healthy() returns True or False.

    Returns:
        Tuple of (retriever, mock_client, mock_pipeline).
    """
    mock_client = MagicMock()
    mock_client.is_healthy.return_value = healthy

    mock_pipeline = MagicMock()
    mock_pipeline.embed_text.return_value = _DUMMY_VEC

    with patch("src.ai.semantic_retriever.MilvusClient", return_value=mock_client), \
            patch("src.ai.semantic_retriever.EmbeddingPipeline", return_value=mock_pipeline), \
            patch("src.ai.semantic_retriever.load_config") as mock_cfg:
        mock_cfg.return_value.milvus.enabled = False
        mock_cfg.return_value.milvus.top_k = 5
        mock_cfg.return_value.milvus.similarity_threshold = 0.7
        return SemanticRetriever(), mock_client, mock_pipeline


# ---------------------------------------------------------------------------
# get_relevant_characters
# ---------------------------------------------------------------------------


def test_get_relevant_characters_milvus_path() -> None:
    """When Milvus is healthy, results come from the search backend."""
    print("\n[TEST] SemanticRetriever.get_relevant_characters - Milvus path")
    retriever, mock_client, _ = _make_retriever(healthy=True)
    mock_client.search.return_value = [_CHAR_HIT]

    results = retriever.get_relevant_characters("ranger in the north")

    mock_client.search.assert_called_once()
    assert len(results) == 1
    assert results[0]["character_name"] == "Aragorn"
    print(f"  [OK] {len(results)} result(s) from Milvus search")


def test_get_relevant_characters_uses_fallback_when_unavailable() -> None:
    """When Milvus is not healthy, search is never called."""
    print("\n[TEST] SemanticRetriever.get_relevant_characters - fallback path")
    retriever, mock_client, _ = _make_retriever(healthy=False)

    retriever.get_relevant_characters("halfling adventurer")

    mock_client.search.assert_not_called()
    print("  [OK] search() bypassed; keyword fallback used instead")


# ---------------------------------------------------------------------------
# get_relevant_npcs
# ---------------------------------------------------------------------------


def test_get_relevant_npcs_appends_location_to_query() -> None:
    """Location string is appended to the query before embedding."""
    print("\n[TEST] SemanticRetriever.get_relevant_npcs - location in query")
    retriever, mock_client, mock_pipeline = _make_retriever(healthy=True)
    mock_client.search.return_value = [_NPC_HIT]

    retriever.get_relevant_npcs("innkeeper", location="Bree")

    embed_calls = mock_pipeline.embed_text.call_args_list
    assert len(embed_calls) == 1
    combined_query = embed_calls[0][0][0]
    assert "Bree" in combined_query, f"Expected 'Bree' in query, got: {combined_query}"
    print(f"  [OK] Location appended to query: '{combined_query}'")


def test_get_relevant_npcs_no_location_uses_raw_query() -> None:
    """When no location is given, query is used as-is."""
    print("\n[TEST] SemanticRetriever.get_relevant_npcs - no location")
    retriever, _, mock_pipeline = _make_retriever(healthy=True)
    mock_pipeline.embed_text.return_value = _DUMMY_VEC

    retriever.get_relevant_npcs("mysterious merchant")

    embed_calls = mock_pipeline.embed_text.call_args_list
    query_used = embed_calls[0][0][0]
    assert "location:" not in query_used
    print(f"  [OK] No location suffix in query: '{query_used}'")


# ---------------------------------------------------------------------------
# Threshold filtering (tested through the public API)
# ---------------------------------------------------------------------------


def test_threshold_filters_low_score_results() -> None:
    """Results below the similarity threshold (0.7) are discarded."""
    print("\n[TEST] SemanticRetriever threshold filtering via public API")
    retriever, mock_client, _ = _make_retriever(healthy=True)
    mock_client.search.return_value = [
        {"character_name": "Aragorn", "chunk_text": "High", "score": 0.90},
        {"character_name": "Ghost", "chunk_text": "Low", "score": 0.60},
    ]

    results = retriever.get_relevant_characters("test query")

    names = [r["character_name"] for r in results]
    assert "Aragorn" in names, "High-score hit should pass threshold 0.7"
    assert "Ghost" not in names, "Low-score hit (0.60) should be filtered"
    print(f"  [OK] {len(results)} result(s) pass threshold; low-score hit removed")


# ---------------------------------------------------------------------------
# get_relevant_story_context
# ---------------------------------------------------------------------------


def test_get_relevant_story_context_scopes_by_campaign() -> None:
    """The Milvus search expression includes the campaign name."""
    print("\n[TEST] SemanticRetriever.get_relevant_story_context - campaign scope")
    retriever, mock_client, _ = _make_retriever(healthy=True)
    mock_client.search.return_value = [_STORY_HIT]

    retriever.get_relevant_story_context("fellowship departed", "Example_Campaign")

    search_call = mock_client.search.call_args
    call_kwargs = search_call[1] if search_call[1] else {}
    call_pos = search_call[0] if search_call[0] else []
    expr = call_kwargs.get("expr") or (call_pos[4] if len(call_pos) > 4 else "")
    assert "Example_Campaign" in expr, f"Campaign name missing from expr: {expr}"
    print(f"  [OK] Campaign name present in filter expr: '{expr}'")


def test_get_relevant_story_context_returns_empty_when_unavailable() -> None:
    """Returns [] and never calls search when Milvus is down."""
    print("\n[TEST] SemanticRetriever.get_relevant_story_context - unavailable")
    retriever, mock_client, _ = _make_retriever(healthy=False)

    results = retriever.get_relevant_story_context("some prompt", "Example_Campaign")

    assert results == []
    mock_client.search.assert_not_called()
    print("  [OK] Returns [] when Milvus unavailable")


# ---------------------------------------------------------------------------
# get_relevant_lore
# ---------------------------------------------------------------------------


def test_get_relevant_lore_returns_empty_when_unavailable() -> None:
    """Returns [] when Milvus is not reachable."""
    print("\n[TEST] SemanticRetriever.get_relevant_lore - unavailable")
    retriever, mock_client, _ = _make_retriever(healthy=False)
    results = retriever.get_relevant_lore("ancient ruins")
    assert results == []
    mock_client.search.assert_not_called()
    print("  [OK] Returns [] when Milvus unavailable")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_all_tests() -> None:
    """Run all SemanticRetriever tests."""
    test_get_relevant_characters_milvus_path()
    test_get_relevant_characters_uses_fallback_when_unavailable()
    test_get_relevant_npcs_appends_location_to_query()
    test_get_relevant_npcs_no_location_uses_raw_query()
    test_threshold_filters_low_score_results()
    test_get_relevant_story_context_scopes_by_campaign()
    test_get_relevant_story_context_returns_empty_when_unavailable()
    test_get_relevant_lore_returns_empty_when_unavailable()
    print("\n[PASS] All SemanticRetriever tests passed.")


if __name__ == "__main__":
    run_all_tests()
