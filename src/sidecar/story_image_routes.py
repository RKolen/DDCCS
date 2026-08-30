"""Story-scene illustration routes for the FastAPI sidecar.

``/story/events`` reads key visual moments out of a session body in bounded
chunks. ``/story/scene`` analyses one picked excerpt, then renders a landscape
illustration with at most two IPAdapter leads and staggered ReActor swaps.
Nothing is written - Drupal's queued job stores the PNG for review.
"""

import base64
import logging
import os
import random
from functools import lru_cache
from typing import List, Optional, Sequence, Tuple

from fastapi import APIRouter, HTTPException

from src.ai.ai_client import AIClient
from src.ai.comfyui_client import ComfyUIClient
from src.ai.ollama_admin import unload_ollama_models
from src.config.config_loader import load_config
from src.sidecar.ai_profiles import build_profile_client
from src.sidecar.comfyui_guard import comfyui_unavailable, raise_unless_ready
from src.sidecar.models import (
    StoryEventModel,
    StoryEventsRequest,
    StoryEventsResponse,
    StoryRosterPerson,
    StoryScenePerson,
    StorySceneRequest,
    StorySceneResponse,
)
from src.story_images.appearance import fill_appearances
from src.story_images.events import extract_events
from src.story_images.framing import SceneFraming
from src.story_images.render import SceneRenderRequest, render_scene
from src.story_images.scene_prompt import build_scene_prompt
from src.story_images.shot import analyze_shot
from src.story_images.types import RosterEntry, ShotAnalysis, ShotPerson, apply_roster

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/story", tags=["story-images"])


@lru_cache(maxsize=1)
def get_story_image_ai_client() -> Optional[AIClient]:
    """Return the AI client used for event extraction and shot analysis.

    Must be an instruct model, same reason as ``/relations/suggest``: a local
    "thinking" model returns empty content over the OpenAI endpoint, which
    reads here as a story with no events. Override with ``STORY_IMAGE_PROFILE``.

    Returns:
        A configured AIClient, or None when no profile is usable.
    """
    return build_profile_client(os.getenv("STORY_IMAGE_PROFILE", "creative"))


def _roster(entries: Sequence[StoryRosterPerson]) -> List[RosterEntry]:
    """Convert request roster rows into RosterEntry values.

    Args:
        entries: Pydantic roster rows.

    Returns:
        Roster entries with blank names dropped.
    """
    out: List[RosterEntry] = []
    for row in entries:
        entry = RosterEntry.from_dict(row.model_dump())
        if entry.name:
            out.append(entry)
    return out


def _people_from_request(
    rows: List[StoryScenePerson], roster: List[RosterEntry]
) -> List[ShotPerson]:
    """Build the in-frame list the operator confirmed.

    Args:
        rows: Request people, already filtered by the console.
        roster: Campaign roster, used to fill portraits when the row omitted
            them.

    Returns:
        Shot people with roster fields applied.
    """
    out: List[ShotPerson] = []
    for row in rows:
        person = apply_roster(ShotPerson.from_dict(row.model_dump()), roster)
        if person.name:
            out.append(person)
    return out


@router.post("/events", response_model=StoryEventsResponse)
def story_events_endpoint(req: StoryEventsRequest) -> StoryEventsResponse:
    """Extract selectable key events from a story body.

    Args:
        req: The story body, title, and campaign roster (roster is unused here
            but accepted so the job payload can be shared with /scene).

    Returns:
        The event list, empty when nothing usable came back.
    """
    events = extract_events(get_story_image_ai_client(), req.body, req.title)
    return StoryEventsResponse(
        events=[
            StoryEventModel(
                title=event.title, one_line=event.one_line, excerpt=event.excerpt
            )
            for event in events
        ]
    )


def _analyse_event(
    req: StorySceneRequest, roster: List[RosterEntry]
) -> Tuple[ShotAnalysis, List[ShotPerson], str, str]:
    """Run shot analysis and build the SD prompts.

    Args:
        req: The scene request.
        roster: Campaign characters for name matching.

    Returns:
        (analysis, people, positive_prompt, negative_prompt).
    """
    analysis = analyze_shot(
        get_story_image_ai_client(), req.excerpt, req.title, roster
    )
    people = _people_from_request(list(req.people), roster)
    if not people:
        people = analysis.people
    config = load_config()
    # A blank record leaves only lineage and class in the prompt, so anything
    # the portrait shows and nobody wrote down is lost. Caption it instead.
    people = fill_appearances(people, config.comfyui, config.drupal.ca_bundle)
    positive, negative = build_scene_prompt(
        analysis, people, SceneFraming(shot=req.shot, angle=req.angle)
    )
    return analysis, people, positive, negative


def _scene_alt(title: str, action: str) -> str:
    """Alt text from the event title and analysed action.

    Args:
        title: The event title.
        action: The analysed action, possibly empty.

    Returns:
        Alt text suitable for a Drupal media image field.
    """
    alt = title.strip() or "Story illustration"
    if action:
        return f"{alt}: {action}"
    return alt


@router.post("/scene", response_model=StorySceneResponse)
def story_scene_endpoint(req: StorySceneRequest) -> StorySceneResponse:
    """Analyse one event and render a scene illustration.

    Ollama runs first (shot analysis). It is unloaded before ComfyUI loads the
    checkpoint. ReActor swaps, when configured, run one face at a time with
    ``/free`` between them.

    Args:
        req: The event excerpt, optional confirmed people, and roster.

    Returns:
        The base64 PNG plus prompt metadata.

    Raises:
        HTTPException: 503 when ComfyUI is disabled or unreachable; 500 when
            generation fails; 422 when the excerpt is empty (Pydantic).
    """
    comfyui = load_config().comfyui
    raw_client = None
    if comfyui.get_base_url():
        raw_client = ComfyUIClient(comfyui.get_base_url(), timeout=comfyui.scene_timeout)
    client = raise_unless_ready(
        comfyui_unavailable(
            comfyui,
            raw_client,
            "ComfyUI scene generation is disabled (set COMFYUI_ENABLED=true)",
        ),
        raw_client,
    )

    roster = _roster(list(req.roster))
    analysis, people, positive, negative = _analyse_event(req, roster)
    seed = req.seed if req.seed is not None else random.randrange(2**31)
    alt = _scene_alt(req.title, analysis.action)

    if comfyui.ollama_url:
        freed = unload_ollama_models(comfyui.ollama_url)
        if freed:
            logger.info("Unloaded %d Ollama model(s) before scene generation", freed)

    result = render_scene(
        SceneRenderRequest(
            client=client,
            comfyui=comfyui,
            positive=positive,
            negative=negative,
            seed=seed,
            people=people,
            ca_bundle=load_config().drupal.ca_bundle,
        )
    )
    if result.png is None:
        raise HTTPException(
            status_code=500, detail="ComfyUI generation failed or timed out"
        )

    return StorySceneResponse(
        image_base64=base64.b64encode(result.png).decode("ascii"),
        seed=seed,
        prompt=positive,
        alt=alt,
        setting=analysis.setting,
        action=analysis.action,
        mood=analysis.mood,
        used_ipadapter=len(result.leads),
        lead_faces=result.leads,
        swapped_faces=result.swapped,
        people=[StoryScenePerson(**person.to_dict()) for person in people],
    )
