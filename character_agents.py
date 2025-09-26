"""
Base Agent class and specific character agent implementations.
"""

import random
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from character_sheet import CharacterSheet
import json
from pathlib import Path


class Agent(ABC):
    """Base class for all AI agents in the D&D system."""
    
    def __init__(self, name: str):
        self.name = name
        self.memory: List[str] = []  # Store conversation/action history
        
    @abstractmethod
    def make_decision(self, situation: Dict[str, Any]) -> Dict[str, Any]:
        """Make a decision based on the current situation."""
        pass
    
    @abstractmethod
    def respond_to_action(self, action: Dict[str, Any]) -> str:
        """Respond to another agent's action."""
        pass
    
    def add_to_memory(self, event: str):
        """Add an event to the agent's memory."""
        self.memory.append(event)
        # Keep only last 50 events to prevent memory bloat
        if len(self.memory) > 50:
            self.memory = self.memory[-50:]


class CharacterAgent(Agent):
    def get_major_plot_actions(self) -> List[dict]:
        """Return the character's major plot actions."""
        return getattr(self.character, 'major_plot_actions', [])
    
    def get_relationships(self) -> Dict[str, str]:
        """Return the character's relationships with other characters and NPCs."""
        return getattr(self.character, 'relationships', {})
    
    def suggest_relationship_update(self, other_character: str, interaction_context: str) -> Optional[str]:
        """Suggest updating relationships based on story interactions."""
        current_relationships = self.get_relationships()
        
        # If no existing relationship, suggest creating one
        if other_character not in current_relationships:
            suggestions = {
                'positive_interaction': f"Appreciates {other_character}'s help in {interaction_context}",
                'conflict': f"Has tensions with {other_character} over {interaction_context}",
                'neutral': f"Working relationship with {other_character} after {interaction_context}",
                'suspicious': f"Remains cautious about {other_character} following {interaction_context}"
            }
            
            # Suggest based on character class tendencies
            class_name = self.character.dnd_class.lower()
            
            if class_name in ['paladin', 'cleric']:
                return f"SUGGESTION: Add relationship - '{other_character}': '{suggestions['positive_interaction']}'"
            elif class_name in ['rogue', 'warlock']:
                return f"SUGGESTION: Add relationship - '{other_character}': '{suggestions['suspicious']}'"
            else:
                return f"SUGGESTION: Add relationship - '{other_character}': '{suggestions['neutral']}'"
        
        # If existing relationship, suggest updating it
        else:
            current = current_relationships[other_character]
            return f"SUGGESTION: Update relationship with {other_character} - Current: '{current}' - Consider how {interaction_context} affects this"
    
    def suggest_plot_action_logging(self, action: str, reasoning: str, chapter: str) -> str:
        """Suggest adding an action to major_plot_actions."""
        return f"""SUGGESTION: Log this action to major_plot_actions:
{{
  "chapter": "{chapter}",
  "action": "{action}",
  "reasoning": "{reasoning}"
}}"""
    
    def suggest_character_development(self, new_behavior: str, context: str) -> List[str]:
        """Suggest character file updates based on new behaviors."""
        suggestions = []
        
        # Check if this behavior suggests new personality traits
        if any(word in new_behavior.lower() for word in ['brave', 'courageous', 'bold']):
            suggestions.append(f"SUGGESTION: Consider adding personality trait: 'Shows courage in {context}'")
        
        if any(word in new_behavior.lower() for word in ['cautious', 'careful', 'wary']):
            suggestions.append(f"SUGGESTION: Consider adding personality trait: 'Exercises caution when {context}'")
        
        if any(word in new_behavior.lower() for word in ['lead', 'command', 'direct']):
            suggestions.append(f"SUGGESTION: Consider adding personality trait: 'Takes leadership during {context}'")
        
        # Check if this suggests new fears or motivations
        if any(word in new_behavior.lower() for word in ['afraid', 'fear', 'terrified']):
            suggestions.append(f"SUGGESTION: Consider adding to fears_weaknesses: 'Fear related to {context}'")
        
        if any(word in new_behavior.lower() for word in ['protect', 'save', 'help']):
            suggestions.append(f"SUGGESTION: Consider updating motivations to include protecting others in {context}")
        
        return suggestions
    
    def analyze_story_content(self, story_text: str, chapter_name: str) -> Dict[str, List[str]]:
        """Analyze story content and provide comprehensive suggestions."""
        suggestions = {
            'relationships': [],
            'plot_actions': [],
            'character_development': [],
            'npc_creation': []
        }
        
        lines = story_text.split('\n')
        
        for line in lines:
            # Look for CHARACTER: ACTION: REASONING: patterns
            if line.strip().startswith('CHARACTER:') and self.name in line:
                # Extract action and reasoning from subsequent lines
                try:
                    action_line = next((l for l in lines[lines.index(line)+1:lines.index(line)+4] if l.strip().startswith('ACTION:')), '')
                    reasoning_line = next((l for l in lines[lines.index(line)+1:lines.index(line)+4] if l.strip().startswith('REASONING:')), '')
                    
                    if action_line and reasoning_line:
                        action = action_line.replace('ACTION:', '').strip()
                        reasoning = reasoning_line.replace('REASONING:', '').strip()
                        
                        # Suggest logging this action
                        suggestions['plot_actions'].append(
                            self.suggest_plot_action_logging(action, reasoning, chapter_name)
                        )
                        
                        # Suggest character development updates
                        suggestions['character_development'].extend(
                            self.suggest_character_development(action, chapter_name)
                        )
                except:
                    pass
            
            # Look for mentions of other characters or potential NPCs
            if self.name in line:
                # Find potential character interactions
                other_names = self._extract_character_names(line)
                for other_name in other_names:
                    if other_name != self.name:
                        relationship_suggestion = self.suggest_relationship_update(other_name, chapter_name)
                        if relationship_suggestion:
                            suggestions['relationships'].append(relationship_suggestion)
        
        return suggestions
    
    def _extract_character_names(self, text: str) -> List[str]:
        """Extract potential character/NPC names from text (simple implementation)."""
        # This is a basic implementation - could be enhanced with NLP
        words = text.split()
        potential_names = []
        
        for word in words:
            # Look for capitalized words that might be names
            if word.strip(',.:;!?').istitle() and len(word) > 2:
                potential_names.append(word.strip(',.:;!?'))
        
        return potential_names
    
    """AI agent that controls a D&D character."""
    
    def __init__(self, character_sheet: CharacterSheet):
        super().__init__(character_sheet.name)
        self.character = character_sheet
        self.action_tendencies = self._determine_action_tendencies()
        
    def _determine_action_tendencies(self) -> Dict[str, float]:
        """Determine character's tendencies based on class and personality."""
        base_tendencies = {
            'combat': 0.5,
            'social': 0.3,
            'exploration': 0.4,
            'problem_solving': 0.3,
            'helping_others': 0.6,
            'taking_risks': 0.4,
            'using_magic': 0.2,
            'stealth': 0.2
        }
        
        # Modify tendencies based on class
        class_modifiers = {
            'Fighter': {'combat': 0.8, 'taking_risks': 0.7, 'helping_others': 0.8},
            'Wizard': {'using_magic': 0.9, 'problem_solving': 0.8, 'social': 0.4},
            'Rogue': {'stealth': 0.9, 'exploration': 0.8, 'taking_risks': 0.6},
            'Cleric': {'helping_others': 0.9, 'using_magic': 0.7, 'social': 0.7}
        }
        
        if self.character.dnd_class in class_modifiers:
            for action, modifier in class_modifiers[self.character.dnd_class].items():
                base_tendencies[action] = modifier
                
        return base_tendencies
    
    def make_decision(self, situation: Dict[str, Any]) -> Dict[str, Any]:
        """Make a decision based on character's personality and current situation."""
        situation_type = situation.get('type', 'general')
        available_actions = situation.get('actions', [])
        
        if situation_type == 'combat':
            return self._make_combat_decision(situation)
        elif situation_type == 'social':
            return self._make_social_decision(situation)
        elif situation_type == 'exploration':
            return self._make_exploration_decision(situation)
        else:
            return self._make_general_decision(situation)
    
    def _make_combat_decision(self, situation: Dict[str, Any]) -> Dict[str, Any]:
        """Make combat-related decisions."""
        enemies = situation.get('enemies', [])
        allies_in_danger = situation.get('allies_in_danger', [])
        
        # Prioritize healing if cleric and allies are hurt
        if (self.character.dnd_class == 'Cleric' and 
            allies_in_danger and 
            self.character.can_cast_spell(1)):
            target = random.choice(allies_in_danger)
            return {
                'action': 'cast_spell',
                'spell': 'Cure Wounds',
                'target': target,
                'reasoning': f"{self.name} prioritizes healing {target}."
            }
        
        # Use magic if wizard
        if (self.character.dnd_class == 'Wizard' and 
            enemies and 
            self.character.can_cast_spell(1)):
            target = random.choice(enemies)
            return {
                'action': 'cast_spell',
                'spell': 'Magic Missile',
                'target': target,
                'reasoning': f"{self.name} casts Magic Missile at {target}."
            }
        
        # Sneak attack if rogue
        if (self.character.dnd_class == 'Rogue' and enemies):
            target = random.choice(enemies)
            return {
                'action': 'sneak_attack',
                'target': target,
                'reasoning': f"{self.name} attempts a sneak attack on {target}."
            }
        
        # Default melee attack
        if enemies:
            target = random.choice(enemies)
            weapon = self.character.equipment.weapons[0] if self.character.equipment.weapons else "fists"
            return {
                'action': 'attack',
                'weapon': weapon,
                'target': target,
                'reasoning': f"{self.name} attacks {target} with {weapon}."
            }
        
        return {
            'action': 'defend',
            'reasoning': f"{self.name} takes a defensive stance."
        }
    
    def _make_social_decision(self, situation: Dict[str, Any]) -> Dict[str, Any]:
        """Make social interaction decisions."""
        npc = situation.get('npc', 'stranger')
        conversation_topic = situation.get('topic', 'general')
        
        # Base response on charisma and personality
        charisma_mod = self.character.get_ability_modifier('charisma')
        
        if charisma_mod >= 2:  # High charisma characters are more persuasive
            approach = random.choice(['persuade', 'charm'])
        elif charisma_mod <= -2:  # Low charisma characters might intimidate
            approach = random.choice(['intimidate', 'direct'])
        else:
            approach = random.choice(['friendly', 'cautious'])
        
        responses = {
            'persuade': f"{self.name} tries to persuade {npc} with logical arguments.",
            'charm': f"{self.name} uses charm and wit to win over {npc}.",
            'intimidate': f"{self.name} attempts to intimidate {npc}.",
            'direct': f"{self.name} speaks directly and honestly to {npc}.",
            'friendly': f"{self.name} approaches {npc} in a friendly manner.",
            'cautious': f"{self.name} speaks cautiously to {npc}."
        }
        
        return {
            'action': 'social_interaction',
            'approach': approach,
            'target': npc,
            'reasoning': responses[approach]
        }
    
    def _make_exploration_decision(self, situation: Dict[str, Any]) -> Dict[str, Any]:
        """Make exploration-related decisions."""
        options = situation.get('paths', ['forward'])
        dangers = situation.get('dangers', [])
        
        # Rogues prefer stealthy approaches
        if self.character.dnd_class == 'Rogue':
            if 'sneak' in [opt.lower() for opt in options]:
                return {
                    'action': 'move_stealthily',
                    'direction': 'sneak',
                    'reasoning': f"{self.name} chooses to move stealthily."
                }
        
        # Wizards might use magic to scout
        if (self.character.dnd_class == 'Wizard' and 
            'Detect Magic' in self.character.known_spells):
            return {
                'action': 'cast_spell',
                'spell': 'Detect Magic',
                'reasoning': f"{self.name} casts Detect Magic to scout ahead."
            }
        
        # Default exploration
        chosen_path = random.choice(options)
        return {
            'action': 'explore',
            'direction': chosen_path,
            'reasoning': f"{self.name} decides to go {chosen_path}."
        }
    
    def _make_general_decision(self, situation: Dict[str, Any]) -> Dict[str, Any]:
        """Make general decisions when situation type is unclear."""
        context = situation.get('context', '')
        
        # Check if character needs rest
        # If you want to check for injury, use max_hit_points only or remove this logic.
        
        # Default to asking for more information
        return {
            'action': 'gather_information',
            'reasoning': f"{self.name} wants to understand the situation better before acting."
        }
    
    def respond_to_action(self, action: Dict[str, Any]) -> str:
        """Respond to another character's action based on personality."""
        actor = action.get('actor', 'someone')
        action_type = action.get('action', 'unknown')
        
        # Personality-based responses
        if 'helpful' in [trait.lower() for trait in self.character.personality_traits]:
            if action_type in ['attack', 'help']:
                return f"{self.name}: 'Well done, {actor}! I'll support you.'"
            elif action_type == 'rest':
                return f"{self.name}: 'Good idea, {actor}. We should all recover our strength.'"
        
        if 'cautious' in [trait.lower() for trait in self.character.personality_traits]:
            if action_type == 'attack':
                return f"{self.name}: '{actor}, be careful! Make sure you're not walking into a trap.'"
            elif action_type == 'explore':
                return f"{self.name}: 'Let me check for dangers first, {actor}.'"
        
        # Default neutral response
        return f"{self.name}: 'I see what you're doing, {actor}.'"
    
    def get_status(self) -> dict:
        """Get current character status including new fields."""
        return {
            'name': self.name,
            'class': self.character.dnd_class,
            'subclass': getattr(self.character, 'subclass', None),
            'species': getattr(self.character, 'species', None),
            'lineage': getattr(self.character, 'lineage', None),
            'level': self.character.level,
            'ac': self.character.armor_class,
            'movement_speed': getattr(self.character, 'movement_speed', 30),
            'spell_slots': self.character.spell_slots,
            'equipment': getattr(self.character, 'equipment', {}),
            'feats': getattr(self.character, 'feats', []),
            'magic_items': getattr(self.character, 'magic_items', []),
            'class_abilities': getattr(self.character, 'class_abilities', []),
            'specialized_abilities': getattr(self.character, 'specialized_abilities', []),
            'background': getattr(self.character, 'background', ''),
            'personality_traits': getattr(self.character, 'personality_traits', []),
            'ideals': getattr(self.character, 'ideals', []),
            'bonds': getattr(self.character, 'bonds', []),
            'flaws': getattr(self.character, 'flaws', []),
            'backstory': getattr(self.character, 'backstory', '')
        }


