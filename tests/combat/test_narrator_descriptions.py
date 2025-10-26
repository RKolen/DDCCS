"""Tests for `src.combat.narrator_descriptions.CombatDescriptor`.

Adds the project root to sys.path so tests can import the `src` package
when executed directly (common test runner environment difference).
"""

import unittest
from tests import test_helpers

# Import production symbol via centralized helper
CombatDescriptor = test_helpers.safe_from_import(
    "src.combat.narrator_descriptions", "CombatDescriptor"
)

class TestCombatDescriptor(unittest.TestCase):
    """Unit tests for the CombatDescriptor narrative generation helpers.

    These tests verify that the descriptor returns expected phrases and
    damage-bucket descriptions for a variety of combat action inputs.
    """

    def setUp(self) -> None:
        """Create a descriptor instance with no character consultants."""
        self.descriptor = CombatDescriptor(character_consultants={})

    def test_describe_attack_hit(self):
        """An ordinary attack that deals moderate damage produces expected phrasing and bucket."""
        action = {"type": "attack", "target": "goblin", "roll": 10, "damage": 6}
        result = self.descriptor.describe_action(action, consultant=None, style="cinematic")
        self.assertIn("strikes at goblin", result)
        # Damage 6 falls into the (4,8) -> "a solid hit"
        self.assertIn("a solid hit (6 damage)", result)

    def test_describe_attack_crit(self):
        """A critical attack (high roll) includes the devastating precision wording."""
        action = {"type": "attack", "target": "orc", "roll": 20, "damage": 12}
        result = self.descriptor.describe_action(action, consultant=None, style="gritty")
        self.assertIn("devastating precision", result)
        self.assertIn("heavy blow (12 damage)", result)

    def test_describe_spell_damage(self):
        """Spell-casting actions include the spell name and a damage description."""
        action = {"type": "spell", "spell": "Fireball", "damage": 15}
        result = self.descriptor.describe_action(action, consultant=None, style="cinematic")
        self.assertIn("casts Fireball", result)
        self.assertIn("heavy blow (15 damage)", result)

    def test_describe_healing(self):
        """Healing actions describe recovery and amount restored."""
        action = {"type": "healing", "amount": 8}
        result = self.descriptor.describe_action(action, consultant=None, style="heroic")
        self.assertIn("receives healing energy", result)
        self.assertIn("8 hit points", result)

    def test_describe_status(self):
        """Status effect actions are rendered using human-readable effect descriptions."""
        action = {"type": "status", "effect": "prone"}
        result = self.descriptor.describe_action(action, consultant=None, style="cinematic")
        self.assertIn("knocked to the ground", result)

    def test_get_damage_description_edge(self):
        """Very large damage values map to the highest damage bucket."""
        description = self.descriptor.get_damage_description(40)
        self.assertIn("massive crushing blow", description)
        self.assertIn("40 damage", description)


if __name__ == "__main__":
    unittest.main()
