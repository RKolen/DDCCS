"""
Tests for story amender orchestrator.
"""

import unittest
import os
import tempfile
from src.stories import story_amender
from src.utils.file_io import write_text_file, read_text_file


class TestStoryAmender(unittest.TestCase):
    """Test cases for story amendment orchestration."""

    def setUp(self):
        self.profiles = {
            "Aragorn": {"name": "Aragorn", "class_abilities": ["Track", "Survival"]},
            "Gandalf": {"name": "Gandalf", "known_spells": ["Fireball"]},
        }

    def test_identify_character_actions(self):
        """Test identifying actions for a character in text."""
        text = "Aragorn looks at the ground. He tracks the orcs.\nGandalf waits."
        actions = story_amender.identify_character_actions(text, "Aragorn")

        self.assertEqual(len(actions), 1)
        self.assertIn("tracks the orcs", actions[0]["text"])
        self.assertEqual(actions[0]["line_index"], 0)

    def test_generate_amended_text(self):
        """Test swapping character names in a line."""
        line = "Aragorn tracks the orcs through the mud."
        new_line = story_amender.generate_amended_text(line, "Aragorn", "Gandalf")
        self.assertEqual(new_line, "Gandalf tracks the orcs through the mud.")

    def test_apply_amendment_to_file(self):
        """Test applying an amendment to a physical file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".md") as tmp:
            tmp_path = tmp.name
            content = "Line 1\nAragorn tracks the orcs.\nLine 3"
            write_text_file(tmp_path, content)

        try:
            new_line = "Gandalf tracks the orcs."
            success = story_amender.apply_amendment_to_file(tmp_path, 1, new_line)

            self.assertTrue(success)
            updated = read_text_file(tmp_path)
            self.assertEqual(updated, "Line 1\nGandalf tracks the orcs.\nLine 3")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
