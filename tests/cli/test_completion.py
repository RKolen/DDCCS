"""Tests for src.cli.completion: name and path provider functions."""

from src.cli.completion import (
    get_campaign_names,
    get_character_names,
    get_npc_names,
    get_story_files,
)


# ---------------------------------------------------------------------------
# Character names
# ---------------------------------------------------------------------------


def test_get_character_names_returns_list():
    """get_character_names should return a list."""
    result = get_character_names()
    assert isinstance(result, list)


def test_get_character_names_sorted():
    """get_character_names should return names in sorted order."""
    names = get_character_names()
    assert names == sorted(names)


def test_get_character_names_prefix_filter():
    """get_character_names should apply the case-insensitive prefix filter."""
    all_names = get_character_names()
    if not all_names:
        return

    first_char = all_names[0][0]
    filtered = get_character_names(prefix=first_char)
    assert all(n.lower().startswith(first_char.lower()) for n in filtered)


def test_get_character_names_no_hidden_files():
    """get_character_names should not include names starting with '.'."""
    names = get_character_names()
    assert not any(n.startswith(".") for n in names)


def test_get_character_names_known_characters():
    """Known example characters should appear in the list."""
    names = get_character_names()
    assert {"aragorn", "frodo", "gandalf"}.issubset(set(names))


# ---------------------------------------------------------------------------
# NPC names
# ---------------------------------------------------------------------------


def test_get_npc_names_returns_list():
    """get_npc_names should return a list."""
    result = get_npc_names()
    assert isinstance(result, list)


def test_get_npc_names_sorted():
    """get_npc_names should return names in sorted order."""
    names = get_npc_names()
    assert names == sorted(names)


def test_get_npc_names_prefix_filter():
    """get_npc_names should apply the case-insensitive prefix filter."""
    all_names = get_npc_names()
    if not all_names:
        return
    first_char = all_names[0][0]
    filtered = get_npc_names(prefix=first_char)
    assert all(n.lower().startswith(first_char.lower()) for n in filtered)


# ---------------------------------------------------------------------------
# Campaign names
# ---------------------------------------------------------------------------


def test_get_campaign_names_returns_list():
    """get_campaign_names should return a list."""
    result = get_campaign_names()
    assert isinstance(result, list)


def test_get_campaign_names_sorted():
    """get_campaign_names should return names in sorted order."""
    names = get_campaign_names()
    assert names == sorted(names)


def test_get_campaign_names_known_campaign():
    """The Example_Campaign directory should appear in the list."""
    names = get_campaign_names()
    assert "Example_Campaign" in names


# ---------------------------------------------------------------------------
# Story files
# ---------------------------------------------------------------------------


def test_get_story_files_for_known_campaign():
    """get_story_files should return .md files for Example_Campaign."""
    files = get_story_files("Example_Campaign")
    assert isinstance(files, list)
    assert all(f.endswith(".md") for f in files)


def test_get_story_files_sorted():
    """get_story_files should return file names in sorted order."""
    files = get_story_files("Example_Campaign")
    assert files == sorted(files)


def test_get_story_files_prefix_filter():
    """get_story_files should apply the case-insensitive prefix filter."""
    all_files = get_story_files("Example_Campaign")
    if not all_files:
        return
    first_char = all_files[0][0]
    filtered = get_story_files("Example_Campaign", prefix=first_char)
    assert all(f.lower().startswith(first_char.lower()) for f in filtered)


def test_get_story_files_unknown_campaign_returns_empty():
    """get_story_files for a non-existent campaign should return an empty list."""
    assert get_story_files("__nonexistent_campaign__") == []


if __name__ == "__main__":
    test_get_character_names_returns_list()
    test_get_character_names_sorted()
    test_get_character_names_prefix_filter()
    test_get_character_names_no_hidden_files()
    test_get_character_names_known_characters()
    test_get_npc_names_returns_list()
    test_get_npc_names_sorted()
    test_get_npc_names_prefix_filter()
    test_get_campaign_names_returns_list()
    test_get_campaign_names_sorted()
    test_get_campaign_names_known_campaign()
    test_get_story_files_for_known_campaign()
    test_get_story_files_sorted()
    test_get_story_files_prefix_filter()
    test_get_story_files_unknown_campaign_returns_empty()
    print("All completion tests passed.")
