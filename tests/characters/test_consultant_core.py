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

from tests import test_helpers

# Configure project root and import production symbols via test_helpers
project_root = test_helpers.setup_test_environment()

CharacterConsultant = test_helpers.safe_from_import(
    "src.characters.consultants.consultant_core", "CharacterConsultant"
)
CharacterProfile = test_helpers.safe_from_import(
    "src.characters.consultants.character_profile", "CharacterProfile"
)
DnDClass = test_helpers.safe_from_import("src.characters.character_sheet", "DnDClass")

def test_character_profile_initialization():
    """Test loading Aragorn profile and consultant initialization."""
    aragorn_path = project_root / "game_data" / "characters" / "aragorn.json"
    profile = CharacterProfile.load_from_file(str(aragorn_path))
    consultant = CharacterConsultant(profile)
    assert profile.name == "Aragorn", "Name should be Aragorn"
    assert profile.character_class == DnDClass.RANGER, "Class should be ranger"
    assert profile.level == 10, "Level should be 10"
    assert consultant.profile == profile, "Consultant profile mismatch"
    assert consultant.class_knowledge is not None, "Class knowledge not loaded"
    assert consultant.dc_calculator is not None, "DC calculator not initialized"
    assert consultant.story_analyzer is not None, "Story analyzer not initialized"
    assert consultant.ai_consultant is not None, "AI consultant not initialized"
    print("  [OK] Aragorn profile and consultant initialized")
    assert consultant.ai_consultant is not None, "AI consultant not initialized"
    print("  [OK] Aragorn profile and consultant initialized")


def test_consultant_initialization():
    """Test CharacterConsultant initialization with Aragorn."""
    print("\n[TEST] CharacterConsultant Initialization")
    aragorn_path = project_root / "game_data" / "characters" / "aragorn.json"
    profile = CharacterProfile.load_from_file(str(aragorn_path))
    consultant = CharacterConsultant(profile)
    assert consultant.profile == profile, "Profile not set correctly"
    assert consultant.class_knowledge is not None, "Class knowledge not loaded"
    assert consultant.dc_calculator is not None, "DC calculator not initialized"
    assert consultant.story_analyzer is not None, "Story analyzer not initialized"
    assert consultant.ai_consultant is not None, "AI consultant not initialized"
    print("  [OK] All components initialized")
    # Verify class knowledge is correct
    assert consultant.class_knowledge["primary_ability"] == "Dexterity and Wisdom", \
        "Ranger should use Dexterity and Wisdom"
    print("  [OK] Class knowledge loaded correctly")
    print("[PASS] CharacterConsultant Initialization")


def test_suggest_reaction_threat():
    """Test reaction suggestions for threat situations."""
    print("\n[TEST] Suggest Reaction - Threat")
    aragorn_path = project_root / "game_data" / "characters" / "aragorn.json"
    profile = CharacterProfile.load_from_file(str(aragorn_path))
    consultant = CharacterConsultant(profile)
    result = consultant.suggest_reaction("A dragon attacks the party!")
    assert "character" in result, "Missing character field"
    assert "class_reaction" in result, "Missing class reaction"
    assert "personality_modifier" in result, "Missing personality modifier"
    assert "suggested_approach" in result, "Missing suggested approach"
    assert "dialogue_suggestion" in result, "Missing dialogue suggestion"
    assert "consistency_notes" in result, "Missing consistency notes"
    assert result["character"] == "Aragorn", "Wrong character name"
    print("  [OK] Threat reaction structure correct")
    print("[PASS] Suggest Reaction - Threat")



def test_suggest_reaction_puzzle():
    """Test reaction suggestions for puzzle situations."""
    print("\n[TEST] Suggest Reaction - Puzzle")
    aragorn_path = project_root / "game_data" / "characters" / "aragorn.json"
    profile = CharacterProfile.load_from_file(str(aragorn_path))
    consultant = CharacterConsultant(profile)
    result = consultant.suggest_reaction("You encounter a mysterious riddle")
    assert "class_reaction" in result, "Missing class reaction"
    assert "suggested_approach" in result, "Missing suggested approach"
    print("  [OK] Puzzle reaction structure correct")
    print("[PASS] Suggest Reaction - Puzzle")



