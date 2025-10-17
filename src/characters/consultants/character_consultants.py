"""
Character Consultant System - 12 AI agents (one per D&D 5e 2024 class)
that provide character knowledge, suggestions, and story consistency analysis.
"""

# pylint: disable=too-many-lines

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from src.characters.character_sheet import DnDClass
from src.utils.file_io import load_json_file, save_json_file

# Optional imports
try:
    from src.ai.ai_client import CharacterAIConfig
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    CharacterAIConfig = None

try:
    from src.validation.character_validator import validate_character_json
    VALIDATOR_AVAILABLE = True
except ImportError:
    VALIDATOR_AVAILABLE = False
    validate_character_json = None

try:
    from src.ai.rag_system import get_rag_system
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    get_rag_system = None


@dataclass
class CharacterProfile:  # pylint: disable=too-many-instance-attributes
    """Extended character profile with custom background and consultant capabilities."""

    name: str
    character_class: DnDClass
    nickname: Optional[str] = None
    level: int = 1
    species: str = "Human"
    lineage: Optional[str] = None

    # Custom background (written by user)
    background_story: str = ""
    personality_summary: str = ""
    motivations: List[str] = field(default_factory=list)
    fears_weaknesses: List[str] = field(default_factory=list)
    # character_name: relationship_description
    relationships: Dict[str, str] = field(default_factory=dict)
    goals: List[str] = field(default_factory=list)
    secrets: List[str] = field(default_factory=list)

    # Class-specific knowledge
    preferred_strategies: List[str] = field(default_factory=list)
    # situation_type: typical_reaction
    typical_reactions: Dict[str, str] = field(default_factory=dict)
    speech_patterns: List[str] = field(default_factory=list)
    decision_making_style: str = ""

    # Story integration
    story_hooks: List[str] = field(default_factory=list)
    character_arcs: List[str] = field(default_factory=list)

    # Game mechanics (from character JSON files)
    ability_scores: Dict[str, int] = field(default_factory=dict)
    skills: Dict[str, Any] = field(default_factory=dict)
    max_hit_points: int = 0
    armor_class: int = 10
    movement_speed: int = 30
    proficiency_bonus: int = 2
    # {weapons: [], armor: [], items: [], gold: int}
    equipment: Dict[str, List[str]] = field(default_factory=dict)
    spell_slots: Dict[str, int] = field(default_factory=dict)
    known_spells: List[str] = field(default_factory=list)
    background: str = ""
    feats: List[str] = field(default_factory=list)
    magic_items: List[str] = field(default_factory=list)
    class_abilities: List[str] = field(default_factory=list)
    specialized_abilities: List[str] = field(default_factory=list)
    major_plot_actions: List[Any] = field(default_factory=list)
    subclass: Optional[str] = None

    # AI Configuration (optional)
    ai_config: Optional[Dict[str, Any]] = None

    def save_to_file(self, filepath: str):
        """Save character profile to JSON file."""
        data = self.__dict__.copy()
        # Ensure nickname is present (can be None)
        if "nickname" not in data:
            data["nickname"] = None
        # Convert ai_config if it's a CharacterAIConfig object
        if AI_AVAILABLE and hasattr(self, "ai_config") and self.ai_config:
            if isinstance(self.ai_config, CharacterAIConfig):
                data["ai_config"] = self.ai_config.to_dict()

        # Validate before saving
        if VALIDATOR_AVAILABLE and validate_character_json:
            is_valid, errors = validate_character_json(data, filepath)
            if not is_valid:
                print("⚠️  Character profile validation failed:")
                for error in errors:
                    print(f"  - {error}")
                print("  Saving anyway, but please fix these issues.")

        save_json_file(filepath, data)

    @classmethod
    def load_from_file(cls, filepath: str):
        """Load character profile from JSON file."""
        data = load_json_file(filepath)
        # Ensure nickname is present (can be None)
        if "nickname" not in data:
            data["nickname"] = None

        # Handle both 'character_class' and 'dnd_class' field names
        character_class_name = data.get(
            "character_class", data.get("dnd_class", "Fighter")
        )
        try:
            character_class = DnDClass(character_class_name)
        except ValueError:
            # If the class name doesn't match enum, default to Fighter
            character_class = DnDClass.FIGHTER

        profile = cls(
            name=data.get("name", "Unknown"),
            character_class=character_class,
            level=data.get("level", 1),
        )

        # Set attributes from JSON, mapping field names as needed
        profile.background_story = data.get(
            "backstory", data.get("background_story", "")
        )
        profile.personality_summary = "; ".join(data.get("personality_traits", []))
        profile.motivations = data.get("bonds", data.get("motivations", []))
        profile.fears_weaknesses = data.get("flaws", data.get("fears_weaknesses", []))
        profile.relationships = data.get("relationships", {})
        profile.goals = data.get("ideals", data.get("goals", []))
        profile.secrets = data.get("secrets", [])

        # Set other optional attributes if they exist
        for key in [
            "preferred_strategies",
            "typical_reactions",
            "speech_patterns",
            "decision_making_style",
            "story_hooks",
            "character_arcs",
        ]:
            if key in data:
                setattr(profile, key, data[key])

        # Store additional JSON data for full character access
        profile.major_plot_actions = data.get("major_plot_actions", [])
        profile.species = data.get("species", "Human")
        profile.lineage = data.get("lineage")
        profile.subclass = data.get("subclass")
        profile.ability_scores = data.get("ability_scores", {})
        profile.skills = data.get("skills", {})
        profile.max_hit_points = data.get("max_hit_points", 0)
        profile.armor_class = data.get("armor_class", 10)
        profile.movement_speed = data.get("movement_speed", 30)
        profile.proficiency_bonus = data.get("proficiency_bonus", 2)
        profile.equipment = data.get("equipment", {})
        profile.spell_slots = data.get("spell_slots", {})
        profile.known_spells = data.get("known_spells", [])
        profile.background = data.get("background", "")
        profile.feats = data.get("feats", [])
        profile.magic_items = data.get("magic_items", [])
        profile.class_abilities = data.get("class_abilities", [])
        profile.specialized_abilities = data.get("specialized_abilities", [])

        # Load AI configuration if present
        if "ai_config" in data and AI_AVAILABLE:
            profile.ai_config = CharacterAIConfig.from_dict(data["ai_config"])
        elif "ai_config" in data:
            # Store as dict if AI not available
            profile.ai_config = data["ai_config"]

        return profile


