"""
Character Template System

Provides template loading, validation, and level-scaling utilities for
creating D&D 2024 characters from pre-configured class archetypes.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from src.utils.file_io import load_json_file
from src.utils.path_utils import get_character_templates_dir
from src.utils.dnd_rules import PROFICIENCY_BY_LEVEL


# Alias for the shared proficiency bonus table (D&D 2024).
PROFICIENCY_BONUS_BY_LEVEL: Dict[int, int] = PROFICIENCY_BY_LEVEL

# Levels at which Ability Score Improvements are granted (most classes).
ASI_LEVELS: List[int] = [4, 8, 12, 16, 19]


@dataclass
class TemplateOptions:
    """Options for customising a character created from a template.

    Attributes:
        name: Character name.
        race: Character species/race.
        level: Target character level (1-20).
        background: Character background name.
        subclass: Optional subclass selection.
        ability_scores: Optional ability score overrides. If None, the
            template's base_ability_scores are used.
        skills: Optional list of selected skill proficiency names.
    """

    name: str
    race: str = "Human"
    level: int = 1
    background: str = ""
    subclass: Optional[str] = None
    ability_scores: Optional[Dict[str, int]] = None
    skills: List[str] = field(default_factory=list)


def calculate_modifier(score: int) -> int:
    """Calculate the ability score modifier for a given score.

    Args:
        score: Ability score value.

    Returns:
        Modifier value (can be negative).
    """
    return (score - 10) // 2


def calculate_hit_points(hit_die: int, constitution_score: int, level: int) -> int:
    """Calculate maximum hit points for a given level.

    Level 1 grants the maximum hit die value plus Constitution modifier.
    Each subsequent level grants the average (rounded up) plus Constitution modifier.

    Args:
        hit_die: The size of the class hit die (6, 8, 10, or 12).
        constitution_score: The character's Constitution score.
        level: The target character level (1-20).

    Returns:
        Maximum hit points, with a minimum of 1 per level.
    """
    constitution_mod = calculate_modifier(constitution_score)
    hp = hit_die + constitution_mod
    average_hit_die = (hit_die // 2) + 1
    hp += (average_hit_die + constitution_mod) * (level - 1)
    return max(hp, level)


def get_proficiency_bonus(level: int) -> int:
    """Get the proficiency bonus for a given character level.

    Args:
        level: Character level (1-20).

    Returns:
        Proficiency bonus value.

    Raises:
        ValueError: If level is not in the range 1-20.
    """
    if level not in PROFICIENCY_BONUS_BY_LEVEL:
        raise ValueError(f"Level must be between 1 and 20, got {level}")
    return PROFICIENCY_BONUS_BY_LEVEL[level]


def get_class_features_up_to_level(
    class_features: Dict[str, List[str]], level: int
) -> List[str]:
    """Collect all class features gained up to and including the target level.

    Args:
        class_features: Mapping of level string to list of feature names.
        level: Target character level.

    Returns:
        Flat list of all features gained at or below the target level.
    """
    features: List[str] = []
    for lvl_str, lvl_features in class_features.items():
        try:
            lvl = int(lvl_str)
        except ValueError:
            continue
        if lvl <= level:
            features.extend(lvl_features)
    return features


def get_spell_slots_for_level(
    spellcasting: Optional[Dict[str, Any]], level: int
) -> Dict[str, int]:
    """Retrieve spell slots for a given character level from a template.

    Args:
        spellcasting: The spellcasting block from a template (may be None).
        level: Target character level.

    Returns:
        Dictionary mapping spell level string to slot count, or empty dict
        if the class has no spellcasting or has not yet gained slots.
    """
    if not spellcasting:
        return {}
    spell_slots_table = spellcasting.get("spell_slots", {})
    if str(level) in spell_slots_table:
        return dict(spell_slots_table[str(level)])
    # For half-casters, find the closest lower level that has slots.
    for lvl in range(level, 0, -1):
        if str(lvl) in spell_slots_table:
            return dict(spell_slots_table[str(lvl)])
    return {}


def load_template(class_name: str) -> Optional[Dict[str, Any]]:
    """Load a character template by class name.

    Args:
        class_name: The D&D class name (case-insensitive, e.g. 'Fighter').

    Returns:
        Template dictionary if found, None otherwise.
    """
    templates_dir = get_character_templates_dir()
    filepath = os.path.join(templates_dir, f"{class_name.lower()}.json")
    if not os.path.isfile(filepath):
        return None
    return load_json_file(filepath)


def list_available_templates() -> List[str]:
    """Return the names of all available class templates.

    Returns:
        Sorted list of class names (e.g. ['Barbarian', 'Bard', ...]).
    """
    templates_dir = get_character_templates_dir()
    if not os.path.isdir(templates_dir):
        return []
    names = []
    for entry in sorted(os.listdir(templates_dir)):
        if not entry.endswith(".json"):
            continue
        stem = entry[:-5]
        if stem != "schema":
            names.append(stem.capitalize())
    return names


def _build_skills_data(
    skill_list: List[str], saving_throws: List[str]
) -> Dict[str, Any]:
    """Build the skills dictionary with proficiency flags.

    Args:
        skill_list: Skill names the character is proficient in.
        saving_throws: Saving throw ability names the character is proficient in.

    Returns:
        Skills dictionary with proficiency markers.
    """
    skills_data: Dict[str, Any] = {}
    for skill in skill_list:
        skills_data[skill] = {"proficient": True}
    for saving_throw in saving_throws:
        skills_data[f"{saving_throw} Save"] = {"proficient": True}
    return skills_data


def _build_equipment_data(
    equipment: Dict[str, Any]
) -> Dict[str, List[str]]:
    """Build the equipment dictionary from a template's starting_equipment block.

    Args:
        equipment: The starting_equipment block from a template.

    Returns:
        Equipment dictionary with weapons, armor, and items lists.
    """
    return {
        "weapons": list(equipment.get("weapons", [])),
        "armor": list(equipment.get("armor", [])),
        "items": list(equipment.get("items", [])),
    }


def build_character_data_from_template(
    template: Dict[str, Any],
    options: TemplateOptions,
) -> Dict[str, Any]:
    """Build a character JSON data dictionary from a template.

    Uses the template defaults for all values not explicitly overridden.
    Calculates hit points, proficiency bonus, spell slots, and class
    features automatically for the target level.

    Args:
        template: Loaded template dictionary.
        options: Customisation options for the new character.

    Returns:
        Dictionary ready to be saved as a character JSON file.

    Raises:
        ValueError: If options.level is out of the valid 1-20 range.
    """
    if not 1 <= options.level <= 20:
        raise ValueError(f"Level must be between 1 and 20, got {options.level}")

    scores = options.ability_scores or template.get("base_ability_scores", {})
    max_hp = calculate_hit_points(
        template.get("hit_die", 8), scores.get("constitution", 10), options.level
    )
    features_list = [
        f for f in get_class_features_up_to_level(
            template.get("class_features", {}), options.level
        ) if f
    ]
    spell_slots = get_spell_slots_for_level(
        template.get("spellcasting"), options.level
    )
    skills_data = _build_skills_data(
        options.skills, template.get("saving_throws", [])
    )
    equipment_data = _build_equipment_data(template.get("starting_equipment", {}))

    return {
        "name": options.name,
        "species": options.race,
        "dnd_class": template.get("class", "Fighter"),
        "level": options.level,
        "subclass": options.subclass,
        "background": options.background,
        "backstory": "",
        "personality_traits": [],
        "bonds": [],
        "flaws": [],
        "ideals": [],
        "relationships": {},
        "ability_scores": {
            "strength": scores.get("strength", 10),
            "dexterity": scores.get("dexterity", 10),
            "constitution": scores.get("constitution", 10),
            "intelligence": scores.get("intelligence", 10),
            "wisdom": scores.get("wisdom", 10),
            "charisma": scores.get("charisma", 10),
        },
        "skills": skills_data,
        "max_hit_points": max_hp,
        "armor_class": 10,
        "movement_speed": 30,
        "proficiency_bonus": get_proficiency_bonus(options.level),
        "feats": [],
        "class_abilities": features_list,
        "specialized_abilities": [],
        "spell_slots": spell_slots,
        "known_spells": [],
        "equipment": equipment_data,
        "magic_items": [],
    }
