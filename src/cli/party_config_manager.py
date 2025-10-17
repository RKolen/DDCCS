"""
Party Configuration Manager

Handles loading and saving of party configuration files.
"""

import json
import os
from typing import List
from datetime import datetime

try:
    from src.validation.party_validator import validate_party_json

    VALIDATOR_AVAILABLE = True
except ImportError:
    VALIDATOR_AVAILABLE = False


def load_current_party(
    config_path: str = "game_data/current_party/current_party.json",
) -> List[str]:
    """
    Load current party members from configuration file.

    Args:
        config_path (str): Path to party configuration JSON file

    Returns:
        List[str]: List of party member names
    """
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("party_members", [])
        except (OSError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load party configuration: {e}")

    # Return default party if no config found
    return [
        "Theron Brightblade",
        "Mira Shadowstep",
        "Garrick Stonefist",
        "Elara Moonwhisper",
    ]


def save_current_party(
    party_members: List[str],
    config_path: str = "game_data/current_party/current_party.json",
):
    """
    Save current party members to configuration file.

    Args:
        party_members (List[str]): List of party member names
        config_path (str): Path to party configuration JSON file
    """
    data = {"party_members": party_members, "last_updated": datetime.now().isoformat()}

    # Validate before saving if validator is available
    if VALIDATOR_AVAILABLE:
        is_valid, errors = validate_party_json(data)
        if not is_valid:
            print("⚠️  Party configuration validation failed:")
            for error in errors:
                print(f"  - {error}")
            print("  Saving anyway, but please fix these issues.")

    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except (OSError, TypeError) as e:
        print(f"Error: Could not save party configuration: {e}")
