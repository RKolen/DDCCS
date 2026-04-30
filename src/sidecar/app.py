"""FastAPI application for the D&D search query parser sidecar."""

from fastapi import FastAPI

from src.config.config_loader import load_config
from src.sidecar.models import HealthResponse, ParseQueryRequest, ParseQueryResponse
from src.sidecar.query_parser import parse_query

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


@app.post("/parse-query", response_model=ParseQueryResponse)
def parse_query_endpoint(req: ParseQueryRequest) -> ParseQueryResponse:
    """Parse a natural-language D&D search query into structured intent.

    Args:
        req: ParseQueryRequest containing the raw query string.

    Returns:
        ParseQueryResponse with normalized query and optional content type.
    """
    return parse_query(req.q)
