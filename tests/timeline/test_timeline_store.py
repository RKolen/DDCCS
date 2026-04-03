"""Tests for TimelineStore - event persistence and retrieval."""

import os
import tempfile

from tests import test_helpers
from tests.timeline.timeline_test_helpers import (
    EventPriority,
    EventType,
    make_event,
)

TimelineStore = test_helpers.safe_from_import(
    "src.timeline.timeline_store",
    "TimelineStore",
)
TimelineQuery = test_helpers.safe_from_import(
    "src.timeline.timeline_store",
    "TimelineQuery",
)


def _make_store(campaign_name="Test_Campaign"):
    """Helper: create a TimelineStore backed by a temp directory."""
    tmp_dir = tempfile.mkdtemp()
    store = TimelineStore(campaign_name=campaign_name, workspace_path=tmp_dir)
    return store, tmp_dir


def test_store_add_and_get_event():
    """Test adding an event and retrieving it by ID."""
    print("\n[TEST] TimelineStore add and get event")

    store, _tmp = _make_store()
    event = make_event(event_id="evt_001", title="Cave Discovery")
    store.add_event(event)

    retrieved = store.get_event("evt_001")
    assert retrieved is not None
    assert retrieved.title == "Cave Discovery"
    print("  [OK] Event stored and retrieved")
    print("[PASS] TimelineStore add and get event")


def test_store_get_event_missing_returns_none():
    """Test that get_event returns None for unknown IDs."""
    print("\n[TEST] TimelineStore get_event missing")

    store, _tmp = _make_store()
    result = store.get_event("nonexistent_id")
    assert result is None
    print("  [OK] Missing event returns None")
    print("[PASS] TimelineStore get_event missing")


def test_store_get_campaign_timeline():
    """Test retrieving all events for a campaign."""
    print("\n[TEST] TimelineStore get_campaign_timeline")

    store, _tmp = _make_store("MyCampaign")
    store.add_event(make_event("evt_001", campaign_name="MyCampaign"))
    store.add_event(make_event("evt_002", campaign_name="MyCampaign"))
    store.add_event(make_event("evt_003", campaign_name="OtherCampaign"))

    events = store.get_campaign_timeline("MyCampaign")
    ids = {e.event_id for e in events}
    assert "evt_001" in ids
    assert "evt_002" in ids
    assert "evt_003" not in ids
    print(f"  [OK] Retrieved {len(events)} events for MyCampaign")
    print("[PASS] TimelineStore get_campaign_timeline")


def test_store_get_character_timeline():
    """Test retrieving all events involving a specific character."""
    print("\n[TEST] TimelineStore get_character_timeline")

    store, _tmp = _make_store()
    store.add_event(
        make_event("evt_001", characters=["Elara", "Theron"])
    )
    store.add_event(make_event("evt_002", characters=["Vex"]))
    store.add_event(make_event("evt_003", characters=["Elara"]))

    elara_events = store.get_character_timeline("Elara")
    ids = {e.event_id for e in elara_events}
    assert "evt_001" in ids
    assert "evt_003" in ids
    assert "evt_002" not in ids
    print(f"  [OK] {len(elara_events)} events found for Elara")
    print("[PASS] TimelineStore get_character_timeline")


def test_store_get_character_timeline_case_insensitive():
    """Test that character lookup is case-insensitive."""
    print("\n[TEST] TimelineStore get_character_timeline case insensitive")

    store, _tmp = _make_store()
    store.add_event(make_event("evt_001", characters=["Elara"]))

    assert len(store.get_character_timeline("elara")) == 1
    assert len(store.get_character_timeline("ELARA")) == 1
    print("  [OK] Case-insensitive lookup works")
    print("[PASS] TimelineStore get_character_timeline case insensitive")


def test_store_query_by_campaign():
    """Test TimelineQuery filtering by campaign."""
    print("\n[TEST] TimelineStore query by campaign")

    store, _tmp = _make_store()
    store.add_event(make_event("evt_001", campaign_name="Camp_A"))
    store.add_event(make_event("evt_002", campaign_name="Camp_B"))

    query = TimelineQuery(campaign_name="Camp_A")
    results = store.query(query)
    assert len(results) == 1
    assert results[0].event_id == "evt_001"
    print("  [OK] Query by campaign returns correct events")
    print("[PASS] TimelineStore query by campaign")


