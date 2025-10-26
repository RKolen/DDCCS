"""
Hooks and Analysis Tests

Tests for story hooks file generation and NPC suggestions.
"""

import os
import tempfile

from tests import test_helpers

# Configure test environment and import target symbol via centralized helper
create_story_hooks_file = test_helpers.safe_from_import(
    "src.stories.hooks_and_analysis", "create_story_hooks_file"
)


def test_create_story_hooks_basic():
    """Test creating basic story hooks file."""
    print("\n[TEST] Create Story Hooks - Basic")

    with tempfile.TemporaryDirectory() as temp_dir:
        hooks = [
            "The mysterious stranger's warning about the coming storm",
            "The sealed door in the basement remains unopened",
            "Mayor's daughter is still missing",
        ]

        filepath = create_story_hooks_file(
            temp_dir, "The Tavern Mystery", hooks, session_date="2024-01-15"
        )

        assert os.path.exists(filepath), "File should be created"

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Story Hooks & Future Sessions: The Tavern Mystery" in content
        assert "2024-01-15" in content
        assert "Unresolved Plot Threads" in content
        assert "mysterious stranger" in content
        assert "sealed door" in content
        assert "Mayor's daughter" in content
        print("  [OK] Basic story hooks file created")

    print("[PASS] Create Story Hooks - Basic")


def test_create_story_hooks_with_npcs():
    """Test creating story hooks file with NPC suggestions."""
    print("\n[TEST] Create Story Hooks - With NPCs")

    with tempfile.TemporaryDirectory() as temp_dir:
        hooks = ["Investigate the warehouse"]

        npc_suggestions = [
            {
                "name": "Marcus",
                "role": "Blacksmith",
                "context_excerpt": (
                    "Marcus, the blacksmith, mentioned seeing "
                    "suspicious activity near the old warehouse "
                    "late at night. He seemed nervous."
                ),
                "filename": "marcus.json",
            },
            {
                "name": "Sarah",
                "role": "Merchant",
                "context_excerpt": (
                    "Sarah, a traveling merchant, offered to sell "
                    "them information about the local guild."
                ),
                "filename": "sarah.json",
            },
        ]

        filepath = create_story_hooks_file(
            temp_dir,
            "Guild Intrigue",
            hooks,
            session_date="2024-02-20",
            npc_suggestions=npc_suggestions,
        )

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        assert "NPC Profile Suggestions" in content
        assert "Marcus" in content
        assert "Blacksmith" in content
        assert "Sarah" in content
        assert "Merchant" in content
        assert "marcus.json" in content
        assert "sarah.json" in content
        assert "generate_npc_from_story" in content
        print("  [OK] Story hooks with NPC suggestions created")

    print("[PASS] Create Story Hooks - With NPCs")


def test_create_story_hooks_default_date():
    """Test creating story hooks with default date."""
    print("\n[TEST] Create Story Hooks - Default Date")

    with tempfile.TemporaryDirectory() as temp_dir:
        hooks = ["Follow up on the clue"]

        filepath = create_story_hooks_file(temp_dir, "Test Story", hooks)

        assert os.path.exists(filepath), "File should be created"
        filename = os.path.basename(filepath)
        assert filename.startswith("story_hooks_"), "Should have correct prefix"
        assert "test_story" in filename, "Should include story name"
        print("  [OK] Default date handling works")

    print("[PASS] Create Story Hooks - Default Date")


def test_create_story_hooks_filename_format():
    """Test that filename is correctly formatted."""
    print("\n[TEST] Create Story Hooks - Filename Format")

    with tempfile.TemporaryDirectory() as temp_dir:
        hooks = ["Test hook"]

        filepath = create_story_hooks_file(
            temp_dir,
            "The Dragon's Lair",
            hooks,
            session_date="2024-03-10",
        )

        filename = os.path.basename(filepath)
        expected = "story_hooks_2024-03-10_the_dragon's_lair.md"
        assert filename == expected, f"Expected {expected}, got {filename}"
        print("  [OK] Filename formatted correctly")

    print("[PASS] Create Story Hooks - Filename Format")


def test_create_story_hooks_empty_hooks():
    """Test creating file with no hooks."""
    print("\n[TEST] Create Story Hooks - Empty Hooks")

    with tempfile.TemporaryDirectory() as temp_dir:
        hooks = []

        filepath = create_story_hooks_file(
            temp_dir, "No Hooks", hooks, session_date="2024-04-01"
        )

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Unresolved Plot Threads" in content
        assert "Potential Next Sessions" in content
        print("  [OK] Empty hooks handled correctly")

    print("[PASS] Create Story Hooks - Empty Hooks")


def test_create_story_hooks_sections_present():
    """Test that all standard sections are present."""
    print("\n[TEST] Create Story Hooks - All Sections")

    with tempfile.TemporaryDirectory() as temp_dir:
        hooks = ["Test hook"]

        filepath = create_story_hooks_file(
            temp_dir, "Test", hooks, session_date="2024-05-15"
        )

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Unresolved Plot Threads" in content
        assert "Potential Next Sessions" in content
        assert "Session Ideas" in content
        assert "NPC Follow-ups" in content
        assert "Location Hooks" in content
        assert "Faction Developments" in content
        print("  [OK] All standard sections present")

    print("[PASS] Create Story Hooks - All Sections")


def test_create_story_hooks_npc_context_truncated():
    """Test that long NPC context is truncated."""
    print("\n[TEST] Create Story Hooks - NPC Context Truncation")

    with tempfile.TemporaryDirectory() as temp_dir:
        hooks = ["Hook"]

        long_context = "A" * 300  # Long context string
        npc_suggestions = [
            {
                "name": "LongStory",
                "role": "Talkative NPC",
                "context_excerpt": long_context,
                "filename": "longstory.json",
            }
        ]

        filepath = create_story_hooks_file(
            temp_dir, "Test", hooks, npc_suggestions=npc_suggestions
        )

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Context should be truncated to 150 chars + "..."
        assert "A" * 150 + "..." in content
        assert "A" * 200 not in content
        print("  [OK] NPC context truncated to 150 characters")

    print("[PASS] Create Story Hooks - NPC Context Truncation")


def run_all_tests():
    """Run all hooks and analysis tests."""
    print("=" * 70)
    print("HOOKS AND ANALYSIS TESTS")
    print("=" * 70)

    test_create_story_hooks_basic()
    test_create_story_hooks_with_npcs()
    test_create_story_hooks_default_date()
    test_create_story_hooks_filename_format()
    test_create_story_hooks_empty_hooks()
    test_create_story_hooks_sections_present()
    test_create_story_hooks_npc_context_truncated()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL HOOKS AND ANALYSIS TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
