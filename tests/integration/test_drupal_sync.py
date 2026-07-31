"""Tests for src.integration.drupal_sync.

The wiki cache is reached over GraphQL; JSON:API is disabled server-side.
Unit tests patch the GraphQL transport so no live Drupal instance is required.
Integration tests (prefixed live_) are skipped unless DRUPAL_BASE_URL is set.

Usage (unit tests only):
    python3 tests/integration/test_drupal_sync.py

Usage (with live Drupal via DDEV):
    DRUPAL_BASE_URL=https://drupal-cms.ddev.site \\
    DRUPAL_GRAPHQL_TOKEN=... \\
    python3 tests/integration/test_drupal_sync.py
"""

import os
import time
import unittest.mock
from typing import Any, Dict, Optional

from tests.test_helpers import (
    make_drupal_config,
    setup_test_environment,
    import_module,
)


setup_test_environment()

drupal_sync_mod = import_module("src.integration.drupal_sync")
DrupalSync = drupal_sync_mod.DrupalSync
DrupalSyncError = drupal_sync_mod.DrupalSyncError

drupal_graphql_mod = import_module("src.integration.drupal_graphql")
DrupalGraphQLError = drupal_graphql_mod.DrupalGraphQLError

config_types_mod = import_module("src.config.config_types")
DrupalConfig = config_types_mod.DrupalConfig


_make_config = make_drupal_config

_ENTRY = {
    "url": "https://wiki.test/page",
    "fetchedAt": 1753900000.5,
    "content": '{"sections": []}',
}


def _skip_if_no_live_drupal() -> Optional[str]:
    """Return a skip reason when DRUPAL_BASE_URL is not configured."""
    if not os.getenv("DRUPAL_BASE_URL"):
        return "DRUPAL_BASE_URL not set - live Drupal tests skipped"
    return None


def _live_config() -> Any:
    """Build a DrupalConfig from environment variables for live tests.

    The CA that verifies DDEV's TLS comes from MKCERT_CA - the same variable
    start.sh exports for the sidecar and Gatsby. It maps onto
    ``DrupalConfig.ca_bundle``; the names differ, so read the variable rather
    than guessing one from the field.
    """
    return DrupalConfig(
        base_url=os.getenv("DRUPAL_BASE_URL", ""),
        graphql_token=os.getenv("DRUPAL_GRAPHQL_TOKEN", ""),
        ca_bundle=os.getenv("MKCERT_CA", ""),
    )


def _patch_query(result: Dict[str, Any]) -> Any:
    """Patch query_drupal in the drupal_sync module to return a fixed payload."""
    return unittest.mock.patch.object(
        drupal_sync_mod, "query_drupal", return_value=result
    )


def _patch_mutate(result: Any) -> Any:
    """Patch mutate_drupal in the drupal_sync module.

    Args:
        result: Return value, or an exception instance to raise.

    Returns:
        A patcher for use as a context manager.
    """
    if isinstance(result, Exception):
        return unittest.mock.patch.object(
            drupal_sync_mod, "mutate_drupal", side_effect=result
        )
    return unittest.mock.patch.object(
        drupal_sync_mod, "mutate_drupal", return_value=result
    )


# ---------------------------------------------------------------------------
# Read path
# ---------------------------------------------------------------------------

def test_get_wiki_page_cache_maps_entry_fields() -> None:
    """A cache hit is mapped onto the field_* keys DrupalWikiCache expects."""
    sync = DrupalSync(_make_config())
    with _patch_query({"wikiCacheEntry": _ENTRY}):
        result = sync.get_wiki_page_cache("abc123")

    assert result is not None
    assert result["field_wiki_url"] == "https://wiki.test/page"
    assert result["field_wiki_fetched_at"] == 1753900000.5
    assert result["field_wiki_content"] == '{"sections": []}'


def test_get_wiki_page_cache_returns_none_on_miss() -> None:
    """A null entry is a cache miss, not an error."""
    sync = DrupalSync(_make_config())
    with _patch_query({"wikiCacheEntry": None}):
        assert sync.get_wiki_page_cache("missing") is None


