"""
Test character JSON validation
Verifies that character validator correctly identifies valid and invalid character files.
"""

import os
from tests import test_helpers

# Import validators via centralized helper
validate_character_json, validate_character_file = test_helpers.safe_from_import(
    "src.validation.character_validator",
    "validate_character_json",
    "validate_character_file",
)


def test_valid_character():
    """Test that a valid character passes validation."""
    valid_character = {
        "name": "Test Character",
        "species": "Human",
        "dnd_class": "fighter",
        "level": 5,
        "ability_scores": {
            "strength": 16,
            "dexterity": 14,
            "constitution": 15,
            "intelligence": 10,
            "wisdom": 12,
            "charisma": 8,
        },
        "equipment": {
            "weapons": ["Longsword", "Shield"],
            "armor": ["Plate Armor"],
            "items": ["Backpack", "Rope"],
        },
        "known_spells": [],
        "background": "Soldier",
        "backstory": "A veteran warrior seeking redemption.",
        "relationships": {},
    }

    is_valid, errors = validate_character_json(valid_character)
    assert is_valid, f"Valid character failed validation: {errors}"
    assert len(errors) == 0
    print("[OK] Valid character test passed")


def test_missing_required_field():
    """Test that missing required fields are detected."""
    invalid_character = {
        "name": "Test Character",
        "species": "Human",
        # Missing dnd_class
        "level": 5,
        "ability_scores": {
            "strength": 16,
            "dexterity": 14,
            "constitution": 15,
            "intelligence": 10,
            "wisdom": 12,
            "charisma": 8,
        },
    }

    is_valid, errors = validate_character_json(invalid_character)
    assert not is_valid, "Invalid character passed validation"
    assert any("dnd_class" in error for error in errors)
    print("[OK] Missing required field test passed")


def test_invalid_level_range():
    """Test that invalid level values are detected."""
    invalid_character = {
        "name": "Test Character",
        "species": "Human",
        "dnd_class": "wizard",
        "level": 25,  # Invalid: > 20
        "ability_scores": {
            "strength": 10,
            "dexterity": 10,
            "constitution": 10,
            "intelligence": 10,
            "wisdom": 10,
            "charisma": 10,
        },
        "equipment": {"weapons": [], "armor": [], "items": []},
        "known_spells": [],
        "background": "Scholar",
        "backstory": "A wizard.",
        "relationships": {},
    }

    is_valid, errors = validate_character_json(invalid_character)
    assert not is_valid, "Invalid level passed validation"
    assert any("Level must be between 1 and 20" in error for error in errors)
    print("[OK] Invalid level range test passed")


def test_wrong_field_type():
    """Test that incorrect field types are detected."""
    invalid_character = {
        "name": "Test Character",
        "species": "Human",
        "dnd_class": "rogue",
        "level": "5",  # Should be int, not str
        "ability_scores": {
            "strength": 10,
            "dexterity": 18,
            "constitution": 12,
            "intelligence": 14,
            "wisdom": 10,
            "charisma": 10,
        },
        "equipment": {"weapons": ["Dagger"], "armor": [], "items": []},
        "known_spells": [],
        "background": "Criminal",
        "backstory": "A rogue.",
        "relationships": {},
    }

    is_valid, errors = validate_character_json(invalid_character)
    assert not is_valid, "Wrong field type passed validation"
    assert any("level" in error and "int" in error for error in errors)
    print("[OK] Wrong field type test passed")


def test_validate_actual_character_files():
    """Test validation against actual character files in game_data/characters/."""
    characters_path = "game_data/characters"

    if not os.path.exists(characters_path):
        print("[WARNING] Skipping actual file test: game_data/characters/ not found")
        return

    all_valid = True
    file_count = 0

    for filename in os.listdir(characters_path):
        if (
            filename.endswith(".json")
            and not filename.startswith("class.example")
            and not filename.endswith(".example.json")
        ):

            filepath = os.path.join(characters_path, filename)
            is_valid, errors = validate_character_file(filepath)
            file_count += 1

            if not is_valid:
                print(f"[FAILED] {filename} failed validation:")
                for error in errors:
                    print(f"  - {error}")
                all_valid = False

    assert all_valid, "Some character files failed validation"
    print(f"[OK] All {file_count} actual character files validated successfully")


if __name__ == "__main__":
    print("Running character validator tests...\n")

    test_valid_character()
    test_missing_required_field()
    test_invalid_level_range()
    test_wrong_field_type()
    test_validate_actual_character_files()

    print("\n[OK] All validator tests passed!")
