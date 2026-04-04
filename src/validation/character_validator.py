"""
Character Profile JSON Validation
Validates character JSON files against required schema.
"""

from typing import Dict, List, Any, Tuple
from src.utils.file_io import load_json_file, get_json_files_in_directory
from src.utils.path_utils import get_characters_dir
from src.utils.validation_helpers import get_type_name, print_validation_report
from src.characters.npc_constants import ABILITY_SCORE_NAMES
from src.characters.consultants.class_knowledge import get_all_class_names
from src.utils.errors import display_error, DnDFileNotFoundError
from src.utils.name_utils import validate_name_fields


def _validate_required_fields(
    data: Dict[str, Any], file_prefix: str
) -> List[str]:
    """Validate presence and types of required fields."""
    errors = []

    # Required fields that must be present. Note: background/backstory
    # historically used multiple keys. We validate presence of one of the
    # accepted background keys below instead of requiring multiple names.
    required_fields = {
        "name": str,
        "species": str,
        "dnd_class": str,
        "level": int,
        "ability_scores": dict,
        "equipment": dict,
        "known_spells": list,
        "relationships": dict,
    }

    # Optional fields with type validation if present
    optional_fields: dict[str, Any] = {
        "nickname": (str, type(None)),
        "pronouns": (str, type(None)),
        "model_profile": (str, type(None)),
    }

    # Validate required fields
    for field, expected_type in required_fields.items():
        if field not in data:
            errors.append(f"{file_prefix}Missing required field: '{field}'")
            continue
        if not isinstance(data[field], expected_type):
            errors.append(
                f"{file_prefix}Field '{field}' should be {expected_type.__name__}, "
                f"got {type(data[field]).__name__}"
            )

    # Background field compatibility: accept any of these keys
    background_keys = ("background", "backstory", "background_story")
    present_bg_key = next((k for k in background_keys if k in data), None)
    if not present_bg_key:
        errors.append(
            f"{file_prefix}Missing required background field: one of {background_keys}"
        )
    else:
        if not isinstance(data[present_bg_key], str):
            errors.append(
                f"{file_prefix}Background field '{present_bg_key}' should be str, "
                f"got {type(data[present_bg_key]).__name__}"
            )

    # Validate optional fields if present
    for field, expected_type in optional_fields.items():
        if field in data and not isinstance(data[field], expected_type):
            # Build type name string for error message
            type_name = get_type_name(expected_type)
            errors.append(
                f"{file_prefix}Field '{field}' should be {type_name}, "
                f"got {type(data[field]).__name__}"
            )

    return errors


def _validate_character_name(data: Dict[str, Any], file_prefix: str) -> List[str]:
    """Validate character name doesn't contain disallowed characters."""
    errors = []
    disallowed_chars = set("'\"`$%&|<>/\\")
    name = data.get("name", "")
    if any(c in name for c in disallowed_chars):
        errors.append(
            f"{file_prefix}Strange characters are not allowed in character name. "
            f"Please use another name (disallowed: {''.join(disallowed_chars)}). "
            f"Name: '{name}'"
        )
    return errors


def _validate_level_range(data: Dict[str, Any], file_prefix: str) -> List[str]:
    """Validate character level is within valid range."""
    errors = []
    if "level" in data:
        level = data["level"]
        if isinstance(level, int) and not 1 <= level <= 20:
            errors.append(
                f"{file_prefix}Level must be between 1 and 20, got {level}"
            )
    return errors


def _validate_equipment_structure(
    data: Dict[str, Any], file_prefix: str
) -> List[str]:
    """Validate equipment dictionary structure."""
    errors = []
    if "equipment" in data and isinstance(data["equipment"], dict):
        equipment = data["equipment"]
        required_equipment_fields = {"weapons": list, "armor": list, "items": list}

        for field, expected_type in required_equipment_fields.items():
            if field not in equipment:
                errors.append(
                    f"{file_prefix}Equipment missing required field: '{field}'"
                )
            elif not isinstance(equipment[field], expected_type):
                errors.append(
                    f"{file_prefix}Equipment field '{field}' should be "
                    f"{expected_type.__name__}, got {type(equipment[field]).__name__}"
                )
    return errors


