"""
Story Suggestion Types

Data models for AI-generated story suggestions.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class SuggestionType(Enum):
    """Types of story suggestions."""

    PLOT_HOOK = "plot_hook"
    CHARACTER_MOMENT = "character_moment"
    PLOT_TWIST = "plot_twist"
    NARRATIVE_IMPROVEMENT = "narrative_improvement"
    NPC_INTERACTION = "npc_interaction"
    FORESHADOWING = "foreshadowing"


class SuggestionPriority(Enum):
    """Priority levels for suggestions."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class SuggestionContext:
    """Optional context and metadata for a story suggestion.

    Attributes:
        source_story: Filename of the story that triggered the suggestion.
        relevant_characters: Character names referenced by this suggestion.
        relevant_npcs: NPC names referenced by this suggestion.
        implementation_notes: Practical guidance for the DM.
        suggested_timing: When to use this suggestion (e.g. "next session").
        created_at: Timestamp when the suggestion was generated.
    """

    source_story: Optional[str] = None
    relevant_characters: List[str] = field(default_factory=list)
    relevant_npcs: List[str] = field(default_factory=list)
    implementation_notes: Optional[str] = None
    suggested_timing: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SuggestionReview:
    """DM review status and notes for a suggestion.

    Attributes:
        accepted: None = pending, True = accepted, False = rejected.
        user_notes: Optional DM notes attached to this suggestion.
    """

    accepted: Optional[bool] = None
    user_notes: Optional[str] = None


@dataclass
class StorySuggestion:
    """A single AI-generated story suggestion.

    Attributes:
        suggestion_type: Category of the suggestion.
        title: Short headline for the suggestion.
        description: Full description of the suggestion.
        rationale: Why this suggestion fits the campaign.
        priority: Urgency or importance of the suggestion.
        context: Optional context and metadata for the suggestion.
        review: DM review status and notes.
    """

    suggestion_type: SuggestionType
    title: str
    description: str
    rationale: str
    priority: SuggestionPriority = SuggestionPriority.MEDIUM
    context: SuggestionContext = field(default_factory=SuggestionContext)
    review: SuggestionReview = field(default_factory=SuggestionReview)

    def to_dict(self) -> Dict:
        """Serialize to a flat JSON-compatible dictionary.

        Returns:
            Flat dictionary representation of the suggestion.
        """
        return {
            "suggestion_type": self.suggestion_type.value,
            "title": self.title,
            "description": self.description,
            "rationale": self.rationale,
            "priority": self.priority.value,
            "source_story": self.context.source_story,
            "relevant_characters": self.context.relevant_characters,
            "relevant_npcs": self.context.relevant_npcs,
            "implementation_notes": self.context.implementation_notes,
            "suggested_timing": self.context.suggested_timing,
            "created_at": self.context.created_at.isoformat(),
            "accepted": self.review.accepted,
            "user_notes": self.review.user_notes,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "StorySuggestion":
        """Deserialize from a flat dictionary.

        Args:
            data: Flat dictionary produced by to_dict.

        Returns:
            StorySuggestion instance.
        """
        created_raw = data.get("created_at")
        created_at = datetime.fromisoformat(created_raw) if created_raw else datetime.now()

        return cls(
            suggestion_type=SuggestionType(data["suggestion_type"]),
            title=data["title"],
            description=data["description"],
            rationale=data["rationale"],
            priority=SuggestionPriority(data.get("priority", "medium")),
            context=SuggestionContext(
                source_story=data.get("source_story"),
                relevant_characters=data.get("relevant_characters", []),
                relevant_npcs=data.get("relevant_npcs", []),
                implementation_notes=data.get("implementation_notes"),
                suggested_timing=data.get("suggested_timing"),
                created_at=created_at,
            ),
            review=SuggestionReview(
                accepted=data.get("accepted"),
                user_notes=data.get("user_notes"),
            ),
        )


@dataclass
class SuggestionSet:
    """A collection of suggestions for a campaign.

    Attributes:
        campaign_name: Name of the campaign these suggestions belong to.
        story_file: Optional story filename that triggered generation.
        suggestions: List of all suggestions in this set.
        generated_at: Timestamp when the set was created.
    """

    campaign_name: str
    story_file: Optional[str]
    suggestions: List[StorySuggestion] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)

    def add_suggestion(self, suggestion: StorySuggestion) -> None:
        """Add a suggestion to this set.

        Args:
            suggestion: StorySuggestion to add.
        """
        self.suggestions.append(suggestion)

    def get_by_type(self, suggestion_type: SuggestionType) -> List[StorySuggestion]:
        """Return suggestions filtered by type.

        Args:
            suggestion_type: The SuggestionType to filter for.

        Returns:
            List of matching StorySuggestion objects.
        """
        return [s for s in self.suggestions if s.suggestion_type == suggestion_type]

    def get_accepted(self) -> List[StorySuggestion]:
        """Return all accepted suggestions.

        Returns:
            List of StorySuggestion objects where accepted is True.
        """
        return [s for s in self.suggestions if s.review.accepted is True]

    def get_pending(self) -> List[StorySuggestion]:
        """Return all unreviewed suggestions.

        Returns:
            List of StorySuggestion objects where accepted is None.
        """
        return [s for s in self.suggestions if s.review.accepted is None]

    def to_dict(self) -> Dict:
        """Serialize to a JSON-compatible dictionary.

        Returns:
            Dictionary representation of the suggestion set.
        """
        return {
            "campaign_name": self.campaign_name,
            "story_file": self.story_file,
            "suggestions": [s.to_dict() for s in self.suggestions],
            "generated_at": self.generated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "SuggestionSet":
        """Deserialize from a dictionary.

        Args:
            data: Dictionary produced by to_dict.

        Returns:
            SuggestionSet instance.
        """
        generated_raw = data.get("generated_at")
        generated_at = (
            datetime.fromisoformat(generated_raw) if generated_raw else datetime.now()
        )
        return cls(
            campaign_name=data["campaign_name"],
            story_file=data.get("story_file"),
            suggestions=[
                StorySuggestion.from_dict(s) for s in data.get("suggestions", [])
            ],
            generated_at=generated_at,
        )
