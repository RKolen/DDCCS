"""
Equipment Consistency Checker.

Shared helper for checking weapon usage consistency across story analysis modules.
"""

from typing import List, Optional, Tuple


def check_weapon_usage_consistency(
    action_text: str, weapons: List[str]
) -> Optional[str]:
    """
    Check if action mentions weapon not in character's equipment.

    Args:
        action_text: Action description text
        weapons: List of weapons in character's equipment

    Returns:
        Weapon type if inconsistency found, None otherwise
    """
    action_lower = action_text.lower()
    weapons_lower = [w.lower() for w in weapons]

    # Check for weapon usage patterns
    weapon_patterns = [
        (["bow", "arrow", "shoots an arrow", "fires an arrow"], "bow"),
        (["sword", "blade", "slashes with sword"], "sword"),
        (["dagger", "knife"], "dagger"),
        (["axe", "hatchet"], "axe"),
        (["hammer", "warhammer"], "hammer"),
        (["staff of", "quarterstaff"], "staff"),
        (["mace", "club"], "mace"),
        (["spear", "lance"], "spear"),
    ]

    for keywords, weapon_type in weapon_patterns:
        # Check if action mentions this weapon
        if any(keyword in action_lower for keyword in keywords):
            # Check if character has this weapon type in equipment
            has_weapon = any(weapon_type in w_lower for w_lower in weapons_lower)
            if not has_weapon:
                return weapon_type

    return None


def format_equipment_warning(weapon_type: str, available_weapons: List[str]) -> str:
    """
    Format equipment inconsistency warning message.

    Args:
        weapon_type: Type of weapon used
        available_weapons: List of available weapons

    Returns:
        Formatted warning message
    """
    available = ", ".join(available_weapons) if available_weapons else "none"
    return (
        f"INCONSISTENT: Character uses {weapon_type} but doesn't have "
        f"one in equipment (Available weapons: {available})"
    )


def format_equipment_issue(weapon_type: str) -> Tuple[str, str]:
    """
    Format equipment inconsistency as tuple for consistency checker.

    Args:
        weapon_type: Type of weapon used

    Returns:
        Tuple of (weapon_type, issue_description)
    """
    return (
        weapon_type,
        f"Character uses {weapon_type} but doesn't have one in equipment",
    )
