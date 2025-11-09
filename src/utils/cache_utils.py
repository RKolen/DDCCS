"""Cache utilities for managing in-memory character profile caching.

This module provides reusable functions for clearing and reloading cached
character profiles from disk. Useful when users choose "Exit without Saving"
to discard in-memory modifications.
"""

import os
from typing import Dict, Optional, Any
from src.characters.consultants.character_profile import CharacterProfile
from src.stories.character_load_helper import load_character_consultant


def clear_character_from_cache(
    consultants_cache: Dict[str, Any], character_name: str
) -> bool:
    """Clear a character from the in-memory consultants cache.

    Removes the character from the cache dict so subsequent loads will get
    fresh data from disk. Useful after "Exit without Saving" to discard
    in-memory modifications.

    Args:
        consultants_cache: Dict of character_name -> consultant objects
        character_name: Name of character to clear from cache

    Returns:
        True if character was in cache and removed, False otherwise
    """
    if character_name in consultants_cache:
        del consultants_cache[character_name]
        return True
    return False


def reload_character_from_disk(
    consultants_cache: Dict[str, Any],
    characters_path: str,
    character_name: str,
    ai_client=None,
) -> bool:
    """Reload a character from disk and update cache.

    Clears the character from cache and attempts to reload it from disk.
    This ensures fresh data without in-memory modifications.

    Args:
        consultants_cache: Dict of character_name -> consultant objects (modified in-place)
        characters_path: Path to characters directory
        character_name: Name of character to reload
        ai_client: Optional AI client for character features

    Returns:
        True if reload succeeded, False if character file not found or load failed
    """
    # Clear from cache first
    clear_character_from_cache(consultants_cache, character_name)

    # Find character file matching the name
    if not os.path.isdir(characters_path):
        return False

    # Search for character file with matching name
    for filename in os.listdir(characters_path):
        if not filename.endswith(".json"):
            continue

        filepath = os.path.join(characters_path, filename)
        try:
            # Try to load and check if name matches
            consultant = load_character_consultant(
                filepath, ai_client=ai_client, verbose=False
            )
            if consultant and consultant.profile.name == character_name:
                # Found it - cache the loaded consultant
                consultants_cache[character_name] = consultant
                return True
        except (OSError, ValueError, KeyError):
            # Continue searching if this file doesn't work
            continue

    return False


def get_character_profile_from_cache(
    consultants_cache: Dict[str, Any], character_name: str
) -> Optional[CharacterProfile]:
    """Get a character profile from cache.

    Simple utility to get a profile from the consultants cache dict.

    Args:
        consultants_cache: Dict of character_name -> consultant objects
        character_name: Name of character to retrieve

    Returns:
        CharacterProfile if found, None otherwise
    """
    consultant = consultants_cache.get(character_name)
    if consultant:
        return consultant.profile
    return None
