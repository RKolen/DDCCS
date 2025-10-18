"""
Story Management System for VSCode Integration.

Main orchestrator that delegates to specialized components for character loading,
story file operations, analysis, and updates.
"""

from typing import Dict, List, Any, Optional
from src.characters.consultants.character_profile import CharacterProfile
from src.stories.story_character_loader import CharacterLoader
from src.stories.story_file_ops import StoryFileOperations
from src.stories.story_analysis import StoryAnalyzer
from src.stories.story_updater import StoryUpdater


class StoryManager:
    """Manages the story sequence system using specialized components."""

    def __init__(self, workspace_path: str, ai_client=None):
        """
        Initialize story manager with specialized components.

        Args:
            workspace_path: Root workspace directory path
            ai_client: Optional AI client for character consultants
        """
        self.workspace_path = workspace_path
        self.ai_client = ai_client

        # Initialize components using composition
        self.character_loader = CharacterLoader(workspace_path, ai_client)
        self.file_ops = StoryFileOperations(workspace_path)
        self.updater = StoryUpdater()

        # Load characters (creates analyzer after consultants are loaded)
        self.character_loader.load_characters()
        self.analyzer = StoryAnalyzer(self.character_loader.consultants)

    @property
    def consultants(self) -> Dict:
        """Access to character consultants."""
        return self.character_loader.consultants

    # Character Management Methods
    def load_characters(self):
        """Load all character profiles and create consultants."""
        self.character_loader.load_characters()
        # Update analyzer with new consultants
        self.analyzer = StoryAnalyzer(self.character_loader.consultants)

    def save_character_profile(self, profile: CharacterProfile):
        """
        Save a character profile and update consultant.

        Args:
            profile: Character profile to save
        """
        self.character_loader.save_character_profile(profile)
        # Update analyzer with new consultants
        self.analyzer = StoryAnalyzer(self.character_loader.consultants)

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
        self, character_name: str, situation: str, context: Dict[str, Any] = None
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

        return consultant.suggest_reaction(situation, context)

    # Story File Operations Methods
    def get_existing_stories(self) -> List[str]:
        """
        Get existing story files in the root directory (legacy stories).

        Returns:
            Sorted list of story filenames
        """
        return self.file_ops.get_existing_stories()

    def get_story_series(self) -> List[str]:
        """
        Get available story series (folders with numbered stories).

        Returns:
            Sorted list of series folder names
        """
        return self.file_ops.get_story_series()

    def get_story_files_in_series(self, series_name: str) -> List[str]:
        """
        Get story files within a specific series folder.

        Args:
            series_name: Name of the series folder

        Returns:
            Sorted list of story filenames in the series
        """
        return self.file_ops.get_story_files_in_series(series_name)

    def get_story_files(self) -> List[str]:
        """
        Get all story files (legacy method for backward compatibility).

        Returns:
            Sorted list of story filenames
        """
        return self.get_existing_stories()

    def create_new_story_series(
        self, series_name: str, first_story_name: str, description: str = ""
    ) -> str:
        """
        Create a new story series in its own folder.

        Args:
            series_name: Series name (must end with valid suffix)
            first_story_name: Name of the first story
            description: Optional story description

        Returns:
            Path to the created story file

        Raises:
            ValueError: If series name is invalid
        """
        return self.file_ops.create_new_story_series(
            series_name, first_story_name, description
        )

    def create_story_in_series(
        self, series_name: str, story_name: str, description: str = ""
    ) -> str:
        """
        Create a new story in an existing series.

        Args:
            series_name: Name of the existing series
            story_name: Name of the new story
            description: Optional story description

        Returns:
            Path to the created story file

        Raises:
            ValueError: If series does not exist
        """
        return self.file_ops.create_story_in_series(series_name, story_name, description)

    def create_new_story(self, story_name: str, description: str = "") -> str:
        """
        Create a new story file with the next sequence number in root directory.

        Args:
            story_name: Name of the story
            description: Optional story description

        Returns:
            Path to the created story file
        """
        return self.file_ops.create_new_story(story_name, description)

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
