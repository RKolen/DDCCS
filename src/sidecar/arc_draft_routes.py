"""Story-arc drafting routes for the FastAPI sidecar.

Exposes ``/arc-draft/propose`` (the arc a campaign's sessions add up to) and
``/arc-draft/npcs`` (the cast those sessions name). Two calls rather than one:
asking a single prompt to both write an arc and enumerate a cast gets a worse
answer at both, and the cast is what lets the console offer NPCs that do not
exist yet.

Nothing is written - the console reviews and edits, and only an explicit accept
creates anything.
"""

import os
from functools import lru_cache
from typing import Optional

from fastapi import APIRouter

from src.ai.ai_client import AIClient
from src.sidecar.ai_profiles import build_profile_client
from src.sidecar.models import (
    ArcDraftModel,
    ArcDraftRequest,
    ArcDraftResponse,
    DiscoveredNpcModel,
    NpcExtractRequest,
    NpcExtractResponse,
)
from src.story_arcs.arc_draft_types import ArcRoster, SessionRecap
from src.story_arcs.arc_drafter import draft_arc
from src.story_arcs.npc_extractor import extract_npcs

router = APIRouter(prefix="/arc-draft", tags=["arc-draft"])


@lru_cache(maxsize=1)
def get_arc_draft_ai_client() -> Optional[AIClient]:
    """Return the AI client used for arc drafting.

    Must be an instruct model, for the same reason relationship suggestion
    must: a local "thinking" model ignores ``think:false`` over the OpenAI
    endpoint and spends the whole budget reasoning. Override with
    ``ARC_DRAFT_PROFILE``.

    Returns:
        A configured AIClient, or None when no profile is usable.
    """
    return build_profile_client(os.getenv("ARC_DRAFT_PROFILE", "creative"))


def get_arc_draft_num_ctx() -> int:
    """Return the context window to request for a recap-reading pass.

    A campaign's recaps run to roughly 1900 tokens before the answer is even
    budgeted, and Ollama's default window is 2048: the overflow is dropped
    without a word, which is why a fourteen-session campaign produced an arc
    describing only its first five. Sized for the whole span rather than left
    to the default. Override with ``ARC_DRAFT_NUM_CTX``; a wide window costs
    memory on a CPU-only host, so raise it deliberately.

    Returns:
        The context window in tokens.
    """
    raw = os.getenv("ARC_DRAFT_NUM_CTX", "8192")
    try:
        return max(int(raw), 0)
    except ValueError:
        return 8192


@router.post("/propose", response_model=ArcDraftResponse)
def arc_draft_propose_endpoint(req: ArcDraftRequest) -> ArcDraftResponse:
    """Propose the story arc a campaign's played sessions add up to.

    Args:
        req: The campaign name, its session recaps, and the rosters the draft
            may name.

    Returns:
        The proposed arc, or an empty draft when nothing usable came back.
    """
    draft = draft_arc(
        get_arc_draft_ai_client(),
        req.campaign_name,
        [SessionRecap.from_dict(recap.model_dump()) for recap in req.recaps],
        ArcRoster(party=list(req.party), npcs=list(req.npcs)),
        num_ctx=get_arc_draft_num_ctx(),
    )
    if draft is None:
        return ArcDraftResponse(draft=None)
    return ArcDraftResponse(draft=ArcDraftModel(**draft.to_dict()))


@router.post("/npcs", response_model=NpcExtractResponse)
def arc_draft_npcs_endpoint(req: NpcExtractRequest) -> NpcExtractResponse:
    """Read the NPC cast out of a campaign's played sessions.

    Args:
        req: The campaign name, its session recaps, the party to exclude, and
            the characters already on record.

    Returns:
        The discovered cast, each marked known when it matched the roster.
    """
    npcs = extract_npcs(
        get_arc_draft_ai_client(),
        req.campaign_name,
        [SessionRecap.from_dict(recap.model_dump()) for recap in req.recaps],
        ArcRoster(party=list(req.party), npcs=list(req.known)),
        num_ctx=get_arc_draft_num_ctx(),
    )
    return NpcExtractResponse(npcs=[DiscoveredNpcModel(**npc.to_dict()) for npc in npcs])
