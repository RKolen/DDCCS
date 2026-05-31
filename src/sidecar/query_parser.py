"""AI-powered D&D search query parser using the shared AI client."""

import json
import logging
from typing import Any, Dict, List, Optional

from src.ai.ai_client import AIClient, get_client_for_task
from src.config.config_loader import load_config
from src.sidecar.models import ParseQueryResponse

_LOG = logging.getLogger(__name__)

_VALID_TYPES = frozenset({"character", "npc", "spell", "item", "feat", "monster"})

_SYSTEM_PROMPT = (
    "You are a D&D search query parser. Analyse the natural-language search query and "
    "return ONLY a JSON object with these three keys:\n"
    '- "query": normalized search terms for semantic search (strip filler words)\n'
    '- "inferred_type": one of character/npc/spell/item/feat/monster, or null\n'
    '- "confidence": float 0.0-1.0 reflecting certainty of inferred_type\n\n'
    "Rules:\n"
    "- Strip filler words (show me, find, search for, what is, give me, list, etc.)\n"
    "- Preserve D&D-specific vocabulary exactly (spell names, class names, creature types)\n"
    "- Set inferred_type to null when the query spans multiple types or is ambiguous\n"
    "- confidence 1.0: user explicitly named the type; "
    "0.5: implied by vocabulary; 0.0: no signal\n\n"
    "Return ONLY the JSON object. No markdown fences. No explanation."
)


class _ClientHolder:
    """Lazy singleton for the query-parser AI client."""

    _client: Optional[AIClient] = None

    @classmethod
    def get(cls) -> Optional[AIClient]:
        """Return or lazily initialize the shared parser client.

        Returns:
            Initialized AIClient, or None if AI is not configured.
        """
        if cls._client is None:
            cls._client = _build_parser_client()
        return cls._client

    @classmethod
    def reset(cls) -> None:
        """Clear the cached client (used in tests)."""
        cls._client = None


def reset_client_cache() -> None:
    """Clear the cached AI client so the next call re-initializes it.

    Intended for use in tests to ensure a clean state between test cases.
    """
    _ClientHolder.reset()


def _build_parser_client() -> Optional[AIClient]:
    """Build an AIClient for low-latency query parsing using the fast profile.

    Returns:
        Initialized AIClient, or None if AI is not configured.
    """
    config = load_config()
    if not config.ai.is_configured():
        return None
    return get_client_for_task("story_analysis")


def _fallback(original: str) -> ParseQueryResponse:
    """Return a no-op response that passes the original query unchanged.

    Args:
        original: The original search query string.

    Returns:
        ParseQueryResponse with query equal to original and no type inference.
    """
    return ParseQueryResponse(
        original=original,
        query=original,
        inferred_type=None,
        confidence=0.0,
    )


def parse_query(query: str) -> ParseQueryResponse:
    """Parse a natural-language D&D search query into structured intent.

    Uses an AI model to extract normalized search terms and infer the most
    likely content type. Degrades gracefully to the raw query when the AI
    client is unavailable or returns an unparseable response.

    Args:
        query: Raw natural-language search query.

    Returns:
        ParseQueryResponse with normalized query and optional content type.
    """
    client = _ClientHolder.get()
    if client is None:
        _LOG.warning("AI client not configured; returning raw query unchanged")
        return _fallback(query)

    messages: List[Dict[str, str]] = [
        client.create_system_message(_SYSTEM_PROMPT),
        client.create_user_message(query),
    ]

    try:
        raw = client.chat_completion(
            messages, temperature=0.1, max_tokens=150, json_mode=True
        )
    except RuntimeError as exc:
        _LOG.warning("AI client error during query parsing: %s", exc)
        return _fallback(query)

    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict):
            raise ValueError(f"Expected JSON object, got: {type(parsed).__name__}")
        data: Dict[str, Any] = parsed
    except (json.JSONDecodeError, ValueError) as exc:
        _LOG.warning("Failed to parse AI response: %s", exc)
        return _fallback(query)

    normalized = str(data.get("query") or query).strip() or query

    inferred_type_raw = data.get("inferred_type")
    inferred_type: Optional[str] = None
    if isinstance(inferred_type_raw, str) and inferred_type_raw in _VALID_TYPES:
        inferred_type = inferred_type_raw

    try:
        confidence = float(data.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(1.0, confidence))

    return ParseQueryResponse(
        original=query,
        query=normalized,
        inferred_type=inferred_type,
        confidence=confidence,
    )
