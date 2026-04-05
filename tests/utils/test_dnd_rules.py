"""Unit tests for `src.utils.dnd_rules` constants and scaling functions."""

from tests import test_helpers  # configures environment on import

from src.utils.dnd_rules import (
    BASE_DC,
    DC_EASY,
    DC_HARD,
    DC_MEDIUM,
    DifficultyTier,
    ScalingMode,
    calculate_modifier,
    get_dc_for_difficulty,
    get_dc_for_difficulty_legacy,
    get_proficiency_bonus,
)

# Suppress unused-import warning; test_helpers is imported for side-effects only
_ = test_helpers


# ---------------------------------------------------------------------------
# Legacy API
# ---------------------------------------------------------------------------

def test_get_dc_for_difficulty_legacy_known_and_unknown():
    """Known difficulty strings map to correct DCs; unknown defaults to medium."""
    assert get_dc_for_difficulty_legacy("easy") == DC_EASY
    assert get_dc_for_difficulty_legacy("hard") == DC_HARD
    assert get_dc_for_difficulty_legacy("something-unknown") == DC_MEDIUM


def test_calculate_modifier_edge_cases():
    """calculate_modifier should produce expected modifiers for edge scores."""
    assert calculate_modifier(10) == 0
    assert calculate_modifier(1) == -5
    assert calculate_modifier(30) == 10


def test_get_proficiency_bonus_levels():
    """Proficiency bonus increases every 4 levels (clamped to 2..6)."""
    assert get_proficiency_bonus(1) == 2
    assert get_proficiency_bonus(5) == 3
    assert get_proficiency_bonus(9) == 4
    assert get_proficiency_bonus(13) == 5
    assert get_proficiency_bonus(17) == 6
    assert get_proficiency_bonus(0) == 2
    assert get_proficiency_bonus(25) == 6


# ---------------------------------------------------------------------------
# New scaling API - static mode
# ---------------------------------------------------------------------------

def test_get_dc_for_difficulty_static_mode():
    """Static mode returns fixed BASE_DC regardless of level."""
    assert get_dc_for_difficulty(DifficultyTier.EASY, 1, ScalingMode.STATIC) == 10
    assert get_dc_for_difficulty(DifficultyTier.MEDIUM, 1, ScalingMode.STATIC) == 15
    assert get_dc_for_difficulty(DifficultyTier.HARD, 1, ScalingMode.STATIC) == 20
    assert get_dc_for_difficulty(DifficultyTier.MEDIUM, 20, ScalingMode.STATIC) == 15


def test_get_dc_for_difficulty_no_level_returns_base():
    """Omitting level always returns the static base DC."""
    assert get_dc_for_difficulty(DifficultyTier.EASY) == BASE_DC[DifficultyTier.EASY]
    assert get_dc_for_difficulty(DifficultyTier.MEDIUM) == DC_MEDIUM
    assert get_dc_for_difficulty(DifficultyTier.HARD) == DC_HARD
    assert get_dc_for_difficulty(DifficultyTier.NEARLY_IMPOSSIBLE) == 30


# ---------------------------------------------------------------------------
# New scaling API - tiered mode
# ---------------------------------------------------------------------------

def test_get_dc_for_difficulty_tiered_heroic_tier():
    """Heroic tier (levels 1-4) DCs are below the standard 10/15/20 baseline."""
    assert get_dc_for_difficulty(DifficultyTier.MEDIUM, 1) == 13
    assert get_dc_for_difficulty(DifficultyTier.MEDIUM, 3) == 14
    assert get_dc_for_difficulty(DifficultyTier.HARD, 1) == 18


def test_get_dc_for_difficulty_tiered_standard_level5():
    """At level 5 tiered DCs match the classic 10/15/20 values."""
    assert get_dc_for_difficulty(DifficultyTier.EASY, 5) == 10
    assert get_dc_for_difficulty(DifficultyTier.MEDIUM, 5) == 15
    assert get_dc_for_difficulty(DifficultyTier.HARD, 5) == 20


