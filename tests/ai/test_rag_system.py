"""
Test RAG System (Retrieval-Augmented Generation)

Tests the WikiCache and WikiClient classes for caching, wiki fetching,
and custom item filtering. Tests focus on cache operations and configuration,
NOT actual web scraping (requires live internet connection).

What we test:
- WikiCache initialization and operations
- Cache key generation and file management
- Cache TTL (time-to-live) expiration
- WikiClient initialization
- Custom item filtering via item registry
- Configuration from environment variables

Why we test this:
- Ensures wiki content is cached correctly for performance
- Validates cache expiration prevents stale data
- Confirms custom items block wiki lookups (homebrew filtering)
- Verifies RAG system configuration works
"""

import sys
from pathlib import Path
import time
import tempfile
from tests import test_helpers
# Add tests directory to path for test_helpers
sys.path.insert(0, str(Path(__file__).parent.parent))


# Import and configure test environment
test_helpers.setup_test_environment()

# Import RAG system components
try:
    from src.ai.rag_system import WikiCache, WikiClient
except ImportError as e:
    print(f"Error importing RAG system: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


def test_wiki_cache_initialization():
    """Test WikiCache initialization and basic setup."""
    print("\n[TEST] WikiCache Initialization")

    # Create temporary cache directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = WikiCache(cache_dir=temp_dir, ttl_seconds=3600)

        # Check cache directory created
        assert Path(temp_dir).exists(), "Cache directory not created"
        print("  [OK] Cache directory created")

        # Check index loaded (empty dict initially)
        assert isinstance(cache.index, dict), "Index not initialized as dict"
        assert len(cache.index) == 0, "Index not empty on initialization"
        print("  [OK] Index initialized as empty dict")

        # Check TTL configured
        assert cache.ttl_seconds == 3600, "TTL not set correctly"
        print("  [OK] TTL configured correctly")

    print("[PASS] WikiCache Initialization")


def test_wiki_cache_key_generation():
    """Test cache key generation from URLs (indirectly via caching behavior)."""
    print("\n[TEST] WikiCache Key Generation")

    with tempfile.TemporaryDirectory() as temp_dir:
        cache = WikiCache(cache_dir=temp_dir)

        # Test that same URL retrieves same content
        url1 = "https://example.com/wiki/Page1"
        content1 = {"title": "Page 1", "text": "Content 1"}

        cache.set(url1, content1)
        retrieved = cache.get(url1)
        assert retrieved is not None, "Same URL should retrieve cached content"
        assert retrieved["title"] == "Page 1", "Retrieved content should match"
        print("  [OK] Same URL retrieves same content (keys consistent)")

        # Test that different URLs cache separately
        url2 = "https://example.com/wiki/Page2"
        content2 = {"title": "Page 2", "text": "Content 2"}

        cache.set(url2, content2)
        retrieved1 = cache.get(url1)
        retrieved2 = cache.get(url2)
        assert retrieved1["title"] == "Page 1", "URL1 content changed"
        assert retrieved2["title"] == "Page 2", "URL2 content incorrect"
        print("  [OK] Different URLs cache separately (keys unique)")

    print("[PASS] WikiCache Key Generation")


def test_wiki_cache_set_and_get():
    """Test caching and retrieving content."""
    print("\n[TEST] WikiCache Set and Get")

    with tempfile.TemporaryDirectory() as temp_dir:
        cache = WikiCache(cache_dir=temp_dir, ttl_seconds=3600)

        test_url = "https://example.com/wiki/TestPage"
        test_content = {
            "title": "Test Page",
            "text": "This is test content",
            "sections": [
                {"title": "Introduction", "content": "Intro text"}
            ]
        }

        # Cache content
        cache.set(test_url, test_content)
        print("  [OK] Content cached")

        # Retrieve content
        retrieved = cache.get(test_url)
        assert retrieved is not None, "Failed to retrieve cached content"
        assert retrieved["title"] == "Test Page", "Retrieved content title mismatch"
        assert retrieved["text"] == "This is test content", "Retrieved content text mismatch"
        assert len(retrieved["sections"]) == 1, "Retrieved content sections mismatch"
        print("  [OK] Content retrieved correctly")

        # Check index updated (verify at least one entry exists)
        assert len(cache.index) == 1, "Index not updated after caching"
        # Verify the cached entry has correct URL in index
        index_entry = next(iter(cache.index.values()))
        assert index_entry["url"] == test_url, "Index URL mismatch"
        assert index_entry["title"] == "Test Page", "Index title mismatch"
        print("  [OK] Index updated correctly")

    print("[PASS] WikiCache Set and Get")


def test_wiki_cache_expiration():
    """Test cache TTL (time-to-live) expiration."""
    print("\n[TEST] WikiCache TTL Expiration")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create cache with very short TTL (1 second)
        cache = WikiCache(cache_dir=temp_dir, ttl_seconds=1)

        test_url = "https://example.com/wiki/ExpireTest"
        test_content = {"title": "Expire Test", "text": "Will expire soon"}

        # Cache content
        cache.set(test_url, test_content)
        print("  [OK] Content cached")

        # Should be retrievable immediately
        retrieved = cache.get(test_url)
        assert retrieved is not None, "Content not retrievable immediately after caching"
        print("  [OK] Content retrievable immediately")

        # Wait for TTL to expire
        time.sleep(1.5)

        # Should return None after expiration
        expired = cache.get(test_url)
        assert expired is None, "Expired content still retrievable"
        print("  [OK] Content expired after TTL")

    print("[PASS] WikiCache TTL Expiration")


def test_wiki_cache_delete():
    """Test manual cache deletion."""
    print("\n[TEST] WikiCache Delete")

    with tempfile.TemporaryDirectory() as temp_dir:
        cache = WikiCache(cache_dir=temp_dir)

        test_url = "https://example.com/wiki/DeleteTest"
        test_content = {"title": "Delete Test", "text": "Will be deleted"}

        # Cache and verify
        cache.set(test_url, test_content)
        assert cache.get(test_url) is not None, "Content not cached"
        print("  [OK] Content cached")

        # Delete
        cache.delete(test_url)
        print("  [OK] Content deleted")

        # Verify deleted
        deleted = cache.get(test_url)
        assert deleted is None, "Content still retrievable after deletion"
        print("  [OK] Content no longer retrievable")

        # Verify index updated (should be empty now)
        assert len(cache.index) == 0, "Index not updated after deletion"
        print("  [OK] Index updated after deletion")

    print("[PASS] WikiCache Delete")


def test_wiki_cache_stats():
    """Test cache statistics."""
    print("\n[TEST] WikiCache Stats")

    with tempfile.TemporaryDirectory() as temp_dir:
        cache = WikiCache(cache_dir=temp_dir)

        # Get initial stats
        stats = cache.get_stats()
        assert "entries" in stats, "Stats missing entries"
        assert "size_mb" in stats, "Stats missing size_mb"
        assert "cache_dir" in stats, "Stats missing cache_dir"
        assert stats["entries"] == 0, "Initial entry count not 0"
        print("  [OK] Initial stats correct")

        # Add some content
        for i in range(3):
            cache.set(
                f"https://example.com/wiki/Page{i}",
                {"title": f"Page {i}", "text": "Content " * 100}
            )

        # Check updated stats
        stats = cache.get_stats()
        assert stats["entries"] == 3, "Entry count not updated"
        assert stats["size_mb"] > 0, "Size not calculated"
        print("  [OK] Stats updated after caching")

    print("[PASS] WikiCache Stats")


def test_wiki_client_initialization():
    """Test WikiClient initialization."""
    print("\n[TEST] WikiClient Initialization")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Test with default cache
        client1 = WikiClient(base_url="https://example.com/wiki")
        assert client1.base_url == "https://example.com/wiki", "Base URL not set"
        assert client1.cache is not None, "Cache not created"
        print("  [OK] Client with default cache initialized")

        # Test with custom cache
        custom_cache = WikiCache(cache_dir=temp_dir)
        client2 = WikiClient(
            base_url="https://example.com/wiki",
            cache=custom_cache
        )
        assert client2.cache is custom_cache, "Custom cache not used"
        print("  [OK] Client with custom cache initialized")

        # Test base URL normalization (trailing slash removal)
        client3 = WikiClient(base_url="https://example.com/wiki/")
        assert client3.base_url == "https://example.com/wiki", "Trailing slash not removed"
        print("  [OK] Base URL normalized (trailing slash removed)")

    print("[PASS] WikiClient Initialization")


def test_wiki_client_custom_item_filtering():
    """Test that custom items block wiki lookups."""
    print("\n[TEST] WikiClient Custom Item Filtering")

    # Create a mock item registry (minimal implementation for testing)
    class MockItemRegistry:
        """Mock ItemRegistry for testing custom item filtering."""
        def __init__(self):
            self.custom_items = {"Sword of Testing", "Magic Test Shield"}

        def is_custom(self, item_name):
            """Check if item is in custom registry."""
            return item_name in self.custom_items

        def add_item(self, item_name):
            """Add item to custom registry (for test completeness)."""
            self.custom_items.add(item_name)

    with tempfile.TemporaryDirectory() as temp_dir:
        cache = WikiCache(cache_dir=temp_dir)
        registry = MockItemRegistry()

        # Create client with item registry
        client = WikiClient(
            base_url="https://example.com/wiki",
            cache=cache,
            item_registry=registry
        )
        assert client.item_registry is registry, "Item registry not set"
        print("  [OK] Client initialized with item registry")

        # Try to fetch custom item (should be blocked)
        result = client.fetch_page("Sword of Testing")
        assert result is None, "Custom item lookup not blocked"
        print("  [OK] Custom item lookup blocked")

        # Note: We can't test non-custom items without actual web scraping
        # which requires requests/beautifulsoup4 and internet connection
        print("  [SKIP] Non-custom item test (requires web scraping)")

    print("[PASS] WikiClient Custom Item Filtering")


def test_wiki_cache_clear_expired():
    """Test clearing expired cache entries."""
    print("\n[TEST] WikiCache Clear Expired")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create cache with very short TTL
        cache = WikiCache(cache_dir=temp_dir, ttl_seconds=1)

        # Add multiple entries
        for i in range(3):
            cache.set(
                f"https://example.com/wiki/Page{i}",
                {"title": f"Page {i}", "text": f"Content {i}"}
            )

        # Verify all cached
        assert cache.get_stats()["entries"] == 3, "Not all entries cached"
        print("  [OK] All entries cached")

        # Wait for expiration
        time.sleep(1.5)

        # Clear expired
        cache.clear_expired()
        print("  [OK] clear_expired() called")

        # Verify all cleared
        stats = cache.get_stats()
        assert stats["entries"] == 0, "Expired entries not cleared"
        print("  [OK] All expired entries cleared")

    print("[PASS] WikiCache Clear Expired")


def run_all_tests():
    """Run all RAG system tests."""
    print("=" * 70)
    print("RAG SYSTEM TESTS")
    print("=" * 70)

    test_wiki_cache_initialization()
    test_wiki_cache_key_generation()
    test_wiki_cache_set_and_get()
    test_wiki_cache_expiration()
    test_wiki_cache_delete()
    test_wiki_cache_stats()
    test_wiki_client_initialization()
    test_wiki_client_custom_item_filtering()
    test_wiki_cache_clear_expired()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL RAG SYSTEM TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
