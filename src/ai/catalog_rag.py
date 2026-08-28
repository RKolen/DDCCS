"""Resolve which backgrounds, species, and classes exist, per sourcebook.

Reads index pages from the rules wiki at ``RAG_RULES_BASE_URL`` and returns
catalogue entries tagged with the sourcebook each came from, so a group is only
offered content from books it owns. Degrades to an empty catalogue whenever RAG
is unavailable, and never blocks character creation.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Sequence, TypedDict

from src.ai.abilities_rag import page_urls
from src.ai.rag_system import RAGSystem, get_rag_system
from src.ai.wiki_scraping import SCRAPING_AVAILABLE, fetch_html, page_content, page_title
from src.config.config_loader import load_config
from src.config.config_types import RulesetConfig

logger = logging.getLogger(__name__)


class CatalogEntry(TypedDict):
    """One character-creation option offered by the rules wiki."""

    name: str
    kind: str
    source: str


# Index page and link shape per catalogue kind. Entry pages are namespaced by
# kind (``background:harper``) except classes, which use ``<class>:main``.
_INDEX_PAGES: Dict[str, str] = {
    "background": "background:all",
    "species": "species:all",
    "class": "class:all",
}
_ENTRY_HREFS: Dict[str, "re.Pattern[str]"] = {
    "background": re.compile(r"^/background:([a-z0-9-]+)$"),
    "species": re.compile(r"^/species:([a-z0-9-]+)$"),
    "class": re.compile(r"^/([a-z0-9-]+):main$"),
}

# Index pages link to their own overview alongside the real entries.
_INDEX_SLUGS = frozenset({"all"})

# The label opening the sourcebook line at the top of every rules page.
_SOURCE_LABEL = "Source:"

# Separates an entry's own title from the site name in the HTML <title>.
_TITLE_SEPARATOR = " - D&D"

# Words the wiki capitalises in page titles but that read wrong in a name
# ("Knight Of The Gauntlet"). Lowercasing them does not change the derived page
# slug, so round-tripping a name back to its wiki page is unaffected.
_MINOR_WORDS = frozenset({
    "a", "an", "and", "at", "by", "for", "from", "in", "of", "on", "or",
    "the", "to", "with",
})


def list_catalog(kind: str, *, rag: Optional[RAGSystem] = None) -> List[CatalogEntry]:
    """List every option of one kind the rules wiki publishes.

    Args:
        kind: Catalogue kind: "background", "species", or "class".
        rag: Optional RAG system to use; resolved from config when omitted.
            Pass an explicit instance to control or bypass RAG, which aids
            testing.

    Returns:
        Entries sorted by name, each tagged with its sourcebook. Empty when the
        kind is unknown, RAG is unavailable, or the index cannot be fetched.
    """
    index_page = _INDEX_PAGES.get(kind)
    if index_page is None:
        logger.debug("Unknown catalogue kind: %s", kind)
        return []

    client = _rules_client(rag)
    if client is None:
        return []

    base_url = str(getattr(client, "base_url", ""))
    html = fetch_html(client, f"{base_url}/{index_page}")
    if html is None:
        return []

    entries = []
    for slug in _index_slugs(html, kind):
        entry = _entry_from_page(client, kind, slug)
        if entry is not None:
            entries.append(entry)
    return sorted(entries, key=lambda entry: entry["name"])


def _entry_from_page(client: object, kind: str, slug: str) -> Optional[CatalogEntry]:
    """Build one catalogue entry by reading its own wiki page.

    Args:
        client: The rules WikiClient.
        kind: Catalogue kind, selecting the page-slug form.
        slug: The entry's page slug.

    Returns:
        The entry, or None when its page cannot be fetched.
    """
    base_url = str(getattr(client, "base_url", ""))
    for url in page_urls(base_url, kind, slug):
        html = fetch_html(client, url)
        if html is None:
            continue
        return CatalogEntry(
            name=_display_name(_entry_title(html) or slug),
            kind=kind,
            source=_parse_sourcebook(html),
        )
    return None


def get_sourcebook(kind: str, name: str, *, rag: Optional[RAGSystem] = None) -> str:
    """Resolve the sourcebook that introduced one catalogue entry.

    Args:
        kind: Catalogue kind: "background", "species", or "class".
        name: The entry name (e.g. "Harper").
        rag: Optional RAG system; resolved from config when omitted.

    Returns:
        The sourcebook title (e.g. "Eberron - Forge of the Artificer"), or an
        empty string when the page carries no source line or cannot be fetched.
    """
    client = _rules_client(rag)
    if client is None:
        return ""
    entry = _entry_from_page(client, kind, name)
    return "" if entry is None else entry["source"]


def owned_sourcebooks() -> List[str]:
    """Return the configured sourcebooks whose content should be offered.

    Returns:
        The ``RAG_SOURCEBOOKS`` entries, or an empty list when unset (meaning
        no restriction).
    """
    try:
        return list(load_config().ruleset.sourcebooks)
    except (OSError, ValueError) as exc:
        logger.debug("Could not load sourcebook config: %s", exc)
        return []


def filter_by_sourcebooks(
    entries: Sequence[CatalogEntry], sourcebooks: Optional[Sequence[str]] = None
) -> List[CatalogEntry]:
    """Keep only entries introduced by one of the given sourcebooks.

    Matching is case-insensitive and substring-based, so a short configured
    name ("Eberron") selects every printing from that line.

    Args:
        entries: Catalogue entries to filter.
        sourcebooks: Sourcebook names to keep; resolved from config when
            omitted. An empty list means keep everything.

    Returns:
        The matching entries, in their original order.
    """
    wanted = list(sourcebooks) if sourcebooks is not None else owned_sourcebooks()
    ruleset = RulesetConfig(sourcebooks=wanted)
    return [entry for entry in entries if ruleset.owns(entry["source"])]


def _rules_client(rag: Optional[RAGSystem]) -> Optional[object]:
    """Resolve the rules-wiki client, returning None when unusable.

    Args:
        rag: Optional RAG system; resolved from config when omitted.

    Returns:
        The rules WikiClient, or None when RAG or scraping is unavailable.
    """
    rag_system = rag if rag is not None else _safe_rag_system()
    if rag_system is None or not getattr(rag_system, "enabled", False):
        return None
    client = getattr(rag_system, "rules_client", None)
    if client is None or not SCRAPING_AVAILABLE or getattr(client, "session", None) is None:
        return None
    return client


def _safe_rag_system() -> Optional[RAGSystem]:
    """Resolve the shared RAG system, returning None when unavailable.

    Returns:
        A RAG system instance when one can be built, otherwise None.
    """
    try:
        return get_rag_system()
    except (ImportError, OSError, ValueError) as exc:
        logger.debug("RAG system unavailable for the catalogue: %s", exc)
        return None


def _index_slugs(html: str, kind: str) -> List[str]:
    """Extract the entry slugs an index page links to.

    Args:
        html: Raw index page HTML.
        kind: Catalogue kind, selecting the link shape to match.

    Returns:
        De-duplicated slugs in first-seen order.
    """
    content = page_content(html)
    if content is None:
        return []

    pattern = _ENTRY_HREFS[kind]
    slugs: List[str] = []
    seen = set()
    for anchor in content.find_all("a", href=True):
        match = pattern.match(str(anchor["href"]))
        if match is None:
            continue
        slug = match.group(1)
        if slug in _INDEX_SLUGS or slug in seen:
            continue
        seen.add(slug)
        slugs.append(slug)
    return slugs


def _parse_sourcebook(html: str) -> str:
    """Read the sourcebook title from a rules page's leading source line.

    Args:
        html: Raw entry page HTML.

    Returns:
        The sourcebook title, or an empty string when absent.
    """
    content = page_content(html)
    if content is None:
        return ""
    for paragraph in content.find_all("p"):
        text = paragraph.get_text(" ", strip=True)
        if text.startswith(_SOURCE_LABEL):
            return text[len(_SOURCE_LABEL):].strip()
    return ""


def _entry_title(html: str) -> str:
    """Read an entry page's own title, dropping the site-name suffix.

    Args:
        html: Raw entry page HTML.

    Returns:
        The page title (e.g. "Lords' Alliance Vassal"), or an empty string.
    """
    return page_title(html).split(_TITLE_SEPARATOR)[0].strip()


def _display_name(raw: str) -> str:
    """Normalise a wiki title or page slug into a readable entry name.

    The wiki capitalises every word of a page title, which reads wrong for
    minor words ("Knight Of The Gauntlet"). Lowercasing them does not change
    the derived page slug, so the name still round-trips to its wiki page.

    Args:
        raw: A wiki page title or hyphenated slug.

    Returns:
        The normalised name (e.g. "Knight of the Gauntlet").
    """
    words = [word for word in raw.replace("-", " ").split() if word]
    named = []
    for index, word in enumerate(words):
        lowered = word.lower()
        if index > 0 and lowered in _MINOR_WORDS:
            named.append(lowered)
        elif word.isupper() or not word.islower():
            named.append(word)
        else:
            named.append(word.capitalize())
    return " ".join(named)
