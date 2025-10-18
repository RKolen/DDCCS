"""
DC Calculation Component for Character Consultant

Provides DC (Difficulty Class) calculation methods for character actions,
including class-specific bonuses and alternative approach suggestions.
"""

from typing import Dict, List, Any

from src.utils.dnd_rules import DC_MEDIUM


class DCCalculator:
    """Handles DC calculations for character actions."""

    def __init__(self, profile, class_knowledge):
        """
        Initialize DC calculator.

        Args:
            profile: CharacterProfile instance
            class_knowledge: Class knowledge dictionary
        """
        self.profile = profile
        self.class_knowledge = class_knowledge

    def suggest_dc_for_action(
        self, action_description: str, _character_abilities: Dict[str, int] = None
    ) -> Dict[str, Any]:
        """
        Suggest appropriate DC for an action this character wants to take.

        Args:
            action_description: Description of the action
            _character_abilities: Optional ability scores dict (reserved for future use)

        Returns:
            Dictionary with DC suggestion, reasoning, alternatives, and advantages
        """
        action_lower = action_description.lower()

        # Determine action type and base DC
        if any(word in action_lower for word in ["persuade", "convince", "negotiate"]):
            action_type = "Persuasion"
            base_dc = DC_MEDIUM
        elif any(word in action_lower for word in ["deceive", "lie", "bluff"]):
            action_type = "Deception"
            base_dc = DC_MEDIUM
        elif any(word in action_lower for word in ["intimidate", "threaten", "menace"]):
            action_type = "Intimidation"
            base_dc = DC_MEDIUM
        elif any(word in action_lower for word in ["sneak", "hide", "stealth"]):
            action_type = "Stealth"
            base_dc = DC_MEDIUM
        elif any(word in action_lower for word in ["climb", "jump", "athletics"]):
            action_type = "Athletics"
            base_dc = DC_MEDIUM
        elif any(word in action_lower for word in ["search", "investigate", "examine"]):
            action_type = "Investigation"
            base_dc = DC_MEDIUM
        elif any(word in action_lower for word in ["notice", "spot", "perceive"]):
            action_type = "Perception"
            base_dc = DC_MEDIUM
        else:
            action_type = "General"
            base_dc = DC_MEDIUM

        # Adjust DC based on difficulty indicators
        if any(word in action_lower for word in ["easy", "simple", "basic"]):
            adjusted_dc = base_dc - 5
        elif any(word in action_lower for word in ["hard", "difficult", "challenging"]):
            adjusted_dc = base_dc + 5
        elif any(
            word in action_lower for word in ["impossible", "extreme", "legendary"]
        ):
            adjusted_dc = base_dc + 10
        else:
            adjusted_dc = base_dc

        # Consider class strengths
        class_bonuses = {
            "Rogue": {"Stealth": -2, "Investigation": -2, "Deception": -1},
            "Bard": {"Persuasion": -2, "Deception": -1, "Performance": -2},
            "Paladin": {"Intimidation": -1, "Persuasion": -1},
            "Ranger": {"Stealth": -1, "Perception": -2, "Athletics": -1},
            "Fighter": {"Athletics": -2, "Intimidation": -1},
            "Barbarian": {"Athletics": -2, "Intimidation": -2},
            "Monk": {"Athletics": -1, "Stealth": -1},
            "Cleric": {"Persuasion": -1, "Insight": -2},
            "Wizard": {"Investigation": -2, "Arcana": -2},
            "Sorcerer": {"Persuasion": -1, "Intimidation": -1},
            "Warlock": {"Deception": -1, "Intimidation": -1},
            "Druid": {"Perception": -1, "Animal Handling": -2},
        }

        class_adjustment = class_bonuses.get(
            self.profile.character_class.value, {}
        ).get(action_type, 0)
        final_dc = max(5, adjusted_dc + class_adjustment)

        return {
            "action_type": action_type,
            "suggested_dc": final_dc,
            "reasoning": (
                f"Base DC {base_dc}, adjusted for difficulty and "
                f"{self.profile.character_class.value} abilities"
            ),
            "alternative_approaches": self.suggest_alternative_approaches(
                action_description
            ),
            "character_advantage": self.check_character_advantages(action_type),
        }

    def suggest_alternative_approaches(self, _action: str) -> List[str]:
        """
        Suggest alternative approaches based on character class.

        Args:
            _action: Action description (reserved for future context-aware suggestions)

        Returns:
            List of class-appropriate alternative approaches
        """
        class_name = self.profile.character_class.value

        approach_map = {
            "Barbarian": [
                "Use intimidation instead of persuasion",
                "Solve with strength if possible",
            ],
            "Bard": [
                "Try a different social approach",
                "Use inspiration or performance",
            ],
            "Cleric": ["Invoke divine guidance", "Appeal to moral principles"],
            "Druid": ["Use natural solutions", "Shape change for advantage"],
            "Fighter": ["Apply military tactics", "Use direct action"],
            "Monk": ["Use patience and observation", "Apply martial arts discipline"],
            "Paladin": ["Lead by example", "Use divine sense"],
            "Ranger": ["Use survival skills", "Apply tracking knowledge"],
            "Rogue": ["Find a sneaky alternative", "Look for weak points"],
            "Sorcerer": ["Use innate magical intuition", "Trust instincts"],
            "Warlock": ["Consult patron knowledge", "Use eldritch powers"],
            "Wizard": ["Research the problem first", "Apply magical analysis"],
        }

        return approach_map.get(
            class_name, ["Consider character-appropriate alternatives"]
        )

    def check_character_advantages(self, action_type: str) -> List[str]:
        """
        Check if character has natural advantages for this action type.

        Args:
            action_type: Type of action (Stealth, Persuasion, etc.)

        Returns:
            List of advantages the character has for this action
        """
        advantages = []
        class_name = self.profile.character_class.value

        # Class-based advantages
        if class_name == "Rogue" and action_type in [
            "Stealth",
            "Investigation",
            "Sleight of Hand",
        ]:
            advantages.append("Expertise doubles proficiency bonus")
        elif class_name == "Bard" and action_type in [
            "Persuasion",
            "Deception",
            "Performance",
        ]:
            advantages.append("Jack of All Trades adds bonus to non-proficient checks")
        elif class_name == "Ranger" and action_type in ["Perception", "Survival"]:
            advantages.append("Natural Explorer provides advantage in favored terrain")

        # Check background advantages from profile
        if (
            "noble" in self.profile.background_story.lower()
            and action_type == "Persuasion"
        ):
            advantages.append("Noble background aids in social situations")
        elif "criminal" in self.profile.background_story.lower() and action_type in [
            "Stealth",
            "Deception",
        ]:
            advantages.append("Criminal background provides relevant experience")

        return advantages
