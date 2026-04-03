"""Tests for ArcStorage - persistence and retrieval of character arc data."""

import os
import tempfile

from tests import test_helpers

ArcStorage = test_helpers.safe_from_import(
    "src.character_arc.arc_storage",
    "ArcStorage",
)
CharacterArc = test_helpers.safe_from_import(
    "src.character_arc.arc_data",
    "CharacterArc",
)
ArcDataPoint = test_helpers.safe_from_import(
    "src.character_arc.arc_data",
    "ArcDataPoint",
)


def _make_storage(campaign_name="Test_Campaign"):
    """Helper: create an ArcStorage backed by a temp directory."""
    tmp_dir = tempfile.mkdtemp()
    storage = ArcStorage(campaign_name=campaign_name, workspace_path=tmp_dir)
    return storage, tmp_dir


def test_storage_create_and_get_arc():
    """Test creating and retrieving a character arc."""
    print("\n[TEST] ArcStorage create and get arc")

    storage, _tmp = _make_storage()
    arc = storage.create_arc("Elara")

    assert arc.character_name == "Elara"
    assert arc.campaign_name == "Test_Campaign"

    retrieved = storage.get_arc("Elara")
    assert retrieved is not None
    assert retrieved.character_name == "Elara"
    print("  [OK] Arc created and retrieved")
    print("[PASS] ArcStorage create and get arc")


def test_storage_get_arc_case_insensitive():
    """Test that arc lookup is case-insensitive."""
    print("\n[TEST] ArcStorage get_arc case insensitive")

    storage, _tmp = _make_storage()
    storage.create_arc("Elara")

    assert storage.get_arc("elara") is not None
    assert storage.get_arc("ELARA") is not None
    assert storage.get_arc("Elara") is not None
    print("  [OK] Case-insensitive lookup works")
    print("[PASS] ArcStorage get_arc case insensitive")


def test_storage_get_arc_missing_returns_none():
    """Test that a missing arc returns None."""
    print("\n[TEST] ArcStorage get_arc missing")

    storage, _tmp = _make_storage()
    result = storage.get_arc("NonExistent")
    assert result is None
    print("  [OK] Missing arc returns None")
    print("[PASS] ArcStorage get_arc missing")


def test_storage_save_arc_persists_to_disk():
    """Test that saving an arc writes a JSON file."""
    print("\n[TEST] ArcStorage save_arc persists to disk")

    storage, tmp_dir = _make_storage()
    storage.create_arc("Elara")

    arc_file = os.path.join(
        tmp_dir, "game_data", "campaigns", "Test_Campaign", "arcs", "elara_arc.json"
    )
    assert os.path.exists(arc_file), f"Expected arc file at {arc_file}"
    print("  [OK] Arc file written to disk")
    print("[PASS] ArcStorage save_arc persists to disk")


def test_storage_add_data_point():
    """Test adding a data point to a character's arc."""
    print("\n[TEST] ArcStorage add_data_point")

    storage, _tmp = _make_storage()
    storage.create_arc("Elara")

    data_point = ArcDataPoint(
        story_file="story_001.md",
        session_id="001",
        timestamp="2026-01-01T00:00:00",
        metric_values={"confidence": 5},
        observations=["Elara grew bolder"],
        key_events=["Defeated the troll"],
    )
    storage.add_data_point("Elara", data_point)

    arc = storage.get_arc("Elara")
    assert arc is not None
    assert len(arc.data_points) == 1
    assert arc.data_points[0].session_id == "001"
    assert arc.data_points[0].metric_values["confidence"] == 5
    print("  [OK] Data point added and persisted")
    print("[PASS] ArcStorage add_data_point")


def test_storage_add_data_point_creates_arc_if_missing():
    """Test that add_data_point auto-creates the arc when absent."""
    print("\n[TEST] ArcStorage add_data_point auto-creates arc")

    storage, _tmp = _make_storage()

    data_point = ArcDataPoint(
        story_file="story_001.md",
        session_id="001",
        timestamp="2026-01-01T00:00:00",
    )
    storage.add_data_point("NewCharacter", data_point)

    arc = storage.get_arc("NewCharacter")
    assert arc is not None
    assert len(arc.data_points) == 1
    print("  [OK] Arc auto-created for new character")
    print("[PASS] ArcStorage add_data_point auto-creates arc")


def test_storage_get_all_arcs():
    """Test retrieving all arcs for a campaign."""
    print("\n[TEST] ArcStorage get_all_arcs")

    storage, _tmp = _make_storage()
    storage.create_arc("Elara")
    storage.create_arc("Theron")
    storage.create_arc("Vex")

    arcs = storage.get_all_arcs()
    names = {arc.character_name.lower() for arc in arcs}
    assert "elara" in names
    assert "theron" in names
    assert "vex" in names
    print(f"  [OK] {len(arcs)} arcs returned")
    print("[PASS] ArcStorage get_all_arcs")


def test_storage_get_all_arcs_empty():
    """Test get_all_arcs on an empty campaign."""
    print("\n[TEST] ArcStorage get_all_arcs empty")

    storage, _tmp = _make_storage()
    arcs = storage.get_all_arcs()
    assert arcs == []
    print("  [OK] Empty list returned for new campaign")
    print("[PASS] ArcStorage get_all_arcs empty")


def test_storage_delete_arc():
    """Test deleting a character arc."""
    print("\n[TEST] ArcStorage delete_arc")

    storage, _tmp = _make_storage()
    storage.create_arc("Elara")

    deleted = storage.delete_arc("Elara")
    assert deleted is True
    assert storage.get_arc("Elara") is None
    print("  [OK] Arc deleted successfully")
    print("[PASS] ArcStorage delete_arc")


def test_storage_delete_arc_missing_returns_false():
    """Test that deleting a non-existent arc returns False."""
    print("\n[TEST] ArcStorage delete_arc missing")

    storage, _tmp = _make_storage()
    result = storage.delete_arc("Ghost")
    assert result is False
    print("  [OK] False returned for missing arc")
    print("[PASS] ArcStorage delete_arc missing")


def test_storage_serialization_roundtrip():
    """Test that arc data survives a save/reload cycle."""
    print("\n[TEST] ArcStorage serialization roundtrip")

    storage, tmp_dir = _make_storage()
    arc = storage.create_arc("Elara", baseline={"level": 3})
    arc.goals.append({"description": "Defeat the lich", "status": "active", "progress": 20})
    arc.state.summary = "Growing in power."
    storage.save_arc(arc)

    storage2 = ArcStorage(campaign_name="Test_Campaign", workspace_path=tmp_dir)
    reloaded = storage2.get_arc("Elara")

    assert reloaded is not None
    assert reloaded.baseline == {"level": 3}
    assert len(reloaded.goals) == 1
    assert reloaded.goals[0]["description"] == "Defeat the lich"
    assert reloaded.state.summary == "Growing in power."
    print("  [OK] Roundtrip serialization preserves all fields")
    print("[PASS] ArcStorage serialization roundtrip")


if __name__ == "__main__":
    test_storage_create_and_get_arc()
    test_storage_get_arc_case_insensitive()
    test_storage_get_arc_missing_returns_none()
    test_storage_save_arc_persists_to_disk()
    test_storage_add_data_point()
    test_storage_add_data_point_creates_arc_if_missing()
    test_storage_get_all_arcs()
    test_storage_get_all_arcs_empty()
    test_storage_delete_arc()
    test_storage_delete_arc_missing_returns_false()
    test_storage_serialization_roundtrip()
    print("\n[ALL TESTS PASSED]")
