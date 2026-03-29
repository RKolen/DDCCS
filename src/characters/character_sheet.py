"""
Character Sheet data structures for D&D 5e characters.

Note: This file contains enums and reference data used across the project.
The actual character profile implementation is in consultants/character_profile.py
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from src.characters.npc_constants import DEFAULT_ABILITY_SCORES, DEFAULT_EQUIPMENT


def _make_nested_property(attr_path: str, doc: str):
    """Create a property that accesses a nested attribute.

    Args:
        attr_path: Dot-separated path to the attribute (e.g., 'basic.name')
        doc: Documentation string for the property

    Returns:
        property object
    """

    def getter(self):
        obj = self
        for attr in attr_path.split("."):
            obj = getattr(obj, attr, None)
            if obj is None:
                return None
        return obj

    getter.__doc__ = doc
    return property(getter)


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
class NPCBasicInfo:
    """Basic identifying information for an NPC."""

    name: str
    nickname: Optional[str] = None
    role: str = "NPC"
    recurring: bool = False
    profile_type: str = "simplified"
    faction: str = "neutral"
    ai_config: Optional[Dict] = None


@dataclass
class NPCPhysicalInfo:
    """Physical characteristics of an NPC."""

    species: str = "Human"  # Species/ancestry (e.g., "Elf", "Dwarf", "Human")
    lineage: str = ""  # Optional lineage/subspecies (e.g., "High Elf", "Hill Dwarf")


@dataclass
class NPCCharacterInfo:
    """Character traits and story elements for an NPC."""

    personality: str = ""
    relationships: Dict[str, str] = field(default_factory=dict)
    key_traits: List[str] = field(default_factory=list)
    abilities: List[str] = field(default_factory=list)
    notes: str = ""


def _get_default_ability_scores():
    """Factory function for default ability scores."""
    return DEFAULT_ABILITY_SCORES.copy()


def _get_default_equipment():
    """Factory function for default equipment."""
    return DEFAULT_EQUIPMENT.copy()


@dataclass
class CharacterCombatStats:
    """Combat statistics for D&D 5e characters."""

    max_hit_points: int = 10
    armor_class: int = 10
    movement_speed: int = 30
    proficiency_bonus: int = 2
    ability_scores: Dict[str, int] = field(default_factory=_get_default_ability_scores)
    skills: Dict[str, int] = field(default_factory=dict)


@dataclass
class CharacterRoleplayStats:
    """Roleplay and personality statistics for D&D 5e characters."""

    background: Optional[str] = None
    personality_traits: List[str] = field(default_factory=list)
    ideals: List[str] = field(default_factory=list)
    bonds: List[str] = field(default_factory=list)
    flaws: List[str] = field(default_factory=list)
    backstory: Optional[str] = None


@dataclass
class SpellcraftInfo:
    """Spellcasting information for D&D 5e characters."""

    spell_slots: Dict[str, int] = field(default_factory=dict)
    known_spells: List[str] = field(default_factory=list)


@dataclass
class CharacterAbilities:
    """Spells, abilities, and special features for D&D 5e characters."""

    equipment: Dict[str, Any] = field(default_factory=_get_default_equipment)
    spellcraft: SpellcraftInfo = field(default_factory=SpellcraftInfo)
    feats: List[str] = field(default_factory=list)
    magic_items: List[str] = field(default_factory=list)
    class_abilities: List[str] = field(default_factory=list)
    specialized_abilities: List[str] = field(default_factory=list)
    major_plot_actions: List[str] = field(default_factory=list)


@dataclass
class FullCharacterStats:
    """Complete D&D 5e character statistics (for full NPC profiles)."""

    dnd_class: str = "Fighter"
    subclass: Optional[str] = None
    level: int = 1
    combat: CharacterCombatStats = field(default_factory=CharacterCombatStats)
    roleplay: CharacterRoleplayStats = field(default_factory=CharacterRoleplayStats)
    abilities: CharacterAbilities = field(default_factory=CharacterAbilities)


@dataclass
class MajorNPCStats:
    """BBEG-specific statistics for major NPC profiles.

    Holds boss encounter mechanics and plot data not present in regular
    full profiles: legendary actions, lair actions, regional effects,
    encounter tactics, plot hooks, and defeat conditions.
    """

    legendary_actions: Optional[Dict[str, Any]] = None
    lair_actions: Optional[Dict[str, Any]] = None
    regional_effects: Optional[Dict[str, Any]] = None
    encounter_tactics: List[str] = field(default_factory=list)
    plot_hooks: List[str] = field(default_factory=list)
    defeat_conditions: List[str] = field(default_factory=list)


@dataclass
class NPCProfile:
    """NPC character profile for D&D campaigns.

    Supports both simplified (narrative-focused) and full (combat-ready) profiles.
    - Simplified: Basic NPC fields for narrative elements
    - Full: Complete D&D 5e character stats + NPC fields
    """

    basic: NPCBasicInfo
    physical: NPCPhysicalInfo = field(default_factory=NPCPhysicalInfo)
    character: NPCCharacterInfo = field(default_factory=NPCCharacterInfo)
    combat_stats: Optional[FullCharacterStats] = None
    major_stats: Optional[MajorNPCStats] = None

    @classmethod
    def create(cls, name: str, **kwargs) -> "NPCProfile":
        """Create an NPCProfile from individual fields (backward compatibility).

        Args:
            name: NPC name (required)
            **kwargs: Optional fields for both simplified and full profiles

        Returns:
            NPCProfile instance
        """
        profile = cls(
            basic=NPCBasicInfo(
                name=name,
                nickname=kwargs.get("nickname"),
                role=kwargs.get("role", "NPC"),
                recurring=kwargs.get("recurring", False),
                profile_type=kwargs.get("profile_type", "simplified"),
                faction=kwargs.get("faction", "neutral"),
            ),
            physical=NPCPhysicalInfo(
                species=kwargs.get("species", "Human"),
                lineage=kwargs.get("lineage", ""),
            ),
            character=NPCCharacterInfo(
                personality=kwargs.get("personality", ""),
                relationships=kwargs.get("relationships", {}),
                key_traits=kwargs.get("key_traits", []),
                abilities=kwargs.get("abilities", []),
                notes=kwargs.get("notes", ""),
            ),
        )

        # Add full character profile if provided (also applies to "major")
        if kwargs.get("profile_type") in ("full", "major"):
            profile.combat_stats = FullCharacterStats(
                dnd_class=kwargs.get("dnd_class", "Fighter"),
                subclass=kwargs.get("subclass"),
                level=kwargs.get("level", 1),
                combat=CharacterCombatStats(
                    max_hit_points=kwargs.get("max_hit_points", 10),
                    armor_class=kwargs.get("armor_class", 10),
                    movement_speed=kwargs.get("movement_speed", 30),
                    proficiency_bonus=kwargs.get("proficiency_bonus", 2),
                    ability_scores=kwargs.get(
                        "ability_scores", DEFAULT_ABILITY_SCORES.copy()
                    ),
                    skills=kwargs.get("skills", {}),
                ),
                roleplay=CharacterRoleplayStats(
                    background=kwargs.get("background"),
                    personality_traits=kwargs.get("personality_traits", []),
                    ideals=kwargs.get("ideals", []),
                    bonds=kwargs.get("bonds", []),
                    flaws=kwargs.get("flaws", []),
                    backstory=kwargs.get("backstory"),
                ),
                abilities=CharacterAbilities(
                    equipment=kwargs.get("equipment", DEFAULT_EQUIPMENT.copy()),
                    spellcraft=SpellcraftInfo(
                        spell_slots=kwargs.get("spell_slots", {}),
                        known_spells=kwargs.get("known_spells", []),
                    ),
                    feats=kwargs.get("feats", []),
                    magic_items=kwargs.get("magic_items", []),
                    class_abilities=kwargs.get("class_abilities", []),
                    specialized_abilities=kwargs.get("specialized_abilities", []),
                    major_plot_actions=kwargs.get("major_plot_actions", []),
                ),
            )

        # Add major-only fields if provided
        if kwargs.get("profile_type") == "major":
            profile.major_stats = MajorNPCStats(
                legendary_actions=kwargs.get("legendary_actions"),
                lair_actions=kwargs.get("lair_actions"),
                regional_effects=kwargs.get("regional_effects"),
                encounter_tactics=kwargs.get("encounter_tactics", []),
                plot_hooks=kwargs.get("plot_hooks", []),
                defeat_conditions=kwargs.get("defeat_conditions", []),
            )

        return profile

    # Backward compatibility properties using helper
    name = _make_nested_property("basic.name", "NPC name")
    nickname = _make_nested_property("basic.nickname", "NPC nickname")
    role = _make_nested_property("basic.role", "NPC role")
    species = _make_nested_property("physical.species", "NPC species")
    lineage = _make_nested_property("physical.lineage", "NPC lineage")
    personality = _make_nested_property("character.personality", "NPC personality")
    relationships = _make_nested_property(
        "character.relationships", "NPC relationships"
    )
    key_traits = _make_nested_property("character.key_traits", "NPC key traits")
    abilities = _make_nested_property("character.abilities", "NPC abilities")
    recurring = _make_nested_property("basic.recurring", "NPC recurring status")
    notes = _make_nested_property("character.notes", "NPC notes")
    profile_type = _make_nested_property("basic.profile_type", "NPC profile type")
    faction = _make_nested_property("basic.faction", "NPC faction")

    @property
    def ai_config(self) -> Optional[Dict]:
        """Get NPC AI config (for backward compatibility)."""
        return self.basic.ai_config

    @ai_config.setter
    def ai_config(self, value: Optional[Dict]):
        """Set NPC AI config (for backward compatibility)."""
        self.basic.ai_config = value

    def is_full_profile(self) -> bool:
        """Check if this NPC has a full character profile (with combat stats).

        Returns True for both 'full' and 'major' profile types since major
        profiles include all full profile fields.
        """
        return self.basic.profile_type in ("full", "major") and self.combat_stats is not None

    def is_major_profile(self) -> bool:
        """Check if this NPC is a major NPC (BBEG or key antagonist/ally)."""
        return self.basic.profile_type == "major" and self.major_stats is not None

    def has_combat_stats(self) -> bool:
        """Alias for is_full_profile (for backward compatibility)."""
        return self.is_full_profile()

    # Full profile properties using helper
    dnd_class = _make_nested_property(
        "combat_stats.dnd_class", "NPC class (full profiles)"
    )
    level = _make_nested_property("combat_stats.level", "NPC level (full profiles)")
    ability_scores = _make_nested_property(
        "combat_stats.combat.ability_scores", "NPC ability scores (full profiles)"
    )
    max_hit_points = _make_nested_property(
        "combat_stats.combat.max_hit_points", "NPC max HP (full profiles)"
    )
    armor_class = _make_nested_property(
        "combat_stats.combat.armor_class", "NPC AC (full profiles)"
    )
    equipment = _make_nested_property(
        "combat_stats.abilities.equipment", "NPC equipment (full profiles)"
    )
    known_spells = _make_nested_property(
        "combat_stats.abilities.spellcraft.known_spells",
        "NPC known spells (full profiles)",
    )
    class_abilities = _make_nested_property(
        "combat_stats.abilities.class_abilities", "NPC class abilities (full profiles)"
    )
