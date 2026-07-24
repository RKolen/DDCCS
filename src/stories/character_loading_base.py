"""
Shared base class for lazy character loading functionality.

Extracted to avoid code duplication between CharacterLoader and CharacterManager.
"""

import os
from typing import TYPE_CHECKING, Dict, List, Any, Optional
from src.stories.character_loader import load_single_character_consultant
from src.characters.consultants.consultant_core import CharacterConsultant
from src.utils.string_utils import sanitize_filename

if TYPE_CHECKING:
    from src.characters.consultants.character_profile import CharacterProfile


class CharacterLoadingMixin:
    """Mixin providing lazy character loading methods.

    Classes using this mixin must have:
    - self.characters_path: str
    - self.ai_client: Optional
    - self.consultants: Dict[str, CharacterConsultant]
    - self._characters_loaded: bool
    """

    # Type annotations for mixin attributes
    characters_path: str
    ai_client: Optional[Any]
    consultants: Dict[str, Any]
    _characters_loaded: bool

    def load_characters(self):
        """Must be implemented by subclass."""
        raise NotImplementedError("Subclass must implement load_characters()")

    def ensure_characters_loaded(self):
        """Ensure all characters are loaded (lazy loading compatible)."""
        if not self._characters_loaded:
            self.load_characters()

    def is_characters_loaded(self) -> bool:
        """Check if characters have been loaded."""
        return self._characters_loaded

    def save_character_profile(self, profile: "CharacterProfile") -> None:
        """Save a character profile to disk and refresh its consultant.

        Shared by ``CharacterLoader`` and ``CharacterManager`` so the save path
        exists once rather than being duplicated in each.

        Args:
            profile: Character profile to save.
        """
        filepath = os.path.join(
            self.characters_path, f"{sanitize_filename(profile.name)}.json"
        )
        profile.save_to_file(filepath)
        self.consultants[profile.name] = CharacterConsultant(
            profile, ai_client=self.ai_client
        )
        print(f"[SUCCESS] Saved character profile: {profile.name}")

    def _load_party_characters_into_dict(
        self, party_members: List[str]
    ) -> Dict[str, Any]:
        """Helper to load party characters into dict (avoids code duplication).

        Args:
            party_members: List of character names to load

        Returns:
            Dict mapping character name to consultant for loaded characters
        """
        loaded: Dict[str, Any] = {}
        for character_name in party_members:
            if character_name in self.consultants:
                loaded[character_name] = self.consultants[character_name]
            else:
                consultant = load_single_character_consultant(
                    self.characters_path,
                    character_name,
                    ai_client=self.ai_client,
                    verbose=False,
                )
                if consultant is not None:
                    self.consultants[character_name] = consultant
                    loaded[character_name] = consultant
        return loaded

    def load_party_characters(self, party_members: List[str]) -> Dict[str, Any]:
        """Load only specific party member characters.

        Loads only requested characters if not already loaded. Skips characters
        that are already in the consultants dict to avoid redundant loading.

        Args:
            party_members: List of character names to load

        Returns:
            Dict mapping character name to consultant for loaded characters
        """
        loaded = self._load_party_characters_into_dict(party_members)
        self._characters_loaded = True
        return loaded
