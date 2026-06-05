"""
Test RAG System (Retrieval-Augmented Generation)

Tests the DrupalWikiCache and WikiClient classes using a mock DrupalSync so
no live Drupal instance or internet connection is required.

What we test:
- DrupalWikiCache with no sync configured (graceful no-op)
- DrupalWikiCache set/get/delete/stats via MockDrupalSync
- TTL expiration logic
- DrupalSyncError graceful handling (cache miss on error)
- WikiClient initialization and URL normalization
- Custom item filtering via item registry

Why we test this:
- Ensures wiki content is cached correctly via Drupal
- Validates TTL expiration prevents stale data
- Confirms custom items block wiki lookups (homebrew filtering)
- Verifies graceful degradation when Drupal is unavailable
"""

import hashlib
import time
from tests import test_helpers
from src.integration.drupal_sync import DrupalSyncError

# Import RAG system components using centralized helper
(
    DrupalWikiCache,
    WikiClient,
    WikiCacheProtocol,
    RAGSystem,
    _RELEVANCE_TITLE_MATCH,
    _RELEVANCE_TITLE_WORD,
    _RELEVANCE_CONTENT_WORD,
) = test_helpers.safe_from_import(
    "src.ai.rag_system",
    "DrupalWikiCache",
    "WikiClient",
    "WikiCacheProtocol",
    "RAGSystem",
    "_RELEVANCE_TITLE_MATCH",
    "_RELEVANCE_TITLE_WORD",
    "_RELEVANCE_CONTENT_WORD",
)


class MockDrupalSync:
    """In-memory DrupalSync stand-in for testing DrupalWikiCache."""

    def __init__(self):
        self._store = {}

    def _key(self, url_hash):
        return url_hash

    def get_wiki_page_cache(self, url_hash):
        """Return stored entry or None."""
        return self._store.get(self._key(url_hash))

    def set_wiki_page_cache(self, url_hash, url, fetched_at, content_json):
        """Store a cache entry and return a fake UUID."""
        self._store[self._key(url_hash)] = {
            "field_wiki_url": url,
            "field_wiki_fetched_at": fetched_at,
            "field_wiki_content": content_json,
        }
        return "mock-uuid"

    def delete_wiki_page_cache(self, url_hash):
        """Remove entry if present."""
        self._store.pop(self._key(url_hash), None)

    def count_wiki_page_cache(self):
        """Return number of stored entries."""
        return len(self._store)

    def backdate_entry(self, url, age_seconds):
        """Move field_wiki_fetched_at backward to simulate an aged entry."""
        key = hashlib.md5(url.encode("utf-8")).hexdigest()
        if key in self._store:
            self._store[key]["field_wiki_fetched_at"] = time.time() - age_seconds

    def corrupt_entry(self, url, bad_json):
        """Replace content with bad JSON to simulate corruption."""
        key = hashlib.md5(url.encode("utf-8")).hexdigest()
        if key in self._store:
            self._store[key]["field_wiki_content"] = bad_json

    def wrap_content_as_dict(self, url):
        """Wrap field_wiki_content in Drupal text_long dict format."""
        key = hashlib.md5(url.encode("utf-8")).hexdigest()
        if key in self._store:
            raw = self._store[key]["field_wiki_content"]
            self._store[key]["field_wiki_content"] = {"value": raw, "format": "plain_text"}


class ErrorDrupalSync:
    """DrupalSync stub that raises DrupalSyncError on every call."""

    def get_wiki_page_cache(self, url_hash):
        """Always raise DrupalSyncError."""
        raise DrupalSyncError("connection refused")

    def set_wiki_page_cache(self, url_hash, url, fetched_at, content_json):
        """Always raise DrupalSyncError."""
        raise DrupalSyncError("connection refused")

    def delete_wiki_page_cache(self, url_hash):
        """Always raise DrupalSyncError."""
        raise DrupalSyncError("connection refused")

    def count_wiki_page_cache(self):
        """Always raise DrupalSyncError."""
        raise DrupalSyncError("connection refused")


