"""Resolve D&D spell stat blocks from the rules wiki.

Fetches ``spell:{slug}`` pages at ``RAG_RULES_BASE_URL`` and extracts the
fields Drupal stores on ``node--spell``: level, school, casting time, range,
components, duration, concentration, ritual, and the rules text.

Degrades to None whenever RAG is disabled, scraping extras are missing, or
the page cannot be fetched or parsed. Never blocks the console.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, TypedDict

from src.ai.abilities_rag import _clean
from src.ai.rag_system import RAGSystem
from src.ai.wiki_scraping import (
    SCRAPING_AVAILABLE as _SCRAPING_AVAILABLE,
    fetch_first as _fetch_first,
    page_content,
    page_title,
    ready_rules_client,
)

if _SCRAPING_AVAILABLE:
    from bs4.element import Tag

logger = logging.getLogger(__name__)

# Cap stored rules text so a wiki page cannot balloon a Drupal node.
_MAX_DESCRIPTION = 4000

_SCHOOLS = (
    "abjuration",
    "conjuration",
    "divination",
    "enchantment",
    "evocation",
    "illusion",
    "necromancy",
    "transmutation",
)

_LEVEL_ORDINAL = re.compile(
    r"(\d+)(?:st|nd|rd|th)?[-\s]level",
    re.IGNORECASE,
)
_LEVEL_LABELED = re.compile(r"level\s+(\d+)", re.IGNORECASE)
_CANTRIP = re.compile(r"\bcantrip\b", re.IGNORECASE)
_SCHOOL_RE = re.compile(
    r"\b(" + "|".join(_SCHOOLS) + r")\b",
    re.IGNORECASE,
)
_LABEL = re.compile(
    r"^(casting time|range|components|duration)\s*:\s*(.+)$",
    re.IGNORECASE,
)

_TITLE_SEPARATOR = " - D&D"


class SpellData(TypedDict):
    """Structured spell fields scraped from a rules-wiki page."""

    name: str
    level: int
    school: str
    casting_time: str
    spell_range: str
    components: str
    duration: str
    concentration: bool
    ritual: bool
    description: str


def lookup_spell(name: str, *, rag: Optional[RAGSystem] = None) -> Optional[SpellData]:
    """Resolve one spell's stat block from the rules wiki.

    Args:
        name: Spell name (e.g. "Fireball").
        rag: Optional RAG system; resolved from config when omitted.

    Returns:
        Structured spell data, or None when it cannot be resolved.
    """
    client = ready_rules_client(rag)
    if client is None:
        return None
    base_url = str(getattr(client, "base_url", "") or "")
    html = _fetch_first(client, spell_page_urls(base_url, name))
    if html is None:
        return None
    return parse_spell_page(html, fallback_name=name.strip())


def _wiki_slug(name: str) -> str:
    """Build the Wikidot page slug for a spell name.

    Apostrophes are dropped (``Melf's Acid Arrow`` -> ``melfs-acid-arrow``)
    because that is how the rules wiki names its pages.

    Args:
        name: Spell name.

    Returns:
        Lowercase hyphenated slug, or an empty string when the name is blank.
    """
    slug = name.strip().lower().replace(" ", "-")
    return slug.replace("'", "").replace("\u2019", "")


def spell_page_urls(base_url: str, name: str) -> List[str]:
    """Build candidate rules-wiki URLs for a spell, best guess first.

    Args:
        base_url: The rules wiki base URL.
        name: Spell name.

    Returns:
        Ordered candidate URLs, or an empty list when the name is blank.
    """
    slug = _wiki_slug(name)
    if slug == "":
        return []
    root = base_url.rstrip("/")
    return [
        f"{root}/spell:{slug}",
        f"{root}/spells:{slug}",
        f"{root}/{slug}",
    ]


def parse_spell_page(html: str, *, fallback_name: str = "") -> Optional[SpellData]:
    """Parse a rules-wiki spell page into SpellData.

    Args:
        html: Raw page HTML.
        fallback_name: Name to use when the page title cannot be read.

    Returns:
        Structured spell data, or None when the page has no usable body.
    """
    content = page_content(html)
    if content is None:
        return None
    heading = _heading_text(content)
    name = _spell_name(html, fallback_name)
    level = _parse_level(heading)
    school = _parse_school(heading)
    labels = _labeled_fields(content)
    duration = labels.get("duration", "")
    concentration = "concentration" in duration.lower()
    ritual = "ritual" in heading.lower()
    description = _description_text(content)
    if name == "" and heading == "" and not labels:
        return None
    return {
        "name": name or fallback_name,
        "level": level,
        "school": school,
        "casting_time": labels.get("casting time", ""),
        "spell_range": labels.get("range", ""),
        "components": labels.get("components", ""),
        "duration": duration,
        "concentration": concentration,
        "ritual": ritual,
        "description": description[:_MAX_DESCRIPTION],
    }


def _spell_name(html: str, fallback_name: str) -> str:
    """Read the spell name from the page title.

    Args:
        html: Raw page HTML.
        fallback_name: Name to use when the title is empty.

    Returns:
        Display name without the site suffix.
    """
    title = page_title(html)
    if _TITLE_SEPARATOR in title:
        title = title.split(_TITLE_SEPARATOR, 1)[0].strip()
    return title or fallback_name


def _heading_text(content: "Tag") -> str:
    """First italic or emphasized line, which carries level and school.

    Args:
        content: The page-content element.

    Returns:
        Heading text, or an empty string.
    """
    for tag_name in ("em", "i", "strong"):
        found = content.find(tag_name)
        if found is not None:
            text = _clean(found.get_text(" ", strip=True))
            if text:
                return text
    first_p = content.find("p")
    if first_p is None:
        return ""
    return _clean(first_p.get_text(" ", strip=True))


def _parse_level(heading: str) -> int:
    """Extract the spell level from a heading line.

    Args:
        heading: Level/school line.

    Returns:
        0 for a cantrip, otherwise the parsed level (default 0).
    """
    if _CANTRIP.search(heading):
        return 0
    match = _LEVEL_ORDINAL.search(heading) or _LEVEL_LABELED.search(heading)
    if match is None:
        return 0
    return int(match.group(1))


def _parse_school(heading: str) -> str:
    """Extract the school of magic from a heading line.

    Args:
        heading: Level/school line.

    Returns:
        Canonical school name, or an empty string.
    """
    match = _SCHOOL_RE.search(heading)
    if match is None:
        return ""
    return match.group(1).title()


def _labeled_fields(content: "Tag") -> Dict[str, str]:
    """Read Casting Time / Range / Components / Duration lines.

    Args:
        content: The page-content element.

    Returns:
        Map of lowercased label to value.
    """
    fields: Dict[str, str] = {}
    for para in content.find_all("p"):
        text = _clean(para.get_text(" ", strip=True))
        match = _LABEL.match(text)
        if match is None:
            continue
        fields[match.group(1).lower()] = match.group(2).strip()
    return fields


def _description_text(content: "Tag") -> str:
    """Collect remaining paragraphs as the rules text.

    Skips the level/school heading and the labeled stat-block lines.

    Args:
        content: The page-content element.

    Returns:
        Joined description paragraphs.
    """
    parts: List[str] = []
    skipped_heading = False
    for para in content.find_all("p"):
        text = _clean(para.get_text(" ", strip=True))
        if text == "":
            continue
        if _LABEL.match(text):
            continue
        if not skipped_heading:
            skipped_heading = True
            continue
        parts.append(text)
    return "\n\n".join(parts)
