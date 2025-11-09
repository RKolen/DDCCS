"""
Test CharacterProfile Dataclass

Tests the CharacterProfile dataclass for character data management,
JSON serialization/deserialization, and field validation.

What we test:
- CharacterProfile initialization with defaults
- Field validation and required fields
- JSON serialization (to_dict, save_to_file)
- JSON deserialization (from_dict, load_from_file)
- File I/O operations

Why we test this:
- CharacterProfile is the core data structure for all characters
- Must correctly save/load character data from JSON files
- Field validation prevents invalid character configurations
- Serialization must preserve all character information
"""

from pathlib import Path
import tempfile
import os
import json

from tests import test_helpers

# Import required character profile symbols via canonical test helper
CharacterProfile = test_helpers.safe_from_import(
    "src.characters.consultants.character_profile", "CharacterProfile"
)
CharacterIdentity = test_helpers.safe_from_import(
    "src.characters.consultants.character_profile", "CharacterIdentity"
)
CharacterPersonality = test_helpers.safe_from_import(
    "src.characters.consultants.character_profile", "CharacterPersonality"
)
CharacterBehavior = test_helpers.safe_from_import(
    "src.characters.consultants.character_profile", "CharacterBehavior"
)
CharacterStory = test_helpers.safe_from_import(
    "src.characters.consultants.character_profile", "CharacterStory"
)
CharacterStats = test_helpers.safe_from_import(
    "src.characters.consultants.character_profile", "CharacterStats"
)
CharacterAbilities = test_helpers.safe_from_import(
    "src.characters.consultants.character_profile", "CharacterAbilities"
)
CharacterMechanics = test_helpers.safe_from_import(
    "src.characters.consultants.character_profile", "CharacterMechanics"
)
CharacterPossessions = test_helpers.safe_from_import(
    "src.characters.consultants.character_profile", "CharacterPossessions"
)
DnDClass = test_helpers.safe_from_import("src.characters.character_sheet", "DnDClass")


def test_character_profile_initialization():
    """Test CharacterProfile can be loaded from canonical Aragorn profile."""
    print("\n[TEST] CharacterProfile Initialization (Aragorn)")

    # Load Aragorn profile from canonical JSON
    aragorn_path = (
        Path(__file__).parent.parent.parent / "game_data" / "characters" / "aragorn.json"
    )
    assert aragorn_path.exists(), f"Aragorn profile not found at {aragorn_path}"
    profile = CharacterProfile.load_from_file(str(aragorn_path))

    # Basic identity checks
    assert profile.name == "Aragorn", "Name not set to Aragorn"
    assert profile.character_class == DnDClass.RANGER, "Class not set to Ranger"
    assert profile.level == 10, "Level not set"
    print("  [OK] Canonical Aragorn profile loaded")

    # Check nested dataclasses
    assert isinstance(
        profile.personality, CharacterPersonality
    ), "Personality not initialized"
    assert isinstance(profile.behavior, CharacterBehavior), "Behavior not initialized"
    assert isinstance(profile.story, CharacterStory), "Story not initialized"
    assert isinstance(
        profile.mechanics, CharacterMechanics
    ), "Mechanics not initialized"
    assert isinstance(
        profile.possessions, CharacterPossessions
    ), "Possessions not initialized"
    print("  [OK] Nested dataclasses initialized correctly")

    # Check property values
    assert isinstance(profile.background_story, str), "Background story not string"
    assert len(profile.background_story) > 0, "Background story is empty"
    assert isinstance(profile.relationships, dict), "Relationships not dict"
    assert isinstance(profile.known_spells, list), "Known spells not list"
    assert isinstance(profile.equipment, dict), "Equipment not dict"
    print("  [OK] Canonical property values correct")

    print("[PASS] CharacterProfile Initialization (Aragorn)")


def test_character_profile_full_initialization():
    """Test CharacterProfile with all nested structures populated."""
    print("\n[TEST] CharacterProfile Full Initialization")

    # Create fully populated profile with new structure
    identity = CharacterIdentity(
        name="Thorin Ironforge",
        character_class=DnDClass.FIGHTER,
        species="Dwarf",
        level=10,
        nickname="The Hammer",
        subclass="Battle Master",
    )

    personality = CharacterPersonality(
        background_story="A veteran warrior from the mountains",
        personality_summary="Brave, loyal, and honor-bound",
        motivations=["Protect the innocent", "Honor ancestors"],
        fears_weaknesses=["Fear of drowning", "Stubborn pride"],
        relationships={"Elara": "Trusted ally and friend", "Grimlock": "Bitter rival"},
        goals=["Reclaim ancestral homeland"],
        secrets=["Harbors guilt from past failure"],
    )

    abilities = CharacterAbilities(
        known_spells=["Shield", "Misty Step"],
        feats=["Great Weapon Master"],
        class_abilities=["Second Wind", "Action Surge"],
    )

    mechanics = CharacterMechanics(
        stats=CharacterStats(
            ability_scores={"strength": 18, "constitution": 16},
            armor_class=18,
            max_hit_points=95,
        ),
        abilities=abilities,
    )

    possessions = CharacterPossessions(
        equipment={"weapons": ["Battleaxe", "Shield"], "armor": ["Plate Armor"]},
        magic_items=["Ring of Protection"],
    )

    profile = CharacterProfile(
        identity=identity,
        personality=personality,
        mechanics=mechanics,
        possessions=possessions,
    )

    # Behavior should be generated in-memory for profiles that don't provide one
    assert isinstance(profile.behavior, CharacterBehavior), "Behavior not generated"
    assert isinstance(profile.behavior.preferred_strategies, list), "preferred_strategies not list"
    assert isinstance(profile.behavior.typical_reactions, dict), "typical_reactions not dict"
    assert isinstance(profile.behavior.speech_patterns, list), "speech_patterns not list"

    # Verify all fields via properties
    assert profile.name == "Thorin Ironforge", "Name incorrect"
    assert profile.species == "Dwarf", "Species incorrect"
    assert profile.character_class == DnDClass.FIGHTER, "Class incorrect"
    assert profile.level == 10, "Level incorrect"
    assert profile.identity.nickname == "The Hammer", "Nickname incorrect"
    assert profile.identity.subclass == "Battle Master", "Subclass incorrect"
    assert "veteran warrior" in profile.background_story, "Background incorrect"
    assert len(profile.personality.motivations) == 2, "Motivations count incorrect"
    assert "Elara" in profile.relationships, "Relationship missing"
    assert "Battleaxe" in profile.equipment["weapons"], "Weapon missing"
    assert "Shield" in profile.known_spells, "Spell missing"
    assert profile.mechanics.stats.armor_class == 18, "AC incorrect"
    print("  [OK] All nested structures populated correctly")

    print("[PASS] CharacterProfile Full Initialization")