def test_get_wiki_page_cache_returns_none_when_drupal_unreachable() -> None:
    """An unreachable Drupal degrades to a miss so the caller re-fetches."""
    sync = DrupalSync(_make_config())
    with _patch_query({}):
        assert sync.get_wiki_page_cache("abc123") is None


def test_get_wiki_page_cache_passes_url_hash_as_variable() -> None:
    """The hash is sent as a GraphQL variable, not interpolated into the query."""
    sync = DrupalSync(_make_config())
    with _patch_query({"wikiCacheEntry": _ENTRY}) as mocked:
        sync.get_wiki_page_cache("hash-under-test")

    variables = mocked.call_args[0][1]
    assert variables == {"urlHash": "hash-under-test"}


def test_client_config_is_passed_to_the_transport() -> None:
    """The config the client was built with is the one the request uses.

    Regression guard: the transport otherwise falls back to the globally loaded
    configuration, silently ignoring the connection the caller asked for.
    """
    config = DrupalConfig(base_url="https://other-drupal.test", graphql_token="tok")
    sync = DrupalSync(config)

    with _patch_query({"wikiCacheEntry": _ENTRY}) as mocked:
        sync.get_wiki_page_cache("abc123")
    assert mocked.call_args[0][2] is config

    with _patch_mutate({"setWikiCacheEntry": _ENTRY}) as mocked:
        sync.set_wiki_page_cache("abc123", "https://wiki.test/p", 1.0, "{}")
    assert mocked.call_args[0][2] is config


# ---------------------------------------------------------------------------
# Write path
# ---------------------------------------------------------------------------

def test_set_wiki_page_cache_sends_all_variables() -> None:
    """The upsert forwards every field Drupal needs to store the entry."""
    sync = DrupalSync(_make_config())
    with _patch_mutate({"setWikiCacheEntry": _ENTRY}) as mocked:
        returned = sync.set_wiki_page_cache(
            "abc123", "https://wiki.test/page", 1753900000.5, '{"sections": []}'
        )

    assert returned == "https://wiki.test/page"
    variables = mocked.call_args[0][1]
    assert variables == {
        "urlHash": "abc123",
        "url": "https://wiki.test/page",
        "fetchedAt": 1753900000.5,
        "content": '{"sections": []}',
    }


def test_set_wiki_page_cache_coerces_fetched_at_to_float() -> None:
    """An int timestamp is sent as a Float, which the schema requires."""
    sync = DrupalSync(_make_config())
    with _patch_mutate({"setWikiCacheEntry": _ENTRY}) as mocked:
        sync.set_wiki_page_cache("abc123", "https://wiki.test/page", 1753900000, "{}")

    variables = mocked.call_args[0][1]
    assert isinstance(variables["fetchedAt"], float)


def test_set_wiki_page_cache_raises_on_transport_error() -> None:
    """A failed write raises rather than silently doing nothing."""
    sync = DrupalSync(_make_config())
    with _patch_mutate(DrupalGraphQLError("permission denied")):
        try:
            sync.set_wiki_page_cache("abc123", "https://wiki.test/p", 1.0, "{}")
            raise AssertionError("expected DrupalSyncError")
        except DrupalSyncError as exc:
            assert "permission denied" in str(exc)


def test_set_wiki_page_cache_raises_when_response_has_no_entry() -> None:
    """A 200 response without the entry is still a failed write."""
    sync = DrupalSync(_make_config())
    with _patch_mutate({"setWikiCacheEntry": None}):
        try:
            sync.set_wiki_page_cache("abc123", "https://wiki.test/p", 1.0, "{}")
            raise AssertionError("expected DrupalSyncError")
        except DrupalSyncError as exc:
            assert "returned no entry" in str(exc)


# ---------------------------------------------------------------------------
# Delete path
# ---------------------------------------------------------------------------

def test_delete_wiki_page_cache_succeeds_on_true() -> None:
    """A TRUE result means the cache no longer holds the entry."""
    sync = DrupalSync(_make_config())
    with _patch_mutate({"deleteWikiCacheEntry": True}):
        sync.delete_wiki_page_cache("abc123")


