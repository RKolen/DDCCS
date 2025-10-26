"""Unit tests for `src.utils.behaviour_generation` heuristics.

These tests exercise the heuristic branch (AI unavailable) by calling the
public `generate_behavior_from_personality` function with controlled inputs
and asserting on the returned structure.
"""

from test_helpers import setup_test_environment, import_module

setup_test_environment()

behave_mod = import_module("src.utils.behaviour_generation")
generate = behave_mod.generate_behavior_from_personality


def test_generate_behavior_heuristic_outputs_expected_keys():
    """Heuristic output includes expected keys and types."""
    behavior = generate(
        personality_traits=["wise", "compassionate"],
        ideals=["Protect the village"],
        bonds=["family"],
        flaws=["fear of spiders"],
        backstory="A ranger and tracker from the northern woods.",
    )

    assert isinstance(behavior, dict)
    assert "preferred_strategies" in behavior
    assert "typical_reactions" in behavior
    assert "speech_patterns" in behavior
    assert "decision_making_style" in behavior

    # Heuristic should include strategy derived from ideals and bonds
    strategies = behavior["preferred_strategies"]
    assert any("protect" in s or "protect" in s for s in strategies)

    # Bonds contribute a protect <b> style entry
    assert any("protect family" in s for s in strategies) or any(
        "protect family" in s for s in behavior["speech_patterns"]
    )

    # Backstory indicates ranger/tracker speech patterns
    assert any("fieldwise" in p or "pragmatic" in p for p in behavior["speech_patterns"])


def test_generate_behavior_empty_inputs_fallbacks():
    """When given empty inputs, heuristics provide safe defaults (non-empty lists)."""
    behavior = generate([], [], [], [], "")

    assert isinstance(behavior["preferred_strategies"], list)
    assert len(behavior["preferred_strategies"]) >= 1
    assert isinstance(behavior["speech_patterns"], list)
    assert len(behavior["speech_patterns"]) >= 1
    assert isinstance(behavior["typical_reactions"], dict)
    assert behavior["decision_making_style"]
