"""
NPC Auto-Detection Tests

Tests for automatic NPC detection and profile generation.
"""

import os
import tempfile
from pathlib import Path

# Use test_helpers to set up environment and import required symbols
from tests import test_helpers
(
    detect_npc_suggestions,
    generate_npc_from_story,
    save_npc_profile,
    _create_fallback_profile,
) = test_helpers.safe_from_import(
    "src.npcs.npc_auto_detection",
    "detect_npc_suggestions",
    "generate_npc_from_story",
    "save_npc_profile",
    "_create_fallback_profile",
)


def test_detect_npc_innkeeper_named():
    """Test detecting innkeeper with 'named' keyword."""
    print("\n[TEST] Detect NPC - Innkeeper Named")

    story = """
    The party entered the tavern. The innkeeper named Garrett greeted them
    warmly and showed them to a table.
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        suggestions = detect_npc_suggestions(story, [], temp_dir)

        assert len(suggestions) == 1, "Should detect 1 NPC"
        assert suggestions[0]["name"] == "Garrett", "Name incorrect"
        assert suggestions[0]["role"] == "Innkeeper", "Role incorrect"
        assert "Garrett" in suggestions[0]["context_excerpt"]
        print("  [OK] Innkeeper detected with 'named' keyword")

    print("[PASS] Detect NPC - Innkeeper Named")


def test_detect_npc_innkeeper_the():
    """Test detecting innkeeper with 'the innkeeper' pattern."""
    print("\n[TEST] Detect NPC - The Innkeeper Pattern")

    story = """
    Marcus, the innkeeper, wiped down the bar and listened to the
    party's request for rooms.
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        suggestions = detect_npc_suggestions(story, [], temp_dir)

        assert len(suggestions) == 1, "Should detect 1 NPC"
        assert suggestions[0]["name"] == "Marcus", "Name incorrect"
        assert suggestions[0]["role"] == "Innkeeper", "Role incorrect"
        print("  [OK] Innkeeper detected with 'the innkeeper' pattern")

    print("[PASS] Detect NPC - The Innkeeper Pattern")


def test_detect_npc_merchant():
    """Test detecting merchant NPCs."""
    print("\n[TEST] Detect NPC - Merchant")

    story = """
    The party visited the merchant named Sarah who sold them potions
    and supplies for their journey.
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        suggestions = detect_npc_suggestions(story, [], temp_dir)

        assert len(suggestions) == 1, "Should detect 1 NPC"
        assert suggestions[0]["name"] == "Sarah", "Name incorrect"
        assert suggestions[0]["role"] == "Merchant", "Role incorrect"
        print("  [OK] Merchant detected")

    print("[PASS] Detect NPC - Merchant")


def test_detect_npc_guard_captain():
    """Test detecting guard captain NPCs."""
    print("\n[TEST] Detect NPC - Guard Captain")

    story = """
    The guard captain named Thomas approached and questioned them
    about their business in the city.
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        suggestions = detect_npc_suggestions(story, [], temp_dir)

        assert len(suggestions) == 1, "Should detect 1 NPC"
        assert suggestions[0]["name"] == "Thomas", "Name incorrect"
        assert suggestions[0]["role"] == "Guard Captain", "Role incorrect"
        print("  [OK] Guard captain detected")

    print("[PASS] Detect NPC - Guard Captain")


def test_detect_npc_blacksmith():
    """Test detecting blacksmith NPCs (both patterns)."""
    print("\n[TEST] Detect NPC - Blacksmith")

    story1 = "The blacksmith named Dorn repaired their weapons."
    story2 = "Elena, the blacksmith, showed them her finest work."

    with tempfile.TemporaryDirectory() as temp_dir:
        suggestions1 = detect_npc_suggestions(story1, [], temp_dir)
        suggestions2 = detect_npc_suggestions(story2, [], temp_dir)

        assert len(suggestions1) == 1, "Should detect blacksmith (named)"
        assert suggestions1[0]["name"] == "Dorn"
        print("  [OK] Blacksmith detected with 'named' pattern")

        assert len(suggestions2) == 1, "Should detect blacksmith (the)"
        assert suggestions2[0]["name"] == "Elena"
        print("  [OK] Blacksmith detected with 'the blacksmith' pattern")

    print("[PASS] Detect NPC - Blacksmith")


