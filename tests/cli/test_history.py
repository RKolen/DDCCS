"""Tests for src.cli.history: CommandHistory and HistoryEntry."""

import json
import tempfile
from pathlib import Path

from src.cli.history import CommandHistory, HistoryEntry


# ---------------------------------------------------------------------------
# HistoryEntry
# ---------------------------------------------------------------------------


def test_history_entry_to_dict_round_trip():
    """HistoryEntry.to_dict() and from_dict() should be inverse operations."""
    entry = HistoryEntry(
        command="manage_characters",
        timestamp="2026-01-01T10:00:00",
        session_id="20260101_100000",
        working_dir="/home/user",
        success=True,
    )
    restored = HistoryEntry.from_dict(entry.to_dict())
    assert restored.command == entry.command
    assert restored.timestamp == entry.timestamp
    assert restored.session_id == entry.session_id
    assert restored.working_dir == entry.working_dir
    assert restored.success == entry.success


def test_history_entry_from_dict_defaults():
    """from_dict should populate optional fields with sensible defaults."""
    entry = HistoryEntry.from_dict({"command": "test", "timestamp": "2026-01-01T00:00:00"})
    assert entry.session_id == ""
    assert entry.working_dir == ""
    assert entry.success is True


# ---------------------------------------------------------------------------
# CommandHistory: add and retrieve
# ---------------------------------------------------------------------------


def test_add_command_persists_to_file():
    """add_command should write the entry to the JSON history file."""
    with tempfile.TemporaryDirectory() as tmp:
        hist = CommandHistory(history_dir=tmp)
        hist.add_command("manage_stories")

        with open(Path(tmp) / "command_history.json", encoding="utf-8") as fh:
            data = json.load(fh)

        assert len(data["entries"]) == 1
        assert data["entries"][0]["command"] == "manage_stories"


def test_add_command_skips_consecutive_duplicates():
    """Consecutive identical commands should not be stored twice."""
    with tempfile.TemporaryDirectory() as tmp:
        hist = CommandHistory(history_dir=tmp)
        hist.add_command("manage_characters")
        hist.add_command("manage_characters")
        assert len(hist.get_recent(10)) == 1


def test_get_recent_returns_last_n():
    """get_recent should return the most recent entries up to the limit."""
    with tempfile.TemporaryDirectory() as tmp:
        hist = CommandHistory(history_dir=tmp)
        for cmd in ["a", "b", "c", "d", "e"]:
            hist.add_command(cmd)
        recent = hist.get_recent(3)
        assert len(recent) == 3
        assert recent[-1].command == "e"


def test_search_returns_matching_entries():
    """search should return only entries whose command contains the query."""
    with tempfile.TemporaryDirectory() as tmp:
        hist = CommandHistory(history_dir=tmp)
        hist.add_command("manage_characters")
        hist.add_command("manage_stories")
        hist.add_command("read_stories")

        results = hist.search("stories")
        commands = [r.command for r in results]
        assert "manage_stories" in commands
        assert "read_stories" in commands
        assert "manage_characters" not in commands


def test_search_is_case_insensitive():
    """search should match regardless of case."""
    with tempfile.TemporaryDirectory() as tmp:
        hist = CommandHistory(history_dir=tmp)
        hist.add_command("Manage_Characters")
        results = hist.search("manage")
        assert len(results) == 1


# ---------------------------------------------------------------------------
# History navigation
# ---------------------------------------------------------------------------


def test_get_previous_navigates_back():
    """get_previous should step backward through history entries."""
    with tempfile.TemporaryDirectory() as tmp:
        hist = CommandHistory(history_dir=tmp)
        hist.add_command("first")
        hist.add_command("second")

        assert hist.get_previous() == "second"
        assert hist.get_previous() == "first"
        assert hist.get_previous() is None


def test_get_next_navigates_forward():
    """get_next should step forward after navigating back."""
    with tempfile.TemporaryDirectory() as tmp:
        hist = CommandHistory(history_dir=tmp)
        hist.add_command("first")
        hist.add_command("second")

        hist.get_previous()
        hist.get_previous()
        assert hist.get_next() == "second"
        assert hist.get_next() is None


# ---------------------------------------------------------------------------
# Clear and stats
# ---------------------------------------------------------------------------


def test_clear_removes_all_entries():
    """clear() should leave the history empty and persist that state."""
    with tempfile.TemporaryDirectory() as tmp:
        hist = CommandHistory(history_dir=tmp)
        hist.add_command("some_command")
        hist.clear()
        assert hist.get_recent(100) == []


def test_get_stats_empty_history():
    """get_stats on an empty history should return zeroed counts."""
    with tempfile.TemporaryDirectory() as tmp:
        hist = CommandHistory(history_dir=tmp)
        stats = hist.get_stats()
        assert stats["total_commands"] == 0
        assert stats["sessions"] == 0
        assert stats["most_common"] == []


def test_get_stats_populated_history():
    """get_stats should count commands and identify the most-used ones."""
    with tempfile.TemporaryDirectory() as tmp:
        hist = CommandHistory(history_dir=tmp)
        for idx in range(3):
            hist.add_command(f"alpha_{idx}")
        hist.add_command("beta_a")
        hist.add_command("beta_b")

        stats = hist.get_stats()
        assert stats["total_commands"] == 5
        assert stats["sessions"] >= 1


# ---------------------------------------------------------------------------
# Persistence across instances
# ---------------------------------------------------------------------------


def test_history_persists_across_instances():
    """A new CommandHistory pointing to the same dir should reload saved entries."""
    with tempfile.TemporaryDirectory() as tmp:
        hist1 = CommandHistory(history_dir=tmp)
        hist1.add_command("persistent_command")

        hist2 = CommandHistory(history_dir=tmp)
        recent = hist2.get_recent(10)
        assert any(e.command == "persistent_command" for e in recent)


def test_history_trims_to_max():
    """History should not grow beyond MAX_HISTORY entries."""

    class SmallHistory(CommandHistory):
        """CommandHistory with a reduced MAX_HISTORY for testing."""

        MAX_HISTORY = 5

    with tempfile.TemporaryDirectory() as tmp:
        hist = SmallHistory(history_dir=tmp)
        for idx in range(10):
            hist.add_command(f"cmd_{idx}")
        assert len(hist.get_recent(100)) == 5


if __name__ == "__main__":
    test_history_entry_to_dict_round_trip()
    test_history_entry_from_dict_defaults()
    test_add_command_persists_to_file()
    test_add_command_skips_consecutive_duplicates()
    test_get_recent_returns_last_n()
    test_search_returns_matching_entries()
    test_search_is_case_insensitive()
    test_get_previous_navigates_back()
    test_get_next_navigates_forward()
    test_clear_removes_all_entries()
    test_get_stats_empty_history()
    test_get_stats_populated_history()
    test_history_persists_across_instances()
    test_history_trims_to_max()
    print("All history tests passed.")
