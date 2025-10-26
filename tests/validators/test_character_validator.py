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
    valid_character = test_helpers.sample_character_data(
        name="Test Character",
        dnd_class="fighter",
        level=5,
        overrides={"backstory": "A veteran warrior seeking redemption."},
    )

    is_valid, errors = validate_character_json(valid_character)
    assert is_valid, f"Valid character failed validation: {errors}"
    assert len(errors) == 0
    print("[OK] Valid character test passed")


def test_missing_required_field():
    """Test that missing required fields are detected."""
    invalid_character = test_helpers.sample_character_data(
        name="Test Character",
        dnd_class="fighter",
        level=5,
    )
    # remove required field to simulate invalid file
    invalid_character.pop("dnd_class", None)

    is_valid, errors = validate_character_json(invalid_character)
    assert not is_valid, "Invalid character passed validation"
    assert any("dnd_class" in error for error in errors)
    print("[OK] Missing required field test passed")


def test_invalid_level_range():
    """Test that invalid level values are detected."""
    invalid_character = test_helpers.sample_character_data(
        name="Test Character",
        dnd_class="wizard",
        level=25,  # Invalid: > 20
    )

    is_valid, errors = validate_character_json(invalid_character)
    assert not is_valid, "Invalid level passed validation"
    assert any("Level must be between 1 and 20" in error for error in errors)
    print("[OK] Invalid level range test passed")


def test_wrong_field_type():
    """Test that incorrect field types are detected."""
    invalid_character = test_helpers.sample_character_data(
        name="Test Character",
        dnd_class="rogue",
        level="5",  # Should be int, not str
    )

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
    test_list = [
        test_valid_character,
        test_missing_required_field,
        test_invalid_level_range,
        test_wrong_field_type,
        test_validate_actual_character_files,
    ]
    test_helpers.run_tests_safely(test_list, success_message="[OK] All validator tests passed!")
