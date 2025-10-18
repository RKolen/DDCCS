"""
Story File Operations Component.

Handles story file discovery, creation, and series management.
"""

import os
import re
from typing import List
from datetime import datetime
from src.utils.file_io import read_text_file, write_text_file, file_exists
from src.utils.path_utils import get_campaign_path


class StoryFileOperations:
    """Manages story file operations including creation and discovery."""

    # Allowed folder suffixes for story series
    VALID_SUFFIXES = ["_Campaign", "_Quest", "_Story", "_Adventure"]

    def __init__(self, workspace_path: str):
        """
        Initialize story file operations.

        Args:
            workspace_path: Root workspace directory path
        """
        self.workspace_path = workspace_path
        self.stories_path = workspace_path

    def validate_series_name(self, series_name: str) -> str:
        """
        Validate and fix series name to ensure it ends with a valid suffix.

        Args:
            series_name: The proposed series name

        Returns:
            Valid series name with proper suffix

        Raises:
            ValueError: If series name cannot be made valid
        """
        # Check if already has valid suffix
        for suffix in self.VALID_SUFFIXES:
            if series_name.endswith(suffix):
                return series_name

        # If no valid suffix, suggest adding _Quest as default
        suggested_name = f"{series_name}_Quest"
        raise ValueError(
            f"Series name '{series_name}' must end with one of: "
            f"{', '.join(self.VALID_SUFFIXES)}.\n"
            f"Suggestion: Use '{suggested_name}' instead."
        )

    def get_existing_stories(self) -> List[str]:
        """
        Get existing story files in the root directory (legacy stories).

        Returns:
            Sorted list of story filenames
        """
        story_files = []
        for filename in os.listdir(self.stories_path):
            if re.match(r"\d{3}.*\.md$", filename):
                story_files.append(filename)

        return sorted(story_files)

    def get_story_series(self) -> List[str]:
        """
        Get available story series (folders with numbered stories).

        Returns:
            Sorted list of series folder names
        """
        series_folders = []
        for item in os.listdir(self.stories_path):
            item_path = os.path.join(self.stories_path, item)
            if (
                os.path.isdir(item_path)
                and not item.startswith(".")
                and item != "characters"
                and item != "npcs"
                and item != "__pycache__"
            ):
                # Check if folder contains numbered story files
                if any(
                    re.match(r"\d{3}.*\.md$", f)
                    for f in os.listdir(item_path)
                    if f.endswith(".md")
                ):
                    series_folders.append(item)

        return sorted(series_folders)

    def get_story_files_in_series(self, series_name: str) -> List[str]:
        """
        Get story files within a specific series folder.

        Args:
            series_name: Name of the series folder

        Returns:
            Sorted list of story filenames in the series
        """
        series_path = get_campaign_path(series_name, self.workspace_path)
        if not file_exists(series_path):
            return []

        story_files = []
        for filename in os.listdir(series_path):
            if re.match(r"\d{3}.*\.md$", filename):
                story_files.append(filename)

        return sorted(story_files)

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
        # Validate series name has proper suffix
        validated_name = self.validate_series_name(series_name)

        # Create series folder
        clean_series_name = re.sub(r"[^a-zA-Z0-9_-]", "_", validated_name)
        series_path = get_campaign_path(clean_series_name, self.workspace_path)
        os.makedirs(series_path, exist_ok=True)

        # Create first story in series
        clean_name = re.sub(r"[^a-zA-Z0-9_-]", "_", first_story_name)
        filename = f"001_{clean_name}.md"
        filepath = os.path.join(series_path, filename)

        # Create story template
        template = self._create_story_template(first_story_name, description)

        write_text_file(filepath, template)

        print(f"OK Created new story series: {clean_series_name}")
        print(f"OK Created first story: {filename}")
        return filepath

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
        series_path = get_campaign_path(series_name, self.workspace_path)
        if not file_exists(series_path):
            raise ValueError(f"Story series '{series_name}' does not exist")

        # Get existing stories in series to determine next number
        existing_stories = self.get_story_files_in_series(series_name)

        if existing_stories:
            last_number = max(int(f[:3]) for f in existing_stories)
            next_number = last_number + 1
        else:
            next_number = 1

        # Create filename
        clean_name = re.sub(r"[^a-zA-Z0-9_-]", "_", story_name)
        filename = f"{next_number:03d}_{clean_name}.md"
        filepath = os.path.join(series_path, filename)

        # Create story template
        template = self._create_story_template(story_name, description)

        write_text_file(filepath, template)

        print(f"OK Created new story in {series_name}: {filename}")
        return filepath

    def create_new_story(self, story_name: str, description: str = "") -> str:
        """
        Create a new story file with the next sequence number in root directory.

        For legacy stories not in a series folder.

        Args:
            story_name: Name of the story
            description: Optional story description

        Returns:
            Path to the created story file
        """
        existing_stories = self.get_existing_stories()

        # Determine next sequence number
        if existing_stories:
            last_number = max(int(f[:3]) for f in existing_stories)
            next_number = last_number + 1
        else:
            next_number = 1

        # Create filename
        clean_name = re.sub(r"[^a-zA-Z0-9_-]", "_", story_name)
        filename = f"{next_number:03d}_{clean_name}.md"
        filepath = os.path.join(self.stories_path, filename)

        # Create story template
        template = self._create_story_template(story_name, description)

        write_text_file(filepath, template)

        print(f"OK Created new story: {filename}")
        return filepath

    def _create_story_template(self, story_name: str, description: str) -> str:
        """
        Create a markdown template for a new story.

        Args:
            story_name: Name of the story
            description: Story description

        Returns:
            Markdown template content
        """
        template_path = os.path.join(
            self.workspace_path, "templates", "story_template.md"
        )
        if file_exists(template_path):
            template = read_text_file(template_path)
            # Inject story_name and description at the top
            header = (
                f"# {story_name}\n\n**Created:** "
                f"{datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                f"**Description:** {description}\n\n---\n"
            )
            return header + template

        # Fallback to a minimal template
        return (
            f"# {story_name}\n\n"
            f"**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            f"**Description:** {description}\n\n---\n\n"
            "## DC Suggestions Needed\n"
            "*List any actions that need DC suggestions from the character consultants.*\n\n"
            "## Combat Summary\n*Paste combat prompts*\n\n"
            "## Story Narrative\n"
            "*The final narrative version of events will go here.*\n"
        )
