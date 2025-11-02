"""
Story File Management Module

Handles story file I/O operations, story sequence numbering, and series management.
This module is responsible for:
- Creating new story series (campaigns, quests, adventures)
- Managing story sequence numbers (001_, 002_, etc.)
- Story file listing and organization
- Story template generation
"""

import os
import re
from dataclasses import dataclass
from typing import List
from datetime import datetime
from src.utils.file_io import read_text_file, write_text_file, file_exists
from src.utils.path_utils import get_campaign_path
from src.utils.story_file_helpers import (
    list_story_files,
    has_numbered_story_files,
    next_filename_for_dir,
)


@dataclass
class StoryFileContext:
    """Context for story file operations."""

    stories_path: str
    workspace_path: str


@dataclass
class StoryCreationOptions:
    """Options for story creation."""

    use_template: bool = False
    ai_generated_content: str = ""


def get_existing_stories(stories_path: str) -> List[str]:
    """Get existing story files in the root directory (legacy stories)."""
    return list_story_files(stories_path)


def get_story_series(stories_path: str) -> List[str]:
    """Get available story series (folders with numbered stories)."""
    series_folders = []
    for item in os.listdir(stories_path):
        item_path = os.path.join(stories_path, item)
        if (
            os.path.isdir(item_path)
            and not item.startswith(".")
            and item != "game_data"
            and item != "npcs"
            and item != "__pycache__"
        ):
            # Delegate numbered-file detection to helper
            if has_numbered_story_files(item_path):
                series_folders.append(item)

    return sorted(series_folders)


def get_story_files_in_series(stories_path: str, series_name: str) -> List[str]:
    """Get story files within a specific series folder."""
    series_path = get_campaign_path(series_name, stories_path)
    if not file_exists(series_path):
        return []
    return list_story_files(series_path)


def validate_series_name(series_name: str) -> str:
    """Validate and ensure series name has proper suffix."""
    valid_suffixes = ["_Campaign", "_Quest", "_Story", "_Adventure"]

    # Check if already has a valid suffix
    for suffix in valid_suffixes:
        if series_name.endswith(suffix):
            return series_name

    # Add _Campaign as default suffix
    return f"{series_name}_Campaign"


def _create_story_template(
    story_name: str,
    description: str,
    workspace_path: str = "",
    options: StoryCreationOptions = None,
) -> str:
    """Create markdown template for story (helper function).

    Supports three modes:
    1. AI-generated: If options.ai_generated_content provided
    2. Template-based: If options.use_template=True, loads from templates/
    3. Pure narrative: Default - just header with no content

    Args:
        story_name: Name of the story
        description: Story description
        workspace_path: Root workspace path (for finding templates/)
        options: StoryCreationOptions with template and AI settings

    Returns:
        Complete story file content as markdown string
    """
    if options is None:
        options = StoryCreationOptions()

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    header = (
        f"# {story_name}\n\n"
        f"**Created:** {timestamp}\n"
        f"**Description:** {description}\n\n"
    )

    # Priority 1: Use AI-generated content if provided
    if options.ai_generated_content and options.ai_generated_content.strip():
        return header + "---\n\n" + options.ai_generated_content

    # Priority 2: Use template if requested and workspace provided
    if options.use_template and workspace_path:
        template_path = os.path.join(workspace_path, "templates", "story_template.md")
        if file_exists(template_path):
            template_content = read_text_file(template_path)
            # Skip first line if it's a title (starts with #)
            lines = template_content.split("\n")
            if lines and lines[0].startswith("#"):
                template_content = "\n".join(lines[1:]).lstrip()
            return header + "---\n\n" + template_content

    # Priority 3: Default - pure narrative template
    return header


