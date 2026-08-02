"""Shared Wikidot scraping primitives for the rules-wiki resolvers.

Every rules-wiki resolver needs the same three things: an optional BeautifulSoup
import that must not break the app when the scraping extras are absent, the
``#page-content`` element a Wikidot page wraps its body in, and a page fetch
that degrades to None instead of raising. They live here so the resolvers in
this package share one implementation rather than each carrying a copy.
"""

from __future__ import annotations

import logging
from typing import List, Optional, cast

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
