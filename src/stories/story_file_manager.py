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
from typing import List
from datetime import datetime
from src.utils.file_io import read_text_file, write_text_file, file_exists
from src.utils.path_utils import get_campaign_path
from src.utils.story_file_helpers import (
    list_story_files,
    has_numbered_story_files,
    next_filename_for_dir,
)

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


def create_story_template(story_name: str, description: str,
                         use_template: bool = False,
                         workspace_path: str = "") -> str:
    """Create a markdown template for a new story."""
    if use_template and workspace_path:
        # Use full template with guidance
        template_path = os.path.join(workspace_path, "templates", "story_template.md")
        if file_exists(template_path):
            template = read_text_file(template_path)
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
            header = (f"# {story_name}\n\n**Created:** {timestamp}\n"
                     f"**Description:** {description}\n\n---\n")
            return header + template

    # Pure narrative template (default)
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    return (f"# {story_name}\n\n**Created:** {timestamp}\n"
           f"**Description:** {description}\n\n")


def create_new_story_series(stories_path: str, workspace_path: str,
                            series_name: str, first_story_name: str,
                            description: str = "") -> str:
    """
    Create a new story series in its own folder.

    Series name MUST end with: _Campaign, _Quest, _Story, or _Adventure
    """
    # Validate series name has proper suffix
    validated_name = validate_series_name(series_name)

    # Create series folder
    clean_series_name = re.sub(r"[^a-zA-Z0-9_-]", "_", validated_name)
    series_path = get_campaign_path(clean_series_name, stories_path)
    os.makedirs(series_path, exist_ok=True)

    # Create first story in series
    clean_name = re.sub(r"[^a-zA-Z0-9_-]", "_", first_story_name)
    filename = f"001_{clean_name}.md"
    filepath = os.path.join(series_path, filename)

    # Create story template
    template = create_story_template(first_story_name, description,
                                    use_template=False,
                                    workspace_path=workspace_path)

    write_text_file(filepath, template)

    print(f"OK Created new story series: {clean_series_name}")
    print(f"OK Created first story: {filename}")
    return filepath


def create_story_in_series(stories_path: str, workspace_path: str,
                          series_name: str, story_name: str,
                          description: str = "") -> str:
    """Create a new story in an existing series."""
    series_path = get_campaign_path(series_name, stories_path)
    if not file_exists(series_path):
        raise ValueError(f"Story series '{series_name}' does not exist")

    # Compute next filename via helper
    filename, filepath = next_filename_for_dir(series_path, story_name)

    # Create story template
    template = create_story_template(story_name, description,
                                    use_template=False,
                                    workspace_path=workspace_path)

    write_text_file(filepath, template)

    print(f"OK Created new story in {series_name}: {filename}")
    return filepath


def create_new_story(stories_path: str, workspace_path: str,
                    story_name: str, description: str = "") -> str:
    """Create new story file with next sequence number (for legacy stories in root)."""
    # Compute next filename via helper
    filename, filepath = next_filename_for_dir(stories_path, story_name)

    # Create story template
    template = create_story_template(story_name, description,
                                    use_template=False,
                                    workspace_path=workspace_path)

    write_text_file(filepath, template)

    print(f"OK Created new story: {filename}")
    return filepath


def create_pure_narrative_story(stories_path: str, workspace_path: str,
                               series_name: str, story_name: str,
                               description: str = "") -> str:
    """Create a story file with pure narrative template (no guidance sections)."""
    # Validate series name has proper suffix
    validated_series_name = validate_series_name(series_name)

    series_path = get_campaign_path(validated_series_name, stories_path)
    if not file_exists(series_path):
        os.makedirs(series_path, exist_ok=True)

    # Compute next filename via helper
    filename, filepath = next_filename_for_dir(series_path, story_name)

    # Create pure narrative template
    template = create_story_template(story_name, description,
                                    use_template=False,
                                    workspace_path=workspace_path)

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
