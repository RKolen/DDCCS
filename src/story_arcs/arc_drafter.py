"""Draft a story arc from the sessions a campaign has already played.

A campaign that predates the arc feature has stories but no arc, so the arc
screen has nothing to show and relationship suggestion has nothing to hang on.
This reads the per-session recaps the campaign already stores and proposes the
arc they add up to.

The result is a proposal, never a write: the console reviews and edits it, and
only an explicit accept creates the node.
"""

from typing import Any, Dict, List, Optional, Sequence

from src.ai.ai_client import AIClientProtocol
from src.story_arcs.arc_draft_types import ArcDraft, ArcRoster, SessionRecap
from src.story_arcs.recap_prompt import session_preamble, usable_recaps
from src.utils.ai_json import extract_json_object

MAX_ROSTER = 25
MAX_DRAFT_TOKENS = 1500

# Beyond this the model is inventing rather than reading the campaign.
MAX_KEY_NPCS = 10

_SYSTEM_TASK = (
    "You are a D&D campaign archivist. Given a campaign's sessions in order, "
    "name the story arc they form and describe it. Read the arc out of what "
    "actually happened - do not invent events, places, or characters that the "
    "recaps do not mention."
)


def build_draft_prompt(
    campaign_name: str,
    recaps: Sequence[SessionRecap],
    npc_names: Sequence[str],
) -> str:
    """Build the prompt that turns session recaps into an arc proposal.

    Args:
        campaign_name: The campaign the arc belongs to.
        recaps: Session recaps, in play order.
        npc_names: NPCs the model may name as central to the arc.

    Returns:
        The prompt text.
    """
    blocks = session_preamble(_SYSTEM_TASK, campaign_name, recaps)
    if npc_names:
        roster = ", ".join(npc_names[:MAX_ROSTER])
        blocks.extend(
            [
                "",
                f"NPCs on record: {roster}",
                "Name central NPCs only from that list; never invent one.",
            ]
        )
    blocks.extend(
        [
            "",
            "Reply with JSON only:",
            '{"title": "<arc name>", '
            '"premise": "<two or three sentences on what this arc is about>", '
            '"overall_plot": ["<act one>", "<act two>", "<act three>"], '
            '"faction": "<the antagonist faction, or empty>", '
            '"key_npcs": ["<name>"]}',
            "",
            "The premise is what the arc is about, not a session-by-session "
            "recap. Each act line is one sentence. Leave a field empty rather "
            "than guessing at it.",
        ]
    )
    return "\n".join(blocks)


def _as_lines(value: Any) -> str:
    """Render a model's act spine as one line per act.

    Args:
        value: A list of act strings, or already-joined prose.

    Returns:
        The spine as newline-separated text.
    """
    if isinstance(value, list):
        lines = [str(item).strip() for item in value]
        return "\n".join(line for line in lines if line)
    return str(value or "").strip()


def _clean_names(value: Any, allowed: Sequence[str], limit: int) -> List[str]:
    """Keep only the names the model was offered, in the order it gave them.

    A name the roster does not contain cannot be resolved to a character node,
    so it is dropped here rather than stored half-anchored.

    Args:
        value: The model's list of names.
        allowed: The names that were offered.
        limit: Maximum names to keep.

    Returns:
        The recognised names, deduplicated.
    """
    if not isinstance(value, list):
        return []
    known = {name.strip().lower(): name for name in allowed if name.strip()}
    out: List[str] = []
    for item in value:
        match = known.get(str(item).strip().lower())
        if match is not None and match not in out:
            out.append(match)
        if len(out) >= limit:
            break
    return out


def parse_draft(
    response: str,
    party_names: Sequence[str],
    npc_names: Sequence[str],
) -> Optional[ArcDraft]:
    """Parse a model response into a reviewable arc draft.

    Args:
        response: The raw model response.
        party_names: The party the arc covers; carried through unchanged.
        npc_names: The NPCs the model was allowed to name.

    Returns:
        The draft, or None when the response has no usable title and premise.
    """
    payload = extract_json_object(response)
    if payload is None:
        return None

    draft = ArcDraft(
        title=str(payload.get("title", "")).strip(),
        premise=str(payload.get("premise", "")).strip(),
        overall_plot=_as_lines(payload.get("overall_plot")),
        faction=str(payload.get("faction", "")).strip(),
        roster=ArcRoster(
            party=[name for name in party_names if name.strip()],
            npcs=_clean_names(payload.get("key_npcs"), npc_names, MAX_KEY_NPCS),
        ),
    )
    return draft if draft.is_usable() else None


def draft_arc(
    ai_client: Optional[AIClientProtocol],
    campaign_name: str,
    recaps: Sequence[SessionRecap],
    roster: ArcRoster,
    num_ctx: int = 0,
) -> Optional[ArcDraft]:
    """Propose the arc a campaign's played sessions add up to.

    Args:
        ai_client: The AI client, or None when AI is unavailable.
        campaign_name: The campaign the arc belongs to.
        recaps: Session recaps, in play order.
        roster: The party the arc covers, and the NPCs the model may name.
        num_ctx: Context window to request. A campaign's recaps run well past
            Ollama's 2048-token default, and the overflow is dropped silently -
            which produced arcs describing only the first few sessions.

    Returns:
        The draft, or None when AI is unavailable or the model returns nothing
        usable.
    """
    party_names = roster.party
    npc_names = roster.npcs
    ordered = usable_recaps(recaps)
    if ai_client is None or not ordered:
        return None

    prompt = build_draft_prompt(campaign_name, ordered, npc_names)
    messages: List[Dict[str, str]] = [{"role": "user", "content": prompt}]
    try:
        response = ai_client.chat_completion(
            messages,
            max_tokens=MAX_DRAFT_TOKENS,
            json_mode=True,
            disable_thinking=True,
            num_ctx=num_ctx,
        )
    except (RuntimeError, OSError, ValueError):
        return None
    return parse_draft(response, party_names, npc_names)
