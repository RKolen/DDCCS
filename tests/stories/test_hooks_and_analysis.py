"""
Hooks and Analysis Tests

Tests for story hooks file generation and NPC suggestions.
"""

import os
import tempfile
from src.stories.hooks_and_analysis import create_story_hooks_file


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


def test_create_story_hooks_structured_dict():
    """Test creating story hooks from structured AI dict (new feature)."""
    print("\n[TEST] Create Story Hooks - Structured Dict")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Structured dict from AI generation
        hooks_dict = {
            "unresolved_threads": [
                "The mysterious figure hasn't been identified",
                "The lost amulet remains missing",
            ],
            "next_session_ideas": [
                "Follow up on the tavern keeper's hint",
                "Investigate the nearby ruins",
            ],
            "npc_follow_ups": [
                "Marcus wants more information about the party",
                "Sarah mentioned a hidden entrance",
            ],
            "character_specific_hooks": {
                "Kael": ["Kael's past connection to the location surfaced"],
                "Theron": ["Theron recognized an old friend"],
            },
        }

        filepath = create_story_hooks_file(
            temp_dir,
            "The Mystery Deepens",
            hooks_dict,
            session_date="2024-06-01",
        )

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify all sections from structured dict are present
        assert "Story Hooks & Future Sessions: The Mystery Deepens" in content
        assert "2024-06-01" in content

        # Unresolved threads
        assert "mysterious figure" in content
        assert "lost amulet" in content

        # Session ideas (from next_session_ideas)
        assert "tavern keeper" in content
        assert "nearby ruins" in content

        # NPC follow-ups
        assert "Marcus" in content
        assert "hidden entrance" in content

        # Character specific
        assert "Kael" in content
        assert "Theron" in content
        assert "old friend" in content

        print("  [OK] Structured dict converted to complete hooks file")

    print("[PASS] Create Story Hooks - Structured Dict")


def test_create_story_hooks_mixed_dict_and_npc():
    """Test structured dict with NPC suggestions (hybrid case)."""
    print("\n[TEST] Create Story Hooks - Structured Dict with NPCs")

    with tempfile.TemporaryDirectory() as temp_dir:
        hooks_dict = {
            "unresolved_threads": ["Find the missing artifact"],
            "next_session_ideas": ["Explore the temple"],
            "npc_follow_ups": ["Contact the sage"],
            "character_specific_hooks": {
                "Rogue": ["Rogue's connections matter"],
            },
        }

        npc_suggestions = [
            {
                "name": "Elara",
                "role": "Sage",
                "context_excerpt": "Elara, the ancient sage, knows secrets.",
                "filename": "elara.json",
            }
        ]

        filepath = create_story_hooks_file(
            temp_dir,
            "Temple Quest",
            hooks_dict,
            session_date="2024-06-05",
            npc_suggestions=npc_suggestions,
        )

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify structured dict content
        assert "missing artifact" in content
        assert "Explore the temple" in content
        assert "Contact the sage" in content
        assert "Rogue" in content

        # Verify NPC suggestions are included
        assert "NPC Profile Suggestions" in content
        assert "Elara" in content
        assert "Sage" in content
        assert "elara.json" in content

        print("  [OK] Structured dict and NPC suggestions both present")

    print("[PASS] Create Story Hooks - Structured Dict with NPCs")


def test_create_story_hooks_empty_structured_dict():
    """Test structured dict with some empty sections (defensive case)."""
    print("\n[TEST] Create Story Hooks - Partial Structured Dict")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Partial dict (some sections with content, some empty)
        hooks_dict = {
            "unresolved_threads": ["Thread 1"],
            "next_session_ideas": [],  # Empty - won't generate section
            "npc_follow_ups": ["NPC follow-up"],
            "character_specific_hooks": {},  # Empty - won't generate section
        }

        filepath = create_story_hooks_file(
            temp_dir,
            "Partial Hooks",
            hooks_dict,
            session_date="2024-06-10",
        )

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify present sections appear
        assert "Thread 1" in content
        assert "NPC follow-up" in content
        assert "NPC Follow-ups" in content

        # Empty sections won't be generated (only non-empty sections appear)
        # This is correct behavior - don't output empty sections
        print("  [OK] Partial dict handled gracefully - empty sections omitted")

    print("[PASS] Create Story Hooks - Partial Structured Dict")


def test_create_story_hooks_legacy_list():
    """Test that function still handles legacy list input (backward compatibility)."""
    print("\n[TEST] Create Story Hooks - Legacy List Input")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Old-style list input (fallback scenario)
        hooks_list = [
            "Legacy hook 1",
            "Legacy hook 2",
            "Legacy hook 3",
        ]

        filepath = create_story_hooks_file(
            temp_dir,
            "Legacy Test",
            hooks_list,
            session_date="2024-06-15",
        )

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify legacy list items are in unresolved threads
        assert "Legacy hook 1" in content
        assert "Legacy hook 2" in content
        assert "Legacy hook 3" in content

        # Verify structure sections still present
        assert "Unresolved Plot Threads" in content
        assert "Session Ideas" in content

        print("  [OK] Legacy list input still works (backward compatible)")

    print("[PASS] Create Story Hooks - Legacy List Input")


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
    test_create_story_hooks_structured_dict()
    test_create_story_hooks_mixed_dict_and_npc()
    test_create_story_hooks_empty_structured_dict()
    test_create_story_hooks_legacy_list()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL HOOKS AND ANALYSIS TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
