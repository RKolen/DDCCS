"""
Character Consistency Checking Component.

Handles validation of combat actions against character profiles to ensure
consistency with established personalities and behaviors.
"""

from typing import Dict, List
from src.characters.consultants.consultant_core import CharacterConsultant

class ConsistencyChecker:
    """Checks combat narrative consistency with character profiles."""

    def __init__(self, character_consultants: Dict[str, CharacterConsultant]):
        self.consultants = character_consultants

    def check_action_consistency(self, character: str, action: str) -> str:
        """
        Check if a single action is consistent with character profile.

        Args:
            character: Character name
            action: Action description

        Returns:
            Consistency note or empty string
        """
        if character not in self.consultants:
            return ""

        consultant = self.consultants[character]

        # Analyze if combat action fits character
        if any(
            combat_word in action.lower()
            for combat_word in ["attack", "cast", "heal", "defend"]
        ):
            reaction = consultant.suggest_reaction(f"combat situation: {action}")

            # Check if action aligns with character nature
            if "class_reaction" in reaction:
                return f"**{character}:** {reaction['class_reaction']}"

        return ""

    def enhance_with_character_consistency(
        self, narrative: str, character_actions: Dict[str, List[str]]
    ) -> str:
        """Enhance narrative with character consistency notes."""
        enhanced = narrative

        consistency_notes = []

        for character, actions in character_actions.items():
            for action in actions:
                note = self.check_action_consistency(character, action)
                if note:
                    consistency_notes.append(note)

        if consistency_notes:
            enhanced += "\\n\\n**Character Consistency Notes:**\\n"
            enhanced += "\\n".join(consistency_notes)

        return enhanced