def test_store_query_by_event_type():
    """Test TimelineQuery filtering by event type."""
    print("\n[TEST] TimelineStore query by event type")

    store, _tmp = _make_store()
    store.add_event(make_event("evt_001", event_type_val="combat"))
    store.add_event(make_event("evt_002", event_type_val="discovery"))

    query = TimelineQuery(event_types=[EventType.COMBAT])
    results = store.query(query)
    ids = {e.event_id for e in results}
    assert "evt_001" in ids
    assert "evt_002" not in ids
    print("  [OK] Query by event type filters correctly")
    print("[PASS] TimelineStore query by event type")


def test_store_query_by_priority():
    """Test TimelineQuery filtering by priority."""
    print("\n[TEST] TimelineStore query by priority")

    store, _tmp = _make_store()
    store.add_event(make_event("evt_001", priority_val="critical"))
    store.add_event(make_event("evt_002", priority_val="minor"))

    query = TimelineQuery(priority=EventPriority.CRITICAL)
    results = store.query(query)
    ids = {e.event_id for e in results}
    assert "evt_001" in ids
    assert "evt_002" not in ids
    print("  [OK] Query by priority filters correctly")
    print("[PASS] TimelineStore query by priority")


def test_store_link_events():
    """Test creating a bidirectional link between two events."""
    print("\n[TEST] TimelineStore link_events")

    store, _tmp = _make_store()
    store.add_event(make_event("evt_001"))
    store.add_event(make_event("evt_002"))

    result = store.link_events("evt_001", "evt_002")
    assert result is True

    event1 = store.get_event("evt_001")
    event2 = store.get_event("evt_002")
    assert "evt_002" in event1.links.linked_events
    assert "evt_001" in event2.links.linked_events
    print("  [OK] Bidirectional link created")
    print("[PASS] TimelineStore link_events")


def test_store_link_events_missing_returns_false():
    """Test that linking a non-existent event returns False."""
    print("\n[TEST] TimelineStore link_events missing")

    store, _tmp = _make_store()
    store.add_event(make_event("evt_001"))

    result = store.link_events("evt_001", "nonexistent")
    assert result is False
    print("  [OK] False returned for missing event")
    print("[PASS] TimelineStore link_events missing")


def test_store_persistence_to_disk():
    """Test that adding an event creates a timeline.json file."""
    print("\n[TEST] TimelineStore persistence to disk")

    store, tmp_dir = _make_store("SaveCamp")
    store.add_event(make_event("evt_001", campaign_name="SaveCamp"))

    timeline_path = os.path.join(
        tmp_dir, "game_data", "campaigns", "SaveCamp", "timeline.json"
    )
    assert os.path.exists(timeline_path), f"Expected file at {timeline_path}"
    print("  [OK] timeline.json written to disk")
    print("[PASS] TimelineStore persistence to disk")


def test_store_reload_from_disk():
    """Test that events survive a store reload from disk."""
    print("\n[TEST] TimelineStore reload from disk")

    store, tmp_dir = _make_store("ReloadCamp")
    event = make_event(
        "evt_reload",
        title="Persistent Quest",
        campaign_name="ReloadCamp",
        characters=["Elara"],
    )
    store.add_event(event)

    store2 = TimelineStore(campaign_name="ReloadCamp", workspace_path=tmp_dir)
    reloaded = store2.get_event("evt_reload")
    assert reloaded is not None
    assert reloaded.title == "Persistent Quest"
    assert "Elara" in reloaded.context.characters_involved
    print("  [OK] Events survive store reload")
    print("[PASS] TimelineStore reload from disk")


def test_store_get_campaign_names():
    """Test get_campaign_names returns all indexed campaigns."""
    print("\n[TEST] TimelineStore get_campaign_names")

    store, _tmp = _make_store()
    store.add_event(make_event("evt_001", campaign_name="Alpha"))
    store.add_event(make_event("evt_002", campaign_name="Beta"))

    names = store.get_campaign_names()
    assert "Alpha" in names
    assert "Beta" in names
    print(f"  [OK] Campaigns found: {names}")
    print("[PASS] TimelineStore get_campaign_names")


if __name__ == "__main__":
    test_store_add_and_get_event()
    test_store_get_event_missing_returns_none()
    test_store_get_campaign_timeline()
    test_store_get_character_timeline()
    test_store_get_character_timeline_case_insensitive()
    test_store_query_by_campaign()
    test_store_query_by_event_type()
    test_store_query_by_priority()
    test_store_link_events()
    test_store_link_events_missing_returns_false()
    test_store_persistence_to_disk()
    test_store_reload_from_disk()
    test_store_get_campaign_names()
    print("\n[ALL TESTS PASSED]")
