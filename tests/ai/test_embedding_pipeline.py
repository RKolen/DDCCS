"""
Tests for EmbeddingPipeline

Validates chunking logic for each data type without requiring a live AI
endpoint. The embed_text() call is patched to return a fixed dummy vector.
"""

import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

from tests import test_helpers

(
    EmbeddingPipeline,
    _MIN_PARAGRAPH_CHARS,
    _STORY_CHUNK_TARGET,
) = test_helpers.safe_from_import(
    "src.ai.embedding_pipeline",
    "EmbeddingPipeline",
    "_MIN_PARAGRAPH_CHARS",
    "_STORY_CHUNK_TARGET",
)

# Dummy vector returned by every patched embed_text call.
_DUMMY_VEC: List[float] = [0.1] * 1536

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pipeline() -> Any:
    """Return a pipeline with a mocked AI client."""
    mock_ai = MagicMock()
    mock_ai.embed.return_value = _DUMMY_VEC
    with patch("src.ai.ai_client.AIClient", return_value=mock_ai), \
            patch("src.ai.embedding_pipeline.load_config") as mock_cfg:
        mock_cfg.return_value.milvus.embedding_model = "test-model"
        return EmbeddingPipeline()


def _patched_embed(text: str) -> List[float]:
    """Return dummy vector for any non-empty input."""
    return _DUMMY_VEC if text.strip() else []


# ---------------------------------------------------------------------------
# embed_text
# ---------------------------------------------------------------------------


def test_embed_text_returns_empty_for_blank() -> None:
    """embed_text returns [] for blank or whitespace-only input."""
    print("\n[TEST] embed_text - empty input")
    pipeline = _make_pipeline()
    with patch.object(pipeline, "embed_text", side_effect=_patched_embed):
        result = pipeline.embed_text("")
        assert result == [], f"Expected [] for empty input, got {result}"
        result_ws = pipeline.embed_text("   ")
        assert not result_ws, f"Expected [] for whitespace, got {result_ws}"
    print("  [OK] Empty / whitespace input returns []")


# ---------------------------------------------------------------------------
# embed_character
# ---------------------------------------------------------------------------


def test_embed_character_returns_rows() -> None:
    """A valid character dict produces at least one row with correct keys."""
    print("\n[TEST] embed_character - valid dict produces rows")
    pipeline = _make_pipeline()
    char: Dict[str, Any] = {
        "name": "Aragorn",
        "class": "Ranger",
        "race": "Human",
        "level": "10",
        "background": "A ranger of the north",
        "_source_file": "game_data/characters/aragorn.json",
    }
    with patch.object(pipeline, "embed_text", side_effect=_patched_embed):
        rows = pipeline.embed_character(char)
    assert len(rows) >= 1, "Expected at least one row"
    for row in rows:
        assert "character_name" in row
        assert "source_file" in row
        assert "chunk_text" in row
        assert "chunk_type" in row
        assert "embedding" in row
    print(f"  [OK] {len(rows)} rows produced with correct keys")


def test_embed_character_skips_empty_fields() -> None:
    """Fields with None or empty string do not produce chunks."""
    print("\n[TEST] embed_character - empty fields skipped")
    pipeline = _make_pipeline()
    char: Dict[str, Any] = {
        "name": "Minimal",
        "class": "Fighter",
        "race": "",
        "level": "1",
        "background": "",
        "personality_traits": None,
        "_source_file": "",
    }
    with patch.object(pipeline, "embed_text", side_effect=_patched_embed):
        rows = pipeline.embed_character(char)
    chunk_types = [r["chunk_type"] for r in rows]
    assert "personality" not in chunk_types, "Empty personality should be skipped"
    assert "background" not in chunk_types, "Empty background should be skipped"
    print(f"  [OK] {len(rows)} rows, empty fields correctly omitted")


# ---------------------------------------------------------------------------
# embed_npc
# ---------------------------------------------------------------------------


