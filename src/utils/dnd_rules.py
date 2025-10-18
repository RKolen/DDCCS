"""
D&D 5e (2024) game rules constants and utilities.

Provides standard DC difficulty levels, ability score calculations,
and other core D&D 5e game mechanics.
"""

# DC Difficulty Levels (DMG 2024)
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


def get_dc_for_difficulty(difficulty: str) -> int:
    """
    Get DC value for a difficulty level.

    Args:
        difficulty: Difficulty level name (easy, medium, hard, very_hard, nearly_impossible)

    Returns:
        DC value (10-30), defaults to medium (15) if difficulty not recognized
    """
    return DIFFICULTY_LEVELS.get(difficulty.lower(), DC_MEDIUM)


def calculate_modifier(ability_score: int) -> int:
    """
    Calculate ability modifier from ability score.

    Args:
        ability_score: Ability score value (1-30)

    Returns:
        Ability modifier (-5 to +10)
    """
    return (ability_score - 10) // 2


def get_proficiency_bonus(level: int) -> int:
    """
    Get proficiency bonus for character level.

    Args:
        level: Character level (1-20)

    Returns:
        Proficiency bonus (+2 to +6)
    """
    if level < 1:
        return 2
    if level > 20:
        return 6
    return 2 + (level - 1) // 4