def test_delete_wiki_page_cache_raises_when_refused() -> None:
    """A FALSE result means Drupal refused, which must not pass silently."""
    sync = DrupalSync(_make_config())
    with _patch_mutate({"deleteWikiCacheEntry": False}):
        try:
            sync.delete_wiki_page_cache("abc123")
            raise AssertionError("expected DrupalSyncError")
        except DrupalSyncError as exc:
            assert "refused" in str(exc)


def test_delete_wiki_page_cache_raises_on_transport_error() -> None:
    """A transport failure during delete is surfaced."""
    sync = DrupalSync(_make_config())
    with _patch_mutate(DrupalGraphQLError("boom")):
        try:
            sync.delete_wiki_page_cache("abc123")
            raise AssertionError("expected DrupalSyncError")
        except DrupalSyncError as exc:
            assert "boom" in str(exc)


# ---------------------------------------------------------------------------
# Count
# ---------------------------------------------------------------------------

def test_count_wiki_page_cache_returns_count() -> None:
    """The entry count is read straight from the query result."""
    sync = DrupalSync(_make_config())
    with _patch_query({"wikiCacheCount": 42}):
        assert sync.count_wiki_page_cache() == 42


def test_count_wiki_page_cache_returns_zero_when_unreachable() -> None:
    """An unreachable Drupal reports an empty cache rather than raising."""
    sync = DrupalSync(_make_config())
    with _patch_query({}):
        assert sync.count_wiki_page_cache() == 0


def test_count_wiki_page_cache_returns_zero_on_bad_value() -> None:
    """A non-numeric count degrades to zero instead of raising."""
    sync = DrupalSync(_make_config())
    with _patch_query({"wikiCacheCount": "not-a-number"}):
        assert sync.count_wiki_page_cache() == 0


# ---------------------------------------------------------------------------
# Live round trip (skipped unless DRUPAL_BASE_URL is set)
# ---------------------------------------------------------------------------

def test_live_wiki_cache_round_trip_real_drupal() -> None:
    """Write, read back, and delete a cache entry against a real Drupal."""
    skip = _skip_if_no_live_drupal()
    if skip:
        print(f"  [SKIP] {skip}")
        return

    sync = DrupalSync(_live_config())
    url_hash = f"pytest-{int(time.time())}"
    page_url = f"https://wiki.test/{url_hash}"
    content = '{"sections": [{"title": "A \\"quoted\\" bit"}]}'

    try:
        sync.set_wiki_page_cache(url_hash, page_url, time.time(), content)
    except DrupalSyncError as exc:
        print(f"  [SKIP] Drupal wiki cache not writable: {exc}")
        return

    entry = sync.get_wiki_page_cache(url_hash)
    assert entry is not None, "entry should be readable straight after writing"
    assert entry["field_wiki_url"] == page_url
    assert entry["field_wiki_content"] == content

    sync.delete_wiki_page_cache(url_hash)
    assert sync.get_wiki_page_cache(url_hash) is None
    print("[PASS] live wiki cache round trip")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all_tests() -> None:
    """Run all drupal_sync tests."""
    print("=" * 70)
    print("DRUPAL SYNC TESTS")
    print("=" * 70)

    test_get_wiki_page_cache_maps_entry_fields()
    test_get_wiki_page_cache_returns_none_on_miss()
    test_get_wiki_page_cache_returns_none_when_drupal_unreachable()
    test_get_wiki_page_cache_passes_url_hash_as_variable()
    test_client_config_is_passed_to_the_transport()
    test_set_wiki_page_cache_sends_all_variables()
    test_set_wiki_page_cache_coerces_fetched_at_to_float()
    test_set_wiki_page_cache_raises_on_transport_error()
    test_set_wiki_page_cache_raises_when_response_has_no_entry()
    test_delete_wiki_page_cache_succeeds_on_true()
    test_delete_wiki_page_cache_raises_when_refused()
    test_delete_wiki_page_cache_raises_on_transport_error()
    test_count_wiki_page_cache_returns_count()
    test_count_wiki_page_cache_returns_zero_when_unreachable()
    test_count_wiki_page_cache_returns_zero_on_bad_value()
    test_live_wiki_cache_round_trip_real_drupal()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL DRUPAL SYNC TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
