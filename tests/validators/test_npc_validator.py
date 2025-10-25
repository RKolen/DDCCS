"""
Test NPC JSON validation
Verifies that NPC validator correctly identifies valid and invalid NPC files.
"""

import os
import sys
import test_helpers
# Import and configure test environment (UTF-8, project paths)
test_helpers.setup_test_environment()

# Import validators from src.validation
try:
    from src.validation.npc_validator import validate_npc_json, validate_npc_file
except ImportError as e:
    print(f"Error importing npc_validator: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


def test_valid_npc():
    """Test that a valid NPC passes validation."""
    valid_npc = {
        "name": "Test NPC",
        "role": "Merchant",
        "species": "Human",
        "lineage": "",
        "personality": "Friendly and helpful",
        "relationships": {"Hero": "Respects their courage"},
        "key_traits": ["Honest", "Resourceful"],
        "abilities": ["Bargain", "Appraise"],
        "recurring": True,
        "notes": "Important merchant in the story",
        "ai_config": {"enabled": False, "temperature": 0.7, "max_tokens": 1000},
    }

    is_valid, errors = validate_npc_json(valid_npc)
    assert is_valid, f"Valid NPC failed validation: {errors}"
    assert len(errors) == 0
    print("[OK] Valid NPC test passed")


def test_missing_required_field():
    """Test that missing required fields are detected."""
    invalid_npc = {
        "name": "Test NPC",
        "species": "Human",
        # Missing: role, lineage, personality, relationships, key_traits,
        # abilities, recurring, notes, ai_config
    }

    is_valid, errors = validate_npc_json(invalid_npc)
    assert not is_valid, "NPC with missing fields should fail validation"
    assert any("role" in error for error in errors), "Should detect missing role field"
    print("[OK] Missing required field test passed")


def test_wrong_field_type():
    """Test that wrong field types are detected."""
    invalid_npc = {
        "name": "Test NPC",
        "role": "Merchant",
        "species": "Human",
        "lineage": "",
        "personality": "Friendly",
        "relationships": "Not a dict",  # Should be dict
        "key_traits": "Not a list",  # Should be list
        "abilities": [],
        "recurring": True,
        "notes": "",
        "ai_config": {},
    }

    is_valid, errors = validate_npc_json(invalid_npc)
    assert not is_valid, "NPC with wrong types should fail validation"
    assert any("relationships" in error and "dict" in error for error in errors)
    assert any("key_traits" in error and "list" in error for error in errors)
    print("[OK] Wrong field type test passed")


def test_invalid_ai_config():
    """Test that invalid ai_config structure is detected."""
    invalid_npc = {
        "name": "Test NPC",
        "role": "Merchant",
        "species": "Human",
        "lineage": "",
        "personality": "Friendly",
        "relationships": {},
        "key_traits": [],
        "abilities": [],
        "recurring": True,
        "notes": "",
        "ai_config": {
            "enabled": "not a bool",  # Should be bool
            "temperature": "not a number",  # Should be number
            "max_tokens": "not an int",  # Should be int
        },
    }

    is_valid, errors = validate_npc_json(invalid_npc)
    assert not is_valid, "NPC with invalid ai_config should fail validation"
    assert any("enabled" in error and "boolean" in error for error in errors)
    print("[OK] Invalid ai_config test passed")


def test_validate_actual_npc_files():
    """Test validation of actual NPC files in the game_data directory."""
    npcs_dir = os.path.join("game_data", "npcs")

    if not os.path.exists(npcs_dir):
        print("[WARNING] NPCs directory not found, skipping actual file test")
        return

    all_valid = True
    validated_count = 0

    for filename in os.listdir(npcs_dir):
        if filename.endswith(".json") and not filename.endswith(".example.json"):
            filepath = os.path.join(npcs_dir, filename)
            is_valid, errors = validate_npc_file(filepath)

            if not is_valid:
                print(f"[FAILED] {filename} validation failed:")
                for error in errors:
                    print(f"  - {error}")
                all_valid = False
            validated_count += 1

    assert all_valid, "Some NPC files failed validation"
    print(f"[OK] All {validated_count} actual NPC files validated successfully")


def test_npc_relationships_validation():
    """Test that relationships are properly validated."""
    invalid_npc = {
        "name": "Test NPC",
        "role": "Merchant",
        "species": "Human",
        "lineage": "",
        "personality": "Friendly",
        "relationships": {"Hero": 123},  # Should be string
        "key_traits": [],
        "abilities": [],
        "recurring": True,
        "notes": "",
        "ai_config": {"enabled": False},
    }

    is_valid, errors = validate_npc_json(invalid_npc)
    assert not is_valid, "NPC with invalid relationship value should fail"
    assert any("Hero" in error and "string" in error for error in errors)
    print("[OK] NPC relationships validation test passed")


def test_npc_trait_validation():
    """Test that key_traits and abilities contain only strings."""
    invalid_npc = {
        "name": "Test NPC",
        "role": "Merchant",
        "species": "Human",
        "lineage": "",
        "personality": "Friendly",
        "relationships": {},
        "key_traits": ["Valid", 123],  # Should be all strings
        "abilities": ["Valid", True],  # Should be all strings
        "recurring": True,
        "notes": "",
        "ai_config": {"enabled": False},
    }

    is_valid, errors = validate_npc_json(invalid_npc)
    assert not is_valid, "NPC with non-string traits/abilities should fail"
    assert any("key_traits" in error for error in errors)
    assert any("abilities" in error for error in errors)
    print("[OK] NPC trait validation test passed")


if __name__ == "__main__":
    print("Running NPC validator tests...\n")

    try:
        test_valid_npc()
        test_missing_required_field()
        test_wrong_field_type()
        test_invalid_ai_config()
        test_npc_relationships_validation()
        test_npc_trait_validation()
        test_validate_actual_npc_files()

        print("\n[OK] All NPC validator tests passed!")
    except AssertionError as e:
        print(f"\n[FAILED] Test failed: {e}")
        sys.exit(1)
    except (ImportError, ValueError, KeyError, OSError) as e:
        print(f"\n[FAILED] Unexpected error: {e}")
        sys.exit(1)
