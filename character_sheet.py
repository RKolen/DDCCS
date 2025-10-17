"""
Character Sheet data structures for D&D 5e characters.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class DnDClass(Enum):
    """D&D 5e character classes."""

    BARBARIAN = "Barbarian"
    BARD = "Bard"
    CLERIC = "Cleric"
    DRUID = "Druid"
    FIGHTER = "Fighter"
    MONK = "Monk"
    PALADIN = "Paladin"
    RANGER = "Ranger"
    ROGUE = "Rogue"
    SORCERER = "Sorcerer"
    WARLOCK = "Warlock"
    WIZARD = "Wizard"


class Species(Enum):
    """D&D 5e character species/ancestries."""

    AASIMAR = "Aasimar"
    HUMAN = "Human"
    ELF = "Elf"
    DWARF = "Dwarf"
    HALFLING = "Halfling"
    DRAGONBORN = "Dragonborn"
    GNOME = "Gnome"
    GOLIATH = "Goliath"
    ORC = "Orc"
    TIEFLING = "Tiefling"


# Lineage/subspecies definitions
ELF_LINEAGES = ["High Elf", "Wood Elf", "Drow"]
GNOME_LINEAGES = ["Forest Gnome", "Rock Gnome"]
TIEFLING_LINEAGES = ["Chthonic", "Abyssal", "Infernal"]
DRAGONBORN_LINEAGES = [
    "Black (Chromatic)",
    "Blue (Chromatic)",
    "Green (Chromatic)",
    "Red (Chromatic)",
    "White (Chromatic)",
    "Brass (Metallic)",
    "Bronze (Metallic)",
    "Copper (Metallic)",
    "Gold (Metallic)",
    "Silver (Metallic)",
]
GOLIATH_LINEAGES = [
    "Hill Giant",
    "Cloud Giant",
    "Fire Giant",
    "Frost Giant",
    "Stone Giant",
    "Storm Giant",
]


@dataclass
class AbilityScores:
    """D&D 5e ability scores."""

    strength: int = 10
    dexterity: int = 10
    constitution: int = 10
    intelligence: int = 10
    wisdom: int = 10
    charisma: int = 10

    def get_modifier(self, ability: str) -> int:
        """Calculate the modifier for a given ability score."""
        score = getattr(self, ability.lower(), 10)
        return (score - 10) // 2


@dataclass
class Skills:  # pylint: disable=too-many-instance-attributes
    """D&D 5e skills."""

    acrobatics: int = 0
    animal_handling: int = 0
    arcana: int = 0
    athletics: int = 0
    deception: int = 0
    history: int = 0
    insight: int = 0
    intimidation: int = 0
    investigation: int = 0
    medicine: int = 0
    nature: int = 0
    perception: int = 0
    performance: int = 0
    persuasion: int = 0
    religion: int = 0
    sleight_of_hand: int = 0
    stealth: int = 0
    survival: int = 0


@dataclass
class Equipment:  # pylint: disable=too-many-instance-attributes
    """D&D 5e equipment."""

    weapons: List[str] = field(default_factory=list)
    armor: List[str] = field(default_factory=list)
    items: List[str] = field(default_factory=list)
    gold: int = 0


@dataclass
class Spell: # pylint: disable=too-many-instance-attributes
    """D&D 5e spell."""

    name: str
    level: int
    school: str
    casting_time: str
    range: str
    components: str
    duration: str
    description: str
    damage: Optional[str] = None


@dataclass
class CharacterSheet:  # pylint: disable=too-many-instance-attributes
    """Complete D&D 5e character sheet matching JSON structure."""

    name: str
    species: str
    dnd_class: str
    lineage: Optional[str] = None
    subclass: Optional[str] = None
    level: int = 1
    ability_scores: Dict[str, int] = field(default_factory=dict)
    skills: Dict[str, int] = field(default_factory=dict)
    max_hit_points: int = 8
    armor_class: int = 10
    movement_speed: int = 30
    proficiency_bonus: int = 2
    equipment: Dict[str, List[str]] = field(default_factory=dict)
    spell_slots: Dict[str, int] = field(default_factory=dict)
    known_spells: List[str] = field(default_factory=list)
    background: str = ""
    personality_traits: List[str] = field(default_factory=list)
    ideals: List[str] = field(default_factory=list)
    bonds: List[str] = field(default_factory=list)
    flaws: List[str] = field(default_factory=list)
    backstory: str = ""
    feats: List[str] = field(default_factory=list)
    magic_items: List[str] = field(default_factory=list)
    class_abilities: List[str] = field(default_factory=list)
    specialized_abilities: List[str] = field(default_factory=list)
    major_plot_actions: List[dict] = field(default_factory=list)
    relationships: Dict[str, str] = field(default_factory=dict)

    def get_major_plot_actions(self) -> List[dict]:
        """Return the character's major plot actions."""
        return self.major_plot_actions

    def get_ability_modifier(self, ability: str) -> int:
        """Get the modifier for a given ability score."""
        score = self.ability_scores.get(ability, 10)
        return (score - 10) // 2

    def get_skill_bonus(self, skill: str) -> int:
        """Calculate total skill bonus including ability modifier and proficiency."""
        skill_value = self.skills.get(skill, 0)

        # Map skills to their governing abilities
        skill_abilities = {
            "acrobatics": "dexterity",
            "animal_handling": "wisdom",
            "arcana": "intelligence",
            "athletics": "strength",
            "deception": "charisma",
            "history": "intelligence",
            "insight": "wisdom",
            "intimidation": "charisma",
            "investigation": "intelligence",
            "medicine": "wisdom",
            "nature": "intelligence",
            "perception": "wisdom",
            "performance": "charisma",
            "persuasion": "charisma",
            "religion": "intelligence",
            "sleight_of_hand": "dexterity",
            "stealth": "dexterity",
            "survival": "wisdom",
        }

        ability = skill_abilities.get(skill, "strength")
        ability_mod = self.get_ability_modifier(ability)

        # If skill is trained (non-zero), add proficiency bonus
        proficiency = self.proficiency_bonus if skill_value > 0 else 0

        return ability_mod + proficiency + skill_value

    def can_cast_spell(self, spell_level: int) -> bool:
        """Check if character has spell slots for given level."""
        return self.spell_slots.get(str(spell_level), 0) > 0

    def use_spell_slot(self, spell_level: int) -> bool:
        """Use a spell slot of given level. Returns True if successful."""
        if self.can_cast_spell(spell_level):
            self.spell_slots[str(spell_level)] -= 1
            return True
        return False