def _validate_known_spells(data: Dict[str, Any], file_prefix: str) -> List[str]:
    """Validate known_spells list contains only strings."""
    errors = []
    if "known_spells" in data and isinstance(data["known_spells"], list):
        if not all(isinstance(item, str) for item in data["known_spells"]):
            errors.append(f"{file_prefix}All items in 'known_spells' must be strings")
    return errors


def _validate_ability_scores(data: Dict[str, Any], file_prefix: str) -> List[str]:
    """Validate ability_scores dictionary structure."""
    errors = []
    if "ability_scores" in data and isinstance(data["ability_scores"], dict):
        for ability in ABILITY_SCORE_NAMES:
            if ability not in data["ability_scores"]:
                errors.append(f"{file_prefix}Missing ability score: '{ability}'")
            elif not isinstance(data["ability_scores"][ability], int):
                errors.append(
                    f"{file_prefix}Ability score '{ability}' must be an integer"
                )
    return errors


def _validate_relationships(data: Dict[str, Any], file_prefix: str) -> List[str]:
    """Validate relationships dictionary structure.

    Accepts both legacy string values and structured relationship objects.
    """
    errors: List[str] = []
    if "relationships" not in data or not isinstance(data["relationships"], dict):
        return errors

    relationships = data["relationships"]
    for key, value in relationships.items():
        if not isinstance(key, str):
            errors.append(
                f"{file_prefix}All keys in 'relationships' must be strings"
            )
            break
        if isinstance(value, str):
            # Legacy format - valid
            continue
        if isinstance(value, dict):
            # Structured format - validate required sub-fields
            if "type" in value and not isinstance(value["type"], str):
                errors.append(
                    f"{file_prefix}Relationship '{key}': 'type' must be a string"
                )
            if "strength" in value:
                strength = value["strength"]
                if not isinstance(strength, int) or not 1 <= strength <= 10:
                    errors.append(
                        f"{file_prefix}Relationship '{key}': 'strength' must be an integer 1-10"
                    )
            if "status" in value and not isinstance(value["status"], str):
                errors.append(
                    f"{file_prefix}Relationship '{key}': 'status' must be a string"
                )
        else:
            errors.append(
                f"{file_prefix}Relationship '{key}': value must be a string or object"
            )
    return errors


def _validate_class_entry(
    class_entry: Any, entry_prefix: str, valid_classes: set
) -> tuple:
    """Validate a single class entry dict. Returns (errors, level_contribution)."""
    errors: List[str] = []
    level_contribution = 0

    if not isinstance(class_entry, dict):
        return [f"{entry_prefix}Must be an object"], 0

    name = class_entry.get("name")
    if not name:
        errors.append(f"{entry_prefix}Missing required field: 'name'")
    elif name not in valid_classes:
        errors.append(f"{entry_prefix}Unknown class: '{name}'")

    level = class_entry.get("level")
    if level is None:
        errors.append(f"{entry_prefix}Missing required field: 'level'")
    elif not isinstance(level, int):
        errors.append(f"{entry_prefix}Level must be an integer")
    elif not 1 <= level <= 20:
        errors.append(f"{entry_prefix}Level must be 1-20, got {level}")
    else:
        level_contribution = level

    subclass = class_entry.get("subclass")
    if subclass is not None and not isinstance(subclass, str):
        errors.append(f"{entry_prefix}Field 'subclass' must be a string or null")

    return errors, level_contribution


