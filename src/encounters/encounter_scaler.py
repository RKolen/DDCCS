"""Encounter difficulty scaling and calculation.

Provides tools for assessing and scaling combat encounters based on
party composition, level, and enemy XP values following D&D 5e guidelines.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Tuple

from src.utils.dnd_rules import (
    DifficultyTier,
    get_dc_for_difficulty,
    get_proficiency_bonus,
)


class EncounterDifficulty(Enum):
    """Overall encounter difficulty ratings."""

    TRIVIAL = "trivial"
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    DEADLY = "deadly"


@dataclass
class PartyMember:
    """Represents a party member for encounter scaling."""

    name: str
    level: int
    character_class: str
    max_hp: int
    armor_class: int

    @property
    def proficiency_bonus(self) -> int:
        """Proficiency bonus derived from character level.

        Returns:
            Proficiency bonus for this member's level.
        """
        return get_proficiency_bonus(self.level)


@dataclass
class EncounterMetrics:
    """Calculated metrics for an encounter."""

    difficulty: EncounterDifficulty
    average_party_level: float
    effective_party_size: float
    suggested_dc_range: Tuple[int, int]
    threat_level: str
    resource_drain_estimate: str


# XP thresholds by character level for encounter difficulty (D&D 5e DMG)
_XP_THRESHOLDS: Dict[int, Dict[EncounterDifficulty, int]] = {
    1:  {EncounterDifficulty.EASY: 25,   EncounterDifficulty.MEDIUM: 50,
         EncounterDifficulty.HARD: 75,   EncounterDifficulty.DEADLY: 100},
    2:  {EncounterDifficulty.EASY: 50,   EncounterDifficulty.MEDIUM: 100,
         EncounterDifficulty.HARD: 150,  EncounterDifficulty.DEADLY: 200},
    3:  {EncounterDifficulty.EASY: 75,   EncounterDifficulty.MEDIUM: 150,
         EncounterDifficulty.HARD: 225,  EncounterDifficulty.DEADLY: 400},
    4:  {EncounterDifficulty.EASY: 125,  EncounterDifficulty.MEDIUM: 250,
         EncounterDifficulty.HARD: 375,  EncounterDifficulty.DEADLY: 500},
    5:  {EncounterDifficulty.EASY: 250,  EncounterDifficulty.MEDIUM: 500,
         EncounterDifficulty.HARD: 750,  EncounterDifficulty.DEADLY: 1100},
    6:  {EncounterDifficulty.EASY: 300,  EncounterDifficulty.MEDIUM: 600,
         EncounterDifficulty.HARD: 900,  EncounterDifficulty.DEADLY: 1400},
    7:  {EncounterDifficulty.EASY: 350,  EncounterDifficulty.MEDIUM: 750,
         EncounterDifficulty.HARD: 1100, EncounterDifficulty.DEADLY: 1700},
    8:  {EncounterDifficulty.EASY: 450,  EncounterDifficulty.MEDIUM: 900,
         EncounterDifficulty.HARD: 1400, EncounterDifficulty.DEADLY: 2100},
    9:  {EncounterDifficulty.EASY: 550,  EncounterDifficulty.MEDIUM: 1100,
         EncounterDifficulty.HARD: 1600, EncounterDifficulty.DEADLY: 2400},
    10: {EncounterDifficulty.EASY: 600,  EncounterDifficulty.MEDIUM: 1200,
         EncounterDifficulty.HARD: 1900, EncounterDifficulty.DEADLY: 2800},
    11: {EncounterDifficulty.EASY: 800,  EncounterDifficulty.MEDIUM: 1600,
         EncounterDifficulty.HARD: 2400, EncounterDifficulty.DEADLY: 3600},
    12: {EncounterDifficulty.EASY: 1000, EncounterDifficulty.MEDIUM: 2000,
         EncounterDifficulty.HARD: 3000, EncounterDifficulty.DEADLY: 4500},
    13: {EncounterDifficulty.EASY: 1100, EncounterDifficulty.MEDIUM: 2200,
         EncounterDifficulty.HARD: 3400, EncounterDifficulty.DEADLY: 5100},
    14: {EncounterDifficulty.EASY: 1250, EncounterDifficulty.MEDIUM: 2500,
         EncounterDifficulty.HARD: 3800, EncounterDifficulty.DEADLY: 5700},
    15: {EncounterDifficulty.EASY: 1400, EncounterDifficulty.MEDIUM: 2800,
         EncounterDifficulty.HARD: 4300, EncounterDifficulty.DEADLY: 6400},
    16: {EncounterDifficulty.EASY: 1600, EncounterDifficulty.MEDIUM: 3200,
         EncounterDifficulty.HARD: 4800, EncounterDifficulty.DEADLY: 7200},
    17: {EncounterDifficulty.EASY: 2000, EncounterDifficulty.MEDIUM: 3900,
         EncounterDifficulty.HARD: 5900, EncounterDifficulty.DEADLY: 8800},
    18: {EncounterDifficulty.EASY: 2100, EncounterDifficulty.MEDIUM: 4200,
         EncounterDifficulty.HARD: 6300, EncounterDifficulty.DEADLY: 9500},
    19: {EncounterDifficulty.EASY: 2400, EncounterDifficulty.MEDIUM: 4900,
         EncounterDifficulty.HARD: 7300, EncounterDifficulty.DEADLY: 10900},
    20: {EncounterDifficulty.EASY: 2800, EncounterDifficulty.MEDIUM: 5700,
         EncounterDifficulty.HARD: 8500, EncounterDifficulty.DEADLY: 12700},
}

# Party size multipliers applied to XP thresholds
_PARTY_SIZE_MULTIPLIERS: Dict[int, float] = {
    1: 0.5,
    2: 0.75,
    3: 1.0,
    4: 1.0,
    5: 1.25,
    6: 1.5,
    7: 1.75,
    8: 2.0,
}

# Enemy count multipliers applied to adjusted XP
_ENEMY_COUNT_MULTIPLIERS: Dict[int, float] = {
    1: 1.0,
    2: 1.5,
    3: 2.0,
    4: 2.0,
    5: 2.0,
    6: 2.0,
    7: 2.5,
    8: 2.5,
    9: 2.5,
    10: 2.5,
    11: 3.0,
    12: 3.0,
    13: 3.0,
    14: 3.0,
    15: 4.0,
}

_RESOURCE_DRAIN: Dict[EncounterDifficulty, str] = {
    EncounterDifficulty.TRIVIAL: "none",
    EncounterDifficulty.EASY: "low",
    EncounterDifficulty.MEDIUM: "medium",
    EncounterDifficulty.HARD: "high",
    EncounterDifficulty.DEADLY: "extreme",
}

_THREAT_DESCRIPTIONS: Dict[EncounterDifficulty, str] = {
    EncounterDifficulty.TRIVIAL: "Negligible - party should handle easily",
    EncounterDifficulty.EASY: "Low - minor challenge expected",
    EncounterDifficulty.MEDIUM: "Moderate - fair fight for the party",
    EncounterDifficulty.HARD: "High - significant risk of setbacks",
    EncounterDifficulty.DEADLY: "Extreme - character death possible",
}


class EncounterScaler:
    """Calculates and scales encounter difficulty for a given party."""

    def __init__(self, party: List[PartyMember]) -> None:
        """Initialise with a list of party members.

        Args:
            party: List of PartyMember instances representing the adventuring party.
        """
        self.party = party

    @property
    def average_level(self) -> float:
        """Average level across all party members.

        Returns:
            Average party level, or 1.0 for an empty party.
        """
        if not self.party:
            return 1.0
        return sum(m.level for m in self.party) / len(self.party)

    @property
    def party_size(self) -> int:
        """Number of party members.

        Returns:
            Count of members in the party.
        """
        return len(self.party)

    def get_party_xp_threshold(self, difficulty: EncounterDifficulty) -> int:
        """Calculate the total XP threshold for the party at a given difficulty.

        Args:
            difficulty: The encounter difficulty to calculate for.

        Returns:
            Total XP threshold for the party (size-adjusted).
        """
        total = sum(
            _XP_THRESHOLDS.get(member.level, {}).get(difficulty, 0)
            for member in self.party
        )
        size_mult = _PARTY_SIZE_MULTIPLIERS.get(self.party_size, 1.0)
        return int(total * size_mult)

    def assess_encounter(
        self,
        enemy_xp_total: int,
        enemy_count: int = 1,
    ) -> EncounterMetrics:
        """Assess encounter difficulty based on enemy XP.

        Args:
            enemy_xp_total: Total XP value of all enemies.
            enemy_count: Number of enemies in the encounter.

        Returns:
            EncounterMetrics with difficulty assessment and DC suggestions.
        """
        encounter_multiplier = self._get_encounter_multiplier(enemy_count)
        adjusted_xp = enemy_xp_total * encounter_multiplier

        difficulty = self._classify_difficulty(adjusted_xp)

        avg_level = int(self.average_level)
        easy_dc = get_dc_for_difficulty(DifficultyTier.EASY, avg_level)
        hard_dc = get_dc_for_difficulty(DifficultyTier.HARD, avg_level)

        return EncounterMetrics(
            difficulty=difficulty,
            average_party_level=self.average_level,
            effective_party_size=self.party_size * encounter_multiplier,
            suggested_dc_range=(easy_dc, hard_dc),
            threat_level=_THREAT_DESCRIPTIONS.get(difficulty, "Unknown"),
            resource_drain_estimate=_RESOURCE_DRAIN.get(difficulty, "medium"),
        )

    def suggest_encounter_dc(
        self,
        check_type: str,
        desired_difficulty: DifficultyTier = DifficultyTier.MEDIUM,
    ) -> int:
        """Suggest DC for a check in this encounter.

        Args:
            check_type: Type of check (e.g. 'attack', 'save', 'skill').
            desired_difficulty: How hard the check should be.

        Returns:
            Suggested DC value scaled to average party level.
        """
        _ = check_type  # reserved for future check-type-specific modifiers
        avg_level = int(round(self.average_level))
        return get_dc_for_difficulty(desired_difficulty, avg_level)

    def _classify_difficulty(self, adjusted_xp: float) -> EncounterDifficulty:
        """Classify encounter difficulty based on adjusted XP vs thresholds.

        Args:
            adjusted_xp: Enemy XP total after applying encounter multiplier.

        Returns:
            EncounterDifficulty rating.
        """
        if adjusted_xp <= self.get_party_xp_threshold(EncounterDifficulty.EASY):
            return EncounterDifficulty.TRIVIAL
        if adjusted_xp <= self.get_party_xp_threshold(EncounterDifficulty.MEDIUM):
            return EncounterDifficulty.EASY
        if adjusted_xp <= self.get_party_xp_threshold(EncounterDifficulty.HARD):
            return EncounterDifficulty.MEDIUM
        if adjusted_xp <= self.get_party_xp_threshold(EncounterDifficulty.DEADLY):
            return EncounterDifficulty.HARD
        return EncounterDifficulty.DEADLY

    @staticmethod
    def _get_encounter_multiplier(enemy_count: int) -> float:
        """Get XP multiplier for the number of enemies.

        Args:
            enemy_count: Number of enemies in the encounter.

        Returns:
            Multiplier value (1.0-4.0).
        """
        return _ENEMY_COUNT_MULTIPLIERS.get(enemy_count, 4.0)


def build_party_from_characters(characters: List[Dict]) -> List[PartyMember]:
    """Build a list of PartyMember objects from character dictionaries.

    Args:
        characters: List of character data dicts containing at minimum
            'name', 'level', 'class', 'max_hp', and 'armor_class' keys.

    Returns:
        List of PartyMember instances.
    """
    members: List[PartyMember] = []
    for char in characters:
        members.append(
            PartyMember(
                name=char.get("name", "Unknown"),
                level=int(char.get("level", 1)),
                character_class=char.get("class", "Fighter"),
                max_hp=int(char.get("max_hp", 10)),
                armor_class=int(char.get("armor_class", 10)),
            )
        )
    return members
