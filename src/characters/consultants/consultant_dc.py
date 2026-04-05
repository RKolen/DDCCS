"""
DC Calculation Component for Character Consultant

Provides DC (Difficulty Class) calculation methods for character actions,
including level-based scaling, class-specific bonuses, and alternative
approach suggestions.
"""

from typing import Any, Dict, List, Optional

from src.utils.dc_config import DCConfig, get_dc_config
from src.utils.dnd_rules import (
    DC_MEDIUM,
    DifficultyTier,
    get_proficiency_bonus,
)

# Action keyword groups used to classify a free-text action description
_ACTION_PATTERNS: Dict[str, List[str]] = {
    "Persuasion":    ["persuade", "convince", "negotiate", "bargain"],
    "Deception":     ["deceive", "lie", "bluff", "mislead"],
    "Intimidation":  ["intimidate", "threaten", "menace", "coerce"],
    "Stealth":       ["sneak", "hide", "stealth", "creep"],
    "Athletics":     ["climb", "jump", "swim", "athletics"],
    "Investigation": ["search", "investigate", "examine", "analyze"],
    "Perception":    ["notice", "spot", "perceive", "detect"],
    "Arcana":        ["cast", "identify", "dispel", "arcana"],
    "History":       ["recall", "remember", "history", "lore"],
    "Nature":        ["nature", "survival", "forage", "track"],
}

# Skill -> ability score mapping for success-chance estimation
_ABILITY_MAP: Dict[str, str] = {
    "Persuasion":    "charisma",
    "Deception":     "charisma",
    "Intimidation":  "charisma",
    "Stealth":       "dexterity",
    "Athletics":     "strength",
    "Investigation": "intelligence",
    "Perception":    "wisdom",
    "Arcana":        "intelligence",
    "History":       "intelligence",
    "Nature":        "wisdom",
}

# Class -> skill -> DC reduction (negative = easier for the character)
_CLASS_BONUSES: Dict[str, Dict[str, int]] = {
    "Rogue":     {"Stealth": -2, "Investigation": -2, "Deception": -1},
    "Bard":      {"Persuasion": -2, "Deception": -1, "Performance": -2},
    "Paladin":   {"Intimidation": -1, "Persuasion": -1},
    "Ranger":    {"Stealth": -1, "Perception": -2, "Athletics": -1},
    "Fighter":   {"Athletics": -2, "Intimidation": -1},
    "Barbarian": {"Athletics": -2, "Intimidation": -2},
    "Monk":      {"Athletics": -1, "Stealth": -1},
    "Cleric":    {"Persuasion": -1, "Insight": -2},
    "Wizard":    {"Investigation": -2, "Arcana": -2},
    "Sorcerer":  {"Persuasion": -1, "Intimidation": -1},
    "Warlock":   {"Deception": -1, "Intimidation": -1},
    "Druid":     {"Perception": -1, "Animal Handling": -2},
}

_ALTERNATIVE_APPROACHES: Dict[str, List[str]] = {
    "Barbarian": [
        "Use intimidation instead of persuasion",
        "Solve with strength if possible",
    ],
    "Bard":    ["Try a different social approach", "Use inspiration or performance"],
    "Cleric":  ["Invoke divine guidance", "Appeal to moral principles"],
    "Druid":   ["Use natural solutions", "Shape change for advantage"],
    "Fighter": ["Apply military tactics", "Use direct action"],
    "Monk":    ["Use patience and observation", "Apply martial arts discipline"],
    "Paladin": ["Lead by example", "Use divine sense"],
    "Ranger":  ["Use survival skills", "Apply tracking knowledge"],
    "Rogue":   ["Find a sneaky alternative", "Look for weak points"],
    "Sorcerer": ["Use innate magical intuition", "Trust instincts"],
    "Warlock": ["Consult patron knowledge", "Use eldritch powers"],
    "Wizard":  ["Research the problem first", "Apply magical analysis"],
}


def _classify_action(action_lower: str) -> tuple:
    """Classify an action string into (action_type, DifficultyTier).

    Args:
        action_lower: Lower-cased action description.

    Returns:
        Tuple of (action_type str, DifficultyTier).
    """
    action_type = "General"
    for atype, patterns in _ACTION_PATTERNS.items():
        if any(p in action_lower for p in patterns):
            action_type = atype
            break

    if any(w in action_lower for w in ["easy", "simple", "basic", "trivial"]):
        difficulty = DifficultyTier.EASY
    elif any(w in action_lower for w in ["hard", "difficult", "challenging"]):
        difficulty = DifficultyTier.HARD
    elif any(w in action_lower for w in ["impossible", "extreme", "legendary"]):
        difficulty = DifficultyTier.NEARLY_IMPOSSIBLE
    else:
        difficulty = DifficultyTier.MEDIUM

    return action_type, difficulty


