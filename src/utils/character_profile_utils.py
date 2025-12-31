"""
Character Profile Utility Functions.

This module provides centralized functions for:
- Loading character profiles from JSON files
- Finding character files by name
- Loading party members with their profiles
- Normalizing character names for file lookups

These functions consolidate duplicate character loading logic found across
story_updater.py, story_consistency_analyzer.py, cli_story_analysis.py,
party_config_manager.py, and other modules.
"""

import os
from typing import Any, Dict, List, Optional

from src.utils.file_io import load_json_file, file_exists
from src.utils.path_utils import get_characters_dir
from src.utils.string_utils import sanitize_filename


def find_character_file(
    character_name: str, workspace_path: Optional[str] = None
) -> Optional[str]:
    """Find character JSON file for a given character name.

    Searches for a character file using multiple matching strategies:
    1. Exact filename match (name normalized to lowercase with underscores)
    2. First name only match

    Args:
        character_name: Character name to search for
        workspace_path: Optional workspace root path

    Returns:
        Full path to character file, or None if not found
    """
    chars_dir = get_characters_dir(workspace_path)
    if not os.path.isdir(chars_dir):
        return None

    # Strategy 1: Try exact filename match (normalized)
    normalized_name = sanitize_filename(character_name)
    candidate = os.path.join(chars_dir, f"{normalized_name}.json")
    if file_exists(candidate):
        return candidate

    # Strategy 2: Try first name only
    first_name = character_name.split()[0].lower()
    candidate = os.path.join(chars_dir, f"{first_name}.json")
    if file_exists(candidate):
        return candidate

    return None


def load_character_profile(
    character_name: str, workspace_path: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """Load a character profile by name.

    Args:
        character_name: Name of the character to load
        workspace_path: Optional workspace root path

    Returns:
        Character profile dictionary, or None if not found or on error
    """
    char_file = find_character_file(character_name, workspace_path)
    if not char_file:
        return None

    try:
        return load_json_file(char_file)
    except (OSError, ValueError):
        return None


def load_character_profiles(
    character_names: List[str], workspace_path: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """Load profiles for multiple characters.

    Args:
        character_names: List of character names to load
        workspace_path: Optional workspace root path

    Returns:
        Dictionary mapping character names to their profiles
    """
    profiles = {}
    for name in character_names:
        profile = load_character_profile(name, workspace_path)
        if profile:
            profiles[name] = profile
    return profiles


def load_character_traits(
    character_names: List[str], workspace_path: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """Load character trait dictionaries for story analysis.

    Loads specific personality and background fields useful for
    character development analysis.

    Args:
        character_names: List of character names to load
        workspace_path: Optional workspace root path

    Returns:
        Dictionary mapping character names to trait dictionaries containing:
        - name, dnd_class, personality_summary, background_story
        - motivations, fears_weaknesses, goals, relationships, secrets
        - class_abilities, specialized_abilities, known_spells, feats
    """
    traits = {}
    for character_name in character_names:
        profile = load_character_profile(character_name, workspace_path)
        if profile:
            traits[character_name] = {
                "name": character_name,
                "dnd_class": profile.get("dnd_class", ""),
                "personality_summary": profile.get("personality_summary", ""),
                "background_story": profile.get("background_story", ""),
                "motivations": profile.get("motivations", []),
                "fears_weaknesses": profile.get("fears_weaknesses", []),
                "goals": profile.get("goals", []),
                "relationships": profile.get("relationships", {}),
                "secrets": profile.get("secrets", []),
                "class_abilities": profile.get("class_abilities", []),
                "specialized_abilities": profile.get("specialized_abilities", []),
                "known_spells": profile.get("known_spells", []),
                "feats": profile.get("feats", []),
            }
    return traits


def is_example_or_template_file(filename: str) -> bool:
    """Check if a filename is an example or template file.

    Args:
        filename: Filename to check

    Returns:
        True if filename contains 'example' or 'template' (case-insensitive)
    """
    name_lower = filename.lower()
    return "example" in name_lower or "template" in name_lower


def list_character_files(
    workspace_path: Optional[str] = None, include_examples: bool = False
) -> List[str]:
    """List all character JSON files in the characters directory.

    Args:
        workspace_path: Optional workspace root path
        include_examples: Whether to include example/template files (default: False)

    Returns:
        List of character filenames (without path)
    """
    chars_dir = get_characters_dir(workspace_path)
    if not os.path.isdir(chars_dir):
        return []

    files = []
    for filename in sorted(os.listdir(chars_dir)):
        if not filename.lower().endswith(".json"):
            continue
        if not include_examples and is_example_or_template_file(filename):
            continue
        files.append(filename)
    return files


def list_character_names(
    workspace_path: Optional[str] = None, include_examples: bool = False
) -> List[str]:
    """List all character names from character JSON files.

    Reads the 'name' field from each character file. Falls back to
    filename-derived name if 'name' field is not present.

    Args:
        workspace_path: Optional workspace root path
        include_examples: Whether to include example/template files (default: False)

    Returns:
        List of character names
    """
    chars_dir = get_characters_dir(workspace_path)
    files = list_character_files(workspace_path, include_examples)
    names = []

    for filename in files:
        filepath = os.path.join(chars_dir, filename)
        try:
            data = load_json_file(filepath)
            if data and "name" in data:
                names.append(data["name"])
            else:
                # Fallback: derive name from filename
                stem = filename[:-5]  # Remove .json
                names.append(stem.replace("_", " ").title())
        except (OSError, ValueError):
            continue

    return names
