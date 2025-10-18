"""
String utility functions for text processing and normalization.

This module provides reusable functions for:
- String normalization (lowercase, replace spaces)
- Filename sanitization
- Text cleaning
- Name formatting
"""

import re
from typing import Optional

def sanitize_filename(name: str) -> str:
    """Convert a name to a safe filename format.

    Converts to lowercase and replaces spaces with underscores.

    Args:
        name: The name to sanitize

    Returns:
        Sanitized filename (lowercase with underscores)

    Example:
        >>> sanitize_filename("Kael Ironheart")
        'kael_ironheart'
    """
    return name.lower().replace(' ', '_')


def normalize_name(name: str) -> str:
    """Normalize a name for comparison.

    Converts to lowercase and strips whitespace.

    Args:
        name: The name to normalize

    Returns:
        Normalized name (lowercase, stripped)

    Example:
        >>> normalize_name("  Kael Ironheart  ")
        'kael ironheart'
    """
    return name.lower().strip()


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug.

    Converts to lowercase, replaces spaces with hyphens,
    and removes special characters.

    Args:
        text: The text to slugify

    Returns:
        URL-safe slug

    Example:
        >>> slugify("The Lost Mine of Phandelver")
        'the-lost-mine-of-phandelver'
    """
    # Convert to lowercase
    text = text.lower()
    # Replace spaces with hyphens
    text = text.replace(' ', '-')
    # Remove special characters (keep alphanumeric and hyphens)
    text = re.sub(r'[^a-z0-9-]', '', text)
    # Remove multiple consecutive hyphens
    text = re.sub(r'-+', '-', text)
    # Strip leading/trailing hyphens
    text = text.strip('-')
    return text


def clean_whitespace(text: str) -> str:
    """Clean excessive whitespace from text.

    Replaces multiple spaces with single space and strips ends.

    Args:
        text: The text to clean

    Returns:
        Text with normalized whitespace
    """
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    # Strip leading/trailing whitespace
    return text.strip()


def title_case_category(category: str) -> str:
    """Convert a category string to title case.

    Replaces underscores with spaces and applies title case.

    Args:
        category: The category string (e.g., "unresolved_plot_threads")

    Returns:
        Title-cased category (e.g., "Unresolved Plot Threads")
    """
    return category.replace('_', ' ').title()


def extract_bracketed_text(text: str, opening: str = '[', closing: str = ']') -> list[str]:
    """Extract text within brackets.

    Args:
        text: The text to search
        opening: Opening bracket character (default: '[')
        closing: Closing bracket character (default: ']')

    Returns:
        List of strings found within brackets
    """
    pattern = re.escape(opening) + r'([^\]]+)' + re.escape(closing)
    return re.findall(pattern, text)


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to a maximum length.

    Args:
        text: The text to truncate
        max_length: Maximum length (including suffix)
        suffix: Suffix to add if truncated (default: "...")

    Returns:
        Truncated text with suffix if needed
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def is_empty_or_whitespace(text: Optional[str]) -> bool:
    """Check if text is None, empty, or only whitespace.

    Args:
        text: The text to check

    Returns:
        True if text is None, empty, or only whitespace
    """
    return text is None or not text.strip()


def capitalize_first_letter(text: str) -> str:
    """Capitalize only the first letter of text, leaving the rest unchanged.

    Args:
        text: The text to capitalize

    Returns:
        Text with first letter capitalized

    Example:
        >>> capitalize_first_letter("kael speaks softly")
        'Kael speaks softly'
    """
    if not text:
        return text
    return text[0].upper() + text[1:]


def remove_multiple_blank_lines(text: str) -> str:
    """Remove multiple consecutive blank lines, leaving only one.

    Args:
        text: The text to clean

    Returns:
        Text with normalized blank lines
    """
    return re.sub(r'\n\n+', '\n\n', text)