# Predefined character agents - deprecated, use create_party_from_json instead

def load_character_from_json(json_path: Path) -> CharacterSheet:
    """Load a character from a JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Convert JSON to CharacterSheet (manual mapping for nested objects)
    ability_scores = data.get('ability_scores', {})
    skills = data.get('skills', {})
    equipment = data.get('equipment', {})
    spell_slots = data.get('spell_slots', {})
    known_spells = data.get('known_spells', [])
    return CharacterSheet(
        name=data.get('name', ''),
        species=data.get('species', 'Human'),
        lineage=data.get('lineage'),
        dnd_class=data.get('dnd_class', 'Fighter'),
        subclass=data.get('subclass'),
        level=data.get('level', 1),
        ability_scores=ability_scores,
        skills=skills,
        max_hit_points=data.get('max_hit_points', 8),
        armor_class=data.get('armor_class', 10),
        movement_speed=data.get('movement_speed', 30),
        proficiency_bonus=data.get('proficiency_bonus', 2),
        equipment=equipment,
        spell_slots=spell_slots,
        known_spells=known_spells,
        background=data.get('background', ''),
        personality_traits=data.get('personality_traits', []),
        ideals=data.get('ideals', []),
        bonds=data.get('bonds', []),
        flaws=data.get('flaws', []),
        backstory=data.get('backstory', ''),
        feats=data.get('feats', []),
        magic_items=data.get('magic_items', []),
        class_abilities=data.get('class_abilities', []),
        specialized_abilities=data.get('specialized_abilities', []),
        major_plot_actions=data.get('major_plot_actions', []),
        relationships=data.get('relationships', {})
    )


def create_party_from_json(characters_dir: Path) -> list:
    """Create agents for all character JSON files in the directory."""
    party = []
    for char_file in characters_dir.glob('*.json'):
        sheet = load_character_from_json(char_file)
        party.append(CharacterAgent(sheet))
    return party