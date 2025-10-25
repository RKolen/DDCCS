"""
Party Configuration Manager

Handles loading and saving of party configuration files.
"""

from typing import List, Optional
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
        "Theron Brightblade",
        "Mira Shadowstep",
        "Garrick Stonefist",
        "Elara Moonwhisper",
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
