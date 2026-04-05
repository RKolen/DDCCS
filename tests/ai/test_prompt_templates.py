"""
Test Prompt Templates

Validates that the shared AI prompt fragments are correctly defined
and that the language instruction is present in all system prompts
across the codebase.

What we test:
- LANGUAGE_INSTRUCTION constant is a non-empty string
- LANGUAGE_INSTRUCTION references English as the default
- LANGUAGE_INSTRUCTION instructs the model to match the user's language
- Key system prompt builder functions include the language instruction

Why we test this:
- Guards against the local LLM reverting to Chinese or another unexpected
  language when the user's prompt is in English.
- Ensures multi-language support: a Dutch or German prompt yields a
  response in the same language.
"""

import unittest

from src.ai.prompt_templates import LANGUAGE_INSTRUCTION
from src.combat.narrator_ai import AIEnhancedNarrator
from src.stories.story_ai_generator import _build_story_system_prompt


class TestLanguageInstruction(unittest.TestCase):
    """Tests for the LANGUAGE_INSTRUCTION constant."""

    def test_is_non_empty_string(self):
        """LANGUAGE_INSTRUCTION must be a non-empty string."""
        self.assertIsInstance(LANGUAGE_INSTRUCTION, str)
        self.assertTrue(len(LANGUAGE_INSTRUCTION) > 0)

    def test_references_english_default(self):
        """LANGUAGE_INSTRUCTION must mention English as the default."""
        self.assertIn("English", LANGUAGE_INSTRUCTION)

    def test_instructs_language_matching(self):
        """LANGUAGE_INSTRUCTION must tell the model to match the user's language."""
        self.assertIn("same language", LANGUAGE_INSTRUCTION)


class TestSystemPromptsContainLanguageInstruction(unittest.TestCase):
    """Tests that system prompts across key modules include the language instruction."""

    def test_combat_narrator_system_prompt(self):
        """Combat narrator system prompt includes language instruction."""
        narrator = AIEnhancedNarrator(character_consultants={})
        prompt = narrator.create_system_prompt("cinematic")
        self.assertIn(LANGUAGE_INSTRUCTION, prompt)

    def test_story_ai_generator_system_prompt(self):
        """Story AI generator system prompt includes language instruction."""
        prompt = _build_story_system_prompt(is_exploration=False)
        self.assertIn(LANGUAGE_INSTRUCTION, prompt)

    def test_story_ai_generator_exploration_prompt(self):
        """Story AI generator exploration system prompt includes language instruction."""
        prompt = _build_story_system_prompt(is_exploration=True)
        self.assertIn(LANGUAGE_INSTRUCTION, prompt)


if __name__ == "__main__":
    unittest.main()
