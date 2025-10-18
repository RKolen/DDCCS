"""
File I/O utility functions for JSON operations and file handling.

This module provides reusable functions for:
- JSON file reading and writing with consistent error handling
- File existence checks
- UTF-8 encoding standardization
"""

import json
import os
from typing import Any, Dict, List, Optional
from pathlib import Path

def load_json_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Load JSON data from a file.

    Args:
        filepath: Path to the JSON file

    Returns:
        Dictionary containing the JSON data, or None if file doesn't exist

    Raises:
        json.JSONDecodeError: If the file contains invalid JSON
        IOError: If there's an error reading the file
    """
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json_file(filepath: str, data: Dict[str, Any],
                   indent: int = 2, ensure_ascii: bool = False) -> None:
    """Save data to a JSON file.

    Args:
        filepath: Path where the JSON file should be saved
        data: Dictionary to save as JSON
        indent: Number of spaces for indentation (default: 2)
        ensure_ascii: Whether to escape non-ASCII characters (default: False)

    Raises:
        IOError: If there's an error writing the file
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)


def read_text_file(filepath: str) -> Optional[str]:
    """Read text content from a file.

    Args:
        filepath: Path to the text file

    Returns:
        String containing the file contents, or None if file doesn't exist

    Raises:
        IOError: If there's an error reading the file
    """
    if not os.path.exists(filepath):
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def write_text_file(filepath: str, content: str) -> None:
    """Write text content to a file.

    Args:
        filepath: Path where the file should be saved
        content: Text content to write

    Raises:
        IOError: If there's an error writing the file
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def read_text_file_lines(filepath: str) -> Optional[List[str]]:
    """Read lines from a text file.

    Args:
        filepath: Path to the text file

    Returns:
        List of strings (lines), or None if file doesn't exist

    Raises:
        IOError: If there's an error reading the file
    """
    if not os.path.exists(filepath):
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        return f.readlines()


def file_exists(filepath: str) -> bool:
    """Check if a file exists.

    Args:
        filepath: Path to check

    Returns:
        True if file exists, False otherwise
    """
    return os.path.exists(filepath) and os.path.isfile(filepath)


def directory_exists(dirpath: str) -> bool:
    """Check if a directory exists.

    Args:
        dirpath: Path to check

    Returns:
        True if directory exists, False otherwise
    """
    return os.path.exists(dirpath) and os.path.isdir(dirpath)


def ensure_directory(dirpath: str) -> None:
    """Ensure a directory exists, creating it if necessary.

    Args:
        dirpath: Path to the directory
    """
    os.makedirs(dirpath, exist_ok=True)


def get_json_files_in_directory(directory: str,
                                exclude_patterns: Optional[List[str]] = None) -> List[Path]:
    """Get all JSON files in a directory, optionally excluding certain patterns.

    Args:
        directory: Directory path to search
        exclude_patterns: List of lowercase patterns to exclude (e.g., ["example", "template"])

    Returns:
        List of Path objects for JSON files
    """
    if not directory_exists(directory):
        return []

    exclude_patterns = exclude_patterns or []
    json_files = []

    for file in Path(directory).glob("*.json"):
        # Check if file should be excluded
        if any(pattern in file.name.lower() for pattern in exclude_patterns):
            continue
        json_files.append(file)

    return json_files
