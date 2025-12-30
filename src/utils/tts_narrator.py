"""
Text-to-Speech Narrator Module

Provides offline voice narration for story files using pyttsx3.
Supports Windows SAPI5, macOS NSSpeechSynthesizer, and Linux eSpeak.
"""

import os
import re
import sys
import time
import subprocess
from typing import Optional
from pathlib import Path

try:
    import pyttsx3

    TTS_AVAILABLE = True
except ImportError:
    pyttsx3 = None
    TTS_AVAILABLE = False


class StoryNarrator:
    """Handles text-to-speech narration for story files."""

    def __init__(
        self, rate: int = 140, volume: float = 1.0, voice_id: Optional[str] = None
    ):
        """Initialize TTS narrator.

        Args:
            rate: Speech rate (words per minute), default 140
            volume: Volume level (0.0 to 1.0), default 1.0
            voice_id: Specific voice ID to use (None = try male voice first, else default)

        Note:
            To install male voices on Windows:
            1. Settings > Time & Language > Speech
            2. Manage voices > Add voices
            3. Download voices like "Microsoft David" or "Microsoft Mark"
        """
        self.engine = None
        self.rate = rate
        self.volume = volume
        self.voice_id = voice_id
        self.available = TTS_AVAILABLE

        if TTS_AVAILABLE:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty("rate", rate)
                self.engine.setProperty("volume", volume)

                # Try to set preferred voice
                if voice_id:
                    self.engine.setProperty("voice", voice_id)
                else:
                    # Try to find and set a male voice by default
                    self._set_male_voice()
            except (RuntimeError, OSError) as e:
                print(f"[WARNING] TTS initialization failed: {e}")
                self.available = False

    def _set_male_voice(self) -> bool:
        """Try to set a male voice automatically.

        Returns:
            True if male voice was found and set
        """
        if not self.engine:
            return False

        try:
            voices = self.engine.getProperty("voices")
            # Look for common male voice names
            male_keywords = ["david", "mark", "james", "george", "male"]

            for voice in voices:
                voice_name_lower = voice.name.lower()
                if any(keyword in voice_name_lower for keyword in male_keywords):
                    self.engine.setProperty("voice", voice.id)
                    self.voice_id = voice.id
                    return True
            return False
        except (RuntimeError, AttributeError):
            return False

    def set_voice(self, voice_index: int = 0) -> bool:
        """Set TTS voice by index.

        Args:
            voice_index: Index of voice to use (0 for default)

        Returns:
            True if voice was set successfully
        """
        if not self.available or not self.engine:
            return False

        try:
            voices = self.engine.getProperty("voices")
            if 0 <= voice_index < len(voices):
                self.engine.setProperty("voice", voices[voice_index].id)
                return True
            return False
        except (RuntimeError, IndexError) as e:
            print(f"[WARNING] Failed to set voice: {e}")
            return False

    def list_available_voices(self) -> list[str]:
        """Get list of available TTS voices.

        Returns:
            List of voice names
        """
        if not self.available or not self.engine:
            return []

        try:
            voices = self.engine.getProperty("voices")
            return [voice.name for voice in voices]
        except (RuntimeError, AttributeError):
            return []

    def speak(self, text: str, block: bool = True) -> bool:
        """Speak text using TTS.

        Args:
            text: Text to speak
            block: If True, wait for speech to finish

        Returns:
            True if speech started successfully
        """
        if not self.available:
            print("[ERROR] TTS not available")
            return False

        if not text.strip():
            return False

        if not block:
            # Non-blocking not supported with subprocess approach
            print("[WARNING] Non-blocking TTS not supported")
            return False

        try:
            # Use subprocess to run TTS in isolation (fixes Windows SAPI5 state issues)
            voice_cmd = ""
            if self.voice_id:
                voice_cmd = f"e.setProperty('voice', {repr(self.voice_id)}); "

            code = (
                f"import pyttsx3; "
                f"e = pyttsx3.init(); "
                f"e.setProperty('rate', {self.rate}); "
                f"e.setProperty('volume', {self.volume}); "
                f"{voice_cmd}"
                f"e.say({repr(text)}); "
                f"e.runAndWait()"
            )
            result = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, OSError) as e:
            print(f"[ERROR] TTS speech failed: {e}")
            return False

    def stop(self) -> None:
        """Stop current narration."""
        if self.available and self.engine:
            try:
                self.engine.stop()
            except (RuntimeError, OSError):
                pass


