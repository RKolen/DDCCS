"""Display and export timeline views."""

from datetime import datetime
from typing import List, Optional

from src.timeline.event_schema import EventPriority, EventType, TimelineEvent
from src.timeline.timeline_store import TimelineQuery, TimelineStore
from src.utils.cli_utils import print_section_header
from src.utils.terminal_display import print_info

_PRIORITY_MARKERS = {
    EventPriority.CRITICAL: "[!]",
    EventPriority.IMPORTANT: "[*]",
    EventPriority.NORMAL: "[ ]",
    EventPriority.MINOR: "[-]",
}


class TimelineDisplay:
    """Display timeline views in the terminal and export to files."""

    def __init__(self, store: Optional[TimelineStore] = None):
        """Initialize display with a timeline store."""
        self.store = store or TimelineStore()

    def display_campaign_timeline(
        self,
        campaign_name: str,
        event_types: Optional[List[EventType]] = None,
    ) -> None:
        """Display all events for a campaign, optionally filtered by type."""
        timeline_query = TimelineQuery(
            campaign_name=campaign_name,
            event_types=event_types,
        )
        events = self.store.query(timeline_query)

        print_section_header(f"Timeline: {campaign_name}")

        if not events:
            print_info("No events found for this campaign.")
            return

        for event in events:
            self._display_event(event)

    def display_character_timeline(self, character_name: str) -> None:
        """Display all events involving a character, grouped by campaign."""
        events = self.store.get_character_timeline(character_name)

        print_section_header(f"Timeline: {character_name}")

        if not events:
            print_info(f"No events found for {character_name}.")
            return

        by_campaign: dict = {}
        for event in events:
            campaign = event.source.campaign_name or "Unknown"
            by_campaign.setdefault(campaign, [])
            by_campaign[campaign].append(event)

        for campaign, campaign_events in by_campaign.items():
            print(f"\n[{campaign}]")
            for event in campaign_events:
                self._display_event(event, show_campaign=False)

    def _display_event(
        self, event: TimelineEvent, show_campaign: bool = True
    ) -> None:
        """Display a single event summary."""
        marker = _PRIORITY_MARKERS.get(event.meta.priority, "[ ]")

        date_str = ""
        if event.context.in_world_date:
            date_info = event.context.in_world_date
            day = date_info.get("day", "?")
            month = date_info.get("month", "?")
            year = date_info.get("year", "?")
            date_str = f"{day} {month}, {year}"

        parts = [marker, event.title]
        if date_str:
            parts.append(f"({date_str})")
        if show_campaign and event.source.campaign_name:
            parts.append(f"[{event.source.campaign_name}]")
        print(" ".join(parts))

        high_priority = (EventPriority.CRITICAL, EventPriority.IMPORTANT)
        if event.meta.priority in high_priority and event.context.description:
            desc = event.context.description
            preview = desc[:100] + "..." if len(desc) > 100 else desc
            print(f"    {preview}")

        if event.context.characters_involved:
            chars = event.context.characters_involved
            display = ", ".join(chars[:3])
            if len(chars) > 3:
                display += f" (+{len(chars) - 3} more)"
            print(f"    Characters: {display}")

        if event.context.location:
            print(f"    Location: {event.context.location}")

        if event.links.linked_events:
            print(f"    Linked: {len(event.links.linked_events)} event(s)")

        print()

    def display_event_detail(self, event_id: str) -> None:
        """Display a detailed view of a single event."""
        event = self.store.get_event(event_id)
        if not event:
            print_info(f"Event not found: {event_id}")
            return

        print_section_header(f"Event: {event.title}")
        print(f"Type: {event.event_type.value}")
        print(f"Priority: {event.meta.priority.value}")
        print(f"Campaign: {event.source.campaign_name or 'Unknown'}")

        if event.context.in_world_date:
            print(f"Date: {event.context.in_world_date}")
        if event.context.real_world_date:
            print(f"Real Date: {event.context.real_world_date}")
        if event.context.location:
            print(f"Location: {event.context.location}")

        print(f"\nDescription:\n{event.context.description}")

        if event.context.characters_involved:
            print(f"\nCharacters: {', '.join(event.context.characters_involved)}")
        if event.context.npcs_involved:
            print(f"NPCs: {', '.join(event.context.npcs_involved)}")
        if event.links.tags:
            print(f"Tags: {', '.join(event.links.tags)}")

        if event.links.linked_events:
            print("\nLinked Events:")
            for linked_id in event.links.linked_events:
                linked = self.store.get_event(linked_id)
                if linked:
                    print(f"  - {linked.title} ({linked.source.campaign_name})")

        if event.meta.consequences:
            print("\nConsequences:")
            for cons in event.meta.consequences:
                print(f"  - {cons}")

    def export_timeline_markdown(
        self, campaign_name: str, output_path: str
    ) -> None:
        """Export the campaign timeline to a markdown file."""
        events = self.store.get_campaign_timeline(campaign_name)

        lines = [
            f"# Timeline: {campaign_name}",
            "",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "## Events",
            "",
        ]

        for event in events:
            lines.append(f"### {event.title}")
            lines.append("")
            if event.context.in_world_date:
                lines.append(f"**Date:** {event.context.in_world_date}")
            if event.context.location:
                lines.append(f"**Location:** {event.context.location}")
            lines.append(f"**Type:** {event.event_type.value}")
            lines.append(f"**Priority:** {event.meta.priority.value}")
            lines.append("")
            lines.append(event.context.description)
            lines.append("")
            if event.context.characters_involved:
                chars = ", ".join(event.context.characters_involved)
                lines.append(f"**Characters:** {chars}")
            if event.context.npcs_involved:
                npcs = ", ".join(event.context.npcs_involved)
                lines.append(f"**NPCs:** {npcs}")
            lines.append("")
            lines.append("---")
            lines.append("")

        with open(output_path, "w", encoding="utf-8") as out_file:
            out_file.write("\n".join(lines))
