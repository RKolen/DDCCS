"""
Session Results Manager Tests

Tests for session results tracking and file generation.
"""

import os
import tempfile

# Use test_helpers to set up environment and import required symbols
from tests import test_helpers
StorySession, create_session_results_file = test_helpers.safe_from_import(
    "src.stories.session_results_manager", "StorySession", "create_session_results_file"
)


def test_story_session_initialization():
    """Test StorySession initialization."""
    print("\n[TEST] StorySession Initialization")

    session = StorySession("Test Adventure", "2024-01-15")
    assert session.story_name == "Test Adventure"
    assert session.session_date == "2024-01-15"
    assert not session.roll_results
    assert not session.character_actions
    assert not session.narrative_events
    assert not session.recruiting_pool
    print("  [OK] StorySession initialized correctly")

    print("[PASS] StorySession Initialization")


def test_story_session_default_date():
    """Test StorySession with default date."""
    print("\n[TEST] StorySession Default Date")

    session = StorySession("Test")
    assert session.story_name == "Test"
    assert session.session_date is not None
    assert len(session.session_date) == 10  # YYYY-MM-DD format
    print("  [OK] Default date set correctly")

    print("[PASS] StorySession Default Date")


def test_add_roll_result_with_dict():
    """Test adding roll result with dictionary."""
    print("\n[TEST] Add Roll Result - Dictionary")

    session = StorySession("Test")
    roll_data = {
        "character": "Theron",
        "action": "Attack goblin",
        "roll_type": "Attack roll",
        "roll_value": 18,
        "dc": 15,
        "outcome": "Hit and dealt 12 damage",
    }

    session.add_roll_result(roll_data)

    assert len(session.roll_results) == 1
    result = session.roll_results[0]
    assert result["character"] == "Theron"
    assert result["action"] == "Attack goblin"
    assert result["roll_type"] == "Attack roll"
    assert result["roll_value"] == 18
    assert result["dc"] == 15
    assert result["success"] is True
    assert result["outcome"] == "Hit and dealt 12 damage"
    print("  [OK] Roll result added with dictionary")

    print("[PASS] Add Roll Result - Dictionary")


def test_add_roll_result_with_kwargs():
    """Test adding roll result with keyword arguments."""
    print("\n[TEST] Add Roll Result - Kwargs")

    session = StorySession("Test")
    session.add_roll_result(
        character="Kael",
        action="Cast Fireball",
        roll_type="Spell save",
        roll_value=14,
        dc=16,
        outcome="Enemy saved, half damage",
    )

    assert len(session.roll_results) == 1
    result = session.roll_results[0]
    assert result["character"] == "Kael"
    assert result["success"] is False
    print("  [OK] Roll result added with kwargs")

    print("[PASS] Add Roll Result - Kwargs")


def test_add_roll_result_success_calculation():
    """Test success/failure calculation."""
    print("\n[TEST] Add Roll Result - Success Calculation")

    session = StorySession("Test")

    # Success: roll >= DC
    session.add_roll_result(
        character="Test1",
        action="Action",
        roll_type="Check",
        roll_value=15,
        dc=15,
        outcome="Success",
    )

    # Failure: roll < DC
    session.add_roll_result(
        character="Test2",
        action="Action",
        roll_type="Check",
        roll_value=14,
        dc=15,
        outcome="Failure",
    )

    assert session.roll_results[0]["success"] is True
    assert session.roll_results[1]["success"] is False
    print("  [OK] Success/failure calculated correctly")

    print("[PASS] Add Roll Result - Success Calculation")


def test_create_session_results_file_basic():
    """Test creating basic session results file."""
    print("\n[TEST] Create Session Results File - Basic")

    with tempfile.TemporaryDirectory() as temp_dir:
        session = StorySession("Dragon Battle", "2024-02-20")
        session.add_roll_result(
            character="Theron",
            action="Attack dragon",
            roll_type="Attack roll",
            roll_value=22,
            dc=18,
            outcome="Critical hit! 24 damage",
        )

        filepath = create_session_results_file(temp_dir, session)

        assert os.path.exists(filepath)

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Session Results: Dragon Battle" in content
        assert "2024-02-20" in content
        assert "Roll Results" in content
        assert "Theron" in content
        assert "Attack dragon" in content
        assert "22 vs DC 18" in content
        assert "SUCCESS" in content
        assert "Critical hit! 24 damage" in content
        print("  [OK] Basic session results file created")

    print("[PASS] Create Session Results File - Basic")


