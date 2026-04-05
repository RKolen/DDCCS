"""Shared helpers and imports for timeline tests."""

from typing import Any

from tests import test_helpers

EventContext = test_helpers.safe_from_import(
    "src.timeline.event_schema",
    "EventContext",
)
EventMeta = test_helpers.safe_from_import(
    "src.timeline.event_schema",
    "EventMeta",
)
EventPriority = test_helpers.safe_from_import(
    "src.timeline.event_schema",
    "EventPriority",
)
EventSource = test_helpers.safe_from_import(
    "src.timeline.event_schema",
    "EventSource",
)
EventType = test_helpers.safe_from_import(
    "src.timeline.event_schema",
    "EventType",
)
TimelineEvent = test_helpers.safe_from_import(
    "src.timeline.event_schema",
    "TimelineEvent",
)


def make_event(
    event_id: str = "evt_001",
    title: str = "Test Event",
    event_type_val: str = "combat",
    campaign_name: str = "Test_Campaign",
    **kwargs,
) -> Any:
    """Create a TimelineEvent for use in tests.

    Extra kwargs: story_file, characters (list), location, priority_val.
    """
    return TimelineEvent(
        event_id=event_id,
        title=title,
        event_type=EventType(event_type_val),
        context=EventContext(
            description=f"Description for {title}.",
            location=kwargs.get("location", ""),
            characters_involved=kwargs.get("characters") or [],
        ),
        source=EventSource(
            campaign_name=campaign_name,
            story_file=kwargs.get("story_file", "story_001.md"),
        ),
        meta=EventMeta(
            priority=EventPriority(kwargs.get("priority_val", "normal")),
            extraction_confidence=0.8,
        ),
    )
