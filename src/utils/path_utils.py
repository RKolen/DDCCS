"""
Path utility functions for game data directories and file paths.

This module provides standardized path construction for:
- game_data directory structure
- Character files
- NPC files
- Campaign directories
- Items registry
- Party configuration
"""

import os
from typing import Optional

from src.utils.string_utils import sanitize_filename


def get_game_data_path(workspace_path: Optional[str] = None) -> str:
    """Get the path to the game_data directory.

    Args:
        workspace_path: Optional workspace root path (defaults to current directory)

    Returns:
        Path to game_data directory
    """
    if workspace_path is None:
        workspace_path = os.getcwd()
    return os.path.join(workspace_path, "game_data")


def get_characters_dir(workspace_path: Optional[str] = None) -> str:
    """Get the path to the characters directory.

    Args:
        workspace_path: Optional workspace root path

    Returns:
        Path to game_data/characters directory
    """
    return os.path.join(get_game_data_path(workspace_path), "characters")


def get_npcs_dir(workspace_path: Optional[str] = None) -> str:
    """Get the path to the NPCs directory.

    Args:
        workspace_path: Optional workspace root path

    Returns:
        Path to game_data/npcs directory
    """
    return os.path.join(get_game_data_path(workspace_path), "npcs")


def get_campaigns_dir(workspace_path: Optional[str] = None) -> str:
    """Get the path to the campaigns directory.

    Args:
        workspace_path: Optional workspace root path

    Returns:
        Path to game_data/campaigns directory
    """
    return os.path.join(get_game_data_path(workspace_path), "campaigns")


def get_campaign_path(campaign_name: str, workspace_path: Optional[str] = None) -> str:
    """Get the path to a specific campaign directory.

    Args:
        campaign_name: Name of the campaign
        workspace_path: Optional workspace root path

    Returns:
        Path to game_data/campaigns/<campaign_name> directory
    """
    return os.path.join(get_campaigns_dir(workspace_path), campaign_name)


def get_items_registry_path(workspace_path: Optional[str] = None) -> str:
    """Get the path to the custom items registry file.

    Args:
        workspace_path: Optional workspace root path

    Returns:
        Path to game_data/items/custom_items_registry.json
    """
    return os.path.join(
        get_game_data_path(workspace_path), "items", "custom_items_registry.json"
    )


def get_party_config_path(
    workspace_path: Optional[str] = None, campaign_name: Optional[str] = None
) -> str:
    """Get the path to the current party configuration file.

    By default this returns the global `game_data/current_party/current_party.json`.
    If `campaign_name` is provided, returns the campaign-local
    `game_data/campaigns/<campaign_name>/current_party.json` so each campaign can
    have its own party configuration.

    Args:
        workspace_path: Optional workspace root path
        campaign_name: Optional campaign folder name to use for campaign-local party

    Returns:
        Path to the selected current_party.json file
    """
    if campaign_name:
        campaign_path = get_campaign_path(campaign_name, workspace_path)
        return os.path.join(campaign_path, "current_party.json")

    return os.path.join(
        get_game_data_path(workspace_path),
        "current_party",
        "current_party.json",
    )


def get_character_file_path(
    character_name: str, workspace_path: Optional[str] = None
) -> str:
    """Get the path to a character JSON file.

    Args:
        character_name: Name of the character (will be sanitized)
        workspace_path: Optional workspace root path

    Returns:
        Path to game_data/characters/<character_name>.json
    """
    filename = sanitize_filename(character_name)
    return os.path.join(get_characters_dir(workspace_path), f"{filename}.json")


def get_npc_file_path(npc_name: str, workspace_path: Optional[str] = None) -> str:
    """Get the path to an NPC JSON file.

    Args:
        npc_name: Name of the NPC (will be sanitized)
        workspace_path: Optional workspace root path

    Returns:
        Path to game_data/npcs/<npc_name>.json
    """
    filename = sanitize_filename(npc_name)
    return os.path.join(get_npcs_dir(workspace_path), f"{filename}.json")


def get_story_file_path(
    campaign_name: str, story_name: str, workspace_path: Optional[str] = None
) -> str:
    """Get the path to a story markdown file.

    Args:
        campaign_name: Name of the campaign
        story_name: Name/number of the story file
        workspace_path: Optional workspace root path

    Returns:
        Path to game_data/campaigns/<campaign>/<story>.md
    """
    campaign_path = get_campaign_path(campaign_name, workspace_path)
    return os.path.join(campaign_path, story_name)
