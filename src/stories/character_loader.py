"""
Centralized character loading helper.

Provides functions to load character consultants from a characters directory.
This centralization removes duplicated loading logic across multiple modules.
"""

from pathlib import Path
from typing import Dict, Optional
import os

from src.characters.consultants.consultant_core import CharacterConsultant
from src.stories.character_load_helper import load_character_consultant
from src.utils.story_file_helpers import list_character_json_candidates


def load_all_character_consultants(
    characters_dir: str, ai_client: Optional[object] = None, verbose: bool = False
) -> Dict[str, CharacterConsultant]:
    """Load all character consultants from a directory.

    Args:
        characters_dir: Path to the characters directory.
        ai_client: Optional AI client passed to each consultant loader.
        verbose: Whether to enable verbose output from the underlying loader.

    Returns:
        Mapping of character name -> CharacterConsultant for each successfully
        loaded character.
    """
    consultants: Dict[str, CharacterConsultant] = {}

    # Ensure the directory exists (idempotent)
    try:
        os.makedirs(characters_dir, exist_ok=True)
    except OSError:
        # If directory cannot be created, proceed; callers often check existence
        # Only catch OSError which is expected for filesystem issues.
        pass

    p = Path(characters_dir)
    if not p.exists():
        return consultants

    for fp in list_character_json_candidates(str(p)):
        consultant = load_character_consultant(fp, ai_client=ai_client, verbose=verbose)
        if consultant is None:
            continue
        consultants[consultant.profile.name] = consultant

    return consultants


def load_single_character_consultant(
    characters_dir: str,
    character_name: str,
    ai_client: Optional[object] = None,
    verbose: bool = False,
) -> Optional[CharacterConsultant]:
    """Load a single character consultant by name.

    Searches for a JSON file matching the character name (case-insensitive)
    and loads it if found. Useful for lazy loading specific party members.

    Args:
        characters_dir: Path to the characters directory.
        character_name: Name of character to load (e.g., "Aragorn", "Frodo Baggins").
        ai_client: Optional AI client passed to consultant loader.
        verbose: Whether to enable verbose output from the underlying loader.

    Returns:
        CharacterConsultant if found and loaded, None if not found or load failed.
    """
    # Ensure directory exists
    try:
        os.makedirs(characters_dir, exist_ok=True)
    except OSError:
        return None

    p = Path(characters_dir)
    if not p.exists():
        return None

    # Find JSON file matching character name (case-insensitive)
    for fp in list_character_json_candidates(str(p)):
        consultant = load_character_consultant(fp, ai_client=ai_client, verbose=verbose)
        if consultant is not None:
            if consultant.profile.name == character_name:
                return consultant

    return None
