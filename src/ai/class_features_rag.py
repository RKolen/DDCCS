"""Reusable class-feature retrieval with a RAG fallback.

Class features are sourced from the bundled class templates first (the
deterministic baseline). When a template is missing features and the RAG
system is enabled, the rules wiki configured via ``RAG_RULES_BASE_URL`` is
consulted and any additional feature names are merged in.

This module is intentionally generic: it exposes a small, dependency-injected
surface (:func:`get_class_features`) so other features that need
rules-from-RAG data can reuse the same pattern. The RAG path always degrades
gracefully to the template baseline on any failure.
"""

import logging
from typing import List, Optional

from src.ai.rag_system import RAGSystem, get_rag_system
from src.characters.character_template import (
    get_class_features_up_to_level,
    load_template,
)

logger = logging.getLogger(__name__)

# Section titles on a rules-wiki class page that are not themselves features.
_NON_FEATURE_SECTIONS = frozenset(
    {
        "introduction",
        "class features",
        "quick build",
        "creating a character",
        "hit points",
        "proficiencies",
        "equipment",
        "starting equipment",
        "the table",
        "multiclassing",
        "spellcasting",
    }
)

# Maximum number of RAG-derived feature names to merge into the baseline.
_MAX_RAG_FEATURES = 40


def get_class_features(
    class_name: str,
    level: int,
    *,
    rag: Optional[RAGSystem] = None,
) -> List[str]:
    """Return class features up to a level, enriched from RAG when sparse.

    The bundled class template provides the deterministic baseline. When RAG
    is available the rules wiki is consulted and any additional feature names
    are merged after the baseline. Any RAG failure falls back to the baseline.

    Args:
        class_name: D&D class name (case-insensitive, e.g. "Bard").
        level: Target character level (features at or below this level).
        rag: Optional RAG system to use; when omitted a shared instance is
            resolved. Pass an explicit instance (or one built with a disabled
            config) to control or bypass RAG, which aids testing.

    Returns:
        Ordered, de-duplicated list of feature names. May be empty when the
        class is unknown and RAG yields nothing.
    """
    baseline = _template_features(class_name, level)

    rag_system = rag if rag is not None else _safe_rag_system()
    if rag_system is None:
        return baseline

    extra = _rag_features(rag_system, class_name)
    return _merge_unique(baseline, extra)


def _template_features(class_name: str, level: int) -> List[str]:
    """Collect baseline features from the bundled class template.

    Args:
        class_name: D&D class name (case-insensitive).
        level: Target character level.

    Returns:
        Feature names from the template, or an empty list when no template
        exists for the class.
    """
    template = load_template(class_name)
    if not template:
        return []
    class_features = template.get("class_features", {})
    return [feature for feature in get_class_features_up_to_level(class_features, level) if feature]


def _safe_rag_system() -> Optional[RAGSystem]:
    """Resolve the shared RAG system, returning None when unavailable.

    Returns:
        A RAG system instance when one can be built, otherwise None.
    """
    try:
        return get_rag_system()
    except (ImportError, OSError, ValueError) as exc:
        logger.debug("RAG system unavailable for class features: %s", exc)
        return None


def _rag_features(rag: RAGSystem, class_name: str) -> List[str]:
    """Fetch candidate feature names for a class from the rules wiki.

    Section titles on the class page are treated as candidate feature names,
    excluding generic, non-feature sections. Any fetch or parse failure
    yields an empty list so the caller can fall back to the baseline.

    Args:
        rag: RAG system providing the rules wiki client.
        class_name: D&D class name to look up.

    Returns:
        Candidate feature names, capped at a sensible maximum.
    """
    rules_client = getattr(rag, "rules_client", None)
    if not getattr(rag, "enabled", False) or rules_client is None:
        return []

    try:
        page_data = rules_client.fetch_page(class_name)
    except (AttributeError, KeyError, IndexError, OSError) as exc:
        logger.debug("Rules lookup failed for class %r: %s", class_name, exc)
        return []

    if not page_data or not page_data.get("sections"):
        return []

    features: List[str] = []
    for section in page_data["sections"]:
        title = str(section.get("title", "")).strip()
        if title and title.lower() not in _NON_FEATURE_SECTIONS:
            features.append(title)
        if len(features) >= _MAX_RAG_FEATURES:
            break
    return features


def _merge_unique(primary: List[str], secondary: List[str]) -> List[str]:
    """Merge two feature lists, preserving order and dropping duplicates.

    Comparison is case-insensitive; the first-seen casing is kept.

    Args:
        primary: Features that take precedence and ordering priority.
        secondary: Additional features appended when not already present.

    Returns:
        Ordered list of unique feature names.
    """
    seen = set()
    merged: List[str] = []
    for feature in [*primary, *secondary]:
        key = feature.lower()
        if key in seen:
            continue
        seen.add(key)
        merged.append(feature)
    return merged
