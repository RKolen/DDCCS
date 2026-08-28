"""Read JSON out of a model response.

A local model answers a JSON request with the object wrapped in prose, a code
fence, or both. Every caller that asks for JSON needs the same unwrapping, so
it lives here rather than once per feature.

It also needs the same salvage. A response that runs into its token budget
stops mid-value, leaving brackets open, and a strict parse of that throws the
whole answer away - a cast of seven NPCs was lost because the seventh name was
cut in half. Truncation is normal at these budgets, so a fragment is closed at
its last complete value rather than discarded.
"""

import json
import re
from typing import Any, Dict, List, Optional

_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def extract_json_object(response: str) -> Optional[Dict[str, Any]]:
    """Pull the first JSON object out of a model response.

    Args:
        response: The raw response, which may be fenced or prefaced.

    Returns:
        The decoded object, or None when nothing parses.
    """
    text = response.strip()
    if not text:
        return None
    fenced = _FENCE_RE.search(text)
    if fenced:
        text = fenced.group(1).strip()
    start = text.find("{")
    if start == -1:
        return None
    end = text.rfind("}")
    if end > start:
        parsed = _load(text[start : end + 1])
        if parsed is not None:
            return parsed

    repaired = _close_truncated(text[start:])
    return None if repaired is None else _load(repaired)


def _load(candidate: str) -> Optional[Dict[str, Any]]:
    """Decode a JSON object, returning None rather than raising.

    Args:
        candidate: The text to decode.

    Returns:
        The decoded object, or None when it does not parse to one.
    """
    try:
        parsed = json.loads(candidate)
    except (ValueError, TypeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def _close_truncated(fragment: str) -> Optional[str]:
    """Close a JSON fragment at its last complete value.

    Walks the fragment tracking string literals and bracket depth, remembers
    the last point where a nested value finished, and shuts the still-open
    brackets there. What was cut off is lost; everything before it survives.

    Args:
        fragment: Text starting at the opening brace.

    Returns:
        A closeable JSON string, or None when no nested value ever completed.
    """
    stack: List[str] = []
    in_string = False
    escaped = False
    cut: Optional[int] = None
    closers = ""

    for index, char in enumerate(fragment):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char in "{[":
            stack.append(char)
        elif char in "}]":
            if not stack:
                break
            stack.pop()
            if stack:
                cut = index + 1
                closers = "".join("}" if open_char == "{" else "]" for open_char in reversed(stack))

    if cut is None:
        return None
    return fragment[:cut] + closers
