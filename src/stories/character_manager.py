"""
Character Management for Story System

Handles character loading, profiles, consultants, and spell highlighting.
"""

import os
import json
from typing import Optional
from src.characters.consultants.character_profile import CharacterProfile
from src.characters.consultants.consultant_core import CharacterConsultant
from src.utils.spell_highlighter import highlight_spells_in_text
from src.utils.file_io import directory_exists, get_json_files_in_directory

# Optional validator import (fail-safe if not available)
try:
    from src.validation.character_validator import validate_character_file
    VALIDATOR_AVAILABLE = True
except ImportError:
    VALIDATOR_AVAILABLE = False
    validate_character_file = None


class CharacterManager:
    """Manages character loading, profiles, and consultants."""

    def __init__(self, characters_path: str, ai_client=None):
        """Initialize character manager.

        Args:
            characters_path: Path to characters directory
            ai_client: Optional AI client for enhanced features
        """
        self.characters_path = characters_path
        self.ai_client = ai_client
        self.consultants = {}
        self.known_spells = set()

        # Ensure directory exists
        os.makedirs(self.characters_path, exist_ok=True)

    def load_characters(self):
        """Load all character profiles and create consultants."""
        if not directory_exists(self.characters_path):
            return

        for filepath in get_json_files_in_directory(self.characters_path):
            filename = os.path.basename(filepath)

            # Skip template and example files
            if (
                filename.startswith("class.example")
                or filename.endswith(".example.json")
                or filename.startswith("template")
            ):
                continue

            # Validate character JSON before loading
            if VALIDATOR_AVAILABLE:
                is_valid, errors = validate_character_file(filepath)
                if not is_valid:
                    print(f"[FAILED] Validation failed for {filename}:")
                    for error in errors:
                        print(f"  - {error}")
                    continue

            try:
                profile = CharacterProfile.load_from_file(filepath)
                self.consultants[profile.name] = CharacterConsultant(
                    profile, ai_client=self.ai_client
                )
                if VALIDATOR_AVAILABLE:
                    print(f"[OK] Loaded and validated: {filename}")
            except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"Warning: Could not load character {filename}: {e}")

        # Extract known spells from all loaded characters
        self._update_known_spells()

    def _update_known_spells(self):
        """Extract and cache known spells from all loaded characters."""
        self.known_spells = set()
        for consultant in self.consultants.values():
            # Add known spells from profile
            if consultant.profile.known_spells:
                for spell in consultant.profile.known_spells:
                    self.known_spells.add(spell)

    def apply_spell_highlighting(self, text: str) -> str:
        """Apply spell name highlighting to narrative text.

        Args:
            text: Narrative text to process

        Returns:
            Text with spell names highlighted using **bold markdown**
        """
        if not self.known_spells:
            return text

        return highlight_spells_in_text(text, self.known_spells)

    def get_character_list(self):
        """Get list of all character names."""
        return list(self.consultants.keys())

    def get_character_profile(self, character_name: str) -> Optional[CharacterProfile]:
        """Get a specific character's profile."""
        consultant = self.consultants.get(character_name)
        if consultant:
            return consultant.profile
        return None
