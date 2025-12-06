"""
Test character profile save/load roundtrip for current format.

This test verifies that when a character is edited and saved,
all fields in the current CharacterProfile format are preserved.
"""

import json
import tempfile
from pathlib import Path

from src.characters.consultants.character_profile import CharacterProfile


def test_character_profile_roundtrip_current_format():
    """Test that aragorn.json format fields roundtrip correctly through load/edit/save."""
    # Create a character using ARAGORN.JSON format (backstory, personality_traits,
    # bonds, flaws, ideals)
    aragorn_format_data = {
        "name": "TestCharacter",
        "nickname": "TC",
        "dnd_class": "Ranger",
        "level": 5,
        "species": "Human",
        "lineage": None,
        "subclass": "Hunter",
        # Aragorn.json personality format
        "backstory": "A ranger who protects the realm",
        "personality_traits": ["Stoic", "Wise"],
        "bonds": ["Defend companions", "Seek truth"],
        "flaws": ["Overly cautious", "Trust issues"],
        "relationships": {"Frodo": "Protector", "Gandalf": "Mentor"},
        "ideals": ["Protect the realm", "Find peace"],
        "secrets": [],
        # Behavior
        "preferred_strategies": [],
        "typical_reactions": {},
        "speech_patterns": [],
        "decision_making_style": "",
        # Story
        "story_hooks": [],
        "character_arcs": [],
        "major_plot_actions": ["Defended village", "Mentored newcomer"],
        # Stats
        "ability_scores": {
            "strength": 18,
            "dexterity": 16,
            "constitution": 16,
            "intelligence": 14,
            "wisdom": 15,
            "charisma": 16,
        },
        "skills": {"Survival": 9, "Perception": 8},
        "max_hit_points": 85,
        "armor_class": 17,
        "movement_speed": 35,
        "proficiency_bonus": 4,
        # Abilities
        "feats": ["Alert", "Skilled"],
        "class_abilities": ["Favored Enemy"],
        "specialized_abilities": ["Tracking"],
        "spell_slots": {"1": 4, "2": 3},
        "known_spells": ["Hunter's Mark"],
        # Possessions
        "equipment": {
            "weapons": ["Longsword", "Dagger"],
            "armor": ["Leather Armor"],
            "items": [],
        },
        "magic_items": ["Ring of Protection"],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "test_character.json"

        # Write aragorn format data
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(aragorn_format_data, f)

        # Load character
        profile = CharacterProfile.load_from_file(str(filepath))

        # Verify basic fields loaded (from aragorn.json format)
        assert profile.identity.name == "TestCharacter"
        assert profile.identity.level == 5
        assert profile.personality.background_story == "A ranger who protects the realm"
        assert "Stoic" in profile.personality.personality_summary
        assert profile.personality.motivations == ["Defend companions", "Seek truth"]
        assert profile.personality.fears_weaknesses == [
            "Overly cautious",
            "Trust issues",
        ]

        # Edit a field
        profile.personality.personality_summary = "Updated: Brave and cautious"

        # Save
        profile.save_to_file(str(filepath))

        # Reload
        profile2 = CharacterProfile.load_from_file(str(filepath))

        # Verify the edit was saved
        assert profile2.personality.personality_summary == "Updated: Brave and cautious"

        # Verify ALL aragorn.json format fields are still present
        with open(filepath, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        # Check identity fields
        assert saved_data["name"] == "TestCharacter"
        assert saved_data["nickname"] == "TC"
        assert saved_data["level"] == 5

        # Check personality fields (aragorn.json format: backstory, personality_traits,
        # bonds, flaws, ideals)
        assert "Updated: Brave and cautious" in saved_data["personality_traits"]
        assert saved_data["backstory"] == "A ranger who protects the realm"
        assert saved_data["bonds"] == ["Defend companions", "Seek truth"]
        assert saved_data["flaws"] == ["Overly cautious", "Trust issues"]
        assert saved_data["ideals"] == ["Protect the realm", "Find peace"]

        # Check story fields
        assert saved_data["major_plot_actions"] == [
            "Defended village",
            "Mentored newcomer",
        ]

        # Check abilities
        assert saved_data["feats"] == ["Alert", "Skilled"]
        assert saved_data["class_abilities"] == ["Favored Enemy"]

        # Check equipment
        assert saved_data["equipment"]["weapons"] == ["Longsword", "Dagger"]
        assert saved_data["magic_items"] == ["Ring of Protection"]

        print("[PASS] Aragorn.json format roundtrip test passed!")


def test_edit_cli_personality_preserves_all_fields():
    """Test the specific scenario: edit personality via CLI, save, reload."""
    aragorn_format_data = {
        "name": "Aragorn",
        "nickname": "Strider",
        "dnd_class": "Ranger",
        "level": 10,
        "species": "Human",
        "lineage": None,
        "subclass": "Hunter",
        "backstory": "Heir of Isildur",
        "personality_traits": ["Stoic", "Wise"],
        "bonds": ["Defend companions", "Unite kingdoms"],
        "flaws": ["Fear of failure", "Isolation"],
        "relationships": {"Frodo": "Protector", "Gandalf": "Mentor"},
        "ideals": ["Protect realm", "Claim throne"],
        "secrets": [],
        "preferred_strategies": [],
        "typical_reactions": {},
        "speech_patterns": [],
        "decision_making_style": "",
        "story_hooks": [],
        "character_arcs": [],
        "major_plot_actions": ["Led Fellowship", "Claimed throne"],
        "ability_scores": {
            "strength": 18,
            "dexterity": 16,
            "constitution": 16,
            "intelligence": 14,
            "wisdom": 15,
            "charisma": 16,
        },
        "skills": {"Survival": 9},
        "max_hit_points": 85,
        "armor_class": 17,
        "movement_speed": 35,
        "proficiency_bonus": 4,
        "feats": ["Alert"],
        "class_abilities": ["Favored Enemy: Orcs"],
        "specialized_abilities": [],
        "spell_slots": {"1": 4},
        "known_spells": ["Hunter's Mark"],
        "equipment": {"weapons": ["Sword"], "armor": ["Leather"], "items": []},
        "magic_items": [],
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = Path(tmpdir) / "aragorn.json"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(aragorn_format_data, f)

        # Load
        profile = CharacterProfile.load_from_file(str(filepath))

        # Simulate CLI edit: change personality summary to "Silly"
        profile.personality.personality_summary = "Silly"

        # Save
        profile.save_to_file(str(filepath))

        # Reload
        profile2 = CharacterProfile.load_from_file(str(filepath))

        # Verify edit was saved
        assert "Silly" in profile2.personality.personality_summary

        # Verify original fields still present (aragorn.json format)
        with open(filepath, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        assert saved_data["bonds"] == ["Defend companions", "Unite kingdoms"]
        assert saved_data["flaws"] == ["Fear of failure", "Isolation"]
        assert saved_data["feats"] == ["Alert"]
        assert saved_data["class_abilities"] == ["Favored Enemy: Orcs"]

        print("[PASS] CLI edit scenario preserves all data!")


if __name__ == "__main__":
    test_character_profile_roundtrip_current_format()
    test_edit_cli_personality_preserves_all_fields()
    print("\n[PASS] All character profile roundtrip tests passed!")
