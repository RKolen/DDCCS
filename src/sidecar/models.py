"""Pydantic request and response models for the query parser sidecar."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class ParseQueryRequest(BaseModel):
    """Incoming query parse request from Drupal."""

    q: str

    @field_validator("q")
    @classmethod
    def strip_and_validate(cls, value: str) -> str:
        """Strip surrounding whitespace and reject blank queries.

        Args:
            value: Raw query string.

        Returns:
            Stripped query string.

        Raises:
            ValueError: If the query is empty after stripping.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("q must not be empty")
        return stripped


class ParseQueryResponse(BaseModel):
    """Parsed query result returned to the caller."""

    original: str
    query: str
    inferred_type: Optional[str] = None
    confidence: float


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    ai_configured: bool


class SpotlightRequest(BaseModel):
    """Spotlight score request from the Gatsby frontend."""

    campaign_name: str
    character_names: List[str]


class SpotlightCharacterScore(BaseModel):
    """Spotlight score for a single character."""

    name: str
    score: float


class SpotlightResponse(BaseModel):
    """Spotlight scores for all requested characters."""

    campaign_name: str
    entries: List[SpotlightCharacterScore]


class BuildCharacterRequest(BaseModel):
    """Request to derive a character sheet from a class template."""

    name: str
    class_name: str
    level: int = Field(default=1, ge=1, le=20)
    ability_scores: Optional[Dict[str, int]] = None
    subclass: Optional[str] = None
    background: str = ""
    race: str = "Human"
    skills: List[str] = Field(default_factory=list)

    @field_validator("name", "class_name")
    @classmethod
    def strip_required(cls, value: str) -> str:
        """Strip whitespace and reject blank required identifiers.

        Args:
            value: Raw field value.

        Returns:
            The stripped value.

        Raises:
            ValueError: If the value is empty after stripping.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be empty")
        return stripped


class BuildCharacterResponse(BaseModel):
    """Derived character sheet ready for persistence.

    The ``character`` payload follows the game_data character dictionary
    shape produced by the template engine (ability scores, derived hit
    points, proficiency bonus, class features, spell slots, equipment).
    """

    character: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Shared error envelope returned by all sidecar endpoints on failure."""

    error: str
    detail: str