def test_suggest_reaction_social():
    """Test reaction suggestions for social situations."""
    print("\n[TEST] Suggest Reaction - Social")
    aragorn_path = project_root / "game_data" / "characters" / "aragorn.json"
    profile = CharacterProfile.load_from_file(str(aragorn_path))
    consultant = CharacterConsultant(profile)
    result = consultant.suggest_reaction("You need to persuade the guard")
    assert "class_reaction" in result, "Missing class reaction"
    assert "dialogue_suggestion" in result, "Missing dialogue suggestion"
    print("  [OK] Social reaction structure correct")
    print("[PASS] Suggest Reaction - Social")



def test_suggest_reaction_magic():
    """Test reaction suggestions for magic situations."""
    print("\n[TEST] Suggest Reaction - Magic")
    aragorn_path = project_root / "game_data" / "characters" / "aragorn.json"
    profile = CharacterProfile.load_from_file(str(aragorn_path))
    consultant = CharacterConsultant(profile)
    result = consultant.suggest_reaction("You sense magical energy nearby")
    assert "class_reaction" in result, "Missing class reaction"
    assert "suggested_approach" in result, "Missing suggested approach"
    print("  [OK] Magic reaction structure correct")
    print("[PASS] Suggest Reaction - Magic")



def test_get_personality_modifier():
    """Test personality modifier generation."""
    print("\n[TEST] Get Personality Modifier")
    aragorn_path = project_root / "game_data" / "characters" / "aragorn.json"
    profile = CharacterProfile.load_from_file(str(aragorn_path))
    consultant = CharacterConsultant(profile)
    modifier = consultant.get_personality_modifier("threat")
    assert isinstance(modifier, str), "Modifier should be string"
    assert len(modifier) > 0, "Modifier should not be empty"
    print("  [OK] Personality modifier generated")
    print("[PASS] Get Personality Modifier")



def test_check_consistency_factors():
    """Test consistency factor checking."""
    print("\n[TEST] Check Consistency Factors")
    aragorn_path = project_root / "game_data" / "characters" / "aragorn.json"
    profile = CharacterProfile.load_from_file(str(aragorn_path))
    consultant = CharacterConsultant(profile)
    factors = consultant.check_consistency_factors("rushing into battle")
    assert isinstance(factors, list), "Factors should be list"
    assert len(factors) > 0, "Should detect consistency issue"
    print(f"  [OK] Found {len(factors)} consistency factors")
    print("[PASS] Check Consistency Factors")


def test_get_all_character_items():
    """Test retrieval of all character items."""
    print("\n[TEST] Get All Character Items")

    # Create profile with equipment
    profile = test_helpers.make_profile(
        name="Equipped Character",
        dnd_class=DnDClass.FIGHTER,
        level=5,
        weapons=["Longsword", "Shield"],
        armor=["Plate Armor"],
        items_list=["Rope", "Torch"],
        magic_items=["Ring of Protection"],
        speech_patterns=["measured, formal"],
    )
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

    profile = test_helpers.make_profile(
        name="Social Character",
        dnd_class=DnDClass.BARD,
        level=3,
        speech_patterns=["charming, musical"],
        relationships={"NPC1": "Friend", "NPC2": "Rival"},
    )
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
    aragorn_path = project_root / "game_data" / "characters" / "aragorn.json"
    profile = CharacterProfile.load_from_file(str(aragorn_path))
    consultant = CharacterConsultant(profile)
    status = consultant.get_status()
    assert isinstance(status, dict), "Status should be dict"
    assert "name" in status, "Missing name"
    assert "dnd_class" in status, "Missing dnd_class"
    assert "level" in status, "Missing level"
    assert "personality_traits" in status, "Missing personality_traits"
    assert status["name"] == "Aragorn", "Wrong name"
    # Match the expected level from the loaded profile (may change in canonical file)
    assert status["level"] == profile.level, "Wrong level"
    assert status["dnd_class"] == "Ranger", "Wrong class"
    print("  [OK] Status structure correct")
    print("[PASS] Get Status")



