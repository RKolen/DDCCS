"""FastAPI application for the D&D search query parser sidecar."""

import logging
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from src.ai.abilities_rag import Ability, get_abilities
from src.characters.character_template import (
    TemplateOptions,
    build_character_data_from_template,
    load_template,
)
from src.config.config_loader import load_config
from src.sidecar.models import (
    BuildCharacterRequest,
    BuildCharacterResponse,
    ErrorResponse,
    HealthResponse,
    ParseQueryRequest,
    ParseQueryResponse,
    SpotlightCharacterScore,
    SpotlightRequest,
    SpotlightResponse,
)
from src.sidecar.query_parser import parse_query
from src.stories.spotlight_engine import SpotlightEngine

logger = logging.getLogger(__name__)

_HEALTH_PATH = "/health"


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifespan context — log startup and flush resources on shutdown."""
    logger.info("Sidecar starting")
    yield
    logger.info("Sidecar shutting down")


app = FastAPI(
    title="D&D Search Query Parser",
    description="Normalises natural-language search queries for the Milvus content index.",
    version="1.0.0",
    lifespan=_lifespan,
)


@app.middleware("http")
async def _auth_middleware(request: Request, call_next: Any) -> Any:
    """Reject requests missing a valid X-Sidecar-Secret header.

    Auth is skipped for /health so readiness probes always pass through.
    When SIDECAR_SECRET is unset, all requests are allowed.

    Args:
        request: Incoming HTTP request.
        call_next: Next middleware or route handler.

    Returns:
        401 JSONResponse when auth fails, otherwise the downstream response.
    """
    if request.url.path == _HEALTH_PATH:
        return await call_next(request)
    secret = os.getenv("SIDECAR_SECRET", "")
    if secret and request.headers.get("X-Sidecar-Secret", "") != secret:
        return JSONResponse(
            status_code=401,
            content=ErrorResponse(
                error="Unauthorized",
                detail="Missing or invalid X-Sidecar-Secret header",
            ).model_dump(),
        )
    return await call_next(request)

_search_router = APIRouter(prefix="/search", tags=["search"])
_eval_router = APIRouter(prefix="/eval", tags=["eval"])
_character_router = APIRouter(prefix="/character", tags=["character"])


@app.exception_handler(Exception)
async def _unhandled_exception_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    """Return a structured JSON error envelope for unhandled exceptions."""
    logger.exception("Unhandled exception in sidecar route")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=type(exc).__name__,
            detail=str(exc),
        ).model_dump(),
    )


@app.get(_HEALTH_PATH, response_model=HealthResponse)
def health() -> HealthResponse:
    """Return service health and AI configuration status.

    Returns:
        HealthResponse indicating service status and AI availability.
    """
    config = load_config()
    return HealthResponse(status="ok", ai_configured=config.ai.is_configured())


@_search_router.post("/parse-query", response_model=ParseQueryResponse)
def parse_query_endpoint(req: ParseQueryRequest) -> ParseQueryResponse:
    """Parse a natural-language D&D search query into structured intent.

    Args:
        req: ParseQueryRequest containing the raw query string.

    Returns:
        ParseQueryResponse with normalized query and optional content type.
    """
    return parse_query(req.q)


@_eval_router.post("/spotlight", response_model=SpotlightResponse)
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


@_character_router.post("/build-from-template", response_model=BuildCharacterResponse)
def build_from_template_endpoint(req: BuildCharacterRequest) -> BuildCharacterResponse:
    """Derive a full character sheet from a class template.

    Reuses the template engine to compute hit points, proficiency bonus,
    skills/saves, spell slots, and equipment, then enriches the class
    features through the reusable RAG-backed feature service. The returned
    payload is a source-character sheet ready to persist via the Drupal
    createCharacter mutation.

    Args:
        req: BuildCharacterRequest with the user's class/level/score choices.

    Returns:
        BuildCharacterResponse wrapping the derived character dictionary.

    Raises:
        HTTPException: 404 when no template exists for the requested class.
    """
    template = load_template(req.class_name)
    if template is None:
        raise HTTPException(
            status_code=404,
            detail=f"No class template found for '{req.class_name}'",
        )
    options = TemplateOptions(
        name=req.name,
        race=req.race,
        level=req.level,
        background=req.background,
        subclass=req.subclass,
        ability_scores=req.ability_scores,
        skills=req.skills,
    )
    character = build_character_data_from_template(template, options)
    character["subspecies"] = req.subspecies or ""
    character["abilities"] = _resolve_abilities(req)
    return BuildCharacterResponse(character=character)


def _resolve_abilities(req: BuildCharacterRequest) -> list[Ability]:
    """Resolve class, species, and subspecies abilities from the rules wiki.

    Args:
        req: The build request with class/species/subspecies and level.

    Returns:
        De-duplicated abilities up to the requested level. Empty when RAG is
        unavailable (the character is still created without ability terms).
    """
    resolved: list[Ability] = []
    resolved.extend(get_abilities("class", req.class_name, req.level))
    resolved.extend(get_abilities("species", req.race, req.level))
    if req.subspecies:
        resolved.extend(get_abilities("subspecies", req.subspecies, req.level))

    seen: set[str] = set()
    unique: list[Ability] = []
    for ability in resolved:
        key = ability["name"].lower()
        if key and key not in seen:
            seen.add(key)
            unique.append(ability)
    return unique


app.include_router(_search_router)
app.include_router(_eval_router)
app.include_router(_character_router)
