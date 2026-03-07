"""
NPC Profile Migration Utility

Converts simplified NPC profiles to full D&D 5e character profiles.
Prompts for missing combat stats and character details.
"""

from typing import Dict, Any, Optional
from pathlib import Path
from src.utils.file_io import load_json_file, save_json_file
from src.utils.errors import display_error, DnDError
from src.validation.npc_validator import validate_npc_json
from src.characters.npc_constants import (
    ABILITY_SCORE_NAMES,
    DEFAULT_ABILITY_SCORES,
    DEFAULT_EQUIPMENT,
)


def prompt_for_ability_scores() -> Dict[str, int]:
    """Prompt user for ability scores."""
    print("\nEnter ability scores (press Enter for default 10):")
    scores = {}
    for ability in ABILITY_SCORE_NAMES:
        while True:
            value = input(f"  {ability.capitalize()}: ").strip()
            if not value:
                scores[ability] = 10
                break
            try:
                score = int(value)
                if 1 <= score <= 30:
                    scores[ability] = score
                    break
                print("    Score must be between 1 and 30.")
            except ValueError:
                print("    Please enter a number.")
    return scores


def prompt_for_class_info() -> tuple:
    """Prompt user for class, subclass, and level."""
    print("\nEnter class information:")
    dnd_class = input("  Class (Fighter, Wizard, Rogue, etc.): ").strip() or "Fighter"
    subclass = input("  Subclass (optional, press Enter to skip): ").strip() or None
    while True:
        level_input = input("  Level (1-20, default 1): ").strip()
        if not level_input:
            level = 1
            break
        try:
            level = int(level_input)
            if 1 <= level <= 20:
                break
            print("    Level must be between 1 and 20.")
        except ValueError:
            print("    Please enter a number.")
    return dnd_class, subclass, level