# Base blank character template for manual entry
def create_blank_character(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    name: str = "",
    species: str = "Human",
    lineage: str = None,
    character_class: str = "Fighter",
    subclass: str = None,
    movement_speed: int = 30,
    feats: list = None,
    magic_items: list = None,
    class_abilities: list = None,
    specialized_abilities: list = None,
) -> CharacterSheet:
    """Create a blank character sheet for manual entry."""
    # Set up default ability scores and skills
    default_abilities = {
        "strength": 10,
        "dexterity": 10,
        "constitution": 10,
        "intelligence": 10,
        "wisdom": 10,
        "charisma": 10,
    }

    default_skills = {
        "acrobatics": 0,
        "animal_handling": 0,
        "arcana": 0,
        "athletics": 0,
        "deception": 0,
        "history": 0,
        "insight": 0,
        "intimidation": 0,
        "investigation": 0,
        "medicine": 0,
        "nature": 0,
        "perception": 0,
        "performance": 0,
        "persuasion": 0,
        "religion": 0,
        "sleight_of_hand": 0,
        "stealth": 0,
        "survival": 0,
    }

    default_equipment = {"weapons": [], "armor": [], "items": []}

    return CharacterSheet(
        name=name,
        species=species,
        lineage=lineage,
        dnd_class=character_class,
        subclass=subclass,
        level=1,
        ability_scores=default_abilities,
        skills=default_skills,
        max_hit_points=8,
        armor_class=10,
        movement_speed=movement_speed,
        proficiency_bonus=2,
        equipment=default_equipment,
        spell_slots={},
        known_spells=[],
        background="",
        personality_traits=[],
        ideals=[],
        bonds=[],
        flaws=[],
        backstory="",
        feats=feats if feats is not None else [],
        magic_items=magic_items if magic_items is not None else [],
        class_abilities=class_abilities if class_abilities is not None else [],
        specialized_abilities=(
            specialized_abilities if specialized_abilities is not None else []
        ),
        major_plot_actions=[],
        relationships={},
    )


@dataclass
class NPCProfile:  # pylint: disable=too-many-instance-attributes
    """NPC character profile for D&D campaigns."""

    name: str
    nickname: Optional[str] = None
    role: str = "NPC"
    species: str = "Human"  # Species/ancestry (e.g., "Elf", "Dwarf", "Human")
    lineage: str = ""  # Optional lineage/subspecies (e.g., "High Elf", "Hill Dwarf")
    personality: str = ""
    relationships: Dict[str, str] = field(default_factory=dict)
    key_traits: List[str] = field(default_factory=list)
    abilities: List[str] = field(default_factory=list)
    recurring: bool = False
    notes: str = ""
