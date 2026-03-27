"""Tests for spotlight_signals.py signal collector functions.

Uses real game_data from Example_Campaign and existing character/NPC files.
All tests work offline without an AI connection.
"""

import json
import os
import tempfile
from pathlib import Path

from src.stories.spotlight_signals import (
    collect_dc_failure_signals,
    collect_recency_signals,
    collect_relationship_tension_signals,
    collect_unresolved_thread_signals,
)

project_root = Path(__file__).parent.parent.parent.resolve()
_CAMPAIGN_PATH = str(project_root / "game_data" / "campaigns" / "Example_Campaign")
_CHARACTER_NAMES = ["Aragorn", "Frodo Baggins", "Gandalf the Grey"]
_NPC_NAMES = ["Barliman Butterbur"]


# ---------------------------------------------------------------------------
# Recency signal tests
# ---------------------------------------------------------------------------


def test_collect_recency_signals_returns_dict():
    """collect_recency_signals returns a dict (possibly empty)."""
    result = collect_recency_signals(_CAMPAIGN_PATH, _CHARACTER_NAMES, "character")

    assert isinstance(result, dict), "Should return a dict"


def test_collect_recency_signals_absent_entity_gets_signal():
    """An entity absent from all sessions receives a recency signal."""
    with tempfile.TemporaryDirectory() as tmp:
        # Write two story files that never mention "Mystery Character"
        for num, name in [("001", "first"), ("002", "second")]:
            filepath = os.path.join(tmp, f"{num}_{name}.md")
            with open(filepath, "w", encoding="utf-8") as fh:
                fh.write("Aragorn walked through the forest.\n")

        result = collect_recency_signals(tmp, ["Mystery Character"], "character")

    assert "Mystery Character" in result, "Absent entity should get a recency signal"
    signal = result["Mystery Character"]
    assert signal.signal_type == "recency"
    assert signal.weight > 0


def test_collect_recency_signals_present_entity_no_signal():
    """An entity appearing in the last session receives no recency signal."""
    with tempfile.TemporaryDirectory() as tmp:
        filepath = os.path.join(tmp, "001_only.md")
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write("Aragorn led the charge at dawn.\n")

        result = collect_recency_signals(tmp, ["Aragorn"], "character")

    assert "Aragorn" not in result, "Entity in last session should not get recency signal"


def test_collect_recency_signals_empty_campaign():
    """Empty campaign directory returns empty dict."""
    with tempfile.TemporaryDirectory() as tmp:
        result = collect_recency_signals(tmp, ["Aragorn"], "character")

    assert not result, "Empty campaign should return empty dict"


def test_collect_recency_signals_weight_proportional():
    """Absent entities score higher when more sessions have passed."""
    with tempfile.TemporaryDirectory() as tmp:
        for num, name in [("001", "first"), ("002", "second"), ("003", "third")]:
            filepath = os.path.join(tmp, f"{num}_{name}.md")
            with open(filepath, "w", encoding="utf-8") as fh:
                # Only mention Hero in first session
                if num == "001":
                    fh.write("Hero appears here.\n")
                else:
                    fh.write("No mention of anyone.\n")

        result = collect_recency_signals(tmp, ["Hero"], "character", recency_weight=20.0)

    assert "Hero" in result, "Entity absent from recent sessions should score"
    # Absent for 2 of 3 sessions -> weight = 20 * (2/3) ~= 13.33
    assert result["Hero"].weight > 10.0


# ---------------------------------------------------------------------------
# Unresolved thread signal tests
# ---------------------------------------------------------------------------


def test_collect_unresolved_thread_signals_finds_mentioned_entity():
    """Entity mentioned in Unresolved Plot Threads section gets a signal."""
    with tempfile.TemporaryDirectory() as tmp:
        hooks_path = os.path.join(tmp, "story_hooks_2026-01-01_001_start.md")
        with open(hooks_path, "w", encoding="utf-8") as fh:
            fh.write("## Unresolved Plot Threads\n\n")
            fh.write("1. What happened to Aragorn after the battle?\n")
            fh.write("2. Will Frodo recover?\n")

        result = collect_unresolved_thread_signals(
            tmp, ["Aragorn", "Frodo", "Gandalf"]
        )

    assert "Aragorn" in result, "Aragorn mentioned in threads should get signal"
    assert "Frodo" in result, "Frodo mentioned in threads should get signal"
    assert "Gandalf" not in result, "Gandalf not mentioned should not get signal"


def test_collect_unresolved_thread_signals_no_hooks_returns_empty():
    """No hooks file returns empty dict."""
    with tempfile.TemporaryDirectory() as tmp:
        result = collect_unresolved_thread_signals(tmp, ["Aragorn"])

    assert not result, "No hooks file should return empty dict"