def test_detect_npc_multiple():
    """Test detecting multiple NPCs in one story."""
    print("\n[TEST] Detect NPC - Multiple NPCs")

    story = """
    The innkeeper named Garrett directed them to the blacksmith called
    Marcus. Later they met the merchant named Sarah at the market.
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        suggestions = detect_npc_suggestions(story, [], temp_dir)

        assert len(suggestions) == 3, "Should detect 3 NPCs"
        names = [s["name"] for s in suggestions]
        assert "Garrett" in names, "Garrett not detected"
        assert "Marcus" in names, "Marcus not detected"
        assert "Sarah" in names, "Sarah not detected"
        print("  [OK] All 3 NPCs detected")

    print("[PASS] Detect NPC - Multiple NPCs")


def test_detect_npc_exclude_party():
    """Test that party members are excluded from detection."""
    print("\n[TEST] Detect NPC - Exclude Party Members")

    story = """
    The innkeeper named Garrett greeted Theron warmly. Theron ordered
    ale for the group.
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        party_names = ["Theron", "Kael", "Lyra"]
        suggestions = detect_npc_suggestions(story, party_names, temp_dir)

        assert len(suggestions) == 1, "Should detect only 1 NPC"
        assert suggestions[0]["name"] == "Garrett", "Should detect Garrett"
        names = [s["name"] for s in suggestions]
        assert "Theron" not in names, "Party member should be excluded"
        print("  [OK] Party members excluded from detection")

    print("[PASS] Detect NPC - Exclude Party Members")


def test_detect_npc_false_positives():
    """Test that common false positives are filtered."""
    print("\n[TEST] Detect NPC - Filter False Positives")

    story = """
    The innkeeper called to the party. Then the merchant spoke to
    them about prices.
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        suggestions = detect_npc_suggestions(story, [], temp_dir)

        # Should not detect articles or common words
        names = [s["name"] for s in suggestions]
        assert "The" not in names, "Article should be filtered"
        assert "Then" not in names, "Common word should be filtered"
        print("  [OK] False positives filtered correctly")

    print("[PASS] Detect NPC - Filter False Positives")


def test_detect_npc_existing_profile():
    """Test that NPCs with existing profiles are not suggested."""
    print("\n[TEST] Detect NPC - Skip Existing Profiles")

    story = "The innkeeper named Garrett welcomed them."

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create existing NPC file (sanitized: lowercase)
        npcs_dir = Path(temp_dir) / "game_data" / "npcs"
        npcs_dir.mkdir(parents=True, exist_ok=True)
        existing_npc = npcs_dir / "garrett.json"
        existing_npc.write_text('{"name": "Garrett"}', encoding="utf-8")

        suggestions = detect_npc_suggestions(story, [], temp_dir)

        assert len(suggestions) == 0, "Existing NPC should not be suggested"
        print("  [OK] Existing NPC profile skipped")

    print("[PASS] Detect NPC - Skip Existing Profiles")


def test_detect_npc_context_excerpt():
    """Test that context excerpt is provided."""
    print("\n[TEST] Detect NPC - Context Excerpt")

    story = """
    The warm glow of the fireplace welcomed them. The innkeeper named
    Garrett, a portly man with a friendly smile, greeted each guest
    personally. He recommended the lamb stew.
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        suggestions = detect_npc_suggestions(story, [], temp_dir)

        assert len(suggestions) == 1, "Should detect 1 NPC"
        context = suggestions[0]["context_excerpt"]
        assert "Garrett" in context, "Context should mention NPC"
        assert len(context) > 0, "Context should not be empty"
        print("  [OK] Context excerpt provided")

    print("[PASS] Detect NPC - Context Excerpt")


