"""
Test Character Consultant Core

Tests the main CharacterConsultant class that coordinates all character
consultation services.

What we test:
- Consultant initialization with CharacterProfile
- Reaction suggestions based on situation type
- Personality-based modifications
- Item management and retrieval
- Status reporting
- Delegation to specialized components (DC, Story, AI)

Why we test this:
- CharacterConsultant is the main interface for character consultations
- Must correctly coordinate between multiple components
- Reactions must be consistent with class and personality
- Component delegation must work correctly
"""

import sys
from pathlib import Path
import tempfile
import os
import test_helpers
# Add tests directory to path for test_helpers
sys.path.insert(0, str(Path(__file__).parent.parent))


# Import and configure test environment
test_helpers.setup_test_environment()

# Import consultant components
try:
    from src.characters.consultants.consultant_core import CharacterConsultant
    from src.characters.consultants.character_profile import (
        CharacterProfile,
        CharacterIdentity,
        CharacterPersonality,
        CharacterAbilities,
        CharacterMechanics,
        CharacterPossessions,
    )
    from src.characters.character_sheet import DnDClass
except ImportError as e:
    print(f"[ERROR] Failed to import consultant_core: {e}")
    sys.exit(1)


def create_test_profile(character_class: DnDClass = DnDClass.WIZARD) -> CharacterProfile:
    """Create a test character profile for testing."""
    identity = CharacterIdentity(
        name="Test Character",
        character_class=character_class,
        level=5,
        species="Human"
    )

    personality = CharacterPersonality(
        background_story="A curious scholar seeking knowledge",
        personality_summary="Cautious and analytical",
        motivations=["Discover ancient secrets"],
        fears_weaknesses=["Rushing into danger"],
        goals=["Master arcane arts"]
    )

    abilities = CharacterAbilities(
        known_spells=["Fireball", "Shield", "Detect Magic"]
    )

    mechanics = CharacterMechanics(abilities=abilities)

    return CharacterProfile(
        identity=identity,
        personality=personality,
        mechanics=mechanics
    )


def test_consultant_initialization():
    """Test CharacterConsultant initialization."""
    print("\n[TEST] CharacterConsultant Initialization")

    profile = create_test_profile()
    consultant = CharacterConsultant(profile)

    assert consultant.profile == profile, "Profile not set correctly"
    assert consultant.class_knowledge is not None, "Class knowledge not loaded"
    assert consultant.dc_calculator is not None, "DC calculator not initialized"
    assert consultant.story_analyzer is not None, "Story analyzer not initialized"
    assert consultant.ai_consultant is not None, "AI consultant not initialized"
    print("  [OK] All components initialized")

    # Verify class knowledge is correct
    assert consultant.class_knowledge["primary_ability"] == "Intelligence", \
        "Wizard should use Intelligence"
    print("  [OK] Class knowledge loaded correctly")

    print("[PASS] CharacterConsultant Initialization")


def test_suggest_reaction_threat():
    """Test reaction suggestions for threat situations."""
    print("\n[TEST] Suggest Reaction - Threat")

    profile = create_test_profile()
    consultant = CharacterConsultant(profile)

    result = consultant.suggest_reaction("A dragon attacks the party!")

    assert "character" in result, "Missing character field"
    assert "class_reaction" in result, "Missing class reaction"
    assert "personality_modifier" in result, "Missing personality modifier"
    assert "suggested_approach" in result, "Missing suggested approach"
    assert "dialogue_suggestion" in result, "Missing dialogue suggestion"
    assert "consistency_notes" in result, "Missing consistency notes"
    assert result["character"] == "Test Character", "Wrong character name"
    print("  [OK] Threat reaction structure correct")

    print("[PASS] Suggest Reaction - Threat")


def test_suggest_reaction_puzzle():
    """Test reaction suggestions for puzzle situations."""
    print("\n[TEST] Suggest Reaction - Puzzle")

    profile = create_test_profile()
    consultant = CharacterConsultant(profile)

    result = consultant.suggest_reaction("You encounter a mysterious riddle")

    assert "class_reaction" in result, "Missing class reaction"
    assert "suggested_approach" in result, "Missing suggested approach"
    print("  [OK] Puzzle reaction structure correct")

    print("[PASS] Suggest Reaction - Puzzle")


