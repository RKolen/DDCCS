"""Unit tests for TTS narrator module."""

import unittest
import tempfile
import os
from src.utils.tts_narrator import (
    StoryNarrator,
    clean_text_for_narration,
    is_tts_available,
    is_piper_available,
    narrate_text,
    narrate_file,
    MultiVoiceNarrator,
    MultiVoiceConfig,
)
from src.utils.dialogue_detector import segment_story_for_tts


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


class TestPiperAvailability(unittest.TestCase):
    """Test cases for Piper TTS availability."""

    def test_is_piper_available(self):
        """Test Piper availability check."""
        available = is_piper_available()
        self.assertIsInstance(available, bool)


class TestMultiVoiceConfig(unittest.TestCase):
    """Test cases for MultiVoiceConfig."""

    def test_config_defaults(self):
        """Test default configuration values."""
        config = MultiVoiceConfig()
        self.assertEqual(config.piper_path, "piper")
        self.assertEqual(config.narrator_voice_id, "en_US-joe-medium")
        self.assertEqual(config.pause_between_segments, 0.5)
        self.assertEqual(config.pause_on_speaker_change, 0.75)

    def test_config_custom(self):
        """Test custom configuration."""
        config = MultiVoiceConfig(
            piper_path="/usr/local/bin/piper",
            narrator_voice_id="en_US-amy-medium",
            character_voices={"Aragorn": "en_US-ryan-low"},
            pause_between_segments=1.0,
            pause_on_speaker_change=1.5,
        )
        self.assertEqual(config.piper_path, "/usr/local/bin/piper")
        self.assertEqual(config.narrator_voice_id, "en_US-amy-medium")
        self.assertEqual(config.character_voices["Aragorn"], "en_US-ryan-low")
        self.assertEqual(config.pause_between_segments, 1.0)
        self.assertEqual(config.pause_on_speaker_change, 1.5)


class TestMultiVoiceNarrator(unittest.TestCase):
    """Test cases for MultiVoiceNarrator."""

    def test_narrator_initialization(self):
        """Test MultiVoiceNarrator can be initialized."""
        narrator = MultiVoiceNarrator()
        self.assertIsNotNone(narrator)

    def test_narrator_with_config(self):
        """Test MultiVoiceNarrator with custom config."""
        config = MultiVoiceConfig(
            narrator_voice_id="en_US-amy-medium",
            character_voices={"Gorak": "en_US-ryan-low"},
        )
        narrator = MultiVoiceNarrator(config=config)
        self.assertEqual(narrator.narrator_voice_id, "en_US-amy-medium")
        self.assertEqual(narrator.character_voices["Gorak"], "en_US-ryan-low")


class TestDialogueDetector(unittest.TestCase):
    """Test cases for dialogue detection."""

    def test_detect_speech_segments_basic(self):
        """Test basic speech segment detection."""
        text = 'Gandalf: "You shall not pass!"'
        segments = segment_story_for_tts(text)
        self.assertIsInstance(segments, list)

    def test_detect_inline_dialogue(self):
        """Test inline dialogue detection."""
        text = '"Hello," said the wizard.'
        segments = segment_story_for_tts(text)
        self.assertIsInstance(segments, list)

    def test_detect_multiple_speakers(self):
        """Test detection with multiple speakers."""
        text = '''Gandalf: "A wizard is never late."
Aragorn: "Nor is he early."'''
        segments = segment_story_for_tts(text)
        self.assertIsInstance(segments, list)
        self.assertGreater(len(segments), 0)

    def test_speech_segment_attributes(self):
        """Test SpeechSegment has required attributes."""
        text = 'Gandalf: "Fly, you fools!"'
        segments = segment_story_for_tts(text)
        if segments:
            seg = segments[0]
            self.assertTrue(hasattr(seg, 'text'))
            self.assertTrue(hasattr(seg, 'speaker'))


class TestMultiVoiceStoryNarration(unittest.TestCase):
    """Test multi-voice story narration with sample story."""

    def test_narrate_story_with_multiple_voices(self):
        """Test narration of story with multiple character voices."""
        story_text = '''The fire crackled warmly in the common room.

Gandalf: "I have been waiting for you, Frodo."

Frodo: "How did you know I was coming?"

Gandalf: "A concerned wizard knows many things."

The hobbit looked nervous.

Frodo: "I brought the Ring, as you asked."'''

        # Create temporary story file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as temp_file:
            temp_file.write(story_text)
            temp_path = temp_file.name

        try:
            # Test dialogue detection
            known_characters = ["Frodo", "Gandalf", "Aragorn"]
            known_npcs = ["Barliman Butterbur"]

            segments = segment_story_for_tts(
                story_text, known_characters, known_npcs
            )

            # Should have detected several speech segments
            self.assertIsInstance(segments, list)

            # Check for character-specific voice assignment
            character_voices = {
                "Gandalf": "en_US-joe-medium",
                "Frodo": "en_US-amy-medium",
            }

            narrator = MultiVoiceNarrator(
                narrator_voice_id="en_US-joe-medium",
                character_voices=character_voices,
            )
            self.assertIsNotNone(narrator)

        finally:
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except (OSError, PermissionError):
                    pass
