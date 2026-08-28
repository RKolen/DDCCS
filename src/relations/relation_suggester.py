"""Suggest relationships between the characters of a story arc.

Split one subject at a time: a large cast is hundreds of possible connections,
too many for one local inference pass. Each call asks about one character
against short digests of the others; the caller merges the batches.
"""

import json
import re
from typing import Any, Dict, List, Optional, Sequence

from src.ai.ai_client import AIClientProtocol
from src.relations.relation_types import (
    CharacterDigest,
    RelationSuggestion,
    TIER_DIRECT,
    TIER_THEMATIC,
)

# Keep prompts small; local inference degrades with a wide context. The JSON
# request needs an instruct model - a "thinking" model spends the whole budget
# reasoning and returns empty content. The sidecar picks the profile.
MAX_OTHERS = 14
MAX_CONTEXT_CHARS = 1200
MAX_SUGGESTION_TOKENS = 900

_PARTY_TASK = (
    "Suggest bonds, frictions, or shared history between the subject and the "
    "other party members. Focus on what is already on their sheets: shared "
    "origins, opposed allegiances, complementary or clashing roles."
)

_NPC_TASK = (
    "Suggest connections between the subject and these NPCs. Focus on what "
    "would be explosive if revealed: shared origins, a wrong that was done, "
    "mirrored abilities, or a stake in the same events."
)


def _clip(text: str, limit: int) -> str:
    """Trim text to a character budget on a word boundary.

    Args:
        text: The text to clip.
        limit: Maximum characters to keep.

    Returns:
        The clipped text.
    """
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit].rsplit(" ", 1)[0]


def build_prompt(
    subject: CharacterDigest,
    others: Sequence[CharacterDigest],
    kind: str,
    context: str = "",
) -> str:
    """Build the prompt for one subject's relationship batch.

    Args:
        subject: The character the suggestions are about.
        others: The candidates to relate the subject to.
        kind: Either ``"party"`` or ``"npc"``, selecting the task wording.
        context: Optional arc plot spine, clipped to keep the prompt small.

    Returns:
        The prompt text.
    """
    task = _NPC_TASK if kind == "npc" else _PARTY_TASK
    roster = "\n".join(f"- {other.to_line()}" for other in others[:MAX_OTHERS])
    blocks = [
        f"Subject: {subject.to_line()}",
        "",
        "Candidates:",
        roster,
    ]
    if context:
        blocks.extend(["", f"Arc context: {_clip(context, MAX_CONTEXT_CHARS)}"])
    blocks.extend(
        [
            "",
            task,
            "",
            "Only suggest a connection you can justify from the details above. "
            "It is correct to return fewer connections than candidates, and "
            "correct to return none. Never invent a character that is not "
            "listed.",
            "",
            'Reply with JSON only: {"relations": [{"source": "<subject>", '
            '"target": "<candidate name>", "relation_type": "<short label>", '
            '"tier": 1, "note": "<the connection and how to play it>"}]}',
            "tier 1 = direct and personal, 2 = thematic, 3 = incidental.",
        ]
    )
    return "\n".join(blocks)


def parse_suggestions(
    response: str,
    subject_name: str,
    allowed: Sequence[str],
) -> List[RelationSuggestion]:
    """Parse a model response into validated suggestions.

    Names are checked against the roster that was offered; invented characters
    produce unstorable pairs and are dropped here.

    Args:
        response: The raw model response.
        subject_name: The subject the batch was about.
        allowed: Names the model was allowed to use.

    Returns:
        The valid suggestions, in model order.
    """
    payload = _extract_json(response)
    if payload is None:
        return []
    raw = payload.get("relations")
    if not isinstance(raw, list):
        return []

    known = {name.strip().lower(): name for name in allowed if name.strip()}
    known[subject_name.strip().lower()] = subject_name

    out: List[RelationSuggestion] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        suggestion = RelationSuggestion.from_dict(item)
        if suggestion is None:
            continue
        source = known.get(suggestion.source.strip().lower())
        target = known.get(suggestion.target.strip().lower())
        if source is None or target is None:
            continue
        suggestion.source = source
        suggestion.target = target
        key = suggestion.pair_key()
        if key in seen:
            continue
        seen.add(key)
        out.append(suggestion)
    return out


