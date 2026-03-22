"""Session notes data structures for D&D session tracking.

Defines the schema for capturing structured session details including
events, plot threads, NPC introductions, and player decisions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class NotePriority(Enum):
    """Priority level for session notes."""

    CRITICAL = "critical"
    IMPORTANT = "important"
    MINOR = "minor"
    FLAVOR = "flavor"


class PlotStatus(Enum):
    """Status of a plot thread."""

    INTRODUCED = "introduced"
    ACTIVE = "active"
    RESOLVED = "resolved"
    ABANDONED = "abandoned"


@dataclass
class PlotThread:
    """A plot thread or story arc tracked across sessions."""

    name: str
    description: str
    status: PlotStatus = PlotStatus.ACTIVE
    introduced_session: Optional[str] = None
    resolved_session: Optional[str] = None
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON storage."""
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "introduced_session": self.introduced_session,
            "resolved_session": self.resolved_session,
            "notes": self.notes,
        }


@dataclass
class SessionEvent:
    """A significant event from a session."""

    title: str
    description: str
    characters_involved: List[str] = field(default_factory=list)
    npcs_involved: List[str] = field(default_factory=list)
    location: Optional[str] = None
    outcome: Optional[str] = None
    priority: NotePriority = NotePriority.IMPORTANT

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON storage."""
        return {
            "title": self.title,
            "description": self.description,
            "characters_involved": self.characters_involved,
            "npcs_involved": self.npcs_involved,
            "location": self.location,
            "outcome": self.outcome,
            "priority": self.priority.value,
        }


@dataclass
class NPCIntroduction:
    """An NPC introduced during a session."""

    name: str
    role: str
    location: str
    first_impression: str
    relationship_to_party: str = "Neutral"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON storage."""
        return {
            "name": self.name,
            "role": self.role,
            "location": self.location,
            "first_impression": self.first_impression,
            "relationship_to_party": self.relationship_to_party,
        }


