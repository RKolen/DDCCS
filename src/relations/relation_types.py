"""Data types for arc relationship suggestion."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Narrative weight, matching Drupal's field_pair_tier.
TIER_DIRECT = 1
TIER_THEMATIC = 2
TIER_INCIDENTAL = 3

VALID_TIERS = (TIER_DIRECT, TIER_THEMATIC, TIER_INCIDENTAL)


@dataclass
class CharacterDigest:
    """The little a model needs to reason about one character.

    Kept small: whole sheets for a large cast will not fit a local prompt, so
    only the fields that actually generate connections are carried.

    Attributes:
        name: The character's name, used verbatim in suggestions.
        summary: One-line description (species, class, role).
        origin: Hometown or place of origin, if known.
        faction: Faction or allegiance, if known.
        hooks: Short plot hooks, bonds, or traits from the sheet.
    """

    name: str
    summary: str = ""
    origin: str = ""
    faction: str = ""
    hooks: List[str] = field(default_factory=list)

    def to_line(self) -> str:
        """Render the digest as one compact prompt line.

        Returns:
            A single line naming the character and its salient details.
        """
        parts: List[str] = [self.name]
        if self.summary:
            parts.append(self.summary)
        if self.origin:
            parts.append(f"from {self.origin}")
        if self.faction:
            parts.append(f"faction: {self.faction}")
        if self.hooks:
            parts.append("; ".join(self.hooks[:3]))
        return " - ".join(parts)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterDigest":
        """Build a digest from a plain dictionary.

        Args:
            data: Mapping with any of name, summary, origin, faction, hooks.

        Returns:
            The populated digest.
        """
        hooks = data.get("hooks") or []
        return cls(
            name=str(data.get("name", "")),
            summary=str(data.get("summary", "")),
            origin=str(data.get("origin", "")),
            faction=str(data.get("faction", "")),
            hooks=[str(h) for h in hooks if str(h).strip()],
        )


@dataclass
class RelationSuggestion:
    """One suggested directed relationship between two characters.

    Attributes:
        source: Name of the character the bond originates from.
        target: Name of the character the bond points at.
        relation_type: Short label, e.g. "sworn protector".
        tier: Narrative weight, 1 (direct) to 3 (incidental).
        note: The connection itself and how it can be used in play.
    """

    source: str
    target: str
    relation_type: str = ""
    tier: int = TIER_THEMATIC
    note: str = ""

    def pair_key(self) -> str:
        """Return an order-independent key for the two characters.

        Two suggestions naming the same people are one bond, whichever end the
        model made the source.

        Returns:
            A stable key for the unordered pair.
        """
        ends = sorted([self.source.strip().lower(), self.target.strip().lower()])
        return "||".join(ends)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the suggestion for transport.

        Returns:
            A JSON-safe dictionary.
        """
        return {
            "source": self.source,
            "target": self.target,
            "relation_type": self.relation_type,
            "tier": self.tier,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional["RelationSuggestion"]:
        """Build a suggestion from a model or client dictionary.

        Args:
            data: Mapping with at least source and target.

        Returns:
            The suggestion, or None when either end is missing or self-paired.
        """
        source = str(data.get("source", "")).strip()
        target = str(data.get("target", "")).strip()
        if not source or not target or source.lower() == target.lower():
            return None
        try:
            tier = int(data.get("tier", TIER_THEMATIC))
        except (TypeError, ValueError):
            tier = TIER_THEMATIC
        if tier not in VALID_TIERS:
            tier = TIER_THEMATIC
        return cls(
            source=source,
            target=target,
            relation_type=str(data.get("relation_type", "") or data.get("type", "")).strip(),
            tier=tier,
            note=str(data.get("note", "")).strip(),
        )
