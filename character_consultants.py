"""
Character Consultant System - 12 AI agents (one per D&D 5e 2024 class) 
that provide character knowledge, suggestions, and story consistency analysis.
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from character_sheet import DnDClass, CharacterSheet


@dataclass
class CharacterProfile:
    """Extended character profile with custom background and consultant capabilities."""
    name: str
    character_class: DnDClass
    level: int = 1
    
    # Custom background (written by user)
    background_story: str = ""
    personality_summary: str = ""
    motivations: List[str] = field(default_factory=list)
    fears_weaknesses: List[str] = field(default_factory=list)
    relationships: Dict[str, str] = field(default_factory=dict)  # character_name: relationship_description
    goals: List[str] = field(default_factory=list)
    secrets: List[str] = field(default_factory=list)
    
    # Class-specific knowledge
    preferred_strategies: List[str] = field(default_factory=list)
    typical_reactions: Dict[str, str] = field(default_factory=dict)  # situation_type: typical_reaction
    speech_patterns: List[str] = field(default_factory=list)
    decision_making_style: str = ""
    
    # Story integration
    story_hooks: List[str] = field(default_factory=list)
    character_arcs: List[str] = field(default_factory=list)
    
    def save_to_file(self, filepath: str):
        """Save character profile to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.__dict__, f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, filepath: str):
        """Load character profile from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle both 'character_class' and 'dnd_class' field names
        character_class_name = data.get('character_class', data.get('dnd_class', 'Fighter'))
        try:
            character_class = DnDClass(character_class_name)
        except ValueError:
            # If the class name doesn't match enum, default to Fighter
            character_class = DnDClass.FIGHTER
        
        profile = cls(
            name=data.get('name', 'Unknown'),
            character_class=character_class,
            level=data.get('level', 1)
        )
        
        # Set attributes from JSON, mapping field names as needed
        profile.background_story = data.get('backstory', data.get('background_story', ''))
        profile.personality_summary = '; '.join(data.get('personality_traits', []))
        profile.motivations = data.get('bonds', data.get('motivations', []))
        profile.fears_weaknesses = data.get('flaws', data.get('fears_weaknesses', []))
        profile.relationships = data.get('relationships', {})
        profile.goals = data.get('goals', [])
        profile.secrets = data.get('secrets', [])
        
        # Set other optional attributes if they exist
        for key in ['preferred_strategies', 'typical_reactions', 'speech_patterns', 
                   'decision_making_style', 'story_hooks', 'character_arcs']:
            if key in data:
                setattr(profile, key, data[key])
        
        return profile


class CharacterConsultant:
    """AI consultant for a specific character, provides advice and analysis."""
    
    def __init__(self, profile: CharacterProfile):
        self.profile = profile
        self.class_knowledge = self._load_class_knowledge()
    
    def _load_class_knowledge(self) -> Dict[str, Any]:
        """Load D&D 5e (2024) class-specific knowledge."""
        class_data = {
            "Barbarian": {
                "primary_ability": "Strength",
                "typical_role": "Tank/Damage",
                "decision_style": "Instinctive and direct",
                "common_reactions": {
                    "threat": "Charge headfirst into danger",
                    "puzzle": "Try to solve with brute force first",
                    "social": "Speak bluntly and honestly",
                    "magic": "Distrust or be wary of magic"
                },
                "key_features": ["Rage", "Unarmored Defense", "Reckless Attack"],
                "roleplay_notes": "Often act on emotion, value strength and courage"
            },
            "Bard": {
                "primary_ability": "Charisma",
                "typical_role": "Support/Face",
                "decision_style": "Creative and social",
                "common_reactions": {
                    "threat": "Try to talk way out or inspire allies",
                    "puzzle": "Use knowledge and creativity",
                    "social": "Take the lead in conversations",
                    "magic": "Appreciate all forms of magic and art"
                },
                "key_features": ["Bardic Inspiration", "Spellcasting", "Jack of All Trades"],
                "roleplay_notes": "Love stories, music, and being the center of attention"
            },
            "Cleric": {
                "primary_ability": "Wisdom",
                "typical_role": "Healer/Support",
                "decision_style": "Faith-based and protective",
                "common_reactions": {
                    "threat": "Protect allies and fight evil",
                    "puzzle": "Seek divine guidance or wisdom",
                    "social": "Offer comfort and moral guidance",
                    "magic": "View divine magic as sacred duty"
                },
                "key_features": ["Spellcasting", "Channel Divinity", "Divine Domain"],
                "roleplay_notes": "Strong moral compass, serve their deity's will"
            },
            "Druid": {
                "primary_ability": "Wisdom", 
                "typical_role": "Versatile Caster",
                "decision_style": "Nature-focused and balanced",
                "common_reactions": {
                    "threat": "Use nature's power or wild shape",
                    "puzzle": "Look for natural solutions",
                    "social": "Advocate for nature and balance",
                    "magic": "Prefer natural magic over artificial"
                },
                "key_features": ["Spellcasting", "Wild Shape", "Druidcraft"],
                "roleplay_notes": "Protect nature, suspicious of civilization"
            },
            "Fighter": {
                "primary_ability": "Strength or Dexterity",
                "typical_role": "Tank/Damage",
                "decision_style": "Tactical and disciplined",
                "common_reactions": {
                    "threat": "Assess tactically and engage strategically",
                    "puzzle": "Use experience and practical knowledge",
                    "social": "Be direct and honest",
                    "magic": "Respect magic but rely on martial skill"
                },
                "key_features": ["Fighting Style", "Action Surge", "Extra Attack"],
                "roleplay_notes": "Disciplined, value training and skill"
            },
            "Monk": {
                "primary_ability": "Dexterity and Wisdom",
                "typical_role": "Mobile Striker",
                "decision_style": "Contemplative and disciplined",
                "common_reactions": {
                    "threat": "Use speed and ki abilities",
                    "puzzle": "Meditate and seek inner wisdom",
                    "social": "Speak thoughtfully and with purpose",
                    "magic": "View ki as internal magic"
                },
                "key_features": ["Martial Arts", "Ki", "Unarmored Defense"],
                "roleplay_notes": "Seek self-improvement and inner peace"
            },
            "Paladin": {
                "primary_ability": "Strength and Charisma",
                "typical_role": "Tank/Support",
                "decision_style": "Honor-bound and righteous",
                "common_reactions": {
                    "threat": "Stand firm against evil",
                    "puzzle": "Apply oath principles",
                    "social": "Lead by example and inspire",
                    "magic": "Use divine power for righteous cause"
                },
                "key_features": ["Divine Sense", "Lay on Hands", "Sacred Oath"],
                "roleplay_notes": "Follow sacred oath, champion justice"
            },
            "Ranger": {
                "primary_ability": "Dexterity and Wisdom",
                "typical_role": "Scout/Damage",
                "decision_style": "Practical and observant",
                "common_reactions": {
                    "threat": "Use terrain and ranged attacks",
                    "puzzle": "Apply survival knowledge",
                    "social": "Be cautious with strangers",
                    "magic": "Use nature magic practically"
                },
                "key_features": ["Favored Enemy", "Natural Explorer", "Spellcasting"],
                "roleplay_notes": "Independent, protect civilization's borders"
            },
            "Rogue": {
                "primary_ability": "Dexterity",
                "typical_role": "Scout/Damage",
                "decision_style": "Opportunistic and careful",
                "common_reactions": {
                    "threat": "Look for advantages and weak points",
                    "puzzle": "Find creative or sneaky solutions",
                    "social": "Read people and situations carefully",
                    "magic": "Be wary but appreciate utility"
                },
                "key_features": ["Sneak Attack", "Thieves' Cant", "Cunning Action"],
                "roleplay_notes": "Trust carefully, always have an escape plan"
            },
            "Sorcerer": {
                "primary_ability": "Charisma",
                "typical_role": "Damage/Utility Caster",
                "decision_style": "Intuitive and emotional",
                "common_reactions": {
                    "threat": "React with raw magical power",
                    "puzzle": "Use innate magical understanding",
                    "social": "Let emotions guide interactions",
                    "magic": "Magic is part of their being"
                },
                "key_features": ["Spellcasting", "Sorcerous Origin", "Metamagic"],
                "roleplay_notes": "Magic is instinctive, often emotional"
            },
            "Warlock": {
                "primary_ability": "Charisma",
                "typical_role": "Damage/Utility Caster",
                "decision_style": "Driven by pact obligations",
                "common_reactions": {
                    "threat": "Use eldritch power strategically",
                    "puzzle": "Consult patron knowledge",
                    "social": "Pursue personal agenda",
                    "magic": "Magic comes with a price"
                },
                "key_features": ["Otherworldly Patron", "Pact Magic", "Eldritch Invocations"],
                "roleplay_notes": "Bound by pact, complex relationship with patron"
            },
            "Wizard": {
                "primary_ability": "Intelligence", 
                "typical_role": "Utility/Control Caster",
                "decision_style": "Analytical and methodical",
                "common_reactions": {
                    "threat": "Analyze and use appropriate spell",
                    "puzzle": "Apply knowledge and research",
                    "social": "Use intelligence and reasoning",
                    "magic": "Magic is science to be mastered"
                },
                "key_features": ["Spellcasting", "Arcane Recovery", "Spell Mastery"],
                "roleplay_notes": "Knowledge is power, always learning"
            }
        }
        
        return class_data.get(self.profile.character_class.value, {})
    
    def suggest_reaction(self, situation: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Suggest how this character would react to a situation."""
        context = context or {}
        
        # Determine situation type
        situation_lower = situation.lower()
        if any(word in situation_lower for word in ['fight', 'combat', 'attack', 'enemy']):
            situation_type = 'threat'
        elif any(word in situation_lower for word in ['puzzle', 'riddle', 'mystery', 'problem']):
            situation_type = 'puzzle'
        elif any(word in situation_lower for word in ['talk', 'negotiate', 'persuade', 'social']):
            situation_type = 'social'
        elif any(word in situation_lower for word in ['magic', 'spell', 'arcane', 'divine']):
            situation_type = 'magic'
        else:
            situation_type = 'general'
        
        # Get class-based reaction
        class_reaction = self.class_knowledge.get('common_reactions', {}).get(situation_type, "Act according to class nature")
        
        # Get personality-based modification
        personality_modifier = self._get_personality_modifier(situation_type)
        
        # Check for relevant motivations
        relevant_motivations = [m for m in self.profile.motivations if any(word in situation.lower() for word in m.lower().split())]
        
        return {
            'character': self.profile.name,
            'class_reaction': class_reaction,
            'personality_modifier': personality_modifier,
            'relevant_motivations': relevant_motivations,
            'suggested_approach': self._synthesize_approach(situation, situation_type),
            'dialogue_suggestion': self._suggest_dialogue(situation, situation_type),
            'consistency_notes': self._check_consistency_factors(situation)
        }
    
    def _get_personality_modifier(self, situation_type: str) -> str:
        """Get personality-based modification to class reaction."""
        if not self.profile.personality_summary:
            return "Act according to established personality"
        
        modifiers = {
            'threat': f"Given {self.profile.name}'s personality ({self.profile.personality_summary}), they might approach threats",
            'social': f"In social situations, {self.profile.name}'s {self.profile.personality_summary} nature would lead them to",
            'puzzle': f"When problem-solving, {self.profile.name}'s {self.profile.personality_summary} personality suggests they would",
            'magic': f"Regarding magic, {self.profile.name}'s {self.profile.personality_summary} outlook would"
        }
        
        return modifiers.get(situation_type, f"Given their {self.profile.personality_summary} nature, {self.profile.name} would")
    
    def _synthesize_approach(self, situation: str, situation_type: str) -> str:
        """Synthesize overall approach recommendation."""
        class_style = self.class_knowledge.get('decision_style', 'methodically')
        
        if self.profile.goals:
            goal_influence = f"considering their goal: {self.profile.goals[0]}"
        else:
            goal_influence = "staying true to their character"
        
        return f"{self.profile.name} would likely approach this {class_style}, {goal_influence}."
    
    def _suggest_dialogue(self, situation: str, situation_type: str) -> str:
        """Suggest what the character might say."""
        if self.profile.speech_patterns:
            speech_note = f"Speaking in their typical {self.profile.speech_patterns[0]} manner"
        else:
            speech_note = f"Speaking as a {self.profile.character_class.value} would"
        
        return f"{speech_note}, {self.profile.name} might say something that reflects their class nature and personal motivations."
    
    def _check_consistency_factors(self, situation: str) -> List[str]:
        """Identify factors that should be considered for character consistency."""
        factors = []
        
        # Check against fears/weaknesses
        for fear in self.profile.fears_weaknesses:
            if any(word in situation.lower() for word in fear.lower().split()):
                factors.append(f"Remember {self.profile.name} has issues with: {fear}")
        
        # Check against motivations
        for motivation in self.profile.motivations:
            if any(word in situation.lower() for word in motivation.lower().split()):
                factors.append(f"This situation relates to {self.profile.name}'s motivation: {motivation}")
        
        # Class-specific consistency
        roleplay_notes = self.class_knowledge.get('roleplay_notes', '')
        if roleplay_notes:
            factors.append(f"As a {self.profile.character_class.value}: {roleplay_notes}")
        
        return factors
    
    def analyze_story_consistency(self, story_text: str, character_actions: List[str]) -> Dict[str, Any]:
        """Analyze if character actions in a story are consistent with their profile."""
        consistency_score = 0
        issues = []
        positive_notes = []
        
        # Check each action against character profile
        for action in character_actions:
            action_analysis = self._analyze_single_action(action, story_text)
            consistency_score += action_analysis['score']
            issues.extend(action_analysis['issues'])
            positive_notes.extend(action_analysis['positives'])
        
        average_score = consistency_score / len(character_actions) if character_actions else 0
        
        return {
            'character': self.profile.name,
            'consistency_score': round(average_score, 2),
            'overall_rating': self._get_consistency_rating(average_score),
            'issues': issues,
            'positive_notes': positive_notes,
            'suggestions': self._get_improvement_suggestions(issues)
        }
    
    def _analyze_single_action(self, action: str, context: str) -> Dict[str, Any]:
        """Analyze a single character action for consistency."""
        score = 0.5  # Neutral starting score
        issues = []
        positives = []
        
        action_lower = action.lower()
        
        # Check against class tendencies
        class_reactions = self.class_knowledge.get('common_reactions', {})
        for situation, expected in class_reactions.items():
            if situation in context.lower():
                if any(word in action_lower for word in expected.lower().split()):
                    score += 0.3
                    positives.append(f"Action aligns with {self.profile.character_class.value} nature")
        
        # Check against personality
        if self.profile.personality_summary:
            personality_words = self.profile.personality_summary.lower().split()
            if any(word in action_lower for word in personality_words):
                score += 0.2
                positives.append("Action reflects established personality")
        
        # Check against motivations
        for motivation in self.profile.motivations:
            if any(word in action_lower for word in motivation.lower().split()):
                score += 0.2
                positives.append(f"Action driven by motivation: {motivation}")
        
        # Check against fears/weaknesses (should be hesitant or conflicted)
        for fear in self.profile.fears_weaknesses:
            if any(word in context.lower() for word in fear.lower().split()):
                if 'hesitat' in action_lower or 'reluctant' in action_lower or 'afraid' in action_lower:
                    score += 0.1
                    positives.append(f"Appropriately shows concern about: {fear}")
                else:
                    score -= 0.2
                    issues.append(f"Didn't acknowledge fear/weakness: {fear}")
        
        return {
            'score': max(0, min(1, score)),  # Clamp between 0 and 1
            'issues': issues,
            'positives': positives
        }
    
    def _get_consistency_rating(self, score: float) -> str:
        """Convert numerical score to rating."""
        if score >= 0.8:
            return "Excellent - Very true to character"
        elif score >= 0.6:
            return "Good - Mostly consistent"
        elif score >= 0.4:
            return "Fair - Some inconsistencies"
        elif score >= 0.2:
            return "Poor - Several character issues"
        else:
            return "Very Poor - Out of character"
    
    def _get_improvement_suggestions(self, issues: List[str]) -> List[str]:
        """Generate suggestions for improving character consistency."""
        suggestions = []
        
        if issues:
            suggestions.append(f"Consider how {self.profile.name}'s {self.profile.character_class.value} training would influence their approach")
            
            if self.profile.motivations:
                suggestions.append(f"Remember {self.profile.name}'s primary motivation: {self.profile.motivations[0]}")
            
            if self.profile.personality_summary:
                suggestions.append(f"Keep {self.profile.name}'s {self.profile.personality_summary} personality in mind")
        
        return suggestions
    
    def suggest_dc_for_action(self, action_description: str, character_abilities: Dict[str, int] = None) -> Dict[str, Any]:
        """Suggest appropriate DC for an action this character wants to take."""
        action_lower = action_description.lower()
        
        # Determine action type and base DC
        if any(word in action_lower for word in ['persuade', 'convince', 'negotiate']):
            action_type = 'Persuasion'
            base_dc = 15
        elif any(word in action_lower for word in ['deceive', 'lie', 'bluff']):
            action_type = 'Deception'
            base_dc = 15
        elif any(word in action_lower for word in ['intimidate', 'threaten', 'menace']):
            action_type = 'Intimidation'
            base_dc = 15
        elif any(word in action_lower for word in ['sneak', 'hide', 'stealth']):
            action_type = 'Stealth'
            base_dc = 15
        elif any(word in action_lower for word in ['climb', 'jump', 'athletics']):
            action_type = 'Athletics'
            base_dc = 15
        elif any(word in action_lower for word in ['search', 'investigate', 'examine']):
            action_type = 'Investigation'
            base_dc = 15
        elif any(word in action_lower for word in ['notice', 'spot', 'perceive']):
            action_type = 'Perception'
            base_dc = 15
        else:
            action_type = 'General'
            base_dc = 15
        
        # Adjust DC based on difficulty indicators
        if any(word in action_lower for word in ['easy', 'simple', 'basic']):
            adjusted_dc = base_dc - 5
        elif any(word in action_lower for word in ['hard', 'difficult', 'challenging']):
            adjusted_dc = base_dc + 5
        elif any(word in action_lower for word in ['impossible', 'extreme', 'legendary']):
            adjusted_dc = base_dc + 10
        else:
            adjusted_dc = base_dc
        
        # Consider class strengths
        class_bonuses = {
            'Rogue': {'Stealth': -2, 'Investigation': -2, 'Deception': -1},
            'Bard': {'Persuasion': -2, 'Deception': -1, 'Performance': -2},
            'Paladin': {'Intimidation': -1, 'Persuasion': -1},
            'Ranger': {'Stealth': -1, 'Perception': -2, 'Athletics': -1},
            'Fighter': {'Athletics': -2, 'Intimidation': -1},
            'Barbarian': {'Athletics': -2, 'Intimidation': -2},
            'Monk': {'Athletics': -1, 'Stealth': -1},
            'Cleric': {'Persuasion': -1, 'Insight': -2},
            'Wizard': {'Investigation': -2, 'Arcana': -2},
            'Sorcerer': {'Persuasion': -1, 'Intimidation': -1},
            'Warlock': {'Deception': -1, 'Intimidation': -1},
            'Druid': {'Perception': -1, 'Animal Handling': -2}
        }
        
        class_adjustment = class_bonuses.get(self.profile.character_class.value, {}).get(action_type, 0)
        final_dc = max(5, adjusted_dc + class_adjustment)
        
        return {
            'action_type': action_type,
            'suggested_dc': final_dc,
            'reasoning': f"Base DC {base_dc}, adjusted for difficulty and {self.profile.character_class.value} abilities",
            'alternative_approaches': self._suggest_alternative_approaches(action_description),
            'character_advantage': self._check_character_advantages(action_type)
        }
    
    def _suggest_alternative_approaches(self, action: str) -> List[str]:
        """Suggest alternative approaches based on character class."""
        alternatives = []
        class_name = self.profile.character_class.value
        
        approach_map = {
            'Barbarian': ["Use intimidation instead of persuasion", "Solve with strength if possible"],
            'Bard': ["Try a different social approach", "Use inspiration or performance"],
            'Cleric': ["Invoke divine guidance", "Appeal to moral principles"],
            'Druid': ["Use natural solutions", "Shape change for advantage"],
            'Fighter': ["Apply military tactics", "Use direct action"],
            'Monk': ["Use patience and observation", "Apply martial arts discipline"],
            'Paladin': ["Lead by example", "Use divine sense"],
            'Ranger': ["Use survival skills", "Apply tracking knowledge"],
            'Rogue': ["Find a sneaky alternative", "Look for weak points"],
            'Sorcerer': ["Use innate magical intuition", "Trust instincts"],
            'Warlock': ["Consult patron knowledge", "Use eldritch powers"],
            'Wizard': ["Research the problem first", "Apply magical analysis"]
        }
        
        return approach_map.get(class_name, ["Consider character-appropriate alternatives"])
    
    def _check_character_advantages(self, action_type: str) -> List[str]:
        """Check if character has natural advantages for this action type."""
        advantages = []
        class_name = self.profile.character_class.value
        
        # Class-based advantages
        if class_name == 'Rogue' and action_type in ['Stealth', 'Investigation', 'Sleight of Hand']:
            advantages.append("Expertise doubles proficiency bonus")
        elif class_name == 'Bard' and action_type in ['Persuasion', 'Deception', 'Performance']:
            advantages.append("Jack of All Trades adds bonus to non-proficient checks")
        elif class_name == 'Ranger' and action_type in ['Perception', 'Survival']:
            advantages.append("Natural Explorer provides advantage in favored terrain")
        
        # Check background advantages from profile
        if 'noble' in self.profile.background_story.lower() and action_type == 'Persuasion':
            advantages.append("Noble background aids in social situations")
        elif 'criminal' in self.profile.background_story.lower() and action_type in ['Stealth', 'Deception']:
            advantages.append("Criminal background provides relevant experience")
        
        return advantages
    
    @classmethod
    def load_from_file(cls, filepath: str):
        """Load character consultant from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create a CharacterProfile from the JSON data
        # The JSON files use 'dnd_class' but CharacterProfile expects 'character_class'
        character_class_name = data.get('dnd_class', 'Fighter')
        try:
            character_class = DnDClass(character_class_name)
        except ValueError:
            # If the class name doesn't match enum, default to Fighter
            character_class = DnDClass.FIGHTER
        
        profile = CharacterProfile(
            name=data.get('name', 'Unknown'),
            character_class=character_class,
            level=data.get('level', 1),
            background_story=data.get('backstory', ''),
            personality_summary='; '.join(data.get('personality_traits', [])),
            motivations=data.get('bonds', []),
            fears_weaknesses=data.get('flaws', []),
            relationships=data.get('relationships', {}),
            goals=[],  # Not in standard JSON
            secrets=[]  # Not in standard JSON
        )
        
        return cls(profile)