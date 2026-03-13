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
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, cast, Any

# Import character and NPC utilities for voice loading
from src.utils.character_profile_utils import list_character_names
from src.utils.character_profile_utils import load_character_profile
from src.utils.path_utils import get_characters_dir
from src.utils.path_utils import get_npcs_dir
from src.utils.file_io import load_json_file
from src.utils.piper_tts_client import PiperTTSClient
from src.utils.audio_player import AudioPlayer
from src.utils.audio_player import play_wav_bytes
from src.utils.dialogue_detector import segment_story_for_tts
from src.utils.dialogue_detector import get_speaker_voice_map

try:
    import pyttsx3

    TTS_AVAILABLE = True
except ImportError:
    pyttsx3 = None
    TTS_AVAILABLE = False


def _print_error(msg: str) -> None:
    """Print error message with styling."""
    print(f"[ERROR] {msg}")


def _print_warning(msg: str) -> None:
    """Print warning message with styling."""
    print(f"[WARNING] {msg}")


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
            voice_list: List[Any] = cast(List[Any], voices)
            # Look for common male voice names
            male_keywords = ["david", "mark", "james", "george", "male"]

            for voice in voice_list:
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
            voice_list: List[Any] = cast(List[Any], voices)
            if voice_list and 0 <= voice_index < len(voice_list):
                self.engine.setProperty("voice", voice_list[voice_index].id)
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
            voice_list: List[Any] = cast(List[Any], voices)
            if not voice_list:
                return []
            return [voice.name for voice in voice_list]
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
            _print_error("TTS not available")
            return False

        if not text.strip():
            return False

        if not block:
            # Non-blocking not supported with subprocess approach
            _print_warning("Non-blocking TTS not supported")
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
            _print_error("TTS not available")
            print(f"TTS speech failed: {e}")
            print("Check that pyttsx3 is installed correctly.")
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
        _print_error("TTS not available")
        print(f"File not found: {filepath}")
        print("Check that the file path is correct.")
        return False

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError) as e:
        _print_error("TTS not available")
        print(f"Failed to read file: {e}")
        print("Check file permissions and encoding.")
        return False

    # Clean text for narration
    clean_text = clean_text_for_narration(content)

    if not clean_text:
        _print_warning("No text to narrate")
        return False

    # Create narrator if not provided
    if narrator is None:
        narrator = StoryNarrator()

    if not narrator.available:
        _print_error("TTS not available")
        print("Install pyttsx3 or use a different narration method.")
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
            _print_warning("No paragraphs found to narrate")
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
        _print_error("TTS not available")
        print(f"Narration failed: {e}")
        print("Check that pyttsx3 is working correctly.")
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
        _print_error("TTS not available")
        print("Install pyttsx3 or use a different narration method.")
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


# ============================================================================
# Multi-Voice TTS (Piper) Support
# ============================================================================

def is_piper_available() -> bool:
    """Check if Piper TTS is available on this system.

    Returns:
        True if Piper can be executed
    """
    client = PiperTTSClient()
    return client.is_available()


