"""
Combat to Story Converter - Transforms combat descriptions into narrative text.

Converts natural language combat prompts into engaging narrative prose with:
- RAG integration for D&D spell/ability lookup (dnd5e.wikidot.com)
- Automatic spell description enrichment
- Character-aware combat narration
- Multiple narrative styles (cinematic, gritty, heroic, tactical)
"""

from typing import Dict, List
from src.characters.consultants.consultant_core import CharacterConsultant
from src.combat.narrator_ai import AIEnhancedNarrator
from src.combat.narrator_descriptions import CombatDescriptor
from src.combat.narrator_consistency import ConsistencyChecker


class CombatNarrator:
    """Converts combat descriptions into narrative story format."""

    def __init__(
        self, character_consultants: Dict[str, CharacterConsultant], ai_client=None
    ):
        """
        Initialize combat narrator with specialized components.

        Args:
            character_consultants: Dictionary of character consultants
            ai_client: Optional AI client for enhanced narration
        """
        self.consultants = character_consultants
        self.ai_client = ai_client

        # Initialize components using composition
        self.ai_narrator = AIEnhancedNarrator(character_consultants, ai_client)
        self.descriptor = CombatDescriptor(character_consultants)
        self.consistency_checker = ConsistencyChecker(character_consultants)

    def narrate_combat_from_prompt(
        self, combat_prompt: str, story_context: str = "", style: str = "cinematic"
    ) -> str:
        """
        Convert a natural language combat prompt into narrative prose.

        Args:
            combat_prompt: Tactical description of combat
            story_context: Optional story so far for context
            style: Narrative style (cinematic, gritty, heroic, tactical)

        Returns:
            Narrative prose describing the combat scene
        """
        return self.ai_narrator.narrate_combat_from_prompt(
            combat_prompt, story_context, style
        )

    def generate_combat_title(
        self, combat_prompt: str, story_context: str = ""
    ) -> str:
        """
        Generate a situational combat title based on combat description.

        Args:
            combat_prompt: The tactical combat description
            story_context: Optional story context for better title generation

        Returns:
            A descriptive combat title
        """
        return self.ai_narrator.generate_combat_title(combat_prompt, story_context)

    def enhance_with_character_consistency(
        self, narrative: str, character_actions: Dict[str, List[str]]
    ) -> str:
        """
        Enhance narrative with character consistency notes.

        Args:
            narrative: Combat narrative text
            character_actions: Dictionary mapping character names to their actions

        Returns:
            Enhanced narrative with consistency notes
        """
        return self.consistency_checker.enhance_with_character_consistency(
            narrative, character_actions
        )