def _extract_json(response: str) -> Optional[Dict[str, Any]]:
    """Pull the first JSON object out of a model response.

    Args:
        response: The raw response, which may be fenced or prefaced.

    Returns:
        The decoded object, or None when nothing parses.
    """
    text = response.strip()
    if not text:
        return None
    fenced = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
    except (ValueError, TypeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def suggest_relations_for_subject(
    ai_client: Optional[AIClientProtocol],
    subject: CharacterDigest,
    others: Sequence[CharacterDigest],
    kind: str = "party",
    context: str = "",
) -> List[RelationSuggestion]:
    """Suggest one subject's relationships in a single model call.

    Args:
        ai_client: The AI client, or None when AI is unavailable.
        subject: The character to suggest relationships for.
        others: Candidate characters to relate the subject to.
        kind: Either ``"party"`` or ``"npc"``.
        context: Optional arc plot spine.

    Returns:
        The validated suggestions, empty when AI is unavailable or the model
        returns nothing usable.
    """
    if ai_client is None or not others:
        return []
    prompt = build_prompt(subject, others, kind, context)
    messages = [{"role": "user", "content": prompt}]
    try:
        response = ai_client.chat_completion(
            messages,
            max_tokens=MAX_SUGGESTION_TOKENS,
            json_mode=True,
            disable_thinking=True,
        )
    except (RuntimeError, OSError, ValueError):
        return []
    return parse_suggestions(response, subject.name, [o.name for o in others])


def merge_suggestions(
    batches: Sequence[Sequence[RelationSuggestion]],
) -> List[RelationSuggestion]:
    """Merge per-subject batches into one deduplicated set.

    Subjects propose the same bond from both ends, so merging keys on the
    unordered pair. Stronger tier wins; at equal tiers, the longer note.

    Args:
        batches: Per-subject suggestion lists.

    Returns:
        One suggestion per character pair, strongest tier first.
    """
    best: Dict[str, RelationSuggestion] = {}
    for batch in batches:
        for suggestion in batch:
            key = suggestion.pair_key()
            current = best.get(key)
            if current is None or _is_better(suggestion, current):
                best[key] = suggestion
    merged = list(best.values())
    merged.sort(key=lambda s: (s.tier, s.source.lower(), s.target.lower()))
    return merged


def _is_better(candidate: RelationSuggestion, current: RelationSuggestion) -> bool:
    """Decide whether a candidate should replace the kept suggestion.

    Args:
        candidate: The newly seen suggestion.
        current: The suggestion already kept for this pair.

    Returns:
        True when the candidate is more specific.
    """
    if candidate.tier != current.tier:
        return candidate.tier < current.tier
    return len(candidate.note) > len(current.note)


def split_into_batches(
    subjects: Sequence[CharacterDigest],
    others: Sequence[CharacterDigest],
    kind: str = "party",
) -> List[Dict[str, Any]]:
    """Build the per-subject batches the console runs one at a time.

    Party subjects are never offered themselves; NPC candidates are shared.

    Args:
        subjects: The characters to generate suggestions for.
        others: The candidate pool.
        kind: Either ``"party"`` or ``"npc"``.

    Returns:
        One batch dictionary per subject, each with ``subject``, ``others``,
        and ``kind`` keys.
    """
    batches: List[Dict[str, Any]] = []
    for subject in subjects:
        if kind == "party":
            pool = [o for o in others if o.name.strip().lower() != subject.name.strip().lower()]
        else:
            pool = list(others)
        if not pool:
            continue
        batches.append(
            {
                "subject": subject,
                "others": pool[:MAX_OTHERS],
                "kind": kind,
            }
        )
    return batches


def default_tier(kind: str) -> int:
    """Return the tier a suggestion defaults to for a relation side.

    Args:
        kind: Either ``"party"`` or ``"npc"``.

    Returns:
        The default tier constant.
    """
    return TIER_DIRECT if kind == "npc" else TIER_THEMATIC