def create_new_story_series(
    ctx: StoryFileContext,
    series_name: str,
    first_story_name: str,
    *,
    description: str = "",
    options: StoryCreationOptions = None,
) -> str:
    """Create a new story series in its own folder.

    Series name MUST end with: _Campaign, _Quest, _Story, or _Adventure

    Args:
        ctx: StoryFileContext with paths
        series_name: Name of series (will be validated with suffix)
        first_story_name: Name of first story in series
        description: Story description
        options: StoryCreationOptions with template and AI settings

    Returns:
        Path to created story file
    """
    if options is None:
        options = StoryCreationOptions()

    # Validate series name has proper suffix
    validated_name = validate_series_name(series_name)

    # Create series folder
    clean_series_name = re.sub(r"[^a-zA-Z0-9_-]", "_", validated_name)
    series_path = get_campaign_path(clean_series_name, ctx.stories_path)
    os.makedirs(series_path, exist_ok=True)

    # Create first story in series
    clean_name = re.sub(r"[^a-zA-Z0-9_-]", "_", first_story_name)
    filename = f"001_{clean_name}.md"
    filepath = os.path.join(series_path, filename)

    # Create story template
    template = _create_story_template(
        first_story_name,
        description,
        workspace_path=ctx.workspace_path,
        options=options,
    )

    write_text_file(filepath, template)

    print(f"OK Created new story series: {clean_series_name}")
    print(f"OK Created first story: {filename}")
    return filepath


def create_story_in_series(
    ctx: StoryFileContext,
    series_name: str,
    story_name: str,
    *,
    description: str = "",
    options: StoryCreationOptions = None,
) -> str:
    """Create a new story in an existing series.

    Args:
        ctx: StoryFileContext with paths
        series_name: Existing series name
        story_name: Name of new story
        description: Story description
        options: StoryCreationOptions with template and AI settings

    Returns:
        Path to created story file
    """
    if options is None:
        options = StoryCreationOptions()

    series_path = get_campaign_path(series_name, ctx.stories_path)
    if not file_exists(series_path):
        raise ValueError(f"Story series '{series_name}' does not exist")

    # Compute next filename via helper
    filename, filepath = next_filename_for_dir(series_path, story_name)

    # Create story template
    template = _create_story_template(
        story_name,
        description,
        workspace_path=ctx.workspace_path,
        options=options,
    )

    write_text_file(filepath, template)

    print(f"OK Created new story in {series_name}: {filename}")
    return filepath


def create_new_story(
    ctx: StoryFileContext,
    story_name: str,
    *,
    description: str = "",
    options: StoryCreationOptions = None,
) -> str:
    """Create new story file with next sequence number (legacy stories in root).

    Args:
        ctx: StoryFileContext with paths
        story_name: Name of story
        description: Story description
        options: StoryCreationOptions with template and AI settings

    Returns:
        Path to created story file
    """
    if options is None:
        options = StoryCreationOptions()

    # Compute next filename via helper
    filename, filepath = next_filename_for_dir(ctx.stories_path, story_name)

    # Create story template
    template = _create_story_template(
        story_name,
        description,
        workspace_path=ctx.workspace_path,
        options=options,
    )

    write_text_file(filepath, template)

    print(f"OK Created new story: {filename}")
    return filepath


def create_pure_narrative_story(ctx: StoryFileContext, series_name: str,
                               story_name: str,
                               description: str = "") -> str:
    """Create a story file with pure narrative template (no guidance sections).

    Args:
        ctx: StoryFileContext with paths
        series_name: Name of series
        story_name: Name of story
        description: Story description

    Returns:
        Path to created story file
    """
    # Validate series name has proper suffix
    validated_series_name = validate_series_name(series_name)

    series_path = get_campaign_path(validated_series_name, ctx.stories_path)
    if not file_exists(series_path):
        os.makedirs(series_path, exist_ok=True)

    # Compute next filename via helper
    filename, filepath = next_filename_for_dir(series_path, story_name)

    # Create pure narrative template
    opts = StoryCreationOptions(use_template=False)
    template = _create_story_template(
        story_name,
        description,
        workspace_path=ctx.workspace_path,
        options=opts,
    )

    write_text_file(filepath, template)

    print(f"OK Created pure narrative story: {filename}")
    return filepath


def create_pure_story_file(series_path: str, story_name: str,
                          narrative_content: str) -> str:
    """Create a story file with pure narrative content only."""
    # Compute next filename via helper
    filename, filepath = next_filename_for_dir(series_path, story_name)

    # Write pure narrative
    content = f"# {story_name}\n\n{narrative_content}"
    write_text_file(filepath, content)

    print(f"[SUCCESS] Created pure story file: {filename}")
    return filepath
