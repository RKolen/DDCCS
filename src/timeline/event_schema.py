"""Event schema for timeline tracking."""

import hashlib
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class EventType(Enum):
    """Types of timeline events."""

    COMBAT = "combat"
    SOCIAL = "social"
    EXPLORATION = "exploration"
    DISCOVERY = "discovery"
    QUEST_START = "quest_start"
    QUEST_COMPLETE = "quest_complete"
    CHARACTER_DEATH = "character_death"
    CHARACTER_JOIN = "character_join"
    NPC_INTRO = "npc_intro"
    NPC_DEATH = "npc_death"
    ITEM_GAIN = "item_gain"
    ITEM_LOSS = "item_loss"
    LOCATION_VISIT = "location_visit"
    PLOT_TWIST = "plot_twist"
    RELATIONSHIP_CHANGE = "relationship_change"
    LEVEL_UP = "level_up"
    STORY_MILESTONE = "story_milestone"
    CUSTOM = "custom"


class EventPriority(Enum):
    """Priority levels for events."""

    CRITICAL = "critical"
    IMPORTANT = "important"
    NORMAL = "normal"
    MINOR = "minor"


@dataclass
class EventContext:
    """Temporal, spatial, and participant context for an event."""

    description: str = ""
    in_world_date: Optional[Dict] = None
    real_world_date: Optional[str] = None
    location: str = ""
    region: str = ""
    characters_involved: List[str] = field(default_factory=list)
    npcs_involved: List[str] = field(default_factory=list)


@dataclass
class EventSource:
    """Source tracking for a timeline event."""

    campaign_name: str = ""
    story_file: str = ""
    session_id: str = ""
    story_section: str = ""


@dataclass
class EventLinks:
    """Cross-campaign linking data for an event."""

    linked_events: List[str] = field(default_factory=list)
    parent_event: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    organizations_involved: List[str] = field(default_factory=list)


@dataclass
class EventMeta:
    """Metadata and AI extraction info for an event."""

    priority: EventPriority = EventPriority.NORMAL
    consequences: List[str] = field(default_factory=list)
    foreshadowing: List[str] = field(default_factory=list)
    extraction_confidence: float = 0.0
    manually_verified: bool = False


@dataclass
class TimelineEvent:
    """Represents a single event in the timeline."""

    event_id: str
    title: str
    event_type: EventType
    context: EventContext = field(default_factory=EventContext)
    source: EventSource = field(default_factory=EventSource)
    links: EventLinks = field(default_factory=EventLinks)
    meta: EventMeta = field(default_factory=EventMeta)

    def generate_id(self) -> str:
        """Generate a unique event ID based on content."""
        content = (
            f"{self.title}{self.context.description}{self.source.campaign_name}"
        )
        return f"evt_{hashlib.md5(content.encode()).hexdigest()[:12]}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "event_id": self.event_id,
            "title": self.title,
            "event_type": self.event_type.value,
            # context fields
            "description": self.context.description,
            "in_world_date": self.context.in_world_date,
            "real_world_date": self.context.real_world_date,
            "location": self.context.location,
            "region": self.context.region,
            "characters_involved": self.context.characters_involved,
            "npcs_involved": self.context.npcs_involved,
            # source fields
            "campaign_name": self.source.campaign_name,
            "story_file": self.source.story_file,
            "session_id": self.source.session_id,
            "story_section": self.source.story_section,
            # links fields
            "linked_events": self.links.linked_events,
            "parent_event": self.links.parent_event,
            "tags": self.links.tags,
            "organizations_involved": self.links.organizations_involved,
            # meta fields
            "priority": self.meta.priority.value,
            "consequences": self.meta.consequences,
            "foreshadowing": self.meta.foreshadowing,
            "extraction_confidence": self.meta.extraction_confidence,
            "manually_verified": self.meta.manually_verified,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimelineEvent":
        """Create from dictionary."""
        context = EventContext(
            description=data.get("description", ""),
            in_world_date=data.get("in_world_date"),
            real_world_date=data.get("real_world_date"),
            location=data.get("location", ""),
            region=data.get("region", ""),
            characters_involved=data.get("characters_involved", []),
            npcs_involved=data.get("npcs_involved", []),
        )
        source = EventSource(
            campaign_name=data.get("campaign_name", ""),
            story_file=data.get("story_file", ""),
            session_id=data.get("session_id", ""),
            story_section=data.get("story_section", ""),
        )
        links = EventLinks(
            linked_events=data.get("linked_events", []),
            parent_event=data.get("parent_event"),
            tags=data.get("tags", []),
            organizations_involved=data.get("organizations_involved", []),
        )
        meta = EventMeta(
            priority=EventPriority(data.get("priority", "normal")),
            consequences=data.get("consequences", []),
            foreshadowing=data.get("foreshadowing", []),
            extraction_confidence=data.get("extraction_confidence", 0.0),
            manually_verified=data.get("manually_verified", False),
        )
        return cls(
            event_id=data["event_id"],
            title=data["title"],
            event_type=EventType(data["event_type"]),
            context=context,
            source=source,
            links=links,
            meta=meta,
        )
