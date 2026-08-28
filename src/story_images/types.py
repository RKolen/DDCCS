"""Data types for story-scene illustration."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence


@dataclass
class StoryEvent:
    """One selectable moment extracted from a story.

    ``excerpt`` is the bounded passage the later shot analysis reads, never the
    whole story. ``one_line`` is what the console shows in the picker.
    """

    title: str
    one_line: str
    excerpt: str

    def to_dict(self) -> Dict[str, str]:
        """Serialize for the sidecar response and job result.

        Returns:
            A JSON-ready mapping.
        """
        return {
            "title": self.title,
            "one_line": self.one_line,
            "excerpt": self.excerpt,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StoryEvent":
        """Build from a mapping, ignoring unknown keys.

        Args:
            data: A JSON object with title / one_line / excerpt.

        Returns:
            The event, with missing fields as empty strings.
        """
        return cls(
            title=str(data.get("title", "")).strip(),
            one_line=str(data.get("one_line", "")).strip(),
            excerpt=str(data.get("excerpt", "")).strip(),
        )


@dataclass
class RosterEntry:
    """A campaign character the extractor may match a name against."""

    name: str
    character_id: str = ""
    portrait_url: str = ""
    appearance: str = ""
    is_npc: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for the sidecar request.

        Returns:
            A JSON-ready mapping.
        """
        return {
            "name": self.name,
            "character_id": self.character_id,
            "portrait_url": self.portrait_url,
            "appearance": self.appearance,
            "is_npc": self.is_npc,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RosterEntry":
        """Build from a mapping.

        Args:
            data: A JSON object describing one roster member.

        Returns:
            The roster entry.
        """
        return cls(
            name=str(data.get("name", "")).strip(),
            character_id=str(data.get("character_id", "")).strip(),
            portrait_url=str(data.get("portrait_url", "")).strip(),
            appearance=str(data.get("appearance", "")).strip(),
            is_npc=bool(data.get("is_npc", False)),
        )


@dataclass
class ShotPerson:
    """Someone named in a selected event, matched against the roster or not.

    ``known`` is derived from ``character_id``: a Drupal match always has one.
    """

    name: str
    role: str = ""
    character_id: str = ""
    portrait_url: str = ""
    appearance: str = ""
    is_npc: bool = False
    use_likeness: bool = False

    @property
    def known(self) -> bool:
        """True when this name resolved to a Drupal character."""
        return bool(self.character_id)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for the sidecar response.

        Returns:
            A JSON-ready mapping.
        """
        return {
            "name": self.name,
            "role": self.role,
            "known": self.known,
            "character_id": self.character_id,
            "portrait_url": self.portrait_url,
            "appearance": self.appearance,
            "is_npc": self.is_npc,
            "use_likeness": self.use_likeness,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ShotPerson":
        """Build from a mapping.

        Args:
            data: A JSON object describing one person in the shot.

        Returns:
            The person.
        """
        portrait = str(data.get("portrait_url", "")).strip()
        character_id = str(data.get("character_id", "")).strip()
        likeness = data.get("use_likeness")
        if likeness is None:
            likeness = bool(character_id) and bool(portrait)
        return cls(
            name=str(data.get("name", "")).strip(),
            role=str(data.get("role", "")).strip(),
            character_id=character_id,
            portrait_url=portrait,
            appearance=str(data.get("appearance", "")).strip(),
            is_npc=bool(data.get("is_npc", False)),
            use_likeness=bool(likeness),
        )


@dataclass
class ShotAnalysis:
    """What the selected event looks like as a picture.

    ``people`` is the cast of this shot, not the campaign roster. The operator
    may still uncheck names before the render job runs.
    """

    setting: str = ""
    action: str = ""
    mood: str = ""
    people: List[ShotPerson] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for the sidecar response.

        Returns:
            A JSON-ready mapping.
        """
        return {
            "setting": self.setting,
            "action": self.action,
            "mood": self.mood,
            "people": [person.to_dict() for person in self.people],
        }


def match_roster(
    name: str, roster: Sequence[RosterEntry]
) -> Optional[RosterEntry]:
    """Find a roster member whose name matches, case-insensitively.

    Args:
        name: The name as the story or model wrote it.
        roster: Campaign characters that may appear.

    Returns:
        The matching entry, or None.
    """
    needle = name.strip().lower()
    if not needle:
        return None
    for entry in roster:
        if entry.name.strip().lower() == needle:
            return entry
    return None


def apply_roster(person: ShotPerson, roster: Sequence[RosterEntry]) -> ShotPerson:
    """Fill known / portrait / appearance from the roster when the name matches.

    Args:
        person: A person named in the shot.
        roster: Campaign characters that may appear.

    Returns:
        The same person, with roster fields filled when a match exists.
    """
    entry = match_roster(person.name, roster)
    if entry is None:
        return person
    portrait = person.portrait_url or entry.portrait_url
    return ShotPerson(
        name=entry.name,
        role=person.role,
        character_id=entry.character_id,
        portrait_url=portrait,
        appearance=person.appearance or entry.appearance,
        is_npc=entry.is_npc,
        use_likeness=person.use_likeness or bool(portrait),
    )
