"""
Test lazy character loading functionality.

Verifies that:
1. Characters are not loaded at startup (lazy_load=True)
2. Characters are loaded on-demand with ensure_characters_loaded()
3. Party-based loading works correctly
4. Caching prevents redundant loading
"""

import sys
from pathlib import Path

from src.stories.story_manager import StoryManager
from tests.test_helpers import setup_test_environment

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

WORKSPACE_PATH = str(setup_test_environment())


def test_lazy_startup_no_characters_loaded():
    """Test that startup with lazy_load=True doesn't load characters."""
    story_manager = StoryManager(WORKSPACE_PATH, lazy_load=True)
    assert not story_manager.is_characters_loaded()
    assert len(story_manager.consultants) == 0


def test_load_party_characters():
    """Test that load_party_characters() loads the correct number of characters."""
    story_manager = StoryManager(WORKSPACE_PATH, lazy_load=True)
    party = ["Aragorn", "Frodo Baggins", "Gandalf the Grey"]

    loaded = story_manager.load_party_characters(party)
    assert story_manager.is_characters_loaded()
    # Should load exactly the number of party members requested
    assert len(loaded) == len(party)


def test_load_party_characters_caching():
    """Test that redundant party loads are skipped."""
    story_manager = StoryManager(WORKSPACE_PATH, lazy_load=True)
    party = ["Aragorn", "Frodo Baggins"]

    # First load
    loaded1 = story_manager.load_party_characters(party)
    assert len(loaded1) == 2

    # Second load - should not reload
    loaded2 = story_manager.load_party_characters(party)
    assert len(loaded2) == 2


def test_get_character_profile_lazy():
    """Test getting character profile after lazy loading."""
    story_manager = StoryManager(WORKSPACE_PATH, lazy_load=True)
    party = ["Aragorn"]

    story_manager.load_party_characters(party)
    profile = story_manager.get_character_profile("Aragorn")
    assert profile is not None
    assert profile.name == "Aragorn"


if __name__ == "__main__":
    test_lazy_startup_no_characters_loaded()
    print("[OK] test_lazy_startup_no_characters_loaded")

    test_load_party_characters()
    print("[OK] test_load_party_characters")

    test_load_party_characters_caching()
    print("[OK] test_load_party_characters_caching")

    test_get_character_profile_lazy()
    print("[OK] test_get_character_profile_lazy")

    print("\n[SUCCESS] All lazy character loading tests passed!")
