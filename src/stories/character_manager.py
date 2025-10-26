"""
Character Management for Story System

Handles character loading, profiles, consultants, and spell highlighting.
"""

import os
from typing import Optional
from src.characters.consultants.character_profile import CharacterProfile
from src.utils.spell_highlighter import highlight_spells_in_text
from src.utils.file_io import directory_exists
from src.utils.story_file_helpers import list_character_json_candidates
from src.stories.character_load_helper import load_character_consultant


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
        for filepath in list_character_json_candidates(self.characters_path):
            consultant = load_character_consultant(filepath, ai_client=self.ai_client,
                                                   verbose=False)
            if consultant is None:
                # load_character_consultant already prints details when verbose=True
                continue
            profile = consultant.profile
            self.consultants[profile.name] = consultant

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