def test_suggest_reaction_social():
    """Test reaction suggestions for social situations."""
    print("\n[TEST] Suggest Reaction - Social")

    profile = create_test_profile()
    consultant = CharacterConsultant(profile)

    result = consultant.suggest_reaction("You need to persuade the guard")

    assert "class_reaction" in result, "Missing class reaction"
    assert "dialogue_suggestion" in result, "Missing dialogue suggestion"
    print("  [OK] Social reaction structure correct")

    print("[PASS] Suggest Reaction - Social")


def test_suggest_reaction_magic():
    """Test reaction suggestions for magic situations."""
    print("\n[TEST] Suggest Reaction - Magic")

    profile = create_test_profile()
    consultant = CharacterConsultant(profile)

    result = consultant.suggest_reaction("You sense magical energy nearby")

    assert "class_reaction" in result, "Missing class reaction"
    assert "suggested_approach" in result, "Missing suggested approach"
    print("  [OK] Magic reaction structure correct")

    print("[PASS] Suggest Reaction - Magic")


def test_get_personality_modifier():
    """Test personality modifier generation."""
    print("\n[TEST] Get Personality Modifier")

    profile = create_test_profile()
    consultant = CharacterConsultant(profile)

    modifier = consultant.get_personality_modifier("threat")

    assert isinstance(modifier, str), "Modifier should be string"
    assert len(modifier) > 0, "Modifier should not be empty"
    print("  [OK] Personality modifier generated")

    print("[PASS] Get Personality Modifier")


def test_check_consistency_factors():
    """Test consistency factor checking."""
    print("\n[TEST] Check Consistency Factors")

    profile = create_test_profile()
    consultant = CharacterConsultant(profile)

    factors = consultant.check_consistency_factors("rushing into battle")

    assert isinstance(factors, list), "Factors should be list"
    # Should find fear of "rushing into danger"
    assert len(factors) > 0, "Should detect consistency issue"
    print(f"  [OK] Found {len(factors)} consistency factors")

    print("[PASS] Check Consistency Factors")


def test_get_all_character_items():
    """Test retrieval of all character items."""
    print("\n[TEST] Get All Character Items")

    # Create profile with equipment
    identity = CharacterIdentity(
        name="Equipped Character",
        character_class=DnDClass.FIGHTER,
        level=5
    )

    possessions = CharacterPossessions(
        equipment={
            "weapons": ["Longsword", "Shield"],
            "armor": ["Plate Armor"],
            "items": ["Rope", "Torch"]
        },
        magic_items=["Ring of Protection"]
    )

    profile = CharacterProfile(identity=identity, possessions=possessions)
    consultant = CharacterConsultant(profile)

    items = consultant.get_all_character_items()

    assert isinstance(items, list), "Items should be list"
    assert "Longsword" in items, "Should include weapons"
    assert "Plate Armor" in items, "Should include armor"
    assert "Rope" in items, "Should include items"
    assert "Ring of Protection" in items, "Should include magic items"
    print(f"  [OK] Retrieved {len(items)} items")

    print("[PASS] Get All Character Items")


def test_get_relationships():
    """Test relationship retrieval."""
    print("\n[TEST] Get Relationships")

    identity = CharacterIdentity(
        name="Social Character",
        character_class=DnDClass.BARD,
        level=3
    )

    personality = CharacterPersonality(
        relationships={"NPC1": "Friend", "NPC2": "Rival"}
    )

    profile = CharacterProfile(identity=identity, personality=personality)
    consultant = CharacterConsultant(profile)

    relationships = consultant.get_relationships()

    assert isinstance(relationships, dict), "Relationships should be dict"
    assert "NPC1" in relationships, "Missing relationship"
    assert relationships["NPC1"] == "Friend", "Wrong relationship value"
    print("  [OK] Relationships retrieved correctly")

    print("[PASS] Get Relationships")


