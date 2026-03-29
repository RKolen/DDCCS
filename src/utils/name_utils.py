"""Name formatting utilities for characters and NPCs.

Provides structured name components (first name, last name, nickname, title,
epithet) and helper functions for context-appropriate name display.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from src.utils.validation_helpers import get_type_name


@dataclass
class CharacterName:
    """Structured name components for a character or NPC.

    Supports both legacy monolithic name strings and structured name fields.
    Use :meth:`from_dict` to construct from a JSON data dictionary.
    """

    full_name: str = ""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    nickname: Optional[str] = None
    title: Optional[str] = None
    epithet: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterName":
        """Create a CharacterName from JSON data with fallback parsing.

        Uses structured fields when present; otherwise parses the legacy
        ``name`` string into components.

        Args:
            data: Character or NPC JSON dictionary.

        Returns:
            Populated CharacterName instance.
        """
        full_name: str = data.get("name", "")

        if "first_name" in data or "last_name" in data:
            return cls(
                full_name=full_name,
                first_name=data.get("first_name"),
                last_name=data.get("last_name"),
                nickname=data.get("nickname"),
                title=data.get("title"),
                epithet=data.get("epithet"),
            )

        first, last, epithet = _parse_full_name(full_name)
        return cls(
            full_name=full_name,
            first_name=first,
            last_name=last,
            nickname=data.get("nickname"),
            title=data.get("title"),
            epithet=epithet or data.get("epithet"),
        )

    @property
    def formal_name(self) -> str:
        """Formal name with title prefix if available.

        Returns ``"King Aragorn"`` or ``"Frodo Baggins"`` depending on what
        fields are populated.
        """
        if self.title and self.first_name:
            return f"{self.title} {self.first_name}"
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.full_name

    @property
    def casual_name(self) -> str:
        """Casual name: nickname if available, else first name."""
        return self.nickname or self.first_name or self.full_name

    @property
    def short_name(self) -> str:
        """Shortest reasonable name for dialogue tags."""
        return self.nickname or self.first_name or self.full_name

    @property
    def sort_key(self) -> str:
        """Name key for alphabetical sorting by last name."""
        if self.last_name and self.first_name:
            return f"{self.last_name}, {self.first_name}"
        return self.first_name or self.full_name

    def get_name_for_context(self, context: str) -> str:
        """Return the appropriate name for a given narrative context.

        Args:
            context: One of ``'formal'``, ``'casual'``, ``'dialogue'``,
                ``'narrative'``, or ``'sort'``.

        Returns:
            Name string appropriate for the context.  Falls back to
            ``full_name`` for unrecognised contexts.
        """
        context_map: Dict[str, str] = {
            "formal": self.formal_name,
            "casual": self.casual_name,
            "dialogue": self.short_name,
            "narrative": self.full_name,
            "sort": self.sort_key,
        }
        return context_map.get(context, self.full_name)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _parse_full_name(full_name: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Parse a full name string into (first_name, last_name, epithet).

    Handles epithets of the form ``"the Grey"`` or ``"The Dunedan"``, then
    splits remaining text into first and last components.

    Args:
        full_name: The complete name string to parse.

    Returns:
        Tuple of ``(first_name, last_name, epithet)`` where ``last_name``
        and ``epithet`` may be ``None``.
    """
    epithet: Optional[str] = None
    working = full_name

    match = re.search(r"\s+the\s+", working, flags=re.IGNORECASE)
    if match:
        epithet = "the " + working[match.end():].strip()
        working = working[: match.start()].strip()

    parts = working.split(None, 1)
    first = parts[0] if parts else working or None
    last = parts[1] if len(parts) > 1 else None

    return first, last, epithet


# ---------------------------------------------------------------------------
# Public formatting helpers
# ---------------------------------------------------------------------------

