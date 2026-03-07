"""
Error Message Templates

Standardized error messages with consistent formatting and actionable guidance.
This module provides a centralized dictionary of error templates that can be
used throughout the D&D Consultant system.

Usage:
    from src.utils.error_templates import get_error_template, ERROR_TEMPLATES

    # Get formatted error message
    message, guidance = get_error_template("character_not_found", name="Aragorn")
"""

from typing import Any, Dict, Tuple

# Template format: {key: (message_template, guidance_template)}
ERROR_TEMPLATES: Dict[str, Tuple[str, str]] = {
    # Character errors
    "character_not_found": (
        "Character '{name}' not found",
        "Check the character name spelling. Use Character Management to see available characters.",
    ),
    "character_load_failed": (
        "Failed to load character '{name}'",
        "The character file may be corrupted. Check game_data/characters/{name}.json",
    ),
    "character_save_failed": (
        "Failed to save character '{name}'",
        "Check file permissions and disk space. The file may be open in another program.",
    ),
    "character_create_failed": (
        "Failed to create character '{name}'",
        "Check the character data and ensure all required fields are provided.",
    ),
    "character_delete_failed": (
        "Failed to delete character '{name}'",
        "Check file permissions. The file may be in use by another program.",
    ),
    # Story errors
    "story_not_found": (
        "Story '{name}' not found in campaign '{campaign}'",
        "Use 'List Stories' to see available stories in this campaign.",
    ),
    "story_generation_failed": (
        "Failed to generate story",
        "Ensure AI is configured correctly and you have characters in your party.",
    ),
    "story_parse_error": (
        "Could not parse story file",
        "The story file may have invalid markdown. Check for unclosed brackets or headers.",
    ),
    "story_save_failed": (
        "Failed to save story",
        "Check file permissions and disk space.",
    ),
    "story_delete_failed": (
        "Failed to delete story",
        "The file may be in use by another program.",
    ),
    # Campaign errors
    "campaign_not_found": (
        "Campaign '{name}' not found",
        "Use 'List Campaigns' to see available campaigns.",
    ),
    "campaign_create_failed": (
        "Failed to create campaign '{name}'",
        "Check that the campaign name is valid and you have write permissions.",
    ),
    "campaign_delete_failed": (
        "Failed to delete campaign '{name}'",
        "The campaign folder may contain files or be in use.",
    ),
    # AI errors
    "ai_not_configured": (
        "AI is not configured",
        "Set OPENAI_API_KEY in your .env file or use Setup menu to configure AI.",
    ),
    "ai_request_failed": (
        "AI request failed: {reason}",
        "Check your internet connection and API key. Try again in a moment.",
    ),
    "ai_response_invalid": (
        "AI returned invalid response",
        "The AI model may be overloaded. Try with a simpler prompt.",
    ),
    "ai_connection_failed": (
        "Could not connect to AI service",
        "Check your internet connection and API configuration.",
    ),
    "ai_rate_limited": (
        "AI service rate limit exceeded",
        "Wait a moment before trying again.",
    ),
    # File errors
    "file_not_found": (
        "{file_type} not found: {path}",
        "Check that the file exists and the path is correct.",
    ),
    "file_permission_denied": (
        "Permission denied: {path}",
        "Check file permissions or run with appropriate access rights.",
    ),
    "file_parse_error": (
        "Could not parse {file_type} file: {path}",
        "Ensure the file is valid {format} format.",
    ),
    "file_save_error": (
        "Failed to save {file_type}: {path}",
        "Check file permissions and disk space.",
    ),
    # Validation errors
    "validation_failed": (
        "Validation failed for {data_type}",
        "Fix the following issues: {errors}",
    ),
    "schema_validation_failed": (
        "{data_type} data does not match expected schema",
        "Check the data format and required fields.",
    ),
    # Party errors
    "party_empty": (
        "No characters in party",
        "Add characters to your party using the Party Configuration menu.",
    ),
    "party_member_not_found": (
        "Party member '{name}' not found in characters",
        "The character file may have been moved or renamed. Update party configuration.",
    ),
    "party_add_failed": (
        "Failed to add character to party",
        "Check that the character exists and is not already in the party.",
    ),
    "party_remove_failed": (
        "Failed to remove character from party",
        "The character may not be in the party.",
    ),
    # NPC errors
    "npc_not_found": (
        "NPC '{name}' not found",
        "Check the NPC name or use 'Create NPC' to add a new NPC.",
    ),
    "npc_detection_failed": (
        "NPC detection failed",
        "Story analysis could not identify NPCs. The story may not contain NPC references.",
    ),
    "npc_save_failed": (
        "Failed to save NPC '{name}'",
        "Check file permissions and NPC data.",
    ),
    "npc_load_failed": (
        "Failed to load NPC '{name}'",
        "The NPC file may be corrupted.",
    ),
    # Item errors
    "item_not_found": (
        "Item '{name}' not found",
        "Check the item name or use 'Create Item' to add a new item.",
    ),
    "item_save_failed": (
        "Failed to save item '{name}'",
        "Check file permissions and item data.",
    ),
    # Configuration errors
    "config_missing": (
        "Missing configuration: {config_name}",
        "Set {config_name} in your .env file or configuration.",
    ),
    "config_invalid": (
        "Invalid configuration for {config_name}: '{value}'",
        "Expected: {expected}",
    ),
    # General errors
    "operation_failed": (
        "Operation '{operation}' failed",
        "An unexpected error occurred. Check the logs for details.",
    ),
    "invalid_input": (
        "Invalid input: {details}",
        "Check your input and try again.",
    ),
    "data_not_found": (
        "{data_type} '{name}' not found",
        "Check that the {data_type} exists.",
    ),
    "data_load_failed": (
        "Failed to load {data_type}",
        "The data file may be corrupted or missing.",
    ),
    "data_save_failed": (
        "Failed to save {data_type}",
        "Check file permissions and disk space.",
    ),
}


def get_error_template(key: str, **kwargs: Any) -> Tuple[str, str]:
    """Get formatted error message and guidance.

    Args:
        key: Template key from ERROR_TEMPLATES.
        **kwargs: Values to format into templates.

    Returns:
        Tuple of (message, guidance).

    Raises:
        KeyError: If template key not found.
    """
    if key not in ERROR_TEMPLATES:
        raise KeyError(f"Unknown error template: '{key}'")

    message_template, guidance_template = ERROR_TEMPLATES[key]

    try:
        message = message_template.format(**kwargs)
        guidance = guidance_template.format(**kwargs)
    except KeyError as exc:
        # Missing format argument - leave placeholder
        placeholder = f"[{exc.args[0]}]"
        message = message_template.replace(f"{{{exc.args[0]}}}", placeholder)
        guidance = guidance_template.replace(f"{{{exc.args[0]}}}", placeholder)

    return message, guidance


def list_available_templates() -> Dict[str, str]:
    """Get a list of all available error template keys.

    Returns:
        Dictionary mapping template keys to their message templates.
    """
    return {key: msg for key, (msg, _) in ERROR_TEMPLATES.items()}


# Convenience exports
__all__ = [
    "ERROR_TEMPLATES",
    "get_error_template",
    "list_available_templates",
]
