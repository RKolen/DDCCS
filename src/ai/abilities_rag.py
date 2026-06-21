"""Resolve D&D abilities and features from the 2024 ruleset.

Given a source (class, species, subspecies, ...) and a character level, this
fetches the relevant page from the rules wiki configured via
``RAG_RULES_BASE_URL`` and extracts the abilities granted up to that level,
with their rules text.

Two page layouts are supported:
  * Class pages use ``Level N: Feature`` headings followed by description text.
  * Species/subspecies pages list traits as bold-lead paragraphs
    (``<strong>Resourceful.</strong> ...``); higher-level lineage traits using
    ``Level N:`` headings are also captured.

The resolver degrades gracefully to an empty list whenever RAG is disabled,
scraping dependencies are missing, or a page cannot be fetched or parsed. It is
intentionally generic so other features can resolve rules content the same way.
"""

from __future__ import annotations

import logging
import re
from typing import List, Optional, TypedDict, cast

from src.ai.rag_system import RAGSystem, get_rag_system

try:
    from bs4 import BeautifulSoup
    from bs4.element import Tag
    _SCRAPING_AVAILABLE = True
except ImportError:
    _SCRAPING_AVAILABLE = False

logger = logging.getLogger(__name__)

# Heading form used for leveled features, e.g. "Level 1: Second Wind".
_LEVEL_HEADING = re.compile(r"^Level\s+(\d+):\s*(.+)$", re.IGNORECASE)

# Source categories that use the species-style trait layout.
_TRAIT_SOURCES = frozenset({"species", "subspecies"})

# Cache key suffix so ability parses do not collide with WikiClient section
# caches stored under the same page URL.
_CACHE_SUFFIX = "#abilities"

# Cap a single feature description to keep payloads and storage reasonable.
_MAX_DESCRIPTION = 2000


class Ability(TypedDict):
    """A resolved ability/feature granted by a source at a given level."""

    name: str
    description: str
    level: int
    source_type: str


def get_abilities(
    source_type: str,
    source_name: str,
    level: int,
    *,
    rag: Optional[RAGSystem] = None,
) -> List[Ability]:
    """Resolve abilities a source grants up to a character level.

    Args:
        source_type: Source category ("class", "species", "subspecies", ...).
        source_name: Source name used to locate the wiki page (e.g. "Fighter").
        level: Highest character level to include (features above are dropped).
        rag: Optional RAG system to use; when omitted a shared instance is
            resolved. Pass an explicit instance to control or bypass RAG, which
            aids testing.

    Returns:
        Ordered, de-duplicated abilities at or below the requested level. Empty
        when RAG is unavailable or the page cannot be resolved.
    """
    rag_system = rag if rag is not None else _safe_rag_system()
    if rag_system is None or not getattr(rag_system, "enabled", False):
        return []

    all_abilities = _resolve_page(rag_system, source_type, source_name)
    return [ability for ability in all_abilities if ability["level"] <= level]


def _safe_rag_system() -> Optional[RAGSystem]:
    """Resolve the shared RAG system, returning None when unavailable.

    Returns:
        A RAG system instance when one can be built, otherwise None.
    """
    try:
        return get_rag_system()
    except (ImportError, OSError, ValueError) as exc:
        logger.debug("RAG system unavailable for abilities: %s", exc)
        return None


def _resolve_page(rag: RAGSystem, source_type: str, source_name: str) -> List[Ability]:
    """Fetch and parse all abilities for a source page, with caching.

    Args:
        rag: RAG system providing the rules wiki client.
        source_type: Source category.
        source_name: Source name to locate the page.

    Returns:
        All abilities parsed from the page (unfiltered by level).
    """
    client = getattr(rag, "rules_client", None)
    if client is None or not _SCRAPING_AVAILABLE or getattr(client, "session", None) is None:
        return []

    slug = source_name.strip().lower().replace(" ", "-")
    if slug == "":
        return []
    url = f"{client.base_url}/{slug}"

    cached = client.cache.get(url + _CACHE_SUFFIX)
    if cached is not None and isinstance(cached.get("abilities"), list):
        return [_coerce_ability(item) for item in cached["abilities"] if isinstance(item, dict)]

    html = _fetch_html(client, url)
    if html is None:
        return []

    abilities = _parse_abilities(html, source_type)
    client.cache.set(url + _CACHE_SUFFIX, {"abilities": [dict(a) for a in abilities]})
    return abilities