def test_delegation_to_dc_calculator():
    """Test that DC calculations are delegated correctly."""
    print("\n[TEST] Delegation to DC Calculator")
    aragorn_path = project_root / "game_data" / "characters" / "aragorn.json"
    profile = CharacterProfile.load_from_file(str(aragorn_path))
    consultant = CharacterConsultant(profile)
    result = consultant.suggest_dc_for_action("track an enemy")
    assert "suggested_dc" in result, "Missing suggested_dc value"
    assert "action_type" in result, "Missing action_type"
    assert isinstance(result["suggested_dc"], int), "DC should be integer"
    assert result["suggested_dc"] > 0, "DC should be positive"
    print("  [OK] DC calculation delegated correctly")
    print("[PASS] Delegation to DC Calculator")



def test_delegation_to_story_analyzer():
    """Test that story analysis is delegated correctly."""
    print("\n[TEST] Delegation to Story Analyzer")
    aragorn_path = project_root / "game_data" / "characters" / "aragorn.json"
    profile = CharacterProfile.load_from_file(str(aragorn_path))
    consultant = CharacterConsultant(profile)
    story_text = "Aragorn carefully analyzes the situation before acting."
    character_actions = ["Analyzes the situation carefully"]
    result = consultant.analyze_story_consistency(story_text, character_actions)
    assert "character" in result, "Missing character field"
    assert "consistency_score" in result, "Missing consistency score"
    assert "overall_rating" in result, "Missing overall rating"
    assert "issues" in result, "Missing issues"
    assert result["character"] == "Aragorn", "Wrong character"
    print("  [OK] Story analysis delegated correctly")
    print("[PASS] Delegation to Story Analyzer")


def test_different_class_behaviors():
    """Test that different classes have different behaviors."""
    print("\n[TEST] Different Class Behaviors")

    # Load canonical profiles for different classes
    aragorn_profile = CharacterProfile.load_from_file(str(project_root /
        "game_data" / "characters" / "aragorn.json"))
    frodo_profile = CharacterProfile.load_from_file(str(project_root /
        "game_data" / "characters" / "frodo.json"))
    gandalf_profile = CharacterProfile.load_from_file(str(project_root /
        "game_data" / "characters" / "gandalf.json"))

    aragorn_consultant = CharacterConsultant(aragorn_profile)
    frodo_consultant = CharacterConsultant(frodo_profile)
    gandalf_consultant = CharacterConsultant(gandalf_profile)

    situation = "An enemy approaches!"

    aragorn_reaction = aragorn_consultant.suggest_reaction(situation)
    frodo_reaction = frodo_consultant.suggest_reaction(situation)
    gandalf_reaction = gandalf_consultant.suggest_reaction(situation)

    # Reactions should differ based on class
    assert aragorn_reaction["class_reaction"] != frodo_reaction["class_reaction"], \
        "Ranger and Rogue should have different reactions"
    assert gandalf_reaction["class_reaction"] != aragorn_reaction["class_reaction"], \
        "Wizard and Ranger should have different reactions"
    print("  [OK] Class-specific reactions differ")
    print("[PASS] Different Class Behaviors")


def test_load_from_file():
    """Test loading consultant from Aragorn character file."""
    print("\n[TEST] Load Consultant from File")
    aragorn_path = project_root / "game_data" / "characters" / "aragorn.json"
    consultant = CharacterConsultant.load_from_file(str(aragorn_path))
    assert consultant.profile.name == "Aragorn", "Name not loaded"
    assert consultant.profile.level == 10, "Level not loaded"
    assert "Hunter's Mark" in consultant.profile.known_spells, "Spells not loaded"
    print("  [OK] Consultant loaded from file correctly")
    print("[PASS] Load Consultant from File")



def run_all_tests():
    """Run all consultant core tests."""
    print("=" * 70)
    print("CHARACTER CONSULTANT CORE TESTS")
    print("=" * 70)
    test_character_profile_initialization()
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
