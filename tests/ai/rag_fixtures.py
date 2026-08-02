"""
Shared fixtures for the rules-wiki resolver tests.

The abilities, equipment, and catalogue resolvers all reach for the same client
surface, so they would otherwise each carry an identical fake. It lives here
rather than in tests/test_helpers.py only because that module is already at its
size limit; this is the same shared-fixture role, scoped to the tests that need
it.
"""

import types
from typing import Callable, Optional


def make_fake_rules_rag(
    pages: Callable[[str], Optional[str]],
    enabled: bool = True,
) -> types.SimpleNamespace:
    """Build a RAG stand-in whose rules client serves canned page HTML.

    The client exposes the surface the resolvers reach for: ``base_url``, a
    ``session`` with ``get``, and a no-op ``cache``.

    Args:
        pages: Maps a requested URL to its HTML body; return None for a URL the
            wiki does not have, and the fake session raises like a 404 would.
        enabled: RAG enabled flag.

    Returns:
        A SimpleNamespace exposing ``enabled`` + ``rules_client``.
    """

    def _get(url: str, timeout: int = 10) -> types.SimpleNamespace:
        _ = timeout
        body = pages(url)
        if body is None:
            raise OSError(f"404 {url}")
        return types.SimpleNamespace(text=body, raise_for_status=lambda: None)

    session = types.SimpleNamespace(get=_get)
    cache = types.SimpleNamespace(get=lambda key: None, set=lambda key, content: None)
    client = types.SimpleNamespace(
        base_url="http://rules.example", session=session, cache=cache
    )
    return types.SimpleNamespace(enabled=enabled, rules_client=client)