def _fetch_html(client: object, url: str) -> Optional[str]:
    """Fetch the page-content HTML for a URL, returning None on any failure.

    Args:
        client: The rules WikiClient (provides a requests session).
        url: Absolute page URL.

    Returns:
        The raw HTML body, or None when the request fails.
    """
    session = getattr(client, "session", None)
    if session is None:
        return None
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
    except OSError as exc:
        logger.debug("Ability page fetch failed for %s: %s", url, exc)
        return None
    return str(response.text)


def _parse_abilities(html: str, source_type: str) -> List[Ability]:
    """Parse abilities from page HTML for the given source type.

    Args:
        html: Raw page HTML.
        source_type: Source category determining the layout to expect.

    Returns:
        De-duplicated abilities parsed from the page.
    """
    if not _SCRAPING_AVAILABLE:
        return []
    found = BeautifulSoup(html, "html.parser").find("div", id="page-content")
    if not isinstance(found, Tag):
        return []
    content = cast("Tag", found)

    leveled = _parse_level_headings(content, source_type)
    if source_type not in _TRAIT_SOURCES:
        return _dedupe(leveled)
    return _dedupe(_parse_bold_traits(content, source_type) + leveled)


def _parse_level_headings(content: "Tag", source_type: str) -> List[Ability]:
    """Parse "Level N: Feature" headings into abilities.

    Args:
        content: The page-content BeautifulSoup element.
        source_type: Source category to stamp on each ability.

    Returns:
        Abilities derived from leveled headings.
    """
    abilities: List[Ability] = []
    for heading in content.find_all(["h1", "h2", "h3", "h4"]):
        match = _LEVEL_HEADING.match(heading.get_text(strip=True))
        if match is None:
            continue
        abilities.append(
            Ability(
                name=match.group(2).strip(),
                description=_collect_description(heading),
                level=int(match.group(1)),
                source_type=source_type,
            )
        )
    return abilities


def _parse_bold_traits(content: "Tag", source_type: str) -> List[Ability]:
    """Parse bold-lead trait paragraphs (e.g. species traits) into abilities.

    Args:
        content: The page-content BeautifulSoup element.
        source_type: Source category to stamp on each ability.

    Returns:
        Level-1 abilities derived from bold-lead paragraphs.
    """
    abilities: List[Ability] = []
    for paragraph in content.find_all("p"):
        lead = paragraph.find(["strong", "b"])
        if lead is None:
            continue
        lead_text = lead.get_text(strip=True)
        # A trailing period marks a trait name; stat lines end with a colon.
        if not lead_text.endswith("."):
            continue
        name = lead_text.rstrip(".").strip()
        if name == "":
            continue
        full = paragraph.get_text(" ", strip=True)
        description = full[len(lead_text):].strip() if full.startswith(lead_text) else full
        abilities.append(
            Ability(
                name=name,
                description=_clean(description),
                level=1,
                source_type=source_type,
            )
        )
    return abilities


def _collect_description(heading: "Tag") -> str:
    """Collect description text following a heading until the next heading.

    Args:
        heading: A heading BeautifulSoup element.

    Returns:
        Cleaned, joined description text capped at a sensible length.
    """
    parts: List[str] = []
    for sibling in heading.find_next_siblings():
        if sibling.name in ("h1", "h2", "h3", "h4"):
            break
        if sibling.name in ("p", "ul"):
            text = _clean(sibling.get_text(" ", strip=True))
            if text:
                parts.append(text)
    return "\n\n".join(parts)[:_MAX_DESCRIPTION]


def _clean(text: str) -> str:
    """Strip citation/edit markers and collapse whitespace.

    Args:
        text: Raw text.

    Returns:
        Cleaned text.
    """
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"\[edit\]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _coerce_ability(item: dict) -> Ability:
    """Coerce a cached dict into an Ability with safe defaults.

    Args:
        item: Cached ability dict.

    Returns:
        A well-formed Ability.
    """
    return Ability(
        name=str(item.get("name", "")),
        description=str(item.get("description", "")),
        level=int(item.get("level", 1)),
        source_type=str(item.get("source_type", "")),
    )


def _dedupe(abilities: List[Ability]) -> List[Ability]:
    """Drop abilities with duplicate names, keeping first-seen order.

    Args:
        abilities: Abilities to de-duplicate.

    Returns:
        De-duplicated abilities.
    """
    seen = set()
    unique: List[Ability] = []
    for ability in abilities:
        key = ability["name"].lower()
        if key in seen or key == "":
            continue
        seen.add(key)
        unique.append(ability)
    return unique
