"""Session notes manager for D&D campaign session tracking.

Handles saving, loading, and querying session notes across all sessions
in a campaign.  Provides context extraction for AI story generation.
"""

import os
from typing import Any, Dict, List, Optional

from src.sessions.session_notes import NotePriority, PlotStatus, SessionNotes
from src.utils.file_io import ensure_directory, load_json_file, save_json_file
from src.utils.path_utils import get_game_data_path
from src.utils.string_utils import get_session_date


class SessionNotesManager:
    """Manages session notes for a single campaign.

    Attributes:
        campaign_name: Name of the campaign.
        workspace_path: Root workspace path.
        campaign_dir: Path to the campaign directory.
        notes_dir: Path to the session_notes subdirectory.
    """

    def __init__(
        self,
        campaign_name: str,
        workspace_path: Optional[str] = None,
    ) -> None:
        """Initialize the manager for a campaign.

        Args:
            campaign_name: Name of the campaign folder.
            workspace_path: Optional workspace root (defaults to cwd-based path).
        """
        self.campaign_name = campaign_name
        self.campaign_dir = os.path.join(
            get_game_data_path(workspace_path), "campaigns", campaign_name
        )
        self.notes_dir = os.path.join(self.campaign_dir, "session_notes")

    def _ensure_notes_dir(self) -> None:
        """Create the notes directory if it does not exist."""
        ensure_directory(self.notes_dir)

    def create_session_notes(
        self,
        session_id: str,
        story_file: Optional[str] = None,
    ) -> SessionNotes:
        """Create a new empty SessionNotes instance for the given session.

        Args:
            session_id: Unique identifier for this session (e.g. "001").
            story_file: Optional filename of the associated story file.

        Returns:
            A new SessionNotes instance (not yet saved to disk).
        """
        return SessionNotes(
            session_id=session_id,
            session_date=get_session_date(),
            campaign_name=self.campaign_name,
            story_file=story_file,
        )

    def save_session_notes(self, notes: SessionNotes) -> str:
        """Save session notes to a JSON file.

        Args:
            notes: SessionNotes instance to persist.

        Returns:
            Path to the saved JSON file.
        """
        self._ensure_notes_dir()
        filename = f"notes_{notes.session_date}_{notes.session_id}.json"
        filepath = os.path.join(self.notes_dir, filename)
        save_json_file(filepath, notes.to_dict())
        return filepath

    def load_session_notes(self, session_id: str) -> Optional[SessionNotes]:
        """Load session notes by session ID.

        Searches for a file matching the pattern
        ``notes_*_<session_id>.json`` in the notes directory.

        Args:
            session_id: Session identifier to look up.

        Returns:
            SessionNotes instance if found, otherwise None.
        """
        if not os.path.isdir(self.notes_dir):
            return None

        for filename in os.listdir(self.notes_dir):
            if filename.endswith(f"_{session_id}.json") and filename.startswith(
                "notes_"
            ):
                filepath = os.path.join(self.notes_dir, filename)
                data = load_json_file(filepath)
                if data:
                    return SessionNotes.from_dict(data)

        return None

    def get_all_session_notes(self) -> List[SessionNotes]:
        """Return all session notes for the campaign, sorted by date and ID.

        Returns:
            List of SessionNotes instances, oldest first.
        """
        notes_list: List[SessionNotes] = []

        if not os.path.isdir(self.notes_dir):
            return notes_list

        for filename in os.listdir(self.notes_dir):
            if not (filename.startswith("notes_") and filename.endswith(".json")):
                continue
            filepath = os.path.join(self.notes_dir, filename)
            data = load_json_file(filepath)
            if data:
                notes_list.append(SessionNotes.from_dict(data))

        return sorted(notes_list, key=lambda n: (n.session_date, n.session_id))

    def get_recent_notes(self, count: int = 3) -> List[SessionNotes]:
        """Return the most recent session notes.

        Args:
            count: Number of most-recent sessions to return.

        Returns:
            List of the most recent SessionNotes instances.
        """
        all_notes = self.get_all_session_notes()
        return all_notes[-count:] if all_notes else []

    def get_active_plot_threads(self) -> List[Dict[str, Any]]:
        """Collect all active (unresolved) plot threads across all sessions.

        Returns:
            List of dicts with keys: name, description, introduced, notes.
        """
        threads: Dict[str, Dict[str, Any]] = {}

        for notes in self.get_all_session_notes():
            for thread in notes.plot_threads:
                if thread.status == PlotStatus.ACTIVE:
                    threads[thread.name] = {
                        "name": thread.name,
                        "description": thread.description,
                        "introduced": thread.introduced_session,
                        "notes": thread.notes,
                    }
                elif thread.status == PlotStatus.RESOLVED:
                    threads.pop(thread.name, None)

        return list(threads.values())

    def get_npc_introductions(self) -> List[Dict[str, Any]]:
        """Return all NPCs introduced across sessions (first occurrence only).

        Returns:
            List of dicts with keys: name, role, location, first_impression,
            relationship, introduced_session.
        """
        npcs: Dict[str, Dict[str, Any]] = {}

        for notes in self.get_all_session_notes():
            for npc in notes.npc_introductions:
                if npc.name not in npcs:
                    npcs[npc.name] = {
                        "name": npc.name,
                        "role": npc.role,
                        "location": npc.location,
                        "first_impression": npc.first_impression,
                        "relationship": npc.relationship_to_party,
                        "introduced_session": notes.session_id,
                    }

        return list(npcs.values())

    def get_campaign_timeline(self) -> List[Dict[str, Any]]:
        """Build a chronological list of all recorded events.

        Returns:
            List of event dicts sorted by date then session ID.
        """
        timeline: List[Dict[str, Any]] = []

        for notes in self.get_all_session_notes():
            for event in notes.events:
                timeline.append(
                    {
                        "date": notes.session_date,
                        "session_id": notes.session_id,
                        "title": event.title,
                        "description": event.description,
                        "characters": event.characters_involved,
                        "npcs": event.npcs_involved,
                        "location": event.location,
                        "priority": event.priority.value,
                    }
                )

        return sorted(timeline, key=lambda e: (e["date"], e["session_id"]))

    def get_context_for_story_generation(self) -> Dict[str, Any]:
        """Build a context dict suitable for injecting into story AI prompts.

        Pulls together recent important events, active plot threads, recently
        introduced NPCs, and player decisions whose consequences are not yet
        defined.

        Returns:
            Dict with keys:
              - recent_events: last 10 important/critical events
              - active_plots: unresolved plot threads
              - recent_npcs: last 5 introduced NPCs
              - pending_decisions: decisions without known consequences
        """
        recent = self.get_recent_notes(3)

        events: List[Dict[str, Any]] = []
        for notes in recent:
            for event in notes.events:
                if event.priority in (NotePriority.CRITICAL, NotePriority.IMPORTANT):
                    events.append(
                        {
                            "session": notes.session_id,
                            "title": event.title,
                            "description": event.description,
                        }
                    )

        pending_decisions: List[Dict[str, Any]] = [
            {
                "decision": dec.decision,
                "made_by": dec.made_by,
                "consequences": dec.consequences,
            }
            for notes in recent
            for dec in notes.player_decisions
            if dec.consequences is None
        ]

        return {
            "recent_events": events[-10:],
            "active_plots": self.get_active_plot_threads(),
            "recent_npcs": self.get_npc_introductions()[-5:],
            "pending_decisions": pending_decisions,
        }

    def export_timeline_markdown(self) -> str:
        """Export the campaign timeline as a Markdown string.

        Returns:
            Markdown-formatted string listing all events grouped by date.
        """
        timeline = self.get_campaign_timeline()

        lines = [
            f"# Campaign Timeline: {self.campaign_name}",
            "",
            "## Events in Chronological Order",
            "",
        ]

        current_date: Optional[str] = None
        for event in timeline:
            if event["date"] != current_date:
                current_date = event["date"]
                lines.append(f"### {current_date}")
                lines.append("")

            lines.append(f"**{event['title']}**")
            lines.append(f"- {event['description']}")
            if event["characters"]:
                lines.append(f"- Characters: {', '.join(event['characters'])}")
            if event["npcs"]:
                lines.append(f"- NPCs: {', '.join(event['npcs'])}")
            lines.append("")

        return "\n".join(lines)
