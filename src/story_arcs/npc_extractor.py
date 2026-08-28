"""Read a campaign's NPC cast out of its session recaps.

The NPC roster is not the cast. A campaign ported from somewhere else has
stories full of innkeepers, patrons, and antagonists nobody has ever created a
character node for, so offering the arc only the NPCs already on record offers
it people who never appear in the story.

This asks one question of the recaps - who are the NPCs - and reports each with
a one-line role. Names that already match a character are marked known; the
rest are what the console offers to create.
"""

from typing import Any, Dict, List, Optional, Sequence

from src.ai.ai_client import AIClientProtocol
from src.story_arcs.arc_draft_types import (
    ArcRoster,
    DiscoveredNpc,
    MAX_DISCOVERED_NPCS,
    SessionRecap,
)
from src.story_arcs.recap_prompt import session_preamble, usable_recaps
from src.utils.ai_json import extract_json_object
from src.utils.string_utils import clip_to_budget

MAX_ROLE_CHARS = 200
MAX_EXTRACT_TOKENS = 1200

# Sessions per call. One call over a whole campaign returns the handful it
# finds most salient, which in practice means the earliest: a fourteen-session
# run named nobody from the last six. A window gets its own attention and its
# own output budget, so the innkeeper in session seven is still found.
RECAPS_PER_CALL = 4

_TASK = (
    "You are a D&D campaign archivist. List the non-player characters who "
    "appear in these sessions - the people the party met, hired, fought, or "
    "were sent by. Do not list the player characters. Do not list places, "
    "groups, ships, or items. Only name someone the recaps actually mention."
)


def build_npc_prompt(
    campaign_name: str,
    recaps: Sequence[SessionRecap],
    party_names: Sequence[str],
) -> str:
    """Build the prompt that reads the NPC cast out of session recaps.

    Args:
        campaign_name: The campaign the sessions belong to.
        recaps: Session recaps, in play order.
        party_names: The player characters, named so they are not returned.

    Returns:
        The prompt text.
    """
    blocks = session_preamble(_TASK, campaign_name, recaps)
    if party_names:
        blocks.extend(
            [
                "",
                f"Player characters (never list these): {', '.join(party_names)}",
            ]
        )
    blocks.extend(
        [
            "",
            "Reply with JSON only:",
            '{"npcs": [{"name": "<name as written>", '
            '"role": "<one line on who they are and what they did>"}]}',
            "",
            "It is correct to return few. Never invent a name to fill the list.",
        ]
    )
    return "\n".join(blocks)


def parse_npcs(
    response: str,
    known_names: Sequence[str],
    exclude_names: Sequence[str] = (),
) -> List[DiscoveredNpc]:
    """Parse a model response into the discovered cast.

    The party is excluded here rather than only in the prompt. Asking a model
    not to name the player characters does not stop it: a run over real
    sessions returned a party member as an NPC because he reads like one in the
    recaps. An exclusion that matters is enforced in code.

    Args:
        response: The raw model response.
        known_names: Characters already on record, used to mark matches.
        exclude_names: Names that must never be returned, whatever the model says.

    Returns:
        The discovered NPCs, deduplicated, in model order.
    """
    payload = extract_json_object(response)
    if payload is None:
        return []
    raw = payload.get("npcs")
    if not isinstance(raw, list):
        return []

    known = {name.strip().lower() for name in known_names if name.strip()}
    excluded = {name.strip().lower() for name in exclude_names if name.strip()}
    out: List[DiscoveredNpc] = []
    seen: set[str] = set()
    for item in raw:
        npc = _read_npc(item, known)
        if npc is None:
            continue
        lowered = npc.name.lower()
        if lowered in seen or lowered in excluded:
            continue
        seen.add(lowered)
        out.append(npc)
        if len(out) >= MAX_DISCOVERED_NPCS:
            break
    return out


def _read_npc(item: Any, known: set[str]) -> Optional[DiscoveredNpc]:
    """Read one NPC entry from the model's list.

    Args:
        item: One entry, expected to be a mapping with a name.
        known: Lowercased names already on record.

    Returns:
        The NPC, or None when the entry carries no usable name.
    """
    if isinstance(item, str):
        name, role = item.strip(), ""
    elif isinstance(item, dict):
        name = str(item.get("name", "")).strip()
        role = clip_to_budget(str(item.get("role", "")), MAX_ROLE_CHARS)
    else:
        return None
    if not name:
        return None
    return DiscoveredNpc(name=name, role=role, known=name.lower() in known)


def merge_npcs(batches: Sequence[Sequence[DiscoveredNpc]]) -> List[DiscoveredNpc]:
    """Merge per-window casts into one, keeping the fullest description.

    The same NPC recurs across windows; the window that says most about them
    is the one worth keeping.

    Args:
        batches: Per-window discovered casts.

    Returns:
        One entry per name, in first-seen order.
    """
    best: Dict[str, DiscoveredNpc] = {}
    order: List[str] = []
    for batch in batches:
        for npc in batch:
            key = npc.name.strip().lower()
            current = best.get(key)
            if current is None:
                best[key] = npc
                order.append(key)
            elif len(npc.role) > len(current.role):
                # Keep the first spelling; take the better description.
                best[key] = DiscoveredNpc(current.name, npc.role, current.known)
    return [best[key] for key in order[:MAX_DISCOVERED_NPCS]]


def _windows(
    recaps: Sequence[SessionRecap],
    size: int,
) -> List[Sequence[SessionRecap]]:
    """Split recaps into consecutive windows.

    Args:
        recaps: Session recaps, in play order.
        size: Sessions per window.

    Returns:
        The windows, in order.
    """
    step = max(size, 1)
    return [recaps[i : i + step] for i in range(0, len(recaps), step)]


def extract_npcs(
    ai_client: Optional[AIClientProtocol],
    campaign_name: str,
    recaps: Sequence[SessionRecap],
    roster: ArcRoster,
    num_ctx: int = 0,
) -> List[DiscoveredNpc]:
    """Read the NPC cast out of a campaign's session recaps.

    Args:
        ai_client: The AI client, or None when AI is unavailable.
        campaign_name: The campaign the sessions belong to.
        recaps: Session recaps, in play order.
        roster: The party (excluded from the answer) and the NPCs already on
            record (used to mark matches).
        num_ctx: Context window to request. The recaps run well past Ollama's
            2048-token default, and the overflow is dropped silently - which is
            why late sessions contributed no NPCs at all.

    Returns:
        The discovered NPCs, empty when AI is unavailable or nothing parsed.
    """
    party_names = roster.party
    known_names = roster.npcs
    ordered = usable_recaps(recaps)
    if ai_client is None or not ordered:
        return []

    batches: List[List[DiscoveredNpc]] = []
    for window in _windows(ordered, RECAPS_PER_CALL):
        prompt = build_npc_prompt(campaign_name, window, party_names)
        try:
            response = ai_client.chat_completion(
                [{"role": "user", "content": prompt}],
                max_tokens=MAX_EXTRACT_TOKENS,
                json_mode=True,
                disable_thinking=True,
                num_ctx=num_ctx,
            )
        except (RuntimeError, OSError, ValueError):
            # One window the model fumbled must not cost the rest of the cast.
            continue
        batches.append(parse_npcs(response, known_names, party_names))
    return merge_npcs(batches)
