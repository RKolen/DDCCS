"""
Piper TTS Client Module

Provides text-to-speech synthesis using the Piper neural TTS system.
Piper is a fast, local neural text-to-speech system.

Reference: https://github.com/rhasspy/piper
"""

import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class VoiceInfo:
    """Information about a available Piper voice."""

    voice_id: str
    name: str
    language: str
    quality: str
    onnx_path: Path
    json_path: Optional[Path] = None

    def __post_init__(self):
        """Ensure paths are Path objects."""
        if isinstance(self.onnx_path, str):
            self.onnx_path = Path(self.onnx_path)
        if self.json_path and isinstance(self.json_path, str):
            self.json_path = Path(self.json_path)


class PiperTTSClient:
    """Client for Piper TTS synthesis."""

    def __init__(
        self,
        executable_path: str = "piper",
        voices_directory: Optional[str] = None,
        default_speaker: int = 0,
    ):
        """Initialize Piper TTS client.

        Args:
            executable_path: Path to piper executable
            voices_directory: Directory containing .onnx voice files
            default_speaker: Default speaker ID for multi-speaker models
        """
        self.executable_path = executable_path
        self.default_speaker = default_speaker

        # Set default voices directory to game_data/piper/voices if not provided
        if voices_directory is None:
            # Try to find game_data relative to current working directory
            game_data = Path.cwd() / "game_data" / "piper" / "voices"
            if game_data.exists():
                self.voices_directory = game_data
            else:
                # Try parent directory
                game_data = Path.cwd().parent / "game_data" / "piper" / "voices"
                if game_data.exists():
                    self.voices_directory = game_data
                else:
                    self.voices_directory = None
        else:
            self.voices_directory = Path(voices_directory)

        self._available_voices: Optional[List[VoiceInfo]] = None

    def is_available(self) -> bool:
        """Check if Piper TTS is available.

        Returns:
            True if Piper can be executed
        """
        # First check if executable exists
        if not shutil.which(self.executable_path):
            return False

        # Try running piper with a simple test
        try:
            # Use --help which works for all versions
            result = subprocess.run(
                [self.executable_path, "--help"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            return False

    def _discover_voices(self) -> List[VoiceInfo]:
        """Discover available voices in the voices directory.

        Returns:
            List of available VoiceInfo objects
        """
        if not self.voices_directory or not self.voices_directory.exists():
            return []

        voices = []
        for onnx_file in self.voices_directory.glob("*.onnx"):
            voice_id = onnx_file.stem  # filename without extension
            json_file = onnx_file.with_suffix(".onnx.json")

            # Try to extract metadata from JSON config
            name = voice_id
            language = "en"
            quality = "medium"

            if json_file.exists():
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        config = json.load(f)
                        name = config.get("name", voice_id)
                        language = config.get("language", "en")
                except (OSError, json.JSONDecodeError):
                    pass

            # Parse voice ID to extract quality if not found
            if "-" in voice_id:
                parts = voice_id.split("-")
                if parts[-1] in ["low", "medium", "high"]:
                    quality = parts[-1]

            voices.append(
                VoiceInfo(
                    voice_id=voice_id,
                    name=name,
                    language=language,
                    quality=quality,
                    onnx_path=onnx_file,
                    json_path=json_file if json_file.exists() else None,
                )
            )

        return voices

    def list_available_voices(self) -> List[VoiceInfo]:
        """List all available Piper voices.

        Returns:
            List of available VoiceInfo objects
        """
        if self._available_voices is None:
            self._available_voices = self._discover_voices()
        return self._available_voices

    def is_voice_available(self, voice_id: str) -> bool:
        """Check if a specific voice is available.

        Args:
            voice_id: Piper voice identifier (e.g., "en_US-lessac-medium")

        Returns:
            True if the voice is available
        """
        voices = self.list_available_voices()
        return any(v.voice_id == voice_id for v in voices)

    def synthesize(
        self,
        text: str,
        voice_id: str,
        output_path: Optional[Path] = None,
        speed: float = 1.0,
    ) -> Optional[bytes]:
        """Synthesize text to audio.

        Args:
            text: Text to synthesize
            voice_id: Piper voice identifier (e.g., "en_US-lessac-medium")
            output_path: Optional path to save audio file
            speed: Speech speed multiplier (0.5 to 2.0)

        Returns:
            Audio data as bytes (WAV format), or None if synthesis failed
        """
        if not self.is_available():
            return None

        if not self.is_voice_available(voice_id):
            return None

        # Determine output path
        if output_path is None:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                output_path = Path(tmp.name)
        else:
            output_path = Path(output_path)

        model_path = self.voices_directory / f"{voice_id}.onnx"

        # Build command
        cmd = [
            self.executable_path,
            "--model", str(model_path),
            "--output_file", str(output_path),
            "--length_scale", str(1.0 / speed),  # Inverse for speed
            "--speaker", str(self.default_speaker),
        ]

        try:
            result = subprocess.run(
                cmd,
                input=text,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )

            if result.returncode != 0:
                return None

            # Read audio file
            with open(output_path, "rb") as f:
                audio_data = f.read()

            # Clean up temp file if we created one
            if output_path.name.startswith("tmp"):
                try:
                    output_path.unlink()
                except OSError:
                    pass

            return audio_data

        except (subprocess.TimeoutExpired, OSError):
            return None

    def synthesize_to_file(
        self,
        text: str,
        voice_id: str,
        output_path: Path,
        speed: float = 1.0,
    ) -> bool:
        """Synthesize text to an audio file.

        Args:
            text: Text to synthesize
            voice_id: Piper voice identifier
            output_path: Path to save audio file
            speed: Speech speed multiplier

        Returns:
            True if synthesis succeeded
        """
        result = self.synthesize(text, voice_id, output_path, speed)
        return result is not None

    def get_voice_info(self, voice_id: str) -> Optional[VoiceInfo]:
        """Get information about a specific voice.

        Args:
            voice_id: Piper voice identifier

        Returns:
            VoiceInfo object or None if not found
        """
        voices = self.list_available_voices()
        for voice in voices:
            if voice.voice_id == voice_id:
                return voice
        return None


def get_default_voices() -> List[str]:
    """Get list of default voice IDs included in the repository.

    Returns:
        List of default voice ID strings
    """
    return [
        "en_US-joe-medium",  # Clear, standard American male - Narrator
        "en_US-ryan-low",    # Deep, gruff, rugged - Mature/rough characters
        "en_US-amy-medium",  # Warm, expressive - Female NPCs
    ]


def get_narrator_voice_id() -> str:
    """Get the default narrator voice ID.

    Returns:
        Default narrator voice ID
    """
    return "en_US-joe-medium"


def get_character_voice_id(
    character_name: str,
    gender: Optional[str] = None,
    voice_preferences: Optional[dict] = None,
) -> str:
    """Get appropriate voice ID for a character based on their characteristics.

    Args:
        character_name: Name of the character
        gender: Optional gender hint ("male", "female", "neutral")
        voice_preferences: Optional dict of character name to voice ID

    Returns:
        Recommended voice ID
    """
    # Check if character has explicit voice preference
    if voice_preferences and character_name in voice_preferences:
        return voice_preferences[character_name]

    gender_lower = gender.lower() if gender else ""

    if gender_lower in ["female", "f"]:
        return "en_US-amy-medium"

    # Default to joe-medium for male or unknown
    return "en_US-joe-medium"
