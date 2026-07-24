"""
Story Management System for VSCode Integration.

Main orchestrator that delegates to specialized components for character loading,
story file operations, analysis, and updates.
"""

from typing import Dict, List, Any, Optional
from src.ai.ai_client import get_client_for_task
from src.characters.consultants.character_profile import CharacterProfile
from src.stories.story_character_loader import CharacterLoader
from src.stories.story_analysis import StoryAnalyzer
from src.stories.story_updater import StoryUpdater
from src.stories.party_manager import PartyManager
from src.stories.story_file_operations import StoryFileOperationsMixin
from src.ai.ai_client import AIClient
from src.utils.cache_utils import (
    reload_character_from_disk as reload_character_cache,
)


class StoryManager(StoryFileOperationsMixin):
    """Manages the story sequence system using specialized components."""

    def __init__(
        self,
        workspace_path: str,
        ai_client: Optional[AIClient] = None,
        lazy_load: bool = False,
    ):
        """
        Initialize story manager with specialized components.

        Args:
            workspace_path: Root workspace directory path
            ai_client: Optional AI client for character consultants. When omitted
                the task router resolves the "story_generation" profile.
            lazy_load: If True, defer character loading until explicitly requested
        """
        self.workspace_path = workspace_path
        self.ai_client = ai_client or get_client_for_task("story_generation")
        # Legacy stories live at the workspace root for the classic manager.
        self.stories_path = workspace_path

        # Initialize components using composition
        self.character_loader = CharacterLoader(
            workspace_path, ai_client, lazy_load=lazy_load
        )
        self.updater = StoryUpdater()

        # Create analyzer with loaded or empty consultants
        self.analyzer = StoryAnalyzer(self.character_loader.consultants)

        # Party manager with no campaign scope: party operations return an
        # empty list rather than raising, keeping the shared contract valid.
        self.party_manager = PartyManager(None, workspace_path)

    @property
    def consultants(self) -> Dict:
        """Access to character consultants."""
        return self.character_loader.consultants

    # Character Management Methods
    def load_characters(self):
        """Load all character profiles and create consultants."""
        self.character_loader.ensure_characters_loaded()
        # Update analyzer with loaded consultants
        self.analyzer = StoryAnalyzer(self.character_loader.consultants)

    def ensure_characters_loaded(self):
        """Ensure all characters are loaded (lazy loading compatible)."""
        self.character_loader.ensure_characters_loaded()
        # Update analyzer
        self.analyzer = StoryAnalyzer(self.character_loader.consultants)

    def is_characters_loaded(self) -> bool:
        """Check if characters have been loaded."""
        return self.character_loader.is_characters_loaded()

    def load_party_characters(self, party_members: list) -> Dict:
        """Load only specific party member characters.

        Args:
            party_members: List of character names to load

        Returns:
            Dict mapping character name to consultant for loaded characters
        """
        loaded = self.character_loader.load_party_characters(party_members)
        # Update analyzer with current consultants
        self.analyzer = StoryAnalyzer(self.character_loader.consultants)
        return loaded

    def save_character_profile(self, profile: CharacterProfile):
        """
        Save a character profile and update consultant.

        Args:
            profile: Character profile to save
        """
        self.character_loader.save_character_profile(profile)
        # Update analyzer with new consultants
        self.analyzer = StoryAnalyzer(self.character_loader.consultants)

    def reload_character_from_disk(self, character_name: str) -> bool:
        """Reload a character from disk, discarding in-memory edits.

        Part of the shared story-manager contract (see ``StoryManagerLike``).

        Args:
            character_name: Name of the character to reload.

        Returns:
            True if the reload succeeded, False if the file was not found.
        """
        return reload_character_cache(
            self.character_loader.consultants,
            self.character_loader.characters_path,
            character_name,
            self.ai_client,
        )

    def get_current_party(self) -> List[str]:
        """Get current party members (empty when no campaign is active)."""
        return self.party_manager.get_current_party()

    def get_character_list(self) -> List[str]:
        """
        Get list of all character names.

        Returns:
            List of character names
        """
        return self.character_loader.get_character_list()

    def get_character_profile(self, character_name: str) -> Optional[CharacterProfile]:
        """
        Get a character's profile.

        Args:
            character_name: Name of the character

        Returns:
            CharacterProfile if found, None otherwise
        """
        return self.character_loader.get_character_profile(character_name)

    def suggest_character_reaction(
        self,
        character_name: str,
        situation: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Get character reaction suggestion.

        Args:
            character_name: Name of the character
            situation: Situation description
            context: Optional context dictionary

        Returns:
            Reaction suggestion dictionary or error
        """
        consultant = self.character_loader.get_consultant(character_name)
        if not consultant:
            return {"error": f"Character {character_name} not found"}

        return consultant.suggest_reaction(situation, context or {})

    # Story file listing and creation are provided by StoryFileOperationsMixin.

    # Story Analysis Methods
    def analyze_story_file(self, filepath: str) -> Dict[str, Any]:
        """
        Analyze a story file for character actions and consistency.

        Args:
            filepath: Path to the story file

        Returns:
            Dictionary containing analysis results
        """
        return self.analyzer.analyze_story_file(filepath)

    # Story Update Methods
    def update_story_with_analysis(self, filepath: str, analysis: Dict[str, Any]):
        """
        Update story file with consultant analysis.

        Args:
            filepath: Path to the story file
            analysis: Analysis results dictionary
        """
        self.updater.update_story_with_analysis(filepath, analysis)
