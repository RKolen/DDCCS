"""
Character Manager Tests

Tests for character loading, profiles, consultants, and spell highlighting.
"""

import sys
import os
import tempfile
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from src.stories.character_manager import CharacterManager
except ImportError as e:
    print(f"[ERROR] Failed to import required modules: {e}")
    print("[ERROR] Make sure you're running from the tests directory")
    sys.exit(1)


def create_test_character_file(directory, name, dnd_class="fighter", spells=None):
    """Helper to create a test character JSON file."""
    character_data = {
        "name": name,
        "species": "Human",
        "level": 5,
        "dnd_class": dnd_class,
        "background": "Soldier",
        "backstory": f"Test character {name}",
        "personality_summary": "Test personality",
        "motivations": ["test motivation"],
        "fears_weaknesses": ["test fear"],
        "relationships": {},
        "equipment": {
            "weapons": ["sword"],
            "armor": ["plate"],
            "items": ["potion"]
        },
        "ability_scores": {
            "strength": 16,
            "dexterity": 12,
            "constitution": 14,
            "intelligence": 10,
            "wisdom": 10,
            "charisma": 8
        },
        "known_spells": spells or []
    }

    filepath = os.path.join(directory, f"{name.lower()}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(character_data, f, indent=2)
    return filepath


def test_character_manager_initialization():
    """Test CharacterManager initialization."""
    print("\n[TEST] CharacterManager Initialization")

    with tempfile.TemporaryDirectory() as temp_dir:
        manager = CharacterManager(temp_dir)

        assert manager.characters_path == temp_dir
        assert manager.ai_client is None
        assert not manager.consultants
        assert manager.known_spells == set()
        print("  [OK] CharacterManager initialized correctly")

    print("[PASS] CharacterManager Initialization")


def test_load_characters_basic():
    """Test loading character profiles."""
    print("\n[TEST] Load Characters - Basic")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test characters
        create_test_character_file(temp_dir, "Theron")
        create_test_character_file(temp_dir, "Kael", "wizard")

        manager = CharacterManager(temp_dir)
        manager.load_characters()

        assert len(manager.consultants) == 2
        assert "Theron" in manager.consultants
        assert "Kael" in manager.consultants
        print("  [OK] Characters loaded correctly")

    print("[PASS] Load Characters - Basic")


def test_load_characters_with_spells():
    """Test loading characters with spell lists."""
    print("\n[TEST] Load Characters - With Spells")

    with tempfile.TemporaryDirectory() as temp_dir:
        create_test_character_file(
            temp_dir, "Gandalf", "wizard", ["Fireball", "Magic Missile"]
        )
        create_test_character_file(
            temp_dir, "Merlin", "sorcerer", ["Shield", "Fireball"]
        )

        manager = CharacterManager(temp_dir)
        manager.load_characters()

        assert len(manager.known_spells) >= 3
        assert "Fireball" in manager.known_spells
        assert "Magic Missile" in manager.known_spells
        assert "Shield" in manager.known_spells
        print("  [OK] Spells extracted from characters")

    print("[PASS] Load Characters - With Spells")


def test_skip_example_files():
    """Test that example and template files are skipped."""
    print("\n[TEST] Skip Example Files")

    with tempfile.TemporaryDirectory() as temp_dir:
        create_test_character_file(temp_dir, "Theron")

        # Create example/template files that should be skipped
        example1 = os.path.join(temp_dir, "class.example.barbarian.json")
        with open(example1, "w", encoding="utf-8") as f:
            json.dump({"name": "Example"}, f)

        template1 = os.path.join(temp_dir, "template.json")
        with open(template1, "w", encoding="utf-8") as f:
            json.dump({"name": "Template"}, f)

        manager = CharacterManager(temp_dir)
        manager.load_characters()

        assert len(manager.consultants) == 1
        assert "Theron" in manager.consultants
        assert "Example" not in manager.consultants
        assert "Template" not in manager.consultants
        print("  [OK] Example and template files skipped")

    print("[PASS] Skip Example Files")


def test_apply_spell_highlighting():
    """Test spell name highlighting in text."""
    print("\n[TEST] Apply Spell Highlighting")

    with tempfile.TemporaryDirectory() as temp_dir:
        create_test_character_file(
            temp_dir, "Wizard", "wizard", ["Fireball", "Shield"]
        )

        manager = CharacterManager(temp_dir)
        manager.load_characters()

        text = "The wizard casts Fireball at the enemies."
        highlighted = manager.apply_spell_highlighting(text)

        assert "**Fireball**" in highlighted
        print("  [OK] Spell highlighting applied")

    print("[PASS] Apply Spell Highlighting")


def test_apply_spell_highlighting_no_spells():
    """Test spell highlighting with no known spells."""
    print("\n[TEST] Apply Spell Highlighting - No Spells")

    with tempfile.TemporaryDirectory() as temp_dir:
        create_test_character_file(temp_dir, "Fighter", "fighter")

        manager = CharacterManager(temp_dir)
        manager.load_characters()

        text = "The fighter swings his sword."
        highlighted = manager.apply_spell_highlighting(text)

        assert highlighted == text
        print("  [OK] No highlighting when no spells known")

    print("[PASS] Apply Spell Highlighting - No Spells")


def test_get_character_list():
    """Test getting list of character names."""
    print("\n[TEST] Get Character List")

    with tempfile.TemporaryDirectory() as temp_dir:
        create_test_character_file(temp_dir, "Theron")
        create_test_character_file(temp_dir, "Kael")
        create_test_character_file(temp_dir, "Lyra")

        manager = CharacterManager(temp_dir)
        manager.load_characters()

        char_list = manager.get_character_list()
        assert len(char_list) == 3
        assert "Theron" in char_list
        assert "Kael" in char_list
        assert "Lyra" in char_list
        print("  [OK] Character list retrieved")

    print("[PASS] Get Character List")


def test_get_character_profile():
    """Test getting a specific character's profile."""
    print("\n[TEST] Get Character Profile")

    with tempfile.TemporaryDirectory() as temp_dir:
        create_test_character_file(temp_dir, "Theron", "fighter")

        manager = CharacterManager(temp_dir)
        manager.load_characters()

        profile = manager.get_character_profile("Theron")
        assert profile is not None
        assert profile.name == "Theron"
        # CharacterClass enum has capitalized values like "Fighter"
        assert profile.identity.character_class.value == "Fighter"
        print("  [OK] Character profile retrieved")

    print("[PASS] Get Character Profile")


def test_get_character_profile_nonexistent():
    """Test getting non-existent character profile."""
    print("\n[TEST] Get Character Profile - Non-existent")

    with tempfile.TemporaryDirectory() as temp_dir:
        manager = CharacterManager(temp_dir)
        manager.load_characters()

        profile = manager.get_character_profile("Nonexistent")
        assert profile is None
        print("  [OK] Non-existent profile returns None")

    print("[PASS] Get Character Profile - Non-existent")


def test_empty_directory():
    """Test loading from empty directory."""
    print("\n[TEST] Empty Directory")

    with tempfile.TemporaryDirectory() as temp_dir:
        manager = CharacterManager(temp_dir)
        manager.load_characters()

        assert len(manager.consultants) == 0
        assert len(manager.known_spells) == 0
        print("  [OK] Empty directory handled correctly")

    print("[PASS] Empty Directory")


def run_all_tests():
    """Run all character manager tests."""
    print("=" * 70)
    print("CHARACTER MANAGER TESTS")
    print("=" * 70)

    test_character_manager_initialization()
    test_load_characters_basic()
    test_load_characters_with_spells()
    test_skip_example_files()
    test_apply_spell_highlighting()
    test_apply_spell_highlighting_no_spells()
    test_get_character_list()
    test_get_character_profile()
    test_get_character_profile_nonexistent()
    test_empty_directory()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL CHARACTER MANAGER TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
