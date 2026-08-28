"""Data types for drafting a story arc from what has already been played."""

from dataclasses import dataclass, field
from typing import Any, Dict, List

# How many discovered NPCs are worth offering. Beyond this the model is
# listing every name that was ever spoken rather than the cast that matters.
MAX_DISCOVERED_NPCS = 20


@dataclass
class SessionRecap:
    """One session's recap, as stored on the campaign.

    Attributes:
        story_number: The session's position in the campaign.
        summary: The recap prose for that session.
    """

    story_number: int
    summary: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionRecap":
        """Build a recap from a plain dictionary.

        Args:
            data: Mapping with story_number (or storyNumber) and summary.

        Returns:
            The populated recap, with a story number of 0 when absent.
        """
        raw = data.get("story_number", data.get("storyNumber", 0))
        try:
            number = int(raw)
        except (TypeError, ValueError):
            number = 0
        return cls(story_number=number, summary=str(data.get("summary", "")).strip())


@dataclass
class DiscoveredNpc:
    """An NPC the sessions name, whether or not a character node exists yet.

    The campaign's NPC roster is not the cast: a campaign ported from elsewhere
    has stories full of people nobody has created a node for. Reading the cast
    out of the recaps is what lets the console offer them.

    Attributes:
        name: The NPC's name as the sessions spell it.
        role: One line on who they are, for the stub that may be created.
        known: True when the name matched a character already on record.
    """

    name: str
    role: str = ""
    known: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the NPC for transport.

        Returns:
            A JSON-safe dictionary.
        """
        return {"name": self.name, "role": self.role, "known": self.known}


@dataclass
class ArcRoster:
    """The characters an arc covers.

    Held together rather than as two loose lists: the review screen toggles
    them as one roster, and an arc is only meaningful with both sides.

    Attributes:
        party: Names of the player characters the arc covers.
        npcs: Names of the NPCs the arc covers.
    """

    party: List[str] = field(default_factory=list)
    npcs: List[str] = field(default_factory=list)


@dataclass
class ArcDraft:
    """A proposed story arc, before anyone has agreed to it.

    Nothing here is written to Drupal by the code that produces it: the console
    shows the draft for editing and only an explicit accept creates the arc.

    Level range and target-story count are deliberately absent. Both are
    planning decisions that stay fluid for the life of an arc - a campaign can
    plan twenty-seven stories and write fourteen - so a model reading the past
    has nothing to say about them and would only be guessing.

    Attributes:
        title: The arc's proposed name.
        premise: The full premise, as prose.
        overall_plot: The act spine, one act per line.
        faction: Antagonist faction name, empty when none was identified.
        roster: The party and NPCs the arc covers.
    """

    title: str = ""
    premise: str = ""
    overall_plot: str = ""
    faction: str = ""
    roster: ArcRoster = field(default_factory=ArcRoster)

    def is_usable(self) -> bool:
        """Report whether the draft has enough to be worth showing.

        Returns:
            True when the draft has both a title and a premise.
        """
        return bool(self.title.strip() and self.premise.strip())

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the draft for transport.

        The roster is flattened: the wire format the console reads is flat.

        Returns:
            A JSON-safe dictionary.
        """
        return {
            "title": self.title,
            "premise": self.premise,
            "overall_plot": self.overall_plot,
            "faction": self.faction,
            "party": list(self.roster.party),
            "npcs": list(self.roster.npcs),
        }