def _validate_classes_field(data: Dict[str, Any], file_prefix: str) -> List[str]:
    """Validate the optional classes array for multi-class characters."""
    errors: List[str] = []

    if "classes" not in data:
        return errors

    classes = data["classes"]
    if not isinstance(classes, list):
        errors.append(f"{file_prefix}Field 'classes' must be an array")
        return errors

    if not classes:
        errors.append(f"{file_prefix}Field 'classes' cannot be empty if present")
        return errors

    valid_classes = set(get_all_class_names())
    total_levels = 0

    for index, class_entry in enumerate(classes):
        entry_prefix = f"{file_prefix}classes[{index}]: "
        entry_errors, level_contribution = _validate_class_entry(
            class_entry, entry_prefix, valid_classes
        )
        errors.extend(entry_errors)
        total_levels += level_contribution

    if "level" in data and total_levels > 0 and isinstance(data["level"], int):
        if data["level"] != total_levels:
            errors.append(
                f"{file_prefix}Total class levels ({total_levels}) must equal "
                f"character level ({data['level']})"
            )

    return errors


def _validate_pronouns(data: Dict[str, Any], file_prefix: str) -> List[str]:
    """Validate pronouns field format if present."""
    errors: List[str] = []
    if "pronouns" not in data:
        return errors
    pronouns = data["pronouns"]
    if pronouns is None:
        return errors
    if not isinstance(pronouns, str):
        errors.append(
            f"{file_prefix}Field 'pronouns' must be a string or null, "
            f"got {type(pronouns).__name__}"
        )
    elif not pronouns.strip():
        errors.append(f"{file_prefix}Field 'pronouns' cannot be an empty string")
    return errors


def validate_character_json(
    data: Dict[str, Any], filepath: str = ""
) -> Tuple[bool, List[str]]:
    """
    Validate character JSON data against required schema.

    Args:
        data: Character JSON data to validate
        filepath: Optional file path for error reporting

    Returns:
        Tuple of (is_valid, error_messages)
    """
    file_prefix = f"{filepath}: " if filepath else ""

    # Run all validation checks
    errors = []
    errors.extend(_validate_required_fields(data, file_prefix))
    errors.extend(_validate_character_name(data, file_prefix))
    errors.extend(validate_name_fields(data, file_prefix))
    errors.extend(_validate_level_range(data, file_prefix))
    errors.extend(_validate_equipment_structure(data, file_prefix))
    errors.extend(_validate_known_spells(data, file_prefix))
    errors.extend(_validate_ability_scores(data, file_prefix))
    errors.extend(_validate_relationships(data, file_prefix))
    errors.extend(_validate_pronouns(data, file_prefix))
    errors.extend(_validate_classes_field(data, file_prefix))

    return len(errors) == 0, errors


def validate_character_file(filepath: str) -> Tuple[bool, List[str]]:
    """
    Validate a character JSON file.

    Args:
        filepath: Path to character JSON file

    Returns:
        Tuple of (is_valid, error_messages)
    """
    try:
        data = load_json_file(filepath)
        if data is None:
            return False, [f"{filepath}: File not found"]

        return validate_character_json(data, filepath)

    except ValueError as e:  # json.JSONDecodeError is a subclass of ValueError
        return False, [f"{filepath}: Invalid JSON - {str(e)}"]
    except (OSError, IOError, PermissionError) as e:
        return False, [f"{filepath}: Error reading file - {str(e)}"]


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Validate specific file
        file_path = sys.argv[1]
        valid, error_list = validate_character_file(file_path)
        print_validation_report(file_path, valid, error_list)
        sys.exit(0 if valid else 1)
    else:
        # Validate all character files
        characters_dir = get_characters_dir()
        json_files = get_json_files_in_directory(
            characters_dir,
            exclude_patterns=["class.example", ".example"]
        )

        if not json_files:
            error = DnDFileNotFoundError(
                filepath=str(characters_dir),
                file_type="characters directory"
            )
            display_error(error)
            sys.exit(1)

        all_valid: bool = True
        for char_path in json_files:
            valid, error_list = validate_character_file(str(char_path))
            print_validation_report(str(char_path), valid, error_list)

            if not valid:
                all_valid = False

        sys.exit(0 if all_valid else 1)
