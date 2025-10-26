"""
Test Character Sheet Data Structures

Tests enums and NPC dataclasses from character_sheet.py.

What we test:
- DnDClass enum has all 12 classes
- Species enum has expected species
- Lineage lists are non-empty
- NPC dataclasses can be instantiated
- NPC data structures are valid

Why we test this:
- These structures are used throughout the character system
- Enums must have correct values for JSON serialization
- NPC profiles are used by story manager and auto-detection
"""

import sys
from pathlib import Path
from tests import test_helpers
# Add tests directory to path for test_helpers
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import and configure test environment
test_helpers.setup_test_environment()

# Import character sheet components
try:
    from src.characters.character_sheet import (
        DnDClass,
        Species,
        ELF_LINEAGES,
        GNOME_LINEAGES,
        TIEFLING_LINEAGES,
        DRAGONBORN_LINEAGES,
        NPCBasicInfo,
        NPCPhysicalInfo,
        NPCCharacterInfo,
        NPCProfile
    )
except ImportError as e:
    print(f"[ERROR] Failed to import character_sheet: {e}")
    sys.exit(1)


def test_dnd_class_enum():
    """Test that DnDClass enum has all 12 classes."""
    print("\n[TEST] DnDClass Enum")

    expected_classes = [
        ("BARBARIAN", "Barbarian"),
        ("BARD", "Bard"),
        ("CLERIC", "Cleric"),
        ("DRUID", "Druid"),
        ("FIGHTER", "Fighter"),
        ("MONK", "Monk"),
        ("PALADIN", "Paladin"),
        ("RANGER", "Ranger"),
        ("ROGUE", "Rogue"),
        ("SORCERER", "Sorcerer"),
        ("WARLOCK", "Warlock"),
        ("WIZARD", "Wizard"),
    ]

    for enum_name, enum_value in expected_classes:
        assert hasattr(DnDClass, enum_name), f"Missing class: {enum_name}"
        assert getattr(DnDClass, enum_name).value == enum_value, \
            f"{enum_name} has wrong value"
        print(f"  [OK] {enum_name} = {enum_value}")

    assert len(DnDClass) == 12, f"Expected 12 classes, found {len(DnDClass)}"
    print("  [OK] All 12 D&D classes present")

    print("[PASS] DnDClass Enum")


def test_species_enum():
    """Test that Species enum has expected species."""
    print("\n[TEST] Species Enum")

    expected_species = [
        "AASIMAR", "HUMAN", "ELF", "DWARF", "HALFLING",
        "DRAGONBORN", "GNOME", "GOLIATH", "ORC", "TIEFLING"
    ]

    for species_name in expected_species:
        assert hasattr(Species, species_name), f"Missing species: {species_name}"
        print(f"  [OK] {species_name} present")

    assert len(Species) >= len(expected_species), \
        f"Expected at least {len(expected_species)} species"
    print(f"  [OK] All expected species present ({len(Species)} total)")

    print("[PASS] Species Enum")


def test_lineage_lists():
    """Test that lineage lists are non-empty and valid."""
    print("\n[TEST] Lineage Lists")

    assert isinstance(ELF_LINEAGES, list), "ELF_LINEAGES must be list"
    assert len(ELF_LINEAGES) > 0, "ELF_LINEAGES must not be empty"
    print(f"  [OK] ELF_LINEAGES has {len(ELF_LINEAGES)} lineages")

    assert isinstance(GNOME_LINEAGES, list), "GNOME_LINEAGES must be list"
    assert len(GNOME_LINEAGES) > 0, "GNOME_LINEAGES must not be empty"
    print(f"  [OK] GNOME_LINEAGES has {len(GNOME_LINEAGES)} lineages")

    assert isinstance(TIEFLING_LINEAGES, list), "TIEFLING_LINEAGES must be list"
    assert len(TIEFLING_LINEAGES) > 0, "TIEFLING_LINEAGES must not be empty"
    print(f"  [OK] TIEFLING_LINEAGES has {len(TIEFLING_LINEAGES)} lineages")

    assert isinstance(DRAGONBORN_LINEAGES, list), "DRAGONBORN_LINEAGES must be list"
    assert len(DRAGONBORN_LINEAGES) > 0, "DRAGONBORN_LINEAGES must not be empty"
    print(f"  [OK] DRAGONBORN_LINEAGES has {len(DRAGONBORN_LINEAGES)} lineages")

    print("[PASS] Lineage Lists")


def test_npc_basic_info():
    """Test NPCBasicInfo dataclass."""
    print("\n[TEST] NPCBasicInfo Dataclass")

    # Create minimal NPC basic info
    basic = NPCBasicInfo(name="Test NPC")

    assert basic.name == "Test NPC", "Name not set correctly"
    assert basic.role == "NPC", "Role should default to NPC"
    assert basic.nickname is None, "Nickname should default to None"
    assert basic.recurring is False, "Recurring should default to False"
    print("  [OK] Minimal initialization works")

    # Create full NPC basic info
    full_basic = NPCBasicInfo(
        name="Full NPC",
        nickname="Nicky",
        role="Quest Giver",
        recurring=True
    )

    assert full_basic.name == "Full NPC", "Name not set"
    assert full_basic.nickname == "Nicky", "Nickname not set"
    assert full_basic.role == "Quest Giver", "Role not set"
    assert full_basic.recurring is True, "Recurring not set"
    print("  [OK] Full initialization works")

    print("[PASS] NPCBasicInfo Dataclass")


