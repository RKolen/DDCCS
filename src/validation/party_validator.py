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

import json
import os
from typing import Dict, Any, List, Tuple
from datetime import datetime


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
                "got {type(data[field]).__name__}"
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
    data: Dict[str, Any], characters_dir: str
) -> List[str]:
    errors = []
    members = data.get("party_members", [])
    if (
        not isinstance(members, list)
        or not characters_dir
        or not os.path.exists(characters_dir)
    ):
        return errors
    available_characters = set()
    for filename in os.listdir(characters_dir):
        if filename.endswith(".json") and not filename.endswith(".example.json"):
            char_path = os.path.join(characters_dir, filename)
            try:
                with open(char_path, "r", encoding="utf-8") as f:
                    char_data = json.load(f)
                    if "name" in char_data:
                        available_characters.add(char_data["name"])
            except (json.JSONDecodeError, OSError):
                continue
    for member in members:
        if isinstance(member, str) and member not in available_characters:
            errors.append(
                f"Party member '{member}' does not match any character "
                "file in {characters_dir}"
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
    data: Dict[str, Any], characters_dir: str = None
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
    party_file_path: str, characters_dir: str = None
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
    if not os.path.exists(party_file_path):
        return (False, [f"File not found: {party_file_path}"])

    try:
        with open(party_file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as err:
        return (False, [f"Invalid JSON format: {err}"])
    except OSError as err:
        return (False, [f"Error reading file: {err}"])
    return validate_party_json(data, characters_dir)


def print_validation_report(file_path: str, is_valid: bool, errors: List[str]):
    """Print a formatted validation report."""
    if is_valid:
        print(f"✓ {file_path}: Valid")
    else:
        print(f"✗ {file_path}: INVALID")
        for error_item in errors:
            print(f"  - {error_item}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Validate specific file
        filepath = sys.argv[1]

        # Auto-detect characters directory for cross-reference
        CHARACTERS_PATH = os.path.join("game_data", "characters")
        if not os.path.exists(CHARACTERS_PATH):
            CHARACTERS_PATH = None

            main_valid, main_errors = validate_party_file(filepath, CHARACTERS_PATH)
            print_validation_report(filepath, main_valid, main_errors)
            sys.exit(0 if main_valid else 1)
    else:
        # Validate current party file
        PARTY_FILE = os.path.join("game_data", "current_party", "current_party.json")
        if not os.path.exists(PARTY_FILE):
            print(f"Error: Party configuration file not found: {PARTY_FILE}")
            print("Looking for current_party.json in game_data/current_party/")
            sys.exit(1)

        MAIN_CHARACTERS_DIR = os.path.join("game_data", "characters")
        if not os.path.exists(MAIN_CHARACTERS_DIR):
            MAIN_CHARACTERS_DIR = None

            main_valid, main_errors = validate_party_file(
                PARTY_FILE, MAIN_CHARACTERS_DIR
            )
            print_validation_report(PARTY_FILE, main_valid, main_errors)
            sys.exit(0 if main_valid else 1)
