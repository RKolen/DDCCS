"""Tests for event schema data structures."""

from tests import test_helpers
from tests.timeline.timeline_test_helpers import (
    EventContext,
    EventMeta,
    EventPriority,
    EventSource,
    EventType,
    TimelineEvent,
    make_event,
)

EventLinks = test_helpers.safe_from_import(
    "src.timeline.event_schema",
    "EventLinks",
)


def test_event_type_values():
    """Test that EventType enum has the expected values."""
    print("\n[TEST] EventType enum values")

    assert EventType.COMBAT.value == "combat"
    assert EventType.SOCIAL.value == "social"
    assert EventType.DISCOVERY.value == "discovery"
    assert EventType.QUEST_START.value == "quest_start"
    assert EventType.QUEST_COMPLETE.value == "quest_complete"
    assert EventType.CHARACTER_DEATH.value == "character_death"
    assert EventType.NPC_INTRO.value == "npc_intro"
    assert EventType.LOCATION_VISIT.value == "location_visit"
    assert EventType.PLOT_TWIST.value == "plot_twist"
    assert EventType.CUSTOM.value == "custom"
    print("  [OK] All EventType values correct")
    print("[PASS] EventType enum values")


def test_event_priority_values():
    """Test that EventPriority enum has the expected values."""
    print("\n[TEST] EventPriority enum values")

    assert EventPriority.CRITICAL.value == "critical"
    assert EventPriority.IMPORTANT.value == "important"
    assert EventPriority.NORMAL.value == "normal"
    assert EventPriority.MINOR.value == "minor"
    print("  [OK] All EventPriority values correct")
    print("[PASS] EventPriority enum values")


def test_timeline_event_defaults():
    """Test that nested dataclass defaults work correctly."""
    print("\n[TEST] TimelineEvent nested dataclass defaults")

    event = TimelineEvent(
        event_id="evt_001",
        title="Test",
        event_type=EventType.COMBAT,
    )

    assert event.context.description == ""
    assert event.context.characters_involved == []
    assert event.source.campaign_name == ""
    assert event.links.linked_events == []
    assert event.meta.priority == EventPriority.NORMAL
    assert event.meta.extraction_confidence == 0.0
    print("  [OK] All defaults are correct")
    print("[PASS] TimelineEvent nested dataclass defaults")


def test_generate_id_is_stable():
    """Test that generate_id produces consistent results."""
    print("\n[TEST] TimelineEvent.generate_id stability")

    event = TimelineEvent(
        event_id="",
        title="Dragon Appears",
        event_type=EventType.COMBAT,
        context=EventContext(description="A dragon attacks."),
        source=EventSource(campaign_name="TestCamp"),
    )
    id1 = event.generate_id()
    id2 = event.generate_id()

    assert id1 == id2, "generate_id must be deterministic"
    assert id1.startswith("evt_"), "ID should start with 'evt_'"
    assert len(id1) == 16, f"Expected length 16, got {len(id1)}"
    print(f"  [OK] Stable ID: {id1}")
    print("[PASS] TimelineEvent.generate_id stability")


def test_generate_id_differs_for_different_events():
    """Test that different events produce different IDs."""
    print("\n[TEST] TimelineEvent.generate_id uniqueness")

    event1 = TimelineEvent(
        event_id="",
        title="Combat A",
        event_type=EventType.COMBAT,
        context=EventContext(description="First fight."),
        source=EventSource(campaign_name="Camp1"),
    )
    event2 = TimelineEvent(
        event_id="",
        title="Combat B",
        event_type=EventType.COMBAT,
        context=EventContext(description="Second fight."),
        source=EventSource(campaign_name="Camp1"),
    )

    assert event1.generate_id() != event2.generate_id()
    print("  [OK] Different events produce different IDs")
    print("[PASS] TimelineEvent.generate_id uniqueness")


def test_to_dict_contains_all_fields():
    """Test that to_dict produces a flat dict with all expected keys."""
    print("\n[TEST] TimelineEvent.to_dict")

    event = make_event(
        event_id="evt_abc",
        title="Quest Start",
        event_type_val="quest_start",
        campaign_name="MyCarpaign",
        characters=["Elara", "Theron"],
        location="Forest",
        priority_val="important",
    )
    data = event.to_dict()

    assert data["event_id"] == "evt_abc"
    assert data["title"] == "Quest Start"
    assert data["event_type"] == "quest_start"
    assert data["campaign_name"] == "MyCarpaign"
    assert data["characters_involved"] == ["Elara", "Theron"]
    assert data["location"] == "Forest"
    assert data["priority"] == "important"
    assert "description" in data
    assert "linked_events" in data
    print("  [OK] to_dict contains expected fields")
    print("[PASS] TimelineEvent.to_dict")


def test_serialization_roundtrip():
    """Test that to_dict / from_dict round-trips without data loss."""
    print("\n[TEST] TimelineEvent serialization roundtrip")

    original = TimelineEvent(
        event_id="evt_round",
        title="Roundtrip Event",
        event_type=EventType.DISCOVERY,
        context=EventContext(
            description="They discovered a cave.",
            location="Misty Mountains",
            characters_involved=["Elara"],
        ),
        source=EventSource(
            campaign_name="Test_Campaign",
            story_file="story_003.md",
            session_id="003",
        ),
        meta=EventMeta(
            priority=EventPriority.CRITICAL,
            extraction_confidence=0.95,
            manually_verified=True,
        ),
    )

    data = original.to_dict()
    restored = TimelineEvent.from_dict(data)

    assert restored.event_id == original.event_id
    assert restored.title == original.title
    assert restored.event_type == original.event_type
    assert restored.context.description == original.context.description
    assert restored.context.location == original.context.location
    assert restored.context.characters_involved == original.context.characters_involved
    assert restored.source.campaign_name == original.source.campaign_name
    assert restored.source.story_file == original.source.story_file
    assert restored.meta.priority == original.meta.priority
    assert restored.meta.extraction_confidence == original.meta.extraction_confidence
    assert restored.meta.manually_verified == original.meta.manually_verified
    print("  [OK] All fields survive roundtrip")
    print("[PASS] TimelineEvent serialization roundtrip")


def test_event_links_defaults():
    """Test EventLinks dataclass default values."""
    print("\n[TEST] EventLinks defaults")

    links = EventLinks()
    assert links.linked_events == []
    assert links.parent_event is None
    assert links.tags == []
    assert links.organizations_involved == []
    print("  [OK] EventLinks defaults are correct")
    print("[PASS] EventLinks defaults")


if __name__ == "__main__":
    test_event_type_values()
    test_event_priority_values()
    test_timeline_event_defaults()
    test_generate_id_is_stable()
    test_generate_id_differs_for_different_events()
    test_to_dict_contains_all_fields()
    test_serialization_roundtrip()
    test_event_links_defaults()
    print("\n[ALL TESTS PASSED]")
