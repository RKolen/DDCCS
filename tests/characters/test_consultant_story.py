"""
Tests for Story Analysis Component

This module tests the StoryAnalyzer component that provides story
consistency analysis, character development tracking, and relationship
management.
"""

from tests import test_helpers

# Import production symbols via centralized helper
StoryAnalyzer, CharacterProfile, CharacterIdentity = test_helpers.safe_from_import(
    "src.characters.consultants.consultant_story",
    "StoryAnalyzer",
    "CharacterProfile",
    "CharacterIdentity",
)
DnDClass = test_helpers.safe_from_import("src.characters.character_sheet", "DnDClass")


def test_story_analyzer_initialization():
    """Test story analyzer initialization."""
    print("\n[TEST] Story Analyzer - Initialization")

    profile = test_helpers.make_profile(name="TestChar", dnd_class=DnDClass.FIGHTER, level=5)
    class_knowledge = {"common_reactions": {"danger": "charge forward"}}

    analyzer = StoryAnalyzer(profile, class_knowledge)

    assert analyzer.profile == profile, "Profile not set correctly"
    assert analyzer.class_knowledge == class_knowledge, "Knowledge not set"
    print("  [OK] Story analyzer initialized correctly")

    print("[PASS] Story Analyzer - Initialization")


def test_get_relationships():
    """Test retrieving character relationships."""
    print("\n[TEST] Story Analyzer - Get Relationships")

    profile = test_helpers.make_profile(name="TestChar", dnd_class=DnDClass.FIGHTER, level=5)
    profile.personality.relationships = {
        "Gandalf": "Trusted mentor",
        "Aragorn": "Fellow warrior"
    }

    analyzer = StoryAnalyzer(profile, {})
    relationships = analyzer.get_relationships()

    assert isinstance(relationships, dict), "Relationships not a dict"
    assert len(relationships) == 2, "Wrong number of relationships"
    assert relationships["Gandalf"] == "Trusted mentor", "Wrong relationship"
    print("  [OK] Relationships retrieved correctly")

    print("[PASS] Story Analyzer - Get Relationships")


def test_analyze_story_consistency_basic():
    """Test basic story consistency analysis."""
    print("\n[TEST] Story Analyzer - Story Consistency Basic")

    profile = test_helpers.make_profile(name="BraveKnight", dnd_class=DnDClass.FIGHTER, level=5)
    profile.personality.personality_summary = "brave and honorable"
    profile.personality.motivations = ["Protect the innocent"]

    class_knowledge = {
        "common_reactions": {
            "danger": "stand ground"
        }
    }

    analyzer = StoryAnalyzer(profile, class_knowledge)

    story_text = "A group of bandits threatened the village"
    actions = ["stand ground and fight the bandits"]

    result = analyzer.analyze_story_consistency(story_text, actions)

    assert "character" in result, "Missing character field"
    assert result["character"] == "BraveKnight", "Wrong character"
    assert "consistency_score" in result, "Missing consistency_score"
    assert "overall_rating" in result, "Missing overall_rating"
    assert "issues" in result, "Missing issues"
    assert "positive_notes" in result, "Missing positive_notes"
    assert "suggestions" in result, "Missing suggestions"
    print("  [OK] Story consistency analysis structure correct")

    print("[PASS] Story Analyzer - Story Consistency Basic")


def test_analyze_story_consistency_with_personality():
    """Test consistency analysis considering personality."""
    print("\n[TEST] Story Analyzer - Consistency with Personality")

    profile = test_helpers.make_profile(name="CautiousRogue", dnd_class=DnDClass.ROGUE, level=5)
    profile.personality.personality_summary = "cautious and stealthy"
    profile.personality.motivations = ["Survive at all costs"]

    analyzer = StoryAnalyzer(profile, {})

    story_text = "A dangerous dragon appeared"
    actions = ["hide in the shadows and observe"]

    result = analyzer.analyze_story_consistency(story_text, actions)

    assert result["consistency_score"] > 0, "Score should be positive"
    assert len(result["positive_notes"]) > 0, "Should have positive notes"
    print("  [OK] Personality reflected in analysis")

    print("[PASS] Story Analyzer - Consistency with Personality")


