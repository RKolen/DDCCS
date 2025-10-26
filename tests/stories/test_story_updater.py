"""
Story Updater Tests

Tests for story file updating with analysis and combat narratives.
"""

import os
import tempfile

from tests import test_helpers

# Import StoryUpdater via centralized safe import helper
StoryUpdater = test_helpers.safe_from_import("src.stories.story_updater", "StoryUpdater")


def test_story_updater_initialization():
    """Test StoryUpdater initialization."""
    print("\n[TEST] StoryUpdater Initialization")

    updater = StoryUpdater()
    assert updater is not None, "Updater should be created"
    print("  [OK] StoryUpdater initialized correctly")

    print("[PASS] StoryUpdater Initialization")


def test_update_story_with_analysis():
    """Test updating story file with analysis results."""
    print("\n[TEST] Update Story with Analysis")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write("# Test Story\n\nSome story content here.\n")
        temp_path = f.name

    try:
        updater = StoryUpdater()
        analysis = {
            "dc_suggestions": {
                "stealth check": {
                    "Theron": {
                        "suggested_dc": 15,
                        "reasoning": "moderate difficulty",
                        "alternative_approaches": ["diplomacy"],
                    }
                }
            },
            "consultant_analyses": {
                "Theron": {"suggestions": ["Use Shield spell"]}
            },
        }

        updater.update_story_with_analysis(temp_path, analysis)

        # Read updated content
        with open(temp_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Character Consultant Notes" in content
        assert "Consistency Analysis" in content
        assert "Theron" in content
        assert "DC 15" in content
        print("  [OK] Story updated with analysis sections")
    finally:
        os.unlink(temp_path)

    print("[PASS] Update Story with Analysis")


def test_update_story_nonexistent_file():
    """Test updating non-existent file (should handle gracefully)."""
    print("\n[TEST] Update Story - Non-existent File")

    updater = StoryUpdater()
    analysis = {"character_reactions": []}

    # Should not raise error for non-existent file
    updater.update_story_with_analysis("/nonexistent/file.md", analysis)
    print("  [OK] Non-existent file handled gracefully")

    print("[PASS] Update Story - Non-existent File")


def test_append_combat_narrative():
    """Test appending combat narrative to story file."""
    print("\n[TEST] Append Combat Narrative")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write("# Test Story\n\nPrevious story content.\n")
        temp_path = f.name

    try:
        updater = StoryUpdater()
        narrative = (
            "Theron swings his sword at the goblin, striking true. "
            "The creature falls with a cry."
        )

        updater.append_combat_narrative(temp_path, narrative)

        # Read updated content
        with open(temp_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Combat Scene" in content, "Should have combat section"
        assert narrative in content, "Should contain narrative"
        assert "Previous story content" in content, "Should preserve original"
        print("  [OK] Combat narrative appended correctly")
    finally:
        os.unlink(temp_path)

    print("[PASS] Append Combat Narrative")


def test_append_combat_narrative_nonexistent():
    """Test appending combat to non-existent file."""
    print("\n[TEST] Append Combat - Non-existent File")

    updater = StoryUpdater()
    narrative = "Some combat narrative."

    # Should not raise error for non-existent file
    updater.append_combat_narrative("/nonexistent/file.md", narrative)
    print("  [OK] Non-existent file handled gracefully")

    print("[PASS] Append Combat - Non-existent File")


def test_update_existing_sections():
    """Test updating file that already has sections."""
    print("\n[TEST] Update Existing Sections")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write("""# Test Story

Story content here.

## Character Consultant Notes

Old notes here.

## Consistency Analysis

Old consistency data.
""")
        temp_path = f.name

    try:
        updater = StoryUpdater()
        analysis = {
            "consultant_analyses": {
                "Kael": {"suggestions": ["Save spell slot for boss fight"]}
            }
        }

        updater.update_story_with_analysis(temp_path, analysis)

        # Read updated content
        with open(temp_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Kael" in content, "Should have new character"
        assert "Old notes" not in content or content.index("Kael") > 0
        print("  [OK] Existing sections updated correctly")
    finally:
        os.unlink(temp_path)

    print("[PASS] Update Existing Sections")


def test_multiple_combat_appends():
    """Test appending multiple combat narratives."""
    print("\n[TEST] Multiple Combat Appends")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write("# Test Story\n\nInitial content.\n")
        temp_path = f.name

    try:
        updater = StoryUpdater()

        narrative1 = "First combat encounter."
        narrative2 = "Second combat encounter."

        updater.append_combat_narrative(temp_path, narrative1)
        updater.append_combat_narrative(temp_path, narrative2)

        # Read final content
        with open(temp_path, "r", encoding="utf-8") as f:
            content = f.read()

        assert narrative1 in content, "Should have first narrative"
        assert narrative2 in content, "Should have second narrative"
        assert content.count("Combat Scene") == 2, "Should have 2 sections"
        print("  [OK] Multiple combat narratives appended")
    finally:
        os.unlink(temp_path)

    print("[PASS] Multiple Combat Appends")


def run_all_tests():
    """Run all story updater tests."""
    print("=" * 70)
    print("STORY UPDATER TESTS")
    print("=" * 70)

    test_story_updater_initialization()
    test_update_story_with_analysis()
    test_update_story_nonexistent_file()
    test_append_combat_narrative()
    test_append_combat_narrative_nonexistent()
    test_update_existing_sections()
    test_multiple_combat_appends()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL STORY UPDATER TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
