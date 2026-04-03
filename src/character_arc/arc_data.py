"""Data structures for character arc tracking."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ArcDataPoint:
    """A single data point in a character's arc."""

    story_file: str
    session_id: str
    timestamp: str

    # Metric values at this point
    metric_values: Dict[str, Any] = field(default_factory=dict)

    # Qualitative observations
    observations: List[str] = field(default_factory=list)

    # Key events that influenced this point
    key_events: List[str] = field(default_factory=list)

    # AI analysis notes
    ai_analysis: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "story_file": self.story_file,
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "metric_values": self.metric_values,
            "observations": self.observations,
            "key_events": self.key_events,
            "ai_analysis": self.ai_analysis,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArcDataPoint":
        """Create from dictionary."""
        return cls(
            story_file=data.get("story_file", ""),
            session_id=data.get("session_id", ""),
            timestamp=data.get("timestamp", ""),
            metric_values=data.get("metric_values", {}),
            observations=data.get("observations", []),
            key_events=data.get("key_events", []),
            ai_analysis=data.get("ai_analysis", ""),
        )


@dataclass
class RelationshipArc:
    """Tracks the arc of a relationship between characters."""

    character_name: str
    target_name: str

    relationship_type: str = "neutral"
    strength: int = 5
    trust: int = 5

    changes: List[Dict[str, Any]] = field(default_factory=list)
    key_moments: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "character_name": self.character_name,
            "target_name": self.target_name,
            "relationship_type": self.relationship_type,
            "strength": self.strength,
            "trust": self.trust,
            "changes": self.changes,
            "key_moments": self.key_moments,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RelationshipArc":
        """Create from dictionary."""
        return cls(
            character_name=data.get("character_name", ""),
            target_name=data.get("target_name", ""),
            relationship_type=data.get("relationship_type", "neutral"),
            strength=data.get("strength", 5),
            trust=data.get("trust", 5),
            changes=data.get("changes", []),
            key_moments=data.get("key_moments", []),
        )


@dataclass
class ArcState:
    """Cached arc analysis state for a character."""

    direction: str = "stasis"
    stage: str = "introduction"
    summary: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CharacterArc:
    """Complete arc data for a character.

    Attributes:
        character_name: Name of the character.
        campaign_name: Name of the campaign.
        baseline: Starting metric values from the character profile.
        data_points: Ordered list of arc observations per story.
        relationships: Relationship arcs keyed by target name.
        goals: List of goal dicts with description, status, and progress.
        state: Cached analysis state (direction, stage, summary, timestamps).
    """

    character_name: str
    campaign_name: str

    baseline: Dict[str, Any] = field(default_factory=dict)
    data_points: List[ArcDataPoint] = field(default_factory=list)
    relationships: Dict[str, RelationshipArc] = field(default_factory=dict)
    goals: List[Dict[str, Any]] = field(default_factory=list)
    state: ArcState = field(default_factory=ArcState)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "character_name": self.character_name,
            "campaign_name": self.campaign_name,
            "baseline": self.baseline,
            "data_points": [dp.to_dict() for dp in self.data_points],
            "relationships": {k: v.to_dict() for k, v in self.relationships.items()},
            "goals": self.goals,
            "arc_direction": self.state.direction,
            "arc_stage": self.state.stage,
            "arc_summary": self.state.summary,
            "created_at": self.state.created_at,
            "updated_at": self.state.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterArc":
        """Create from dictionary."""
        arc = cls(
            character_name=data["character_name"],
            campaign_name=data["campaign_name"],
            baseline=data.get("baseline", {}),
            goals=data.get("goals", []),
            state=ArcState(
                direction=data.get("arc_direction", "stasis"),
                stage=data.get("arc_stage", "introduction"),
                summary=data.get("arc_summary", ""),
                created_at=data.get("created_at", datetime.now().isoformat()),
                updated_at=data.get("updated_at", datetime.now().isoformat()),
            ),
        )

        arc.data_points = [
            ArcDataPoint.from_dict(dp) for dp in data.get("data_points", [])
        ]

        arc.relationships = {
            k: RelationshipArc.from_dict(v)
            for k, v in data.get("relationships", {}).items()
        }

        return arc

    def add_data_point(self, data_point: ArcDataPoint) -> None:
        """Add a new data point to the arc.

        Args:
            data_point: The data point to append.
        """
        self.data_points.append(data_point)
        self.state.updated_at = datetime.now().isoformat()

    def get_metric_progression(self, metric_id: str) -> List[tuple]:
        """Get the progression of a metric over time.

        Args:
            metric_id: ID of the metric to retrieve.

        Returns:
            List of (timestamp, value) tuples.
        """
        progression: List[tuple] = []
        for data_point in self.data_points:
            if metric_id in data_point.metric_values:
                progression.append(
                    (data_point.timestamp, data_point.metric_values[metric_id])
                )
        return progression

    def get_stories_analyzed(self) -> Optional[int]:
        """Return the number of data points, or None if none exist."""
        count = len(self.data_points)
        return count if count > 0 else None