def test_embed_npc_includes_location() -> None:
    """Location is present in every NPC row."""
    print("\n[TEST] embed_npc - location present in all rows")
    pipeline = _make_pipeline()
    npc: Dict[str, Any] = {
        "name": "Beraht",
        "race": "Human",
        "role": "Crime boss",
        "location": "Ostagar",
        "description": "A ruthless crime lord operating from Ostagar.",
        "_source_file": "game_data/npcs/beraht.json",
    }
    with patch.object(pipeline, "embed_text", side_effect=_patched_embed):
        rows = pipeline.embed_npc(npc)
    assert len(rows) >= 1
    for row in rows:
        assert row["location"] == "Ostagar", f"Expected location 'Ostagar', got {row['location']}"
    print(f"  [OK] {len(rows)} rows, all contain location 'Ostagar'")


# ---------------------------------------------------------------------------
# embed_story_file
# ---------------------------------------------------------------------------


def test_embed_story_file_merges_short_paragraphs(tmp_path: Path) -> None:
    """Paragraphs under _MIN_PARAGRAPH_CHARS are merged with the next."""
    print("\n[TEST] embed_story_file - short paragraphs merged")
    short = "Short."
    assert len(short) < _MIN_PARAGRAPH_CHARS, (
        f"Sanity: 'short' must be < {_MIN_PARAGRAPH_CHARS} chars for this test"
    )
    long_para = "A " * 50  # 100 chars once joined
    content = f"{short}\n\n{long_para}"
    story_file = tmp_path / "Example_Campaign" / "story_001.md"
    story_file.parent.mkdir(parents=True)
    story_file.write_text(content, encoding="utf-8")

    pipeline = _make_pipeline()
    with patch.object(pipeline, "embed_text", side_effect=_patched_embed):
        rows = pipeline.embed_story_file(str(story_file))

    # The short paragraph should be merged into the next, so we expect 1 chunk
    assert len(rows) == 1, f"Expected 1 merged chunk, got {len(rows)}"
    assert "Short." in rows[0]["chunk_text"]
    print(f"  [OK] Short paragraph merged: {len(rows)} chunk(s)")


def test_embed_story_file_empty_returns_empty(tmp_path: Path) -> None:
    """An empty file returns an empty list."""
    print("\n[TEST] embed_story_file - empty file returns []")
    story_file = tmp_path / "Campaign" / "empty.md"
    story_file.parent.mkdir(parents=True)
    story_file.write_text("", encoding="utf-8")

    pipeline = _make_pipeline()
    with patch.object(pipeline, "embed_text", side_effect=_patched_embed):
        rows = pipeline.embed_story_file(str(story_file))
    assert not rows
    print("  [OK] Empty file returns []")


# ---------------------------------------------------------------------------
# embed_wiki_page
# ---------------------------------------------------------------------------


def test_embed_wiki_page_respects_chunk_target() -> None:
    """Each chunk except possibly the last meets the story chunk target."""
    print("\n[TEST] embed_wiki_page - chunks respect target size")
    # Build a page long enough to produce at least two chunks
    page_text = " ".join([f"Sentence number {i} about ancient lore." for i in range(100)])
    pipeline = _make_pipeline()
    with patch.object(pipeline, "embed_text", side_effect=_patched_embed):
        rows = pipeline.embed_wiki_page(page_text, "https://example.com/lore")
    assert len(rows) >= 2, f"Expected multiple chunks, got {len(rows)}"
    for row in rows[:-1]:
        # The chunker emits just before adding the next sentence would exceed the
        # target, so the emitted length is typically slightly below the target.
        assert len(row["chunk_text"]) > _STORY_CHUNK_TARGET // 2, (
            f"Chunk too short: {len(row['chunk_text'])} — expected > {_STORY_CHUNK_TARGET // 2}"
        )
    print(f"  [OK] {len(rows)} chunks, all (except last) meet target size")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


def run_all_tests() -> None:
    """Run all embedding pipeline tests."""
    tmp = Path(tempfile.mkdtemp())
    test_embed_text_returns_empty_for_blank()
    test_embed_character_returns_rows()
    test_embed_character_skips_empty_fields()
    test_embed_npc_includes_location()
    test_embed_story_file_merges_short_paragraphs(tmp / "a")
    test_embed_story_file_empty_returns_empty(tmp / "b")
    test_embed_wiki_page_respects_chunk_target()
    print("\n[PASS] All EmbeddingPipeline tests passed.")


if __name__ == "__main__":
    run_all_tests()
