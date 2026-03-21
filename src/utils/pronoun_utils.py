"""Pronoun handling utilities for characters and NPCs.

Provides helpers for parsing, displaying, and validating the optional
pronouns field used in character and NPC JSON profiles.
"""

from typing import Dict, Optional, Tuple

PRONOUN_SETS: Dict[str, Dict[str, str]] = {
    "he/him": {
        "subject": "he",
        "object": "him",
        "possessive_determiner": "his",
        "possessive_pronoun": "his",
        "reflexive": "himself",
    },
    "she/her": {
        "subject": "she",
        "object": "her",
        "possessive_determiner": "her",
        "possessive_pronoun": "hers",
        "reflexive": "herself",
    },
    "they/them": {
        "subject": "they",
        "object": "them",
        "possessive_determiner": "their",
        "possessive_pronoun": "theirs",
        "reflexive": "themselves",
    },
}

DEFAULT_PRONOUNS = "they/them"


def parse_pronouns(pronouns: Optional[str]) -> Dict[str, str]:
    """Parse pronouns field into a complete pronoun set.

    Args:
        pronouns: Pronouns string (e.g., "he/him") or None.

    Returns:
        Dictionary with subject, object, possessive_determiner,
        possessive_pronoun, and reflexive keys.
    """
    if pronouns is None:
        return PRONOUN_SETS[DEFAULT_PRONOUNS]

    pronouns_lower = pronouns.lower().strip()

    if pronouns_lower in PRONOUN_SETS:
        return PRONOUN_SETS[pronouns_lower]

    if "/" in pronouns_lower:
        parts = pronouns_lower.split("/")
        if len(parts) >= 2:
            subject = parts[0].strip()
            obj = parts[1].strip()
            return {
                "subject": subject,
                "object": obj,
                "possessive_determiner": f"{subject}s",
                "possessive_pronoun": f"{obj}s",
                "reflexive": f"{obj}self",
            }

    return PRONOUN_SETS[DEFAULT_PRONOUNS]


def get_pronoun_display(pronouns: Optional[str]) -> str:
    """Get display string for pronouns.

    Args:
        pronouns: Pronouns string or None.

    Returns:
        Display string (e.g., "he/him") or empty string if None.
    """
    if pronouns is None:
        return ""
    return pronouns.strip()


def validate_pronouns(pronouns: Optional[str]) -> Tuple[bool, str]:
    """Validate pronouns field format.

    Args:
        pronouns: Pronouns string or None.

    Returns:
        Tuple of (is_valid, error_message). error_message is empty string
        if valid.
    """
    if pronouns is None:
        return True, ""

    if not isinstance(pronouns, str):
        return False, "Pronouns must be a string or null"

    pronouns_stripped = pronouns.strip()
    if not pronouns_stripped:
        return False, "Pronouns cannot be empty string"

    return True, ""