def test_get_status():
    """Test character status reporting."""
    print("\n[TEST] Get Status")

    profile = create_test_profile()
    consultant = CharacterConsultant(profile)

    status = consultant.get_status()

    assert isinstance(status, dict), "Status should be dict"
    assert "name" in status, "Missing name"
    assert "dnd_class" in status, "Missing dnd_class"
    assert "level" in status, "Missing level"
    assert "personality_traits" in status, "Missing personality_traits"
    assert status["name"] == "Test Character", "Wrong name"
    assert status["level"] == 5, "Wrong level"
    assert status["dnd_class"] == "Wizard", "Wrong class"
    print("  [OK] Status structure correct")

    print("[PASS] Get Status")


def test_delegation_to_dc_calculator():
    """Test that DC calculations are delegated correctly."""
    print("\n[TEST] Delegation to DC Calculator")

    profile = create_test_profile()
    consultant = CharacterConsultant(profile)

    result = consultant.suggest_dc_for_action("cast a spell")

    assert "suggested_dc" in result, "Missing suggested_dc value"
    assert "action_type" in result, "Missing action_type"
    assert isinstance(result["suggested_dc"], int), "DC should be integer"
    assert result["suggested_dc"] > 0, "DC should be positive"
    print("  [OK] DC calculation delegated correctly")

    print("[PASS] Delegation to DC Calculator")


def test_delegation_to_story_analyzer():
    """Test that story analysis is delegated correctly."""
    print("\n[TEST] Delegation to Story Analyzer")

    profile = create_test_profile()
    consultant = CharacterConsultant(profile)

    story_text = "The character carefully analyzes the situation before acting."
    character_actions = ["Analyzes the situation carefully"]

    result = consultant.analyze_story_consistency(story_text, character_actions)

    assert "character" in result, "Missing character field"
    assert "consistency_score" in result, "Missing consistency score"
    assert "overall_rating" in result, "Missing overall rating"
    assert "issues" in result, "Missing issues"
    assert result["character"] == "Test Character", "Wrong character"
    print("  [OK] Story analysis delegated correctly")

    print("[PASS] Delegation to Story Analyzer")


def test_different_class_behaviors():
    """Test that different classes have different behaviors."""
    print("\n[TEST] Different Class Behaviors")

    # Create Barbarian
    barb_profile = create_test_profile(DnDClass.BARBARIAN)
    barb_consultant = CharacterConsultant(barb_profile)

    # Create Wizard
    wiz_profile = create_test_profile(DnDClass.WIZARD)
    wiz_consultant = CharacterConsultant(wiz_profile)

    situation = "An enemy approaches!"

    barb_reaction = barb_consultant.suggest_reaction(situation)
    wiz_reaction = wiz_consultant.suggest_reaction(situation)

    # Reactions should differ based on class
    assert barb_reaction["class_reaction"] != wiz_reaction["class_reaction"], \
        "Different classes should have different reactions"
    print("  [OK] Class-specific reactions differ")

    print("[PASS] Different Class Behaviors")


def test_load_from_file():
    """Test loading consultant from character file."""
    print("\n[TEST] Load Consultant from File")

    # Create temporary character file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name

    try:
        # Save profile
        profile = create_test_profile()
        profile.save_to_file(temp_path)

        # Load consultant from file
        consultant = CharacterConsultant.load_from_file(temp_path)

        assert consultant.profile.name == "Test Character", "Name not loaded"
        assert consultant.profile.level == 5, "Level not loaded"
        assert len(consultant.profile.known_spells) == 3, "Spells not loaded"
        print("  [OK] Consultant loaded from file correctly")

    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    print("[PASS] Load Consultant from File")


def run_all_tests():
    """Run all consultant core tests."""
    print("=" * 70)
    print("CHARACTER CONSULTANT CORE TESTS")
    print("=" * 70)

    test_consultant_initialization()
    test_suggest_reaction_threat()
    test_suggest_reaction_puzzle()
    test_suggest_reaction_social()
    test_suggest_reaction_magic()
    test_get_personality_modifier()
    test_check_consistency_factors()
    test_get_all_character_items()
    test_get_relationships()
    test_get_status()
    test_delegation_to_dc_calculator()
    test_delegation_to_story_analyzer()
    test_different_class_behaviors()
    test_load_from_file()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL CONSULTANT CORE TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
