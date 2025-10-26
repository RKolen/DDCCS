"""
Tests for story_character_loader.py - Character loading for story management.

Tests character profile loading, validation integration, consultant creation,
and character retrieval operations.
"""

import os
import json
import tempfile

from tests import test_helpers

# Use canonical test helper to configure environment and import modules under test.
CharacterLoader = test_helpers.safe_from_import(
    "src.stories.story_character_loader", "CharacterLoader"
)
CharacterProfile = test_helpers.safe_from_import(
    "src.characters.consultants.character_profile", "CharacterProfile"
)
DnDClass = test_helpers.safe_from_import(
    "src.characters.character_sheet", "DnDClass"
)

def create_test_character_file(workspace_path: str, character_name: str):
    """Create a valid test character JSON file."""
    # Delegate to shared helper to reduce duplicated fixture literals
    return test_helpers.write_character_file(workspace_path, character_name)


def test_character_loader_initialization():
    """Test CharacterLoader initialization."""
    print("\n[TEST] CharacterLoader Initialization")

    with tempfile.TemporaryDirectory() as temp_dir:
        loader = CharacterLoader(temp_dir)

        # Check initialization
        assert loader.workspace_path == temp_dir
        assert loader.characters_path == os.path.join(
            temp_dir, "game_data", "characters"
        )
        assert not loader.consultants
        assert os.path.exists(loader.characters_path)

        print("  [OK] CharacterLoader initialized correctly")

    print("[PASS] CharacterLoader Initialization")


def test_load_characters():
    """Test loading multiple character profiles."""
    print("\n[TEST] Load Characters")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test characters
        create_test_character_file(temp_dir, "Aragorn")
        create_test_character_file(temp_dir, "Legolas")
        create_test_character_file(temp_dir, "Gimli")

        loader = CharacterLoader(temp_dir)
        loader.load_characters()

        # Check characters loaded
        assert len(loader.consultants) == 3
        assert "Aragorn" in loader.consultants
        assert "Legolas" in loader.consultants
        assert "Gimli" in loader.consultants

        print("  [OK] All characters loaded successfully")

    print("[PASS] Load Characters")


