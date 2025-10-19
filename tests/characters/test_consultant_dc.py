"""
Tests for DC Calculation Component

This module tests the DCCalculator component that provides DC
(Difficulty Class) calculations for character actions.
"""

import sys
from pathlib import Path
import test_helpers

# Add tests directory to path for test_helpers
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import and configure test environment
test_helpers.setup_test_environment()

# Import character components
try:
    from src.characters.consultants.consultant_dc import DCCalculator
    from src.characters.consultants.character_profile import (
        CharacterProfile, CharacterIdentity
    )
    from src.characters.character_sheet import DnDClass
    from src.utils.dnd_rules import DC_MEDIUM
except ImportError as e:
    print(f"Error importing DC calculator components: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


def test_dc_calculator_initialization():
    """Test DC calculator initialization."""
    print("\n[TEST] DC Calculator - Initialization")

    identity = CharacterIdentity(
        name="TestChar",
        character_class=DnDClass.FIGHTER,
        level=5
    )
    profile = CharacterProfile(identity=identity)
    class_knowledge = {"Fighter": {"abilities": ["Action Surge"]}}

    calculator = DCCalculator(profile, class_knowledge)

    assert calculator.profile == profile, "Profile not set correctly"
    assert calculator.class_knowledge == class_knowledge, "Knowledge not set"
    print("  [OK] DC calculator initialized correctly")

    print("[PASS] DC Calculator - Initialization")


def test_suggest_dc_basic_action():
    """Test basic DC suggestion for common actions."""
    print("\n[TEST] DC Calculator - Basic Action")

    identity = CharacterIdentity(
        name="TestChar",
        character_class=DnDClass.FIGHTER,
        level=5
    )
    profile = CharacterProfile(identity=identity)
    calculator = DCCalculator(profile, {})

    result = calculator.suggest_dc_for_action("persuade the guard")

    assert "action_type" in result, "Missing action_type"
    assert result["action_type"] == "Persuasion", "Wrong action type"
    assert "suggested_dc" in result, "Missing suggested_dc"
    assert result["suggested_dc"] == DC_MEDIUM, "Wrong base DC"
    assert "reasoning" in result, "Missing reasoning"
    assert "alternative_approaches" in result, "Missing alternatives"
    assert "character_advantage" in result, "Missing advantages"
    print("  [OK] Basic action DC calculated correctly")

    print("[PASS] DC Calculator - Basic Action")


def test_suggest_dc_with_difficulty_modifiers():
    """Test DC adjustments based on difficulty keywords."""
    print("\n[TEST] DC Calculator - Difficulty Modifiers")

    # Use Fighter to avoid class bonuses interfering with tests
    identity = CharacterIdentity(
        name="TestChar",
        character_class=DnDClass.FIGHTER,
        level=5
    )
    profile = CharacterProfile(identity=identity)
    calculator = DCCalculator(profile, {})

    # Easy action (no class bonus for Fighter on Investigation)
    easy_result = calculator.suggest_dc_for_action("easy investigation")
    assert easy_result["suggested_dc"] == DC_MEDIUM - 5, "Easy DC not adjusted"
    print("  [OK] Easy modifier applied correctly")

    # Hard action (no class bonus for Fighter on Investigation)
    hard_result = calculator.suggest_dc_for_action("difficult investigation")
    assert hard_result["suggested_dc"] == DC_MEDIUM + 5, "Hard DC not adjusted"
    print("  [OK] Hard modifier applied correctly")

    # Impossible action (no class bonus for Fighter on Investigation)
    impossible_result = calculator.suggest_dc_for_action("impossible investigation")
    assert impossible_result["suggested_dc"] == DC_MEDIUM + 10, (
        "Impossible DC not adjusted"
    )
    print("  [OK] Impossible modifier applied correctly")

    print("[PASS] DC Calculator - Difficulty Modifiers")


def test_suggest_dc_with_class_bonuses():
    """Test DC adjustments for class-specific strengths."""
    print("\n[TEST] DC Calculator - Class Bonuses")

    # Rogue with stealth (should get -2 DC bonus)
    rogue_identity = CharacterIdentity(
        name="SneakyRogue",
        character_class=DnDClass.ROGUE,
        level=5
    )
    rogue_profile = CharacterProfile(identity=rogue_identity)
    rogue_calc = DCCalculator(rogue_profile, {})

    rogue_result = rogue_calc.suggest_dc_for_action("sneak past guards")
    expected_dc = DC_MEDIUM - 2  # Base - class bonus
    assert rogue_result["suggested_dc"] == expected_dc, (
        f"Rogue stealth bonus not applied: got {rogue_result['suggested_dc']}, "
        f"expected {expected_dc}"
    )
    print("  [OK] Rogue stealth bonus applied")

    # Bard with persuasion (should get -2 DC bonus)
    bard_identity = CharacterIdentity(
        name="CharmingBard",
        character_class=DnDClass.BARD,
        level=5
    )
    bard_profile = CharacterProfile(identity=bard_identity)
    bard_calc = DCCalculator(bard_profile, {})

    bard_result = bard_calc.suggest_dc_for_action("persuade the merchant")
    expected_dc = DC_MEDIUM - 2
    assert bard_result["suggested_dc"] == expected_dc, (
        "Bard persuasion bonus not applied"
    )
    print("  [OK] Bard persuasion bonus applied")

    # Barbarian with intimidation (should get -2 DC bonus)
    barb_identity = CharacterIdentity(
        name="AngryBarbarian",
        character_class=DnDClass.BARBARIAN,
        level=5
    )
    barb_profile = CharacterProfile(identity=barb_identity)
    barb_calc = DCCalculator(barb_profile, {})

    barb_result = barb_calc.suggest_dc_for_action("intimidate the bandit")
    expected_dc = DC_MEDIUM - 2
    assert barb_result["suggested_dc"] == expected_dc, (
        "Barbarian intimidation bonus not applied"
    )
    print("  [OK] Barbarian intimidation bonus applied")

    print("[PASS] DC Calculator - Class Bonuses")


def test_suggest_dc_action_type_detection():
    """Test detection of different action types."""
    print("\n[TEST] DC Calculator - Action Type Detection")

    identity = CharacterIdentity(
        name="TestChar",
        character_class=DnDClass.FIGHTER,
        level=5
    )
    profile = CharacterProfile(identity=identity)
    calculator = DCCalculator(profile, {})

    # Test various action types
    test_cases = [
        ("convince the guard", "Persuasion"),
        ("deceive the merchant", "Deception"),
        ("intimidate the bandit", "Intimidation"),
        ("sneak past the guards", "Stealth"),
        ("climb the wall", "Athletics"),
        ("investigate the room", "Investigation"),
        ("perceive hidden enemies", "Perception"),
        ("cast a spell", "General"),  # Unknown action type
    ]

    for action, expected_type in test_cases:
        result = calculator.suggest_dc_for_action(action)
        assert result["action_type"] == expected_type, (
            f"Wrong action type for '{action}': got {result['action_type']}, "
            f"expected {expected_type}"
        )

    print("  [OK] All action types detected correctly")
    print("[PASS] DC Calculator - Action Type Detection")


def test_suggest_dc_minimum_dc():
    """Test that DC never goes below minimum (5)."""
    print("\n[TEST] DC Calculator - Minimum DC")

    # Create a Rogue (strong stealth) doing easy stealth
    identity = CharacterIdentity(
        name="SneakyRogue",
        character_class=DnDClass.ROGUE,
        level=5
    )
    profile = CharacterProfile(identity=identity)
    calculator = DCCalculator(profile, {})

    # Easy stealth for Rogue: base 15 - 5 (easy) - 2 (class) = 8
    result = calculator.suggest_dc_for_action("easy stealth check")
    assert result["suggested_dc"] >= 5, "DC went below minimum of 5"
    print("  [OK] Minimum DC enforced")

    print("[PASS] DC Calculator - Minimum DC")


def test_suggest_alternative_approaches():
    """Test alternative approach suggestions by class."""
    print("\n[TEST] DC Calculator - Alternative Approaches")

    # Test Rogue alternatives
    rogue_identity = CharacterIdentity(
        name="SneakyRogue",
        character_class=DnDClass.ROGUE,
        level=5
    )
    rogue_profile = CharacterProfile(identity=rogue_identity)
    rogue_calc = DCCalculator(rogue_profile, {})

    rogue_alternatives = rogue_calc.suggest_alternative_approaches("any action")
    assert isinstance(rogue_alternatives, list), "Alternatives not a list"
    assert len(rogue_alternatives) > 0, "No alternatives provided"
    assert any("sneak" in alt.lower() for alt in rogue_alternatives), (
        "Rogue alternatives don't mention sneaking"
    )
    print("  [OK] Rogue alternatives appropriate")

    # Test Bard alternatives
    bard_identity = CharacterIdentity(
        name="CharmingBard",
        character_class=DnDClass.BARD,
        level=5
    )
    bard_profile = CharacterProfile(identity=bard_identity)
    bard_calc = DCCalculator(bard_profile, {})

    bard_alternatives = bard_calc.suggest_alternative_approaches("any action")
    assert any(
        "social" in alt.lower() or "performance" in alt.lower()
        for alt in bard_alternatives
    ), "Bard alternatives not social-focused"
    print("  [OK] Bard alternatives appropriate")

    # Test Fighter alternatives
    fighter_identity = CharacterIdentity(
        name="BraveFighter",
        character_class=DnDClass.FIGHTER,
        level=5
    )
    fighter_profile = CharacterProfile(identity=fighter_identity)
    fighter_calc = DCCalculator(fighter_profile, {})

    fighter_alternatives = fighter_calc.suggest_alternative_approaches("any action")
    assert any(
        "tactic" in alt.lower() or "direct" in alt.lower()
        for alt in fighter_alternatives
    ), "Fighter alternatives not tactical"
    print("  [OK] Fighter alternatives appropriate")

    print("[PASS] DC Calculator - Alternative Approaches")


def test_check_character_advantages():
    """Test character advantage detection."""
    print("\n[TEST] DC Calculator - Character Advantages")

    # Rogue with stealth action
    rogue_identity = CharacterIdentity(
        name="SneakyRogue",
        character_class=DnDClass.ROGUE,
        level=5
    )
    rogue_profile = CharacterProfile(identity=rogue_identity)
    rogue_calc = DCCalculator(rogue_profile, {})

    rogue_advantages = rogue_calc.check_character_advantages("Stealth")
    assert isinstance(rogue_advantages, list), "Advantages not a list"
    assert len(rogue_advantages) > 0, "Rogue should have stealth advantage"
    assert any("expertise" in adv.lower() for adv in rogue_advantages), (
        "Rogue expertise not mentioned"
    )
    print("  [OK] Rogue stealth advantages detected")

    # Bard with persuasion action
    bard_identity = CharacterIdentity(
        name="CharmingBard",
        character_class=DnDClass.BARD,
        level=5
    )
    bard_profile = CharacterProfile(identity=bard_identity)
    bard_calc = DCCalculator(bard_profile, {})

    bard_advantages = bard_calc.check_character_advantages("Persuasion")
    assert len(bard_advantages) > 0, "Bard should have persuasion advantage"
    print("  [OK] Bard persuasion advantages detected")

    # Fighter with non-specialty action
    fighter_identity = CharacterIdentity(
        name="BraveFighter",
        character_class=DnDClass.FIGHTER,
        level=5
    )
    fighter_profile = CharacterProfile(identity=fighter_identity)
    fighter_calc = DCCalculator(fighter_profile, {})

    fighter_advantages = fighter_calc.check_character_advantages("Persuasion")
    # Fighter has no special persuasion advantages
    assert isinstance(fighter_advantages, list), "Advantages not a list"
    print("  [OK] Non-specialty actions handled correctly")

    print("[PASS] DC Calculator - Character Advantages")


def test_check_character_advantages_with_background():
    """Test advantage detection based on character background."""
    print("\n[TEST] DC Calculator - Background Advantages")

    # Noble background with persuasion
    noble_identity = CharacterIdentity(
        name="NobleChar",
        character_class=DnDClass.FIGHTER,
        level=5
    )
    noble_profile = CharacterProfile(identity=noble_identity)
    # Set background through the personality field (using backward-compat property)
    noble_profile.personality.background_story = (
        "Born into a noble family, trained in diplomacy"
    )

    noble_calc = DCCalculator(noble_profile, {})
    noble_advantages = noble_calc.check_character_advantages("Persuasion")
    assert any("noble" in adv.lower() for adv in noble_advantages), (
        "Noble background advantage not detected"
    )
    print("  [OK] Noble background advantage detected")

    # Criminal background with stealth
    criminal_identity = CharacterIdentity(
        name="CriminalChar",
        character_class=DnDClass.FIGHTER,
        level=5
    )
    criminal_profile = CharacterProfile(identity=criminal_identity)
    criminal_profile.personality.background_story = (
        "Former criminal who learned to survive on the streets"
    )

    criminal_calc = DCCalculator(criminal_profile, {})
    criminal_advantages = criminal_calc.check_character_advantages("Stealth")
    assert any("criminal" in adv.lower() for adv in criminal_advantages), (
        "Criminal background advantage not detected"
    )
    print("  [OK] Criminal background advantage detected")

    print("[PASS] DC Calculator - Background Advantages")


def run_all_tests():
    """Run all DC calculator tests."""
    print("=" * 70)
    print("DC CALCULATOR TESTS")
    print("=" * 70)

    test_dc_calculator_initialization()
    test_suggest_dc_basic_action()
    test_suggest_dc_with_difficulty_modifiers()
    test_suggest_dc_with_class_bonuses()
    test_suggest_dc_action_type_detection()
    test_suggest_dc_minimum_dc()
    test_suggest_alternative_approaches()
    test_check_character_advantages()
    test_check_character_advantages_with_background()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL DC CALCULATOR TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
