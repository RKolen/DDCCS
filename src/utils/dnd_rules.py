"""
D&D 5e (2024) game rules constants and utilities.

Provides standard DC difficulty levels, ability score calculations,
and other core D&D 5e game mechanics with level-based DC scaling support.
"""

from enum import Enum
from typing import Dict, Optional


class DifficultyTier(Enum):
    """Difficulty tiers for DC scaling."""

    TRIVIAL = "trivial"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    VERY_HARD = "very_hard"
    NEARLY_IMPOSSIBLE = "nearly_impossible"


class ScalingMode(Enum):
    """DC scaling modes."""

    STATIC = "static"
    LINEAR = "linear"
    TIERED = "tiered"
    PROFICIENCY = "proficiency"


# Base DC values for each difficulty tier (static fallback)
BASE_DC: Dict[DifficultyTier, int] = {
    DifficultyTier.TRIVIAL: 5,
    DifficultyTier.EASY: 10,
    DifficultyTier.MEDIUM: 15,
    DifficultyTier.HARD: 20,
    DifficultyTier.VERY_HARD: 25,
    DifficultyTier.NEARLY_IMPOSSIBLE: 30,
}

# Level-based DC values for tiered scaling (EASY / MEDIUM / HARD only)
# Based on D&D 5e encounter building guidelines
LEVEL_DC_MODIFIERS: Dict[int, Dict[DifficultyTier, int]] = {
    1:  {DifficultyTier.EASY: 8,  DifficultyTier.MEDIUM: 13, DifficultyTier.HARD: 18},
    2:  {DifficultyTier.EASY: 8,  DifficultyTier.MEDIUM: 13, DifficultyTier.HARD: 18},
    3:  {DifficultyTier.EASY: 9,  DifficultyTier.MEDIUM: 14, DifficultyTier.HARD: 19},
    4:  {DifficultyTier.EASY: 9,  DifficultyTier.MEDIUM: 14, DifficultyTier.HARD: 19},
    5:  {DifficultyTier.EASY: 10, DifficultyTier.MEDIUM: 15, DifficultyTier.HARD: 20},
    6:  {DifficultyTier.EASY: 10, DifficultyTier.MEDIUM: 15, DifficultyTier.HARD: 20},
    7:  {DifficultyTier.EASY: 11, DifficultyTier.MEDIUM: 16, DifficultyTier.HARD: 21},
    8:  {DifficultyTier.EASY: 11, DifficultyTier.MEDIUM: 16, DifficultyTier.HARD: 21},
    9:  {DifficultyTier.EASY: 12, DifficultyTier.MEDIUM: 17, DifficultyTier.HARD: 22},
    10: {DifficultyTier.EASY: 12, DifficultyTier.MEDIUM: 17, DifficultyTier.HARD: 22},
    11: {DifficultyTier.EASY: 13, DifficultyTier.MEDIUM: 18, DifficultyTier.HARD: 23},
    12: {DifficultyTier.EASY: 13, DifficultyTier.MEDIUM: 18, DifficultyTier.HARD: 23},
    13: {DifficultyTier.EASY: 14, DifficultyTier.MEDIUM: 19, DifficultyTier.HARD: 24},
    14: {DifficultyTier.EASY: 14, DifficultyTier.MEDIUM: 19, DifficultyTier.HARD: 24},
    15: {DifficultyTier.EASY: 15, DifficultyTier.MEDIUM: 20, DifficultyTier.HARD: 25},
    16: {DifficultyTier.EASY: 15, DifficultyTier.MEDIUM: 20, DifficultyTier.HARD: 25},
    17: {DifficultyTier.EASY: 16, DifficultyTier.MEDIUM: 21, DifficultyTier.HARD: 26},
    18: {DifficultyTier.EASY: 16, DifficultyTier.MEDIUM: 21, DifficultyTier.HARD: 26},
    19: {DifficultyTier.EASY: 17, DifficultyTier.MEDIUM: 22, DifficultyTier.HARD: 27},
    20: {DifficultyTier.EASY: 17, DifficultyTier.MEDIUM: 22, DifficultyTier.HARD: 27},
}

# Proficiency bonus lookup by level
PROFICIENCY_BY_LEVEL: Dict[int, int] = {
    1: 2, 2: 2, 3: 2, 4: 2,
    5: 3, 6: 3, 7: 3, 8: 3,
    9: 4, 10: 4, 11: 4, 12: 4,
    13: 5, 14: 5, 15: 5, 16: 5,
    17: 6, 18: 6, 19: 6, 20: 6,
}

# Legacy DC constants (kept for backward compatibility)
DC_EASY = 10
DC_MEDIUM = 15
DC_HARD = 20
DC_VERY_HARD = 25
DC_NEARLY_IMPOSSIBLE = 30

DIFFICULTY_LEVELS = {
    "easy": DC_EASY,
    "medium": DC_MEDIUM,
    "hard": DC_HARD,
    "very_hard": DC_VERY_HARD,
    "nearly_impossible": DC_NEARLY_IMPOSSIBLE,
}


def get_dc_for_difficulty(
    difficulty: DifficultyTier,
    level: Optional[int] = None,
    scaling_mode: ScalingMode = ScalingMode.TIERED,
) -> int:
    """Calculate DC for a given difficulty tier and optional character level.

    Args:
        difficulty: The difficulty tier enum value.
        level: Character or party level (1-20). If None, uses static base DC.
        scaling_mode: How to scale the DC with level.

    Returns:
        The calculated DC value.
    """
    base_dc = BASE_DC.get(difficulty, DC_MEDIUM)

    if level is None or scaling_mode == ScalingMode.STATIC:
        return base_dc

    clamped = min(max(level, 1), 20)

    if scaling_mode == ScalingMode.LINEAR:
        return base_dc + (clamped - 1) // 2

    if scaling_mode == ScalingMode.TIERED:
        level_mods = LEVEL_DC_MODIFIERS.get(clamped, {})
        return level_mods.get(difficulty, base_dc)

    if scaling_mode == ScalingMode.PROFICIENCY:
        prof = get_proficiency_bonus(clamped)
        return base_dc + (prof - 2)

    return base_dc


def get_dc_for_difficulty_legacy(difficulty: str) -> int:
    """Get DC value for a difficulty level string (legacy API).

    Args:
        difficulty: Difficulty level name (easy, medium, hard, very_hard, nearly_impossible).

    Returns:
        DC value (10-30), defaults to medium (15) if difficulty not recognized.
    """
    return DIFFICULTY_LEVELS.get(difficulty.lower(), DC_MEDIUM)


def calculate_modifier(ability_score: int) -> int:
    """Calculate ability modifier from ability score.

    Args:
        ability_score: Ability score value (1-30).

    Returns:
        Ability modifier (-5 to +10).
    """
    return (ability_score - 10) // 2


def get_proficiency_bonus(level: int) -> int:
    """Get proficiency bonus for character level.

    Args:
        level: Character level (1-20).

    Returns:
        Proficiency bonus (+2 to +6).
    """
    if level < 1:
        return 2
    if level > 20:
        return 6
    return PROFICIENCY_BY_LEVEL.get(level, 2)