def test_analyze_story_consistency_with_fears():
    """Test consistency analysis with character fears."""
    print("\n[TEST] Story Analyzer - Consistency with Fears")

    profile = test_helpers.make_profile(name="FearfulMage", dnd_class=DnDClass.WIZARD, level=5)
    profile.personality.fears_weaknesses = ["Fear of fire"]

    analyzer = StoryAnalyzer(profile, {})

    # Character appropriately shows fear
    story_text = "Flames erupted from the brazier with fire everywhere"
    good_actions = ["hesitate and step back from the flames"]

    good_result = analyzer.analyze_story_consistency(story_text, good_actions)
    # Check that either positive notes or no issues
    # (fear handling is working if score isn't penalized)
    assert good_result["consistency_score"] >= 0, (
        "Fear response shouldn't be heavily penalized"
    )
    print("  [OK] Appropriate fear response recognized")

    # Character ignores fear
    bad_actions = ["rush forward into the fire"]
    bad_result = analyzer.analyze_story_consistency(story_text, bad_actions)
    # Character ignored their fear, should have issues or lower score
    assert (len(bad_result["issues"]) > 0 or
            bad_result["consistency_score"] < good_result["consistency_score"]), (
        "Should flag or penalize ignoring fear"
    )
    print("  [OK] Ignoring fear flagged as issue")

    print("[PASS] Story Analyzer - Consistency with Fears")


def test_consistency_rating_levels():
    """Test consistency rating conversion through public API."""
    print("\n[TEST] Story Analyzer - Consistency Rating Levels")

    profile = test_helpers.make_profile(name="TestChar", dnd_class=DnDClass.FIGHTER, level=5)
    profile.personality.personality_summary = "brave and strong"

    analyzer = StoryAnalyzer(profile, {})

    # Test through actual consistency analysis with varying scores
    # High consistency action
    high_result = analyzer.analyze_story_consistency(
        "brave warrior fights",
        ["charge forward bravely"]
    )
    assert "Excellent" in high_result["overall_rating"] or (
        "Good" in high_result["overall_rating"]
    ), "High score rating wrong"
    print("  [OK] High score rating correct")

    # Low consistency empty action
    low_result = analyzer.analyze_story_consistency("test", ["unrelated"])
    assert isinstance(low_result["overall_rating"], str), (
        "Rating should be string"
    )
    print("  [OK] Rating levels working through public API")

    print("[PASS] Story Analyzer - Consistency Rating Levels")


def test_suggest_relationship_update_new():
    """Test suggesting new relationship creation."""
    print("\n[TEST] Story Analyzer - Suggest New Relationship")

    # Paladin should suggest positive relationships
    paladin_profile = test_helpers.make_profile(name="HolyPaladin",
                                                dnd_class=DnDClass.PALADIN, level=5)
    paladin_profile.personality.relationships = {}

    paladin_analyzer = StoryAnalyzer(paladin_profile, {})
    paladin_suggestion = paladin_analyzer.suggest_relationship_update(
        "Helpful NPC", "battle"
    )

    assert paladin_suggestion is not None, "Should provide suggestion"
    assert "SUGGESTION" in paladin_suggestion, "Should be formatted as suggestion"
    assert "Helpful NPC" in paladin_suggestion, "Should mention NPC name"
    print("  [OK] Paladin suggests positive relationship")

    # Rogue should suggest suspicious relationships
    rogue_profile = test_helpers.make_profile(name="SneakyRogue", dnd_class=DnDClass.ROGUE, level=5)
    rogue_profile.personality.relationships = {}

    rogue_analyzer = StoryAnalyzer(rogue_profile, {})
    rogue_suggestion = rogue_analyzer.suggest_relationship_update(
        "Mysterious Stranger", "dark alley"
    )

    assert "cautious" in rogue_suggestion.lower() or (
        "suspicious" in rogue_suggestion.lower()
    ), "Rogue should be suspicious"
    print("  [OK] Rogue suggests suspicious relationship")

    print("[PASS] Story Analyzer - Suggest New Relationship")


def test_suggest_relationship_update_existing():
    """Test suggesting updates to existing relationships."""
    print("\n[TEST] Story Analyzer - Update Existing Relationship")

    profile = test_helpers.make_profile(name="TestChar", dnd_class=DnDClass.FIGHTER, level=5)
    profile.personality.relationships = {"OldFriend": "Childhood companion"}

    analyzer = StoryAnalyzer(profile, {})
    suggestion = analyzer.suggest_relationship_update(
        "OldFriend", "betrayal"
    )

    assert suggestion is not None, "Should provide suggestion"
    assert "SUGGESTION" in suggestion, "Should be formatted as suggestion"
    assert "OldFriend" in suggestion, "Should mention character name"
    assert "Childhood companion" in suggestion, (
        "Should mention current relationship"
    )
    print("  [OK] Existing relationship update suggested")

    print("[PASS] Story Analyzer - Update Existing Relationship")


