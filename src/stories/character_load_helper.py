"""Helper to load a character profile, validate it, and construct a consultant.

Placing this helper in `src.stories` avoids cross-package cyclic imports
between `src.characters` and `src.utils` while removing duplicated code
in the two story modules.
"""
from typing import Optional
import json
from src.characters.consultants.character_profile import CharacterProfile
from src.characters.consultants.consultant_core import CharacterConsultant

from src.utils.optional_imports import import_validator

# Optional validator import (centralized)
VALIDATOR_AVAILABLE, _validator_module = import_validator()
validate_character_file = getattr(_validator_module, "validate_character_file",
                                  None) if _validator_module else None


def load_character_consultant(filepath: str, ai_client=None,
                              verbose: bool = False) -> Optional[CharacterConsultant]:
    """Validate and load a character file and return a CharacterConsultant.

    Returns None if validation fails or loading fails.
    """
    if VALIDATOR_AVAILABLE and validate_character_file:
        is_valid, errors = validate_character_file(filepath)
        if not is_valid:
            if verbose:
                print(f"[FAILED] Validation failed for {filepath}:")
                for error in errors:
                    print(f"  - {error}")
            return None

    try:
        profile = CharacterProfile.load_from_file(filepath)
        consultant = CharacterConsultant(profile, ai_client=ai_client)
        if verbose and VALIDATOR_AVAILABLE:
            print(f"[OK] Loaded and validated: {filepath}")
        return consultant
    except (FileNotFoundError, json.JSONDecodeError, OSError, IOError, KeyError, ValueError) as exc:
        if verbose:
            print(f"Warning: Could not load character {filepath}: {exc}")
        return None
