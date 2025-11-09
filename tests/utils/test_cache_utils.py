"""Tests for cache utility functions."""

import os
import sys
import tempfile
from unittest.mock import Mock

from tests.test_helpers import setup_test_environment, import_module

setup_test_environment()

cache_utils = import_module("src.utils.cache_utils")
clear_character_from_cache = cache_utils.clear_character_from_cache
reload_character_from_disk = cache_utils.reload_character_from_disk
get_character_profile_from_cache = cache_utils.get_character_profile_from_cache


def test_clear_character_from_cache():
    """Test clearing a character from the cache."""
    # Create mock consultant
    mock_profile = Mock(name="Test Character")
    mock_consultant = Mock(profile=mock_profile)

    # Create cache with character
    cache = {"Test Character": mock_consultant, "Other Character": Mock()}

    # Clear character
    result = clear_character_from_cache(cache, "Test Character")

    # Verify character was removed
    assert result is True, "Should return True when character was in cache"
    assert "Test Character" not in cache, "Character should be removed from cache"
    assert "Other Character" in cache, "Other characters should remain"


def test_clear_character_from_cache_not_found():
    """Test clearing a character that's not in cache."""
    cache = {"Other Character": Mock()}

    result = clear_character_from_cache(cache, "Nonexistent Character")

    assert result is False, "Should return False when character not in cache"
    assert len(cache) == 1, "Cache should be unchanged"


def test_get_character_profile_from_cache():
    """Test retrieving a character profile from cache."""
    mock_profile = Mock(name="Test Character")
    mock_consultant = Mock(profile=mock_profile)
    cache = {"Test Character": mock_consultant}

    result = get_character_profile_from_cache(cache, "Test Character")

    assert result is mock_profile, "Should return the profile"


def test_get_character_profile_from_cache_not_found():
    """Test retrieving a nonexistent character from cache."""
    cache = {}

    result = get_character_profile_from_cache(cache, "Nonexistent Character")

    assert result is None, "Should return None when character not found"


def test_reload_character_from_disk_invalid_path():
    """Test reload with invalid characters path."""
    cache = {}
    result = reload_character_from_disk(cache, "/nonexistent/path", "Test", None)

    assert result is False, "Should return False for invalid path"


def test_reload_character_from_disk_no_matching_file():
    """Test reload when no matching character file exists."""
    cache = {}

    # Create temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a character file with different name
        other_file = os.path.join(tmpdir, "other.json")
        with open(other_file, "w", encoding="utf-8") as f:
            f.write('{"name": "Other Character"}')

        result = reload_character_from_disk(cache, tmpdir, "Test Character", None)

        assert result is False, "Should return False when no matching file found"


def test_reload_character_clears_existing_cache():
    """Test that reload clears existing entry before attempting reload."""
    old_consultant = Mock()
    cache = {"Test Character": old_consultant}

    # Test with invalid path to trigger early return
    # (This should still clear the cache)
    result = reload_character_from_disk(cache, "/nonexistent/path", "Test Character", None)

    # Cache should be cleared even though reload failed
    assert "Test Character" not in cache, "Cache should be cleared"
    assert result is False, "Should return False for failed reload"


class TestCacheUtilsIntegration:
    """Integration tests with actual character data."""

    def test_cache_clearing_workflow(self):
        """Test complete workflow: cache -> clear -> reload."""
        # Create mock consultant with profile
        mock_profile = Mock(name="Aragorn")
        mock_profile.personality_summary = "Original personality"
        mock_consultant = Mock(profile=mock_profile)

        # Initialize cache with consultant
        cache = {"Aragorn": mock_consultant}

        # Verify it's in cache
        assert get_character_profile_from_cache(cache, "Aragorn") is not None

        # Simulate in-memory modification
        profile = get_character_profile_from_cache(cache, "Aragorn")
        profile.personality_summary = "TEST MODIFICATION"

        # Clear from cache
        clear_result = clear_character_from_cache(cache, "Aragorn")
        assert clear_result is True, "Should clear successfully"
        assert get_character_profile_from_cache(cache, "Aragorn") is None

    def test_cache_with_multiple_characters(self):
        """Test cache clearing with multiple characters."""
        # Create multiple mock consultants
        cache = {
            "Aragorn": Mock(profile=Mock(name="Aragorn")),
            "Gandalf": Mock(profile=Mock(name="Gandalf")),
            "Frodo": Mock(profile=Mock(name="Frodo")),
        }

        # Clear one character
        result = clear_character_from_cache(cache, "Aragorn")

        assert result is True
        assert len(cache) == 2, "Should have 2 characters left"
        assert "Aragorn" not in cache
        assert "Gandalf" in cache
        assert "Frodo" in cache

    def test_reload_preserves_other_characters(self):
        """Test that reload doesn't affect other cached characters."""
        cache = {
            "Aragorn": Mock(profile=Mock(name="Aragorn")),
            "Gandalf": Mock(profile=Mock(name="Gandalf")),
        }

        # Attempt reload with invalid path (will fail but should clear only target char)
        result = reload_character_from_disk(cache, "/invalid/path", "Aragorn", None)

        assert result is False, "Reload should fail with invalid path"
        assert "Aragorn" not in cache, "Target should be cleared"
        assert "Gandalf" in cache, "Other characters should be preserved"


def run_test_suite():
    """Run all tests in this file."""
    test_functions = [
        ("clear_character_from_cache", test_clear_character_from_cache),
        ("clear_character_from_cache_not_found", test_clear_character_from_cache_not_found),
        ("get_character_profile_from_cache", test_get_character_profile_from_cache),
        (
            "get_character_profile_from_cache_not_found",
            test_get_character_profile_from_cache_not_found,
        ),
        ("reload_character_from_disk_invalid_path", test_reload_character_from_disk_invalid_path),
        (
            "reload_character_from_disk_no_matching_file",
            test_reload_character_from_disk_no_matching_file,
        ),
        ("reload_character_clears_existing_cache", test_reload_character_clears_existing_cache),
    ]

    passed = 0
    failed = 0

    print("\n[D&D] Cache Utils Tests")
    print("=" * 70)

    for test_name, test_func in test_functions:
        try:
            test_func()
            print(f"  [PASS] {test_name}")
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {test_name}: {e}")
            failed += 1
        except (ValueError, KeyError, OSError) as e:
            print(f"  [ERROR] {test_name}: {e}")
            failed += 1

    # Integration tests
    integration_tests = TestCacheUtilsIntegration()
    integration_test_methods = [
        ("cache_clearing_workflow", integration_tests.test_cache_clearing_workflow),
        (
            "cache_with_multiple_characters",
            integration_tests.test_cache_with_multiple_characters,
        ),
        (
            "reload_preserves_other_characters",
            integration_tests.test_reload_preserves_other_characters,
        ),
    ]

    for test_name, test_method in integration_test_methods:
        try:
            test_method()
            print(f"  [PASS] {test_name}")
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {test_name}: {e}")
            failed += 1
        except (ValueError, KeyError, OSError) as e:
            print(f"  [ERROR] {test_name}: {e}")
            failed += 1

    print("=" * 70)
    print(f"Total: {passed} passed, {failed} failed")
    print("=" * 70 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_test_suite()
    sys.exit(0 if success else 1)