def test_get_dc_for_difficulty_tiered_epic_tier():
    """Epic tier (levels 11-16) DCs are above the standard baseline."""
    assert get_dc_for_difficulty(DifficultyTier.MEDIUM, 11) == 18
    assert get_dc_for_difficulty(DifficultyTier.HARD, 13) == 24


def test_get_dc_for_difficulty_tiered_legendary_tier():
    """Legendary tier (levels 17-20) reaches maximum DCs."""
    assert get_dc_for_difficulty(DifficultyTier.MEDIUM, 20) == 22
    assert get_dc_for_difficulty(DifficultyTier.HARD, 20) == 27


def test_get_dc_for_difficulty_tiered_unmapped_tiers_fall_back():
    """TRIVIAL and NEARLY_IMPOSSIBLE fall back to BASE_DC in tiered mode."""
    assert get_dc_for_difficulty(DifficultyTier.TRIVIAL, 10) == BASE_DC[DifficultyTier.TRIVIAL]
    assert get_dc_for_difficulty(DifficultyTier.NEARLY_IMPOSSIBLE, 10) == 30


# ---------------------------------------------------------------------------
# New scaling API - linear mode
# ---------------------------------------------------------------------------

def test_get_dc_for_difficulty_linear_mode():
    """Linear mode adds +1 DC per 2 levels above level 1."""
    assert get_dc_for_difficulty(DifficultyTier.MEDIUM, 1, ScalingMode.LINEAR) == 15
    assert get_dc_for_difficulty(DifficultyTier.MEDIUM, 3, ScalingMode.LINEAR) == 16
    assert get_dc_for_difficulty(DifficultyTier.MEDIUM, 11, ScalingMode.LINEAR) == 20


# ---------------------------------------------------------------------------
# New scaling API - proficiency mode
# ---------------------------------------------------------------------------

def test_get_dc_for_difficulty_proficiency_mode():
    """Proficiency mode scales DC with proficiency bonus above 2."""
    assert get_dc_for_difficulty(DifficultyTier.MEDIUM, 1, ScalingMode.PROFICIENCY) == 15
    assert get_dc_for_difficulty(DifficultyTier.MEDIUM, 5, ScalingMode.PROFICIENCY) == 16
    assert get_dc_for_difficulty(DifficultyTier.MEDIUM, 17, ScalingMode.PROFICIENCY) == 19


# ---------------------------------------------------------------------------
# Level clamping
# ---------------------------------------------------------------------------

def test_get_dc_for_difficulty_clamps_level():
    """Levels outside 1-20 are clamped to the valid range."""
    assert get_dc_for_difficulty(DifficultyTier.MEDIUM, 0) == \
        get_dc_for_difficulty(DifficultyTier.MEDIUM, 1)
    assert get_dc_for_difficulty(DifficultyTier.MEDIUM, 25) == \
        get_dc_for_difficulty(DifficultyTier.MEDIUM, 20)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all_tests():
    """Run all dnd_rules tests."""
    print("=" * 70)
    print("DND RULES TESTS")
    print("=" * 70)

    test_get_dc_for_difficulty_legacy_known_and_unknown()
    test_calculate_modifier_edge_cases()
    test_get_proficiency_bonus_levels()
    test_get_dc_for_difficulty_static_mode()
    test_get_dc_for_difficulty_no_level_returns_base()
    test_get_dc_for_difficulty_tiered_heroic_tier()
    test_get_dc_for_difficulty_tiered_standard_level5()
    test_get_dc_for_difficulty_tiered_epic_tier()
    test_get_dc_for_difficulty_tiered_legendary_tier()
    test_get_dc_for_difficulty_tiered_unmapped_tiers_fall_back()
    test_get_dc_for_difficulty_linear_mode()
    test_get_dc_for_difficulty_proficiency_mode()
    test_get_dc_for_difficulty_clamps_level()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL DND RULES TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
