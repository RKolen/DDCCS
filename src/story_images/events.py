"""Chunk a story and extract selectable key events.

A session body will not fit a local context window, so this splits the prose
into bounded chunks, asks one question of each (what happened), then merges
and caps the list. The later shot analysis reads only the excerpt of the
event the operator picked.
"""

import html
import logging
import re
from typing import Any, List, Optional, Sequence

from src.ai.ai_client import AIClientProtocol
from src.story_images.types import StoryEvent
from src.utils.ai_json import extract_json_object
from src.utils.string_utils import clip_to_budget

_TAG_RE = re.compile(r"<[^>]+>")
logger = logging.getLogger(__name__)

MAX_CHUNK_CHARS = 2400
MAX_EVENTS = 12
MAX_EVENTS_PER_CHUNK = 4
MAX_EXCERPT_CHARS = 900
MAX_LINE_CHARS = 180
MAX_TITLE_CHARS = 80
MAX_EXTRACT_TOKENS = 900

_TASK = (
    "You are a D&D campaign illustrator scouting a session for pictures. "
    "List the distinct visual moments in this passage - arrivals, confrontations, "
    "discoveries, fights, bargains. Skip travel filler and recap. Only name "
    "moments this passage actually describes."
)


def story_to_text(body: str) -> str:
    """Strip HTML and collapse whitespace from a Drupal story body.

    Args:
        body: Processed HTML or plain text.

    Returns:
        Plain prose.
    """
    cleaned = html.unescape(_TAG_RE.sub(" ", body))
    return " ".join(cleaned.split())


def chunk_story(text: str, limit: int = MAX_CHUNK_CHARS) -> List[str]:
    """Split prose into chunks on sentence boundaries, each under ``limit``.

    Args:
        text: Plain story prose.
        limit: Maximum characters per chunk.

    Returns:
        Non-empty chunks in story order. A single oversize sentence is hard-cut.
    """
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    if len(cleaned) <= limit:
        return [cleaned]

    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    chunks: List[str] = []
    current = ""
    for sentence in sentences:
        piece = sentence.strip()
        if not piece:
            continue
        if current and len(current) + 1 + len(piece) > limit:
            chunks.append(current)
            current = ""
        if len(piece) > limit:
            if current:
                chunks.append(current)
                current = ""
            start = 0
            while start < len(piece):
                chunks.append(clip_to_budget(piece[start : start + limit], limit))
                start += limit
            continue
        current = f"{current} {piece}".strip() if current else piece
    if current:
        chunks.append(current)
    return [chunk for chunk in chunks if chunk]


def build_events_prompt(chunk: str, story_title: str) -> str:
    """Build the per-chunk event extraction prompt.

    Args:
        chunk: One bounded passage of the story.
        story_title: The story's title, for context.

    Returns:
        The prompt text.
    """
    return "\n".join(
        [
            _TASK,
            "",
            f"Story: {story_title}",
            "",
            "Passage:",
            clip_to_budget(chunk, MAX_CHUNK_CHARS),
            "",
            "Reply with JSON only:",
            '{"events": [{"title": "<short scene title>", '
            '"one_line": "<one sentence of what is happening>", '
            '"excerpt_hint": "<a short phrase copied from the passage>"}]}',
            "",
            f"At most {MAX_EVENTS_PER_CHUNK} events. It is correct to return none.",
        ]
    )


def _excerpt_for(chunk: str, hint: str) -> str:
    """Take a bounded window of ``chunk`` around ``hint``, or the chunk start.

    Args:
        chunk: The passage this event was read from.
        hint: A phrase the model copied from the passage.

    Returns:
        An excerpt within ``MAX_EXCERPT_CHARS``.
    """
    haystack = chunk.strip()
    needle = " ".join(hint.split())
    if needle:
        index = haystack.lower().find(needle.lower())
        if index >= 0:
            start = max(0, index - 120)
            return clip_to_budget(haystack[start:], MAX_EXCERPT_CHARS)
    return clip_to_budget(haystack, MAX_EXCERPT_CHARS)


def parse_events(response: str, chunk: str) -> List[StoryEvent]:
    """Parse a model response into events, attaching excerpts from ``chunk``.

    Args:
        response: The raw model response.
        chunk: The passage this response was asked about.

    Returns:
        Events in model order, empty when nothing parsed.
    """
    payload = extract_json_object(response)
    if payload is None:
        return []
    raw = payload.get("events")
    if not isinstance(raw, list):
        return []

    out: List[StoryEvent] = []
    for item in raw:
        event = _read_event(item, chunk)
        if event is None:
            continue
        out.append(event)
        if len(out) >= MAX_EVENTS_PER_CHUNK:
            break
    return out


def _read_event(item: Any, chunk: str) -> Optional[StoryEvent]:
    """Read one event from the model's list.

    Args:
        item: One entry, expected to be a mapping.
        chunk: The passage, used to attach an excerpt.

    Returns:
        The event, or None when there is no usable title.
    """
    if not isinstance(item, dict):
        return None
    title = clip_to_budget(str(item.get("title", "")), MAX_TITLE_CHARS)
    if not title:
        return None
    one_line = clip_to_budget(str(item.get("one_line", "")), MAX_LINE_CHARS)
    hint = str(item.get("excerpt_hint", "") or item.get("excerpt", ""))
    excerpt = _excerpt_for(chunk, hint)
    if not excerpt:
        return None
    if not one_line:
        one_line = clip_to_budget(excerpt, MAX_LINE_CHARS)
    return StoryEvent(title=title, one_line=one_line, excerpt=excerpt)


def merge_events(groups: Sequence[Sequence[StoryEvent]]) -> List[StoryEvent]:
    """Flatten chunk results, dropping title duplicates, capped at ``MAX_EVENTS``.

    Args:
        groups: Per-chunk event lists, in story order.

    Returns:
        The merged list.
    """
    out: List[StoryEvent] = []
    seen: set[str] = set()
    for group in groups:
        for event in group:
            key = event.title.strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(event)
            if len(out) >= MAX_EVENTS:
                return out
    return out


def extract_events(
    ai_client: Optional[AIClientProtocol],
    body: str,
    story_title: str,
) -> List[StoryEvent]:
    """Read key visual moments out of a story body.

    Args:
        ai_client: The AI client, or None when AI is unavailable.
        body: Drupal processed HTML or plain text.
        story_title: The story's title.

    Returns:
        Events in story order, empty when AI is unavailable or nothing parsed.
    """
    if ai_client is None:
        return []
    chunks = chunk_story(story_to_text(body))
    if not chunks:
        return []

    groups: List[List[StoryEvent]] = []
    for chunk in chunks:
        prompt = build_events_prompt(chunk, story_title)
        try:
            response = _chunk_completion(ai_client, prompt)
        except (RuntimeError, OSError, ValueError) as err:
            logger.warning("Event extract failed for a chunk of %s: %s", story_title, err)
            continue
        groups.append(parse_events(response, chunk))
    return merge_events(groups)


def _chunk_completion(ai_client: AIClientProtocol, prompt: str) -> str:
    """Ask the instruct model for JSON events from one story chunk.

    Args:
        ai_client: The AI client.
        prompt: The chunk prompt.

    Returns:
        The model response text.

    Raises:
        RuntimeError, OSError, ValueError: Propagated from the client.
    """
    return ai_client.chat_completion(
        [{"content": prompt, "role": "user"}],
        json_mode=True,
        disable_thinking=True,
        max_tokens=MAX_EXTRACT_TOKENS,
    )
