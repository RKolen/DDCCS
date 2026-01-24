"""
NPC JSON Validation Module

Validates NPC profile JSON files to ensure they contain all required fields
and proper data types according to the D&D Campaign System schema.

Usage:
    # Standalone validation
    python -m src.validation.npc_validator [filepath]

    # Programmatic validation
    from src.validation.npc_validator import validate_npc_json, validate_npc_file
    is_valid, errors = validate_npc_file("game_data/npcs/my_npc.json")
"""

from typing import Dict, Any, List, Tuple
from src.utils.file_io import load_json_file, get_json_files_in_directory
from src.utils.path_utils import get_npcs_dir
from src.utils.validation_helpers import get_type_name, print_validation_report
from src.characters.npc_constants import ABILITY_SCORE_NAMES


def _validate_ai_config(ai_config: dict) -> List[str]:
    ai_errors = []
    if "enabled" not in ai_config:
        ai_errors.append("ai_config missing required field: enabled")
    elif not isinstance(ai_config["enabled"], bool):
        ai_errors.append("ai_config.enabled must be a boolean")
    if "temperature" in ai_config and not isinstance(
        ai_config["temperature"], (int, float)
    ):
        ai_errors.append("ai_config.temperature must be a number")
    if "max_tokens" in ai_config and not isinstance(ai_config["max_tokens"], int):
        ai_errors.append("ai_config.max_tokens must be an integer")
    if "system_prompt" in ai_config and not isinstance(ai_config["system_prompt"], str):
        ai_errors.append("ai_config.system_prompt must be a string")
    if "model" in ai_config and not isinstance(ai_config["model"], str):
        ai_errors.append("ai_config.model must be a string")
    if "base_url" in ai_config and not isinstance(ai_config["base_url"], str):
        ai_errors.append("ai_config.base_url must be a string")
    if "api_key" in ai_config and not isinstance(ai_config["api_key"], str):
        ai_errors.append("ai_config.api_key must be a string")
    return ai_errors


def _validate_relationships(relationships: dict) -> List[str]:
    relationship_errors = []
    for char_name, relationship in relationships.items():
        if not isinstance(relationship, str):
            relationship_errors.append(
                f"Relationship value for '{char_name}' must be a string"
            )
    return relationship_errors


def _validate_list_of_strings(field: list, field_name: str) -> List[str]:
    string_errors = []
    for item in field:
        if not isinstance(item, str):
            string_errors.append(f"All {field_name} must be strings")
            break
    return string_errors


def _validate_required_fields(
    data: Dict[str, Any], field_dict: Dict[str, type]
) -> List[str]:
    """Validate required fields and their types.

    Args:
        data: Dictionary containing data to validate
        field_dict: Dictionary mapping field names to expected types

    Returns:
        List of validation error messages
    """
    validation_errors = []
    for field, expected_type in field_dict.items():
        if field not in data:
            validation_errors.append(f"Missing required field: {field}")
        elif not isinstance(data[field], expected_type):
            validation_errors.append(
                f"Field '{field}' must be of type {expected_type.__name__}, got"
                f"{type(data[field]).__name__}"
            )
    return validation_errors


def _validate_optional_fields(
    data: Dict[str, Any], field_dict: Dict[str, Any]
) -> List[str]:
    """Validate optional fields (only if present).

    Args:
        data: Dictionary containing data to validate
        field_dict: Dictionary mapping field names to expected types

    Returns:
        List of validation error messages
    """
    validation_errors = []
    for field, expected_type in field_dict.items():
        if field in data and not isinstance(data[field], expected_type):
            type_name = get_type_name(expected_type)
            validation_errors.append(
                f"Field '{field}' must be of type {type_name}, got "
                f"{type(data[field]).__name__}"
            )
    return validation_errors


def _validate_ability_scores(data: Dict[str, Any]) -> List[str]:
    """Validate ability_scores structure.

    Args:
        data: Dictionary containing NPC data

    Returns:
        List of validation error messages
    """
    validation_errors = []
    if "ability_scores" in data and isinstance(data["ability_scores"], dict):
        for ability in ABILITY_SCORE_NAMES:
            if ability not in data["ability_scores"]:
                validation_errors.append(
                    f"ability_scores missing required field: {ability}"
                )
            elif not isinstance(data["ability_scores"][ability], int):
                validation_errors.append(
                    f"ability_scores['{ability}'] must be int, got "
                    f"{type(data['ability_scores'][ability]).__name__}"
                )
    return validation_errors


class NPCValidationError(Exception):
    """Custom exception for NPC validation errors."""


