"""
Party Configuration JSON Validation Module

Validates current party JSON files to ensure they contain proper structure
and data types according to the D&D Campaign System schema.

Usage:
    # Standalone validation
    python party_validator.py [filepath]

    # Programmatic validation
    from src.validation.party_validator import validate_party_json, validate_party_file
    is_valid, errors = validate_party_file("game_data/current_party/current_party.json")
"""

from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from ..utils.file_io import load_json_file, file_exists, get_json_files_in_directory
from ..utils.path_utils import get_characters_dir, get_party_config_path
from ..utils.validation_helpers import print_validation_report


class PartyValidationError(Exception):
    """Custom exception for party validation errors."""


def _validate_required_fields(data: Dict[str, Any]) -> List[str]:
    errors = []
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
    errors = []
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
    errors = []
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


def validate_party_json(
    data: Dict[str, Any], characters_dir: Optional[str] = None
) -> Tuple[bool, List[str]]:
    """
    Validate party JSON data structure and cross-reference with character files.

    Args:
        data (Dict[str, Any]): The party data dictionary to validate.
        characters_dir (str): Optional path to characters directory for cross-reference.

    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_errors)
    """
    errors = []
    errors.extend(_validate_required_fields(data))
    errors.extend(_validate_party_members(data))
    errors.extend(_validate_party_cross_reference(data, characters_dir))
    errors.extend(_validate_last_updated(data))
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
    #   python party_validator.py [filepath]
    #   python party_validator.py --campaign "Example_Campaign"
    # validate campaign-local current_party.json

    if len(sys.argv) > 1:
        # If --campaign provided, validate the campaign's current_party.json
        if sys.argv[1] == "--campaign" and len(sys.argv) > 2:
            campaign_name = sys.argv[2]
            PARTY_FILE = get_party_config_path(campaign_name=campaign_name)
        else:
            # Validate specific file provided as first arg
            PARTY_FILE = sys.argv[1]

        # Auto-detect characters directory for cross-reference
        CHARACTERS_PATH = get_characters_dir()
        if not file_exists(CHARACTERS_PATH):
            CHARACTERS_PATH = None

        main_valid, main_errors = validate_party_file(PARTY_FILE, CHARACTERS_PATH)
        print_validation_report(PARTY_FILE, main_valid, main_errors)
        sys.exit(0 if main_valid else 1)
    else:
        # Validate default current party file
        PARTY_FILE = get_party_config_path()
        if not file_exists(PARTY_FILE):
            print(f"[ERROR] Party configuration file not found: {PARTY_FILE}")
            print("Looking for current_party.json in game_data/current_party/")
            sys.exit(1)

        MAIN_CHARACTERS_DIR = get_characters_dir()
        if not file_exists(MAIN_CHARACTERS_DIR):
            MAIN_CHARACTERS_DIR = None

        main_valid, main_errors = validate_party_file(PARTY_FILE, MAIN_CHARACTERS_DIR)
        print_validation_report(PARTY_FILE, main_valid, main_errors)
        sys.exit(0 if main_valid else 1)
