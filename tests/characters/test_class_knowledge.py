"""
Test Class Knowledge Database

Tests the static D&D class knowledge database for all 12 classes.

What we test:
- All 12 D&D classes are present
- Each class has required data fields
- Data structure is consistent
- Class data is valid and complete

Why we test this:
- Class knowledge is used by character consultants for roleplay guidance
- Missing or invalid data would break consultant behavior
- Ensures consistency across all character classes
"""

from tests import test_helpers

# Import CLASS_KNOWLEDGE using centralized helper
CLASS_KNOWLEDGE = test_helpers.safe_from_import(
    "src.characters.consultants.class_knowledge", "CLASS_KNOWLEDGE"
)


def test_all_classes_present():
    """Test that all 12 D&D classes are in the database."""
    print("\n[TEST] All D&D Classes Present")

    expected_classes = [
        "Barbarian", "Bard", "Cleric", "Druid",
        "Fighter", "Monk", "Paladin", "Ranger",
        "Rogue", "Sorcerer", "Warlock", "Wizard"
    ]

    for class_name in expected_classes:
        assert class_name in CLASS_KNOWLEDGE, f"Missing class: {class_name}"
        print(f"  [OK] {class_name} present")

    assert len(CLASS_KNOWLEDGE) == 12, f"Expected 12 classes, found {len(CLASS_KNOWLEDGE)}"
    print("  [OK] All 12 classes present")

    print("[PASS] All D&D Classes Present")


def test_class_data_structure():
    """Test that each class has required fields."""
    print("\n[TEST] Class Data Structure")

    required_fields = [
        "primary_ability",
        "typical_role",
        "decision_style",
        "common_reactions",
        "key_features",
        "roleplay_notes"
    ]

    for class_name, class_data in CLASS_KNOWLEDGE.items():
        for field in required_fields:
            assert field in class_data, f"{class_name} missing field: {field}"
        print(f"  [OK] {class_name} has all required fields")

    print("[PASS] Class Data Structure")


def test_common_reactions_structure():
    """Test that common_reactions has expected categories."""
    print("\n[TEST] Common Reactions Structure")

    expected_reactions = ["threat", "puzzle", "social", "magic"]

    for class_name, class_data in CLASS_KNOWLEDGE.items():
        reactions = class_data.get("common_reactions", {})
        for reaction_type in expected_reactions:
            assert reaction_type in reactions, \
                f"{class_name} missing reaction: {reaction_type}"
        print(f"  [OK] {class_name} has all reaction types")

    print("[PASS] Common Reactions Structure")


def test_key_features_present():
    """Test that each class has key features listed."""
    print("\n[TEST] Key Features Present")

    for class_name, class_data in CLASS_KNOWLEDGE.items():
        key_features = class_data.get("key_features", [])
        assert isinstance(key_features, list), \
            f"{class_name} key_features must be a list"
        assert len(key_features) > 0, \
            f"{class_name} must have at least one key feature"
        print(f"  [OK] {class_name} has {len(key_features)} key features")

    print("[PASS] Key Features Present")


def test_primary_abilities_valid():
    """Test that primary abilities are valid D&D ability scores."""
    print("\n[TEST] Primary Abilities Valid")

    valid_abilities = {
        "Strength", "Dexterity", "Constitution",
        "Intelligence", "Wisdom", "Charisma"
    }

    for class_name, class_data in CLASS_KNOWLEDGE.items():
        primary = class_data.get("primary_ability", "")
        # Handle cases like "Strength or Dexterity" and "Dexterity and Wisdom"
        # Split on both "or" and "and"
        abilities_text = primary.replace(" and ", " or ")
        abilities_mentioned = abilities_text.split(" or ")
        for ability in abilities_mentioned:
            ability = ability.strip()
            assert ability in valid_abilities, \
                f"{class_name} has invalid primary ability: {ability}"
        print(f"  [OK] {class_name} primary ability: {primary}")

    print("[PASS] Primary Abilities Valid")


def test_roleplay_notes_non_empty():
    """Test that roleplay notes exist for each class."""
    print("\n[TEST] Roleplay Notes Non-Empty")

    for class_name, class_data in CLASS_KNOWLEDGE.items():
        notes = class_data.get("roleplay_notes", "")
        assert isinstance(notes, str), \
            f"{class_name} roleplay_notes must be string"
        assert len(notes) > 0, \
            f"{class_name} must have roleplay notes"
        print(f"  [OK] {class_name} has roleplay notes")

    print("[PASS] Roleplay Notes Non-Empty")


def test_specific_class_samples():
    """Test specific class data for correctness."""
    print("\n[TEST] Specific Class Samples")

    # Test Barbarian
    barbarian = CLASS_KNOWLEDGE.get("Barbarian", {})
    assert barbarian.get("primary_ability") == "Strength", \
        "Barbarian should have Strength primary"
    assert "Rage" in barbarian.get("key_features", []), \
        "Barbarian should have Rage feature"
    print("  [OK] Barbarian data correct")

    # Test Wizard
    wizard = CLASS_KNOWLEDGE.get("Wizard", {})
    assert wizard.get("primary_ability") == "Intelligence", \
        "Wizard should have Intelligence primary"
    assert "Spellcasting" in wizard.get("key_features", []), \
        "Wizard should have Spellcasting feature"
    print("  [OK] Wizard data correct")

    # Test Cleric
    cleric = CLASS_KNOWLEDGE.get("Cleric", {})
    assert cleric.get("primary_ability") == "Wisdom", \
        "Cleric should have Wisdom primary"
    assert cleric.get("typical_role") == "Healer/Support", \
        "Cleric should be Healer/Support role"
    print("  [OK] Cleric data correct")

    print("[PASS] Specific Class Samples")


def run_all_tests():
    """Run all class knowledge tests."""
    print("=" * 70)
    print("CLASS KNOWLEDGE TESTS")
    print("=" * 70)

    test_all_classes_present()
    test_class_data_structure()
    test_common_reactions_structure()
    test_key_features_present()
    test_primary_abilities_valid()
    test_roleplay_notes_non_empty()
    test_specific_class_samples()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL CLASS KNOWLEDGE TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
