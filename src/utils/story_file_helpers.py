"""Story file helper utilities.

Extracted helpers to reduce duplicate code across story modules.
"""

import os
import re
from typing import List, Optional, Tuple

from src.utils.file_io import get_json_files_in_directory
from src.utils.path_utils import get_campaigns_dir

STORY_PATTERN = re.compile(r"\d{3}.*\.md$")


def list_story_files(dir_path: str) -> List[str]:
    """Return sorted list of story filenames in dir_path matching the numbering pattern."""
    try:
        files = [f for f in os.listdir(dir_path) if STORY_PATTERN.match(f)]
    except (FileNotFoundError, NotADirectoryError):
        return []
    return sorted(files)


def has_numbered_story_files(dir_path: str) -> bool:
    """Return True if the directory contains any numbered story markdown files."""
    try:
        return any(
            STORY_PATTERN.match(f) for f in os.listdir(dir_path) if f.endswith(".md")
        )
    except (FileNotFoundError, NotADirectoryError):
        return False


def next_filename_for_dir(dir_path: str, story_name: str) -> Tuple[str, str]:
    """Compute the next story filename in dir_path for a given story_name.

    Returns (filename, filepath).
    """
    existing = list_story_files(dir_path)
    if existing:
        last_number = max(int(f[:3]) for f in existing)
        next_number = last_number + 1
    else:
        next_number = 1

    clean_name = re.sub(r"[^a-zA-Z0-9_-]", "_", story_name)
    filename = f"{next_number:03d}_{clean_name}.md"
    filepath = os.path.join(dir_path, filename)
    return filename, filepath


def get_story_file_paths_in_series(
    workspace_path: str, series_name: str
) -> List[str]:
    """Return sorted absolute paths to all numbered story files in a series.

    Args:
        workspace_path: Root workspace path.
        series_name: Campaign/series directory name under game_data/campaigns/.

    Returns:
        Sorted list of absolute file paths matching the story numbering pattern.
    """
    series_dir = os.path.join(get_campaigns_dir(workspace_path), series_name)
    if not os.path.isdir(series_dir):
        return []
    return sorted(
        os.path.join(series_dir, f)
        for f in os.listdir(series_dir)
        if STORY_PATTERN.match(f)
    )


def read_story_lines(filepath: str) -> Optional[List[str]]:
    """Read all lines from a story file.

    Args:
        filepath: Absolute path to the story markdown file.

    Returns:
        List of lines (with newlines preserved), or None if the file
        cannot be found or read.
    """
    try:
        with open(filepath, encoding="utf-8") as fh:
            return fh.readlines()
    except OSError:
        return None


def list_character_json_candidates(characters_dir: str) -> List[str]:
    """Return JSON character file paths in a directory excluding templates/examples."""
    result: List[str] = []
    try:
        for fp in get_json_files_in_directory(characters_dir):
            filename = os.path.basename(fp)
            if (
                filename.startswith("class.example")
                or filename.endswith(".example.json")
                or filename.startswith("template")
            ):
                continue
            result.append(str(fp))
    except (FileNotFoundError, NotADirectoryError):
        # If the directory isn't present, return empty
        return []
    return result