def test_generate_npc_without_ai():
    """Test generating NPC profile without AI (fallback)."""
    print("\n[TEST] Generate NPC - Without AI")

    context = "The innkeeper named Garrett welcomed them warmly."
    npc_profile = generate_npc_from_story(
        "Garrett", context, role="Innkeeper", ai_client=None
    )

    assert npc_profile["name"] == "Garrett", "Name incorrect"
    assert npc_profile["role"] == "Innkeeper", "Role incorrect"
    assert npc_profile["species"] == "Human", "Default species incorrect"
    assert npc_profile["nickname"] is None, "Nickname should be None"
    assert npc_profile["recurring"] is False, "Default recurring incorrect"
    assert "ai_config" in npc_profile, "Should have ai_config"
    assert npc_profile["ai_config"]["enabled"] is False
    assert "placeholder" in npc_profile["notes"]
    print("  [OK] Fallback profile generated without AI")

    print("[PASS] Generate NPC - Without AI")


def test_create_fallback_profile():
    """Test fallback profile creation."""
    print("\n[TEST] Create Fallback Profile")

    profile = _create_fallback_profile(
        "TestNPC", "Merchant", "AI unavailable"
    )

    assert profile["name"] == "TestNPC", "Name incorrect"
    assert profile["role"] == "Merchant", "Role incorrect"
    assert profile["species"] == "Human", "Default species incorrect"
    assert "AI unavailable" in profile["notes"], "Error message not in notes"
    assert profile["ai_config"]["enabled"] is False
    print("  [OK] Fallback profile created correctly")

    print("[PASS] Create Fallback Profile")


def test_save_npc_profile_basic():
    """Test saving NPC profile to file."""
    print("\n[TEST] Save NPC Profile - Basic")

    npc_profile = {
        "name": "TestNPC",
        "nickname": None,
        "role": "Merchant",
        "species": "Human",
        "lineage": "",
        "personality": "Friendly",
        "relationships": {},
        "key_traits": ["Honest"],
        "abilities": ["Appraisal"],
        "recurring": False,
        "notes": "Test NPC",
        "ai_config": {
            "enabled": False,
            "temperature": 0.7,
            "max_tokens": 1000,
            "system_prompt": "",
        },
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        saved_path = save_npc_profile(npc_profile, temp_dir)

        assert os.path.exists(saved_path), "File should be created"
        # Filename is sanitized: "TestNPC" -> "testnpc.json"
        assert "testnpc.json" in saved_path.lower()
        print("  [OK] NPC profile saved to file")

    print("[PASS] Save NPC Profile - Basic")


def test_save_npc_profile_validation_warning():
    """Test that validation warnings are displayed but save proceeds."""
    print("\n[TEST] Save NPC Profile - Validation Warning")

    # Missing many required fields
    npc_profile = {
        "name": "Incomplete",
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        # Should save despite validation errors (fail-soft approach)
        saved_path = save_npc_profile(npc_profile, temp_dir)

        assert os.path.exists(saved_path), "File should be created anyway"
        print("  [OK] Save proceeds despite validation warnings")

    print("[PASS] Save NPC Profile - Validation Warning")


def run_all_tests():
    """Run all NPC auto-detection tests."""
    print("=" * 70)
    print("NPC AUTO-DETECTION TESTS")
    print("=" * 70)

    test_detect_npc_innkeeper_named()
    test_detect_npc_innkeeper_the()
    test_detect_npc_merchant()
    test_detect_npc_guard_captain()
    test_detect_npc_blacksmith()
    test_detect_npc_multiple()
    test_detect_npc_exclude_party()
    test_detect_npc_false_positives()
    test_detect_npc_existing_profile()
    test_detect_npc_context_excerpt()
    test_generate_npc_without_ai()
    test_create_fallback_profile()
    test_save_npc_profile_basic()
    test_save_npc_profile_validation_warning()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL NPC AUTO-DETECTION TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
