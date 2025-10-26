"""
AI-Enhanced Combat Narration Component.

Handles AI-powered conversion of tactical combat descriptions into narrative prose,
including character context building, spell/ability lookup via RAG, and text
post-processing.
"""

import re
from typing import Dict
from src.characters.consultants.consultant_core import CharacterConsultant
from src.utils.text_formatting_utils import wrap_narrative_text

# Import RAG system for D&D rules lookup
try:
    from src.ai.rag_system import RAGSystem

    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


class AIEnhancedNarrator:
    """Handles AI-enhanced combat narration with RAG integration."""

    def __init__(
        self, character_consultants: Dict[str, CharacterConsultant], ai_client=None
    ):
        self.consultants = character_consultants
        self.ai_client = ai_client

        # Initialize D&D rules RAG system
        self.dnd_rag = None
        if RAG_AVAILABLE:
            try:
                self.dnd_rag = RAGSystem()

            except (ImportError, AttributeError, KeyError, OSError) as e:
                print(f"WARNING: Could not initialize D&D rules RAG: {e}")

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
        if not self.ai_client:
            return self._narrate_combat_fallback(combat_prompt, style)

        # Build character context
        character_context = self._build_character_context(combat_prompt)

        # Look up D&D spells/abilities for accurate descriptions
        ability_context = self._lookup_spells_and_abilities(combat_prompt)

        # Create AI prompt
        system_prompt = self._create_system_prompt(style)
        user_prompt = self._create_user_prompt(
            {
                "combat_prompt": combat_prompt,
                "character_context": character_context,
                "ability_context": ability_context,
                "story_context": story_context,
                "style": style,
            }
        )

        try:
            narrative = self.ai_client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.8,  # Higher temperature for creative combat descriptions
            )

            # Post-process to ensure no mechanics leaked through
            narrative = self._remove_mechanics_terms(narrative)

            # Wrap text to 80 characters for readability
            narrative = wrap_narrative_text(narrative)

            return narrative

        except (ConnectionError, TimeoutError, ValueError, KeyError, AttributeError) as e:
            print(f"[WARNING]  AI narration failed: {e}")
            return self._narrate_combat_fallback(combat_prompt, style)

    def generate_combat_title(
        self, combat_prompt: str, story_context: str = ""
    ) -> str:
        """
        Generate a situational combat title based on combat description and story context.

        Args:
            combat_prompt: The tactical combat description
            story_context: Optional story context for better title generation

        Returns:
            A descriptive combat title
        """
        if not self.ai_client:
            return self._extract_creature_title(combat_prompt)

        try:
            # Use AI to generate a contextual title
            context_part = (
                "Recent story context: " + story_context[-500:]
                if story_context
                else ""
            )
            prompt = (
                f"Based on this combat description, generate a SHORT, "
                f"situational combat title (3-5 words maximum).\n\n"
                f"Combat: {combat_prompt}\n\n{context_part}\n\n"
                f"Generate ONLY the title, nothing else. "
                f"Make it dramatic and specific to the situation.\n"
                f'Examples: "The Goblin Ambush", "Showdown at the Bridge", '
                f'"Dragon\'s Fury", "Battle in the Tavern"\n\nTitle:'
            )

            title = self.ai_client.chat_completion(
                messages=[{"role": "user", "content": prompt}], temperature=0.7
            ).strip()

            # Clean up the title
            title = title.strip("\"'.")

            # Validate title length (should be short)
            if len(title.split()) > 6:
                return self._extract_creature_title(combat_prompt)

            return title

        except (ConnectionError, TimeoutError, ValueError, KeyError, AttributeError) as e:
            print(f"[WARNING]  Title generation failed: {e}")
            return self._extract_creature_title(combat_prompt)

    def _create_system_prompt(self, style: str) -> str:
        """Create the system prompt for AI narration."""
        return f"""You are an expert D&D combat narrator. Convert \
tactical combat descriptions into engaging narrative prose.

CRITICAL RULES:
1. NEVER mention dice rolls, DCs, or game mechanics (no "rolls", "saves", \
"AC", numbers)
2. EVERY action MUST be included - do not omit or summarize any action
3. Critical hits should be described with exceptional detail and dramatic flair
4. Maintain character personalities and fighting styles
5. Write in {style} style with vivid sensory details
6. Use present tense for immediacy
7. Keep tactical order but make it flow naturally
8. For spells with verbal components, create fitting dialogue/incantations \
based on the spell's actual effect
9. Use the D&D rules context to make spell effects accurate and flavorful

Style Guidelines:
- Cinematic: Movie-like action, dramatic descriptions, epic moments
- Gritty: Realistic, visceral, emphasize the danger and pain
- Heroic: Emphasize bravery, valor, and heroic deeds
- Tactical: Clear action-by-action while maintaining narrative flow"""

    def _create_user_prompt(self, context: Dict[str, str]) -> str:
        """Create the user prompt for AI narration."""
        combat_prompt = context["combat_prompt"]
        character_context = context["character_context"]
        ability_context = context["ability_context"]
        story_context = context["story_context"]
        style = context["style"]

        story_part = (
            f'Story context (for continuity):\n{story_context[:500]}...'
            if story_context
            else ''
        )

        return f"""Convert this tactical combat description into narrative prose:

{combat_prompt}

{character_context}
{ability_context}
{story_part}

Write the combat narrative in {style} style. Remember:
- NO dice rolls or game mechanics
- Include EVERY action mentioned
- Make critical hits dramatically impressive
- Create dialogue for spell incantations that fits the spell's actual effect
- Use the D&D rules context to enhance accuracy
- Make it flow like a story, not a combat log"""

    def _build_character_context(self, combat_prompt: str) -> str:
        """Build context about characters mentioned in the combat."""
        context_parts = []

        # Find character names (capitalized words at sentence start or after commas)
        potential_names = re.findall(
            r"(?:^|[.!?]\s+|,\s+)([A-Z][a-z]+)", combat_prompt
        )

        for name in set(potential_names):
            if name in self.consultants:
                consultant = self.consultants[name]
                profile = consultant.profile

                char_info = f"\n**{name}** ({profile.character_class.value}):"
                char_info += f"\n- Fighting Style: {self._get_fighting_style(profile)}"
                personality = (
                    profile.personality_summary[:100]
                    if profile.personality_summary
                    else 'Brave adventurer'
                )
                char_info += f"\n- Personality: {personality}"

                context_parts.append(char_info)

        if context_parts:
            return "\nCharacter Information (for authentic portrayal):" + "".join(
                context_parts
            )
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
            r"\b(vicious mockery)\b",
            r"\b(eldritch blast)\b",
            r"\b(fireball)\b",
            r"\b(healing word)\b",
            r"\b(cure wounds)\b",
            r"\b(sacred flame)\b",
            r"\b(thunderwave)\b",
            r"\b(magic missile)\b",
            r"\b(shield)\b",
            r"\b(mage armor)\b",
            r"\b(wild shape)\b",
            r"\b(sneak attack)\b",
            r"\b(divine smite)\b",
            r"\b(lay on hands)\b",
            r"\b(bardic inspiration)\b",
            r"\b(rage)\b",
            r"\b(action surge)\b",
            r"\b(second wind)\b",
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
                page_name = ability.lower().replace(" ", "-")

                # Try different page formats
                possible_pages = [
                    f"spell:{page_name}",
                    f"feat:{page_name}",
                    f"class:{page_name}",
                ]

                for page in possible_pages:
                    result = self.dnd_rag.search_rules_wiki(page, max_results=1)
                    if result:
                        ability_descriptions.append(
                            f"\n**{ability.title()}**: {result[0]['content'][:300]}..."
                        )
                        break
            except (AttributeError, KeyError, IndexError, TypeError):
                # Silently skip failed lookups
                pass

        if ability_descriptions:
            return "\n\nD&D Rules Context (for accurate portrayal):" + "".join(
                ability_descriptions
            )
        return ""

    def _get_fighting_style(self, profile) -> str:
        """Determine character's fighting style from their class."""
        class_name = profile.character_class.value

        fighting_styles = {
            "Barbarian": "Reckless and powerful melee combat",
            "Bard": "Support magic and witty verbal jabs",
            "Cleric": "Divine magic and healing with martial backup",
            "Druid": "Wild Shape transformations and nature magic",
            "Fighter": "Skilled weapon combat with tactical precision",
            "Monk": "Swift unarmed strikes and martial arts",
            "Paladin": "Divine smites and righteous combat",
            "Ranger": "Ranged attacks and tactical positioning",
            "Rogue": "Sneaky attacks and precise strikes",
            "Sorcerer": "Raw magical power and spell bombardment",
            "Warlock": "Eldritch blasts and pact magic",
            "Wizard": "Strategic spellcasting and control magic",
        }

        return fighting_styles.get(class_name, "Versatile combat approach")

    def _remove_mechanics_terms(self, narrative: str) -> str:
        """Remove any game mechanics terms that might have slipped through."""
        # List of mechanics terms to remove or replace
        mechanics_patterns = [
            (r"\b(rolls?|rolled)\s+(\d+)", "attempts"),
            (r"\b(saves?|saved|saving throw)\b", "resists"),
            (r"\bAC\s+\d+\b", ""),
            (r"\bDC\s+\d+\b", ""),
            (r"\bd20\b", ""),
            (r"\bnat(ural)?\s*20\b", ""),
            (r"\bcritical\s+hit\b", "devastating strike"),
            (r"\b(\d+)\s+damage\b", "a powerful blow"),
            (r"\binitiative\b", "readiness"),
            (r"\b(hits?|hit roll)\b", "strikes"),
        ]

        cleaned = narrative
        for pattern, replacement in mechanics_patterns:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

        return cleaned

    def _narrate_combat_fallback(self, combat_prompt: str, _style: str) -> str:
        """Fallback narrative generation when AI is not available."""
        # Simple formatting without AI
        lines = combat_prompt.split(".")
        narrative_lines = []

        for line in lines:
            line = line.strip()
            if line:
                # Capitalize first letter
                line = (
                    line[0].upper() + line[1:] if len(line) > 1 else line.upper()
                )
                # Remove obvious mechanics terms
                line = self._remove_mechanics_terms(line)
                narrative_lines.append(line)

        narrative = ". ".join(narrative_lines) + "."

        return (
            f"**Combat Scene:**\n\n{narrative}\n\n"
            "*(Note: AI enhancement unavailable. "
            "Install AI client for richer combat narratives.)*"
        )

    def _extract_creature_title(self, combat_prompt: str) -> str:
        """
        Extract a simple creature-based title from combat prompt.

        Args:
            combat_prompt: The tactical combat description

        Returns:
            A creature-based title or generic "Combat Encounter"
        """
        creatures = re.findall(
            r"\b(goblin|orc|dragon|skeleton|zombie|bandit|wolf|bear|"
            r"cultist|spider|troll)s?\b",
            combat_prompt.lower(),
        )
        if creatures:
            creature = creatures[0].capitalize()
            return f"The {creature} Encounter"
        return "Combat Encounter"
