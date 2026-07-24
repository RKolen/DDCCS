"""Shared story-file operations for the story manager classes.

``StoryManager`` and ``EnhancedStoryManager`` implement an identical set of
story-file listing and creation methods that differ only in which directory they
operate on. This mixin holds that shared behaviour once so both managers honour
the same contract without duplicating it (and so neither class carries the extra
public-method weight).

Concrete managers must provide ``stories_path`` (where legacy/series stories
live) and ``workspace_path`` (the campaign workspace root); the annotations below
declare that requirement for the type checkers.
"""

from typing import List

from src.stories.story_file_manager import (
    StoryFileContext,
    create_new_story,
    create_new_story_series,
    create_story_in_series,
    get_existing_stories,
    get_story_files_in_series,
    get_story_series,
)


class StoryFileOperationsMixin:
    """Story-file listing and creation shared by the story managers."""

    stories_path: str
    workspace_path: str

    def _story_file_context(self) -> StoryFileContext:
        """Build the file-operation context from the manager's paths."""
        return StoryFileContext(
            stories_path=self.stories_path,
            workspace_path=self.workspace_path,
        )

    def get_existing_stories(self) -> List[str]:
        """Get existing story files in the root directory (legacy stories)."""
        return get_existing_stories(self.stories_path)

    def get_story_series(self) -> List[str]:
        """Get available story series (folders with numbered stories)."""
        return get_story_series(self.stories_path)

    def get_story_files_in_series(self, series_name: str) -> List[str]:
        """Get story files within a specific series folder."""
        return get_story_files_in_series(self.stories_path, series_name)

    def get_story_files(self) -> List[str]:
        """Get all story files (legacy alias for backward compatibility)."""
        return self.get_existing_stories()

    def create_new_story_series(
        self, series_name: str, first_story_name: str, description: str = ""
    ) -> str:
        """Create a new story series in its own folder.

        Raises:
            ValueError: If the series name is invalid.
        """
        return create_new_story_series(
            self._story_file_context(),
            series_name,
            first_story_name,
            description=description,
        )

    def create_story_in_series(
        self, series_name: str, story_name: str, description: str = ""
    ) -> str:
        """Create a new story in an existing series.

        Raises:
            ValueError: If the series does not exist.
        """
        return create_story_in_series(
            self._story_file_context(),
            series_name,
            story_name,
            description=description,
        )

    def create_new_story(self, story_name: str, description: str = "") -> str:
        """Create a new story file with the next sequence number (legacy)."""
        return create_new_story(
            self._story_file_context(), story_name, description=description
        )
