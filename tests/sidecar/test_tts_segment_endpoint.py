"""Unit tests for the multi-voice TTS segment endpoint in src.sidecar.app."""

from typing import Any, Dict, Optional

from fastapi.testclient import TestClient

from tests.test_helpers import setup_test_environment, import_module

setup_test_environment()

_app_mod = import_module("src.sidecar.app")
app = _app_mod.app

_HTTP = TestClient(app)
_ENDPOINT = "/tts/segment"

_STORY = (
    "The fire crackled warmly in the common room.\n\n"
    '"Evenin\'," Aragorn said. "We need horses by dawn."\n\n'
    "Frodo: \"I will go with you.\"\n"
)


def _post(body: Optional[Dict[str, Any]] = None) -> Any:
    """POST to the segment endpoint.

    Args:
        body: JSON payload. Defaults to a short multi-speaker story.

    Returns:
        FastAPI TestClient response.
    """
    payload = body if body is not None else {
        "text": _STORY,
        "character_voices": {
            "Aragorn": "en_US-ryan-low",
            "Frodo": {
                "voice_id": "en_US-amy-medium",
                "speed": 1.1,
                "pitch": -1.0,
            },
        },
        "known_characters": ["Aragorn", "Frodo"],
    }
    return _HTTP.post(_ENDPOINT, json=payload)


def test_segment_empty_text_returns_400() -> None:
    """Empty text yields 400."""
    print("\n[TEST] tts/segment - empty text returns 400")
    resp = _post({"text": "   ", "character_voices": {}})
    assert resp.status_code == 400, resp.status_code
    assert "empty" in resp.json()["detail"].lower()
    print("  [OK] 400 for blank text")


def test_segment_assigns_narrator_and_character_voices() -> None:
    """Narrative uses narrator voice; attributed dialogue uses character voices."""
    print("\n[TEST] tts/segment - narrator vs character voices")
    resp = _post()
    assert resp.status_code == 200, resp.text
    segments = resp.json()["segments"]
    assert len(segments) >= 2

    narrators = [s for s in segments if s["speaker"].lower() == "narrator"]
    assert narrators, "expected at least one narrator segment"
    assert all(s["voice_id"] == "en_GB-alan-medium" for s in narrators)

    aragorn = [s for s in segments if "aragorn" in s["speaker"].lower()]
    assert aragorn, "expected Aragorn dialogue segment"
    assert all(s["voice_id"] == "en_US-ryan-low" for s in aragorn)

    frodo = [s for s in segments if "frodo" in s["speaker"].lower()]
    assert frodo, "expected Frodo dialogue segment"
    assert all(s["voice_id"] == "en_US-amy-medium" for s in frodo)
    print(f"  [OK] {len(segments)} segments with correct voice ids")


def test_segment_nickname_resolves_voice() -> None:
    """A nickname key in character_voices resolves the matching speaker."""
    print("\n[TEST] tts/segment - nickname resolves voice")
    story = 'Strider: "The road is long."\n'
    resp = _post({
        "text": story,
        "character_voices": {
            "Aragorn": "en_US-ryan-low",
            "Strider": "en_US-ryan-low",
        },
        "known_characters": ["Aragorn", "Strider"],
    })
    assert resp.status_code == 200, resp.text
    segments = resp.json()["segments"]
    speakers = [s for s in segments if s["speaker"].lower() != "narrator"]
    assert speakers
    assert speakers[0]["voice_id"] == "en_US-ryan-low"
    print("  [OK] nickname mapped to character voice")


def test_segment_applies_speed_and_pitch() -> None:
    """Speed and pitch from a voice entry apply to that character's dialogue."""
    print("\n[TEST] tts/segment - speed and pitch from voice entry")
    resp = _post()
    assert resp.status_code == 200, resp.text
    frodo = [
        s for s in resp.json()["segments"]
        if "frodo" in s["speaker"].lower()
    ]
    assert frodo
    assert frodo[0]["speed"] == 1.1
    assert frodo[0]["pitch"] == -1.0

    narrators = [
        s for s in resp.json()["segments"]
        if s["speaker"].lower() == "narrator"
    ]
    assert narrators
    # Narrator defaults: British Alan at measured speed, natural pitch.
    assert narrators[0]["speed"] == 0.88
    assert narrators[0]["pitch"] == 0.0
    print("  [OK] character speed/pitch applied; narrator Alan defaults")


def test_segment_fuzzy_name_match() -> None:
    """Partial name match (Frodo vs Frodo Baggins) resolves the voice."""
    print("\n[TEST] tts/segment - fuzzy name match")
    story = 'Frodo: "I will take the ring."\n'
    resp = _post({
        "text": story,
        "character_voices": {
            "Frodo Baggins": {
                "voice_id": "en_US-amy-medium",
                "speed": 0.9,
                "pitch": 1.5,
            },
        },
        "known_characters": ["Frodo Baggins"],
    })
    assert resp.status_code == 200, resp.text
    frodo = [
        s for s in resp.json()["segments"]
        if "frodo" in s["speaker"].lower()
    ]
    assert frodo
    assert frodo[0]["voice_id"] == "en_US-amy-medium"
    assert frodo[0]["speed"] == 0.9
    assert frodo[0]["pitch"] == 1.5
    print("  [OK] fuzzy match applied speed/pitch")
