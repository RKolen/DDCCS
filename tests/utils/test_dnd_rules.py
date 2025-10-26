"""Unit tests for `src.utils.dnd_rules` basic calculations."""

from test_helpers import setup_test_environment, import_module

setup_test_environment()

rules = import_module("src.utils.dnd_rules")


def test_get_dc_for_difficulty_known_and_unknown():
    """Known difficulty strings map to correct DCs; unknown defaults to medium."""
    assert rules.get_dc_for_difficulty("easy") == rules.DC_EASY
    assert rules.get_dc_for_difficulty("hard") == rules.DC_HARD
    assert rules.get_dc_for_difficulty("something-unknown") == rules.DC_MEDIUM


def test_calculate_modifier_edge_cases():
    """calculate_modifier should produce expected modifiers for edge scores."""
    assert rules.calculate_modifier(10) == 0
    assert rules.calculate_modifier(1) == -5
    assert rules.calculate_modifier(30) == 10


def test_get_proficiency_bonus_levels():
    """Proficiency bonus increases every 4 levels (clamped to 2..6)."""
    assert rules.get_proficiency_bonus(1) == 2
    assert rules.get_proficiency_bonus(5) == 3
    assert rules.get_proficiency_bonus(9) == 4
    assert rules.get_proficiency_bonus(13) == 5
    assert rules.get_proficiency_bonus(17) == 6
    # Out-of-range values clamp
    assert rules.get_proficiency_bonus(0) == 2
    assert rules.get_proficiency_bonus(25) == 6
