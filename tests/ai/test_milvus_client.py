"""
Tests for MilvusClient

All tests mock pymilvus so these run without a live Milvus instance.
"""

from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

from tests import test_helpers

milvus_client_module = test_helpers.import_module("src.ai.milvus_client")
MilvusClient = test_helpers.safe_from_import("src.ai.milvus_client", "MilvusClient")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_client(prefix: str = "dnd", dim: int = 1536) -> Any:
    """Return a MilvusClient with config patched to known values."""
    with patch("src.ai.milvus_client.load_config") as mock_cfg:
        mc = mock_cfg.return_value.milvus
        mc.host = "localhost"
        mc.port = 19530
        mc.collection_prefix = prefix
        mc.embedding_dim = dim
        return MilvusClient()


# ---------------------------------------------------------------------------
# connect() when pymilvus unavailable
# ---------------------------------------------------------------------------


def test_connect_returns_false_without_pymilvus() -> None:
    """connect() returns False and logs warning when pymilvus not installed."""
    print("\n[TEST] MilvusClient.connect - unavailable pymilvus")
    with patch.object(milvus_client_module, "PYMILVUS_AVAILABLE", False):
        client = _make_client()
        result = client.connect()
    assert result is False, f"Expected False, got {result}"
    assert not client.connected
    print("  [OK] Returns False when PYMILVUS_AVAILABLE is False")


# ---------------------------------------------------------------------------
# collection_name()
# ---------------------------------------------------------------------------


def test_collection_name_respects_prefix() -> None:
    """collection_name() prepends the configured prefix."""
    print("\n[TEST] MilvusClient.collection_name - prefix applied")
    client = _make_client(prefix="dnd")
    assert client.collection_name("characters") == "dnd_characters"
    assert client.collection_name("npcs") == "dnd_npcs"
    assert client.collection_name("story_chunks") == "dnd_story_chunks"
    print("  [OK] Prefix correctly prepended for all collection names")


def test_collection_name_custom_prefix() -> None:
    """collection_name() uses a custom prefix when configured."""
    print("\n[TEST] MilvusClient.collection_name - custom prefix")
    client = _make_client(prefix="myproject")
    assert client.collection_name("wiki_pages") == "myproject_wiki_pages"
    print("  [OK] Custom prefix applied")


# ---------------------------------------------------------------------------
# insert() - column transposition
# ---------------------------------------------------------------------------


def test_insert_transposes_rows() -> None:
    """insert() transposes list-of-dicts into dict-of-lists before passing to col."""
    print("\n[TEST] MilvusClient.insert - row transposition")
    mock_col = MagicMock()
    client = _make_client()
    client.connected = True

    rows: List[Dict[str, Any]] = [
        {"name": "Aragorn", "embedding": [0.1, 0.2]},
        {"name": "Frodo", "embedding": [0.3, 0.4]},
    ]

    with patch.object(client, "get_collection", return_value=mock_col):
        count = client.insert("characters", rows)

    assert count == 2
    # Verify col.insert was called with column-oriented data
    mock_col.insert.assert_called_once()
    inserted_data = mock_col.insert.call_args[0][0]
    # Should be a list of columns: [["Aragorn","Frodo"], [[0.1,0.2],[0.3,0.4]]]
    assert ["Aragorn", "Frodo"] in inserted_data
    print(f"  [OK] {count} rows inserted, column transposition verified")


def test_insert_returns_zero_for_empty_rows() -> None:
    """insert() returns 0 without calling col.insert when rows is empty."""
    print("\n[TEST] MilvusClient.insert - empty rows")
    mock_col = MagicMock()
    client = _make_client()
    client.connected = True

    with patch.object(client, "get_collection", return_value=mock_col):
        count = client.insert("characters", [])

    assert count == 0
    mock_col.insert.assert_not_called()
    print("  [OK] Returns 0 for empty rows without calling insert")


# ---------------------------------------------------------------------------
# search() - score key added
# ---------------------------------------------------------------------------


def test_search_adds_score_to_results() -> None:
    """search() adds a 'score' key to each hit dict."""
    print("\n[TEST] MilvusClient.search - score key added")
    mock_hit = MagicMock()
    mock_hit.entity.get.side_effect = lambda field: f"value_{field}"
    mock_hit.score = 0.92

    mock_col = MagicMock()
    mock_col.search.return_value = [[mock_hit]]

    client = _make_client()
    client.connected = True

    with patch.object(client, "get_collection", return_value=mock_col):
        results = client.search(
            "characters",
            [0.1] * 1536,
            top_k=1,
        )

    assert len(results) == 1
    assert "score" in results[0]
    assert results[0]["score"] == 0.92
    assert results[0]["character_name"] == "value_character_name"
    print(f"  [OK] Score key present: {results[0]['score']}")


# ---------------------------------------------------------------------------
# delete_by_source() - expression building
# ---------------------------------------------------------------------------


def test_delete_by_source_builds_correct_expr() -> None:
    """delete_by_source() calls col.delete with the correct filter expression."""
    print("\n[TEST] MilvusClient.delete_by_source - expression string")
    mock_col = MagicMock()
    client = _make_client()
    client.connected = True

    with patch.object(client, "get_collection", return_value=mock_col):
        client.delete_by_source(
            "characters", "source_file", "game_data/characters/aragorn.json"
        )

    mock_col.delete.assert_called_once_with(
        'source_file == "game_data/characters/aragorn.json"'
    )
    print("  [OK] Correct expression passed to col.delete()")


def test_delete_by_source_no_op_when_unavailable() -> None:
    """delete_by_source() does nothing when collection is None."""
    print("\n[TEST] MilvusClient.delete_by_source - None collection")
    client = _make_client()
    client.connected = False  # get_collection returns None

    # Should not raise
    client.delete_by_source("characters", "source_file", "some_file.json")
    print("  [OK] No error raised when collection unavailable")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_all_tests() -> None:
    """Run all MilvusClient tests."""
    test_connect_returns_false_without_pymilvus()
    test_collection_name_respects_prefix()
    test_collection_name_custom_prefix()
    test_insert_transposes_rows()
    test_insert_returns_zero_for_empty_rows()
    test_search_adds_score_to_results()
    test_delete_by_source_builds_correct_expr()
    test_delete_by_source_no_op_when_unavailable()
    print("\n[PASS] All MilvusClient tests passed.")


if __name__ == "__main__":
    run_all_tests()
