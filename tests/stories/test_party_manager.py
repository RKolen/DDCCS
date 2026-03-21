"""
Party Manager Tests

Tests for party configuration management.
"""

import os
import json
import tempfile
from typing import List
from src.stories.party_manager import PartyManager
from src.utils.path_utils import get_party_config_path


CAMPAIGN = "TestCampaign"


def _write_party(workspace: str, members: List[str]) -> None:
    """Create the party JSON file for TestCampaign in the given workspace."""
    party_path = get_party_config_path(CAMPAIGN, workspace)
    os.makedirs(os.path.dirname(party_path), exist_ok=True)
    with open(party_path, "w", encoding="utf-8") as party_file:
        json.dump({"party_members": members}, party_file)


def _read_party(workspace: str) -> List[str]:
    """Read party members from the party JSON file for TestCampaign."""
    party_path = get_party_config_path(CAMPAIGN, workspace)
    with open(party_path, "r", encoding="utf-8") as party_file:
        data = json.load(party_file)
    return data.get("party_members", [])


def test_party_manager_initialization():
    """Test PartyManager initialization stores campaign_name and workspace_path."""
    print("\n[TEST] PartyManager Initialization")

    with tempfile.TemporaryDirectory() as tmp:
        manager = PartyManager(CAMPAIGN, tmp)
        assert manager.campaign_name == CAMPAIGN
        assert manager.workspace_path == tmp
        print("  [OK] PartyManager initialized correctly")

    print("[PASS] PartyManager Initialization")


def test_get_current_party():
    """Test getting current party members."""
    print("\n[TEST] Get Current Party")

    with tempfile.TemporaryDirectory() as tmp:
        _write_party(tmp, ["Theron", "Kael", "Lyra"])
        manager = PartyManager(CAMPAIGN, tmp)
        party = manager.get_current_party()

        assert len(party) == 3, "Should have 3 party members"
        assert "Theron" in party, "Theron should be in party"
        assert "Kael" in party, "Kael should be in party"
        assert "Lyra" in party, "Lyra should be in party"
        print("  [OK] Party members retrieved correctly")

    print("[PASS] Get Current Party")


def test_set_current_party():
    """Test setting party members."""
    print("\n[TEST] Set Current Party")

    with tempfile.TemporaryDirectory() as tmp:
        _write_party(tmp, ["Theron"])
        manager = PartyManager(CAMPAIGN, tmp)
        new_party = ["Aldric", "Elena", "Marcus"]
        manager.set_current_party(new_party)

        saved_party = _read_party(tmp)
        assert len(saved_party) == 3, "Should have 3 party members"
        assert "Aldric" in saved_party, "Aldric should be in party"
        assert "Elena" in saved_party, "Elena should be in party"
        assert "Marcus" in saved_party, "Marcus should be in party"
        print("  [OK] Party members set and saved correctly")

    print("[PASS] Set Current Party")


def test_add_party_member():
    """Test adding a party member."""
    print("\n[TEST] Add Party Member")

    with tempfile.TemporaryDirectory() as tmp:
        _write_party(tmp, ["Theron", "Kael"])
        manager = PartyManager(CAMPAIGN, tmp)
        manager.add_party_member("Lyra")

        party = manager.get_current_party()
        assert len(party) == 3, "Should have 3 party members"
        assert "Lyra" in party, "Lyra should be added"
        print("  [OK] Party member added successfully")

    print("[PASS] Add Party Member")


def test_add_existing_party_member():
    """Test adding an existing party member (should not duplicate)."""
    print("\n[TEST] Add Existing Party Member")

    with tempfile.TemporaryDirectory() as tmp:
        _write_party(tmp, ["Theron", "Kael"])
        manager = PartyManager(CAMPAIGN, tmp)
        manager.add_party_member("Theron")

        party = manager.get_current_party()
        assert len(party) == 2, "Should still have 2 party members"
        assert party.count("Theron") == 1, "Theron should appear once"
        print("  [OK] Duplicate add prevented")

    print("[PASS] Add Existing Party Member")


def test_remove_party_member():
    """Test removing a party member."""
    print("\n[TEST] Remove Party Member")

    with tempfile.TemporaryDirectory() as tmp:
        _write_party(tmp, ["Theron", "Kael", "Lyra"])
        manager = PartyManager(CAMPAIGN, tmp)
        manager.remove_party_member("Kael")

        party = manager.get_current_party()
        assert len(party) == 2, "Should have 2 party members"
        assert "Kael" not in party, "Kael should be removed"
        assert "Theron" in party, "Theron should remain"
        assert "Lyra" in party, "Lyra should remain"
        print("  [OK] Party member removed successfully")

    print("[PASS] Remove Party Member")


def test_remove_nonexistent_party_member():
    """Test removing a non-existent party member (should warn, not crash)."""
    print("\n[TEST] Remove Non-existent Party Member")

    with tempfile.TemporaryDirectory() as tmp:
        _write_party(tmp, ["Theron", "Kael"])
        manager = PartyManager(CAMPAIGN, tmp)
        manager.remove_party_member("Lyra")

        party = manager.get_current_party()
        assert len(party) == 2, "Should still have 2 party members"
        print("  [OK] Non-existent remove handled")

    print("[PASS] Remove Non-existent Party Member")


def test_empty_party():
    """Test operations with empty party."""
    print("\n[TEST] Empty Party")

    with tempfile.TemporaryDirectory() as tmp:
        _write_party(tmp, [])
        manager = PartyManager(CAMPAIGN, tmp)
        party = manager.get_current_party()
        assert len(party) == 0, "Party should be empty"

        manager.add_party_member("Theron")
        party = manager.get_current_party()
        assert len(party) == 1, "Should have 1 party member"
        assert "Theron" in party
        print("  [OK] Empty party handled correctly")

    print("[PASS] Empty Party")


def run_all_tests() -> None:
    """Run all party manager tests."""
    print("=" * 70)
    print("PARTY MANAGER TESTS")
    print("=" * 70)

    test_party_manager_initialization()
    test_get_current_party()
    test_set_current_party()
    test_add_party_member()
    test_add_existing_party_member()
    test_remove_party_member()
    test_remove_nonexistent_party_member()
    test_empty_party()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL PARTY MANAGER TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