def test_npc_physical_info():
    """Test NPCPhysicalInfo dataclass."""
    print("\n[TEST] NPCPhysicalInfo Dataclass")

    # Test defaults
    physical = NPCPhysicalInfo()
    assert physical.species == "Human", "Species should default to Human"
    assert physical.lineage == "", "Lineage should default to empty string"
    print("  [OK] Default initialization works")

    # Test with values
    physical_elf = NPCPhysicalInfo(species="Elf", lineage="High Elf")
    assert physical_elf.species == "Elf", "Species not set"
    assert physical_elf.lineage == "High Elf", "Lineage not set"
    print("  [OK] Physical info initialization works")

    print("[PASS] NPCPhysicalInfo Dataclass")


def test_npc_character_info():
    """Test NPCCharacterInfo dataclass."""
    print("\n[TEST] NPCCharacterInfo Dataclass")

    # Test defaults
    character = NPCCharacterInfo()
    assert character.personality == "", "Personality should default to empty"
    assert len(character.relationships) == 0, "Relationships should default to empty dict"
    assert len(character.key_traits) == 0, "Traits should default to empty list"
    assert len(character.abilities) == 0, "Abilities should default to empty list"
    assert character.notes == "", "Notes should default to empty"
    print("  [OK] Default initialization works")

    # Test with values
    character_full = NPCCharacterInfo(
        personality="Friendly and curious",
        relationships={"Hero": "Friend"},
        key_traits=["Honest", "Brave"],
        abilities=["Persuasion"],
        notes="Met in tavern"
    )

    assert character_full.personality == "Friendly and curious", "Personality not set"
    assert "Hero" in character_full.relationships, "Relationships not set"
    assert len(character_full.key_traits) == 2, "Traits not set"
    assert len(character_full.abilities) == 1, "Abilities not set"
    assert character_full.notes == "Met in tavern", "Notes not set"
    print("  [OK] Character info initialization works")

    print("[PASS] NPCCharacterInfo Dataclass")


def test_npc_profile():
    """Test NPCProfile complete dataclass."""
    print("\n[TEST] NPCProfile Dataclass")

    # Create NPC profile with nested structures
    basic = NPCBasicInfo(name="Test Merchant", role="Shopkeeper")
    physical = NPCPhysicalInfo(species="Dwarf", lineage="Hill Dwarf")
    character = NPCCharacterInfo(
        personality="Gruff but fair",
        key_traits=["Honest", "Stubborn"],
        notes="Runs the smithy"
    )

    profile = NPCProfile(
        basic=basic,
        physical=physical,
        character=character
    )

    assert profile.basic.name == "Test Merchant", "Basic info not set"
    assert profile.physical.species == "Dwarf", "Physical not set"
    assert profile.character.personality == "Gruff but fair", "Character not set"
    print("  [OK] NPC profile initialization works")

    # Test property access (backward compatibility)
    assert profile.name == "Test Merchant", "Name property not working"
    print("  [OK] Property access works")

    print("[PASS] NPCProfile Dataclass")


def test_npc_profile_create():
    """Test NPCProfile.create() convenience method."""
    print("\n[TEST] NPCProfile.create() Method")

    # Create NPC using convenience method
    npc = NPCProfile.create(
        name="Tavern Owner",
        nickname="Big Tom",
        role="Innkeeper",
        species="Human",
        personality="Jovial and welcoming",
        key_traits=["Friendly", "Gossip"],
        recurring=True
    )

    assert npc.name == "Tavern Owner", "Name not set"
    assert npc.nickname == "Big Tom", "Nickname not set"
    assert npc.basic.role == "Innkeeper", "Role not set"
    assert npc.physical.species == "Human", "Species not set"
    assert npc.character.personality == "Jovial and welcoming", "Personality not set"
    assert len(npc.character.key_traits) == 2, "Traits not set"
    assert npc.basic.recurring is True, "Recurring not set"
    print("  [OK] create() method works")

    # Test minimal create
    minimal_npc = NPCProfile.create(name="Guard")
    assert minimal_npc.name == "Guard", "Minimal name not set"
    assert minimal_npc.basic.role == "NPC", "Default role not set"
    assert minimal_npc.physical.species == "Human", "Default species not set"
    print("  [OK] Minimal create() works")

    print("[PASS] NPCProfile.create() Method")


def test_enum_value_access():
    """Test that enum values can be accessed and compared."""
    print("\n[TEST] Enum Value Access")

    # Test DnDClass enum access
    wizard = DnDClass.WIZARD
    assert wizard.value == "Wizard", "Enum value not accessible"
    assert wizard == DnDClass.WIZARD, "Enum equality check failed"
    assert wizard != DnDClass.FIGHTER, "Enum inequality check failed"
    print("  [OK] DnDClass enum value access works")

    # Test Species enum access
    elf = Species.ELF
    assert elf.value == "Elf", "Species value not accessible"
    assert elf == Species.ELF, "Species equality check failed"
    print("  [OK] Species enum value access works")

    # Test enum construction from value
    wizard_from_value = DnDClass("Wizard")
    assert wizard_from_value == DnDClass.WIZARD, \
        "Enum construction from value failed"
    print("  [OK] Enum construction from value works")

    print("[PASS] Enum Value Access")


def run_all_tests():
    """Run all character sheet tests."""
    print("=" * 70)
    print("CHARACTER SHEET TESTS")
    print("=" * 70)

    test_dnd_class_enum()
    test_species_enum()
    test_lineage_lists()
    test_npc_basic_info()
    test_npc_physical_info()
    test_npc_character_info()
    test_npc_profile()
    test_npc_profile_create()
    test_enum_value_access()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL CHARACTER SHEET TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
