"""
Character Loader Component for Story Management.

Handles loading and validation of character profiles from JSON files,
creating character consultants for story analysis.
"""

import os
from typing import Dict, List, Optional
from src.characters.consultants.character_profile import CharacterProfile
from src.characters.consultants.consultant_core import CharacterConsultant
from src.utils.file_io import directory_exists
from src.utils.path_utils import get_characters_dir, get_character_file_path
from src.utils.story_file_helpers import list_character_json_candidates
from src.stories.character_load_helper import load_character_consultant

USE_CHARACTER_VALIDATION = True

class CharacterLoader:
    """Loads character profiles and creates consultants for story management."""

    def __init__(self, workspace_path: str, ai_client=None):
        """
        Initialize character loader.

        Args:
            workspace_path: Root workspace directory path
            ai_client: Optional AI client for character consultants
        """
        self.workspace_path = workspace_path
        self.characters_path = get_characters_dir(workspace_path)
        self.ai_client = ai_client
        self.consultants: Dict[str, CharacterConsultant] = {}

        # Ensure directories exist
        os.makedirs(self.characters_path, exist_ok=True)

    def load_characters(self):
        """Load all character profiles and create consultants."""
        if not directory_exists(self.characters_path):
            return
        for filepath in list_character_json_candidates(self.characters_path):
            consultant = load_character_consultant(filepath, ai_client=self.ai_client,
                                                   verbose=USE_CHARACTER_VALIDATION)
            if consultant is None:
                continue
            profile = consultant.profile
            self.consultants[profile.name] = consultant

    def save_character_profile(self, profile: CharacterProfile):
        """
        Save a character profile and update consultant.

        Args:
            profile: Character profile to save
        """
        filepath = get_character_file_path(profile.name, self.workspace_path)
        profile.save_to_file(filepath)

        # Update consultant with AI client
        self.consultants[profile.name] = CharacterConsultant(
            profile, ai_client=self.ai_client
        )
        print(f"[SUCCESS] Saved character profile: {profile.name}")

    def get_character_list(self) -> List[str]:
        """
        Get list of all character names.

        Returns:
            List of character names
        """
        return list(self.consultants.keys())

    def get_character_profile(self, character_name: str) -> Optional[CharacterProfile]:
        """
        Get a character's profile.

        Args:
            character_name: Name of the character

        Returns:
            CharacterProfile if found, None otherwise
        """
        consultant = self.consultants.get(character_name)
        return consultant.profile if consultant else None

    def get_consultant(self, character_name: str) -> Optional[CharacterConsultant]:
        """
        Get a character's consultant.

        Args:
            character_name: Name of the character

        Returns:
            CharacterConsultant if found, None otherwise
        """
        return self.consultants.get(character_name)
