"""CLI NPC Manager Tests

Tests for NpcCLIManager: listing, viewing, and validating major NPCs.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from src.cli.cli_npc_manager import NpcCLIManager
from tests.test_helpers import sample_major_npc_data


def _write_major_npc(directory: str, filename: str, name: str) -> str:
    """Write a minimal valid major NPC JSON file and return the path."""
    data = sample_major_npc_data(
        name=name,
        first_name=name,
        last_name=None,
        overrides={"relationships": {"The Party": "Enemies"}},
    )
    filepath = os.path.join(directory, filename)
    Path(filepath).write_text(json.dumps(data), encoding="utf-8")
    return filepath


def test_list_major_npcs_empty():
    """List command prints a message when no major NPC files exist."""
    print("\n[TEST] List Major NPCs - Empty")

    with tempfile.TemporaryDirectory() as tmp:
        npcs_dir = os.path.join(tmp, "game_data", "npcs")
        os.makedirs(npcs_dir)
        manager = NpcCLIManager(tmp)
        manager.list_major_npcs()

    print("[PASS] List Major NPCs - Empty")


def test_list_major_npcs_populated():
    """List command shows a table row for each major NPC."""
    print("\n[TEST] List Major NPCs - Populated")

    with tempfile.TemporaryDirectory() as tmp:
        npcs_dir = os.path.join(tmp, "game_data", "npcs")
        os.makedirs(npcs_dir)
        _write_major_npc(npcs_dir, "major_villain_a.json", "Villain A")
        _write_major_npc(npcs_dir, "major_villain_b.json", "Villain B")

        manager = NpcCLIManager(tmp)
        manager.list_major_npcs()

    print("[PASS] List Major NPCs - Populated")


def test_validate_major_npcs_all_valid():
    """Validate command reports OK when all files are valid."""
    print("\n[TEST] Validate Major NPCs - All Valid")

    with tempfile.TemporaryDirectory() as tmp:
        npcs_dir = os.path.join(tmp, "game_data", "npcs")
        os.makedirs(npcs_dir)
        _write_major_npc(npcs_dir, "major_villain.json", "Arch Villain")

        manager = NpcCLIManager(tmp)
        manager.validate_major_npcs()

    print("[PASS] Validate Major NPCs - All Valid")


def test_validate_major_npcs_with_error():
    """Validate command reports errors for an invalid file."""
    print("\n[TEST] Validate Major NPCs - With Error")

    with tempfile.TemporaryDirectory() as tmp:
        npcs_dir = os.path.join(tmp, "game_data", "npcs")
        os.makedirs(npcs_dir)

        # Write a minimal broken major NPC (missing required fields)
        broken = {"profile_type": "major", "faction": "bbeg", "name": "Broken"}
        filepath = os.path.join(npcs_dir, "major_broken.json")
        Path(filepath).write_text(json.dumps(broken), encoding="utf-8")

        manager = NpcCLIManager(tmp)
        manager.validate_major_npcs()

    print("[PASS] Validate Major NPCs - With Error")


def test_view_major_npc_selection():
    """View command shows details when the user selects a valid NPC."""
    print("\n[TEST] View Major NPC - Selection")

    with tempfile.TemporaryDirectory() as tmp:
        npcs_dir = os.path.join(tmp, "game_data", "npcs")
        os.makedirs(npcs_dir)
        _write_major_npc(npcs_dir, "major_villain.json", "Arch Villain")

        manager = NpcCLIManager(tmp)
        # Simulate user selecting option 1
        with patch("builtins.input", return_value="1"):
            manager.view_major_npc()

    print("[PASS] View Major NPC - Selection")


def test_view_major_npc_back():
    """View command returns without error when user selects 0 (back)."""
    print("\n[TEST] View Major NPC - Back")

    with tempfile.TemporaryDirectory() as tmp:
        npcs_dir = os.path.join(tmp, "game_data", "npcs")
        os.makedirs(npcs_dir)
        _write_major_npc(npcs_dir, "major_villain.json", "Arch Villain")

        manager = NpcCLIManager(tmp)
        with patch("builtins.input", return_value="0"):
            manager.view_major_npc()

    print("[PASS] View Major NPC - Back")


def run_all_tests():
    """Run all CLI NPC manager tests."""
    print("=" * 70)
    print("CLI NPC MANAGER TESTS")
    print("=" * 70)

    test_list_major_npcs_empty()
    test_list_major_npcs_populated()
    test_validate_major_npcs_all_valid()
    test_validate_major_npcs_with_error()
    test_view_major_npc_selection()
    test_view_major_npc_back()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL CLI NPC MANAGER TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
