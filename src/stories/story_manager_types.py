"""Shared type alias for the two interchangeable story manager classes.

``StoryManager`` and ``EnhancedStoryManager`` are not related by inheritance -
``EnhancedStoryManager`` uses composition - yet both are assigned to the same
``self.story_manager`` attribute (see ``src/cli/dnd_consultant.py``) and passed
to the same parameters throughout the CLI. ``StoryManagerLike`` names that
either-or relationship truthfully.

The union members are string forward references, so importing this module never
triggers a runtime import of either manager (avoiding import cycles); the real
imports live under ``TYPE_CHECKING`` for the type checkers to resolve.
"""

from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from src.stories.enhanced_story_manager import EnhancedStoryManager
    from src.stories.story_manager import StoryManager

StoryManagerLike = Union["StoryManager", "EnhancedStoryManager"]