@dataclass
class MultiVoiceConfig:
    """Configuration for multi-voice TTS narration."""

    piper_path: str = "piper"
    voices_dir: Optional[str] = None
    narrator_voice_id: str = "en_US-joe-medium"
    character_voices: dict = field(default_factory=dict)
    pause_between_segments: float = 0.5
    pause_on_speaker_change: float = 0.75

    @classmethod
    def from_game_data(cls) -> "MultiVoiceConfig":
        """Create config with auto-loaded character voices from game data.

        Returns:
            MultiVoiceConfig with character voices loaded from JSON files
        """
        config = cls()
        cls._load_character_voices(config)
        cls._load_npc_voices(config)
        return config

    @classmethod
    def _load_character_voices(cls, config: "MultiVoiceConfig") -> None:
        """Load voice configurations from character JSON files."""
        characters_dir = Path(get_characters_dir())
        if not characters_dir.exists():
            return

        char_names = list_character_names(include_examples=False)
        for name in char_names:
            cls._add_character_voice(config, name)

    @classmethod
    def _add_character_voice(cls, config: "MultiVoiceConfig", name: str) -> None:
        """Add a single character's voice to config."""
        try:
            profile = load_character_profile(name)
            if profile is None:
                return
            voice_id = cls._extract_voice_id(profile)
            if voice_id:
                config.character_voices[name] = voice_id
                nickname = profile.get("nickname")
                if nickname:
                    config.character_voices[nickname] = voice_id
        except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError):
            pass  # Skip characters that fail to load

    @classmethod
    def _extract_voice_id(cls, profile: Optional[dict]) -> Optional[str]:
        """Extract voice ID from a character profile."""
        if not profile or "voice" not in profile:
            return None
        voice_config = profile["voice"]
        return voice_config.get("piper_voice_id")

    @classmethod
    def _load_npc_voices(cls, config: "MultiVoiceConfig") -> None:
        """Load voice configurations from NPC JSON files."""
        npcs_dir = Path(get_npcs_dir())
        if not npcs_dir.exists():
            return

        for npc_file in npcs_dir.glob("*.json"):
            cls._add_npc_voice(config, npc_file)

    @classmethod
    def _add_npc_voice(cls, config: "MultiVoiceConfig", npc_file: Path) -> None:
        """Add a single NPC's voice to config."""
        try:
            npc_data = load_json_file(str(npc_file))
            if npc_data is None:
                return
            voice_id = cls._extract_voice_id(npc_data)
            if voice_id:
                name = npc_data.get("name")
                if name:
                    config.character_voices[name] = voice_id
                nickname = npc_data.get("nickname")
                if nickname:
                    config.character_voices[nickname] = voice_id
        except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError):
            pass  # Skip NPCs that fail to load


