"""Tests for `src.combat.combat_narrator.CombatNarrator`.

Uses real character JSON fixtures (aragorn, frodo, gandalf) from game_data
so we exercise CharacterProfile and CharacterConsultant wiring.
"""

import unittest
from tests.test_helpers import FakeAIClient, make_major_npc_profile
from tests import test_helpers

from src.combat.combat_narrator import CombatNarrator
from src.combat.narrator_ai import AIEnhancedNarrator


class TestCombatNarrator(unittest.TestCase):
    """Tests for CombatNarrator using real character fixtures."""

    def setUp(self) -> None:
        """Load real character fixtures and prepare consultants mapping."""
        self.aragorn = test_helpers.load_consultant_fixture("aragorn")
        self.frodo = test_helpers.load_consultant_fixture("frodo")
        self.gandalf = test_helpers.load_consultant_fixture("gandalf")

        self.consultants = {
            self.aragorn.profile.name: self.aragorn,
            self.frodo.profile.name: self.frodo,
            self.gandalf.profile.name: self.gandalf,
        }

    def test_narrate_fallback_and_title(self):
        """Fallback narration uses non-AI path and extracts title from prompt."""
        narrator = CombatNarrator(self.consultants, ai_client=None)

        prompt = "aragorn attacks a goblin. frodo heals aragorn."
        narrative = narrator.narrate_combat_from_prompt(prompt, style="cinematic")

        # Fallback narrator includes the scene header and capitalizes names
        self.assertIn("Combat Scene", narrative)
        self.assertIn("Aragorn", narrative)

        title = narrator.generate_combat_title(prompt)
        # With AI disabled, title is extracted from creature names
        self.assertIn("Goblin", title)

    def test_enhance_with_character_consistency(self):
        """Ensure consistency notes are appended when applicable."""
        narrator = CombatNarrator(self.consultants, ai_client=None)
        base = "A melee erupted."
        actions = {"Aragorn": ["attack the goblin"], "Frodo": ["hide"]}

        enhanced = narrator.enhance_with_character_consistency(base, actions)
        self.assertIn("Character Consistency Notes", enhanced)
        self.assertIn("**Aragorn:**", enhanced)

    def test_ai_path_integration_mocked(self):
        """When AI client is present, its output is used in narration."""
        fake = FakeAIClient()
        narrator = CombatNarrator(self.consultants, ai_client=fake)

        prompt = "Aragorn charges the orc with a mighty shout."
        out = narrator.narrate_combat_from_prompt(prompt)
        # The fake AI returns a canned string; ensure it's present after processing
        self.assertIn("generated combat narrative", out)

    def test_narrate_with_major_npc_fallback(self):
        """narrate_with_major_npc falls back gracefully when AI is absent."""
        major = make_major_npc_profile(
            legendary_actions={"available": 3, "actions": [{"name": "Cantrip", "cost": 1}]},
            lair_actions={"enabled": True, "actions": [{"name": "Shadow Tendrils"}]},
            encounter_tactics=["Opens with Cloudkill"],
        )

        narrator = CombatNarrator(self.consultants, ai_client=None)
        prompt = "The party faces Arch Villain in his tower."
        out = narrator.narrate_with_major_npc(prompt, major, style="cinematic")
        self.assertIn("Combat Scene", out)

    def test_narrate_with_major_npc_ai_mocked(self):
        """narrate_with_major_npc uses AI output when client is present."""
        major = make_major_npc_profile(
            personality="Cold and calculating",
            encounter_tactics=["Opens with Cloudkill"],
            legendary_actions={"available": 3, "actions": [{"name": "Cantrip", "cost": 1}]},
            ai_config={"enabled": True, "system_prompt": "You are the Arch Villain."},
        )

        fake = FakeAIClient()
        narrator = CombatNarrator(self.consultants, ai_client=fake)
        prompt = "The party faces Arch Villain at his lair."
        out = narrator.narrate_with_major_npc(prompt, major, style="cinematic")
        self.assertIn("generated combat narrative", out)

    def test_build_major_npc_context_includes_tactics(self):
        """_build_major_npc_context includes tactics and legendary actions."""
        ai_narrator = AIEnhancedNarrator(self.consultants)

        status = {
            "name": "Arch Villain",
            "personality": "Cold and calculating",
            "encounter_tactics": ["Opens with Cloudkill", "Targets healers"],
            "legendary_actions": {
                "available": 3,
                "actions": [{"name": "Cantrip", "cost": 1}],
            },
            "lair_actions": {
                "enabled": True,
                "actions": [{"name": "Shadow Tendrils"}],
            },
        }

        context = ai_narrator._build_major_npc_context(status)  # pylint: disable=protected-access
        self.assertIn("Arch Villain", context)
        self.assertIn("Cold and calculating", context)
        self.assertIn("Cantrip", context)
        self.assertIn("Shadow Tendrils", context)
        self.assertIn("Opens with Cloudkill", context)


if __name__ == "__main__":
    unittest.main()
