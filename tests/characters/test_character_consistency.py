"""
Test Character Consistency Module

Tests character development tracking and consistency utilities.

What we test:
- Character development file creation
- Available recruits filtering
- File content formatting
- Exclude list handling

Why we test this:
- Development files track character growth and consistency
- Recruitment system needs accurate character filtering
- File generation must create valid markdown
"""

import tempfile
import os
from tests import test_helpers

# Import required symbols via canonical helper (sets up environment if needed)
create_character_development_file = test_helpers.safe_from_import(
    "src.characters.character_consistency", "create_character_development_file"
)
get_available_recruits = test_helpers.safe_from_import(
    "src.characters.character_consistency", "get_available_recruits"
)
CharacterProfile = test_helpers.safe_from_import(
    "src.characters.consultants.character_profile", "CharacterProfile"
)
CharacterIdentity = test_helpers.safe_from_import(
    "src.characters.consultants.character_profile", "CharacterIdentity"
)
DnDClass = test_helpers.safe_from_import("src.characters.character_sheet", "DnDClass")


def test_create_development_file_basic():
    """Test basic character development file creation."""
    print("\n[TEST] Create Development File - Basic")

    with tempfile.TemporaryDirectory() as temp_dir:
        character_actions = [
            {
                "character": "Test Hero",
                "action": "Charged into battle",
                "reasoning": "Protect the innocent",
                "consistency": "Matches brave personality",
                "notes": "Good character development"
            }
        ]

        filepath = create_character_development_file(
            series_path=temp_dir,
            story_name="Test Story",
            character_actions=character_actions,
            session_date="2024-01-15"
        )

        assert os.path.exists(filepath), "File not created"
        print("  [OK] File created successfully")

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "Test Story" in content, "Story name not in file"
        assert "Test Hero" in content, "Character name not in file"
        assert "Charged into battle" in content, "Action not in file"
        assert "Protect the innocent" in content, "Reasoning not in file"
        print("  [OK] File content correct")

    print("[PASS] Create Development File - Basic")


def test_create_development_file_multiple_actions():
    """Test development file with multiple character actions."""
    print("\n[TEST] Create Development File - Multiple Actions")

    with tempfile.TemporaryDirectory() as temp_dir:
        character_actions = [
            {
                "character": "Fighter",
                "action": "Defended allies",
                "reasoning": "Duty and honor",
                "consistency": "Consistent",
                "notes": "Strong choice"
            },
            {
                "character": "Wizard",
                "action": "Analyzed enemy weakness",
                "reasoning": "Knowledge is power",
                "consistency": "Very consistent",
                "notes": "Classic wizard behavior"
            },
            {
                "character": "Rogue",
                "action": "Scouted ahead",
                "reasoning": "Safety first",
                "consistency": "Consistent",
                "notes": "Good use of skills"
            }
        ]

        filepath = create_character_development_file(
            series_path=temp_dir,
            story_name="Multi Action Test",
            character_actions=character_actions,
            session_date="2024-02-20"
        )

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        assert content.count("CHARACTER:") == 3, "Should have 3 character sections"
        assert "Fighter" in content, "Fighter not in file"
        assert "Wizard" in content, "Wizard not in file"
        assert "Rogue" in content, "Rogue not in file"
        print("  [OK] All 3 characters present")
        print("  [OK] Multiple actions handled correctly")

    print("[PASS] Create Development File - Multiple Actions")


def test_create_development_file_default_date():
    """Test development file creation with default date."""
    print("\n[TEST] Create Development File - Default Date")

    with tempfile.TemporaryDirectory() as temp_dir:
        character_actions = [
            {
                "character": "Test",
                "action": "Action",
                "reasoning": "Reason"
            }
        ]

        filepath = create_character_development_file(
            series_path=temp_dir,
            story_name="Date Test",
            character_actions=character_actions
            # session_date not provided - should use today
        )

        assert os.path.exists(filepath), "File not created"
        filename = os.path.basename(filepath)
        assert filename.startswith("character_development_"), "Wrong filename format"
        print("  [OK] File created with default date")

    print("[PASS] Create Development File - Default Date")


def test_create_development_file_missing_fields():
    """Test development file with missing optional fields."""
    print("\n[TEST] Create Development File - Missing Fields")

    with tempfile.TemporaryDirectory() as temp_dir:
        character_actions = [
            {
                "character": "Incomplete",
                "action": "Did something"
                # Missing reasoning, consistency, notes
            }
        ]

        filepath = create_character_development_file(
            series_path=temp_dir,
            story_name="Missing Fields",
            character_actions=character_actions,
            session_date="2024-03-10"
        )

        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "Incomplete" in content, "Character not in file"
        assert "Did something" in content, "Action not in file"
        assert "No reasoning provided" in content, "Missing reasoning not handled"
        assert "To be analyzed" in content, "Missing consistency not handled"
        assert "No notes" in content, "Missing notes not handled"
        print("  [OK] Missing fields handled with defaults")

    print("[PASS] Create Development File - Missing Fields")