def test_character_profile_save_and_load():
    """Test CharacterProfile file I/O operations (primary use case)."""
    print("\n[TEST] CharacterProfile Save and Load")

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = f.name

    try:
        # Create profile with nested structure
        identity = test_helpers.make_identity(
            name="File Test Character", dnd_class=DnDClass.BARD, level=4
        )
        # Ensure species matches the original explicit test value before saving
        identity.species = "Half-Elf"

        personality = CharacterPersonality(
            background_story="A traveling musician",
            motivations=["Spread joy through music"],
            relationships={"Tavern Owner": "Friend and patron"},
        )

        abilities = CharacterAbilities(
            known_spells=["Vicious Mockery", "Healing Word"], feats=["War Caster"]
        )

        mechanics = CharacterMechanics(abilities=abilities)

        original = CharacterProfile(
            identity=identity, personality=personality, mechanics=mechanics
        )

        # Save to file
        original.save_to_file(temp_path)
        assert os.path.exists(temp_path), "File not created"
        print("  [OK] save_to_file() creates file")

        # Load profile from file
        loaded = CharacterProfile.load_from_file(temp_path)
        assert loaded.name == "File Test Character", "Loaded name incorrect"
        assert loaded.character_class == DnDClass.BARD, "Loaded class incorrect"
        assert loaded.level == 4, "Loaded level incorrect"
        identity.species = "Half-Elf"
        assert loaded.species == identity.species, "Loaded species incorrect"
        assert "musician" in loaded.background_story, "Loaded background incorrect"
        assert len(loaded.known_spells) == 2, "Loaded spells count incorrect"
        assert "Vicious Mockery" in loaded.known_spells, "Spell not loaded"
        assert "Tavern Owner" in loaded.relationships, "Relationship not loaded"
        print("  [OK] load_from_file() restores profile correctly")

        # Verify properties work on loaded profile
        assert loaded.name == original.name, "Name mismatch"
        assert loaded.level == original.level, "Level mismatch"
        assert loaded.character_class == original.character_class, "Class mismatch"
        assert isinstance(loaded.behavior, CharacterBehavior), "Behavior missing on loaded profile"
        print("  [OK] Properties work on loaded profile")

    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    print("[PASS] CharacterProfile Save and Load")


def test_character_profile_backward_compatibility():
    """Test loading old JSON format with dnd_class field."""
    print("\n[TEST] CharacterProfile Backward Compatibility")

    # Create temporary file with old format
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = f.name

    try:
        # Write old-format JSON directly
        old_format = {
            "name": "Legacy Character",
            "dnd_class": "Wizard",  # Old field name (capitalized like enum value)
            "level": 5,
            "species": "Human",
            "backstory": "An old character",  # Old field name
            "personality_traits": ["Curious", "Cautious"],  # Old field name
            "bonds": ["Seek lost knowledge"],  # Old field name (motivations)
            "flaws": ["Overconfident"],  # Old field name (fears_weaknesses)
            "relationships": {},
            "equipment": {"weapons": ["Staff"]},
            "known_spells": ["Fireball"],
        }

        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(old_format, f, indent=2)

        # Load using new CharacterProfile
        loaded = CharacterProfile.load_from_file(temp_path)

        # Verify correct mapping
        assert loaded.name == "Legacy Character", "Name not loaded"
        assert loaded.character_class == DnDClass.WIZARD, "Class not mapped"
        assert loaded.level == 5, "Level not loaded"
        assert (
            "old character" in loaded.background_story.lower()
        ), "Backstory not mapped"
        assert "Curious" in loaded.personality.personality_summary, "Traits not mapped"
        assert (
            "Seek lost knowledge" in loaded.personality.motivations
        ), "Bonds not mapped"
        assert (
            "Overconfident" in loaded.personality.fears_weaknesses
        ), "Flaws not mapped"
        print("  [OK] Old JSON format loaded and mapped correctly")

    finally:
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    print("[PASS] CharacterProfile Backward Compatibility")


def run_all_tests():
    """Run all CharacterProfile tests."""
    print("=" * 70)
    print("CHARACTER PROFILE TESTS")
    print("=" * 70)

    test_character_profile_initialization()
    test_character_profile_full_initialization()
    test_character_profile_save_and_load()
    test_character_profile_backward_compatibility()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL CHARACTER PROFILE TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
