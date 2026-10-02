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
from src.ai.comfyui_admin import restart_comfyui
from src.ai.comfyui_client import ComfyUIClient
from src.ai.ollama_admin import unload_ollama_models
from src.config.config_loader import load_config
from src.config.config_types import ComfyUIConfig
from src.sidecar.ai_profiles import build_profile_client
from src.sidecar.comfyui_guard import comfyui_unavailable, raise_unless_ready
from src.sidecar.models import (
    StoryEventModel,
    StoryEventsRequest,
    StoryEventsResponse,
    StoryRosterPerson,
    StoryLimb,
    StoryPlacement,
    StorySceneOption,
    StoryScenePerson,
    StorySceneRequest,
    StorySceneResponse,
    StoryStageRequest,
    StoryStageResponse,
    StoryStagingResponse,
)
from src.story_images.appearance import fill_appearances
from src.story_images.events import extract_events
from src.story_images.framing import ANGLES, SceneFraming
from src.story_images.render import (
    RegionMode,
    SceneRenderRequest,
    ScenePrompts,
    render_scene,
)
from src.story_images.scene_prompt import (
    build_environment_prompt,
    build_scene_prompt,
)
from src.story_images.pose import (
    LIMB_JOINTS,
    POSE_VARIANTS,
    TOWARD_SIGN,
    figure_layout,
    openpose_png,
    pose_for_index,
)
from src.story_images.regions import Placement, Stance, default_placements, lay_out
from src.story_images.shot import analyze_shot
from src.story_images.staging import (
    MOODS,
    SETTINGS,
    resolve_mood,
    resolve_setting,
)
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


def _staged(rows: Sequence[StoryPlacement]) -> List[Placement]:
    """Turn request placements into layout placements.

    Args:
        rows: Placements as the console sent them.

    Returns:
        The same staging in the layout's own type.
    """
    return [Placement(name=row.name, lateral=row.lateral, depth=row.depth,
                      stance=Stance(
                          pose=row.pose, facing=row.facing, toward=row.toward,
                          limbs={limb.joint: (limb.x, limb.y) for limb in row.limbs},
                      ),
                      order=row.order)
            for row in rows]


def _skeleton(spot: Placement) -> List[StoryLimb]:
    """Every draggable joint of one staged figure, where it is drawn.

    Args:
        spot: The figure's staging, stance already dealt.

    Returns:
        One entry per limb joint, in layout units.
    """
    layout = figure_layout(spot.stance)
    return [StoryLimb(joint=name, x=layout[joint][0], y=layout[joint][1])
            for name, joint in LIMB_JOINTS.items()]


@router.post("/stage", response_model=StoryStageResponse)
def story_stage_endpoint(req: StoryStageRequest) -> StoryStageResponse:
    """Draw the staging as a skeleton, before anything is rendered.

    A scene costs minutes and a restart of ComfyUI; the staging that decides
    who stands where costs nothing to look at. Returning it as an image plus
    the boxes it was drawn from lets the console show it, let the operator
    move people, and send back the same numbers the render will use - so
    what was previewed is what gets painted.

    Args:
        req: The cast, the shot, and any staging already chosen.

    Returns:
        The skeleton PNG, the resolved staging, and each figure's box.
    """
    comfyui = load_config().comfyui
    width, height = comfyui.assets.scene.width, comfyui.assets.scene.height
    people = [ShotPerson.from_dict(row.model_dump()) for row in req.people
              if row.name]
    if not people:
        raise HTTPException(status_code=422, detail="No one is in the shot")

    chosen = {row.name: row for row in req.placements}
    staged = [
        chosen.get(person.name) or StoryPlacement(
            name=person.name, lateral=fallback.lateral, depth=fallback.depth,
        )
        for person, fallback in zip(people, default_placements(people))
    ]
    # An unposed character is dealt a stance by the renderer, so the preview
    # has to deal the same one. Leaving it blank drew everybody standing and
    # promised a staging the render would not paint.
    for index, row in enumerate(staged):
        if not row.pose:
            row.pose = pose_for_index(index)
    # The same placements for both, so the preview cannot draw a stance or a
    # facing the render will not paint.
    layout = _staged(staged)
    regions = lay_out(people, width, height, req.shot, layout)
    png = openpose_png(width, height, regions, layout)
    boxes = {r.name: [r.left, r.top, r.width, r.height] for r in regions}
    for row, spot in zip(staged, layout):
        row.box = boxes.get(row.name, [])
        row.skeleton = _skeleton(spot)
    return StoryStageResponse(
        image_base64=base64.b64encode(png).decode("ascii"),
        width=width, height=height, placements=staged,
        poses=list(POSE_VARIANTS), facings=list(ANGLES),
        towards=list(TOWARD_SIGN),
    )


