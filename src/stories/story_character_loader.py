"""
Character Loader Component for Story Management.

Handles loading and validation of character profiles from JSON files,
creating character consultants for story analysis.
"""

import os
from typing import Dict, List, Optional
from src.characters.consultants.character_profile import CharacterProfile
from src.characters.consultants.consultant_core import CharacterConsultant
from src.validation.character_validator import validate_character_file
from src.utils.file_io import directory_exists, get_json_files_in_directory
from src.utils.path_utils import get_characters_dir, get_character_file_path

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

        use_validation = USE_CHARACTER_VALIDATION
        if not use_validation:
            print("Warning: character_validator module not found, skipping validation")

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
            if use_validation:
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
                if use_validation:
                    print(f"[OK] Loaded and validated: {filename}")
            except (OSError, IOError) as e:
                print(f"Warning: Could not load character {filename}: {e}")

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
