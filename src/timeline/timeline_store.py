"""Storage and retrieval of timeline events."""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from src.timeline.event_schema import EventPriority, EventType, TimelineEvent
from src.utils.file_io import load_json_file, save_json_file
from src.utils.path_utils import get_game_data_path


@dataclass
class TimelineQuery:
    """Query parameters for timeline search."""

    campaign_name: Optional[str] = None
    event_types: Optional[List[EventType]] = None
    characters: Optional[List[str]] = None
    locations: Optional[List[str]] = None
    priority: Optional[EventPriority] = None
    tags: Optional[List[str]] = None
    include_linked: bool = True


class TimelineStore:
    """Manages storage and retrieval of timeline events."""

    _TIMELINE_FILE = "timeline.json"

    def __init__(
        self,
        campaign_name: Optional[str] = None,
        workspace_path: Optional[str] = None,
    ):
        """Initialize timeline store.

        Args:
            campaign_name: Optional campaign to focus on.
            workspace_path: Optional workspace root for testing.
        """
        self.campaign_name = campaign_name
        self.workspace_path = workspace_path
        self._events: Dict[str, TimelineEvent] = {}
        self._campaign_index: Dict[str, List[str]] = {}
        self._character_index: Dict[str, List[str]] = {}
        self._location_index: Dict[str, List[str]] = {}
        self._load_all_timelines()

    def _campaigns_dir(self) -> str:
        """Return the path to the campaigns directory."""
        return os.path.join(
            get_game_data_path(self.workspace_path), "campaigns"
        )

    def _timeline_path(self, campaign: str) -> str:
        """Return the timeline.json path for a campaign."""
        return os.path.join(
            self._campaigns_dir(), campaign, self._TIMELINE_FILE
        )

    def _load_all_timelines(self) -> None:
        """Load timeline data from all campaigns (or only the selected one)."""
        campaigns_dir = self._campaigns_dir()
        if not os.path.isdir(campaigns_dir):
            return

        if self.campaign_name:
            self._load_campaign_timeline(self.campaign_name)
            return

        for entry in os.listdir(campaigns_dir):
            if os.path.isdir(os.path.join(campaigns_dir, entry)):
                self._load_campaign_timeline(entry)

    def _load_campaign_timeline(self, campaign: str) -> None:
        """Load timeline for a specific campaign."""
        timeline_path = self._timeline_path(campaign)
        if not os.path.exists(timeline_path):
            return

        data = load_json_file(timeline_path)
        if not data:
            return

        for event_data in data.get("events", []):
            try:
                event = TimelineEvent.from_dict(event_data)
                self._add_event_to_indexes(event)
            except (KeyError, ValueError):
                pass

    def _add_event_to_indexes(self, event: TimelineEvent) -> None:
        """Add event to all internal indexes."""
        self._events[event.event_id] = event

        campaign = event.source.campaign_name
        if campaign:
            self._campaign_index.setdefault(campaign, [])
            self._campaign_index[campaign].append(event.event_id)

        for char in event.context.characters_involved:
            key = char.lower()
            self._character_index.setdefault(key, [])
            self._character_index[key].append(event.event_id)

        loc = event.context.location
        if loc:
            self._location_index.setdefault(loc.lower(), [])
            self._location_index[loc.lower()].append(event.event_id)

    def add_event(self, event: TimelineEvent) -> None:
        """Add a new event to the store and persist it."""
        self._add_event_to_indexes(event)
        self._save_campaign_timeline(event.source.campaign_name)

    def _save_campaign_timeline(self, campaign: str) -> None:
        """Persist the timeline for a campaign."""
        if not campaign:
            return

        event_ids = self._campaign_index.get(campaign, [])
        events = [
            self._events[eid].to_dict()
            for eid in event_ids
            if eid in self._events
        ]

        data = {
            "campaign_name": campaign,
            "last_updated": datetime.now().isoformat(),
            "events": events,
        }
        save_json_file(self._timeline_path(campaign), data)

    def get_event(self, event_id: str) -> Optional[TimelineEvent]:
        """Get an event by ID."""
        return self._events.get(event_id)

    def get_campaign_names(self) -> List[str]:
        """Return all campaign names that have events in the store."""
        return list(self._campaign_index.keys())

    def query(self, timeline_query: TimelineQuery) -> List[TimelineEvent]:
        """Query events based on criteria, sorted by event_id."""
        results = [
            event
            for event in self._events.values()
            if self._event_matches_query(event, timeline_query)
        ]
        return sorted(results, key=lambda e: e.event_id)

    def _event_matches_query(
        self, event: TimelineEvent, timeline_query: TimelineQuery
    ) -> bool:
        """Return True if the event satisfies all query filters."""
        if timeline_query.campaign_name:
            if event.source.campaign_name != timeline_query.campaign_name:
                return False
        if timeline_query.event_types:
            if event.event_type not in timeline_query.event_types:
                return False
        return self._check_extra_filters(event, timeline_query)

    def _check_extra_filters(
        self, event: TimelineEvent, timeline_query: TimelineQuery
    ) -> bool:
        """Check character, location, priority, and tag filters."""
        if timeline_query.characters:
            event_chars = {c.lower() for c in event.context.characters_involved}
            query_chars = {c.lower() for c in timeline_query.characters}
            if not event_chars.intersection(query_chars):
                return False
        if timeline_query.locations:
            locs = {loc.lower() for loc in timeline_query.locations}
            if event.context.location.lower() not in locs:
                return False
        if timeline_query.priority and event.meta.priority != timeline_query.priority:
            return False
        if timeline_query.tags:
            event_tags = {t.lower() for t in event.links.tags}
            query_tags = {t.lower() for t in timeline_query.tags}
            if not event_tags.intersection(query_tags):
                return False
        return True

    def get_campaign_timeline(self, campaign: str) -> List[TimelineEvent]:
        """Get all events for a campaign."""
        event_ids = self._campaign_index.get(campaign, [])
        return [self._events[eid] for eid in event_ids if eid in self._events]

    def get_character_timeline(self, character_name: str) -> List[TimelineEvent]:
        """Get all events involving a character."""
        event_ids = self._character_index.get(character_name.lower(), [])
        return [self._events[eid] for eid in event_ids if eid in self._events]

    def get_location_timeline(self, location: str) -> List[TimelineEvent]:
        """Get all events at a location."""
        event_ids = self._location_index.get(location.lower(), [])
        return [self._events[eid] for eid in event_ids if eid in self._events]

    def link_events(self, event_id_1: str, event_id_2: str) -> bool:
        """Create a bidirectional link between two events."""
        event1 = self._events.get(event_id_1)
        event2 = self._events.get(event_id_2)
        if not event1 or not event2:
            return False

        if event_id_2 not in event1.links.linked_events:
            event1.links.linked_events.append(event_id_2)
        if event_id_1 not in event2.links.linked_events:
            event2.links.linked_events.append(event_id_1)

        self._save_campaign_timeline(event1.source.campaign_name)
        self._save_campaign_timeline(event2.source.campaign_name)
        return True

    def get_linked_events(self, event_id: str) -> List[TimelineEvent]:
        """Get all events linked to a specific event."""
        event = self._events.get(event_id)
        if not event:
            return []
        return [
            self._events[eid]
            for eid in event.links.linked_events
            if eid in self._events
        ]