class DCCalculator:
    """Handles DC calculations for character actions."""

    def __init__(
        self,
        profile: Any,
        class_knowledge: Dict[str, Any],
        config: Optional[DCConfig] = None,
    ) -> None:
        """Initialize DC calculator.

        Args:
            profile: CharacterProfile instance.
            class_knowledge: Class knowledge dictionary.
            config: Optional DC configuration override; loads default if None.
        """
        self.profile = profile
        self.class_knowledge = class_knowledge
        self.config = config or get_dc_config()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_class_dc_info(
        self, action_type: str
    ) -> tuple:
        """Return (class_label, class_adjustment) for DC calculation.

        Args:
            action_type: The skill/action type string.

        Returns:
            Tuple of (label str, adjustment int).
        """
        multiclass_entries = self.profile.identity.subtype.classes
        if multiclass_entries:
            adjustment = sum(
                _CLASS_BONUSES.get(c.name, {}).get(action_type, 0)
                for c in multiclass_entries
            )
            label = "/".join(c.name for c in multiclass_entries)
        else:
            adjustment = _CLASS_BONUSES.get(
                self.profile.character_class.value, {}
            ).get(action_type, 0)
            label = self.profile.character_class.value
        return label, adjustment

    def _estimate_success_chance(self, action_type: str, dc: int) -> Dict[str, Any]:
        """Estimate success probability based on character stats.

        Args:
            action_type: Skill/action type string.
            dc: Final DC value to beat.

        Returns:
            Dictionary with ability, modifier, proficiency_bonus, needed_roll,
            and success_probability fields.
        """
        ability = _ABILITY_MAP.get(action_type, "strength")
        ability_score = getattr(self.profile.ability_scores, ability, 10)
        modifier = (ability_score - 10) // 2
        prof_bonus = get_proficiency_bonus(self.profile.level)
        needed_roll = dc - modifier - prof_bonus

        if needed_roll <= 1:
            chance = 1.0
        elif needed_roll >= 20:
            chance = 0.05
        else:
            chance = (21 - needed_roll) / 20

        return {
            "ability": ability,
            "modifier": modifier,
            "proficiency_bonus": prof_bonus,
            "needed_roll": max(1, min(20, needed_roll)),
            "success_probability": f"{chance * 100:.0f}%",
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def suggest_dc_for_action(
        self,
        action_description: str,
        _character_abilities: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        """Suggest appropriate DC for an action this character wants to take.

        Uses level-based DC scaling from DCConfig and DifficultyTier. The
        returned dictionary is backward-compatible with the original API: it
        includes both 'suggested_dc' (legacy key) and 'difficulty_tier' plus
        'success_chance' (new fields added by the scaling plan).

        Args:
            action_description: Description of the action.
            _character_abilities: Reserved for future use (ignored).

        Returns:
            Dictionary with DC suggestion, reasoning, alternatives, and advantages.
        """
        action_lower = action_description.lower()
        action_type, difficulty_tier = _classify_action(action_lower)

        base_dc = self.config.get_dc(
            check_type=action_type,
            level=self.profile.level,
            difficulty=difficulty_tier,
        )

        class_label, class_adjustment = self._get_class_dc_info(action_type)
        final_dc = max(5, base_dc + class_adjustment)

        return {
            # Backward-compatible keys
            "action_type": action_type,
            "suggested_dc": final_dc,
            "reasoning": (
                f"Base DC {base_dc} for {difficulty_tier.value} {action_type} check "
                f"at level {self.profile.level}, adjusted by {class_label} class expertise"
            ),
            "alternative_approaches": self.suggest_alternative_approaches(
                action_description
            ),
            "character_advantage": self.check_character_advantages(action_type),
            # New fields from scaling plan
            "difficulty_tier": difficulty_tier.value,
            "base_dc": base_dc,
            "class_adjustment": class_adjustment,
            "success_chance": self._estimate_success_chance(action_type, final_dc),
        }

    def suggest_alternative_approaches(self, _action: str) -> List[str]:
        """Suggest alternative approaches based on character class.

        Args:
            _action: Action description (reserved for future context-aware suggestions).

        Returns:
            List of class-appropriate alternative approaches.
        """
        multiclass_entries = self.profile.identity.subtype.classes
        if multiclass_entries:
            approaches: List[str] = []
            for entry in multiclass_entries:
                approaches.extend(_ALTERNATIVE_APPROACHES.get(entry.name, []))
            return approaches if approaches else ["Consider character-appropriate alternatives"]

        return _ALTERNATIVE_APPROACHES.get(
            self.profile.character_class.value,
            ["Consider character-appropriate alternatives"],
        )

    def check_character_advantages(self, action_type: str) -> List[str]:
        """Check if character has natural advantages for this action type.

        Args:
            action_type: Type of action (Stealth, Persuasion, etc.)

        Returns:
            List of advantages the character has for this action.
        """
        advantages: List[str] = []

        multiclass_entries = self.profile.identity.subtype.classes
        class_names = (
            [c.name for c in multiclass_entries]
            if multiclass_entries
            else [self.profile.character_class.value]
        )

        for class_name in class_names:
            if class_name == "Rogue" and action_type in [
                "Stealth", "Investigation", "Sleight of Hand",
            ]:
                advantages.append("Expertise doubles proficiency bonus")
            elif class_name == "Bard" and action_type in [
                "Persuasion", "Deception", "Performance",
            ]:
                advantages.append(
                    "Jack of All Trades adds bonus to non-proficient checks"
                )
            elif class_name == "Ranger" and action_type in ["Perception", "Survival"]:
                advantages.append(
                    "Natural Explorer provides advantage in favored terrain"
                )

        if (
            "noble" in self.profile.background_story.lower()
            and action_type == "Persuasion"
        ):
            advantages.append("Noble background aids in social situations")
        elif "criminal" in self.profile.background_story.lower() and action_type in [
            "Stealth", "Deception",
        ]:
            advantages.append("Criminal background provides relevant experience")

        return advantages


# Keep DC_MEDIUM importable from this module for any legacy callers
__all__ = ["DCCalculator", "DC_MEDIUM"]