def clean_text_for_narration(text: str) -> str:
    """Clean markdown text for better TTS narration.

    Args:
        text: Raw markdown text

    Returns:
        Cleaned text suitable for narration
    """
    # Remove BOM (byte order mark) if present
    text = text.lstrip("\ufeff")

    # Remove code blocks FIRST (before inline code removes backticks)
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

    # Remove markdown headers - both the symbols and extra whitespace
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    # Remove any remaining standalone hash symbols
    text = re.sub(r"\s*##+\s*", " ", text)

    # Remove markdown callouts/admonitions [WARNING], [INFO], [NOTE], etc.
    text = re.sub(r"\[!?[A-Z]+\]", "", text)

    # Remove reference-style link definitions
    text = re.sub(r"^\[([^\]]+)\]:\s+.+$", "", text, flags=re.MULTILINE)

    # Remove markdown formatting
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)  # Bold
    text = re.sub(r"__([^_]+)__", r"\1", text)  # Bold alternative
    text = re.sub(r"\*([^*]+)\*", r"\1", text)  # Italic
    text = re.sub(r"_([^_]+)_", r"\1", text)  # Italic alternative
    text = re.sub(r"~~([^~]+)~~", r"\1", text)  # Strikethrough
    text = re.sub(r"`([^`]+)`", r"\1", text)  # Inline code

    # Remove links but keep text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # Remove images
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", "", text)

    # Remove horizontal rules
    text = re.sub(r"^---+$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\*\*\*+$", "", text, flags=re.MULTILINE)
    text = re.sub(r"^___+$", "", text, flags=re.MULTILINE)

    # Remove bullet points and list markers
    text = re.sub(r"^[\s]*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^[\s]*\d+\.\s+", "", text, flags=re.MULTILINE)

    # Remove remaining special characters that TTS might mispronounce
    text = re.sub(r"[*_~`<>]", "", text)  # Leftover markdown chars
    text = re.sub(r"\[|\]", "", text)  # Brackets
    text = re.sub(r"\\", "", text)  # Backslashes

    # Remove extra whitespace
    text = re.sub(r"\n\n+", "\n\n", text)

    return text.strip()


def narrate_file(
    filepath: str, narrator: Optional[StoryNarrator] = None, pause_between: float = 2.0
) -> bool:
    """Narrate a text/markdown file.

    Args:
        filepath: Path to file to narrate
        narrator: Optional StoryNarrator instance (creates new if None)
        pause_between: Pause duration between paragraphs (seconds, default 2.0)

    Returns:
        True if narration completed successfully
    """
    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        return False

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError) as e:
        print(f"[ERROR] Failed to read file: {e}")
        return False

    # Clean text for narration
    clean_text = clean_text_for_narration(content)

    if not clean_text:
        print("[WARNING] No text to narrate")
        return False

    # Create narrator if not provided
    if narrator is None:
        narrator = StoryNarrator()

    if not narrator.available:
        print("[ERROR] TTS not available")
        return False

    return _narrate_paragraphs(narrator, clean_text, filepath, pause_between)


def _narrate_paragraphs(
    narrator: StoryNarrator, clean_text: str, filepath: str, pause_between: float
) -> bool:
    """Narrate paragraphs from cleaned text.

    Args:
        narrator: StoryNarrator instance
        clean_text: Cleaned text to narrate
        filepath: Original file path for display
        pause_between: Pause duration between paragraphs

    Returns:
        True if narration completed successfully
    """
    print(f"\n[NARRATING] {Path(filepath).name}")
    print("[INFO] Press Ctrl+C to stop narration")

    try:
        # Split into paragraphs for better pacing
        paragraphs = [
            p.strip()
            for p in clean_text.split("\n\n")
            if p.strip() and len(p.strip()) > 10
        ]

        if not paragraphs:
            print("[WARNING] No paragraphs found to narrate")
            return False

        for i, paragraph in enumerate(paragraphs, 1):
            print(f"[{i}/{len(paragraphs)}] ", end="", flush=True)
            narrator.speak(paragraph, block=True)

            # Small pause between paragraphs (except last)
            if i < len(paragraphs) and narrator.engine:
                time.sleep(pause_between)

        print("\n[SUCCESS] Narration complete")
        return True

    except KeyboardInterrupt:
        print("\n[INFO] Narration stopped by user")
        narrator.stop()
        return False
    except (RuntimeError, OSError) as e:
        print(f"\n[ERROR] Narration failed: {e}")
        return False


def narrate_text(
    text: str, narrator: Optional[StoryNarrator] = None, clean: bool = True
) -> bool:
    """Narrate a text string.

    Args:
        text: Text to narrate
        narrator: Optional StoryNarrator instance
        clean: If True, clean markdown formatting

    Returns:
        True if narration completed successfully
    """
    if not text.strip():
        return False

    if narrator is None:
        narrator = StoryNarrator()

    if not narrator.available:
        print("[ERROR] TTS not available")
        return False

    if clean:
        text = clean_text_for_narration(text)

    try:
        return narrator.speak(text, block=True)
    except KeyboardInterrupt:
        print("\n[INFO] Narration stopped by user")
        narrator.stop()
        return False


def is_tts_available() -> bool:
    """Check if TTS is available on this system.

    Returns:
        True if TTS can be initialized
    """
    if not TTS_AVAILABLE:
        return False

    try:
        test_engine = pyttsx3.init()
        test_engine.stop()
        return True
    except (RuntimeError, OSError):
        return False
