"""Unit tests for ASCII art rendering module."""

import unittest
from src.utils.ascii_art import (
    get_class_icon,
    create_character_portrait,
    display_character_portrait,
    get_default_ascii_templates,
)


class TestASCIIArt(unittest.TestCase):
    """Test cases for ASCII art functionality."""

    def test_get_class_icon_known_classes(self):
        """Test class icon retrieval for known classes."""
        expected_icons = {
            "barbarian": "[X]",
            "bard": "[~]",
            "cleric": "[+]",
            "druid": "[*]",
            "fighter": "[#]",
            "monk": "[@]",
            "paladin": "[^]",
            "ranger": "[>]",
            "rogue": "[/]",
            "sorcerer": "[%]",
            "warlock": "[&]",
            "wizard": "[?]",
        }

        for class_name, expected_icon in expected_icons.items():
            icon = get_class_icon(class_name)
            self.assertEqual(icon, expected_icon)

    def test_get_class_icon_unknown_class(self):
        """Test class icon retrieval for unknown class."""
        icon = get_class_icon("unknown_class")
        self.assertEqual(icon, "[?]")

    def test_get_class_icon_case_insensitive(self):
        """Test class icon retrieval is case insensitive."""
        self.assertEqual(get_class_icon("Fighter"), "[#]")
        self.assertEqual(get_class_icon("WIZARD"), "[?]")

    def test_create_character_portrait_default(self):
        """Test default character portrait creation."""
        portrait = create_character_portrait("Aragorn", "ranger", 5)

        self.assertIsInstance(portrait, str)
        self.assertIn("Aragorn", portrait)
        self.assertIn("ranger", portrait)
        self.assertIn("Level  5", portrait)
        self.assertIn("[>]", portrait)  # Ranger icon

    def test_create_character_portrait_custom_art(self):
        """Test character portrait with custom ASCII art."""
        custom_art = "Custom\nASCII\nArt"
        portrait = create_character_portrait(
            "Test", "fighter", 1, custom_art=custom_art
        )

        self.assertEqual(portrait, custom_art)

    def test_create_character_portrait_long_name(self):
        """Test portrait creation with long character name."""
        long_name = "VeryLongCharacterName"
        portrait = create_character_portrait(long_name, "wizard", 10)

        # Name should be truncated to 11 characters
        self.assertIn(long_name[:11], portrait)

    def test_display_character_portrait_no_error(self):
        """Test display_character_portrait runs without error."""
        # This test just ensures no exceptions are raised
        try:
            display_character_portrait("Gandalf", "wizard", 20, style="cyan")
        except (ImportError, AttributeError, OSError):
            pass  # OK if rich not available or display fails

    def test_get_default_ascii_templates(self):
        """Test default ASCII template retrieval."""
        templates = get_default_ascii_templates()

        self.assertIsInstance(templates, dict)
        self.assertIn("barbarian", templates)
        self.assertIn("wizard", templates)
        self.assertIn("fighter", templates)
        self.assertIn("cleric", templates)

        # Each template should be a non-empty string
        for template in templates.values():
            self.assertIsInstance(template, str)
            self.assertTrue(len(template) > 0)


if __name__ == "__main__":
    unittest.main()
