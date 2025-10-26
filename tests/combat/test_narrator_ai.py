"""Tests for `src.combat.narrator_ai.AIEnhancedNarrator`.

These tests use the shared `FakeAIClient` and `FakeConsultant` from
`tests/test_helpers.py` and the real character JSON fixtures (aragorn,
frodo, gandalf) to exercise character-context building and AI integration.
"""

from tests.test_helpers import FakeAIClient
from tests import test_helpers

# Configure test environment and import required symbols
AIEnhancedNarrator = test_helpers.safe_from_import("src.combat.narrator_ai", "AIEnhancedNarrator")
CharacterProfile = test_helpers.safe_from_import(
    "src.characters.consultants.character_profile", "CharacterProfile"
)
CharacterConsultant = test_helpers.safe_from_import(
    "src.characters.consultants.consultant_core", "CharacterConsultant"
)


def _load_fixture(name: str):
    return test_helpers.load_consultant_fixture(name)


def test_ai_narration_uses_ai_client():
    """AIEnhancedNarrator should use the AI client's output when provided."""
    aragorn = _load_fixture("aragorn")
    frodo = _load_fixture("frodo")
    gandalf = _load_fixture("gandalf")

    consultants = {
        aragorn.profile.name: aragorn,
        frodo.profile.name: frodo,
        gandalf.profile.name: gandalf,
    }

    fake = FakeAIClient()
    narrator = AIEnhancedNarrator(consultants, ai_client=fake)

    prompt = "Aragorn lunges at the goblin and Frodo throws a healing vial."
    out = narrator.narrate_combat_from_prompt(prompt, style="cinematic")

    # The fake AI returns a canned narrative; ensure it's used and processed
    assert "generated combat narrative" in out


def test_generate_title_falls_back_on_long_ai_response():
    """When AI returns a long/verbose title, the narrator should fall back
    to extracting creature-based title from the prompt."""
    consultants = {}
    fake = FakeAIClient()
    narrator = AIEnhancedNarrator(consultants, ai_client=fake)

    prompt = "aragorn attacks a goblin with reckless abandon"
    title = narrator.generate_combat_title(prompt)

    # Our fake AI returns a verbose string; the implementation should fall back
    # to a creature-extracted title which contains 'Goblin'.
    assert "Goblin" in title
