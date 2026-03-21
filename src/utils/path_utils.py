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
from typing import List, Optional

from src.utils.string_utils import sanitize_filename

# Default game_data directory name (can be overridden by config)
DEFAULT_GAME_DATA_DIR = "game_data"


def get_game_data_path(workspace_path: Optional[str] = None) -> str:
    """Get the path to the game_data directory.

    Args:
        workspace_path: Optional workspace root path (defaults to current directory)

    Returns:
        Path to game_data directory
    """
    if workspace_path is None:
        workspace_path = os.getcwd()
    return os.path.join(workspace_path, DEFAULT_GAME_DATA_DIR)


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
    campaign_name: str, workspace_path: Optional[str] = None
) -> str:
    """Get the path to the campaign-specific party configuration file.

    Party configuration is stored exclusively within campaign directories.
    Each campaign has its own ``current_party.json``.

    Args:
        campaign_name: Name of the campaign. Required.
        workspace_path: Optional workspace root path.

    Returns:
        Path to the campaign's current_party.json

    Raises:
        ValueError: If campaign_name is empty or not provided.
    """
    if not campaign_name:
        raise ValueError(
            "campaign_name is required. Party configuration is campaign-specific."
            " Select a campaign first."
        )

    campaign_dir = get_campaign_path(campaign_name, workspace_path)
    return os.path.join(campaign_dir, "current_party.json")


def get_all_campaign_party_paths(workspace_path: Optional[str] = None) -> List[str]:
    """Get all campaign party configuration file paths.

    Args:
        workspace_path: Optional workspace root path.

    Returns:
        List of paths to existing current_party.json files across all campaigns.
    """
    campaigns_dir = get_campaigns_dir(workspace_path)
    if not os.path.isdir(campaigns_dir):
        return []

    party_files: List[str] = []
    for entry in sorted(os.listdir(campaigns_dir)):
        campaign_dir = os.path.join(campaigns_dir, entry)
        if not os.path.isdir(campaign_dir):
            continue
        party_file = os.path.join(campaign_dir, "current_party.json")
        if os.path.isfile(party_file):
            party_files.append(party_file)

    return party_files


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