def prompt_for_combat_stats(level: int) -> tuple:
    """Prompt user for combat statistics."""
    print("\nEnter combat statistics:")
    while True:
        hp_input = input(f"  Max Hit Points (default {level * 8}): ").strip()
        if not hp_input:
            max_hp = level * 8
            break
        try:
            max_hp = int(hp_input)
            if max_hp > 0:
                break
            print("    HP must be positive.")
        except ValueError:
            print("    Please enter a number.")

    while True:
        ac_input = input("  Armor Class (default 10): ").strip()
        if not ac_input:
            armor_class = 10
            break
        try:
            armor_class = int(ac_input)
            if armor_class > 0:
                break
            print("    AC must be positive.")
        except ValueError:
            print("    Please enter a number.")

    while True:
        speed_input = input("  Movement Speed (default 30): ").strip()
        if not speed_input:
            movement_speed = 30
            break
        try:
            movement_speed = int(speed_input)
            if movement_speed > 0:
                break
            print("    Speed must be positive.")
        except ValueError:
            print("    Please enter a number.")

    prof_bonus = 2 + ((level - 1) // 4)
    print(f"  Proficiency Bonus (calculated): +{prof_bonus}")

    return max_hp, armor_class, movement_speed, prof_bonus


def prompt_for_equipment() -> Dict[str, Any]:
    """Prompt user for equipment."""
    print("\nEnter equipment (comma-separated, press Enter to skip):")
    weapons = input("  Weapons: ").strip()
    armor = input("  Armor: ").strip()
    items = input("  Items: ").strip()
    magic_items = input("  Magic Items: ").strip()
    gold = input("  Gold (default 0): ").strip()

    return {
        "weapons": [w.strip() for w in weapons.split(",")] if weapons else [],
        "armor": [a.strip() for a in armor.split(",")] if armor else [],
        "items": [i.strip() for i in items.split(",")] if items else [],
        "magic_items": (
            [m.strip() for m in magic_items.split(",")] if magic_items else []
        ),
        "gold": int(gold) if gold.isdigit() else 0,
    }


def prompt_for_personality_details() -> tuple:
    """Prompt user for personality traits, ideals, bonds, flaws."""
    print("\nEnter personality details (comma-separated, press Enter to skip):")
    traits = input("  Personality Traits: ").strip()
    ideals = input("  Ideals: ").strip()
    bonds = input("  Bonds: ").strip()
    flaws = input("  Flaws: ").strip()
    background = input("  Background (Soldier, Noble, etc.): ").strip() or None

    return (
        [t.strip() for t in traits.split(",")] if traits else [],
        [i.strip() for i in ideals.split(",")] if ideals else [],
        [b.strip() for b in bonds.split(",")] if bonds else [],
        [f.strip() for f in flaws.split(",")] if flaws else [],
        background,
    )


def prompt_for_spells_and_abilities() -> tuple:
    """Prompt user for spells, spell slots, abilities, and feats."""
    print("\nEnter spells and abilities (press Enter to skip each):")
    spells_input = input("  Known spells (comma-separated): ").strip()
    spells = [s.strip() for s in spells_input.split(",") if s.strip()]

    slots_input = input("  Spell slots (e.g., '1:4,2:3,3:2'): ").strip()
    slots = {}
    if slots_input:
        for pair in slots_input.split(","):
            if ":" in pair:
                level_str, count_str = pair.split(":")
                try:
                    slots[level_str.strip()] = int(count_str.strip())
                except ValueError:
                    pass

    abilities_input = input("  Class abilities (comma-separated): ").strip()
    abilities = [a.strip() for a in abilities_input.split(",") if a.strip()]

    feats_input = input("  Feats (comma-separated): ").strip()
    feats = [f.strip() for f in feats_input.split(",") if f.strip()]

    return spells, slots, abilities, feats


def _build_interactive_profile(npc_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build full profile by prompting user for details.

    Args:
        npc_data: Existing simplified NPC data

    Returns:
        Full profile dictionary with user-provided details
    """
    full_profile = npc_data.copy()
    full_profile["profile_type"] = "full"

    # Ensure faction field
    if "faction" not in full_profile:
        print("\nChoose faction:")
        print("  1. ally")
        print("  2. neutral (default)")
        print("  3. enemy")
        choice = input("Selection (1-3): ").strip()
        faction_map = {"1": "ally", "2": "neutral", "3": "enemy"}
        full_profile["faction"] = faction_map.get(choice, "neutral")

    # Get class and level info
    class_info = prompt_for_class_info()
    full_profile.update(
        {"dnd_class": class_info[0], "subclass": class_info[1], "level": class_info[2]}
    )

    # Get ability scores and combat stats
    full_profile["ability_scores"] = prompt_for_ability_scores()
    combat_stats = prompt_for_combat_stats(class_info[2])
    full_profile.update(
        {
            "max_hit_points": combat_stats[0],
            "armor_class": combat_stats[1],
            "movement_speed": combat_stats[2],
            "proficiency_bonus": combat_stats[3],
        }
    )

    # Get equipment and personality
    full_profile["equipment"] = prompt_for_equipment()
    personality_details = prompt_for_personality_details()
    full_profile.update(
        {
            "personality_traits": personality_details[0],
            "ideals": personality_details[1],
            "bonds": personality_details[2],
            "flaws": personality_details[3],
            "background": personality_details[4],
        }
    )

    # Get spells and abilities
    spells_abilities = prompt_for_spells_and_abilities()
    full_profile.update(
        {
            "known_spells": spells_abilities[0],
            "spell_slots": spells_abilities[1],
            "class_abilities": spells_abilities[2],
            "feats": spells_abilities[3],
        }
    )

    # Optional fields
    full_profile.update(
        {
            "backstory": npc_data.get("notes", None),
            "skills": {},
            "magic_items": [],
            "specialized_abilities": [],
            "major_plot_actions": [],
        }
    )

    return full_profile


def _build_default_profile(npc_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build full profile using default values.

    Args:
        npc_data: Existing simplified NPC data

    Returns:
        Full profile dictionary with default combat stats
    """
    full_profile = npc_data.copy()
    full_profile["profile_type"] = "full"

    # Set defaults
    if "faction" not in full_profile:
        full_profile["faction"] = "neutral"

    full_profile.update(
        {
            "dnd_class": "Fighter",
            "subclass": None,
            "level": 1,
            "ability_scores": DEFAULT_ABILITY_SCORES.copy(),
            "skills": {},
            "max_hit_points": 10,
            "armor_class": 10,
            "movement_speed": 30,
            "proficiency_bonus": 2,
            "equipment": DEFAULT_EQUIPMENT.copy(),
            "spell_slots": {},
            "known_spells": [],
            "background": None,
            "personality_traits": [],
            "ideals": [],
            "bonds": [],
            "flaws": [],
            "backstory": npc_data.get("notes", None),
            "feats": [],
            "magic_items": [],
            "class_abilities": [],
            "specialized_abilities": [],
            "major_plot_actions": [],
        }
    )

    return full_profile


def migrate_npc_to_full_profile(
    npc_filepath: str, output_filepath: Optional[str] = None, interactive: bool = True
) -> str:
    """
    Convert a simplified NPC profile to a full character profile.

    Args:
        npc_filepath: Path to simplified NPC JSON file
        output_filepath: Optional output path (defaults to same file with '_full' suffix)
        interactive: If True, prompts user for missing details. If False, uses defaults.

    Returns:
        Path to the created full profile file
    """
    print(f"\nMigrating NPC profile: {npc_filepath}")

    # Load existing NPC profile
    npc_data = load_json_file(npc_filepath)
    if not npc_data:
        raise ValueError(f"Could not load NPC file: {npc_filepath}")

    # Check if already a full profile
    if npc_data.get("profile_type") == "full":
        print("[WARNING] This NPC already has a full profile.")
        return npc_filepath

    # Build full profile using appropriate helper
    if interactive:
        full_profile = _build_interactive_profile(npc_data)
    else:
        full_profile = _build_default_profile(npc_data)

    # Copy specialized abilities from existing profile
    full_profile["specialized_abilities"] = npc_data.get("abilities", [])

    # Validate the full profile
    is_valid, errors = validate_npc_json(full_profile)
    if not is_valid:
        print("\n[WARNING] Validation errors found:")
        for validation_error in errors:
            print(f"  - {validation_error}")
        print("Saving anyway, but please fix these issues manually.")

    # Determine output filepath
    if not output_filepath:
        filepath = Path(npc_filepath)
        output_filepath = str(
            filepath.parent / f"{filepath.stem}_full{filepath.suffix}"
        )

    # Save the full profile
    save_json_file(output_filepath, full_profile)
    print(f"\n[SUCCESS] Full profile saved to: {output_filepath}")

    return output_filepath


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(
            "Usage: python -m src.utils.npc_migration <npc_filepath> [output_filepath]"
        )
        print("\nExample:")
        print("  python -m src.utils.npc_migration game_data/npcs/butterbur.json")
        sys.exit(1)

    npc_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        result = migrate_npc_to_full_profile(npc_file, output_file)
        print(f"\nMigration complete: {result}")
    except (ValueError, KeyError, OSError) as e:
        error = DnDError(
            message=f"Migration failed: {e}",
            user_guidance="Check the NPC file format and permissions.",
            recoverable=False
        )
        display_error(error)
        sys.exit(1)
