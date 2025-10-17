"""
Items Registry JSON Validation Module

Validates custom items registry JSON files to ensure they contain proper structure
and data types according to the D&D Campaign System schema.

Usage:
    # Standalone validation
    python -m src.validation.items_validator [filepath]

    # Programmatic validation
    from src.validation.items_validator import validate_items_json, validate_items_file
    is_valid, errors = validate_items_file("game_data/items/custom_items_registry.json")
"""

from typing import Dict, Any, List, Tuple
from src.utils.file_io import load_json_file
from src.utils.path_utils import get_items_registry_path


class ItemsValidationError(Exception):
    """Custom exception for items validation errors."""


def validate_item_entry(item_key: str, item_data: Dict[str, Any]) -> List[str]:
    """
    Validate a single item entry in the registry.

    Args:
        item_key: The key for this item in the registry
        item_data: Dictionary containing item data

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    # Define required fields and their expected types
    required_fields = {
        "name": str,
        "item_type": str,
        "is_magic": bool,
        "description": str,
        "properties": dict,
        "notes": str,
    }

    # Check for required fields and types
    for field, expected_type in required_fields.items():
        if field not in item_data:
            errors.append(f"Item '{item_key}': Missing required field: {field}")
        elif not isinstance(item_data[field], expected_type):
            errors.append(
                f"Item '{item_key}': Field '{field}' must be of type {expected_type.__name__}, "
                f"got {type(item_data[field]).__name__}"
            )

    # Validate item_type is one of the expected values
    if "item_type" in item_data:
        valid_types = [
            "magic_item",
            "weapon",
            "armor",
            "gear",
            "tool",
            "consumable",
            "treasure",
        ]
        if item_data["item_type"] not in valid_types:
            errors.append(
                f"Item '{item_key}': item_type must be one of {valid_types}, "
                f"got '{item_data['item_type']}'"
            )

    # Validate properties is a dict
    if "properties" in item_data and isinstance(item_data["properties"], dict):
        # All property values should be strings, numbers, or booleans
        for prop_key, prop_value in item_data["properties"].items():
            if not isinstance(prop_value, (str, int, float, bool)):
                errors.append(
                    f"Item '{item_key}': Property '{prop_key}' must be a string, number, or boolean"
                )

    return errors


def validate_items_json(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate an items registry dictionary against the required schema.

    Args:
        data: Dictionary containing items registry data

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # The root should be a dictionary
    if not isinstance(data, dict):
        errors.append("Items registry must be a dictionary/object")
        return (False, errors)

    # Filter out metadata fields (starting with underscore)
    item_entries = {k: v for k, v in data.items() if not k.startswith("_")}

    if len(item_entries) == 0:
        errors.append("Items registry contains no item entries (only metadata)")
        return (False, errors)

    # Validate each item entry
    for item_key, item_data in item_entries.items():
        if not isinstance(item_data, dict):
            errors.append(f"Item '{item_key}': Must be a dictionary/object")
            continue

        item_errors = validate_item_entry(item_key, item_data)
        errors.extend(item_errors)
        # Disallowed characters in item name
        disallowed_chars = set("'\"`$%&|<>/\\")
        name = item_data.get("name", "")
        if any(c in name for c in disallowed_chars):
            errors.append(
                f"Item '{item_key}': Strange characters are not allowed in item name. "
                f"Please use another name (disallowed: {''.join(disallowed_chars)})."
                f" Name: '{name}'"
            )

    return (len(errors) == 0, errors)


def validate_items_file(filepath: str) -> Tuple[bool, List[str]]:
    """
    Validate an items registry JSON file.

    Args:
        filepath: Path to the items registry JSON file

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    # Try to load and parse JSON
    try:
        data = load_json_file(filepath)
        if data is None:
            return (False, [f"File not found: {filepath}"])

        # Validate the data
        return validate_items_json(data)

    except ValueError as e:  # json.JSONDecodeError is a subclass of ValueError
        return (False, [f"Invalid JSON format: {e}"])
    except OSError as e:
        return (False, [f"Error reading file: {e}"])


def print_validation_report(filepath: str, valid_result: bool, errors: List[str]):
    """Print a formatted validation report."""
    if valid_result:
        print(f"✓ {filepath}: Valid")
    else:
        print(f"✗ {filepath}: INVALID")
        for error in errors:
            print(f"  - {error}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Validate specific file
        input_filepath = sys.argv[1]
        is_valid, validation_errors = validate_items_file(input_filepath)
        print_validation_report(input_filepath, is_valid, validation_errors)
        sys.exit(0 if is_valid else 1)
    else:
        # Validate items registry file
        items_file = get_items_registry_path()

        is_valid, validation_errors = validate_items_file(items_file)
        print_validation_report(items_file, is_valid, validation_errors)

        sys.exit(0 if is_valid else 1)