def test_drupal_wiki_cache_no_sync():
    """DrupalWikiCache with no sync configured behaves as a no-op."""
    print("\n[TEST] DrupalWikiCache - No Sync Configured")

    cache = DrupalWikiCache(drupal_sync=None, ttl_seconds=3600)

    assert cache.get("https://example.com/wiki/Page") is None, "get should return None"
    print("  [OK] get() returns None")

    cache.set("https://example.com/wiki/Page", {"title": "Page"})
    print("  [OK] set() is a no-op (no exception)")

    cache.delete("https://example.com/wiki/Page")
    print("  [OK] delete() is a no-op (no exception)")

    stats = cache.get_stats()
    assert stats["entries"] == 0, "Entry count should be 0"
    print("  [OK] get_stats() returns 0 entries")

    cache.clear_expired()
    print("  [OK] clear_expired() is a no-op (no exception)")

    print("[PASS] DrupalWikiCache - No Sync Configured")


def test_drupal_wiki_cache_set_and_get():
    """DrupalWikiCache stores and retrieves page data via MockDrupalSync."""
    print("\n[TEST] DrupalWikiCache Set and Get")

    sync = MockDrupalSync()
    cache = DrupalWikiCache(drupal_sync=sync, ttl_seconds=3600)

    test_url = "https://example.com/wiki/TestPage"
    test_content = {
        "title": "Test Page",
        "sections": [{"title": "Introduction", "content": "Intro text"}],
    }

    cache.set(test_url, test_content)
    print("  [OK] Content stored")

    retrieved = cache.get(test_url)
    assert retrieved is not None, "Failed to retrieve cached content"
    assert retrieved["title"] == "Test Page", "Title mismatch"
    assert len(retrieved["sections"]) == 1, "Sections mismatch"
    print("  [OK] Content retrieved correctly")

    stats = cache.get_stats()
    assert stats["entries"] == 1, "Entry count should be 1"
    assert stats["backend"] == "drupal", "Backend label incorrect"
    print("  [OK] Stats report 1 entry")

    print("[PASS] DrupalWikiCache Set and Get")


def test_drupal_wiki_cache_key_uniqueness():
    """Different URLs produce independent cache entries."""
    print("\n[TEST] DrupalWikiCache Key Uniqueness")

    sync = MockDrupalSync()
    cache = DrupalWikiCache(drupal_sync=sync, ttl_seconds=3600)

    url_a = "https://example.com/wiki/PageA"
    url_b = "https://example.com/wiki/PageB"
    cache.set(url_a, {"title": "Page A"})
    cache.set(url_b, {"title": "Page B"})

    result_a = cache.get(url_a)
    result_b = cache.get(url_b)

    assert result_a is not None and result_a["title"] == "Page A", "Page A mismatch"
    assert result_b is not None and result_b["title"] == "Page B", "Page B mismatch"
    assert sync.count_wiki_page_cache() == 2, "Expected 2 entries"
    print("  [OK] Different URLs cached independently")

    print("[PASS] DrupalWikiCache Key Uniqueness")


def test_drupal_wiki_cache_ttl_expiration():
    """DrupalWikiCache respects TTL and returns None for expired entries."""
    print("\n[TEST] DrupalWikiCache TTL Expiration")

    sync = MockDrupalSync()
    cache = DrupalWikiCache(drupal_sync=sync, ttl_seconds=3600)

    test_url = "https://example.com/wiki/ExpirePage"
    cache.set(test_url, {"title": "Expire Page"})

    sync.backdate_entry(test_url, 7200)
    print("  [OK] Entry back-dated 2 hours beyond TTL")

    expired = cache.get(test_url)
    assert expired is None, "Expired entry should return None"
    print("  [OK] Expired entry returns None")

    assert sync.count_wiki_page_cache() == 0, "Expired entry should be deleted on read"
    print("  [OK] Expired entry deleted on read")

    print("[PASS] DrupalWikiCache TTL Expiration")


def test_drupal_wiki_cache_delete():
    """DrupalWikiCache delete removes the entry."""
    print("\n[TEST] DrupalWikiCache Delete")

    sync = MockDrupalSync()
    cache = DrupalWikiCache(drupal_sync=sync, ttl_seconds=3600)

    test_url = "https://example.com/wiki/DeletePage"
    cache.set(test_url, {"title": "Delete Page"})
    assert cache.get(test_url) is not None, "Entry not stored"
    print("  [OK] Entry stored")

    cache.delete(test_url)
    assert cache.get(test_url) is None, "Entry should be gone after delete"
    print("  [OK] Entry gone after delete")

    assert sync.count_wiki_page_cache() == 0, "Entry count should be 0"
    print("  [OK] Entry count is 0")

    print("[PASS] DrupalWikiCache Delete")


