"""Criteria and metrics for character arc analysis."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class ArcDimension(Enum):
    """Dimensions of character development."""

    PERSONALITY = "personality"
    RELATIONSHIPS = "relationships"
    ABILITIES = "abilities"
    GOALS = "goals"
    BELIEFS = "beliefs"
    REPUTATION = "reputation"
    POSSESSIONS = "possessions"
    TRAUMA = "trauma"
    GROWTH = "growth"


class ArcDirection(Enum):
    """Direction of character change."""

    GROWTH = "growth"
    DECLINE = "decline"
    STASIS = "stasis"
    FLUCTUATION = "fluctuation"
    TRANSFORMATION = "transformation"


class ArcStage(Enum):
    """Stages in a character arc."""

    INTRODUCTION = "introduction"
    ESTABLISHMENT = "establishment"
    CHALLENGE = "challenge"
    DEVELOPMENT = "development"
    CLIMAX = "climax"
    RESOLUTION = "resolution"
    AFTERMATH = "aftermath"


@dataclass
class ArcMetric:
    """A measurable aspect of character development."""

    metric_id: str
    name: str
    dimension: ArcDimension
    description: str
    measurement_type: str  # "numeric", "categorical", "text"
    scale_range: Optional[tuple] = None  # (min, max) for numeric metrics
    categories: List[str] = field(default_factory=list)


STANDARD_METRICS: List[ArcMetric] = [
    ArcMetric(
        metric_id="relationship_strength",
        name="Relationship Strength",
        dimension=ArcDimension.RELATIONSHIPS,
        description="Overall strength of relationships with others",
        measurement_type="numeric",
        scale_range=(1, 10),
    ),
    ArcMetric(
        metric_id="trust_level",
        name="Trust Level",
        dimension=ArcDimension.RELATIONSHIPS,
        description="Willingness to trust others",
        measurement_type="numeric",
        scale_range=(1, 10),
    ),
    ArcMetric(
        metric_id="combat_effectiveness",
        name="Combat Effectiveness",
        dimension=ArcDimension.ABILITIES,
        description="Effectiveness in combat situations",
        measurement_type="numeric",
        scale_range=(1, 10),
    ),
    ArcMetric(
        metric_id="moral_alignment",
        name="Moral Alignment",
        dimension=ArcDimension.BELIEFS,
        description="Current moral stance",
        measurement_type="categorical",
        categories=[
            "lawful_good",
            "neutral_good",
            "chaotic_good",
            "lawful_neutral",
            "true_neutral",
            "chaotic_neutral",
            "lawful_evil",
            "neutral_evil",
            "chaotic_evil",
        ],
    ),
    ArcMetric(
        metric_id="confidence",
        name="Confidence Level",
        dimension=ArcDimension.PERSONALITY,
        description="Self-confidence and assurance",
        measurement_type="numeric",
        scale_range=(1, 10),
    ),
    ArcMetric(
        metric_id="trauma_level",
        name="Trauma Level",
        dimension=ArcDimension.TRAUMA,
        description="Accumulated psychological trauma",
        measurement_type="numeric",
        scale_range=(0, 10),
    ),
    ArcMetric(
        metric_id="goal_progress",
        name="Goal Progress",
        dimension=ArcDimension.GOALS,
        description="Progress toward primary goal",
        measurement_type="numeric",
        scale_range=(0, 100),
    ),
    ArcMetric(
        metric_id="reputation",
        name="Reputation",
        dimension=ArcDimension.REPUTATION,
        description="How the character is perceived by others",
        measurement_type="categorical",
        categories=[
            "unknown",
            "disliked",
            "neutral",
            "respected",
            "renowned",
            "legendary",
        ],
    ),
]

_METRICS_BY_DIMENSION: Dict[str, List[ArcMetric]] = {}
for _m in STANDARD_METRICS:
    _METRICS_BY_DIMENSION.setdefault(_m.dimension.value, []).append(_m)


@dataclass
class ArcCriteria:
    """Criteria for analyzing character arcs."""

    dimensions: List[ArcDimension] = field(
        default_factory=lambda: list(ArcDimension)
    )
    metrics: List[ArcMetric] = field(default_factory=lambda: list(STANDARD_METRICS))
    min_stories_for_analysis: int = 2
    significance_threshold: float = 0.2

    def get_metrics_for_dimension(self, dimension: ArcDimension) -> List[ArcMetric]:
        """Get all metrics for a specific dimension.

        Args:
            dimension: The arc dimension to filter by.

        Returns:
            List of ArcMetric instances for that dimension.
        """
        return [m for m in self.metrics if m.dimension == dimension]
