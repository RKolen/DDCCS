"""Shared Wikidot scraping primitives for the rules-wiki resolvers.

Every rules-wiki resolver needs the same four things: an optional BeautifulSoup
import that must not break the app when the scraping extras are absent, the
``#page-content`` element a Wikidot page wraps its body in, a page fetch
that degrades to None instead of raising, and a ready rules-wiki client.
They live here so the resolvers in this package share one implementation
rather than each carrying a copy.
"""

from __future__ import annotations

import logging
from typing import List, Optional, cast

from src.ai.rag_system import RAGSystem, get_rag_system

try:
    from bs4 import BeautifulSoup
    from bs4.element import Tag
    SCRAPING_AVAILABLE = True
except ImportError:
    SCRAPING_AVAILABLE = False

logger = logging.getLogger(__name__)

# How long to wait on a single rules-wiki page before giving up.
_TIMEOUT = 10


def page_content(html: str) -> Optional["Tag"]:
    """Extract the ``#page-content`` element a Wikidot page wraps its body in.

    Args:
        html: Raw page HTML.

    Returns:
        The content element, or None when scraping is unavailable or the page
        has no content wrapper.
    """
    if not SCRAPING_AVAILABLE:
        return None
    found = BeautifulSoup(html, "html.parser").find("div", id="page-content")
    if not isinstance(found, Tag):
        return None
    return cast("Tag", found)


def page_title(html: str) -> str:
    """Read a page's HTML title.

    Args:
        html: Raw page HTML.

    Returns:
        The title text, or an empty string when scraping is unavailable or the
        page has no title.
    """
    if not SCRAPING_AVAILABLE:
        return ""
    title = BeautifulSoup(html, "html.parser").title
    return "" if title is None else title.get_text(strip=True)


def fetch_html(client: object, url: str) -> Optional[str]:
    """Fetch a page's HTML, returning None on any failure.

    Args:
        client: A WikiClient (provides a requests session).
        url: Absolute page URL.

    Returns:
        The raw HTML body, or None when the request fails.
    """
    session = getattr(client, "session", None)
    if session is None:
        return None
    try:
        response = session.get(url, timeout=_TIMEOUT)
        response.raise_for_status()
    except OSError as exc:
        logger.debug("Wiki page fetch failed for %s: %s", url, exc)
        return None
    return str(response.text)


def fetch_first(client: object, urls: List[str]) -> Optional[str]:
    """Fetch the first URL in a candidate list that resolves.

    Args:
        client: A WikiClient (provides a requests session).
        urls: Ordered candidate page URLs.

    Returns:
        The first successfully fetched page HTML, or None when none resolve.
    """
    for url in urls:
        html = fetch_html(client, url)
        if html is not None:
            return html
    return None


def ready_rules_client(rag: Optional[RAGSystem] = None) -> Optional[object]:
    """Return the rules-wiki client when RAG scraping is usable.

    Args:
        rag: Optional RAG system; resolved from config when omitted.

    Returns:
        The wiki client when enabled with a session, otherwise None.
    """
    try:
        rag_system = rag if rag is not None else get_rag_system()
    except (ImportError, OSError, ValueError) as exc:
        logger.debug("RAG system unavailable: %s", exc)
        return None
    if rag_system is None or not getattr(rag_system, "enabled", False):
        return None
    client = getattr(rag_system, "rules_client", None)
    if client is None or not SCRAPING_AVAILABLE or getattr(client, "session", None) is None:
        return None
    return client
