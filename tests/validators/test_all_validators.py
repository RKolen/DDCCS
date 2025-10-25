"""
Comprehensive test for all game data validators
Tests all validators together and verifies unified validation works correctly.
"""

import json
import os
import sys
import test_helpers

# Configure test environment (project paths)
test_helpers.setup_test_environment()

# Import validators from src.validation
try:
    from src.validation.character_validator import (
        validate_character_file,
        validate_character_json,
    )
    from src.validation.npc_validator import validate_npc_file, validate_npc_json
    from src.validation.items_validator import validate_items_file, validate_items_json
    from src.validation.party_validator import validate_party_file, validate_party_json
except ImportError as e:
    print(f"Error importing validators: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

try:
    from src.utils.path_utils import get_party_config_path
except ImportError:
    get_party_config_path = None


def test_all_characters():
    """Test that all character files are valid."""
    characters_dir = os.path.join("game_data", "characters")

    if not os.path.exists(characters_dir):
        print("[WARNING] Characters directory not found, skipping")
        return

    all_valid = True
    count = 0

    for filename in os.listdir(characters_dir):
        if filename.endswith(".json") and not filename.endswith(".example.json"):
            filepath = os.path.join(characters_dir, filename)
            is_valid, errors = validate_character_file(filepath)

            if not is_valid:
                print(f"[FAILED] {filename} validation failed:")
                for error in errors:
                    print(f"  - {error}")
                all_valid = False
            count += 1

    assert all_valid, "Some character files failed validation"
    print(f"[OK] All {count} character files validated successfully")


def test_all_npcs():
    """Test that all NPC files are valid."""
    npcs_dir = os.path.join("game_data", "npcs")

    if not os.path.exists(npcs_dir):
        print("[WARNING] NPCs directory not found, skipping")
        return

    all_valid = True
    count = 0

    for filename in os.listdir(npcs_dir):
        if filename.endswith(".json") and not filename.endswith(".example.json"):
            filepath = os.path.join(npcs_dir, filename)
            is_valid, errors = validate_npc_file(filepath)

            if not is_valid:
                print(f"[FAILED] {filename} validation failed:")
                for error in errors:
                    print(f"  - {error}")
                all_valid = False
            count += 1

    assert all_valid, "Some NPC files failed validation"
    print(f"[OK] All {count} NPC files validated successfully")


def test_items_registry():
    """Test that items registry is valid."""
    items_file = os.path.join("game_data", "items", "custom_items_registry.json")

    if not os.path.exists(items_file):
        print("[WARNING] Items registry not found, skipping")
        return

    is_valid, errors = validate_items_file(items_file)

    if not is_valid:
        print("[FAILED] Items registry validation failed:")
        for error in errors:
            print(f"  - {error}")

    assert is_valid, "Items registry failed validation"
    print("[OK] Items registry validated successfully")


def test_party_configuration():
    """Test that party configuration is valid."""
    if get_party_config_path:
        party_file = get_party_config_path()
    else:
        party_file = os.path.join("game_data", "current_party", "current_party.json")

    if not os.path.exists(party_file):
        print("[WARNING] Party configuration not found, skipping")
        return

    characters_dir = os.path.join("game_data", "characters")
    if not os.path.exists(characters_dir):
        characters_dir = None

    is_valid, errors = validate_party_file(party_file, characters_dir)

    if not is_valid:
        print("[FAILED] Party configuration validation failed:")
        for error in errors:
            print(f"  - {error}")

    assert is_valid, "Party configuration failed validation"
    print("[OK] Party configuration validated successfully")


def test_cross_validation():
    """Test that party members match actual character files."""
    if get_party_config_path:
        party_file = get_party_config_path()
    else:
        party_file = os.path.join("game_data", "current_party", "current_party.json")
    characters_dir = os.path.join("game_data", "characters")

    if not os.path.exists(party_file) or not os.path.exists(characters_dir):
        print("[WARNING] Party or characters directory not found, skipping cross-validation")
        return

    # Load party configuration
    with open(party_file, "r", encoding="utf-8") as f:
        party_data = json.load(f)

    party_members = party_data.get("party_members", [])

    # Load all character names
    character_names = []
    for filename in os.listdir(characters_dir):
        if filename.endswith(".json") and not filename.endswith(".example.json"):
            filepath = os.path.join(characters_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                char_data = json.load(f)
                if "name" in char_data:
                    character_names.append(char_data["name"])

    # Check if all party members exist as characters
    missing_members = []
    for member in party_members:
        if member not in character_names:
            missing_members.append(member)

    if missing_members:
        print(f"[WARNING] Party members not found in characters: {missing_members}")
        print(f"  Available characters: {character_names}")
    else:
        print(f"[OK] All {len(party_members)} party members match character files")


def test_validator_error_detection():
    """Test that validators correctly detect errors."""
    # Test character validator error detection
    invalid_char = {"name": "Test"}  # Missing required fields
    is_valid, errors = validate_character_json(invalid_char)
    assert not is_valid, "Character validator should detect missing fields"
    assert len(errors) > 0, "Character validator should return errors"

    # Test NPC validator error detection
    invalid_npc = {"name": "Test"}  # Missing required fields
    is_valid, errors = validate_npc_json(invalid_npc)
    assert not is_valid, "NPC validator should detect missing fields"
    assert len(errors) > 0, "NPC validator should return errors"

    # Test items validator error detection
    invalid_items = {}  # Empty registry
    is_valid, errors = validate_items_json(invalid_items)
    assert not is_valid, "Items validator should detect empty registry"
    assert len(errors) > 0, "Items validator should return errors"

    # Test party validator error detection
    invalid_party = {"party_members": []}  # Empty party
    is_valid, errors = validate_party_json(invalid_party)
    assert not is_valid, "Party validator should detect empty party"
    assert len(errors) > 0, "Party validator should return errors"

    print("[OK] All validators correctly detect errors")


def _load_json_files(directory):
    """Helper: Load all JSON files from directory into dict keyed by name."""
    data = {}
    if not os.path.exists(directory):
        return data

    for filename in os.listdir(directory):
        if filename.endswith(".json") and not filename.endswith(".example.json"):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                file_data = json.load(f)
                if "name" in file_data:
                    data[file_data["name"]] = file_data
    return data


def _check_party_members(party_data, characters):
    """Helper: Check that all party members have character files."""
    issues = []
    for member in party_data.get("party_members", []):
        if member not in characters:
            issues.append(f"Party member '{member}' has no character file")
    return issues


def _check_relationships(entities, all_known, entity_type):
    """Helper: Check that all relationships reference valid entities."""
    issues = []
    for entity_name, entity_data in entities.items():
        for related_name in entity_data.get("relationships", {}).keys():
            if related_name not in all_known:
                issues.append(
                    f"{entity_type} '{entity_name}' references "
                    f"unknown entity '{related_name}'"
                )
    return issues


def test_data_consistency():
    """Test consistency across all game data files."""
    # Check that all party members have character files
    if get_party_config_path:
        party_file = get_party_config_path()
    else:
        party_file = os.path.join("game_data", "current_party", "current_party.json")
    characters_dir = os.path.join("game_data", "characters")
    npcs_dir = os.path.join("game_data", "npcs")

    if not all(os.path.exists(p) for p in [party_file, characters_dir, npcs_dir]):
        print("[WARNING] Required directories not found, skipping consistency test")
        return

    # Load party
    with open(party_file, "r", encoding="utf-8") as f:
        party_data = json.load(f)

    # Load all characters and NPCs
    characters = _load_json_files(characters_dir)
    npcs = _load_json_files(npcs_dir)
    all_known = {**characters, **npcs}

    # Collect all consistency issues
    consistency_issues = []
    consistency_issues.extend(_check_party_members(party_data, characters))
    consistency_issues.extend(_check_relationships(characters, all_known, "Character"))
    consistency_issues.extend(_check_relationships(npcs, all_known, "NPC"))

    if consistency_issues:
        print("[WARNING] Data consistency issues found:")
        for issue in consistency_issues:
            print(f"  - {issue}")
    else:
        print("[OK] All game data is consistent")


if __name__ == "__main__":
    print("Running comprehensive game data validation tests...\n")

    try:
        test_all_characters()
        test_all_npcs()
        test_items_registry()
        test_party_configuration()
        test_cross_validation()
        test_validator_error_detection()
        test_data_consistency()

        print("\n[OK] All comprehensive validation tests passed!")
    except AssertionError as e:
        print(f"\n[FAILED] Test failed: {e}")
        sys.exit(1)
    except (ImportError, ValueError, KeyError, OSError, json.JSONDecodeError) as e:
        print(f"\n[FAILED] Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
