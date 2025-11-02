"""
Base Manager for Story-Related CLI Interactions

Provides common functionality for session and character development managers.
"""

import os
from typing import Optional, Tuple

from src.cli.dnd_cli_helpers import get_series_and_story_from_manager


class BaseStoryInteractionManager:
    """Base class for managers that interact with story series/files."""

    def __init__(self, story_manager, workspace_path: str):
        """Initialize base story interaction manager.

        Args:
            story_manager: StoryManager instance
            workspace_path: Root workspace path
        """
        self.story_manager = story_manager
        self.workspace_path = workspace_path

    def get_series_and_story_with_filename(
        self,
    ) -> Optional[Tuple[str, str, str]]:
        """Get series, story filename, and clean story name.

        Returns:
            Tuple of (series_name, story_filename, story_name) or None
        """
        selection = get_series_and_story_from_manager(self.story_manager)
        if selection is None:
            return None

        series_name, story_filename = selection
        story_name = os.path.splitext(story_filename)[0]

        return (series_name, story_filename, story_name)

    def get_series_campaign_path(self, series_name: str) -> str:
        """Get the campaign path for a series.

        Args:
            series_name: Name of the series

        Returns:
            Full path to the campaign folder
        """
        return os.path.join(
            self.workspace_path, "game_data", "campaigns", series_name
        )

    def initialize_recording_workflow(
        self, workflow_name: str
    ) -> Optional[Tuple[str, str, str]]:
        """Initialize a recording workflow (session or character development).

        Prints header and gets series/story selection.

        Args:
            workflow_name: Name of workflow (e.g., "SESSION RESULTS")

        Returns:
            Tuple of (series_name, story_filename, story_name) or None
        """
        print(f"\n {workflow_name}")
        print("-" * 30)

        return self.get_series_and_story_with_filename()
