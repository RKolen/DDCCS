"""Unit tests for TTS narrator module."""

import unittest
import tempfile
import os
from src.utils.tts_narrator import (
    StoryNarrator,
    clean_text_for_narration,
    is_tts_available,
    narrate_text,
    narrate_file,
)


class TestTextCleaning(unittest.TestCase):
    """Test cases for text cleaning functionality."""

    def test_clean_markdown_headers(self):
        """Test removal of markdown headers."""
        text = "# Header 1\n## Header 2\nContent"
        cleaned = clean_text_for_narration(text)
        self.assertNotIn("#", cleaned)
        self.assertIn("Header 1", cleaned)
        self.assertIn("Content", cleaned)

    def test_clean_bold_formatting(self):
        """Test removal of bold formatting."""
        text = "This is **bold** text"
        cleaned = clean_text_for_narration(text)
        self.assertEqual(cleaned, "This is bold text")

    def test_clean_italic_formatting(self):
        """Test removal of italic formatting."""
        text = "This is *italic* text"
        cleaned = clean_text_for_narration(text)
        self.assertEqual(cleaned, "This is italic text")

    def test_clean_inline_code(self):
        """Test removal of inline code formatting."""
        text = "Use `code` here"
        cleaned = clean_text_for_narration(text)
        self.assertEqual(cleaned, "Use code here")

    def test_clean_links(self):
        """Test removal of markdown links."""
        text = "Visit [GitHub](https://github.com)"
        cleaned = clean_text_for_narration(text)
        self.assertEqual(cleaned, "Visit GitHub")

    def test_clean_code_blocks(self):
        """Test removal of code blocks."""
        text = "Before\n```python\ncode here\n```\nAfter"
        cleaned = clean_text_for_narration(text)
        self.assertNotIn("```", cleaned)
        self.assertNotIn("code here", cleaned)
        self.assertIn("Before", cleaned)
        self.assertIn("After", cleaned)

    def test_clean_horizontal_rules(self):
        """Test removal of horizontal rules."""
        text = "Text\n---\nMore text"
        cleaned = clean_text_for_narration(text)
        self.assertNotIn("---", cleaned)
        self.assertIn("Text", cleaned)
        self.assertIn("More text", cleaned)

    def test_clean_extra_whitespace(self):
        """Test removal of extra whitespace."""
        text = "Line 1\n\n\n\nLine 2"
        cleaned = clean_text_for_narration(text)
        # Should reduce multiple newlines to double newlines
        self.assertNotIn("\n\n\n", cleaned)


class TestStoryNarrator(unittest.TestCase):
    """Test cases for StoryNarrator class."""

    def test_narrator_initialization(self):
        """Test narrator can be initialized."""
        narrator = StoryNarrator()
        self.assertIsNotNone(narrator)
        self.assertEqual(narrator.rate, 140)
        self.assertEqual(narrator.volume, 1.0)

    def test_narrator_custom_settings(self):
        """Test narrator with custom rate and volume."""
        narrator = StoryNarrator(rate=120, volume=0.8)
        self.assertEqual(narrator.rate, 120)
        self.assertEqual(narrator.volume, 0.8)

    def test_list_available_voices(self):
        """Test listing available TTS voices."""
        narrator = StoryNarrator()
        voices = narrator.list_available_voices()
        # Should return a list (empty if TTS unavailable)
        self.assertIsInstance(voices, list)

    def test_speak_empty_text(self):
        """Test speaking empty text returns False."""
        narrator = StoryNarrator()
        result = narrator.speak("")
        self.assertFalse(result)

    def test_is_tts_available(self):
        """Test TTS availability check."""
        available = is_tts_available()
        self.assertIsInstance(available, bool)


class TestNarrationFunctions(unittest.TestCase):
    """Test cases for narration utility functions."""

    def test_narrate_text_empty(self):
        """Test narrating empty text."""
        result = narrate_text("")
        self.assertFalse(result)

    def test_narrate_text_without_cleaning(self):
        """Test narrating text without markdown cleaning."""
        text = "**Bold** text"
        # Should not raise exception even if TTS unavailable
        try:
            narrate_text(text, clean=False)
        except (ImportError, RuntimeError, OSError):
            pass  # OK if TTS not available

    def test_narrate_file_nonexistent(self):
        """Test narrating non-existent file."""
        result = narrate_file("/nonexistent/file.md")
        self.assertFalse(result)

    def test_narrate_file_with_temp(self):
        """Test narrating a temporary file."""
        # Create a temporary markdown file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write("# Test Story\n\nThis is a test.")
            temp_path = temp_file.name

        try:
            # Attempt narration (will fail gracefully if TTS unavailable)
            result = narrate_file(temp_path)
            # Result can be True (success) or False (TTS unavailable)
            self.assertIsInstance(result, bool)
        except (ImportError, RuntimeError, OSError):
            pass  # OK if TTS not available
        finally:
            # Clean up temp file (ignore errors if already deleted)
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except (OSError, PermissionError):
                    pass


if __name__ == "__main__":
    unittest.main()
