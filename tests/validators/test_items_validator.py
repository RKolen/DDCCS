"""
Test Items Registry JSON validation
Verifies that items validator correctly identifies valid and invalid item registry files.
"""

import os
from tests import test_helpers

# Import validators from src.validation using the centralized safe importer
validate_items_json, validate_items_file, validate_item_entry = test_helpers.safe_from_import(
    "src.validation.items_validator",
    "validate_items_json",
    "validate_items_file",
    "validate_item_entry",
)


def test_valid_item_entry():
    """Test that a valid item entry passes validation."""
    valid_item = {
        "name": "Test Sword",
        "item_type": "weapon",
        "is_magic": False,
        "description": "A well-crafted sword",
        "properties": {"damage": "1d8 slashing", "weight": "3 lbs"},
        "notes": "Found in the armory",
    }

    errors = validate_item_entry("Test Sword", valid_item)
    assert len(errors) == 0, f"Valid item failed validation: {errors}"
    print("[OK] Valid item entry test passed")


def test_valid_items_registry():
    """Test that a valid items registry passes validation."""
    valid_registry = {
        "_comment": "This is metadata",
        "Magic Amulet": {
            "name": "Magic Amulet",
            "item_type": "magic_item",
            "is_magic": True,
            "description": "A glowing amulet",
            "properties": {"rarity": "rare", "attunement": True},
            "notes": "Provides protection",
        },
        "Steel Sword": {
            "name": "Steel Sword",
            "item_type": "weapon",
            "is_magic": False,
            "description": "A standard sword",
            "properties": {"damage": "1d8"},
            "notes": "Basic weapon",
        },
    }

    is_valid, errors = validate_items_json(valid_registry)
    assert is_valid, f"Valid registry failed validation: {errors}"
    assert len(errors) == 0
    print("[OK] Valid items registry test passed")


def test_missing_required_field():
    """Test that missing required fields are detected."""
    invalid_registry = {
        "Test Item": {
            "name": "Test Item",
            "item_type": "weapon",
            # Missing: is_magic, description, properties, notes
        }
    }

    is_valid, errors = validate_items_json(invalid_registry)
    assert not is_valid, "Registry with missing fields should fail validation"
    assert any("is_magic" in error for error in errors)
    assert any("description" in error for error in errors)
    print("[OK] Missing required field test passed")


def test_invalid_item_type():
    """Test that invalid item_type values are detected."""
    invalid_registry = {
        "Test Item": {
            "name": "Test Item",
            "item_type": "invalid_type",  # Not in valid_types list
            "is_magic": False,
            "description": "Test",
            "properties": {},
            "notes": "",
        }
    }

    is_valid, errors = validate_items_json(invalid_registry)
    assert not is_valid, "Registry with invalid item_type should fail validation"
    assert any("item_type must be one of" in error for error in errors)
    print("[OK] Invalid item_type test passed")


def test_wrong_field_type():
    """Test that wrong field types are detected."""
    invalid_registry = {
        "Test Item": {
            "name": "Test Item",
            "item_type": "weapon",
            "is_magic": "not a bool",  # Should be bool
            "description": "Test",
            "properties": "not a dict",  # Should be dict
            "notes": 123,  # Should be string
        }
    }

    is_valid, errors = validate_items_json(invalid_registry)
    assert not is_valid, "Registry with wrong types should fail validation"
    assert any("is_magic" in error and "bool" in error for error in errors)
    assert any("properties" in error and "dict" in error for error in errors)
    print("[OK] Wrong field type test passed")


def test_invalid_property_values():
    """Test that invalid property values are detected."""
    invalid_registry = {
        "Test Item": {
            "name": "Test Item",
            "item_type": "weapon",
            "is_magic": False,
            "description": "Test",
            "properties": {
                "valid": "string",
                "invalid": ["array not allowed"],  # Should be string, number, or bool
            },
            "notes": "",
        }
    }

    is_valid, errors = validate_items_json(invalid_registry)
    assert not is_valid, "Registry with invalid property values should fail"
    assert any("Property 'invalid'" in error for error in errors)
    print("[OK] Invalid property values test passed")


def test_empty_registry():
    """Test that empty registry (only metadata) is detected."""
    empty_registry = {"_comment": "Only metadata", "_instructions": "No actual items"}

    is_valid, errors = validate_items_json(empty_registry)
    assert not is_valid, "Empty registry should fail validation"
    assert any("no item entries" in error for error in errors)
    print("[OK] Empty registry test passed")


def test_validate_actual_items_file():
    """Test validation of actual items registry file in the game_data directory."""
    items_file = os.path.join("game_data", "items", "custom_items_registry.json")

    if not os.path.exists(items_file):
        print("[WARNING] Items registry file not found, skipping actual file test")
        return

    is_valid, errors = validate_items_file(items_file)

    if not is_valid:
        print("[FAILED] Items registry validation failed:")
        for error in errors:
            print(f"  - {error}")

    assert is_valid, "Items registry file failed validation"
    print("[OK] Actual items registry file validated successfully")


def test_non_dict_item_entry():
    """Test that non-dict item entries are detected."""
    invalid_registry = {
        "Valid Item": {
            "name": "Valid Item",
            "item_type": "weapon",
            "is_magic": False,
            "description": "Test",
            "properties": {},
            "notes": "",
        },
        "Invalid Item": "not a dict",  # Should be a dict
    }

    is_valid, errors = validate_items_json(invalid_registry)
    assert not is_valid, "Registry with non-dict entry should fail"
    assert any("Invalid Item" in error and "dictionary" in error for error in errors)
    print("[OK] Non-dict item entry test passed")


if __name__ == "__main__":
    print("Running items validator tests...\n")
    test_list = [
        test_valid_item_entry,
        test_valid_items_registry,
        test_missing_required_field,
        test_invalid_item_type,
        test_wrong_field_type,
        test_invalid_property_values,
        test_empty_registry,
        test_non_dict_item_entry,
        test_validate_actual_items_file,
    ]
    test_helpers.run_tests_safely(test_list, success_message=
    "[OK] All items validator tests passed!")