@dataclass
class PlayerDecision:
    """A significant player decision made during a session."""

    decision: str
    made_by: str
    alternatives_considered: List[str] = field(default_factory=list)
    consequences: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON storage."""
        return {
            "decision": self.decision,
            "made_by": self.made_by,
            "alternatives_considered": self.alternatives_considered,
            "consequences": self.consequences,
        }


@dataclass
class SessionContent:
    """Narrative and play content captured for a session.

    Groups the mutable content fields of a session so that SessionNotes
    stays within Pylint's instance-attribute limit.

    Attributes:
        summary: Brief summary of the session.
        events: Significant events that occurred.
        plot_threads: Plot threads introduced or updated.
        npc_introductions: NPCs encountered for the first time.
        player_decisions: Important decisions made by players.
        roll_results: Legacy roll result data for compatibility.
        dm_notes: Private DM notes not fed into AI context.
    """

    summary: str = ""
    events: List[SessionEvent] = field(default_factory=list)
    plot_threads: List[PlotThread] = field(default_factory=list)
    npc_introductions: List[NPCIntroduction] = field(default_factory=list)
    player_decisions: List[PlayerDecision] = field(default_factory=list)
    roll_results: List[Dict[str, Any]] = field(default_factory=list)
    dm_notes: str = ""


@dataclass
class SessionNotes:
    """Complete session notes for a single session.

    Attributes:
        session_id: Unique identifier for this session (e.g. "001").
        session_date: Date of the session in YYYY-MM-DD format.
        campaign_name: Name of the campaign this session belongs to.
        story_file: Filename of the story file associated with this session.
        content: Narrative content captured during the session.
        created_date: ISO timestamp when the notes were created.
        last_updated: ISO timestamp of the last update.
    """

    session_id: str
    session_date: str
    campaign_name: str
    story_file: Optional[str] = None
    content: SessionContent = field(default_factory=SessionContent)
    created_date: Optional[str] = None
    last_updated: Optional[str] = None

    def __post_init__(self) -> None:
        """Set timestamps on creation."""
        if self.created_date is None:
            self.created_date = datetime.now().isoformat()
        if self.last_updated is None:
            self.last_updated = datetime.now().isoformat()

    # ------------------------------------------------------------------
    # Convenience properties (do not count as instance attributes)
    # ------------------------------------------------------------------

    @property
    def summary(self) -> str:
        """Short summary of the session."""
        return self.content.summary

    @summary.setter
    def summary(self, value: str) -> None:
        """Set the session summary."""
        self.content.summary = value

    @property
    def events(self) -> List[SessionEvent]:
        """Events recorded during the session."""
        return self.content.events

    @property
    def plot_threads(self) -> List[PlotThread]:
        """Plot threads tracked in the session."""
        return self.content.plot_threads

    @property
    def npc_introductions(self) -> List[NPCIntroduction]:
        """NPCs introduced in the session."""
        return self.content.npc_introductions

    @property
    def player_decisions(self) -> List[PlayerDecision]:
        """Player decisions recorded in the session."""
        return self.content.player_decisions

    @property
    def roll_results(self) -> List[Dict[str, Any]]:
        """Legacy roll results list."""
        return self.content.roll_results

    @property
    def dm_notes(self) -> str:
        """Private DM notes."""
        return self.content.dm_notes

    @dm_notes.setter
    def dm_notes(self, value: str) -> None:
        """Set DM notes."""
        self.content.dm_notes = value

    # ------------------------------------------------------------------
    # Mutation helpers
    # ------------------------------------------------------------------

    def add_event(
        self,
        title: str,
        description: str,
        characters: Optional[List[str]] = None,
        priority: NotePriority = NotePriority.IMPORTANT,
    ) -> SessionEvent:
        """Add a significant event to the session notes.

        For events that also involve NPCs or a specific location, set those
        fields directly on the returned ``SessionEvent`` object::

            event = notes.add_event("Ambush", "Goblins attacked.")
            event.npcs_involved = ["Goblin Chief"]
            event.location = "Darkwood Road"

        Args:
            title: Short title for the event.
            description: Detailed description of the event.
            characters: Character names involved.
            priority: Importance level for context retrieval.

        Returns:
            The newly created and appended SessionEvent.
        """
        event = SessionEvent(
            title=title,
            description=description,
            characters_involved=characters or [],
            priority=priority,
        )
        self.content.events.append(event)
        self.last_updated = datetime.now().isoformat()
        return event

    def add_plot_thread(
        self,
        name: str,
        description: str,
        status: PlotStatus = PlotStatus.INTRODUCED,
    ) -> None:
        """Add or update a plot thread.

        If a thread with the same name already exists, appends a note
        and updates the status.  Otherwise creates a new one.

        Args:
            name: Unique name for the plot thread.
            description: Description of the thread or new note text.
            status: Current status of the thread.
        """
        for thread in self.content.plot_threads:
            if thread.name == name:
                thread.notes.append(description)
                thread.status = status
                return

        thread = PlotThread(
            name=name,
            description=description,
            status=status,
            introduced_session=self.session_id,
        )
        self.content.plot_threads.append(thread)

    def resolve_plot_thread(self, name: str, resolution: str) -> None:
        """Mark a plot thread as resolved.

        Args:
            name: Name of the thread to resolve.
            resolution: Description of how it was resolved.
        """
        for thread in self.content.plot_threads:
            if thread.name == name:
                thread.status = PlotStatus.RESOLVED
                thread.resolved_session = self.session_id
                thread.notes.append(f"Resolved: {resolution}")
                return

    def add_npc_introduction(
        self,
        name: str,
        role: str,
        location: str,
        impression: str,
    ) -> NPCIntroduction:
        """Record an NPC introduction.

        The relationship to party defaults to "Neutral".  To override::

            npc = notes.add_npc_introduction("Elara", "Blacksmith", "Rivendell", "Gruff")
            npc.relationship_to_party = "Friendly"

        Args:
            name: The NPC's name.
            role: Their role in the story.
            location: Where they were encountered.
            impression: First impression of the NPC.

        Returns:
            The newly created and appended NPCIntroduction.
        """
        intro = NPCIntroduction(
            name=name,
            role=role,
            location=location,
            first_impression=impression,
        )
        self.content.npc_introductions.append(intro)
        return intro

    def add_player_decision(
        self,
        decision: str,
        made_by: str,
        alternatives: Optional[List[str]] = None,
        consequences: Optional[str] = None,
    ) -> None:
        """Record a significant player decision.

        Args:
            decision: What was decided.
            made_by: Character name who made the decision.
            alternatives: Other options considered.
            consequences: Known or anticipated consequences.
        """
        dec = PlayerDecision(
            decision=decision,
            made_by=made_by,
            alternatives_considered=alternatives or [],
            consequences=consequences,
        )
        self.content.player_decisions.append(dec)

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON storage.

        Returns:
            Dictionary representation of the full session notes.
        """
        return {
            "session_id": self.session_id,
            "session_date": self.session_date,
            "campaign_name": self.campaign_name,
            "story_file": self.story_file,
            "summary": self.content.summary,
            "events": [e.to_dict() for e in self.content.events],
            "plot_threads": [p.to_dict() for p in self.content.plot_threads],
            "npc_introductions": [
                n.to_dict() for n in self.content.npc_introductions
            ],
            "player_decisions": [
                d.to_dict() for d in self.content.player_decisions
            ],
            "roll_results": self.content.roll_results,
            "dm_notes": self.content.dm_notes,
            "created_date": self.created_date,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionNotes":
        """Deserialize from a dictionary (loaded from JSON).

        Args:
            data: Dictionary containing session notes data.

        Returns:
            Populated SessionNotes instance.
        """
        notes = cls(
            session_id=data["session_id"],
            session_date=data["session_date"],
            campaign_name=data["campaign_name"],
            story_file=data.get("story_file"),
            created_date=data.get("created_date"),
            last_updated=data.get("last_updated"),
        )

        notes.content.summary = data.get("summary", "")
        notes.content.roll_results = data.get("roll_results", [])
        notes.content.dm_notes = data.get("dm_notes", "")

        for event_data in data.get("events", []):
            notes.content.events.append(
                SessionEvent(
                    title=event_data["title"],
                    description=event_data["description"],
                    characters_involved=event_data.get("characters_involved", []),
                    npcs_involved=event_data.get("npcs_involved", []),
                    location=event_data.get("location"),
                    outcome=event_data.get("outcome"),
                    priority=NotePriority(event_data.get("priority", "important")),
                )
            )

        for thread_data in data.get("plot_threads", []):
            notes.content.plot_threads.append(
                PlotThread(
                    name=thread_data["name"],
                    description=thread_data["description"],
                    status=PlotStatus(thread_data.get("status", "active")),
                    introduced_session=thread_data.get("introduced_session"),
                    resolved_session=thread_data.get("resolved_session"),
                    notes=thread_data.get("notes", []),
                )
            )

        for npc_data in data.get("npc_introductions", []):
            notes.content.npc_introductions.append(
                NPCIntroduction(
                    name=npc_data["name"],
                    role=npc_data["role"],
                    location=npc_data["location"],
                    first_impression=npc_data["first_impression"],
                    relationship_to_party=npc_data.get(
                        "relationship_to_party", "Neutral"
                    ),
                )
            )

        for dec_data in data.get("player_decisions", []):
            notes.content.player_decisions.append(
                PlayerDecision(
                    decision=dec_data["decision"],
                    made_by=dec_data["made_by"],
                    alternatives_considered=dec_data.get(
                        "alternatives_considered", []
                    ),
                    consequences=dec_data.get("consequences"),
                )
            )

        return notes
