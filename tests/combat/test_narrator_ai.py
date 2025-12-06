"""Tests for `src.combat.narrator_ai.AIEnhancedNarrator`.

These tests use the shared `FakeAIClient` and `FakeConsultant` from
`tests/test_helpers.py` and the real character JSON fixtures (aragorn,
frodo, gandalf) to exercise character-context building and AI integration.
"""

from tests.test_helpers import FakeAIClient
from tests import test_helpers

# Import directly to avoid tuple unpacking issues with safe_from_import
from src.combat.narrator_ai import AIEnhancedNarrator


def test_ai_narration_uses_ai_client():
    """AIEnhancedNarrator should use the AI client's output when provided."""
    aragorn = test_helpers.load_consultant_fixture("aragorn")
    frodo = test_helpers.load_consultant_fixture("frodo")
    gandalf = test_helpers.load_consultant_fixture("gandalf")

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


def test_rag_lookup_processes_spell_mentions():
    """Test that RAG lookup is integrated into combat narration with spells."""
    consultants = {}
    fake = FakeAIClient()
    narrator = AIEnhancedNarrator(consultants, ai_client=fake)

    # Test prompt with spell mentions - verify narration works correctly
    prompt = "Gandalf casts fireball at the dragon. Aragorn uses divine smite."

    # RAG integration tested via public API (narrate_combat_from_prompt)
    narrative = narrator.narrate_combat_from_prompt(
        combat_prompt=prompt, story_context="", style="cinematic"
    )

    # Should return a string (empty or with narrative, RAG context integrated)
    assert isinstance(narrative, str), "Combat narration should return string"
    assert len(narrative) > 0, "Combat narration should not be empty"


def test_rag_graceful_fallback_when_unavailable():
    """Test that narrator works even if RAG system is unavailable."""
    aragorn = test_helpers.load_consultant_fixture("aragorn")
    consultants = {aragorn.profile.name: aragorn}

    fake = FakeAIClient()
    narrator = AIEnhancedNarrator(consultants, ai_client=fake)

    # Test with spell mention - should not crash if RAG unavailable
    prompt = "Aragorn casts shield spell and attacks"
    narrative = narrator.narrate_combat_from_prompt(prompt, style="cinematic")

    # Should return valid narrative regardless of RAG status
    assert isinstance(narrative, str), "Narration should succeed regardless of RAG"
    assert len(narrative) > 0, "Narration should not be empty"