class CharacterConsultant:
    """AI consultant for a specific character, provides advice and analysis."""

    def __init__(self, profile: CharacterProfile, ai_client=None):
        """
        Initialize character consultant.

        Args:
            profile: Character profile with personality, background, etc.
            ai_client: Optional global AI client (can be overridden by character config)
        """
        self.profile = profile
        self.class_knowledge = self._load_class_knowledge()
        self.ai_client = ai_client
        self._character_ai_client = None  # Character-specific client if configured

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
                    "magic": "Distrust or be wary of magic",
                },
                "key_features": ["Rage", "Unarmored Defense", "Reckless Attack"],
                "roleplay_notes": "Often act on emotion, value strength and courage",
            },
            "Bard": {
                "primary_ability": "Charisma",
                "typical_role": "Support/Face",
                "decision_style": "Creative and social",
                "common_reactions": {
                    "threat": "Try to talk way out or inspire allies",
                    "puzzle": "Use knowledge and creativity",
                    "social": "Take the lead in conversations",
                    "magic": "Appreciate all forms of magic and art",
                },
                "key_features": [
                    "Bardic Inspiration",
                    "Spellcasting",
                    "Jack of All Trades",
                ],
                "roleplay_notes": "Love stories, music, and being the center of attention",
            },
            "Cleric": {
                "primary_ability": "Wisdom",
                "typical_role": "Healer/Support",
                "decision_style": "Faith-based and protective",
                "common_reactions": {
                    "threat": "Protect allies and fight evil",
                    "puzzle": "Seek divine guidance or wisdom",
                    "social": "Offer comfort and moral guidance",
                    "magic": "View divine magic as sacred duty",
                },
                "key_features": ["Spellcasting", "Channel Divinity", "Divine Domain"],
                "roleplay_notes": "Strong moral compass, serve their deity's will",
            },
            "Druid": {
                "primary_ability": "Wisdom",
                "typical_role": "Versatile Caster",
                "decision_style": "Nature-focused and balanced",
                "common_reactions": {
                    "threat": "Use nature's power or wild shape",
                    "puzzle": "Look for natural solutions",
                    "social": "Advocate for nature and balance",
                    "magic": "Prefer natural magic over artificial",
                },
                "key_features": ["Spellcasting", "Wild Shape", "Druidcraft"],
                "roleplay_notes": "Protect nature, suspicious of civilization",
            },
            "Fighter": {
                "primary_ability": "Strength or Dexterity",
                "typical_role": "Tank/Damage",
                "decision_style": "Tactical and disciplined",
                "common_reactions": {
                    "threat": "Assess tactically and engage strategically",
                    "puzzle": "Use experience and practical knowledge",
                    "social": "Be direct and honest",
                    "magic": "Respect magic but rely on martial skill",
                },
                "key_features": ["Fighting Style", "Action Surge", "Extra Attack"],
                "roleplay_notes": "Disciplined, value training and skill",
            },
            "Monk": {
                "primary_ability": "Dexterity and Wisdom",
                "typical_role": "Mobile Striker",
                "decision_style": "Contemplative and disciplined",
                "common_reactions": {
                    "threat": "Use speed and ki abilities",
                    "puzzle": "Meditate and seek inner wisdom",
                    "social": "Speak thoughtfully and with purpose",
                    "magic": "View ki as internal magic",
                },
                "key_features": ["Martial Arts", "Ki", "Unarmored Defense"],
                "roleplay_notes": "Seek self-improvement and inner peace",
            },
            "Paladin": {
                "primary_ability": "Strength and Charisma",
                "typical_role": "Tank/Support",
                "decision_style": "Honor-bound and righteous",
                "common_reactions": {
                    "threat": "Stand firm against evil",
                    "puzzle": "Apply oath principles",
                    "social": "Lead by example and inspire",
                    "magic": "Use divine power for righteous cause",
                },
                "key_features": ["Divine Sense", "Lay on Hands", "Sacred Oath"],
                "roleplay_notes": "Follow sacred oath, champion justice",
            },
            "Ranger": {
                "primary_ability": "Dexterity and Wisdom",
                "typical_role": "Scout/Damage",
                "decision_style": "Practical and observant",
                "common_reactions": {
                    "threat": "Use terrain and ranged attacks",
                    "puzzle": "Apply survival knowledge",
                    "social": "Be cautious with strangers",
                    "magic": "Use nature magic practically",
                },
                "key_features": ["Favored Enemy", "Natural Explorer", "Spellcasting"],
                "roleplay_notes": "Independent, protect civilization's borders",
            },
            "Rogue": {
                "primary_ability": "Dexterity",
                "typical_role": "Scout/Damage",
                "decision_style": "Opportunistic and careful",
                "common_reactions": {
                    "threat": "Look for advantages and weak points",
                    "puzzle": "Find creative or sneaky solutions",
                    "social": "Read people and situations carefully",
                    "magic": "Be wary but appreciate utility",
                },
                "key_features": ["Sneak Attack", "Thieves' Cant", "Cunning Action"],
                "roleplay_notes": "Trust carefully, always have an escape plan",
            },
            "Sorcerer": {
                "primary_ability": "Charisma",
                "typical_role": "Damage/Utility Caster",
                "decision_style": "Intuitive and emotional",
                "common_reactions": {
                    "threat": "React with raw magical power",
                    "puzzle": "Use innate magical understanding",
                    "social": "Let emotions guide interactions",
                    "magic": "Magic is part of their being",
                },
                "key_features": ["Spellcasting", "Sorcerous Origin", "Metamagic"],
                "roleplay_notes": "Magic is instinctive, often emotional",
            },
            "Warlock": {
                "primary_ability": "Charisma",
                "typical_role": "Damage/Utility Caster",
                "decision_style": "Driven by pact obligations",
                "common_reactions": {
                    "threat": "Use eldritch power strategically",
                    "puzzle": "Consult patron knowledge",
                    "social": "Pursue personal agenda",
                    "magic": "Magic comes with a price",
                },
                "key_features": [
                    "Otherworldly Patron",
                    "Pact Magic",
                    "Eldritch Invocations",
                ],
                "roleplay_notes": "Bound by pact, complex relationship with patron",
            },
            "Wizard": {
                "primary_ability": "Intelligence",
                "typical_role": "Utility/Control Caster",
                "decision_style": "Analytical and methodical",
                "common_reactions": {
                    "threat": "Analyze and use appropriate spell",
                    "puzzle": "Apply knowledge and research",
                    "social": "Use intelligence and reasoning",
                    "magic": "Magic is science to be mastered",
                },
                "key_features": ["Spellcasting", "Arcane Recovery", "Spell Mastery"],
                "roleplay_notes": "Knowledge is power, always learning",
            },
        }

        return class_data.get(self.profile.character_class.value, {})

    def suggest_reaction(
        self, situation: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Suggest how this character would react to a situation."""
        context = context or {}

        # Determine situation type
        situation_lower = situation.lower()
        if any(
            word in situation_lower for word in ["fight", "combat", "attack", "enemy"]
        ):
            situation_type = "threat"
        elif any(
            word in situation_lower
            for word in ["puzzle", "riddle", "mystery", "problem"]
        ):
            situation_type = "puzzle"
        elif any(
            word in situation_lower
            for word in ["talk", "negotiate", "persuade", "social"]
        ):
            situation_type = "social"
        elif any(
            word in situation_lower for word in ["magic", "spell", "arcane", "divine"]
        ):
            situation_type = "magic"
        else:
            situation_type = "general"

        # Get class-based reaction
        class_reaction = self.class_knowledge.get("common_reactions", {}).get(
            situation_type, "Act according to class nature"
        )

        # Get personality-based modification
        personality_modifier = self._get_personality_modifier(situation_type)

        # Check for relevant motivations
        relevant_motivations = [
            m
            for m in self.profile.motivations
            if any(word in situation.lower() for word in m.lower().split())
        ]

        return {
            "character": self.profile.name,
            "class_reaction": class_reaction,
            "personality_modifier": personality_modifier,
            "relevant_motivations": relevant_motivations,
            "suggested_approach": self._synthesize_approach(situation, situation_type),
            "dialogue_suggestion": self._suggest_dialogue(situation, situation_type),
            "consistency_notes": self._check_consistency_factors(situation),
        }

    def _get_personality_modifier(self, situation_type: str) -> str:
        """Get personality-based modification to class reaction."""
        if not self.profile.personality_summary:
            return "Act according to established personality"

        modifiers = {
            "threat": (
                f"Given {self.profile.name}'s personality "
                f"({self.profile.personality_summary}), they might approach threats"
            ),
            "social": (
                f"In social situations, {self.profile.name}'s "
                f"{self.profile.personality_summary} nature would lead them to"
            ),
            "puzzle": (
                f"When problem-solving, {self.profile.name}'s "
                f"{self.profile.personality_summary} personality suggests they would"
            ),
            "magic": (
                f"Regarding magic, {self.profile.name}'s "
                f"{self.profile.personality_summary} outlook would"
            ),
        }

        return modifiers.get(
            situation_type,
            f"Given their {self.profile.personality_summary} nature, {self.profile.name} would",
        )

    def _synthesize_approach(self, _situation: str, _situation_type: str) -> str:
        """Synthesize overall approach recommendation."""
        class_style = self.class_knowledge.get("decision_style", "methodically")

        if self.profile.goals:
            goal_influence = f"considering their goal: {self.profile.goals[0]}"
        else:
            goal_influence = "staying true to their character"

        return f"{self.profile.name} would likely approach this {class_style}, {goal_influence}."

    def _suggest_dialogue(self, _situation: str, _situation_type: str) -> str:
        """Suggest what the character might say."""
        if self.profile.speech_patterns:
            speech_note = (
                f"Speaking in their typical {self.profile.speech_patterns[0]} manner"
            )
        else:
            speech_note = f"Speaking as a {self.profile.character_class.value} would"

        return (
            f"{speech_note}, {self.profile.name} might say something that reflects "
            f"their class nature and personal motivations."
        )

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
                factors.append(
                    f"This situation relates to {self.profile.name}'s"
                    f" motivation: {motivation}"
                )

        # Class-specific consistency
        roleplay_notes = self.class_knowledge.get("roleplay_notes", "")
        if roleplay_notes:
            factors.append(
                f"As a {self.profile.character_class.value}: {roleplay_notes}"
            )

        return factors

    def analyze_story_consistency(
        self, story_text: str, character_actions: List[str]
    ) -> Dict[str, Any]:
        """Analyze if character actions in a story are consistent with their profile."""
        consistency_score = 0
        issues = []
        positive_notes = []

        # Check each action against character profile
        for action in character_actions:
            action_analysis = self._analyze_single_action(action, story_text)
            consistency_score += action_analysis["score"]
            issues.extend(action_analysis["issues"])
            positive_notes.extend(action_analysis["positives"])

        average_score = (
            consistency_score / len(character_actions) if character_actions else 0
        )

        return {
            "character": self.profile.name,
            "consistency_score": round(average_score, 2),
            "overall_rating": self._get_consistency_rating(average_score),
            "issues": issues,
            "positive_notes": positive_notes,
            "suggestions": self._get_improvement_suggestions(issues),
        }

    def _analyze_single_action(self, action: str, context: str) -> Dict[str, Any]:
        """Analyze a single character action for consistency."""
        score = 0.5  # Neutral starting score
        issues = []
        positives = []

        action_lower = action.lower()

        # Check against class tendencies
        class_reactions = self.class_knowledge.get("common_reactions", {})
        for situation, expected in class_reactions.items():
            if situation in context.lower():
                if any(word in action_lower for word in expected.lower().split()):
                    score += 0.3
                    positives.append(
                        f"Action aligns with {self.profile.character_class.value} nature"
                    )

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
                if (
                    "hesitat" in action_lower
                    or "reluctant" in action_lower
                    or "afraid" in action_lower
                ):
                    score += 0.1
                    positives.append(f"Appropriately shows concern about: {fear}")
                else:
                    score -= 0.2
                    issues.append(f"Didn't acknowledge fear/weakness: {fear}")

        return {
            "score": max(0, min(1, score)),  # Clamp between 0 and 1
            "issues": issues,
            "positives": positives,
        }

    def _get_consistency_rating(self, score: float) -> str:
        """Convert numerical score to rating."""
        if score >= 0.8:
            return "Excellent - Very true to character"
        if score >= 0.6:
            return "Good - Mostly consistent"
        if score >= 0.4:
            return "Fair - Some inconsistencies"
        if score >= 0.2:
            return "Poor - Several character issues"
        return "Very Poor - Out of character"

    def _get_improvement_suggestions(self, issues: List[str]) -> List[str]:
        """Generate suggestions for improving character consistency."""
        suggestions = []

        if issues:
            suggestions.append(
                f"Consider how {self.profile.name}'s "
                f"{self.profile.character_class.value} training would influence their approach"
            )

            if self.profile.motivations:
                suggestions.append(
                    f"Remember {self.profile.name}'s primary motivation: "
                    f"{self.profile.motivations[0]}"
                )

            if self.profile.personality_summary:
                suggestions.append(
                    f"Keep {self.profile.name}'s {self.profile.personality_summary} "
                    f"personality in mind"
                )

        return suggestions

    def get_all_character_items(self) -> List[str]:
        """
        Extract all items character has (equipment + magic items).

        Returns:
            List of item names
        """
        items = []

        # Get equipment
        equipment = getattr(self.profile, "equipment", {})
        if isinstance(equipment, dict):
            items.extend(equipment.get("weapons", []))
            items.extend(equipment.get("armor", []))
            items.extend(equipment.get("items", []))
        elif isinstance(equipment, list):
            items.extend(equipment)

        # Get magic items
        magic_items = getattr(self.profile, "magic_items", [])
        if isinstance(magic_items, list):
            items.extend(magic_items)

        return items

    def get_item_details(self, item_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about an item using RAG system.

        Args:
            item_name: Name of the item to lookup

        Returns:
            Dict with item info (from custom registry or wikidot), or None if not found
        """
        if not RAG_AVAILABLE or not get_rag_system:
            return None

        try:
            rag = get_rag_system()
            return rag.fetch_item_info(item_name)
        except (AttributeError, KeyError, ValueError) as e:
            print(f"Warning: Could not fetch item info for '{item_name}': {e}")
            return None

    def suggest_dc_for_action(
        self, action_description: str, _character_abilities: Dict[str, int] = None
    ) -> Dict[str, Any]:
        """Suggest appropriate DC for an action this character wants to take."""
        action_lower = action_description.lower()

        # Determine action type and base DC
        if any(word in action_lower for word in ["persuade", "convince", "negotiate"]):
            action_type = "Persuasion"
            base_dc = 15
        elif any(word in action_lower for word in ["deceive", "lie", "bluff"]):
            action_type = "Deception"
            base_dc = 15
        elif any(word in action_lower for word in ["intimidate", "threaten", "menace"]):
            action_type = "Intimidation"
            base_dc = 15
        elif any(word in action_lower for word in ["sneak", "hide", "stealth"]):
            action_type = "Stealth"
            base_dc = 15
        elif any(word in action_lower for word in ["climb", "jump", "athletics"]):
            action_type = "Athletics"
            base_dc = 15
        elif any(word in action_lower for word in ["search", "investigate", "examine"]):
            action_type = "Investigation"
            base_dc = 15
        elif any(word in action_lower for word in ["notice", "spot", "perceive"]):
            action_type = "Perception"
            base_dc = 15
        else:
            action_type = "General"
            base_dc = 15

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
            "alternative_approaches": self._suggest_alternative_approaches(
                action_description
            ),
            "character_advantage": self._check_character_advantages(action_type),
        }

    def _suggest_alternative_approaches(self, _action: str) -> List[str]:
        """Suggest alternative approaches based on character class."""
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

    def _check_character_advantages(self, action_type: str) -> List[str]:
        """Check if character has natural advantages for this action type."""
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

    def _get_ai_client(self):
        """
        Get the appropriate AI client for this character.
        Returns character-specific client if configured, otherwise global client.
        """
        if not AI_AVAILABLE:
            return None

        # Create character-specific client if configured and not yet created
        if self.profile.ai_config and not self._character_ai_client:
            if isinstance(self.profile.ai_config, CharacterAIConfig):
                self._character_ai_client = self.profile.ai_config.create_client(
                    self.ai_client
                )
            elif isinstance(
                self.profile.ai_config, dict
            ) and self.profile.ai_config.get("enabled"):
                # Convert dict to CharacterAIConfig
                config = CharacterAIConfig.from_dict(self.profile.ai_config)
                self._character_ai_client = config.create_client(self.ai_client)

        # Return character-specific or global client
        return self._character_ai_client or self.ai_client

    def _build_character_system_prompt(self) -> str:
        """Build a system prompt that describes this character for AI roleplay."""
        prompt_parts = [
            f"You are {self.profile.name}, a {self.profile.character_class.value}"
            " in a D&D 5e campaign.",
            f"You are level {self.profile.level}.",
        ]

        if self.profile.background_story:
            prompt_parts.append(
                f"\nYour background: {self.profile.background_story[:500]}"
            )

        if self.profile.personality_summary:
            prompt_parts.append(
                f"\nYour personality: {self.profile.personality_summary}"
            )

        if self.profile.motivations:
            prompt_parts.append(
                f"\nYour motivations: {', '.join(self.profile.motivations)}"
            )

        if self.profile.goals:
            prompt_parts.append(f"\nYour goals: {', '.join(self.profile.goals)}")

        if self.profile.fears_weaknesses:
            prompt_parts.append(
                f"\nYour fears/weaknesses: {', '.join(self.profile.fears_weaknesses)}"
            )

        # Add class knowledge
        class_knowledge = self.class_knowledge
        if class_knowledge:
            decision_style = class_knowledge.get(
                "decision_style", "act according to your class"
            )
            prompt_parts.append(
                f"\nAs a {self.profile.character_class.value}, you typically: {decision_style}"
            )

        prompt_parts.append(
            "\nWhen responding, stay in character and consider your personality, "
            "motivations, and class nature."
        )

        return "\n".join(prompt_parts)

    def suggest_reaction_ai(
        self, situation: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        AI-enhanced character reaction suggestion.
        Falls back to rule-based suggestion if AI not available.

        Args:
            situation: Description of the situation
            context: Optional context information

        Returns:
            Dictionary with reaction suggestions, including AI-generated content if available
        """
        # Get rule-based suggestion first
        base_suggestion = self.suggest_reaction(situation, context)

        # Try AI enhancement
        ai_client = self._get_ai_client()
        if not ai_client:
            base_suggestion["ai_enhanced"] = False
            return base_suggestion

        try:
            # Build prompt for AI
            system_prompt = self._build_character_system_prompt()

            # Custom system prompt from character config
            if self.profile.ai_config and isinstance(self.profile.ai_config, dict):
                custom_prompt = self.profile.ai_config.get("system_prompt")
                if custom_prompt:
                    system_prompt = custom_prompt
            elif self.profile.ai_config and hasattr(
                self.profile.ai_config, "system_prompt"
            ):
                if self.profile.ai_config.system_prompt:
                    system_prompt = self.profile.ai_config.system_prompt

            # Create context string
            context_str = ""
            if context:
                context_str = "\n\nAdditional context:\n" + "\n".join(
                    [f"- {k}: {v}" for k, v in context.items()]
                )

            user_prompt = f"""Given this situation: {situation}{context_str}

How would you react? Consider:
1. Your immediate emotional/instinctive response
2. What you would say or do
3. How this aligns with your goals and personality
4. Any class abilities or knowledge you might use

Provide a natural, in-character response."""

            messages = [
                ai_client.create_system_message(system_prompt),
                ai_client.create_user_message(user_prompt),
            ]

            ai_response = ai_client.chat_completion(messages)

            # Add AI response to base suggestion
            base_suggestion["ai_response"] = ai_response
            base_suggestion["ai_enhanced"] = True

        except (
            ImportError,
            AttributeError,
            KeyError,
            ValueError,
            ConnectionError,
            TimeoutError,
        ) as e:
            # AI failed, fall back to rule-based
            base_suggestion["ai_error"] = str(e)
            base_suggestion["ai_enhanced"] = False

        return base_suggestion

    def suggest_dc_for_action_ai(
        self, action: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        AI-enhanced DC suggestion that considers character abilities and situation.
        Falls back to rule-based suggestion if AI not available.
        """
        # Get rule-based suggestion first
        base_suggestion = self.suggest_dc_for_action(action, context)

        ai_client = self._get_ai_client()
        if not ai_client:
            base_suggestion["ai_enhanced"] = False
            return base_suggestion

        try:
            # Build a prompt for DC suggestion
            key_features = ", ".join(self.class_knowledge.get("key_features", []))
            system_prompt = f"""You are a D&D 5e Dungeon Master helping determine"
            " appropriate DCs for character actions.

Character: {self.profile.name} ({self.profile.character_class.value} Level {self.profile.level})
Class abilities: {key_features}"""

            if self.profile.background_story:
                system_prompt += f"\nBackground: {self.profile.background_story[:300]}"

            user_prompt = f"""The character wants to: {action}

Consider:
1. Standard DC guidelines (5=very easy, 10=easy, 15=medium, 20=hard, 25=very hard, 30=nearly impossible)
2. Character's class abilities and level
3. Situational modifiers

Suggest an appropriate DC (5-30) and explain why. Also suggest if the ""
""character has any advantages for this action."""

            messages = [
                ai_client.create_system_message(system_prompt),
                ai_client.create_user_message(user_prompt),
            ]

            ai_response = ai_client.chat_completion(messages)

            base_suggestion["ai_analysis"] = ai_response
            base_suggestion["ai_enhanced"] = True

        except (
            ImportError,
            AttributeError,
            KeyError,
            ValueError,
            ConnectionError,
            TimeoutError,
        ) as e:
            base_suggestion["ai_error"] = str(e)
            base_suggestion["ai_enhanced"] = False

        return base_suggestion

    # Story analysis and character development methods

    def get_major_plot_actions(self) -> List[Any]:
        """Return the character's major plot actions."""
        # Try to access from profile's stored data
        return getattr(self.profile, "major_plot_actions", [])

    def get_relationships(self) -> Dict[str, str]:
        """Return the character's relationships with other characters and NPCs."""
        return self.profile.relationships

    def suggest_relationship_update(
        self, other_character: str, interaction_context: str
    ) -> Optional[str]:
        """Suggest updating relationships based on story interactions."""
        current_relationships = self.get_relationships()

        # If no existing relationship, suggest creating one
        if other_character not in current_relationships:
            suggestions = {
                "positive_interaction": (
                    f"Appreciates {other_character}'s help in {interaction_context}"
                ),
                "conflict": (
                    f"Has tensions with {other_character} over {interaction_context}"
                ),
                "neutral": (
                    f"Working relationship with {other_character} "
                    f"after {interaction_context}"
                ),
                "suspicious": (
                    f"Remains cautious about {other_character} "
                    f"following {interaction_context}"
                ),
            }

            # Suggest based on character class tendencies
            class_name = self.profile.character_class.value.lower()

            if class_name in ["paladin", "cleric"]:
                return (
                    f"SUGGESTION: Add relationship - '{other_character}': "
                    f"'{suggestions['positive_interaction']}'"
                )
            if class_name in ["rogue", "warlock"]:
                return (
                    f"SUGGESTION: Add relationship - '{other_character}': "
                    f"'{suggestions['suspicious']}'"
                )
            return (
                f"SUGGESTION: Add relationship - '{other_character}': "
                f"'{suggestions['neutral']}'"
            )

        # If existing relationship, suggest updating it
        current = current_relationships[other_character]
        return (
            f"SUGGESTION: Update relationship with {other_character} - "
            f"Current: '{current}' - Consider how {interaction_context} affects this"
        )

    def suggest_plot_action_logging(
        self, action: str, reasoning: str, chapter: str
    ) -> str:
        """Suggest adding an action to major_plot_actions."""
        return f"""SUGGESTION: Log this action to major_plot_actions:
{{
  "chapter": "{chapter}",
  "action": "{action}",
  "reasoning": "{reasoning}"
}}"""

    def suggest_character_development(
        self, new_behavior: str, context: str
    ) -> List[str]:
        """Suggest character file updates based on new behaviors."""
        suggestions = []

        # Check if this behavior suggests new personality traits
        if any(
            word in new_behavior.lower() for word in ["brave", "courageous", "bold"]
        ):
            suggestions.append(
                f"SUGGESTION: Consider adding personality trait: "
                f"'Shows courage in {context}'"
            )

        if any(
            word in new_behavior.lower() for word in ["cautious", "careful", "wary"]
        ):
            suggestions.append(
                f"SUGGESTION: Consider adding personality trait: "
                f"'Exercises caution when {context}'"
            )

        if any(word in new_behavior.lower() for word in ["lead", "command", "direct"]):
            suggestions.append(
                f"SUGGESTION: Consider adding personality trait: "
                f"'Takes leadership during {context}'"
            )

        # Check if this suggests new fears or motivations
        if any(
            word in new_behavior.lower() for word in ["afraid", "fear", "terrified"]
        ):
            suggestions.append(
                f"SUGGESTION: Consider adding to fears_weaknesses: "
                f"'Fear related to {context}'"
            )

        if any(word in new_behavior.lower() for word in ["protect", "save", "help"]):
            suggestions.append(
                f"SUGGESTION: Consider updating motivations to include "
                f"protecting others in {context}"
            )

        return suggestions

    def analyze_story_content(
        self, story_text: str, chapter_name: str
    ) -> Dict[str, List[str]]:
        """Analyze story content and provide comprehensive suggestions."""
        suggestions = {
            "relationships": [],
            "plot_actions": [],
            "character_development": [],
            "npc_creation": [],
        }

        lines = story_text.split("\n")

        for line in lines:
            # Look for CHARACTER: ACTION: REASONING: patterns
            if line.strip().startswith("CHARACTER:") and self.profile.name in line:
                # Extract action and reasoning from subsequent lines
                try:
                    idx = lines.index(line)
                    next_lines = lines[idx + 1 : idx + 4]
                    action_line = next(
                        (l for l in next_lines if l.strip().startswith("ACTION:")), ""
                    )
                    reasoning_line = next(
                        (l for l in next_lines if l.strip().startswith("REASONING:")),
                        "",
                    )

                    if action_line and reasoning_line:
                        action = action_line.replace("ACTION:", "").strip()
                        reasoning = reasoning_line.replace("REASONING:", "").strip()

                        # Suggest logging this action
                        suggestions["plot_actions"].append(
                            self.suggest_plot_action_logging(
                                action, reasoning, chapter_name
                            )
                        )

                        # Suggest character development updates
                        suggestions["character_development"].extend(
                            self.suggest_character_development(action, chapter_name)
                        )
                except (AttributeError, KeyError, ValueError):
                    pass

            # Look for mentions of other characters or potential NPCs
            if self.profile.name in line:
                # Find potential character interactions
                other_names = self._extract_character_names(line)
                for other_name in other_names:
                    if other_name != self.profile.name:
                        relationship_suggestion = self.suggest_relationship_update(
                            other_name, chapter_name
                        )
                        if relationship_suggestion:
                            suggestions["relationships"].append(relationship_suggestion)

        return suggestions

    def _extract_character_names(self, text: str) -> List[str]:
        """Extract potential character/NPC names from text (simple implementation)."""
        # This is a basic implementation - could be enhanced with NLP
        words = text.split()
        potential_names = []

        for word in words:
            # Look for capitalized words that might be names
            if word.strip(",.:;!?").istitle() and len(word) > 2:
                potential_names.append(word.strip(",.:;!?"))

        return potential_names

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive character status including all JSON fields."""
        return {
            "name": self.profile.name,
            "species": getattr(self.profile, "species", "Human"),
            "lineage": getattr(self.profile, "lineage", None),
            "dnd_class": self.profile.character_class.value,
            "subclass": getattr(self.profile, "subclass", None),
            "level": self.profile.level,
            "ability_scores": getattr(self.profile, "ability_scores", {}),
            "skills": getattr(self.profile, "skills", {}),
            "max_hit_points": getattr(self.profile, "max_hit_points", 0),
            "armor_class": getattr(self.profile, "armor_class", 10),
            "movement_speed": getattr(self.profile, "movement_speed", 30),
            "proficiency_bonus": getattr(self.profile, "proficiency_bonus", 2),
            "equipment": getattr(self.profile, "equipment", {}),
            "spell_slots": getattr(self.profile, "spell_slots", {}),
            "known_spells": getattr(self.profile, "known_spells", []),
            "background": getattr(self.profile, "background", ""),
            "personality_traits": (
                self.profile.personality_summary.split("; ")
                if self.profile.personality_summary
                else []
            ),
            "ideals": self.profile.goals,
            "bonds": self.profile.motivations,
            "flaws": self.profile.fears_weaknesses,
            "backstory": self.profile.background_story,
            "feats": getattr(self.profile, "feats", []),
            "magic_items": getattr(self.profile, "magic_items", []),
            "class_abilities": getattr(self.profile, "class_abilities", []),
            "specialized_abilities": getattr(self.profile, "specialized_abilities", []),
            "major_plot_actions": getattr(self.profile, "major_plot_actions", []),
            "relationships": self.profile.relationships,
            "ai_config": self.profile.ai_config,
        }

    @classmethod
    def load_from_file(cls, filepath: str):
        """Load character consultant from JSON file."""
        data = load_json_file(filepath)

        # Create a CharacterProfile from the JSON data
        # The JSON files use 'dnd_class' but CharacterProfile expects 'character_class'
        character_class_name = data.get("dnd_class", "Fighter")
        try:
            character_class = DnDClass(character_class_name)
        except ValueError:
            # If the class name doesn't match enum, default to Fighter
            character_class = DnDClass.FIGHTER

        profile = CharacterProfile(
            name=data.get("name", "Unknown"),
            character_class=character_class,
            level=data.get("level", 1),
            background_story=data.get("backstory", ""),
            personality_summary="; ".join(data.get("personality_traits", [])),
            motivations=data.get("bonds", []),
            fears_weaknesses=data.get("flaws", []),
            relationships=data.get("relationships", {}),
            goals=[],  # Not in standard JSON
            secrets=[],  # Not in standard JSON
        )

        return cls(profile)