def format_character_list(
    characters: List[Dict[str, Any]],
    format_type: str = "full",
) -> str:
    """Format a list of character dictionaries as a name string.

    Args:
        characters: List of character data dictionaries.
        format_type: One of ``'full'`` (default), ``'short'``, or
            ``'sorted'``.

    Returns:
        Comma-separated name string.
    """
    if format_type == "sorted":
        def _sort_key(char: Dict[str, Any]) -> str:
            last = char.get("last_name", "")
            first = char.get("first_name") or char.get("name", "")
            return f"{last}, {first}" if last else first

        return ", ".join(
            c.get("name", "Unknown") for c in sorted(characters, key=_sort_key)
        )

    if format_type == "short":
        return ", ".join(
            c.get("nickname") or c.get("first_name") or c.get("name", "Unknown")
            for c in characters
        )

    return ", ".join(c.get("name", "Unknown") for c in characters)


def get_name_for_dialogue(character: Dict[str, Any]) -> str:
    """Return the name to use in dialogue tags for a character.

    Prefers nickname, then first_name, then the full name.

    Args:
        character: Character data dictionary.

    Returns:
        Best name for dialogue attribution.
    """
    return (
        character.get("nickname")
        or character.get("first_name")
        or character.get("name", "Unknown")
    )


def get_formal_introduction(character: Dict[str, Any]) -> str:
    """Build a formal introduction string including title and epithet.

    Args:
        character: Character data dictionary.

    Returns:
        Introduction string, e.g. ``"King Aragorn the Dunedan"``.
    """
    parts: List[str] = []

    if character.get("title"):
        parts.append(character["title"])

    parts.append(character.get("name", "Unknown"))

    if character.get("epithet"):
        parts.append(character["epithet"])

    return " ".join(parts)


def build_name_fields(full_name: str, nickname: Optional[str] = None) -> Dict[str, Any]:
    """Derive structured name fields from a legacy full-name string.

    Useful for migration scripts.

    Args:
        full_name: The complete name string, e.g. ``"Gandalf the Grey"``.
        nickname: Optional pre-existing nickname value.

    Returns:
        Dictionary with ``first_name``, and optionally ``last_name`` and
        ``epithet`` keys.
    """
    first, last, epithet = _parse_full_name(full_name)
    result: Dict[str, Any] = {}
    if first:
        result["first_name"] = first
    if last:
        result["last_name"] = last
    if epithet:
        result["epithet"] = epithet
    if nickname:
        result["nickname"] = nickname
    return result


def _validate_name_consistency(
    data: Dict[str, Any], file_prefix: str
) -> List[str]:
    """Check that first_name, last_name, and epithet are consistent with name.

    Args:
        data: Character or NPC JSON dictionary.
        file_prefix: Error prefix string for messages.

    Returns:
        List of error strings (empty if all consistent).
    """
    errors: List[str] = []
    name: str = data.get("name", "")

    first_name: Optional[str] = data.get("first_name")
    if first_name and not name.startswith(first_name):
        errors.append(
            f"{file_prefix}Field 'first_name' ('{first_name}') should match "
            f"the start of 'name' ('{name}')"
        )

    last_name: Optional[str] = data.get("last_name")
    if last_name and last_name not in name:
        errors.append(
            f"{file_prefix}Field 'last_name' ('{last_name}') does not appear "
            f"in 'name' ('{name}')"
        )

    return errors


def validate_name_fields(data: Dict[str, Any], file_prefix: str = "") -> List[str]:
    """Validate optional structured name fields in a character or NPC dict.

    Only validates the optional sub-fields (``first_name``, ``last_name``,
    ``title``, ``epithet``, ``nickname``) and their consistency with ``name``.
    Presence and type of the required ``name`` field itself is left to the
    calling validator's own required-field checks.

    Args:
        data: Character or NPC JSON dictionary.
        file_prefix: Error prefix string for messages.

    Returns:
        List of validation error strings.
    """
    errors: List[str] = []

    # Nothing to check if name is absent or not a string
    if not isinstance(data.get("name"), str):
        return errors

    optional_name_fields: Dict[str, Any] = {
        "first_name": str,
        "last_name": (str, type(None)),
        "title": str,
        "epithet": str,
        "nickname": (str, type(None)),
    }

    for fname, expected_type in optional_name_fields.items():
        if fname in data and not isinstance(data[fname], expected_type):
            type_name = get_type_name(expected_type)
            errors.append(
                f"{file_prefix}Field '{fname}' should be {type_name}, "
                f"got {type(data[fname]).__name__}"
            )

    errors.extend(_validate_name_consistency(data, file_prefix))
    return errors