@router.get("/staging", response_model=StoryStagingResponse)
def story_staging_endpoint() -> StoryStagingResponse:
    """List the settings and moods a scene can be staged with.

    Served rather than hardcoded in the console so the two cannot drift:
    a setting the console offers and the renderer does not know would fall
    through to free text and quietly render something else.

    Returns:
        Every named setting with its composed caption, and every mood with
        its tone clause.
    """
    return StoryStagingResponse(
        settings=[
            StorySceneOption(name=name, description=setting.describe())
            for name, setting in SETTINGS.items()
        ],
        moods=[
            StorySceneOption(name=name, description=text)
            for name, text in MOODS.items()
        ],
    )


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
    req: StorySceneRequest, roster: List[RosterEntry], framing: SceneFraming
) -> Tuple[ShotAnalysis, List[ShotPerson], str, str]:
    """Run shot analysis and build the SD prompts.

    Args:
        req: The scene request.
        roster: Campaign characters for name matching.
        framing: Shot type and camera angle chosen by the operator.

    Returns:
        (analysis, people, positive_prompt, negative_prompt).
    """
    analysis = analyze_shot(
        get_story_image_ai_client(), req.excerpt, req.title, roster
    )
    _stage(analysis, req)
    people = _people_from_request(list(req.people), roster)
    if not people:
        people = analysis.people
    else:
        _fill_actions(people, analysis.people)
    config = load_config()
    # A blank record leaves only lineage and class in the prompt, so anything
    # the portrait shows and nobody wrote down is lost. Caption it instead.
    people = fill_appearances(people, config.comfyui, config.drupal.ca_bundle)
    positive, negative = build_scene_prompt(analysis, people, framing)
    return analysis, people, positive, negative


def _stage(analysis: ShotAnalysis, req: StorySceneRequest) -> None:
    """Let the operator's setting and mood outrank the analysed ones.

    Both are left alone when nothing was chosen, so a scene nobody has
    staged still renders from the analysis as before.

    Args:
        analysis: The shot analysis, modified in place.
        req: The scene request, carrying any operator choices.
    """
    if req.setting.strip():
        analysis.setting = resolve_setting(req.setting).describe()
    if req.mood.strip():
        analysis.mood = resolve_mood(req.mood)


def _fill_actions(
    people: List[ShotPerson], analysed: Sequence[ShotPerson]
) -> None:
    """Give anyone the operator left blank the action the analysis wrote.

    The console sends a row per person whether or not it has an opinion
    about what they are doing, so an untouched row would otherwise erase
    the analysed action rather than defer to it.

    Args:
        people: The confirmed cast, modified in place.
        analysed: People the shot analysis named.
    """
    written = {other.name.lower(): other.action for other in analysed}
    for person in people:
        if not person.action:
            person.action = written.get(person.name.lower(), "")


def _recycle_comfyui(comfyui: ComfyUIConfig) -> None:
    """Restart a locally managed ComfyUI now this render is off it.

    Synchronous on purpose. ComfyUI keeps the memory a render grew until
    the process ends, so the next job would find a box with no room; doing
    this before the response returns means the next job finds a clean one
    instead. The wait is seconds against a render measured in minutes.

    Off unless COMFYUI_RESTART_AFTER_SCENE is set, and never done to a
    ComfyUI this deployment did not start.

    Args:
        comfyui: Loaded ComfyUI config.
    """
    if not comfyui.local.restart_after_scene:
        return
    if not restart_comfyui(comfyui):
        logger.warning(
            "ComfyUI was not restarted after the render; the next one may "
            "find no memory. Check COMFYUI_DIR and %s",
            "scripts/restart-comfyui.sh",
        )


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
    framing = SceneFraming(shot=req.shot, angle=req.angle)
    analysis, people, positive, negative = _analyse_event(req, roster, framing)
    seed = req.seed if req.seed is not None else random.randrange(2**31)
    alt = _scene_alt(req.title, analysis.action)

    if comfyui.ollama_url:
        freed = unload_ollama_models(comfyui.ollama_url)
        if freed:
            logger.info("Unloaded %d Ollama model(s) before scene generation", freed)

    logger.info(
        "Scene render: mode=%s shot=%s angle=%s people=%d likeness=%d",
        "regions" if req.regions else "whole-scene",
        req.shot,
        req.angle,
        len(people),
        sum(1 for person in people if person.use_likeness),
    )
    result = render_scene(
        SceneRenderRequest(
            client=client,
            comfyui=comfyui,
            prompts=ScenePrompts(
                positive=positive,
                negative=negative,
                environment=build_environment_prompt(analysis, framing),
            ),
            seed=seed,
            people=people,
            ca_bundle=load_config().drupal.ca_bundle,
            region=RegionMode(
                enabled=req.regions,
                shot=req.shot,
                angle_terms=framing.terms()[0],
                placements=_staged(req.placements),
            ),
        )
    )
    # Before the failure check, not after: a render that died part-way
    # through has still grown the arena, and that is the case where the
    # next one is most likely to be killed for want of memory.
    _recycle_comfyui(comfyui)

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
