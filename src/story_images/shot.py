"""Analyse one selected event into a shot: setting, action, mood, people."""

from typing import Any, List, Optional, Sequence

from src.ai.ai_client import AIClientProtocol
from src.story_images.types import (
    RosterEntry,
    ShotAnalysis,
    ShotPerson,
    apply_roster,
)
from src.utils.ai_json import extract_json_object
from src.utils.string_utils import clip_to_budget

MAX_EXCERPT_CHARS = 900
MAX_FIELD_CHARS = 240
MAX_PEOPLE = 12
MAX_SHOT_TOKENS = 900

_TASK = (
    "You are a D&D campaign illustrator. Read this scene and say what a "
    "painting of it would show: where it is, what is happening, the mood, and "
    "who is in frame. Only name people the scene actually mentions. Do not "
    "invent a crowd to fill the shot.\n"
    "Describe the setting by what is visible - the room, its furniture, its "
    "light - never by its name. A renderer has never heard of your world, so "
    "a place name paints nothing and it invents scenery instead.\n"
    "Keep the mood to light and atmosphere. Anything you put there about "
    "where the scene is will fight the setting: one scene said 'the "
    "darkening outdoors' and the tavern came back as a forest."
)


def build_shot_prompt(
    excerpt: str,
    event_title: str,
    roster_names: Sequence[str],
) -> str:
    """Build the shot-analysis prompt.

    Args:
        excerpt: The bounded passage for this event.
        event_title: The event's short title.
        roster_names: Known PC and NPC names, so the model can spell them
            the way Drupal does.

    Returns:
        The prompt text.
    """
    blocks = [
        _TASK,
        "",
        f"Event: {event_title}",
        "",
        "Scene:",
        clip_to_budget(excerpt, MAX_EXCERPT_CHARS),
    ]
    if roster_names:
        blocks.extend(
            [
                "",
                "People on record (spell these names this way when they appear): "
                + ", ".join(roster_names),
            ]
        )
    blocks.extend(
        [
            "",
            "Reply with JSON only:",
            '{"setting": "<what the place looks like, 6-12 words of '
            'visible detail, never a proper name>", '
            '"action": "<what is happening>", '
            '"mood": "<lighting and tone only, 4-8 words>", '
            '"people": [{"name": "<name as written>", '
            '"action": "<one line on what they are doing in this '
            'shot>"}]}',
            "",
            "It is correct to name few people. Never invent a name.",
        ]
    )
    return "\n".join(blocks)


def parse_shot(
    response: str, roster: Sequence[RosterEntry]
) -> ShotAnalysis:
    """Parse a model response into a shot, matching names against the roster.

    Args:
        response: The raw model response.
        roster: Campaign characters that may appear.

    Returns:
        The shot. Empty fields when nothing parsed.
    """
    payload = extract_json_object(response)
    if payload is None:
        return ShotAnalysis()

    people: List[ShotPerson] = []
    raw = payload.get("people")
    if isinstance(raw, list):
        seen: set[str] = set()
        for item in raw:
            person = _read_person(item)
            if person is None:
                continue
            key = person.name.lower()
            if key in seen:
                continue
            seen.add(key)
            people.append(apply_roster(person, roster))
            if len(people) >= MAX_PEOPLE:
                break

    return ShotAnalysis(
        setting=clip_to_budget(str(payload.get("setting", "")), MAX_FIELD_CHARS),
        action=clip_to_budget(str(payload.get("action", "")), MAX_FIELD_CHARS),
        mood=clip_to_budget(str(payload.get("mood", "")), MAX_FIELD_CHARS),
        people=people,
    )


def _read_person(item: Any) -> Optional[ShotPerson]:
    """Read one person from the model's list.

    Args:
        item: One entry, a mapping or a bare name.

    Returns:
        The person, or None when there is no usable name.
    """
    if isinstance(item, str):
        name, action = item.strip(), ""
    elif isinstance(item, dict):
        name = str(item.get("name", "")).strip()
        action = clip_to_budget(
            str(item.get("action") or item.get("role", "")), MAX_FIELD_CHARS)
    else:
        return None
    if not name:
        return None
    return ShotPerson(name=name, action=action)


def analyze_shot(
    ai_client: Optional[AIClientProtocol],
    excerpt: str,
    event_title: str,
    roster: Sequence[RosterEntry],
) -> ShotAnalysis:
    """Read setting, action, mood, and people out of one event excerpt.

    Args:
        ai_client: The AI client, or None when AI is unavailable.
        excerpt: The bounded passage for this event.
        event_title: The event's short title.
        roster: Campaign characters that may appear.

    Returns:
        The shot. Empty when AI is unavailable or nothing parsed.
    """
    if ai_client is None or not excerpt.strip():
        return ShotAnalysis()

    prompt = build_shot_prompt(
        excerpt, event_title, [entry.name for entry in roster if entry.name]
    )
    try:
        response = ai_client.chat_completion(
            [{"role": "user", "content": prompt}],
            max_tokens=MAX_SHOT_TOKENS,
            json_mode=True,
            disable_thinking=True,
        )
    except (RuntimeError, OSError, ValueError):
        return ShotAnalysis()
    return parse_shot(response, roster)
