"""
Combat to Story Converter - Transforms FGU combat results into narrative text.
"""

import re
from typing import Dict, List, Any, Optional
from character_consultants import CharacterConsultant


class CombatNarrator:
    """Converts FGU combat summaries into narrative story format."""
    
    def __init__(self, character_consultants: Dict[str, CharacterConsultant]):
        self.consultants = character_consultants
        
        # Combat action descriptions for narrative
        self.action_templates = {
            'attack': [
                "{attacker} swings their {weapon} at {target}",
                "{attacker} strikes {target} with their {weapon}",
                "{attacker} launches an attack against {target}",
                "{attacker} attempts to hit {target} with their {weapon}"
            ],
            'hit': [
                "and connects solidly",
                "finding their mark",
                "striking true",
                "landing a solid blow"
            ],
            'miss': [
                "but the attack goes wide",
                "but {target} dodges at the last moment",
                "but misses their target",
                "but the strike fails to connect"
            ],
            'critical': [
                "with devastating precision",
                "finding a critical weakness",
                "with exceptional skill",
                "exploiting a perfect opening"
            ],
            'spell_cast': [
                "{caster} weaves magical energy and casts {spell}",
                "{caster} channels arcane power to cast {spell}",
                "{caster} invokes {spell} with mystical words",
                "Magical energy crackles as {caster} casts {spell}"
            ],
            'healing': [
                "{healer} channels healing energy into {target}",
                "{healer} tends to {target}'s wounds",
                "Divine light flows from {healer} to {target}",
                "{healer} whispers a healing prayer over {target}"
            ]
        }
        
        # Damage descriptions
        self.damage_descriptions = {
            (1, 3): "a light wound",
            (4, 8): "a solid hit", 
            (9, 15): "a heavy blow",
            (16, 25): "a devastating strike",
            (26, 999): "a massive crushing blow"
        }
        
        # Status effect descriptions
        self.status_effects = {
            'prone': "knocked to the ground",
            'stunned': "left reeling and stunned",
            'poisoned': "affected by poison",
            'charmed': "falls under a magical influence",
            'frightened': "becomes filled with fear",
            'paralyzed': "becomes unable to move",
            'unconscious': "falls unconscious"
        }
    
    def parse_fgu_summary(self, fgu_text: str) -> Dict[str, Any]:
        """Parse FGU combat summary into structured data."""
        combat_data = {
            'rounds': [],
            'participants': set(),
            'final_state': {}
        }
        
        # Split into rounds (this is a simplified parser - adjust based on actual FGU format)
        rounds_text = fgu_text.split('Round ')
        
        for i, round_text in enumerate(rounds_text[1:], 1):  # Skip the first empty split
            round_data = self._parse_round(round_text, i)
            combat_data['rounds'].append(round_data)
            combat_data['participants'].update(round_data['participants'])
        
        return combat_data
    
    def _parse_round(self, round_text: str, round_number: int) -> Dict[str, Any]:
        """Parse a single round of combat."""
        round_data = {
            'round_number': round_number,
            'actions': [],
            'participants': set()
        }
        
        # Look for common FGU patterns (adjust these based on actual FGU output)
        patterns = {
            'attack': r'(\\w+)\\s+attacks\\s+(\\w+)\\s+.*?rolls?\\s+(\\d+).*?(?:hits?|misses?).*?(?:for\\s+(\\d+)\\s+damage)?',
            'spell': r'(\\w+)\\s+casts\\s+(\\w+)\\s+.*?(?:for\\s+(\\d+)\\s+damage|healing\\s+(\\d+))?',
            'damage': r'(\\w+)\\s+takes\\s+(\\d+)\\s+damage',
            'healing': r'(\\w+)\\s+(?:heals?|recovers?)\\s+(\\d+)\\s+(?:hit\\s+points?|hp)',
            'status': r'(\\w+)\\s+is\\s+(\\w+)'
        }
        
        for action_type, pattern in patterns.items():
            matches = re.findall(pattern, round_text, re.IGNORECASE)
            for match in matches:
                action_data = self._create_action_data(action_type, match)
                round_data['actions'].append(action_data)
                round_data['participants'].update([name for name in match if isinstance(name, str) and name.isalpha()])
        
        return round_data
    
    def _create_action_data(self, action_type: str, match_data: tuple) -> Dict[str, Any]:
        """Create structured action data from regex match."""
        action = {'type': action_type}
        
        if action_type == 'attack':
            action.update({
                'attacker': match_data[0],
                'target': match_data[1],
                'roll': int(match_data[2]) if match_data[2] else 0,
                'damage': int(match_data[3]) if len(match_data) > 3 and match_data[3] else 0
            })
        elif action_type == 'spell':
            action.update({
                'caster': match_data[0],
                'spell': match_data[1],
                'damage': int(match_data[2]) if len(match_data) > 2 and match_data[2] else 0,
                'healing': int(match_data[3]) if len(match_data) > 3 and match_data[3] else 0
            })
        elif action_type == 'damage':
            action.update({
                'target': match_data[0],
                'amount': int(match_data[1])
            })
        elif action_type == 'healing':
            action.update({
                'target': match_data[0],
                'amount': int(match_data[1])
            })
        elif action_type == 'status':
            action.update({
                'target': match_data[0],
                'effect': match_data[1]
            })
        
        return action
    
    def convert_to_narrative(self, fgu_text: str, style: str = 'detailed') -> str:
        """Convert FGU combat summary to narrative story format."""
        combat_data = self.parse_fgu_summary(fgu_text)
        
        if not combat_data['rounds']:
            return "The combat summary could not be parsed. Please check the FGU format."
        
        narrative_parts = []
        narrative_parts.append("## Combat Narrative\\n")
        
        for round_data in combat_data['rounds']:
            round_narrative = self._create_round_narrative(round_data, style)
            narrative_parts.append(round_narrative)
        
        # Add combat conclusion
        conclusion = self._create_combat_conclusion(combat_data)
        if conclusion:
            narrative_parts.append(conclusion)
        
        return "\\n\\n".join(narrative_parts)
    
    def _create_round_narrative(self, round_data: Dict[str, Any], style: str) -> str:
        """Create narrative text for a single round."""
        round_num = round_data['round_number']
        actions = round_data['actions']
        
        if not actions:
            return f"**Round {round_num}:** The combatants circle each other, looking for openings."
        
        narrative = f"**Round {round_num}:**\\n"
        
        # Group actions by character for better flow
        character_actions = {}
        for action in actions:
            actor = self._get_action_actor(action)
            if actor not in character_actions:
                character_actions[actor] = []
            character_actions[actor].append(action)
        
        # Create narrative for each character's actions
        for character, char_actions in character_actions.items():
            char_narrative = self._create_character_action_narrative(character, char_actions, style)
            narrative += f"\\n{char_narrative}"
        
        return narrative
    
    def _get_action_actor(self, action: Dict[str, Any]) -> str:
        """Get the main actor for an action."""
        if 'attacker' in action:
            return action['attacker']
        elif 'caster' in action:
            return action['caster']
        elif 'target' in action:
            return action['target']
        else:
            return 'Unknown'
    
    def _create_character_action_narrative(self, character: str, actions: List[Dict[str, Any]], style: str) -> str:
        """Create narrative for a character's actions in a round."""
        if not actions:
            return ""
        
        # Get character consultant for personality-appropriate descriptions
        consultant = self.consultants.get(character)
        
        narrative_parts = []
        
        for action in actions:
            action_narrative = self._describe_action(action, consultant, style)
            if action_narrative:
                narrative_parts.append(action_narrative)
        
        if narrative_parts:
            return f"**{character}:** " + " ".join(narrative_parts)
        else:
            return ""
    
    def _describe_action(self, action: Dict[str, Any], consultant: Optional[CharacterConsultant], style: str) -> str:
        """Describe a single action in narrative form."""
        action_type = action['type']
        
        if action_type == 'attack':
            return self._describe_attack(action, consultant, style)
        elif action_type == 'spell':
            return self._describe_spell(action, consultant, style)
        elif action_type == 'damage':
            return self._describe_damage(action, style)
        elif action_type == 'healing':
            return self._describe_healing(action, consultant, style)
        elif action_type == 'status':
            return self._describe_status_effect(action, style)
        
        return f"performs an action ({action_type})"
    
    def _describe_attack(self, action: Dict[str, Any], consultant: Optional[CharacterConsultant], style: str) -> str:
        """Describe an attack action."""
        attacker = action['attacker']
        target = action['target']
        roll = action.get('roll', 0)
        damage = action.get('damage', 0)
        
        # Determine weapon (simplified - could be enhanced)
        weapon = "weapon"
        if consultant:
            class_name = consultant.profile.character_class.value
            if class_name in ['Wizard', 'Sorcerer', 'Warlock']:
                weapon = "spell focus"
            elif class_name in ['Ranger', 'Fighter']:
                weapon = "sword"
            elif class_name == 'Rogue':
                weapon = "dagger"
            elif class_name == 'Monk':
                weapon = "fists"
        
        # Build attack description
        attack_desc = f"strikes at {target} with their {weapon}"
        
        if damage > 0:
            # Hit
            damage_desc = self._get_damage_description(damage)
            if roll >= 20:
                return f"{attack_desc} with devastating precision, dealing {damage_desc}!"
            else:
                return f"{attack_desc}, dealing {damage_desc}."
        else:
            # Miss
            if roll <= 5:
                return f"{attack_desc} but misses completely."
            else:
                return f"{attack_desc} but {target} manages to avoid the blow."
    
    def _describe_spell(self, action: Dict[str, Any], consultant: Optional[CharacterConsultant], style: str) -> str:
        """Describe a spell casting action."""
        caster = action['caster']
        spell = action['spell']
        damage = action.get('damage', 0)
        healing = action.get('healing', 0)
        
        # Get class-appropriate casting description
        casting_style = "weaves magical energy"
        if consultant:
            class_name = consultant.profile.character_class.value
            if class_name == 'Cleric':
                casting_style = "channels divine power"
            elif class_name == 'Druid':
                casting_style = "calls upon nature's magic"
            elif class_name == 'Warlock':
                casting_style = "invokes eldritch power"
            elif class_name == 'Sorcerer':
                casting_style = "unleashes innate magic"
        
        base_desc = f"{casting_style} and casts {spell}"
        
        if damage > 0:
            damage_desc = self._get_damage_description(damage)
            return f"{base_desc}, causing {damage_desc}!"
        elif healing > 0:
            return f"{base_desc}, restoring {healing} hit points."
        else:
            return f"{base_desc}."
    
    def _describe_healing(self, action: Dict[str, Any], consultant: Optional[CharacterConsultant], style: str) -> str:
        """Describe a healing action."""
        target = action['target']
        amount = action.get('amount', 0)
        
        return f"receives healing energy, recovering {amount} hit points"
    
    def _describe_damage(self, action: Dict[str, Any], style: str) -> str:
        """Describe taking damage."""
        target = action['target']
        amount = action.get('amount', 0)
        
        damage_desc = self._get_damage_description(amount)
        return f"suffers {damage_desc}"
    
    def _describe_status_effect(self, action: Dict[str, Any], style: str) -> str:
        """Describe a status effect."""
        target = action['target']
        effect = action.get('effect', 'affected')
        
        effect_desc = self.status_effects.get(effect.lower(), f"becomes {effect}")
        return f"is {effect_desc}"
    
    def _get_damage_description(self, damage: int) -> str:
        """Get appropriate damage description based on amount."""
        for (min_dmg, max_dmg), description in self.damage_descriptions.items():
            if min_dmg <= damage <= max_dmg:
                return f"{description} ({damage} damage)"
        
        return f"damage ({damage} points)"
    
    def _create_combat_conclusion(self, combat_data: Dict[str, Any]) -> str:
        """Create a conclusion for the combat."""
        if not combat_data['rounds']:
            return ""
        
        round_count = len(combat_data['rounds'])
        participants = list(combat_data['participants'])
        
        conclusion = f"\\n**Combat Conclusion:**\\n"
        conclusion += f"The battle lasted {round_count} round{'s' if round_count != 1 else ''}, "
        conclusion += f"with {len(participants)} combatants involved. "
        
        # Could add more sophisticated analysis of winners/losers
        conclusion += "The immediate threat has been resolved."
        
        return conclusion
    
    def enhance_with_character_consistency(self, narrative: str, character_actions: Dict[str, List[str]]) -> str:
        """Enhance narrative with character consistency notes."""
        enhanced = narrative
        
        consistency_notes = []
        
        for character, actions in character_actions.items():
            if character in self.consultants:
                consultant = self.consultants[character]
                
                # Analyze if combat actions fit character
                for action in actions:
                    if any(combat_word in action.lower() for combat_word in ['attack', 'cast', 'heal', 'defend']):
                        reaction = consultant.suggest_reaction(f"combat situation: {action}")
                        
                        # Check if action aligns with character nature
                        if 'class_reaction' in reaction:
                            consistency_notes.append(f"**{character}:** {reaction['class_reaction']}")
        
        if consistency_notes:
            enhanced += "\\n\\n**Character Consistency Notes:**\\n"
            enhanced += "\\n".join(consistency_notes)
        
        return enhanced