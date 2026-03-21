"""
Party Configuration JSON Validation Module

Validates current party JSON files to ensure they contain proper structure
and data types according to the D&D Campaign System schema.

Usage:
    # Standalone validation (validates all campaign party files)
    python party_validator.py

    # Validate a specific campaign's party file
    python party_validator.py --campaign "Example_Campaign"

    # Validate a specific file path
    python party_validator.py [filepath]

    # Programmatic validation
    from src.validation.party_validator import validate_party_json, validate_party_file
    is_valid, errors = validate_party_file(
        "game_data/campaigns/Example_Campaign/current_party.json"
    )
"""

from typing import Dict, Any, List, Tuple, Optional
import os
from datetime import datetime
from src.utils.file_io import load_json_file, file_exists, get_json_files_in_directory
from src.utils.path_utils import get_characters_dir, get_party_config_path, get_campaigns_dir
from src.utils.validation_helpers import print_validation_report


def _validate_required_fields(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    required_fields = {"party_members": list, "last_updated": str}
    for field, expected_type in required_fields.items():
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(data[field], expected_type):
            errors.append(
                f"Field '{field}' must be of type {expected_type.__name__}, "
                f"got {type(data[field]).__name__}"
            )
    return errors


def _validate_party_members(data: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    members = data.get("party_members", [])
    if not isinstance(members, list):
        return errors
    if not members:
        errors.append(
            "party_members list is empty - party must have at least one member"
        )
    for i, member in enumerate(members):
        if not isinstance(member, str):
            errors.append(
                f"party_members[{i}] must be a string, got {type(member).__name__}"
            )
        elif not member.strip():
            errors.append(f"party_members[{i}] is an empty string")
    if len(members) != len(set(members)):
        errors.append("party_members contains duplicate entries")
    return errors


def _validate_party_cross_reference(
    data: Dict[str, Any], characters_dir: Optional[str]
) -> List[str]:
    errors: List[str] = []
    members = data.get("party_members", [])
    if (
        not isinstance(members, list)
        or not characters_dir
        or not file_exists(characters_dir)
    ):
        return errors
    available_characters = set()

    for char_file in get_json_files_in_directory(characters_dir):
        if char_file.name.endswith(".example.json"):
            continue
        try:
            char_data = load_json_file(str(char_file))
            if char_data is not None and "name" in char_data:
                available_characters.add(char_data["name"])
        except (ValueError, OSError):
            continue
    for member in members:
        if isinstance(member, str) and member not in available_characters:
            errors.append(
                f"Party member '{member}' does not match any character "
                f"file in {characters_dir}"
            )
    return errors


def _validate_last_updated(data: Dict[str, Any]) -> List[str]:
    errors = []
    last_updated = data.get("last_updated")
    if isinstance(last_updated, str):
        try:
            datetime.fromisoformat(last_updated)
        except ValueError:
            errors.append(
                f"last_updated must be a valid ISO format timestamp, got: '{last_updated}'"
            )
    return errors


def _validate_campaign_reference(
    data: Dict[str, Any], campaigns_dir: str
) -> List[str]:
    """Validate that campaign_name references an existing campaign directory.

    Args:
        data: The party data dictionary.
        campaigns_dir: Path to the campaigns directory.

    Returns:
        List of validation error strings.
    """
    errors: List[str] = []
    campaign_name = data.get("campaign_name")
    if campaign_name and isinstance(campaign_name, str):
        campaign_path = os.path.join(campaigns_dir, campaign_name)
        if not os.path.isdir(campaign_path):
            errors.append(
                f"campaign_name '{campaign_name}' not found in {campaigns_dir}"
            )
    return errors


def validate_party_json(
    data: Dict[str, Any],
    characters_dir: Optional[str] = None,
    campaigns_dir: Optional[str] = None,
) -> Tuple[bool, List[str]]:
    """
    Validate party JSON data structure and cross-reference with character files.

    Args:
        data: The party data dictionary to validate.
        characters_dir: Optional path to characters directory for cross-reference.
        campaigns_dir: Optional path to campaigns directory for campaign reference check.

    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_errors)
    """
    errors = []
    errors.extend(_validate_required_fields(data))
    errors.extend(_validate_party_members(data))
    errors.extend(_validate_party_cross_reference(data, characters_dir))
    errors.extend(_validate_last_updated(data))
    if campaigns_dir:
        errors.extend(_validate_campaign_reference(data, campaigns_dir))
    if errors:
        return (False, errors)
    return (True, [])


def validate_party_file(
    party_file_path: str, characters_dir: Optional[str] = None
) -> Tuple[bool, List[str]]:
    """Validate a party configuration JSON file.
    Loads the JSON file, checks for required fields, validates party members,
    cross-references with character files, and checks timestamp format.
    Args:
        party_file_path: Path to the party JSON file
        characters_dir: Optional path to characters directory for cross-reference validation
    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_errors)
    """
    # Check if file exists
    if not file_exists(party_file_path):
        return (False, [f"File not found: {party_file_path}"])

    try:
        data = load_json_file(party_file_path)
    except (ValueError, OSError) as err:
        return (False, [f"Error loading file: {err}"])
    if data is None:
        return (False, [f"File '{party_file_path}' could not be loaded or is empty"])
    return validate_party_json(data, characters_dir)


if __name__ == "__main__":
    import sys

    # CLI usage:
    #   python party_validator.py --campaign "Example_Campaign"
    #   python party_validator.py [filepath]
    #   python party_validator.py  (validates all campaign party files)

    CHARACTERS_PATH: Optional[str] = get_characters_dir()
    if CHARACTERS_PATH and not file_exists(CHARACTERS_PATH):
        CHARACTERS_PATH = None

    if len(sys.argv) > 1:
        if sys.argv[1] == "--campaign" and len(sys.argv) > 2:
            # Validate a specific campaign's party file
            CAMPAIGN_ARG = sys.argv[2]
            PARTY_FILE = get_party_config_path(CAMPAIGN_ARG)
            MAIN_VALID, MAIN_ERRORS = validate_party_file(PARTY_FILE, CHARACTERS_PATH)
            print_validation_report(PARTY_FILE, MAIN_VALID, MAIN_ERRORS)
            sys.exit(0 if MAIN_VALID else 1)
        else:
            # Validate a specific file path provided as the first argument
            PARTY_FILE = sys.argv[1]
            MAIN_VALID, MAIN_ERRORS = validate_party_file(PARTY_FILE, CHARACTERS_PATH)
            print_validation_report(PARTY_FILE, MAIN_VALID, MAIN_ERRORS)
            sys.exit(0 if MAIN_VALID else 1)
    else:
        # Validate all campaign party files
        CAMPAIGNS_DIR = get_campaigns_dir()
        main_all_valid = True
        main_found_any = False
        entries = sorted(os.listdir(CAMPAIGNS_DIR)) if os.path.isdir(CAMPAIGNS_DIR) else []
        for entry in entries:
            campaign_dir = os.path.join(CAMPAIGNS_DIR, entry)
            if not os.path.isdir(campaign_dir):
                continue
            party_path = os.path.join(campaign_dir, "current_party.json")
            if not os.path.isfile(party_path):
                continue
            main_found_any = True
            file_valid, file_errors = validate_party_file(party_path, CHARACTERS_PATH)
            print_validation_report(party_path, file_valid, file_errors)
            if not file_valid:
                main_all_valid = False
        if not main_found_any:
            print("[WARNING] No campaign party files found.")
            sys.exit(0)
        sys.exit(0 if main_all_valid else 1)