def test_collect_unresolved_thread_signals_npc_followup_section():
    """Entity in NPC Follow-ups section also receives a signal."""
    with tempfile.TemporaryDirectory() as tmp:
        hooks_path = os.path.join(tmp, "story_hooks_2026-01-01_001_start.md")
        with open(hooks_path, "w", encoding="utf-8") as fh:
            fh.write("## NPC Follow-ups\n\n")
            fh.write("- Butterbur expects the party to return with news.\n")

        result = collect_unresolved_thread_signals(tmp, ["Butterbur"])

    assert "Butterbur" in result


def test_collect_unresolved_thread_with_real_campaign():
    """Signal collection runs without error on Example_Campaign."""
    result = collect_unresolved_thread_signals(_CAMPAIGN_PATH, _CHARACTER_NAMES)

    assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# DC failure signal tests
# ---------------------------------------------------------------------------


def test_collect_dc_failure_signals_returns_dict():
    """collect_dc_failure_signals returns a dict."""
    result = collect_dc_failure_signals(_CAMPAIGN_PATH, _CHARACTER_NAMES)

    assert isinstance(result, dict)


def test_collect_dc_failure_signals_detects_dc_section():
    """Character mentioned in DC Suggestions Needed section gets a signal."""
    with tempfile.TemporaryDirectory() as tmp:
        story_path = os.path.join(tmp, "001_test.md")
        with open(story_path, "w", encoding="utf-8") as fh:
            fh.write("## DC Suggestions Needed\n\n")
            fh.write("- Aragorn needs to pass DC 15 Perception to spot the ambush.\n")

        result = collect_dc_failure_signals(tmp, ["Aragorn", "Gandalf"])

    assert "Aragorn" in result, "Aragorn in DC section should get signal"
    assert result["Aragorn"].signal_type == "dc_failure"


def test_collect_dc_failure_signals_empty_campaign():
    """Empty campaign returns empty dict."""
    with tempfile.TemporaryDirectory() as tmp:
        result = collect_dc_failure_signals(tmp, ["Aragorn"])

    assert not result


# ---------------------------------------------------------------------------
# Relationship tension signal tests
# ---------------------------------------------------------------------------


def test_collect_relationship_tension_signals_with_real_characters():
    """collect_relationship_tension_signals runs without error on real data."""
    result = collect_relationship_tension_signals(
        _CHARACTER_NAMES, workspace_path=str(project_root)
    )

    assert isinstance(result, dict)


def test_collect_relationship_tension_signals_detects_tension():
    """Character profile with tension keyword in relationships gets a signal."""
    with tempfile.TemporaryDirectory() as tmp:
        char_data = {
            "name": "TestHero",
            "dnd_class": "Fighter",
            "relationships": {
                "Villain": "Deeply hostile rivalry that defines his existence.",
                "Ally": "Close and trusted friend.",
            },
        }
        chars_dir = os.path.join(tmp, "game_data", "characters")
        os.makedirs(chars_dir)
        char_path = os.path.join(chars_dir, "testhero.json")
        with open(char_path, "w", encoding="utf-8") as fh:
            json.dump(char_data, fh)

        result = collect_relationship_tension_signals(
            ["TestHero"], workspace_path=tmp
        )

    assert "TestHero" in result, "Character with hostile relationship should get signal"
    assert result["TestHero"].signal_type == "relationship_tension"
    assert result["TestHero"].weight > 0


def test_collect_relationship_tension_signals_no_tension():
    """Character with no tension keywords gets no signal."""
    with tempfile.TemporaryDirectory() as tmp:
        char_data = {
            "name": "PeacefulBard",
            "dnd_class": "Bard",
            "relationships": {
                "Everyone": "Loved and appreciated by all.",
            },
        }
        chars_dir = os.path.join(tmp, "game_data", "characters")
        os.makedirs(chars_dir)
        char_path = os.path.join(chars_dir, "peacefulbard.json")
        with open(char_path, "w", encoding="utf-8") as fh:
            json.dump(char_data, fh)

        result = collect_relationship_tension_signals(
            ["PeacefulBard"], workspace_path=tmp
        )

    assert "PeacefulBard" not in result


if __name__ == "__main__":
    test_collect_recency_signals_returns_dict()
    test_collect_recency_signals_absent_entity_gets_signal()
    test_collect_recency_signals_present_entity_no_signal()
    test_collect_recency_signals_empty_campaign()
    test_collect_recency_signals_weight_proportional()
    test_collect_unresolved_thread_signals_finds_mentioned_entity()
    test_collect_unresolved_thread_signals_no_hooks_returns_empty()
    test_collect_unresolved_thread_signals_npc_followup_section()
    test_collect_unresolved_thread_with_real_campaign()
    test_collect_dc_failure_signals_returns_dict()
    test_collect_dc_failure_signals_detects_dc_section()
    test_collect_dc_failure_signals_empty_campaign()
    test_collect_relationship_tension_signals_with_real_characters()
    test_collect_relationship_tension_signals_detects_tension()
    test_collect_relationship_tension_signals_no_tension()
    print("\nAll spotlight_signals tests passed.")
