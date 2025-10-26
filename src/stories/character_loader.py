"""
Centralized character loading helper.

Provides a single function to load all character consultants from a
characters directory. This centralization removes duplicated loading
logic across multiple story/DM modules.
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
