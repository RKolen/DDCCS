"""
Party Configuration Manager

Handles loading and saving of party configuration files.
"""

import os
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.utils.file_io import load_json_file, save_json_file, file_exists
from src.utils.path_utils import get_party_config_path

try:
    from src.validation.party_validator import validate_party_json

    VALIDATOR_AVAILABLE = True
except ImportError:
    VALIDATOR_AVAILABLE = False


def load_current_party(
    config_path: Optional[str] = None,
    workspace_path: Optional[str] = None,
    campaign_name: Optional[str] = None,
) -> List[str]:
    """
    Load current party members from configuration file.

    Args:
        config_path (str): Path to party configuration JSON file

    Returns:
        List[str]: List of party member names
    """
    # Compute default config path if not provided
    if config_path is None:
        config_path = get_party_config_path(workspace_path, campaign_name)

    if file_exists(config_path):
        try:
            data = load_json_file(config_path)
            return data.get("party_members", [])
        except (OSError, ValueError) as e:
            print(f"Warning: Could not load party configuration: {e}")

    # Return default party if no config found
    return [
        "Aragorn",
        "Frodo",
        "Gandalf",
    ]


def save_current_party(
    party_members: List[str],
    config_path: Optional[str] = None,
    workspace_path: Optional[str] = None,
    campaign_name: Optional[str] = None,
):
    """
    Save current party members to configuration file.

    Args:
        party_members (List[str]): List of party member names
        config_path (str): Path to party configuration JSON file
    """
    data = {"party_members": party_members, "last_updated": datetime.now().isoformat()}

    # Compute default config path if not provided
    if config_path is None:
        config_path = get_party_config_path(workspace_path, campaign_name)

    # Validate before saving if validator is available
    if VALIDATOR_AVAILABLE:
        is_valid, errors = validate_party_json(data)
        if not is_valid:
            print("[WARNING]  Party configuration validation failed:")
            for error in errors:
                print(f"  - {error}")
            print("  Saving anyway, but please fix these issues.")

    try:
        save_json_file(config_path, data)
    except (OSError, TypeError) as e:
        print(f"Error: Could not save party configuration: {e}")


def _find_character_profile_by_name(
    member_name: str, characters_dir: str
) -> Optional[Dict[str, Any]]:
    """Find a character profile by matching the 'name' field in JSON files.

    Args:
        member_name: Name to match
        characters_dir: Directory containing character JSON files

    Returns:
        Character profile dict if found, None otherwise
    """
    if not os.path.exists(characters_dir):
        return None

    for filename in os.listdir(characters_dir):
        if filename.endswith(".json") and filename != "class.example.json":
            try:
                filepath = os.path.join(characters_dir, filename)
                profile = load_json_file(filepath)
                # Match by the "name" field in the JSON
                if profile.get("name") == member_name:
                    return profile
            except (json.JSONDecodeError, OSError):
                continue
    return None


def load_party_with_profiles(campaign_dir: str, workspace_path: str) -> Dict[str, Any]:
    """Load party members and their character profiles for a campaign.

    Reads the campaign's current_party.json and loads corresponding character
    profiles from game_data/characters/ directory.

    Args:
        campaign_dir: Path to the campaign directory
        workspace_path: Path to the workspace root

    Returns:
        Dictionary mapping character name to profile dict (JSON format)
    """
    party_dict: Dict[str, Any] = {}
    try:
        party_config_path = os.path.join(campaign_dir, "current_party.json")
        if not file_exists(party_config_path):
            return party_dict

        party_config = load_json_file(party_config_path)
        party_members = party_config.get("party_members", [])

        # Load character profiles
        characters_dir = os.path.join(workspace_path, "game_data", "characters")

        for member_name in party_members:
            profile = _find_character_profile_by_name(member_name, characters_dir)
            if profile:
                party_dict[member_name] = profile
            else:
                print(f"[WARNING] No character profile found for: {member_name}")

    except (OSError, json.JSONDecodeError) as e:
        print(f"[WARNING] Could not load party configuration: {e}")

    return party_dict