def test_create_session_results_file_filename():
    """Test session results file naming."""
    print("\n[TEST] Create Session Results File - Filename")

    with tempfile.TemporaryDirectory() as temp_dir:
        session = StorySession("The Tavern Brawl", "2024-03-10")

        filepath = create_session_results_file(temp_dir, session)

        filename = os.path.basename(filepath)
        expected = "session_results_2024-03-10_the_tavern_brawl.md"
        assert filename == expected
        print("  [OK] Filename formatted correctly")

    print("[PASS] Create Session Results File - Filename")


def test_create_session_results_file_with_recruits():
    """Test session results file with recruiting pool."""
    print("\n[TEST] Create Session Results File - With Recruits")

    with tempfile.TemporaryDirectory() as temp_dir:
        session = StorySession("Test", "2024-04-01")
        session.recruiting_pool = [
            {
                "name": "Aldric",
                "class": "Wizard",
                "personality": "Wise and scholarly",
            },
            {
                "name": "Elena",
                "class": "Ranger",
                "personality": "Cautious tracker",
            },
        ]

        filepath = create_session_results_file(temp_dir, session)

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Available Recruits" in content
        assert "Aldric" in content
        assert "Wizard" in content
        assert "Elena" in content
        assert "Ranger" in content
        print("  [OK] Recruiting pool included in results")

    print("[PASS] Create Session Results File - With Recruits")


def test_create_session_results_file_character_actions():
    """Test session results file with character actions."""
    print("\n[TEST] Create Session Results File - Character Actions")

    with tempfile.TemporaryDirectory() as temp_dir:
        session = StorySession("Test", "2024-05-15")
        session.character_actions = [
            "Theron negotiated with the guard",
            "Kael investigated the mysterious runes",
            "Lyra kept watch from the rooftop",
        ]

        filepath = create_session_results_file(temp_dir, session)

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Character Actions" in content
        assert "Theron negotiated" in content
        assert "Kael investigated" in content
        assert "Lyra kept watch" in content
        print("  [OK] Character actions included")

    print("[PASS] Create Session Results File - Character Actions")


def test_create_session_results_file_multiple_rolls():
    """Test session results with multiple roll results."""
    print("\n[TEST] Create Session Results File - Multiple Rolls")

    with tempfile.TemporaryDirectory() as temp_dir:
        session = StorySession("Test", "2024-06-01")

        session.add_roll_result(
            character="Fighter",
            action="Block",
            roll_type="Defense",
            roll_value=20,
            dc=15,
            outcome="Blocked",
        )

        session.add_roll_result(
            character="Rogue",
            action="Sneak",
            roll_type="Stealth",
            roll_value=12,
            dc=18,
            outcome="Spotted",
        )

        filepath = create_session_results_file(temp_dir, session)

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Fighter" in content
        assert "Rogue" in content
        assert "SUCCESS" in content
        assert "FAILURE" in content
        print("  [OK] Multiple rolls handled correctly")

    print("[PASS] Create Session Results File - Multiple Rolls")


def run_all_tests():
    """Run all session results manager tests."""
    print("=" * 70)
    print("SESSION RESULTS MANAGER TESTS")
    print("=" * 70)

    test_story_session_initialization()
    test_story_session_default_date()
    test_add_roll_result_with_dict()
    test_add_roll_result_with_kwargs()
    test_add_roll_result_success_calculation()
    test_create_session_results_file_basic()
    test_create_session_results_file_filename()
    test_create_session_results_file_with_recruits()
    test_create_session_results_file_character_actions()
    test_create_session_results_file_multiple_rolls()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL SESSION RESULTS MANAGER TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
