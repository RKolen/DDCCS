"""
Combat Action Description Component.

Handles narrative descriptions for combat actions including attacks, spells,
healing, damage, and status effects with character-aware styling.
"""

from typing import Dict, Any, Optional
from src.characters.consultants.consultant_core import CharacterConsultant


class CombatDescriptor:
    """Provides narrative descriptions for combat actions."""

    def __init__(self, character_consultants: Dict[str, CharacterConsultant]):
        self.consultants = character_consultants

        # Damage descriptions
        self.damage_descriptions = {
            (1, 3): "a light wound",
            (4, 8): "a solid hit",
            (9, 15): "a heavy blow",
            (16, 25): "a devastating strike",
            (26, 999): "a massive crushing blow",
        }

        # Status effect descriptions
        self.status_effects = {
            "prone": "knocked to the ground",
            "stunned": "left reeling and stunned",
            "poisoned": "affected by poison",
            "charmed": "falls under a magical influence",
            "frightened": "becomes filled with fear",
            "paralyzed": "becomes unable to move",
            "unconscious": "falls unconscious",
        }

    def describe_action(
        self,
        action: Dict[str, Any],
        consultant: Optional[CharacterConsultant],
        style: str,
    ) -> str:
        """Describe a single action in narrative form."""
        action_type = action["type"]

        if action_type == "attack":
            return self._describe_attack(action, consultant, style)
        if action_type == "spell":
            return self._describe_spell(action, consultant, style)
        if action_type == "damage":
            return self._describe_damage(action, style)
        if action_type == "healing":
            return self._describe_healing(action, consultant, style)
        if action_type == "status":
            return self._describe_status_effect(action, style)

        return f"performs an action ({action_type})"

    def _describe_attack(
        self,
        action: Dict[str, Any],
        consultant: Optional[CharacterConsultant],
        _style: str,
    ) -> str:
        """Describe an attack action."""
        target = action["target"]
        roll = action.get("roll", 0)
        damage = action.get("damage", 0)

        # Determine weapon (simplified - could be enhanced)
        weapon = "weapon"
        if consultant:
            class_name = consultant.profile.character_class.value
            if class_name in ["Wizard", "Sorcerer", "Warlock"]:
                weapon = "spell focus"
            elif class_name in ["Ranger", "Fighter"]:
                weapon = "sword"
            elif class_name == "Rogue":
                weapon = "dagger"
            elif class_name == "Monk":
                weapon = "fists"

        # Build attack description
        attack_desc = f"strikes at {target} with their {weapon}"

        if damage > 0:
            # Hit
            damage_desc = self.get_damage_description(damage)
            if roll >= 20:
                return (
                    f"{attack_desc} with devastating precision, "
                    f"dealing {damage_desc}!"
                )
            return f"{attack_desc}, dealing {damage_desc}."
        # Miss
        if roll <= 5:
            return f"{attack_desc} but misses completely."
        return f"{attack_desc} but {target} manages to avoid the blow."

    def _describe_spell(
        self,
        action: Dict[str, Any],
        consultant: Optional[CharacterConsultant],
        _style: str,
    ) -> str:
        """Describe a spell casting action."""
        spell = action["spell"]
        damage = action.get("damage", 0)
        healing = action.get("healing", 0)

        # Get class-appropriate casting description
        casting_style = "weaves magical energy"
        if consultant:
            class_name = consultant.profile.character_class.value
            if class_name == "Cleric":
                casting_style = "channels divine power"
            elif class_name == "Druid":
                casting_style = "calls upon nature's magic"
            elif class_name == "Warlock":
                casting_style = "invokes eldritch power"
            elif class_name == "Sorcerer":
                casting_style = "unleashes innate magic"

        base_desc = f"{casting_style} and casts {spell}"

        if damage > 0:
            damage_desc = self.get_damage_description(damage)
            return f"{base_desc}, causing {damage_desc}!"
        if healing > 0:
            return f"{base_desc}, restoring {healing} hit points."
        return f"{base_desc}."

    def _describe_healing(
        self,
        action: Dict[str, Any],
        _consultant: Optional[CharacterConsultant],
        _style: str,
    ) -> str:
        """Describe a healing action."""
        amount = action.get("amount", 0)

        return f"receives healing energy, recovering {amount} hit points"

    def _describe_damage(self, action: Dict[str, Any], _style: str) -> str:
        """Describe taking damage."""
        amount = action.get("amount", 0)

        damage_desc = self.get_damage_description(amount)
        return f"suffers {damage_desc}"

    def _describe_status_effect(self, action: Dict[str, Any], _style: str) -> str:
        """Describe a status effect."""
        effect = action.get("effect", "affected")

        effect_desc = self.status_effects.get(effect.lower(), f"becomes {effect}")
        return f"is {effect_desc}"

    def get_damage_description(self, damage: int) -> str:
        """Get appropriate damage description based on amount."""
        for (min_dmg, max_dmg), description in self.damage_descriptions.items():
            if min_dmg <= damage <= max_dmg:
                return f"{description} ({damage} damage)"

        return f"damage ({damage} points)"
