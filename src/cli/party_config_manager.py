"""
Party Configuration Manager

Handles loading and saving of party configuration files.
Party configuration is stored exclusively within campaign directories.
"""

import os
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from src.utils.file_io import load_json_file, save_json_file, file_exists
from src.utils.path_utils import get_party_config_path
from src.utils.terminal_display import print_warning

try:
    from src.validation.party_validator import validate_party_json

    VALIDATOR_AVAILABLE = True
except ImportError:
    VALIDATOR_AVAILABLE = False


def load_current_party(
    campaign_name: str,
    workspace_path: Optional[str] = None,
) -> List[str]:
    """Load current party members from campaign configuration.

    Args:
        campaign_name: Name of the campaign. Required.
        workspace_path: Optional workspace root path.

    Returns:
        List of party member names. Returns empty list if no party file exists.

    Raises:
        ValueError: If campaign_name is empty.
    """
    if not campaign_name:
        raise ValueError(
            "Cannot load party: no campaign selected. "
            "Please select a campaign first."
        )

    config_path = get_party_config_path(campaign_name, workspace_path)

    if not file_exists(config_path):
        return []

    try:
        data = load_json_file(config_path)
        if data is None:
            return []
        return data.get("party_members", [])
    except (OSError, ValueError) as e:
        print(f"Warning: Could not load party configuration: {e}")
        return []


def save_current_party(
    party_members: List[str],
    campaign_name: str,
    workspace_path: Optional[str] = None,
) -> None:
    """Save current party members to campaign configuration.

    Args:
        party_members: List of party member names.
        campaign_name: Name of the campaign. Required.
        workspace_path: Optional workspace root path.

    Raises:
        ValueError: If campaign_name is empty.
    """
    if not campaign_name:
        raise ValueError(
            "Cannot save party: no campaign selected. "
            "Please select a campaign first."
        )

    config_path = get_party_config_path(campaign_name, workspace_path)

    data: Dict[str, Any] = {
        "campaign_name": campaign_name,
        "party_members": party_members,
        "active": True,
        "last_updated": datetime.now().isoformat(),
    }

    # Preserve created_date and notes from existing file when available
    if file_exists(config_path):
        try:
            existing = load_json_file(config_path)
            if existing:
                data["created_date"] = existing.get(
                    "created_date", datetime.now().isoformat()
                )
                data["notes"] = existing.get("notes", "")
            else:
                data["created_date"] = datetime.now().isoformat()
        except (OSError, ValueError):
            data["created_date"] = datetime.now().isoformat()
    else:
        data["created_date"] = datetime.now().isoformat()

    # Validate before saving if validator is available
    if VALIDATOR_AVAILABLE:
        is_valid, errors = validate_party_json(data)
        if not is_valid:
            print_warning("Party configuration validation failed:")
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
                if profile is not None and profile.get("name") == member_name:
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
        if party_config is None:
            return party_dict
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
