"""FastAPI application for the D&D search query parser sidecar."""

import base64
import logging
import os
import random
import shutil
import subprocess
import sys
import tempfile
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Any, AsyncGenerator

from fastapi import APIRouter, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from src.utils.piper_tts_client import PiperTTSClient, get_narrator_voice_id

from src.ai.abilities_rag import Ability, get_abilities, get_background
from src.ai.ai_client import AIClient
from src.ai.comfyui_client import ComfyUIClient
from src.ai.comfyui_workflows import RenderSettings, Txt2ImgParams, txt2img_workflow
from src.ai.equipment_rag import get_equipment_descriptions
from src.ai.portrait_prompt import build_portrait_prompt
from src.character_arc.arc_analyzer import (
    ArcAnalyzer,
    aggregate_arc,
    analyze_character_arc,
    analyze_story_datapoint,
    facts_block,
)
from src.character_arc.arc_data import ArcDataPoint
from src.characters.character_template import (
    TemplateOptions,
    build_character_data_from_template,
    derive_trait_skills,
    load_template,
)
from src.characters.class_plan import get_class_plan
from src.config.config_loader import load_config
from src.sidecar.models import (
    ArcAggregateRequest,
    ArcAnalysisRequest,
    ArcAnalysisResponse,
    ArcDataPointModel,
    ArcGoalModel,
    ArcMetricModel,
    ArcRelationshipModel,
    ArcStoryRequest,
    ArcSynthesisRequest,
    ArcSynthesisResponse,
    BuildCharacterRequest,
    BuildCharacterResponse,
    EquipmentDescribeRequest,
    EquipmentDescribeResponse,
    EquipmentItemInfo,
    ErrorResponse,
    HealthResponse,
    ParseQueryRequest,
    ParseQueryResponse,
    PortraitRequest,
    PortraitResponse,
    ResolveBackgroundRequest,
    ResolveBackgroundResponse,
    SkillPlanRequest,
    SkillPlanResponse,
    SpotlightCharacterScore,
    SpotlightRequest,
    SpotlightResponse,
    TtsRequest,
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
_tts_router = APIRouter(prefix="/tts", tags=["tts"])

# 2024 base languages: every character knows Common plus two of their choice.
_BASE_LANGUAGE = "Common"
_LANGUAGE_CHOICE_COUNT = 2

@lru_cache(maxsize=1)
def _get_piper() -> PiperTTSClient:
    """Return a cached Piper client, resolving the binary next to the venv."""
    candidate = os.path.join(os.path.dirname(sys.executable), "piper")
    executable = candidate if os.path.exists(candidate) else "piper"
    return PiperTTSClient(executable_path=executable)


def _apply_pitch(wav: bytes, semitones: float) -> bytes:
    """Pitch-shift WAV audio by semitones using sox (Piper has no pitch control).

    Returns the input unchanged when the shift is negligible or sox is missing.
    """
    if abs(semitones) < 0.1 or shutil.which("sox") is None:
        return wav
    in_path = out_path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
            handle.write(wav)
            in_path = handle.name
        out_path = f"{in_path}.pitch.wav"
        result = subprocess.run(
            ["sox", in_path, out_path, "pitch", str(semitones * 100)],
            capture_output=True, timeout=30, check=False,
        )
        if result.returncode != 0 or not os.path.exists(out_path):
            return wav
        with open(out_path, "rb") as handle:
            return handle.read() or wav
    except (OSError, subprocess.TimeoutExpired):
        return wav
    finally:
        for path in (in_path, out_path):
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except OSError:
                    pass


def _build_arc_client(profile_name: str) -> AIClient | None:
    """Build an AIClient for a named model profile, or None if unconfigured.

    Args:
        profile_name: The model registry profile to use ("fast" / "creative").

    Returns:
        A configured AIClient, or None when no usable profile is available.
    """
    config = load_config()
    profile = (
        config.model_registry.get_profile(profile_name)
        or config.model_registry.get_active_profile()
    )
    if profile is None or not profile.base_url or not profile.model:
        return None
    # Local CPU inference of a large model takes minutes per call; the default
    # 30s AIClient timeout would abort every arc call. Allow a generous, tunable
    # timeout (ARC_AI_TIMEOUT seconds) so synthesis actually completes.
    return AIClient(
        api_key=os.getenv("OLLAMA_API_KEY", "") or config.ai.api_key,
        base_url=profile.base_url,
        model=profile.model,
        default_temperature=profile.temperature,
        default_max_tokens=max(profile.max_tokens, 2000),
        timeout=float(os.getenv("ARC_AI_TIMEOUT", "1800")),
    )


@lru_cache(maxsize=1)
def _get_arc_ai_client() -> AIClient | None:
    """Fast profile for the per-passage fan-out (quick, cheap, runs 100+ times)."""
    return _build_arc_client("fast")


@lru_cache(maxsize=1)
def _get_arc_aggregate_client() -> AIClient | None:
    """Profile for the final synthesis (relationships, goals, summary).

    Defaults to the ``creative`` (larger) profile for quality. Local qwen3
    "thinking" models always reason first (think:false is ignored over the
    OpenAI endpoint), so the token budget must outlast the reasoning
    (ARC_SYNTHESIS_MAX_TOKENS) and the timeout must allow a slow CPU model to
    finish (ARC_AI_TIMEOUT). Override with ``ARC_AGGREGATE_PROFILE=fast`` to
    trade quality for speed. Falls back to the fast client when the chosen
    profile is unconfigured.
    """
    profile = os.getenv("ARC_AGGREGATE_PROFILE", "creative")
    return _build_arc_client(profile) or _get_arc_ai_client()


@lru_cache(maxsize=1)
def _get_comfyui_client() -> ComfyUIClient | None:
    """Build the ComfyUI portrait client, or None when it is not configured.

    ComfyUI runs on the host (never in DDEV). Returns None when the feature is
    disabled or no base URL resolves, so the endpoint can answer 503 rather
    than raise.

    Returns:
        A configured ComfyUIClient, or None when unavailable.
    """
    comfyui = load_config().comfyui
    if not comfyui.is_configured():
        return None
    return ComfyUIClient(comfyui.get_base_url(), timeout=comfyui.timeout)


def _portrait_alt(profile: dict[str, Any]) -> str:
    """Build alt text for a generated portrait.

    Drupal's media image field sets ``alt_field_required: true``, so this must
    never return an empty string.

    Args:
        profile: The character profile used to build the portrait.

    Returns:
        Human-readable alt text describing the portrait.
    """
    name = str(profile.get("name") or "").strip() or "Character"
    descriptor = " ".join(
        str(profile.get(key) or "").strip()
        for key in ("lineage", "species", "character_class")
    ).split()
    if descriptor:
        return f"Portrait of {name}, a {' '.join(descriptor)}"
    return f"Portrait of {name}"


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


@_character_router.post("/resolve-background", response_model=ResolveBackgroundResponse)
def resolve_background_endpoint(req: ResolveBackgroundRequest) -> ResolveBackgroundResponse:
    """Resolve a background's granted data (abilities, feat, skills, etc.).

    Used to lazily populate an existing-but-empty background term from the
    rules wiki when it is selected during character creation.

    Args:
        req: ResolveBackgroundRequest with the background name.

    Returns:
        ResolveBackgroundResponse with the structured data, or null background
        when it cannot be resolved.
    """
    data = get_background(req.name)
    return ResolveBackgroundResponse(background=dict(data) if data is not None else None)


@_character_router.post("/skill-plan", response_model=SkillPlanResponse)
def skill_plan_endpoint(req: SkillPlanRequest) -> SkillPlanResponse:
    """Derive the class + species/subspecies plan for a character.

    The class portion (skills, tools, equipment, subclass) comes from the class
    taxonomy (the class plan), falling back to the JSON template + rules wiki.
    The species/subspecies trait skill grants/choices are layered on from the
    resolved abilities. Background grants are layered on by the caller.

    Args:
        req: SkillPlanRequest with class/level/species/subspecies.

    Returns:
        SkillPlanResponse with granted skills/tools, choice groups, the class
        equipment choices, and the subclass choice.
    """
    class_plan = get_class_plan(req.class_name, req.level)
    abilities = list(get_abilities("species", req.race, req.level))
    if req.subspecies:
        abilities.extend(get_abilities("subspecies", req.subspecies, req.level))
    traits = derive_trait_skills([dict(ability) for ability in abilities])
    language_choice = {
        "id": "languages", "label": "Languages", "count": _LANGUAGE_CHOICE_COUNT,
        "from": [], "kind": "language",
    }
    return SkillPlanResponse(
        granted=class_plan["granted_skills"] + traits["granted"],
        granted_tools=class_plan["granted_tools"],
        granted_languages=[_BASE_LANGUAGE] + class_plan["granted_languages"],
        choices=class_plan["skill_choices"] + class_plan["tool_choices"]
        + traits["choices"] + [language_choice],
        equipment_choices=class_plan["equipment_choices"],
        subclass=class_plan["subclass"],
        source=class_plan["source"],
    )


@_character_router.post("/equipment/describe", response_model=EquipmentDescribeResponse)
def equipment_describe_endpoint(req: EquipmentDescribeRequest) -> EquipmentDescribeResponse:
    """Resolve prose descriptions and item types for equipment names.

    Looks each name up in the rules-wiki equipment catalogue so newly created
    item nodes can be given an accurate ``field_description`` and type. Unmatched
    names are omitted.

    Args:
        req: EquipmentDescribeRequest with the item names to resolve.

    Returns:
        EquipmentDescribeResponse mapping each matched name to its info.
    """
    resolved = get_equipment_descriptions(req.names)
    items = {
        name: EquipmentItemInfo(description=info["description"], item_type=info["item_type"])
        for name, info in resolved.items()
    }
    return EquipmentDescribeResponse(items=items)


def _safe_int(value: Any, default: int) -> int:
    """Coerce an AI-supplied value to int, falling back on non-numeric input."""
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _build_arc_response(result: dict[str, Any]) -> ArcAnalysisResponse:
    """Map an arc result dict into the ArcAnalysisResponse model."""
    metrics = {
        key: ArcMetricModel(
            label=str(metric.get("label", key)),
            series=[float(v) for v in metric.get("series", [])],
            direction=str(metric.get("direction", "stasis")),
            obs=str(metric.get("obs", "")),
        )
        for key, metric in result["metrics"].items()
    }
    relationships = [
        ArcRelationshipModel(
            target=str(rel.get("target", "")),
            type=str(rel.get("type", "neutral")),
            strength=_safe_int(rel.get("strength", 5), 5),
            trust=_safe_int(rel.get("trust", 5), 5),
            note=str(rel.get("note", "")),
        )
        for rel in result["relationships"]
        if str(rel.get("target", "")).strip()
    ]
    goals = [
        ArcGoalModel(
            description=str(goal.get("description", "")),
            status=str(goal.get("status", "active")),
            progress=_safe_int(goal.get("progress", 0), 0),
        )
        for goal in result["goals"]
        if str(goal.get("description", "")).strip()
    ]
    return ArcAnalysisResponse(
        direction=result["direction"],
        stage=result["stage"],
        summary=result["summary"],
        stories_analyzed=result["stories_analyzed"],
        updated_at=result["updated_at"],
        metrics=metrics,
        relationships=relationships,
        goals=goals,
    )


@_character_router.post("/arc", response_model=ArcAnalysisResponse)
def character_arc_endpoint(req: ArcAnalysisRequest) -> ArcAnalysisResponse:
    """Analyze a character's arc across stories in one request (small campaigns).

    Runs every story then aggregates. For many stories prefer the two-step
    ``/character/arc/story`` + ``/character/arc/aggregate`` path so each request
    is a single model call and progress can be shown.

    Args:
        req: ArcAnalysisRequest with the character name and ordered story texts.

    Returns:
        An ArcAnalysisResponse with the structured arc.
    """
    stories = [
        {"content": s.content, "title": s.title, "story_number": s.story_number}
        for s in req.stories
    ]
    result = analyze_character_arc(
        stories,
        req.character_name,
        campaign_name=req.campaign_name,
        ai_client=_get_arc_ai_client(),
    )
    return _build_arc_response(result)


@_character_router.post("/arc/story", response_model=ArcDataPointModel)
def character_arc_story_endpoint(req: ArcStoryRequest) -> ArcDataPointModel:
    """Analyze a single story into one arc data point (one model call).

    Args:
        req: ArcStoryRequest with the character name and one story's text.

    Returns:
        The story's ArcDataPointModel, to be collected and posted to
        ``/character/arc/aggregate``.
    """
    analyzer = ArcAnalyzer(ai_client=_get_arc_ai_client(), pronouns=req.pronouns)
    data_point = analyze_story_datapoint(
        analyzer,
        req.content,
        req.character_name,
        title=req.title,
        story_number=req.story_number,
    )
    return ArcDataPointModel(**data_point.to_dict())


@_character_router.post("/arc/aggregate", response_model=ArcAnalysisResponse)
def character_arc_aggregate_endpoint(req: ArcAggregateRequest) -> ArcAnalysisResponse:
    """Aggregate stored per-story data points into the full character arc.

    Args:
        req: ArcAggregateRequest with the character name and per-story points.

    Returns:
        An ArcAnalysisResponse with the structured arc.
    """
    data_points = [ArcDataPoint.from_dict(dp.model_dump()) for dp in req.data_points]
    result = aggregate_arc(
        data_points,
        req.character_name,
        campaign_name=req.campaign_name,
        ai_client=_get_arc_aggregate_client(),
        pronouns=req.pronouns,
    )
    return _build_arc_response(result)


@_character_router.post("/arc/synthesize", response_model=ArcSynthesisResponse)
def character_arc_synthesize_endpoint(req: ArcSynthesisRequest) -> ArcSynthesisResponse:
    """Synthesize an arc from stored per-story analysis texts.

    Reads the persisted per-story analyses (rather than re-analysing raw stories)
    to extract relationships and goals and narrate the summary. This is what lets
    a run resume and keeps the synthesis reading stored text instead of holding
    every story in memory.

    Args:
        req: ArcSynthesisRequest with the character name and stored story texts.

    Returns:
        An ArcSynthesisResponse with summary, relationships, and goals.
    """
    analyzer = ArcAnalyzer(ai_client=_get_arc_aggregate_client(), pronouns=req.pronouns)
    narrative = "\n\n".join(text for text in req.story_texts if text)
    relationships_raw = analyzer.analyze_relationships(narrative, req.character_name)
    goals_raw = analyzer.analyze_goals(narrative, req.character_name)
    summary = analyzer.narrate_arc(
        req.character_name, narrative, facts_block({}, relationships_raw, goals_raw)
    )
    relationships = [
        ArcRelationshipModel(
            target=str(rel.get("target", "")),
            type=str(rel.get("type", "neutral")),
            strength=_safe_int(rel.get("strength", 5), 5),
            trust=_safe_int(rel.get("trust", 5), 5),
            note=str(rel.get("note", "")),
        )
        for rel in relationships_raw
        if str(rel.get("target", "")).strip()
    ]
    goals = [
        ArcGoalModel(
            description=str(goal.get("description", "")),
            status=str(goal.get("status", "active")),
            progress=_safe_int(goal.get("progress", 0), 0),
        )
        for goal in goals_raw
        if str(goal.get("description", "")).strip()
    ]
    return ArcSynthesisResponse(
        summary=summary, relationships=relationships, goals=goals
    )


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


@_character_router.post("/portrait", response_model=PortraitResponse)
def character_portrait_endpoint(req: PortraitRequest) -> PortraitResponse:
    """Generate a character portrait with local ComfyUI, returned as base64 PNG.

    Phase A is text-to-image only: the prompt is built from the character
    profile. Models are unloaded afterwards so the SD checkpoint does not stay
    resident alongside other local AI services.

    Args:
        req: PortraitRequest with the character profile and optional seed/size.

    Returns:
        PortraitResponse with the base64 PNG, the seed used, prompt, and alt text.

    Raises:
        HTTPException: 503 when ComfyUI is disabled, unconfigured, or
            unreachable; 500 when generation fails or times out.
    """
    comfyui = load_config().comfyui
    if not comfyui.enabled:
        raise HTTPException(
            status_code=503,
            detail="ComfyUI portrait generation is disabled (set COMFYUI_ENABLED=true)",
        )

    client = _get_comfyui_client()
    if client is None:
        raise HTTPException(
            status_code=503,
            detail="ComfyUI has no reachable base URL (set COMFYUI_HOST/COMFYUI_PORT)",
        )
    if not comfyui.assets.checkpoint:
        raise HTTPException(
            status_code=503,
            detail="No Stable Diffusion checkpoint configured (set COMFYUI_CHECKPOINT)",
        )
    if not client.is_available():
        raise HTTPException(
            status_code=503, detail="ComfyUI is not reachable on the host"
        )

    positive, negative = build_portrait_prompt(req.profile)
    seed = req.seed if req.seed is not None else random.randrange(2**31)

    render = RenderSettings()
    if req.width is not None:
        render.width = req.width
    if req.height is not None:
        render.height = req.height

    workflow = txt2img_workflow(
        Txt2ImgParams(
            checkpoint=comfyui.assets.checkpoint,
            positive=positive,
            negative=negative,
            seed=seed,
            render=render,
        )
    )

    try:
        png = client.generate(workflow)
    finally:
        # Unload models between runs: this box is CPU-only and an SD checkpoint
        # left resident alongside Ollama/DDEV is the top OOM risk.
        client.free()

    if png is None:
        raise HTTPException(
            status_code=500, detail="ComfyUI generation failed or timed out"
        )

    return PortraitResponse(
        image_base64=base64.b64encode(png).decode("ascii"),
        seed=seed,
        prompt=positive,
        alt=_portrait_alt(req.profile),
    )


@_tts_router.post("/speak")
def tts_speak_endpoint(req: TtsRequest) -> Response:
    """Synthesise speech from text with a Piper voice, returning WAV audio.

    Args:
        req: TtsRequest with the text, optional voice id, and speed.

    Returns:
        A ``audio/wav`` response with the synthesised audio.

    Raises:
        HTTPException: 503 when Piper is unavailable, 400 for empty text, or
            500 when synthesis fails.
    """
    text = req.text.strip()
    if text == "":
        raise HTTPException(status_code=400, detail="text must not be empty")
    piper = _get_piper()
    if not piper.is_available():
        raise HTTPException(status_code=503, detail="Piper TTS is not installed")
    voice = req.voice_id.strip() or get_narrator_voice_id()
    if not piper.is_voice_available(voice):
        voice = get_narrator_voice_id()
    audio = piper.synthesize(text, voice, speed=req.speed)
    if audio is None:
        raise HTTPException(status_code=500, detail="Speech synthesis failed")
    audio = _apply_pitch(audio, req.pitch)
    return Response(content=audio, media_type="audio/wav")


app.include_router(_search_router)
app.include_router(_eval_router)
app.include_router(_character_router)
app.include_router(_tts_router)
