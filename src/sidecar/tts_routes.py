"""Piper TTS routes for the FastAPI sidecar.

Exposes ``/tts/speak`` (synthesise one clip) and ``/tts/segment`` (split story
text into multi-voice segments for sequential browser playback).
"""

import os
import shutil
import subprocess
import sys
import tempfile
from functools import lru_cache
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, Response

from src.sidecar.models import (
    TtsRequest,
    TtsSegmentOut,
    TtsSegmentRequest,
    TtsSegmentResponse,
    TtsVoiceEntry,
)
from src.utils.dialogue_detector import get_speaker_voice_map
from src.utils.dialogue_detector import segment_story_for_tts
from src.utils.piper_tts_client import (
    PiperTTSClient,
    get_narrator_pitch,
    get_narrator_speed,
    get_narrator_voice_id,
)

router = APIRouter(prefix="/tts", tags=["tts"])


@lru_cache(maxsize=1)
def _get_piper() -> PiperTTSClient:
    """Return a cached Piper client, resolving the binary next to the venv."""
    candidate = os.path.join(os.path.dirname(sys.executable), "piper")
    executable = candidate if os.path.exists(candidate) else "piper"
    return PiperTTSClient(executable_path=executable)


def _apply_pitch(wav: bytes, semitones: float) -> bytes:
    """Pitch-shift WAV audio by semitones using sox (Piper has no pitch control).

    Returns the input unchanged when the shift is negligible or sox is missing.
    """
    if abs(semitones) < 0.1 or shutil.which("sox") is None:
        return wav
    in_path = out_path = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
            handle.write(wav)
            in_path = handle.name
        out_path = f"{in_path}.pitch.wav"
        result = subprocess.run(
            ["sox", in_path, out_path, "pitch", str(semitones * 100)],
            capture_output=True, timeout=30, check=False,
        )
        if result.returncode != 0 or not os.path.exists(out_path):
            return wav
        with open(out_path, "rb") as handle:
            return handle.read() or wav
    except (OSError, subprocess.TimeoutExpired):
        return wav
    finally:
        for path in (in_path, out_path):
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except OSError:
                    pass


def _normalize_voice_entry(value: TtsVoiceEntry | str) -> TtsVoiceEntry:
    """Coerce a bare voice-id string into a full voice entry.

    Args:
        value: Either a Piper voice id string or a TtsVoiceEntry.

    Returns:
        A TtsVoiceEntry with defaults for missing speed/pitch.
    """
    if isinstance(value, str):
        return TtsVoiceEntry(voice_id=value)
    return value


def _flatten_voice_ids(
    character_voices: Dict[str, TtsVoiceEntry | str],
) -> Dict[str, str]:
    """Map character names to Piper voice ids only.

    Args:
        character_voices: Name -> voice entry or bare voice id.

    Returns:
        Name -> voice_id mapping for dialogue_detector voice assignment.
    """
    return {
        name: _normalize_voice_entry(entry).voice_id
        for name, entry in character_voices.items()
    }


def _lookup_voice_entry(
    speaker: str,
    character_voices: Dict[str, TtsVoiceEntry],
) -> Optional[TtsVoiceEntry]:
    """Find a voice entry for a speaker with fuzzy name matching.

    Args:
        speaker: Detected speaker name from dialogue segmentation.
        character_voices: Normalised name -> TtsVoiceEntry map.

    Returns:
        Matching entry, or None when no character matches.
    """
    if speaker in character_voices:
        return character_voices[speaker]
    speaker_lower = speaker.lower()
    for name, entry in character_voices.items():
        if name.lower() == speaker_lower:
            return entry
    for name, entry in character_voices.items():
        if speaker_lower in name.lower() or name.lower() in speaker_lower:
            return entry
    return None


@router.post("/speak")
def tts_speak_endpoint(req: TtsRequest) -> Response:
    """Synthesise speech from text with a Piper voice, returning WAV audio.

    Args:
        req: TtsRequest with the text, optional voice id, and speed.

    Returns:
        A ``audio/wav`` response with the synthesised audio.

    Raises:
        HTTPException: 503 when Piper is unavailable, 400 for empty text, or
            500 when synthesis fails.
    """
    text = req.text.strip()
    if text == "":
        raise HTTPException(status_code=400, detail="text must not be empty")
    piper = _get_piper()
    if not piper.is_available():
        raise HTTPException(status_code=503, detail="Piper TTS is not installed")
    voice = req.voice_id.strip() or get_narrator_voice_id()
    if not piper.is_voice_available(voice):
        for fallback in (get_narrator_voice_id(), "en_US-joe-medium"):
            if piper.is_voice_available(fallback):
                voice = fallback
                break
    audio = piper.synthesize(text, voice, speed=req.speed)
    if audio is None:
        raise HTTPException(status_code=500, detail="Speech synthesis failed")
    audio = _apply_pitch(audio, req.pitch)
    return Response(content=audio, media_type="audio/wav")


def _build_segment_outputs(
    mapped: list,
    normalised: Dict[str, TtsVoiceEntry],
    narrator_voice: str,
) -> list[TtsSegmentOut]:
    """Attach voice id / speed / pitch to detected speech segments.

    Args:
        mapped: Segments with voice ids already assigned.
        normalised: Character name -> voice entry map.
        narrator_voice: Fallback Piper voice id for narration.

    Returns:
        API segment payloads ready for sequential synthesis.
    """
    narrator_speed = get_narrator_speed()
    narrator_pitch = get_narrator_pitch()
    outputs: list[TtsSegmentOut] = []
    for segment in mapped:
        speaker = segment.speaker
        speed = narrator_speed
        pitch = narrator_pitch
        if speaker.lower() != "narrator" and not segment.is_action:
            entry = _lookup_voice_entry(speaker, normalised)
            if entry is not None:
                speed = entry.speed
                pitch = entry.pitch
        outputs.append(
            TtsSegmentOut(
                text=segment.text,
                speaker=speaker,
                voice_id=segment.voice_id or narrator_voice,
                speed=speed,
                pitch=pitch,
            )
        )
    return outputs


@router.post("/segment", response_model=TtsSegmentResponse)
def tts_segment_endpoint(req: TtsSegmentRequest) -> TtsSegmentResponse:
    """Split story text into multi-voice TTS segments without synthesising.

    Reuses the CLI dialogue detector so character dialogue gets the matching
    Piper voice id (plus optional speed/pitch), while narration uses the
    default narrator voice.

    Args:
        req: Story text, character voice map, and known names.

    Returns:
        Ordered segments ready for sequential ``/tts/speak`` calls.

    Raises:
        HTTPException: 400 when text is empty.
    """
    text = req.text.strip()
    if text == "":
        raise HTTPException(status_code=400, detail="text must not be empty")

    narrator_voice = req.narrator_voice_id.strip() or get_narrator_voice_id()
    normalised: Dict[str, TtsVoiceEntry] = {
        name: _normalize_voice_entry(entry)
        for name, entry in req.character_voices.items()
    }
    raw_segments = segment_story_for_tts(
        text,
        known_characters=req.known_characters or None,
        known_npcs=req.known_npcs or None,
    )
    mapped = get_speaker_voice_map(
        raw_segments,
        _flatten_voice_ids(req.character_voices),
        narrator_voice,
    )
    return TtsSegmentResponse(
        segments=_build_segment_outputs(mapped, normalised, narrator_voice)
    )
