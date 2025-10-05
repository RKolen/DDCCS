"""
Combat to Story Converter - Transforms combat descriptions into narrative text.

Supports two modes:
1. Natural language combat prompts (RECOMMENDED) - Takes tactical descriptions and converts to narrative
2. FGU combat logs (Legacy) - Parses Fantasy Grounds Unity combat summaries

Features:
- RAG integration for D&D spell/ability lookup (dnd5e.wikidot.com)
- Automatic spell description enrichment
- Character-aware combat narration
"""

import re
from typing import Dict, List, Any, Optional
from character_consultants import CharacterConsultant

# Import AI client if available
try:
    from ai_client import AIClient
    AI_AVAILABLE = True
except ImportError:
    AIClient = None
    AI_AVAILABLE = False

# Import RAG system for D&D rules lookup
try:
    from rag_system import RAGSystem
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


class CombatNarrator:
    """Converts combat descriptions into narrative story format."""
    
    def __init__(self, character_consultants: Dict[str, CharacterConsultant], ai_client=None):
        self.consultants = character_consultants
        self.ai_client = ai_client
        
        # Initialize D&D rules RAG system
        self.dnd_rag = None
        if RAG_AVAILABLE:
            try:
                import os
                # Use separate RAG_RULES_BASE_URL for D&D rules lookups
                # This allows campaign wiki (RAG_WIKI_BASE_URL) and rules wiki to be different
                rules_url = os.environ.get('RAG_RULES_BASE_URL', 'https://dnd5e.wikidot.com')
                
                # Temporarily override env for rules lookup
                orig_url = os.environ.get('RAG_WIKI_BASE_URL', '')
                orig_enabled = os.environ.get('RAG_ENABLED', '')
                
                os.environ['RAG_WIKI_BASE_URL'] = rules_url
                os.environ['RAG_ENABLED'] = 'true'
                
                self.dnd_rag = RAGSystem()
                
                # Restore original settings
                if orig_url:
                    os.environ['RAG_WIKI_BASE_URL'] = orig_url
                else:
                    os.environ.pop('RAG_WIKI_BASE_URL', None)
                    
                if orig_enabled:
                    os.environ['RAG_ENABLED'] = orig_enabled
                else:
                    os.environ.pop('RAG_ENABLED', None)
                    
            except Exception as e:
                print(f"WARNING: Could not initialize D&D rules RAG: {e}")
    
    def narrate_combat_from_prompt(
        self,
        combat_prompt: str,
        story_context: str = "",
        style: str = "cinematic"
    ) -> str:
        """
        Convert a natural language combat prompt into narrative prose.
        
        Args:
            combat_prompt: Tactical description of combat (e.g., "Theron charges the enemy line...")
            story_context: Optional story so far for context
            style: Narrative style (cinematic, gritty, heroic, tactical)
            
        Returns:
            Narrative prose describing the combat scene
        """
        if not self.ai_client or not AI_AVAILABLE:
            return self._narrate_combat_fallback(combat_prompt, style)
        
        # Build character context
        character_context = self._build_character_context(combat_prompt)
        
        # Look up D&D spells/abilities for accurate descriptions
        ability_context = self._lookup_spells_and_abilities(combat_prompt)
        
        # Create AI prompt
        system_prompt = f"""You are an expert D&D combat narrator. Convert tactical combat descriptions into engaging narrative prose.

CRITICAL RULES:
1. NEVER mention dice rolls, DCs, or game mechanics (no "rolls", "saves", "AC", numbers)
2. EVERY action MUST be included - do not omit or summarize any action
3. Critical hits should be described with exceptional detail and dramatic flair
4. Maintain character personalities and fighting styles
5. Write in {style} style with vivid sensory details
6. Use present tense for immediacy
7. Keep tactical order but make it flow naturally
8. For spells with verbal components, create fitting dialogue/incantations based on the spell's actual effect
9. Use the D&D rules context to make spell effects accurate and flavorful

Style Guidelines:
- Cinematic: Movie-like action, dramatic descriptions, epic moments
- Gritty: Realistic, visceral, emphasize the danger and pain
- Heroic: Emphasize bravery, valor, and heroic deeds
- Tactical: Clear action-by-action while maintaining narrative flow"""

        user_prompt = f"""Convert this tactical combat description into narrative prose:

{combat_prompt}

{character_context}
{ability_context}
{f'Story context (for continuity):\n{story_context[:500]}...' if story_context else ''}

Write the combat narrative in {style} style. Remember:
- NO dice rolls or game mechanics
- Include EVERY action mentioned
- Make critical hits dramatically impressive
- Create dialogue for spell incantations that fits the spell's actual effect
- Use the D&D rules context to enhance accuracy
- Make it flow like a story, not a combat log"""

        try:
            narrative = self.ai_client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8  # Higher temperature for creative combat descriptions
            )
            
            # Post-process to ensure no mechanics leaked through
            narrative = self._remove_mechanics_terms(narrative)
            
            # Wrap text to 80 characters for readability
            narrative = self._wrap_narrative_text(narrative)
            
            return narrative
            
        except Exception as e:
            print(f"⚠️  AI narration failed: {e}")
            return self._narrate_combat_fallback(combat_prompt, style)
    
    def _build_character_context(self, combat_prompt: str) -> str:
        """Build context about characters mentioned in the combat."""
        context_parts = []
        
        # Find character names in the prompt (capitalized words at sentence start or after commas)
        potential_names = re.findall(r'(?:^|[.!?]\s+|,\s+)([A-Z][a-z]+)', combat_prompt)
        
        for name in set(potential_names):
            if name in self.consultants:
                consultant = self.consultants[name]
                profile = consultant.profile
                
                char_info = f"\n**{name}** ({profile.character_class.value}):"
                char_info += f"\n- Fighting Style: {self._get_fighting_style(profile)}"
                char_info += f"\n- Personality: {profile.personality_summary[:100] if profile.personality_summary else 'Brave adventurer'}"
                
                context_parts.append(char_info)
        
        if context_parts:
            return "\nCharacter Information (for authentic portrayal):" + "".join(context_parts)
        else:
            return ""
    
    def _lookup_spells_and_abilities(self, combat_prompt: str) -> str:
        """
        Look up D&D spells and abilities mentioned in combat.
        Uses dnd5e.wikidot.com via RAG system.
        """
        if not self.dnd_rag:
            return ""
        
        # Common D&D spell/ability patterns to look for
        spell_patterns = [
            r'\b(vicious mockery)\b',
            r'\b(eldritch blast)\b',
            r'\b(fireball)\b',
            r'\b(healing word)\b',
            r'\b(cure wounds)\b',
            r'\b(sacred flame)\b',
            r'\b(thunderwave)\b',
            r'\b(magic missile)\b',
            r'\b(shield)\b',
            r'\b(mage armor)\b',
            r'\b(wild shape)\b',
            r'\b(sneak attack)\b',
            r'\b(divine smite)\b',
            r'\b(lay on hands)\b',
            r'\b(bardic inspiration)\b',
            r'\b(rage)\b',
            r'\b(action surge)\b',
            r'\b(second wind)\b',
        ]
        
        found_abilities = []
        for pattern in spell_patterns:
            matches = re.finditer(pattern, combat_prompt, re.IGNORECASE)
            for match in matches:
                ability_name = match.group(1)
                found_abilities.append(ability_name)
        
        if not found_abilities:
            return ""
        
        # Look up each ability
        ability_descriptions = []
        for ability in set(found_abilities):
            try:
                # Format for wikidot URL
                page_name = ability.lower().replace(' ', '-')
                
                # Try different page formats
                possible_pages = [
                    f"spell:{page_name}",
                    f"feat:{page_name}",
                    f"class:{page_name}",
                ]
                
                for page in possible_pages:
                    result = self.dnd_rag.search_wiki(ability, max_results=1)
                    if result:
                        ability_descriptions.append(f"\n**{ability.title()}**: {result[0]['content'][:300]}...")
                        break
            except Exception as e:
                # Silently skip failed lookups
                pass
        
        if ability_descriptions:
            return "\n\nD&D Rules Context (for accurate portrayal):" + "".join(ability_descriptions)
        else:
            return ""
    
    def _get_fighting_style(self, profile) -> str:
        """Determine character's fighting style from their class."""
        class_name = profile.character_class.value
        
        fighting_styles = {
            'Barbarian': 'Reckless and powerful melee combat',
            'Bard': 'Support magic and witty verbal jabs',
            'Cleric': 'Divine magic and healing with martial backup',
            'Druid': 'Wild Shape transformations and nature magic',
            'Fighter': 'Skilled weapon combat with tactical precision',
            'Monk': 'Swift unarmed strikes and martial arts',
            'Paladin': 'Divine smites and righteous combat',
            'Ranger': 'Ranged attacks and tactical positioning',
            'Rogue': 'Sneaky attacks and precise strikes',
            'Sorcerer': 'Raw magical power and spell bombardment',
            'Warlock': 'Eldritch blasts and pact magic',
            'Wizard': 'Strategic spellcasting and control magic'
        }
        
        return fighting_styles.get(class_name, 'Versatile combat approach')
    
    def _remove_mechanics_terms(self, narrative: str) -> str:
        """Remove any game mechanics terms that might have slipped through."""
        # List of mechanics terms to remove or replace
        mechanics_patterns = [
            (r'\b(rolls?|rolled)\s+(\d+)', 'attempts'),
            (r'\b(saves?|saved|saving throw)\b', 'resists'),
            (r'\bAC\s+\d+\b', ''),
            (r'\bDC\s+\d+\b', ''),
            (r'\bd20\b', ''),
            (r'\bnat(ural)?\s*20\b', ''),
            (r'\bcritical\s+hit\b', 'devastating strike'),
            (r'\b(\d+)\s+damage\b', 'a powerful blow'),
            (r'\binitiative\b', 'readiness'),
            (r'\b(hits?|hit roll)\b', 'strikes'),
        ]
        
        cleaned = narrative
        for pattern, replacement in mechanics_patterns:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        return cleaned
    
    def _narrate_combat_fallback(self, combat_prompt: str, style: str) -> str:
        """Fallback narrative generation when AI is not available."""
        # Simple formatting without AI
        lines = combat_prompt.split('.')
        narrative_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Capitalize first letter
                line = line[0].upper() + line[1:] if len(line) > 1 else line.upper()
                # Remove obvious mechanics terms
                line = self._remove_mechanics_terms(line)
                narrative_lines.append(line)
        
        narrative = ". ".join(narrative_lines) + "."
        
        return f"**Combat Scene:**\n\n{narrative}\n\n*(Note: AI enhancement unavailable. Install AI client for richer combat narratives.)*"
        
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
    
    def _wrap_narrative_text(self, text: str, width: int = 80) -> str:
        """
        Wrap narrative text to specified width while preserving paragraphs.
        
        Args:
            text: The text to wrap
            width: Maximum line width (default 80 characters)
        
        Returns:
            Text wrapped to specified width
        """
        import textwrap
        
        # Split into paragraphs
        paragraphs = text.split('\n\n')
        wrapped_paragraphs = []
        
        for para in paragraphs:
            # Skip if it's a heading, dialogue, or special formatting
            stripped = para.strip()
            if (stripped.startswith('#') or 
                stripped.startswith('**') or 
                stripped.startswith('"') or
                len(stripped) < width):
                wrapped_paragraphs.append(para)
            else:
                # Wrap the paragraph
                wrapped = textwrap.fill(stripped, width=width, break_long_words=False, break_on_hyphens=False)
                wrapped_paragraphs.append(wrapped)
        
        return '\n\n'.join(wrapped_paragraphs)
    
    def generate_combat_title(self, combat_prompt: str, story_context: str = "") -> str:
        """
        Generate a situational combat title based on the combat description and story context.
        
        Args:
            combat_prompt: The tactical combat description
            story_context: Optional story context for better title generation
            
        Returns:
            A descriptive combat title (e.g., "The Goblin Ambush", "Showdown with the Dragon")
        """
        if not self.ai_client:
            # Fallback: extract creatures from prompt
            creatures = re.findall(r'\b(goblin|orc|dragon|skeleton|zombie|bandit|wolf|bear|cultist|spider|troll)s?\b', 
                                 combat_prompt.lower())
            if creatures:
                creature = creatures[0].capitalize()
                return f"The {creature} Encounter"
            return "Combat"
        
        try:
            # Use AI to generate a contextual title
            prompt = f"""Based on this combat description, generate a SHORT, situational combat title (3-5 words maximum).

Combat: {combat_prompt}

{"Recent story context: " + story_context[-500:] if story_context else ""}

Generate ONLY the title, nothing else. Make it dramatic and specific to the situation.
Examples: "The Goblin Ambush", "Showdown at the Bridge", "Dragon's Fury", "Battle in the Tavern"

Title:"""
            
            title = self.ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            ).strip()
            
            # Clean up the title
            title = title.strip('"\'.')
            
            # Validate title length (should be short)
            if len(title.split()) > 6:
                # Too long, use fallback
                creatures = re.findall(r'\b(goblin|orc|dragon|skeleton|zombie|bandit|wolf|bear|cultist|spider|troll)s?\b', 
                                     combat_prompt.lower())
                if creatures:
                    creature = creatures[0].capitalize()
                    return f"The {creature} Encounter"
                return "Combat Encounter"
            
            return title
            
        except Exception as e:
            print(f"⚠️  Title generation failed: {e}")
            # Fallback: extract creatures from prompt
            creatures = re.findall(r'\b(goblin|orc|dragon|skeleton|zombie|bandit|wolf|bear|cultist|spider|troll)s?\b', 
                                 combat_prompt.lower())
            if creatures:
                creature = creatures[0].capitalize()
                return f"The {creature} Encounter"
            return "Combat Encounter"