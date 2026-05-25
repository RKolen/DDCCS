"""Pydantic request and response models for the query parser sidecar."""

from typing import List, Optional

from pydantic import BaseModel, field_validator


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
