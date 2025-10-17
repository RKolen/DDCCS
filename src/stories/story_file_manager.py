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


def get_existing_stories(stories_path: str) -> List[str]:
    """Get existing story files in the root directory (legacy stories)."""
    story_files = []
    for filename in os.listdir(stories_path):
        if re.match(r"\d{3}.*\.md$", filename):
            story_files.append(filename)

    return sorted(story_files)


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
            # Check if folder contains numbered story files
            if any(
                re.match(r"\d{3}.*\.md$", f)
                for f in os.listdir(item_path)
                if f.endswith(".md")
            ):
                series_folders.append(item)

    return sorted(series_folders)


def get_story_files_in_series(stories_path: str, series_name: str) -> List[str]:
    """Get story files within a specific series folder."""
    series_path = os.path.join(stories_path, series_name)
    if not os.path.exists(series_path):
        return []

    story_files = []
    for filename in os.listdir(series_path):
        if re.match(r"\d{3}.*\.md$", filename):
            story_files.append(filename)

    return sorted(story_files)


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
        if os.path.exists(template_path):
            with open(template_path, "r", encoding="utf-8") as template_file:
                template = template_file.read()
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
    series_path = os.path.join(stories_path, clean_series_name)
    os.makedirs(series_path, exist_ok=True)

    # Create first story in series
    clean_name = re.sub(r"[^a-zA-Z0-9_-]", "_", first_story_name)
    filename = f"001_{clean_name}.md"
    filepath = os.path.join(series_path, filename)

    # Create story template
    template = create_story_template(first_story_name, description,
                                    use_template=False,
                                    workspace_path=workspace_path)

    with open(filepath, "w", encoding="utf-8") as story_file:
        story_file.write(template)

    print(f"OK Created new story series: {clean_series_name}")
    print(f"OK Created first story: {filename}")
    return filepath


def create_story_in_series(stories_path: str, workspace_path: str,
                          series_name: str, story_name: str,
                          description: str = "") -> str:
    """Create a new story in an existing series."""
    series_path = os.path.join(stories_path, series_name)
    if not os.path.exists(series_path):
        raise ValueError(f"Story series '{series_name}' does not exist")

    # Get existing stories in series to determine next number
    existing_stories = get_story_files_in_series(stories_path, series_name)

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
    template = create_story_template(story_name, description,
                                    use_template=False,
                                    workspace_path=workspace_path)

    with open(filepath, "w", encoding="utf-8") as story_file:
        story_file.write(template)

    print(f"OK Created new story in {series_name}: {filename}")
    return filepath


def create_new_story(stories_path: str, workspace_path: str,
                    story_name: str, description: str = "") -> str:
    """Create new story file with next sequence number (for legacy stories in root)."""
    existing_stories = get_existing_stories(stories_path)

    # Determine next sequence number
    if existing_stories:
        last_number = max(int(f[:3]) for f in existing_stories)
        next_number = last_number + 1
    else:
        next_number = 1

    # Create filename
    clean_name = re.sub(r"[^a-zA-Z0-9_-]", "_", story_name)
    filename = f"{next_number:03d}_{clean_name}.md"
    filepath = os.path.join(stories_path, filename)

    # Create story template
    template = create_story_template(story_name, description,
                                    use_template=False,
                                    workspace_path=workspace_path)

    with open(filepath, "w", encoding="utf-8") as story_file:
        story_file.write(template)

    print(f"OK Created new story: {filename}")
    return filepath


def create_pure_narrative_story(stories_path: str, workspace_path: str,
                               series_name: str, story_name: str,
                               description: str = "") -> str:
    """Create a story file with pure narrative template (no guidance sections)."""
    # Validate series name has proper suffix
    validated_series_name = validate_series_name(series_name)

    series_path = os.path.join(stories_path, validated_series_name)
    if not os.path.exists(series_path):
        os.makedirs(series_path, exist_ok=True)

    # Get existing stories to determine number
    existing_stories = [
        f for f in os.listdir(series_path) if re.match(r"\d{3}.*\.md$", f)
    ]
    if existing_stories:
        last_number = max(int(f[:3]) for f in existing_stories)
        next_number = last_number + 1
    else:
        next_number = 1

    # Create filename
    clean_name = re.sub(r"[^a-zA-Z0-9_-]", "_", story_name)
    filename = f"{next_number:03d}_{clean_name}.md"
    filepath = os.path.join(series_path, filename)

    # Create pure narrative template
    template = create_story_template(story_name, description,
                                    use_template=False,
                                    workspace_path=workspace_path)

    with open(filepath, "w", encoding="utf-8") as story_file:
        story_file.write(template)

    print(f"OK Created pure narrative story: {filename}")
    return filepath


def create_pure_story_file(series_path: str, story_name: str,
                          narrative_content: str) -> str:
    """Create a story file with pure narrative content only."""
    # Determine story number
    existing_stories = [
        f for f in os.listdir(series_path) if re.match(r"\d{3}.*\.md$", f)
    ]
    if existing_stories:
        last_number = max(int(f[:3]) for f in existing_stories)
        next_number = last_number + 1
    else:
        next_number = 1

    # Create filename
    clean_name = re.sub(r"[^a-zA-Z0-9_-]", "_", story_name)
    filename = f"{next_number:03d}_{clean_name}.md"
    filepath = os.path.join(series_path, filename)

    # Write pure narrative
    with open(filepath, "w", encoding="utf-8") as story_file:
        story_file.write(f"# {story_name}\n\n")
        story_file.write(narrative_content)

    print(f"[SUCCESS] Created pure story file: {filename}")
    return filepath