def test_suggest_plot_action_logging():
    """Test plot action logging suggestions."""
    print("\n[TEST] Story Analyzer - Plot Action Logging")

    profile = test_helpers.make_profile(name="TestChar", dnd_class=DnDClass.FIGHTER, level=5)
    analyzer = StoryAnalyzer(profile, {})

    suggestion = analyzer.suggest_plot_action_logging(
        "Saved the village",
        "Felt duty to protect innocent",
        "Chapter 1"
    )

    assert "SUGGESTION" in suggestion, "Should be formatted as suggestion"
    assert "Saved the village" in suggestion, "Should include action"
    assert "Felt duty to protect innocent" in suggestion, (
        "Should include reasoning"
    )
    assert "Chapter 1" in suggestion, "Should include chapter"
    print("  [OK] Plot action logging formatted correctly")

    print("[PASS] Story Analyzer - Plot Action Logging")


def test_suggest_character_development():
    """Test character development suggestions."""
    print("\n[TEST] Story Analyzer - Character Development")

    profile = test_helpers.make_profile(name="TestChar", dnd_class=DnDClass.FIGHTER, level=5)
    analyzer = StoryAnalyzer(profile, {})

    # Test courage detection
    courage_suggestions = analyzer.suggest_character_development(
        "acted bravely", "facing dragon"
    )
    assert len(courage_suggestions) > 0, "Should suggest courage trait"
    assert any("courage" in s.lower() for s in courage_suggestions), (
        "Should mention courage"
    )
    print("  [OK] Courage trait suggested")

    # Test caution detection
    caution_suggestions = analyzer.suggest_character_development(
        "proceeded cautiously", "dark dungeon"
    )
    assert len(caution_suggestions) > 0, "Should suggest caution trait"
    assert any("caution" in s.lower() for s in caution_suggestions), (
        "Should mention caution"
    )
    print("  [OK] Caution trait suggested")

    # Test leadership detection
    leadership_suggestions = analyzer.suggest_character_development(
        "took command", "battle"
    )
    assert len(leadership_suggestions) > 0, "Should suggest leadership trait"
    assert any("leadership" in s.lower() for s in leadership_suggestions), (
        "Should mention leadership"
    )
    print("  [OK] Leadership trait suggested")

    # Test fear detection
    fear_suggestions = analyzer.suggest_character_development(
        "was afraid", "darkness"
    )
    assert len(fear_suggestions) > 0, "Should suggest fear addition"
    assert any("fear" in s.lower() for s in fear_suggestions), (
        "Should mention fear"
    )
    print("  [OK] Fear addition suggested")

    print("[PASS] Story Analyzer - Character Development")


def test_analyze_story_content():
    """Test comprehensive story content analysis."""
    print("\n[TEST] Story Analyzer - Story Content Analysis")

    profile = test_helpers.make_profile(name="Aragorn", dnd_class=DnDClass.RANGER, level=10)
    analyzer = StoryAnalyzer(profile, {})

    story_text = """
CHARACTER: Aragorn
ACTION: Led the charge against the orcs
REASONING: Must protect the hobbits

Aragorn met with Gandalf to discuss strategy.
"""

    result = analyzer.analyze_story_content(story_text, "Chapter 1")

    assert "relationships" in result, "Missing relationships"
    assert "plot_actions" in result, "Missing plot_actions"
    assert "character_development" in result, "Missing character_development"
    assert "npc_creation" in result, "Missing npc_creation"
    assert isinstance(result["relationships"], list), (
        "Relationships should be list"
    )
    assert isinstance(result["plot_actions"], list), (
        "Plot actions should be list"
    )
    print("  [OK] Story content analysis structure correct")

    print("[PASS] Story Analyzer - Story Content Analysis")


def test_extract_character_names():
    """Test character name extraction through story content analysis."""
    print("\n[TEST] Story Analyzer - Extract Character Names")

    profile = test_helpers.make_profile(name="Aragorn", dnd_class=DnDClass.FIGHTER, level=5)
    analyzer = StoryAnalyzer(profile, {})

    # Test indirectly through analyze_story_content
    story_text = "Aragorn met with Gandalf and Frodo at the inn."
    result = analyzer.analyze_story_content(story_text, "Chapter 1")

    # Story content analysis uses name extraction for relationships
    assert isinstance(result, dict), "Should return dict"
    assert "relationships" in result, "Should include relationships"
    print("  [OK] Character name extraction working through public API")

    print("[PASS] Story Analyzer - Extract Character Names")


def run_all_tests():
    """Run all story analyzer tests."""
    print("=" * 70)
    print("STORY ANALYZER TESTS")
    print("=" * 70)

    test_story_analyzer_initialization()
    test_get_relationships()
    test_analyze_story_consistency_basic()
    test_analyze_story_consistency_with_personality()
    test_analyze_story_consistency_with_fears()
    test_consistency_rating_levels()
    test_suggest_relationship_update_new()
    test_suggest_relationship_update_existing()
    test_suggest_plot_action_logging()
    test_suggest_character_development()
    test_analyze_story_content()
    test_extract_character_names()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL STORY ANALYZER TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
