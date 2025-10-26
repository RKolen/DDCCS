"""
Character Management for Story System

Handles character loading, profiles, consultants, and spell highlighting.
"""

from typing import Optional
from src.characters.consultants.character_profile import CharacterProfile
from src.utils.spell_highlighter import highlight_spells_in_text
from src.stories.character_loader import load_all_character_consultants


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

    # Directory existence is ensured by the centralized loader when needed.

    def load_characters(self):
        """Load all character profiles and create consultants."""
        # Delegate loading to centralized helper which will ensure the
        # directory exists and return a mapping of name -> consultant.
        self.consultants = load_all_character_consultants(
            self.characters_path, ai_client=self.ai_client, verbose=False
        )

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
