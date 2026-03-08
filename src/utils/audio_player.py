"""
Audio Player Module

Cross-platform audio playback for TTS audio files.
Supports queuing and sequential playback of audio segments.
"""

import os
import queue
import subprocess
import sys
import tempfile
import threading
import wave
import shlex
from pathlib import Path
from typing import Optional


class AudioPlayer:
    """Cross-platform audio playback."""

    def __init__(self):
        """Initialize audio player."""
        self._audio_queue: queue.Queue[Optional[Path]] = queue.Queue()
        self._stop_flag = threading.Event()
        self._current_file: Optional[Path] = None
        self._playback_thread: Optional[threading.Thread] = None

    def _get_playback_command(self, filepath: Path) -> Optional[list]:
        """Get platform-specific audio playback command.

        Args:
            filepath: Path to audio file

        Returns:
            Command list or None if no player available
        """
        filepath_str = str(filepath)

        if sys.platform == "darwin":
            # macOS: use afplay
            return ["afplay", filepath_str]
        if sys.platform == "win32":
            # Windows: try PowerShell or built-in player
            return [
                "powershell",
                "-Command",
                f"(New-Object Media.SoundPlayer '{filepath_str}').PlaySync()",
            ]
        # Linux: try various players
        for player in ["paplay", "aplay", "ffplay"]:
            try:
                subprocess.run(
                    [player, "--version"],
                    capture_output=True,
                    timeout=5,
                    check=False,
                )
                return [player, filepath_str]
            except (FileNotFoundError, subprocess.TimeoutExpired):
                continue
        # Fallback: try aplay
        return ["aplay", filepath_str]

    def play_audio_file(self, filepath: Path, block: bool = True) -> bool:
        """Play an audio file.

        Args:
            filepath: Path to audio file
            block: If True, wait for playback to complete

        Returns:
            True if playback succeeded
        """
        if not filepath.exists():
            return False

        cmd = self._get_playback_command(filepath)
        if not cmd:
            return False

        try:
            if block:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    timeout=120,
                    check=False,
                )
                return result.returncode == 0
            # Non-blocking: use os.system for background playback
            cmd_str = ' '.join(shlex.quote(str(c)) for c in cmd)
            os.system(f"{cmd_str} &")
            return True
        except (subprocess.TimeoutExpired, OSError):
            return False

    def queue_audio(self, filepath: Path) -> None:
        """Add audio file to playback queue."""
        self._audio_queue.put(filepath)

    def play_queue(self) -> None:
        """Play all queued audio files in order."""
        while not self._stop_flag.is_set():
            try:
                filepath = self._audio_queue.get(timeout=0.5)
                if filepath is None:  # Stop signal
                    break
                self.play_audio_file(filepath, block=True)
                self._audio_queue.task_done()
            except queue.Empty:
                break

    def stop(self) -> None:
        """Stop current playback and clear queue."""
        self._stop_flag.set()
        # Clear queue
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break
        self._audio_queue.put(None)  # Signal to stop

    def clear_queue(self) -> None:
        """Clear the audio queue without stopping playback."""
        while not self._audio_queue.empty():
            try:
                self._audio_queue.get_nowait()
            except queue.Empty:
                break


def play_wav_bytes(audio_data: bytes) -> bool:
    """Play WAV audio data directly.

    Args:
        audio_data: WAV audio data as bytes

    Returns:
        True if playback succeeded
    """
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_data)
        tmp_path = Path(tmp.name)

    try:
        player = AudioPlayer()
        return player.play_audio_file(tmp_path, block=True)
    finally:
        try:
            tmp_path.unlink()
        except OSError:
            pass


def get_audio_duration_wav(filepath: Path) -> Optional[float]:
    """Get duration of WAV file in seconds.

    Args:
        filepath: Path to WAV file

    Returns:
        Duration in seconds or None if unable to determine
    """
    try:
        with wave.open(str(filepath), "rb") as wav_file:
            frames = wav_file.getnframes()
            rate = wav_file.getframerate()
            return frames / rate if rate > 0 else None
    except (OSError, wave.Error):
        return None
