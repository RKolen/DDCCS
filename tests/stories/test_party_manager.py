"""
Party Manager Tests

Tests for party configuration management.
"""

import sys
import os
import tempfile
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from src.stories.party_manager import PartyManager
except ImportError as e:
    print(f"[ERROR] Failed to import required modules: {e}")
    print("[ERROR] Make sure you're running from the tests directory")
    sys.exit(1)


def test_party_manager_initialization():
    """Test PartyManager initialization."""
    print("\n[TEST] PartyManager Initialization")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump({"party_members": ["Theron", "Kael"]}, f)
        temp_path = f.name

    try:
        manager = PartyManager(temp_path)
        assert manager.party_config_path == temp_path
        print("  [OK] PartyManager initialized correctly")
    finally:
        os.unlink(temp_path)

    print("[PASS] PartyManager Initialization")


def test_get_current_party():
    """Test getting current party members."""
    print("\n[TEST] Get Current Party")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump({"party_members": ["Theron", "Kael", "Lyra"]}, f)
        temp_path = f.name

    try:
        manager = PartyManager(temp_path)
        party = manager.get_current_party()

        assert len(party) == 3, "Should have 3 party members"
        assert "Theron" in party, "Theron should be in party"
        assert "Kael" in party, "Kael should be in party"
        assert "Lyra" in party, "Lyra should be in party"
        print("  [OK] Party members retrieved correctly")
    finally:
        os.unlink(temp_path)

    print("[PASS] Get Current Party")


def test_set_current_party():
    """Test setting party members."""
    print("\n[TEST] Set Current Party")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump({"party_members": ["Theron"]}, f)
        temp_path = f.name

    try:
        manager = PartyManager(temp_path)
        new_party = ["Aldric", "Elena", "Marcus"]
        manager.set_current_party(new_party)

        # Verify by reading file
        with open(temp_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
            saved_party = saved_data["party_members"]

        assert len(saved_party) == 3, "Should have 3 party members"
        assert "Aldric" in saved_party, "Aldric should be in party"
        assert "Elena" in saved_party, "Elena should be in party"
        assert "Marcus" in saved_party, "Marcus should be in party"
        print("  [OK] Party members set and saved correctly")
    finally:
        os.unlink(temp_path)

    print("[PASS] Set Current Party")


def test_add_party_member():
    """Test adding a party member."""
    print("\n[TEST] Add Party Member")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump({"party_members": ["Theron", "Kael"]}, f)
        temp_path = f.name

    try:
        manager = PartyManager(temp_path)
        manager.add_party_member("Lyra")

        party = manager.get_current_party()
        assert len(party) == 3, "Should have 3 party members"
        assert "Lyra" in party, "Lyra should be added"
        print("  [OK] Party member added successfully")
    finally:
        os.unlink(temp_path)

    print("[PASS] Add Party Member")


def test_add_existing_party_member():
    """Test adding an existing party member (should warn)."""
    print("\n[TEST] Add Existing Party Member")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump({"party_members": ["Theron", "Kael"]}, f)
        temp_path = f.name

    try:
        manager = PartyManager(temp_path)
        manager.add_party_member("Theron")

        party = manager.get_current_party()
        assert len(party) == 2, "Should still have 2 party members"
        assert party.count("Theron") == 1, "Theron should appear once"
        print("  [OK] Duplicate add prevented")
    finally:
        os.unlink(temp_path)

    print("[PASS] Add Existing Party Member")


def test_remove_party_member():
    """Test removing a party member."""
    print("\n[TEST] Remove Party Member")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump({"party_members": ["Theron", "Kael", "Lyra"]}, f)
        temp_path = f.name

    try:
        manager = PartyManager(temp_path)
        manager.remove_party_member("Kael")

        party = manager.get_current_party()
        assert len(party) == 2, "Should have 2 party members"
        assert "Kael" not in party, "Kael should be removed"
        assert "Theron" in party, "Theron should remain"
        assert "Lyra" in party, "Lyra should remain"
        print("  [OK] Party member removed successfully")
    finally:
        os.unlink(temp_path)

    print("[PASS] Remove Party Member")


def test_remove_nonexistent_party_member():
    """Test removing a non-existent party member (should warn)."""
    print("\n[TEST] Remove Non-existent Party Member")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump({"party_members": ["Theron", "Kael"]}, f)
        temp_path = f.name

    try:
        manager = PartyManager(temp_path)
        manager.remove_party_member("Lyra")

        party = manager.get_current_party()
        assert len(party) == 2, "Should still have 2 party members"
        print("  [OK] Non-existent remove handled")
    finally:
        os.unlink(temp_path)

    print("[PASS] Remove Non-existent Party Member")


def test_empty_party():
    """Test operations with empty party."""
    print("\n[TEST] Empty Party")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump({"party_members": []}, f)
        temp_path = f.name

    try:
        manager = PartyManager(temp_path)
        party = manager.get_current_party()
        assert len(party) == 0, "Party should be empty"

        manager.add_party_member("Theron")
        party = manager.get_current_party()
        assert len(party) == 1, "Should have 1 party member"
        assert "Theron" in party
        print("  [OK] Empty party handled correctly")
    finally:
        os.unlink(temp_path)

    print("[PASS] Empty Party")


def run_all_tests():
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
