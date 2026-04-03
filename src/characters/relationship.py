"""Relationship data structures and management."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from src.characters.relationship_types import RelationshipType, get_inverse  # noqa: F401


class RelationshipStatus(Enum):
    """Status of a relationship."""
    CURRENT = "current"
    FORMER = "former"
    COMPLICATED = "complicated"
    UNKNOWN = "unknown"


@dataclass
class RelationshipEvent:
    """A significant event in a relationship's history."""
    date: Optional[str] = None
    description: str = ""
    impact: int = 0  # -5 to +5, how this affected the relationship

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "description": self.description,
            "impact": self.impact
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RelationshipEvent':
        return cls(
            date=data.get("date"),
            description=data.get("description", ""),
            impact=data.get("impact", 0)
        )


@dataclass
class Relationship:
    """A structured relationship between two entities."""

    # Required fields
    target_name: str
    relationship_type: RelationshipType

    # Optional fields with defaults
    strength: int = 5  # 1-10 scale
    status: RelationshipStatus = RelationshipStatus.CURRENT
    notes: str = ""
    history: List[RelationshipEvent] = field(default_factory=list)

    # Metadata
    created_date: Optional[str] = None
    last_updated: Optional[str] = None

    def __post_init__(self):
        # Validate strength range
        if not 1 <= self.strength <= 10:
            raise ValueError(f"Strength must be 1-10, got {self.strength}")

        # Set timestamps if not provided
        if self.created_date is None:
            self.created_date = datetime.now().isoformat()
        if self.last_updated is None:
            self.last_updated = datetime.now().isoformat()

    @property
    def is_positive(self) -> bool:
        """Check if this is a generally positive relationship."""
        positive_types = {
            RelationshipType.FAMILY_CLOSE,
            RelationshipType.ROMANTIC_PARTNER,
            RelationshipType.FRIEND_CLOSE,
            RelationshipType.FRIEND,
            RelationshipType.ALLY,
            RelationshipType.MENTOR,
            RelationshipType.STUDENT,
        }
        return self.relationship_type in positive_types

    @property
    def is_negative(self) -> bool:
        """Check if this is a generally negative relationship."""
        negative_types = {
            RelationshipType.FAMILY_ESTRANGED,
            RelationshipType.ENEMY,
            RelationshipType.NEMESIS,
            RelationshipType.RIVAL,
        }
        return self.relationship_type in negative_types

    def add_event(self, description: str, impact: int = 0, date: str = None):
        """Add a relationship event and update strength accordingly."""
        event = RelationshipEvent(
            date=date or datetime.now().isoformat(),
            description=description,
            impact=impact
        )
        self.history.append(event)

        # Adjust strength based on impact
        self.strength = max(1, min(10, self.strength + impact))
        self.last_updated = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "target_name": self.target_name,
            "type": self.relationship_type.value,
            "strength": self.strength,
            "status": self.status.value,
            "notes": self.notes,
            "history": [e.to_dict() for e in self.history],
            "created_date": self.created_date,
            "last_updated": self.last_updated
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Relationship':
        """Create from dictionary."""
        return cls(
            target_name=data["target_name"],
            relationship_type=RelationshipType(data.get("type", "unknown")),
            strength=data.get("strength", 5),
            status=RelationshipStatus(data.get("status", "current")),
            notes=data.get("notes", ""),
            history=[RelationshipEvent.from_dict(e) for e in data.get("history", [])],
            created_date=data.get("created_date"),
            last_updated=data.get("last_updated")
        )

    @classmethod
    def from_legacy(cls, target_name: str, description: str) -> 'Relationship':
        """Create from legacy simple string format."""
        inferred_type = cls._infer_type_from_description(description)
        return cls(
            target_name=target_name,
            relationship_type=inferred_type,
            notes=description
        )

    @staticmethod
    def _infer_type_from_description(description: str) -> RelationshipType:
        """Attempt to infer relationship type from a text description."""
        desc_lower = description.lower()

        # Family keywords
        if any(w in desc_lower for w in ["father", "mother", "sibling", "son", "daughter"]):
            return RelationshipType.FAMILY_CLOSE

        # Romantic keywords
        if any(w in desc_lower for w in ["beloved", "lover", "spouse", "partner", "wife", "husband"]):
            return RelationshipType.ROMANTIC_PARTNER

        # Friendship keywords
        if any(w in desc_lower for w in ["friend", "companion", "trusted"]):
            return RelationshipType.FRIEND_CLOSE

        # Mentor keywords
        if any(w in desc_lower for w in ["mentor", "teacher", "master"]):
            return RelationshipType.MENTOR

        # Enemy keywords
        if any(w in desc_lower for w in ["enemy", "nemesis", "foe", "rival"]):
            return RelationshipType.ENEMY

        # Ally keywords
        if any(w in desc_lower for w in ["ally", "comrade"]):
            return RelationshipType.ALLY

        return RelationshipType.UNKNOWN