def validate_npc_json(
    data: Dict[str, Any], source_path: str = ""
) -> Tuple[bool, List[str]]:
    """
    Validate an NPC profile dictionary against the required schema.

    Supports both simplified and full character profiles.

    Args:
        data: Dictionary containing NPC profile data
        source_path: Optional filepath for error messages

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    validation_errors = []

    # Check profile type
    profile_type = data.get("profile_type", "simplified")
    if profile_type not in ["simplified", "full"]:
        validation_errors.append(
            "profile_type must be 'simplified' or 'full', got " f"'{profile_type}'"
        )

    # Check faction field
    faction = data.get("faction", "neutral")
    if faction not in ["ally", "neutral", "enemy"]:
        validation_errors.append(
            f"faction must be 'ally', 'neutral', or 'enemy', got '{faction}'"
        )

    # Core NPC fields (required for all profiles)
    required_fields = {
        "name": str,
        "role": str,
        "species": str,
        "lineage": str,
        "personality": str,
        "relationships": dict,
        "key_traits": list,
        "abilities": list,
        "recurring": bool,
        "notes": str,
        "ai_config": dict,
        "profile_type": str,
        "faction": str,
    }

    # Optional fields for all profiles
    optional_fields = {
        "nickname": (str, type(None)),
    }

    # Full character profile fields (required only if profile_type="full")
    full_profile_required = {
        "dnd_class": str,
        "level": int,
        "ability_scores": dict,
        "max_hit_points": int,
        "armor_class": int,
    }

    # Full character profile optional fields
    full_profile_optional = {
        "subclass": (str, type(None)),
        "skills": dict,
        "movement_speed": int,
        "proficiency_bonus": int,
        "equipment": dict,
        "spell_slots": dict,
        "known_spells": list,
        "background": (str, type(None)),
        "personality_traits": list,
        "ideals": list,
        "bonds": list,
        "flaws": list,
        "backstory": (str, type(None)),
        "feats": list,
        "magic_items": list,
        "class_abilities": list,
        "specialized_abilities": list,
        "major_plot_actions": list,
    }

    # Check for required fields and types
    validation_errors.extend(_validate_required_fields(data, required_fields))

    # Check optional fields (only validate type if field is present)
    validation_errors.extend(_validate_optional_fields(data, optional_fields))

    # Validate full profile fields if profile_type is "full"
    if profile_type == "full":
        validation_errors.extend(_validate_required_fields(data, full_profile_required))
        validation_errors.extend(_validate_optional_fields(data, full_profile_optional))
        validation_errors.extend(_validate_ability_scores(data))

    # Disallowed characters in name
    disallowed_chars = set("'\"`$%&|<>/\\")
    name = data.get("name", "")
    if any(c in name for c in disallowed_chars):
        validation_errors.append(
            f"{source_path}: Strange characters are not allowed in NPC name. Please "
            f"use another name (disallowed: {''.join(disallowed_chars)}). Name: '{name}'"
        )

    # Validate ai_config structure if present
    if "ai_config" in data and isinstance(data["ai_config"], dict):
        validation_errors.extend(_validate_ai_config(data["ai_config"]))

    # Validate relationships structure
    if "relationships" in data and isinstance(data["relationships"], dict):
        validation_errors.extend(_validate_relationships(data["relationships"]))

    # Validate key_traits is list of strings
    if "key_traits" in data and isinstance(data["key_traits"], list):
        validation_errors.extend(
            _validate_list_of_strings(data["key_traits"], "key_traits")
        )

    # Validate abilities is list of strings
    if "abilities" in data and isinstance(data["abilities"], list):
        validation_errors.extend(
            _validate_list_of_strings(data["abilities"], "abilities")
        )

    return (len(validation_errors) == 0, validation_errors)


def validate_npc_file(filepath: str) -> Tuple[bool, List[str]]:
    """
    Validate an NPC JSON file.

    Args:
        filepath: Path to the NPC JSON file

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    # Try to load and parse JSON
    try:
        data = load_json_file(filepath)
        if data is None:
            return (False, [f"File not found: {filepath}"])

        # Validate the data
        return validate_npc_json(data, filepath)

    except ValueError as e:  # json.JSONDecodeError is a subclass of ValueError
        return (False, [f"Invalid JSON format: {e}"])
    except OSError as e:
        return (False, [f"Error reading file: {e}"])


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Validate specific file
        npc_filepath = sys.argv[1]
        is_valid, errors = validate_npc_file(npc_filepath)
        print_validation_report(npc_filepath, is_valid, errors)
        sys.exit(0 if is_valid else 1)
    else:
        # Validate all NPC files
        npcs_dir = get_npcs_dir()
        json_files = get_json_files_in_directory(
            npcs_dir, exclude_patterns=[".example"]
        )

        if not json_files:
            print(f"No NPC files found in {npcs_dir}")
            sys.exit(1)

        ALL_VALID = True

        for npc_filepath in sorted(json_files):
            is_valid, file_errors = validate_npc_file(str(npc_filepath))
            print_validation_report(str(npc_filepath), is_valid, file_errors)

            if not is_valid:
                ALL_VALID = False

        sys.exit(0 if ALL_VALID else 1)
