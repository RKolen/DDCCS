"""
Character Profile JSON Validation
Validates character JSON files against required schema.
"""

from typing import Dict, List, Any, Tuple
from src.utils.file_io import load_json_file, get_json_files_in_directory
from src.utils.path_utils import get_characters_dir


class CharacterValidationError(Exception):
    """Raised when character JSON validation fails."""


def validate_character_json(  # pylint: disable=too-many-locals,too-many-branches
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
    errors = []
    file_prefix = f"{filepath}: " if filepath else ""

    # Required fields with their expected types (matching actual character file structure)
    required_fields = {
        "name": str,
        "nickname": (str, type(None)),
        "species": str,
        "dnd_class": str,
        "level": int,
        "ability_scores": dict,
        "equipment": dict,
        "known_spells": list,
        "background": str,
        "backstory": str,
        "relationships": dict,
    }

    # Check for missing required fields
    for field, expected_type in required_fields.items():
        if field not in data:
            errors.append(f"{file_prefix}Missing required field: '{field}'")
            continue
        # Check field type
        if not isinstance(data[field], expected_type):
            errors.append(
                f"{file_prefix}Field '{field}' should be {expected_type.__name__}, "
                f"got {type(data[field]).__name__}"
            )

    # Disallowed characters in name
    disallowed_chars = set("'\"`$%&|<>/\\")
    name = data.get("name", "")
    if any(c in name for c in disallowed_chars):
        errors.append(
            f"{file_prefix}Strange characters are not allowed in character name. "
            f"Please use another name (disallowed: {''.join(disallowed_chars)}). "
            f"Name: '{name}'"
        )

    # Validate level range
    if "level" in data:
        level = data["level"]
        if isinstance(level, int):
            if level < 1 or level > 20:
                errors.append(
                    f"{file_prefix}Level must be between 1 and 20, got {level}"
                )

    # Validate equipment structure (actual structure has weapons, armor, items, gold)
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
                    f"{file_prefix}Equipment field '{field}' should be {expected_type.__name__}, "
                    f"got {type(equipment[field]).__name__}"
                )

    # Validate array contents
    if "known_spells" in data and isinstance(data["known_spells"], list):
        if not all(isinstance(item, str) for item in data["known_spells"]):
            errors.append(f"{file_prefix}All items in 'known_spells' must be strings")

    # Validate ability_scores structure
    if "ability_scores" in data and isinstance(data["ability_scores"], dict):
        required_abilities = [
            "strength",
            "dexterity",
            "constitution",
            "intelligence",
            "wisdom",
            "charisma",
        ]
        for ability in required_abilities:
            if ability not in data["ability_scores"]:
                errors.append(f"{file_prefix}Missing ability score: '{ability}'")
            elif not isinstance(data["ability_scores"][ability], int):
                errors.append(
                    f"{file_prefix}Ability score '{ability}' must be an integer"
                )

    # Validate relationships structure
    if "relationships" in data and isinstance(data["relationships"], dict):
        relationships = data["relationships"]
        if not all(
            isinstance(k, str) and isinstance(v, str) for k, v in relationships.items()
        ):
            errors.append(
                f"{file_prefix}All keys and values in 'relationships' must be strings"
            )

    is_valid = len(errors) == 0
    return is_valid, errors


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


def print_validation_report(filepath: str, is_valid: bool, errors: List[str]) -> None:
    """Print a formatted validation report."""
    if is_valid:
        print(f"✓ {filepath}: Valid")
    else:
        print(f"✗ {filepath}: INVALID")
        for error in errors:
            print(f"  - {error}")


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
            print(f"Error: No character files found in {characters_dir}")
            sys.exit(1)

        ALL_VALID = True
        for file_path in json_files:
            valid, error_list = validate_character_file(str(file_path))
            print_validation_report(str(file_path), valid, error_list)

            if not valid:
                ALL_VALID = False

        sys.exit(0 if ALL_VALID else 1)
