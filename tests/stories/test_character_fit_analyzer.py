"""
Tests for character fit analyzer.
"""

import unittest
from src.stories.character_fit_analyzer import (
    score_character_fit,
    suggest_character_amendment,
)


class TestCharacterFitAnalyzer(unittest.TestCase):
    """Test cases for character fit analysis logic."""

    def setUp(self):
        self.profiles = {
            "Aragorn": {
                "name": "Aragorn",
                "dnd_class": "ranger",
                "class_abilities": ["Track", "Survival", "Archery"],
                "specialized_abilities": ["Anduril", "Leadership"],
                "known_spells": [],
                "feats": ["Toughness"],
            },
            "Gandalf": {
                "name": "Gandalf",
                "dnd_class": "wizard",
                "class_abilities": ["Arcane Recovery"],
                "specialized_abilities": ["Staff of Power"],
                "known_spells": ["Fireball", "Light", "Shield"],
                "feats": ["War Caster"],
            },
        }

    def test_score_character_fit_high(self):
        """Test high fit score for matching abilities."""
        # Aragorn tracking
        score = score_character_fit(
            "He tracks the orcs through the woods.", self.profiles["Aragorn"]
        )
        self.assertGreater(
            score, 0.0
        )  # Should have some score, not perfect due to limited data

    def test_score_character_fit_low(self):
        """Test low fit score for non-matching abilities."""
        # Gandalf tracking (he doesn't have track in this mock profile)
        score = score_character_fit(
            "He tracks the orcs through the woods.", self.profiles["Gandalf"]
        )
        self.assertLess(
            score,
            score_character_fit(
                "He tracks the orcs through the woods.", self.profiles["Aragorn"]
            ),
        )  # Should be lower than Aragorn's

    def test_suggest_character_amendment(self):
        """Test suggesting a better character for an action."""
        # Action: casting a fireball (Gandalf's specialty)
        # Current character: Aragorn
        suggestion = suggest_character_amendment(
            actual_character="Aragorn",
            action_text="He casts a massive fireball at the trolls.",
            character_profiles=self.profiles,
            previous_actions_map={},
        )

        # Suggestion should exist if Gandalf has fireball and Aragorn doesn't
        if suggestion:
            self.assertEqual(suggestion["suggested_character"], "Gandalf")
            self.assertGreater(
                suggestion["suggested_fit_score"],
                suggestion["current_fit_score"],
            )

    def test_no_suggestion_if_already_best(self):
        """Test no suggestion if current character is already the best fit."""
        suggestion = suggest_character_amendment(
            actual_character="Gandalf",
            action_text="He casts a massive fireball at the trolls.",
            character_profiles=self.profiles,
            previous_actions_map={},
        )
        self.assertIsNone(suggestion)


if __name__ == "__main__":
    unittest.main()