def test_skip_example_files():
    """Test that example and template files are skipped."""
    print("\n[TEST] Skip Example Files")

    with tempfile.TemporaryDirectory() as temp_dir:
        characters_dir = os.path.join(temp_dir, "game_data", "characters")
        os.makedirs(characters_dir, exist_ok=True)

        # Create example files (should be skipped)
        example_files = [
            "class.example.json",
            "fighter.example.json",
            "template_character.json"
        ]

        for filename in example_files:
            filepath = os.path.join(characters_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as file:
                json.dump({"name": "Example"}, file)

        # Create real character
        create_test_character_file(temp_dir, "Aragorn")

        loader = CharacterLoader(temp_dir)
        loader.load_characters()

        # Only real character should be loaded
        assert len(loader.consultants) == 1
        assert "Aragorn" in loader.consultants

        print("  [OK] Example files skipped correctly")

    print("[PASS] Skip Example Files")


def test_validation_integration():
    """Test validation integration with character loading."""
    print("\n[TEST] Validation Integration")

    with tempfile.TemporaryDirectory() as temp_dir:
        characters_dir = os.path.join(temp_dir, "game_data", "characters")
        os.makedirs(characters_dir, exist_ok=True)

        # Create invalid character file (missing required fields)
        invalid_data = {
            "name": "InvalidChar",
            "dnd_class": "fighter"
            # Missing many required fields
        }

        filepath = os.path.join(characters_dir, "invalid.json")
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(invalid_data, file)

        # Create valid character
        create_test_character_file(temp_dir, "ValidChar")

        loader = CharacterLoader(temp_dir)
        loader.load_characters()

        # Only valid character should be loaded
        assert len(loader.consultants) == 1
        assert "ValidChar" in loader.consultants
        assert "InvalidChar" not in loader.consultants

        print("  [OK] Validation correctly rejected invalid character")

    print("[PASS] Validation Integration")


def test_save_character_profile():
    """Test saving character profile."""
    print("\n[TEST] Save Character Profile")

    with tempfile.TemporaryDirectory() as temp_dir:
        loader = CharacterLoader(temp_dir)

        # Create character by loading from JSON, then saving
        create_test_character_file(temp_dir, "Boromir")
        loader.load_characters()

        # Get the profile
        profile = loader.get_character_profile("Boromir")
        assert profile is not None

        # Modify profile by saving updated JSON
        characters_dir = os.path.join(temp_dir, "game_data", "characters")
        updated_data = {
            "name": "Boromir",
            "species": "Human",
            "background": "Soldier",
            "backstory": "Captain of Gondor",
            "dnd_class": "Fighter",  # Must match DnDClass enum value
            "subclass": "Champion",
            "level": 6,  # Leveled up
            "ability_scores": {
                "strength": 17,
                "dexterity": 12,
                "constitution": 16,
                "intelligence": 10,
                "wisdom": 11,
                "charisma": 14
            },
            "background_story": "Captain of Gondor",
            "personality_summary": "Brave but conflicted",
            "motivations": ["Protect Gondor"],
            "fears_weaknesses": ["Temptation of power"],
            "relationships": {},
            "equipment": {
                "weapons": ["Sword", "Horn of Gondor"],
                "armor": ["Plate"],
                "items": [],
                "magic_items": []
            },
            "known_spells": []
        }

        filepath = os.path.join(characters_dir, "boromir.json")
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(updated_data, file, indent=2)

        # Reload to update consultant
        profile = CharacterProfile.load_from_file(filepath)
        loader.save_character_profile(profile)

        # Check consultant updated
        assert "Boromir" in loader.consultants
        assert loader.consultants["Boromir"].profile.name == "Boromir"
        assert loader.consultants["Boromir"].profile.level == 6

        print("  [OK] Character profile saved and consultant created")

    print("[PASS] Save Character Profile")


def test_get_character_list():
    """Test getting list of character names."""
    print("\n[TEST] Get Character List")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test characters
        create_test_character_file(temp_dir, "Frodo")
        create_test_character_file(temp_dir, "Sam")
        create_test_character_file(temp_dir, "Merry")

        loader = CharacterLoader(temp_dir)
        loader.load_characters()

        # Get character list
        character_list = loader.get_character_list()

        assert len(character_list) == 3
        assert "Frodo" in character_list
        assert "Sam" in character_list
        assert "Merry" in character_list

        print("  [OK] Character list retrieved correctly")

    print("[PASS] Get Character List")


def test_get_character_profile():
    """Test getting individual character profile."""
    print("\n[TEST] Get Character Profile")

    with tempfile.TemporaryDirectory() as temp_dir:
        create_test_character_file(temp_dir, "Pippin")

        loader = CharacterLoader(temp_dir)
        loader.load_characters()

        # Get profile
        profile = loader.get_character_profile("Pippin")

        assert profile is not None
        assert profile.name == "Pippin"
        assert profile.identity.character_class == DnDClass.FIGHTER
        assert profile.identity.level == 5

        # Test non-existent character
        missing_profile = loader.get_character_profile("NonExistent")
        assert missing_profile is None

        print("  [OK] Character profile retrieved correctly")

    print("[PASS] Get Character Profile")


def test_get_consultant():
    """Test getting character consultant."""
    print("\n[TEST] Get Consultant")

    with tempfile.TemporaryDirectory() as temp_dir:
        create_test_character_file(temp_dir, "Gandalf")

        loader = CharacterLoader(temp_dir)
        loader.load_characters()

        # Get consultant
        consultant = loader.get_consultant("Gandalf")

        assert consultant is not None
        assert consultant.profile.name == "Gandalf"

        # Test non-existent character
        missing_consultant = loader.get_consultant("NonExistent")
        assert missing_consultant is None

        print("  [OK] Consultant retrieved correctly")

    print("[PASS] Get Consultant")


def test_empty_character_directory():
    """Test loading from empty character directory."""
    print("\n[TEST] Empty Character Directory")

    with tempfile.TemporaryDirectory() as temp_dir:
        loader = CharacterLoader(temp_dir)
        loader.load_characters()

        # Should handle empty directory gracefully
        assert not loader.consultants
        assert not loader.get_character_list()

        print("  [OK] Empty directory handled correctly")

    print("[PASS] Empty Character Directory")


def test_update_existing_character():
    """Test updating an existing character profile."""
    print("\n[TEST] Update Existing Character")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create initial character
        create_test_character_file(temp_dir, "Aragorn")

        loader = CharacterLoader(temp_dir)
        loader.load_characters()

        # Get original profile
        original_profile = loader.get_character_profile("Aragorn")
        assert original_profile.identity.level == 5

        # Update profile via JSON
        characters_dir = os.path.join(temp_dir, "game_data", "characters")
        updated_data = {
            "name": "Aragorn",
            "species": "Human",
            "background": "Noble",
            "backstory": "King of Gondor",
            "dnd_class": "Ranger",  # Must match DnDClass enum value
            "subclass": "Hunter",
            "level": 10,  # Leveled up!
            "ability_scores": {
                "strength": 18,
                "dexterity": 15,
                "constitution": 16,
                "intelligence": 12,
                "wisdom": 14,
                "charisma": 16
            },
            "background_story": "King of Gondor",
            "personality_summary": "Noble and wise",
            "motivations": ["Rule justly"],
            "fears_weaknesses": ["Burden of leadership"],
            "relationships": {},
            "equipment": {
                "weapons": ["Anduril"],
                "armor": ["Royal Armor"],
                "items": [],
                "magic_items": ["Ring of Barahir"]
            },
            "known_spells": []
        }

        filepath = os.path.join(characters_dir, "aragorn.json")
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(updated_data, file, indent=2)

        # Load and save updated profile
        updated_profile = CharacterProfile.load_from_file(filepath)
        loader.save_character_profile(updated_profile)

        # Verify update
        new_profile = loader.get_character_profile("Aragorn")
        assert new_profile.identity.level == 10
        assert new_profile.identity.character_class == DnDClass.RANGER
        assert "Anduril" in new_profile.possessions.equipment.get("weapons", [])

        print("  [OK] Character profile updated successfully")

    print("[PASS] Update Existing Character")


def run_all_tests():
    """Run all character loader tests."""
    print("=" * 70)
    print("STORY CHARACTER LOADER TESTS")
    print("=" * 70)

    test_character_loader_initialization()
    test_load_characters()
    test_skip_example_files()
    test_validation_integration()
    test_save_character_profile()
    test_get_character_list()
    test_get_character_profile()
    test_get_consultant()
    test_empty_character_directory()
    test_update_existing_character()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL STORY CHARACTER LOADER TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
