"""
Character Sheet data structures for D&D 5e characters.

Note: This file contains enums and reference data used across the project.
The actual character profile implementation is in consultants/character_profile.py
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
class NPCBasicInfo:
    """Basic identifying information for an NPC."""

    name: str
    nickname: Optional[str] = None
    role: str = "NPC"
    recurring: bool = False


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


@dataclass
class NPCProfile:
    """NPC character profile for D&D campaigns.

    This is a lightweight wrapper that groups related NPC information
    into logical categories (basic, physical, character).
    """

    basic: NPCBasicInfo
    physical: NPCPhysicalInfo = field(default_factory=NPCPhysicalInfo)
    character: NPCCharacterInfo = field(default_factory=NPCCharacterInfo)
    ai_config: Optional[Dict] = (
        None  # Optional AI configuration (can be dict or CharacterAIConfig)
    )

    @classmethod
    def create(cls, name: str, **kwargs) -> "NPCProfile":
        """Create an NPCProfile from individual fields (backward compatibility).

        Args:
            name: NPC name (required)
            **kwargs: Optional fields:
                - nickname: Optional nickname
                - role: NPC role (default: "NPC")
                - species: Species/ancestry (default: "Human")
                - lineage: Lineage/subspecies (default: "")
                - personality: Personality description (default: "")
                - relationships: Dict of relationships (default: {})
                - key_traits: List of traits (default: [])
                - abilities: List of abilities (default: [])
                - recurring: Whether NPC is recurring (default: False)
                - notes: Additional notes (default: "")

        Returns:
            NPCProfile instance
        """
        return cls(
            basic=NPCBasicInfo(
                name=name,
                nickname=kwargs.get("nickname"),
                role=kwargs.get("role", "NPC"),
                recurring=kwargs.get("recurring", False),
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

    @property
    def name(self) -> str:
        """Get NPC name (for backward compatibility)."""
        return self.basic.name

    @property
    def nickname(self) -> Optional[str]:
        """Get NPC nickname (for backward compatibility)."""
        return self.basic.nickname

    @property
    def role(self) -> str:
        """Get NPC role (for backward compatibility)."""
        return self.basic.role

    @property
    def species(self) -> str:
        """Get NPC species (for backward compatibility)."""
        return self.physical.species

    @property
    def lineage(self) -> str:
        """Get NPC lineage (for backward compatibility)."""
        return self.physical.lineage

    @property
    def personality(self) -> str:
        """Get NPC personality (for backward compatibility)."""
        return self.character.personality

    @property
    def relationships(self) -> Dict[str, str]:
        """Get NPC relationships (for backward compatibility)."""
        return self.character.relationships

    @property
    def key_traits(self) -> List[str]:
        """Get NPC key traits (for backward compatibility)."""
        return self.character.key_traits

    @property
    def abilities(self) -> List[str]:
        """Get NPC abilities (for backward compatibility)."""
        return self.character.abilities

    @property
    def recurring(self) -> bool:
        """Get NPC recurring status (for backward compatibility)."""
        return self.basic.recurring

    @property
    def notes(self) -> str:
        """Get NPC notes (for backward compatibility)."""
        return self.character.notes
