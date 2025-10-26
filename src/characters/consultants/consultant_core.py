"""
Character Consultant Core - Main consultation system using composition

Coordinates multiple specialized components (DC calculation, story analysis, AI integration)
to provide comprehensive character consultation services.
"""

from typing import Dict, List, Any, Optional

from src.characters.consultants.character_profile import CharacterProfile
from src.characters.consultants.class_knowledge import get_class_knowledge
from src.characters.consultants.consultant_dc import DCCalculator
from src.characters.consultants.consultant_story import StoryAnalyzer
from src.characters.consultants.consultant_ai import AIConsultant

# Optional imports
try:
    from src.ai.rag_system import get_rag_system
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    get_rag_system = None


class CharacterConsultant:
    """
    Main character consultant coordinating specialized components.

    Uses composition to delegate responsibilities:
    - DCCalculator: DC calculations and alternatives
    - StoryAnalyzer: Story consistency and character development
    - AIConsultant: AI-enhanced suggestions (optional)
    """

    def __init__(self, profile: CharacterProfile, ai_client=None):
        """
        Initialize character consultant with profile and optional AI client.

        Args:
            profile: Character profile with personality, background, etc.
            ai_client: Optional global AI client (can be overridden by character config)
        """
        self.profile = profile
        self.class_knowledge = get_class_knowledge(profile.character_class.value)

        # Initialize specialized components using composition
        self.dc_calculator = DCCalculator(profile, self.class_knowledge)
        self.story_analyzer = StoryAnalyzer(profile, self.class_knowledge)
        self.ai_consultant = AIConsultant(profile, self.class_knowledge, ai_client)

    # ============================================================================
    # Core reaction and consultation methods
    # ============================================================================

    def suggest_reaction(
        self, situation: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Suggest how this character would react to a situation.

        Args:
            situation: Description of the situation
            context: Optional context information

        Returns:
            Dictionary with reaction suggestions
        """
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
        personality_modifier = self.get_personality_modifier(situation_type)

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
            "suggested_approach": self.synthesize_approach(situation, situation_type),
            "dialogue_suggestion": self.suggest_dialogue(situation, situation_type),
            "consistency_notes": self.check_consistency_factors(situation),
        }

    def get_personality_modifier(self, situation_type: str) -> str:
        """
        Get personality-based modification to class reaction.

        Args:
            situation_type: Type of situation (threat, social, puzzle, magic)

        Returns:
            Personality-based modifier string
        """
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
            f"Given their {self.profile.personality_summary} nature, "
            f"{self.profile.name} would",
        )

    def synthesize_approach(self, _situation: str, _situation_type: str) -> str:
        """
        Synthesize overall approach recommendation.

        Args:
            _situation: Situation description (reserved for future use)
            _situation_type: Type of situation (reserved for future use)

        Returns:
            Approach recommendation string
        """
        class_style = self.class_knowledge.get("decision_style", "methodically")

        if self.profile.goals:
            goal_influence = f"considering their goal: {self.profile.goals[0]}"
        else:
            goal_influence = "staying true to their character"

        return (
            f"{self.profile.name} would likely approach this {class_style}, "
            f"{goal_influence}."
        )

    def suggest_dialogue(self, _situation: str, _situation_type: str) -> str:
        """
        Suggest what the character might say.

        Args:
            _situation: Situation description (reserved for future use)
            _situation_type: Type of situation (reserved for future use)

        Returns:
            Dialogue suggestion string
        """
        # Use behavior.speech_patterns (nested dataclass). Fall back to class style.
        speech_patterns = []
        if getattr(self.profile, "behavior", None):
            speech_patterns = getattr(self.profile.behavior, "speech_patterns", []) or []

        if speech_patterns:
            speech_note = f"Speaking in their typical {speech_patterns[0]} manner"
        else:
            speech_note = f"Speaking as a {self.profile.character_class.value} would"

        return (
            f"{speech_note}, {self.profile.name} might say something that reflects "
            f"their class nature and personal motivations."
        )

    def check_consistency_factors(self, situation: str) -> List[str]:
        """
        Identify factors that should be considered for character consistency.

        Args:
            situation: Situation description

        Returns:
            List of consistency factors to consider
        """
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

    # ============================================================================
    # Item management methods
    # ============================================================================

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

    # ============================================================================
    # Character data access methods
    # ============================================================================

    def get_major_plot_actions(self) -> List[Any]:
        """
        Return the character's major plot actions.

        Returns:
            List of major plot actions
        """
        return getattr(self.profile, "major_plot_actions", [])

    def get_relationships(self) -> Dict[str, str]:
        """
        Return the character's relationships with other characters and NPCs.

        Returns:
            Dictionary of relationships
        """
        return self.profile.relationships

    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive character status including all JSON fields.

        Returns:
            Dictionary with complete character status
        """
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

    # ============================================================================
    # Delegation to specialized components
    # ============================================================================

    def suggest_dc_for_action(
        self, action_description: str, character_abilities: Dict[str, int] = None
    ) -> Dict[str, Any]:
        """
        Delegate DC calculation to DCCalculator component.

        Args:
            action_description: Description of the action
            character_abilities: Optional ability scores dict

        Returns:
            DC suggestion from DCCalculator
        """
        return self.dc_calculator.suggest_dc_for_action(
            action_description, character_abilities
        )

    def analyze_story_consistency(
        self, story_text: str, character_actions: List[str]
    ) -> Dict[str, Any]:
        """
        Delegate story consistency analysis to StoryAnalyzer component.

        Args:
            story_text: Full story text
            character_actions: List of character actions

        Returns:
            Consistency analysis from StoryAnalyzer
        """
        return self.story_analyzer.analyze_story_consistency(
            story_text, character_actions
        )

    def suggest_relationship_update(
        self, other_character: str, interaction_context: str
    ) -> Optional[str]:
        """
        Delegate relationship suggestion to StoryAnalyzer component.

        Args:
            other_character: Name of other character
            interaction_context: Context of interaction

        Returns:
            Relationship suggestion from StoryAnalyzer
        """
        return self.story_analyzer.suggest_relationship_update(
            other_character, interaction_context
        )

    def suggest_plot_action_logging(
        self, action: str, reasoning: str, chapter: str
    ) -> str:
        """
        Delegate plot action logging suggestion to StoryAnalyzer component.

        Args:
            action: Action taken
            reasoning: Reasoning for action
            chapter: Chapter name

        Returns:
            Plot action suggestion from StoryAnalyzer
        """
        return self.story_analyzer.suggest_plot_action_logging(
            action, reasoning, chapter
        )

    def suggest_character_development(
        self, new_behavior: str, context: str
    ) -> List[str]:
        """
        Delegate character development suggestions to StoryAnalyzer component.

        Args:
            new_behavior: New behavior exhibited
            context: Context of behavior

        Returns:
            Development suggestions from StoryAnalyzer
        """
        return self.story_analyzer.suggest_character_development(new_behavior, context)

    def analyze_story_content(
        self, story_text: str, chapter_name: str
    ) -> Dict[str, List[str]]:
        """
        Delegate comprehensive story analysis to StoryAnalyzer component.

        Args:
            story_text: Full story text
            chapter_name: Chapter name

        Returns:
            Comprehensive suggestions from StoryAnalyzer
        """
        return self.story_analyzer.analyze_story_content(story_text, chapter_name)

    def suggest_reaction_ai(
        self, situation: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Get AI-enhanced reaction suggestion from AIConsultant component.

        Args:
            situation: Situation description
            context: Optional context

        Returns:
            AI-enhanced suggestion from AIConsultant
        """
        # Get rule-based suggestion first
        base_suggestion = self.suggest_reaction(situation, context)
        # Enhance with AI
        return self.ai_consultant.suggest_reaction_ai(
            situation, context, base_suggestion
        )

    def suggest_dc_for_action_ai(
        self, action: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Get AI-enhanced DC suggestion from AIConsultant component.

        Args:
            action: Action description
            context: Optional context

        Returns:
            AI-enhanced DC suggestion from AIConsultant
        """
        # Get rule-based suggestion first
        base_suggestion = self.suggest_dc_for_action(action, context)
        # Enhance with AI
        return self.ai_consultant.suggest_dc_for_action_ai(
            action, context, base_suggestion
        )

    # ============================================================================
    # Class methods for loading
    # ============================================================================

    @classmethod
    def load_from_file(cls, filepath: str, ai_client=None):
        """
        Load character consultant from JSON file.

        Args:
            filepath: Path to character JSON file
            ai_client: Optional AI client

        Returns:
            CharacterConsultant instance
        """
        # Load profile using CharacterProfile's loader
        profile = CharacterProfile.load_from_file(filepath)
        # Create consultant with loaded profile
        return cls(profile, ai_client)