def test_get_available_recruits_basic():
    """Test getting available recruits from consultants."""
    print("\n[TEST] Get Available Recruits - Basic")

    # Create mock consultants using simple objects
    def create_mock_consultant(name, char_class, level):
        """Create a mock consultant for testing."""
        profile = type('MockProfile', (), {
            'name': name,
            'character_class': char_class,
            'level': level,
            'personality_summary': f"{name} is brave and loyal",
            'background_story': f"{name}'s backstory"
        })()
        return type('MockConsultant', (), {'profile': profile})()

    consultants = {
        "Fighter": create_mock_consultant("Fighter", DnDClass.FIGHTER, 5),
        "Wizard": create_mock_consultant("Wizard", DnDClass.WIZARD, 7),
        "Rogue": create_mock_consultant("Rogue", DnDClass.ROGUE, 3)
    }

    recruits = get_available_recruits(consultants)

    assert len(recruits) == 3, "Should return all 3 consultants"
    assert any(r["name"] == "Fighter" for r in recruits), "Fighter not in recruits"
    assert any(r["name"] == "Wizard" for r in recruits), "Wizard not in recruits"
    assert any(r["name"] == "Rogue" for r in recruits), "Rogue not in recruits"
    print("  [OK] All consultants returned")

    # Check recruit structure
    fighter_recruit = next(r for r in recruits if r["name"] == "Fighter")
    assert fighter_recruit["class"] == "Fighter", "Class not correct"
    assert fighter_recruit["level"] == 5, "Level not correct"
    assert "personality" in fighter_recruit, "Missing personality field"
    assert "background" in fighter_recruit, "Missing background field"
    print("  [OK] Recruit structure correct")

    print("[PASS] Get Available Recruits - Basic")


def test_get_available_recruits_with_exclusions():
    """Test getting recruits with exclusion list."""
    print("\n[TEST] Get Available Recruits - With Exclusions")

    # Create mock consultants using factory function
    def create_mock_consultant(name, char_class, level):
        """Create a mock consultant for testing using test_helpers.make_profile."""
        profile = test_helpers.make_profile(name=name, dnd_class=char_class, level=level)
        return type('MockConsultant', (), {'profile': profile})()

    consultants = {
        "Fighter": create_mock_consultant("Fighter", DnDClass.FIGHTER, 5),
        "Wizard": create_mock_consultant("Wizard", DnDClass.WIZARD, 7),
        "Rogue": create_mock_consultant("Rogue", DnDClass.ROGUE, 3),
        "Cleric": create_mock_consultant("Cleric", DnDClass.CLERIC, 4)
    }

    # Exclude Fighter and Cleric (current party)
    recruits = get_available_recruits(
        consultants,
        exclude_characters=["Fighter", "Cleric"]
    )

    assert len(recruits) == 2, "Should return 2 recruits (4 - 2 excluded)"
    assert not any(r["name"] == "Fighter" for r in recruits), "Fighter should be excluded"
    assert not any(r["name"] == "Cleric" for r in recruits), "Cleric should be excluded"
    assert any(r["name"] == "Wizard" for r in recruits), "Wizard should be available"
    assert any(r["name"] == "Rogue" for r in recruits), "Rogue should be available"
    print("  [OK] Exclusion list applied correctly")

    print("[PASS] Get Available Recruits - With Exclusions")


def test_get_available_recruits_empty():
    """Test getting recruits with empty consultant dict."""
    print("\n[TEST] Get Available Recruits - Empty")

    consultants = {}
    recruits = get_available_recruits(consultants)

    assert len(recruits) == 0, "Should return empty list"
    assert isinstance(recruits, list), "Should return list type"
    print("  [OK] Empty consultants handled correctly")

    print("[PASS] Get Available Recruits - Empty")


def test_get_available_recruits_all_excluded():
    """Test getting recruits when all are excluded."""
    print("\n[TEST] Get Available Recruits - All Excluded")

    # Create mock consultants using factory function
    def create_mock_consultant(name, char_class, level):
        """Create a mock consultant for testing."""
        identity = CharacterIdentity(
            name=name,
            character_class=char_class,
            level=level
        )
        return type('MockConsultant', (), {
            'profile': CharacterProfile(identity=identity)
        })()

    consultants = {
        "Fighter": create_mock_consultant("Fighter", DnDClass.FIGHTER, 5),
        "Wizard": create_mock_consultant("Wizard", DnDClass.WIZARD, 7)
    }

    # Exclude all characters
    recruits = get_available_recruits(
        consultants,
        exclude_characters=["Fighter", "Wizard"]
    )

    assert len(recruits) == 0, "Should return empty list when all excluded"
    print("  [OK] All exclusions handled correctly")

    print("[PASS] Get Available Recruits - All Excluded")


def run_all_tests():
    """Run all character consistency tests."""
    print("=" * 70)
    print("CHARACTER CONSISTENCY TESTS")
    print("=" * 70)

    test_create_development_file_basic()
    test_create_development_file_multiple_actions()
    test_create_development_file_default_date()
    test_create_development_file_missing_fields()
    test_get_available_recruits_basic()
    test_get_available_recruits_with_exclusions()
    test_get_available_recruits_empty()
    test_get_available_recruits_all_excluded()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL CHARACTER CONSISTENCY TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
