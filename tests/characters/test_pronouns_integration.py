"""Integration tests for pronouns field in character and NPC profiles.

Tests that the pronouns field is correctly loaded, saved, validated, and
included in AI system prompts, while maintaining backward compatibility
with existing characters that lack the field.
"""

import json
import os
import tempfile
from pathlib import Path

from tests.test_helpers import sample_character_data
from src.characters.consultants.character_profile import CharacterProfile
from src.validation.character_validator import validate_character_json
from src.validation.npc_validator import validate_npc_json


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Use the shared helper so the ability_scores dict is not duplicated across
# multiple test modules, which would trigger Pylint R0801 (duplicate-code).
_MINIMAL_CHAR: dict = sample_character_data(
    name="Test Character",
    dnd_class="Fighter",
    level=1,
)

_MINIMAL_NPC: dict = {
    "name": "Test NPC",
    "role": "Innkeeper",
    "species": "Human",
    "personality": "Friendly",
    "relationships": {},
    "key_traits": [],
    "abilities": [],
    "recurring": False,
    "notes": "",
    "ai_config": {"enabled": False, "temperature": 0.7, "max_tokens": 1000, "system_prompt": ""},
}


def _write_json(tmp_dir: str, filename: str, data: dict) -> str:
    """Write a JSON file and return its path."""
    path = os.path.join(tmp_dir, filename)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)
    return path


# ---------------------------------------------------------------------------
# CharacterProfile loading tests
# ---------------------------------------------------------------------------

def test_load_character_with_pronouns():
    """Loading a character file that has pronouns returns the correct value."""
    with tempfile.TemporaryDirectory() as tmp:
        data = dict(_MINIMAL_CHAR)
        data["pronouns"] = "she/her"
        path = _write_json(tmp, "char.json", data)
        profile = CharacterProfile.load_from_file(path)
        assert profile.identity.pronouns == "she/her"


def test_load_character_without_pronouns_returns_none():
    """Loading a character without pronouns gives None (backward compat)."""
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_json(tmp, "char.json", dict(_MINIMAL_CHAR))
        profile = CharacterProfile.load_from_file(path)
        assert profile.identity.pronouns is None


def test_load_character_with_null_pronouns_returns_none():
    """Explicit null pronouns field loads as None."""
    with tempfile.TemporaryDirectory() as tmp:
        data = dict(_MINIMAL_CHAR)
        data["pronouns"] = None
        path = _write_json(tmp, "char.json", data)
        profile = CharacterProfile.load_from_file(path)
        assert profile.identity.pronouns is None


# ---------------------------------------------------------------------------
# CharacterProfile save/roundtrip tests
# ---------------------------------------------------------------------------

def test_pronouns_roundtrip():
    """Pronouns survive a save-then-load cycle."""
    with tempfile.TemporaryDirectory() as tmp:
        data = dict(_MINIMAL_CHAR)
        data["pronouns"] = "they/them"
        path = _write_json(tmp, "char.json", data)

        profile = CharacterProfile.load_from_file(path)
        assert profile.identity.pronouns == "they/them"
        profile.save_to_file(path)

        reloaded = CharacterProfile.load_from_file(path)
        assert reloaded.identity.pronouns == "they/them"


def test_pronouns_null_roundtrip():
    """None pronouns survive a save-then-load cycle."""
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_json(tmp, "char.json", dict(_MINIMAL_CHAR))

        profile = CharacterProfile.load_from_file(path)
        profile.save_to_file(path)

        reloaded = CharacterProfile.load_from_file(path)
        assert reloaded.identity.pronouns is None


# ---------------------------------------------------------------------------
# Character validator tests
# ---------------------------------------------------------------------------

def test_validator_accepts_pronouns_he_him():
    """Validator accepts he/him pronouns."""
    data = dict(_MINIMAL_CHAR)
    data["pronouns"] = "he/him"
    is_valid, errors = validate_character_json(data)
    assert is_valid, errors
    assert not any("pronouns" in e.lower() for e in errors)


def test_validator_accepts_null_pronouns():
    """Validator accepts null pronouns (field not required)."""
    data = dict(_MINIMAL_CHAR)
    data["pronouns"] = None
    is_valid, errors = validate_character_json(data)
    assert is_valid, errors


def test_validator_accepts_missing_pronouns():
    """Validator accepts characters without a pronouns field at all."""
    is_valid, errors = validate_character_json(dict(_MINIMAL_CHAR))
    assert is_valid, errors


def test_validator_rejects_empty_pronouns_string():
    """Validator rejects an empty string pronouns value."""
    data = dict(_MINIMAL_CHAR)
    data["pronouns"] = ""
    is_valid, errors = validate_character_json(data)
    assert not is_valid
    assert any("pronouns" in e.lower() for e in errors)


def test_validator_rejects_non_string_pronouns():
    """Validator rejects a non-string pronouns value."""
    data = dict(_MINIMAL_CHAR)
    data["pronouns"] = 42
    is_valid, errors = validate_character_json(data)
    assert not is_valid
    assert any("pronouns" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# NPC validator tests
# ---------------------------------------------------------------------------

def test_npc_validator_accepts_pronouns():
    """NPC validator accepts a pronouns field."""
    data = dict(_MINIMAL_NPC)
    data["pronouns"] = "he/him"
    is_valid, errors = validate_npc_json(data)
    assert is_valid, errors


def test_npc_validator_accepts_null_pronouns():
    """NPC validator accepts null pronouns."""
    data = dict(_MINIMAL_NPC)
    data["pronouns"] = None
    is_valid, errors = validate_npc_json(data)
    assert is_valid, errors


def test_npc_validator_accepts_missing_pronouns():
    """NPC validator accepts an NPC without a pronouns field."""
    is_valid, errors = validate_npc_json(dict(_MINIMAL_NPC))
    assert is_valid, errors


# ---------------------------------------------------------------------------
# Real character files: backward compatibility
# ---------------------------------------------------------------------------

def test_existing_characters_load_without_error():
    """All existing game_data characters load successfully (pronouns or not)."""
    chars_dir = (
        Path(__file__).parent.parent.parent / "game_data" / "characters"
    )
    json_files = [
        f for f in chars_dir.glob("*.json")
        if not f.name.endswith(".example.json")
    ]
    assert json_files, "No character JSON files found for backward-compatibility test"
    for char_file in json_files:
        profile = CharacterProfile.load_from_file(str(char_file))
        assert profile is not None, f"Failed to load {char_file.name}"


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all_tests():
    """Run all pronouns integration tests."""
    print("=" * 70)
    print("PRONOUNS INTEGRATION TESTS")
    print("=" * 70)

    test_load_character_with_pronouns()
    test_load_character_without_pronouns_returns_none()
    test_load_character_with_null_pronouns_returns_none()
    test_pronouns_roundtrip()
    test_pronouns_null_roundtrip()
    test_validator_accepts_pronouns_he_him()
    test_validator_accepts_null_pronouns()
    test_validator_accepts_missing_pronouns()
    test_validator_rejects_empty_pronouns_string()
    test_validator_rejects_non_string_pronouns()
    test_npc_validator_accepts_pronouns()
    test_npc_validator_accepts_null_pronouns()
    test_npc_validator_accepts_missing_pronouns()
    test_existing_characters_load_without_error()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL PRONOUNS INTEGRATION TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