def test_drupal_wiki_cache_drupal_error_graceful():
    """DrupalSyncError in get() causes cache miss, not a crash."""
    print("\n[TEST] DrupalWikiCache DrupalSyncError Graceful Handling")

    cache = DrupalWikiCache(drupal_sync=ErrorDrupalSync(), ttl_seconds=3600)

    result = cache.get("https://example.com/wiki/Any")
    assert result is None, "DrupalSyncError should yield cache miss (None)"
    print("  [OK] DrupalSyncError in get() treated as cache miss")

    cache.set("https://example.com/wiki/Any", {"title": "Any"})
    print("  [OK] DrupalSyncError in set() logged, no exception raised")

    stats = cache.get_stats()
    assert stats["entries"] == 0, "Stats should return 0 on error"
    print("  [OK] DrupalSyncError in stats returns 0 entries")

    print("[PASS] DrupalWikiCache DrupalSyncError Graceful Handling")


def test_drupal_wiki_cache_invalid_json():
    """DrupalWikiCache handles corrupt JSON content gracefully."""
    print("\n[TEST] DrupalWikiCache Invalid JSON Handling")

    sync = MockDrupalSync()
    cache = DrupalWikiCache(drupal_sync=sync, ttl_seconds=3600)

    test_url = "https://example.com/wiki/CorruptPage"
    cache.set(test_url, {"title": "Corrupt Page"})

    sync.corrupt_entry(test_url, "not valid json {{{")

    result = cache.get(test_url)
    assert result is None, "Corrupt JSON should yield None"
    print("  [OK] Corrupt JSON returns None and deletes entry")

    assert sync.count_wiki_page_cache() == 0, "Corrupt entry should be deleted"
    print("  [OK] Corrupt entry cleaned up")

    print("[PASS] DrupalWikiCache Invalid JSON Handling")


def test_wiki_client_initialization():
    """WikiClient initializes with correct base URL and cache."""
    print("\n[TEST] WikiClient Initialization")

    sync = MockDrupalSync()
    custom_cache = DrupalWikiCache(drupal_sync=sync, ttl_seconds=3600)

    client1 = WikiClient(base_url="https://example.com/wiki")
    assert client1.base_url == "https://example.com/wiki", "Base URL not set"
    assert client1.cache is not None, "Cache not created"
    print("  [OK] Client with default cache initialized")

    client2 = WikiClient(base_url="https://example.com/wiki", cache=custom_cache)
    assert client2.cache is custom_cache, "Custom cache not used"
    print("  [OK] Client with custom cache initialized")

    client3 = WikiClient(base_url="https://example.com/wiki/")
    assert client3.base_url == "https://example.com/wiki", "Trailing slash not removed"
    print("  [OK] Base URL normalized (trailing slash removed)")

    print("[PASS] WikiClient Initialization")


def test_wiki_client_custom_item_filtering():
    """Custom items block wiki lookups via item registry."""
    print("\n[TEST] WikiClient Custom Item Filtering")

    class MockItemRegistry:
        """Mock ItemRegistry for testing custom item filtering."""

        def __init__(self):
            self.custom_items = {"Sword of Testing", "Magic Test Shield"}

        def is_custom(self, item_name):
            """Return True if item is in the custom set."""
            return item_name in self.custom_items

        def item_count(self):
            """Return number of custom items registered."""
            return len(self.custom_items)

    sync = MockDrupalSync()
    cache = DrupalWikiCache(drupal_sync=sync, ttl_seconds=3600)
    registry = MockItemRegistry()

    client = WikiClient(
        base_url="https://example.com/wiki",
        cache=cache,
        item_registry=registry,
    )
    assert client.item_registry is registry, "Item registry not set"
    print("  [OK] Client initialized with item registry")

    result = client.fetch_page("Sword of Testing")
    assert result is None, "Custom item lookup should be blocked"
    print("  [OK] Custom item lookup blocked (returns None)")

    print("[PASS] WikiClient Custom Item Filtering")


def test_drupal_wiki_cache_content_as_dict():
    """DrupalWikiCache handles Drupal text_long dict format for content field."""
    print("\n[TEST] DrupalWikiCache Content Dict Format")

    sync = MockDrupalSync()
    cache = DrupalWikiCache(drupal_sync=sync, ttl_seconds=3600)

    test_url = "https://example.com/wiki/DictPage"
    cache.set(test_url, {"title": "Dict Page", "sections": []})

    sync.wrap_content_as_dict(test_url)

    result = cache.get(test_url)
    assert result is not None, "Should handle dict-format content field"
    assert result["title"] == "Dict Page", "Title mismatch after dict unwrap"
    print("  [OK] Dict-format content field (text_long) unwrapped correctly")

    print("[PASS] DrupalWikiCache Content Dict Format")


