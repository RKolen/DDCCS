"""FastAPI application for the D&D search query parser sidecar."""

from fastapi import FastAPI

from src.config.config_loader import load_config
from src.sidecar.models import (
    HealthResponse,
    ParseQueryRequest,
    ParseQueryResponse,
    SpotlightCharacterScore,
    SpotlightRequest,
    SpotlightResponse,
)
from src.sidecar.query_parser import parse_query
from src.stories.spotlight_engine import SpotlightEngine

app = FastAPI(
    title="D&D Search Query Parser",
    description="Normalises natural-language search queries for the Milvus content index.",
    version="1.0.0",
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Return service health and AI configuration status.

    Returns:
        HealthResponse indicating service status and AI availability.
    """
    config = load_config()
    return HealthResponse(status="ok", ai_configured=config.ai.is_configured())


@app.post("/spotlight", response_model=SpotlightResponse)
def spotlight_endpoint(req: SpotlightRequest) -> SpotlightResponse:
    """Score a list of characters by narrative importance for a campaign.

    Accepts the authoritative character list from Drupal and scores them
    against local story-file signals (recency, unresolved threads, DC
    failures, relationship tension). Characters with no signal data receive
    a score of zero, which is valid for new campaigns without local history.

    Args:
        req: SpotlightRequest with campaign_name and character_names.

    Returns:
        SpotlightResponse with scores sorted by score descending.
    """
    engine = SpotlightEngine()
    report = engine.generate_report(
        req.campaign_name,
        character_names=req.character_names,
    )
    entries = [
        SpotlightCharacterScore(name=entry.name, score=entry.score)
        for entry in report.entries
        if entry.entity_type == "character"
    ]
    scored_names = {e.name for e in entries}
    for name in req.character_names:
        if name not in scored_names:
            entries.append(SpotlightCharacterScore(name=name, score=0.0))
    return SpotlightResponse(campaign_name=req.campaign_name, entries=entries)


@app.post("/parse-query", response_model=ParseQueryResponse)
def parse_query_endpoint(req: ParseQueryRequest) -> ParseQueryResponse:
    """Parse a natural-language D&D search query into structured intent.

    Args:
        req: ParseQueryRequest containing the raw query string.

    Returns:
        ParseQueryResponse with normalized query and optional content type.
    """
    return parse_query(req.q)
