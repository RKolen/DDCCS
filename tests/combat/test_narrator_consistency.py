"""Unit tests for `src.combat.narrator_consistency.ConsistencyChecker`."""

import unittest

# Import directly to avoid tuple unpacking issues with safe_from_import
from src.combat.narrator_consistency import ConsistencyChecker
from tests.test_helpers import FakeConsultant


class TestConsistencyChecker(unittest.TestCase):
    """Unit tests for the ConsistencyChecker component."""

    def test_no_consultant_returns_empty(self):
        """When no consultant is available, consistency check returns empty string."""
        checker = ConsistencyChecker({})
        self.assertEqual(
            checker.check_action_consistency("Frodo", "attack with sword"), ""
        )

    def test_combat_action_with_class_reaction_returns_note(self):
        """Combat actions produce a consistency note when consultant suggests a reaction."""
        fake = FakeConsultant({"class_reaction": "prefers ranged engagement"})
        checker = ConsistencyChecker({"Aragorn": fake})

        note = checker.check_action_consistency("Aragorn", "attack the goblin")
        self.assertTrue(note.startswith("**Aragorn:**"))
        self.assertIn("prefers ranged engagement", note)

    def test_non_combat_action_returns_empty_even_with_consultant(self):
        """Non-combat verbs should not trigger consistency notes even with a consultant."""
        fake = FakeConsultant({"class_reaction": "prefers ranged engagement"})
        checker = ConsistencyChecker({"Frodo": fake})

        # 'steal' is not recognized as a combat verb in the checker
        self.assertEqual(
            checker.check_action_consistency("Frodo", "sneak and steal"), ""
        )

    def test_enhance_with_character_consistency_appends_notes(self):
        """Enhancing a narrative appends character consistency notes when present."""
        fake_a = FakeConsultant({"class_reaction": "holds back from violence"})
        fake_b = FakeConsultant({})
        checker = ConsistencyChecker({"Gandalf": fake_a, "Sam": fake_b})

        narrative = "A skirmish broke out by the river."
        actions = {"Gandalf": ["cast a spell"], "Sam": ["carry the bag"]}

        enhanced = checker.enhance_with_character_consistency(narrative, actions)
        self.assertIn("Character Consistency Notes:", enhanced)
        self.assertIn("**Gandalf:**", enhanced)


if __name__ == "__main__":
    unittest.main()