def test_wiki_cache_protocol_satisfaction():
    """DrupalWikiCache satisfies WikiCacheProtocol (runtime_checkable)."""
    print("\n[TEST] WikiCacheProtocol Satisfaction")

    cache = DrupalWikiCache(drupal_sync=None, ttl_seconds=3600)
    assert isinstance(cache, WikiCacheProtocol), (
        "DrupalWikiCache does not satisfy WikiCacheProtocol"
    )
    print("  [OK] DrupalWikiCache satisfies WikiCacheProtocol")

    print("[PASS] WikiCacheProtocol Satisfaction")


def test_wiki_client_max_fetches_per_call():
    """WikiClient exposes max_fetches_per_call with correct default and override."""
    print("\n[TEST] WikiClient max_fetches_per_call")

    client_default = WikiClient(base_url="https://example.com/wiki")
    assert client_default.max_fetches_per_call == 5, "Default should be 5"
    print("  [OK] Default max_fetches_per_call is 5")

    client_custom = WikiClient(
        base_url="https://example.com/wiki",
        max_fetches_per_call=2,
    )
    assert client_custom.max_fetches_per_call == 2, "Custom value not set"
    print("  [OK] Custom max_fetches_per_call accepted")

    print("[PASS] WikiClient max_fetches_per_call")


def test_relevance_scoring_constants():
    """Relevance-scoring weights are exported as module-level constants."""
    print("\n[TEST] Relevance Scoring Constants")

    assert _RELEVANCE_TITLE_MATCH == 2.0, "_RELEVANCE_TITLE_MATCH should be 2.0"
    assert _RELEVANCE_TITLE_WORD == 0.5, "_RELEVANCE_TITLE_WORD should be 0.5"
    assert _RELEVANCE_CONTENT_WORD == 0.1, "_RELEVANCE_CONTENT_WORD should be 0.1"
    assert _RELEVANCE_TITLE_MATCH > _RELEVANCE_TITLE_WORD > _RELEVANCE_CONTENT_WORD, (
        "Title match should outrank title word which outranks content word"
    )
    print("  [OK] _RELEVANCE_TITLE_MATCH = 2.0")
    print("  [OK] _RELEVANCE_TITLE_WORD = 0.5")
    print("  [OK] _RELEVANCE_CONTENT_WORD = 0.1")

    print("[PASS] Relevance Scoring Constants")


class _DisabledRAGConfig:
    """Minimal RAGConfig stub that disables all RAG features."""

    enabled = False
    wiki_base_url = ""
    rules_base_url = ""
    cache_ttl = 3600

    def is_configured(self) -> bool:
        """Return False — RAG is disabled."""
        return False

    def to_dict(self) -> dict:
        """Return minimal config dict."""
        return {"enabled": False}


def test_get_context_unified_method():
    """RAGSystem.get_context() returns empty string when disabled."""
    print("\n[TEST] get_context() Unified Method")

    rag = RAGSystem(rag_config=_DisabledRAGConfig())
    result = rag.get_context("The party enters Whitestone", campaign_name="test")
    assert result == "", "Disabled RAGSystem should return empty string"
    print("  [OK] Disabled RAGSystem returns empty string")

    result_no_semantic = rag.get_context(
        "Fireball strikes the goblins", prefer_semantic=False
    )
    assert result_no_semantic == "", "No wiki client gives empty string"
    print("  [OK] prefer_semantic=False with no wiki client returns empty string")

    print("[PASS] get_context() Unified Method")


def run_all_tests():
    """Run all RAG system tests."""
    print("=" * 70)
    print("RAG SYSTEM TESTS")
    print("=" * 70)

    test_drupal_wiki_cache_no_sync()
    test_drupal_wiki_cache_set_and_get()
    test_drupal_wiki_cache_key_uniqueness()
    test_drupal_wiki_cache_ttl_expiration()
    test_drupal_wiki_cache_delete()
    test_drupal_wiki_cache_drupal_error_graceful()
    test_drupal_wiki_cache_invalid_json()
    test_wiki_client_initialization()
    test_wiki_client_custom_item_filtering()
    test_drupal_wiki_cache_content_as_dict()
    test_wiki_cache_protocol_satisfaction()
    test_wiki_client_max_fetches_per_call()
    test_relevance_scoring_constants()
    test_get_context_unified_method()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL RAG SYSTEM TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
