"""
Test Party Configuration JSON validation
Verifies that party validator correctly identifies valid and invalid party config files.
"""

import os
import sys
from datetime import datetime
import test_helpers
# Import and configure test environment (UTF-8, project paths)
test_helpers.setup_test_environment()

# Import validators from src.validation
try:
    from src.validation.party_validator import validate_party_json, validate_party_file
except ImportError as e:
    print(f"Error importing party_validator: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

def test_valid_party():
    """Test that a valid party configuration passes validation."""
    valid_party = {
        "party_members": ["Hero One", "Hero Two", "Hero Three"],
        "last_updated": datetime.now().isoformat(),
    }

    is_valid, errors = validate_party_json(valid_party)
    assert is_valid, f"Valid party failed validation: {errors}"
    assert len(errors) == 0
    print("[OK] Valid party test passed")

def test_missing_required_field():
    """Test that missing required fields are detected."""
    invalid_party = {
        "party_members": ["Hero One"]
        # Missing: last_updated
    }

    is_valid, errors = validate_party_json(invalid_party)
    assert not is_valid, "Party with missing fields should fail validation"
    assert any("last_updated" in error for error in errors)
    print("[OK] Missing required field test passed")

def test_empty_party_members():
    """Test that empty party_members list is detected."""
    invalid_party = {
        "party_members": [],  # Empty list
        "last_updated": datetime.now().isoformat(),
    }

    is_valid, errors = validate_party_json(invalid_party)
    assert not is_valid, "Party with empty members should fail validation"
    assert any("empty" in error.lower() for error in errors)
    print("[OK] Empty party_members test passed")

def test_wrong_field_type():
    """Test that wrong field types are detected."""
    invalid_party = {
        "party_members": "not a list",  # Should be list
        "last_updated": 12345,  # Should be string
    }

    is_valid, errors = validate_party_json(invalid_party)
    assert not is_valid, "Party with wrong types should fail validation"
    assert any("party_members" in error and "list" in error for error in errors)
    assert any("last_updated" in error and "str" in error for error in errors)
    print("[OK] Wrong field type test passed")

def test_invalid_timestamp():
    """Test that invalid ISO timestamp is detected."""
    invalid_party = {
        "party_members": ["Hero One"],
        "last_updated": "not a valid timestamp",
    }

    is_valid, errors = validate_party_json(invalid_party)
    assert not is_valid, "Party with invalid timestamp should fail validation"
    assert any("ISO format" in error for error in errors)
    print("[OK] Invalid timestamp test passed")

def test_non_string_party_member():
    """Test that non-string party members are detected."""
    invalid_party = {
        "party_members": ["Valid Hero", 123, "Another Hero"],  # Should be string
        "last_updated": datetime.now().isoformat(),
    }

    is_valid, errors = validate_party_json(invalid_party)
    assert not is_valid, "Party with non-string member should fail validation"
    assert any("party_members[1]" in error and "string" in error for error in errors)
    print("[OK] Non-string party member test passed")

def test_empty_string_party_member():
    """Test that empty string party members are detected."""
    invalid_party = {
        "party_members": ["Valid Hero", "", "Another Hero"],  # Empty string
        "last_updated": datetime.now().isoformat(),
    }

    is_valid, errors = validate_party_json(invalid_party)
    assert not is_valid, "Party with empty string member should fail validation"
    assert any("party_members[1]" in error and "empty" in error for error in errors)
    print("[OK] Empty string party member test passed")

def test_duplicate_party_members():
    """Test that duplicate party members are detected."""
    invalid_party = {
        "party_members": ["Hero One", "Hero Two", "Hero One"],  # Duplicate
        "last_updated": datetime.now().isoformat(),
    }

    is_valid, errors = validate_party_json(invalid_party)
    assert not is_valid, "Party with duplicate members should fail validation"
    assert any("duplicate" in error.lower() for error in errors)
    print("[OK] Duplicate party members test passed")

def test_validate_actual_party_file():
    """Test validation of actual party file in the game_data directory."""
    party_file = os.path.join("game_data", "current_party", "current_party.json")

    if not os.path.exists(party_file):
        print("[WARNING] Party configuration file not found, skipping actual file test")
        return

    # Get characters directory for cross-reference
    characters_dir = os.path.join("game_data", "characters")
    if not os.path.exists(characters_dir):
        characters_dir = None

    is_valid, errors = validate_party_file(party_file, characters_dir)

    if not is_valid:
        print("[FAILED] Party configuration validation failed:")
        for error in errors:
            print(f"  - {error}")

    assert is_valid, "Party configuration file failed validation"
    print("[OK] Actual party configuration file validated successfully")

def test_cross_reference_with_characters():
    """Test that party members are cross-referenced with character files."""
    party_data = {
        "party_members": ["Nonexistent Character"],  # This character doesn't exist
        "last_updated": datetime.now().isoformat(),
    }

    characters_dir = os.path.join("game_data", "characters")

    if not os.path.exists(characters_dir):
        print("[WARNING] Characters directory not found, skipping cross-reference test")
        return

    is_valid, errors = validate_party_json(party_data, characters_dir=characters_dir)

    # This test is informational - it should warn but the current implementation
    # adds errors for characters not found
    if not is_valid:
        assert any("does not match any character file" in error for error in errors)
        print(
            "[OK] Cross-reference with characters test passed (detected missing character)"
        )
    else:
        print(
            "[WARNING] Cross-reference test: No character files found or validation too permissive"
        )

def test_valid_iso_timestamp_formats():
    """Test that various valid ISO timestamp formats are accepted."""
    valid_timestamps = [
        "2025-09-28T11:30:52.239016",
        "2025-09-28T11:30:52",
        "2025-09-28T00:00:00.000000",
        datetime.now().isoformat(),
    ]

    for timestamp in valid_timestamps:
        party_data = {"party_members": ["Hero One"], "last_updated": timestamp}

        is_valid, errors = validate_party_json(party_data)
        assert is_valid, f"Valid timestamp '{timestamp}' failed validation: {errors}"

    print("[OK] Valid ISO timestamp formats test passed")

if __name__ == "__main__":
    print("Running party validator tests...\n")

    try:
        test_valid_party()
        test_missing_required_field()
        test_empty_party_members()
        test_wrong_field_type()
        test_invalid_timestamp()
        test_non_string_party_member()
        test_empty_string_party_member()
        test_duplicate_party_members()
        test_valid_iso_timestamp_formats()
        test_validate_actual_party_file()
        test_cross_reference_with_characters()

        print("\n[OK] All party validator tests passed!")
    except AssertionError as e:
        print(f"\n[FAILED] Test failed: {e}")
        sys.exit(1)
    except (ImportError, ValueError, KeyError) as e:
        print(f"\n[FAILED] Unexpected error: {e}")
        sys.exit(1)
