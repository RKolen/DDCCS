"""Story file helper utilities.

Extracted helpers to reduce duplicate code across story modules.
"""
import os
import re
from typing import List, Tuple
from src.utils.file_io import get_json_files_in_directory

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
        return any(STORY_PATTERN.match(f) for f in os.listdir(dir_path) if f.endswith(".md"))
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
            result.append(fp)
    except (FileNotFoundError, NotADirectoryError):
        # If the directory isn't present, return empty
        return []
    return result