class MultiVoiceNarrator:
    """Handles multi-voice TTS narration using Piper."""

    # Pronouns that should be resolved to last known speaker
    PRONOUNS = frozenset({"he", "she", "they", "him", "her", "them"})

    def __init__(self, config: Optional[MultiVoiceConfig] = None, **kwargs):
        """Initialize multi-voice narrator.

        Args:
            config: MultiVoiceConfig object (alternative to separate args)
            **kwargs: Individual config options
        """
        if config is None:
            config = MultiVoiceConfig(**kwargs)

        self.piper_client = PiperTTSClient(
            executable_path=config.piper_path,
            voices_directory=config.voices_dir,
        )
        self.audio_player = AudioPlayer()
        self.narrator_voice_id = config.narrator_voice_id
        self.character_voices = config.character_voices
        self.pause_settings = (config.pause_between_segments, config.pause_on_speaker_change)
        self.available = self.piper_client.is_available()
        self._last_speaker: Optional[str] = None

    @property
    def pause_between_segments(self) -> float:
        """Get pause between segments."""
        return self.pause_settings[0]

    @property
    def pause_on_speaker_change(self) -> float:
        """Get pause on speaker change."""
        return self.pause_settings[1]

    def speak_segment(
        self,
        text: str,
        voice_id: str,
        speed: float = 1.0,
    ) -> bool:
        """Speak a single segment with specified voice."""
        if not self.available:
            return False

        if not text.strip():
            return True

        audio_data = self.piper_client.synthesize(
            text=text,
            voice_id=voice_id,
            speed=speed,
        )

        if audio_data is None:
            return False

        return play_wav_bytes(audio_data)

    def narrate_segments(
        self,
        segments: list,
        show_progress: bool = True,
    ) -> bool:
        """Narrate a list of speech segments."""
        if not segments:
            return False

        if not self.available:
            _print_error("Piper TTS not available")
            return False

        if show_progress:
            print(f"\n[NARRATING] {len(segments)} segments")
            print("[INFO] Press Ctrl+C to stop narration")

        try:
            total = len(segments)
            for i, segment in enumerate(segments, 1):
                self._process_segment(segment, i, total, show_progress)

                if i < total:
                    pause = self._calculate_pause(segment, segments[i])
                    time.sleep(pause)

            if show_progress:
                print("\n[SUCCESS] Narration complete")
            return True

        except KeyboardInterrupt:
            print("\n[INFO] Narration stopped by user")
            return False

    def _process_segment(self, segment, index: int, total: int, show_progress: bool) -> None:
        """Process and speak a single segment."""
        if show_progress:
            speaker = getattr(segment, 'speaker', 'narrator')
            print(f"[{index}/{total}] {speaker}: ", end="", flush=True)

        voice_id = self._get_segment_voice(segment)
        speed = getattr(segment, 'speed', 1.0)

        success = self.speak_segment(segment.text, voice_id, speed=speed)

        if not success:
            _print_warning(f"Failed to speak segment: {segment.text[:50]}...")

    def _get_segment_voice(self, segment) -> str:
        """Get voice ID for a segment with fuzzy speaker matching and pronoun resolution."""
        # First check if segment already has a voice assigned
        if hasattr(segment, 'voice_id') and segment.voice_id:
            return segment.voice_id

        speaker = getattr(segment, 'speaker', None)
        if not speaker or speaker.lower() == "narrator":
            return self.narrator_voice_id

        # Resolve pronouns using last known speaker
        resolved_speaker = self._resolve_speaker(speaker)

        # Try exact match first
        if resolved_speaker in self.character_voices:
            self._last_speaker = resolved_speaker
            return self.character_voices[resolved_speaker]

        # Try case-insensitive match
        speaker_lower = resolved_speaker.lower()
        for name, voice_id in self.character_voices.items():
            if name.lower() == speaker_lower:
                self._last_speaker = name
                return voice_id

        # Try partial match (e.g., "Gandalf" matches "Gandalf the Grey")
        for name, voice_id in self.character_voices.items():
            if speaker_lower in name.lower() or name.lower() in speaker_lower:
                self._last_speaker = name
                return voice_id

        # Fall back to narrator voice
        return self.narrator_voice_id

    def _resolve_speaker(self, speaker: str) -> str:
        """Resolve pronoun speakers to last known character."""
        speaker_lower = speaker.lower()
        if speaker_lower in self.PRONOUNS and self._last_speaker:
            return self._last_speaker
        return speaker

    def _calculate_pause(self, current_segment, next_segment) -> float:
        """Calculate pause duration between segments."""
        current = getattr(current_segment, 'speaker', None)
        nxt = getattr(next_segment, 'speaker', None)

        if current != nxt:
            return self.pause_on_speaker_change
        return self.pause_between_segments

    def narrate_file_multi_voice(
        self,
        filepath: str,
        known_characters: Optional[list] = None,
        known_npcs: Optional[list] = None,
        show_progress: bool = True,
    ) -> bool:
        """Narrate a file with multi-voice support."""
        if not os.path.exists(filepath):
            _print_error(f"File not found: {filepath}")
            return False

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except (OSError, UnicodeDecodeError) as e:
            _print_error(f"Failed to read file: {e}")
            return False

        segments = segment_story_for_tts(content, known_characters, known_npcs)

        if not segments:
            _print_warning("No speech segments found")
            return False

        segments = get_speaker_voice_map(
            segments,
            self.character_voices,
            self.narrator_voice_id,
        )

        return self.narrate_segments(segments, show_progress)


def narrate_file_piper(
    filepath: str,
    config: Optional[MultiVoiceConfig] = None,
    **kwargs,
) -> bool:
    """Narrate a file using Piper multi-voice TTS."""
    if config is None:
        known_characters = kwargs.pop('known_characters', None)
        known_npcs = kwargs.pop('known_npcs', None)
        # Auto-load character voices from game data
        config = MultiVoiceConfig.from_game_data(**kwargs)
    else:
        known_characters = None
        known_npcs = None

    narrator = MultiVoiceNarrator(config=config)

    if not narrator.available:
        _print_error("Piper TTS not available")
        print("Make sure Piper is installed and in your PATH.")
        print("Visit: https://github.com/rhasspy/piper")
        return False

    return narrator.narrate_file_multi_voice(
        filepath,
        known_characters,
        known_npcs,
    )
