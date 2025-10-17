"""
Dungeon Master Consultant - Provides narrative suggestions based on user prompts.
Integrates with character and NPC agents for coherent storytelling.
Enhanced with RAG (Retrieval-Augmented Generation) for campaign wiki integration.
"""

import re
from typing import Dict, List, Any
from pathlib import Path
from character_consultants import CharacterConsultant, CharacterProfile
from npc_agents import NPCAgent, create_npc_agents

# Import AI client if available (used for type hints and availability check)
try:
    from ai_client import AIClient  # pylint: disable=unused-import
    AI_AVAILABLE = True
except ImportError:
    AIClient = None
    AI_AVAILABLE = False

# Import RAG system if available
try:
    from rag_system import get_rag_system

    RAG_AVAILABLE = True
except ImportError:
    get_rag_system = None
    RAG_AVAILABLE = False


class DMConsultant:
    """AI consultant that provides DM narrative suggestions based on user prompts."""

    def __init__(self, workspace_path: str = None, ai_client=None):
        self.workspace_path = Path(workspace_path) if workspace_path else Path.cwd()
        self.ai_client = ai_client
        self.character_consultants = self._load_character_consultants()
        self.npc_agents = self._load_npc_agents()
        self.narrative_style = "immersive"  # immersive, cinematic, descriptive

        # Initialize RAG system for wiki integration
        self.rag_system = get_rag_system() if RAG_AVAILABLE else None

    def _load_character_consultants(self) -> Dict[str, CharacterConsultant]:
        """Load all character consultants from the game_data/characters folder."""
        consultants = {}
        characters_dir = self.workspace_path / "game_data" / "characters"
        if characters_dir.exists():
            for char_file in characters_dir.glob("*.json"):
                # Skip template and example files
                if (
                    not char_file.name.startswith("class.example")
                    and not char_file.name.endswith(".example.json")
                    and not char_file.name.startswith("template")
                ):
                    profile = CharacterProfile.load_from_file(str(char_file))
                    consultant = CharacterConsultant(profile, ai_client=self.ai_client)
                    consultants[profile.name] = consultant
        return consultants

    def _load_npc_agents(self) -> Dict[str, NPCAgent]:
        """Load all NPC agents from the game_data/npcs folder."""
        agents = {}
        npcs_dir = self.workspace_path / "game_data" / "npcs"
        if npcs_dir.exists():
            npc_agent_list = create_npc_agents(npcs_dir, ai_client=self.ai_client)
            for agent in npc_agent_list:
                agents[agent.profile.name] = agent
        return agents

    def suggest_narrative(
        self,
        user_prompt: str,
        characters_present: List[str] = None,
        npcs_present: List[str] = None,
    ) -> Dict[str, Any]:
        """Generate narrative suggestions based on user prompt and present characters/NPCs."""
        characters_present = characters_present or []
        npcs_present = npcs_present or []

        # Get character insights for present characters
        character_insights = {}
        for char_name in characters_present:
            if char_name in self.character_consultants:
                consultant = self.character_consultants[char_name]
                reaction = consultant.suggest_reaction(user_prompt, {})
                character_insights[char_name] = {
                    "likely_reaction": reaction["suggested_reaction"],
                    "reasoning": reaction["reasoning"],
                    "class_expertise": reaction.get("class_expertise", ""),
                }

        # Get NPC insights for present NPCs
        npc_insights = {}
        for npc_name in npcs_present:
            if npc_name in self.npc_agents:
                agent = self.npc_agents[npc_name]
                npc_insights[npc_name] = {
                    "personality": agent.profile.personality,
                    "role": agent.profile.role,
                    "relationships": agent.profile.relationships,
                    "likely_behavior": self._suggest_npc_behavior(
                        agent.profile, user_prompt
                    ),
                }

        # Generate narrative suggestions
        narrative_suggestions = self._generate_narrative_suggestions(
            user_prompt, character_insights, npc_insights
        )

        return {
            "user_prompt": user_prompt,
            "character_insights": character_insights,
            "npc_insights": npc_insights,
            "narrative_suggestions": narrative_suggestions,
            "consistency_notes": self._check_consistency(
                characters_present, npcs_present, user_prompt
            ),
        }

    def _suggest_npc_behavior(self, npc_profile, _situation: str) -> str:
        """Suggest how an NPC would behave in the given situation."""
        personality = npc_profile.personality.lower()

        if "friendly" in personality:
            return "Would likely be helpful and accommodating"
        if "hostile" in personality or "aggressive" in personality:
            return "Would likely be confrontational or suspicious"
        if "mysterious" in personality:
            return "Would speak in riddles or reveal information cryptically"
        if "merchant" in npc_profile.role.lower():
            return "Would try to turn the situation into a business opportunity"
        return "Would react cautiously but politely"

    def _generate_narrative_suggestions(
        self, prompt: str, char_insights: Dict, npc_insights: Dict
    ) -> List[str]:
        """Generate multiple narrative direction suggestions."""
        suggestions = []

        # Base narrative suggestion
        suggestions.append(
            f"Setting the scene: {self._create_scene_description(prompt)}"
        )

        # Character-driven suggestions
        if char_insights:
            char_names = list(char_insights.keys())
            suggestions.append(
                f"Character focus: Highlight {char_names[0]}'s expertise in this situation"
            )

        # NPC-driven suggestions
        if npc_insights:
            npc_names = list(npc_insights.keys())
            suggestions.append(
                f"NPC interaction: {npc_names[0]} could provide crucial "
                "information or complications"
            )

        # Tension/conflict suggestions
        suggestions.append("Add tension: Introduce a time constraint or moral dilemma")
        suggestions.append(
            "Character development: Create an opportunity for character growth"
        )

        return suggestions

    def _create_scene_description(self, prompt: str) -> str:
        """Create a brief scene description based on the prompt."""
        if "tavern" in prompt.lower():
            return "The warm glow of the hearth casts dancing shadows across weathered faces"
        if "dungeon" in prompt.lower():
            return "Ancient stone walls echo with the party's footsteps and distant dripping"
        if "forest" in prompt.lower():
            return (
                "Dappled sunlight filters through the canopy as leaves rustle overhead"
            )
        if "town" in prompt.lower():
            return (
                "Bustling streets filled with merchants, guards, and curious onlookers"
            )
        return "The party finds themselves in a situation requiring careful consideration"

    def _check_consistency(
        self, characters: List[str], npcs: List[str], _situation: str
    ) -> List[str]:
        """Check for potential consistency issues with character/NPC behavior."""
        notes = []

        # Check character consistency
        for char_name in characters:
            if char_name in self.character_consultants:
                consultant = self.character_consultants[char_name]
                # Add consistency check based on established personality
                if hasattr(consultant.profile, "personality_summary"):
                    notes.append(
                        f"{char_name}: Remember their {consultant.profile.personality_summary}"
                    )

        # Check NPC relationships
        for npc_name in npcs:
            if npc_name in self.npc_agents:
                agent = self.npc_agents[npc_name]
                for char_name in characters:
                    if char_name in agent.profile.relationships:
                        relationship = agent.profile.relationships[char_name]
                        notes.append(f"{npc_name} and {char_name}: {relationship}")

        return notes

    def get_available_npcs(self) -> List[str]:
        """Get list of available NPC names."""
        return list(self.npc_agents.keys())

    def get_available_characters(self) -> List[str]:
        """Get list of available character names."""
        return list(self.character_consultants.keys())

    def suggest_npc_interaction(self, npc_name: str, situation: str) -> Dict[str, Any]:
        """Get specific suggestions for how an NPC would react in a situation."""
        if npc_name not in self.npc_agents:
            return {"error": f"NPC '{npc_name}' not found"}

        agent = self.npc_agents[npc_name]
        suggested_behavior = self._suggest_npc_behavior(agent.profile, situation)

        return {
            "npc_name": npc_name,
            "personality": agent.profile.personality,
            "role": agent.profile.role,
            "suggested_behavior": suggested_behavior,
            "relationships": agent.profile.relationships,
            "situation": situation,
        }

    def _build_character_context(self, characters_present: List[str]) -> List[str]:
        """Build context strings about present characters."""
        character_context = []
        for char_name in characters_present:
            if char_name in self.character_consultants:
                consultant = self.character_consultants[char_name]
                profile = consultant.profile
                char_info = (
                    f"- {profile.name} ({profile.character_class.value}): "
                    f"{profile.personality_summary[:100]}"
                )
                character_context.append(char_info)
        return character_context

    def _build_npc_context(self, npcs_present: List[str]) -> List[str]:
        """Build context strings about present NPCs."""
        npc_context = []
        for npc_name in npcs_present:
            if npc_name in self.npc_agents:
                agent = self.npc_agents[npc_name]
                npc_info = (
                    f"- {agent.profile.name} ({agent.profile.role}): "
                    f"{agent.profile.personality}"
                )
                npc_context.append(npc_info)
        return npc_context

    def generate_narrative_content(
        self,
        story_prompt: str,
        characters_present: List[str] = None,
        npcs_present: List[str] = None,
        style: str = "immersive",
    ) -> str:
        """
        Generate narrative content using AI based on story prompt and present characters/NPCs.

        Args:
            story_prompt: The story situation/prompt to generate narrative for
            characters_present: List of character names present in the scene
            npcs_present: List of NPC names present in the scene
            style: Narrative style (immersive, cinematic, descriptive)

        Returns:
            Generated narrative content as markdown text
        """
        characters_present = characters_present or []
        npcs_present = npcs_present or []

        # If AI not available, return rule-based narrative
        if not self.ai_client or not AI_AVAILABLE:
            return self._generate_fallback_narrative(
                story_prompt, characters_present, npcs_present
            )

        # Build context about characters and NPCs
        character_context = self._build_character_context(characters_present)
        npc_context = self._build_npc_context(npcs_present)

        # Get RAG context if available
        rag_context = ""
        if self.rag_system and self.rag_system.enabled:
            # Extract location names from prompt (simple keyword extraction)
            potential_locations = self._extract_locations_from_prompt(story_prompt)
            if potential_locations:
                print(
                    f"🔍 RAG: Searching wiki for: {', '.join(potential_locations)}"
                )
                rag_context = self.rag_system.get_context_for_query(
                    story_prompt, potential_locations, max_results=2
                )

        # Create the AI prompt
        system_prompt = f"""You are an expert D&D Dungeon Master creating
engaging narrative content.
Style: {style} - Write in an {style} style that draws readers into the story.
Format: Use markdown with ## headers for scenes, write in past tense, keep
paragraphs to 2-3 sentences.
Line length: Keep lines to approximately 70-80 characters for readability.

Create vivid, engaging narrative that:
- Shows character personalities through actions and dialogue
- Includes environmental descriptions
- Advances the plot naturally
- Maintains appropriate pacing
- Uses proper D&D terminology
- Respects established lore from the campaign setting (see lore context
  if provided)"""

        user_prompt = f"""Create D&D narrative content for this story situation:

{story_prompt}

Characters present:
{chr(10).join(character_context) if character_context else "No specific characters mentioned"}

NPCs present:
{chr(10).join(npc_context) if npc_context else "No specific NPCs mentioned"}
{rag_context}
Generate a complete narrative scene with:
1. An opening that sets the scene
2. Character interactions and dialogue
3. Plot developments
4. A natural transition or hook for continuation

Keep the narrative between 300-500 words.
{("IMPORTANT: Use the lore context provided above to ensure accuracy "
"and enrich the narrative." if rag_context else "")}"""

        try:
            narrative = self.ai_client.chat_completion(
                messages=[
                    self.ai_client.create_system_message(system_prompt),
                    self.ai_client.create_user_message(user_prompt),
                ],
                temperature=0.8,  # Higher temperature for creative narrative
                max_tokens=2000,
            )

            return (
                narrative
                if narrative
                else self._generate_fallback_narrative(
                    story_prompt, characters_present, npcs_present
                )
            )

        except (ConnectionError, TimeoutError, ValueError, KeyError) as e:
            print(f"Warning: AI narrative generation failed: {e}")
            return self._generate_fallback_narrative(
                story_prompt, characters_present, npcs_present
            )

    def _generate_fallback_narrative(
        self, story_prompt: str, characters: List[str], npcs: List[str]
    ) -> str:
        """Generate basic narrative when AI is unavailable."""
        narrative = "## The Story Begins\n\n"
        narrative += f"{story_prompt}\n\n"

        if characters:
            narrative += "## The Adventurers\n\n"
            narrative += f"Present for this adventure: {', '.join(characters)}\n\n"

        if npcs:
            narrative += "## Key NPCs\n\n"
            narrative += f"Important figures in this scene: {', '.join(npcs)}\n\n"

        narrative += "## What Happens Next\n\n"
        narrative += "*[Narrative content would be generated here with AI enabled]*\n"

        return narrative

    def _extract_locations_from_prompt(self, prompt: str) -> List[str]:
        """
        Extract potential location names from prompt for RAG lookup.
        Uses simple heuristics: capitalized words/phrases that might be locations.
        """
        # Look for capitalized phrases (potential proper nouns/locations)
        # Pattern: words starting with capital letter, possibly multi-word
        pattern = r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b"
        matches = re.findall(pattern, prompt)

        # Filter out common words that aren't locations
        common_words = {
            "The",
            "A",
            "An",
            "They",
            "He",
            "She",
            "It",
            "We",
            "You",
            "What",
            "Where",
            "When",
            "Why",
            "How",
            "Which",
            "Who",
        }
        locations = [m for m in matches if m not in common_words and len(m) > 2]

        # Remove duplicates while preserving order
        seen = set()
        unique_locations = []
        for loc in locations:
            if loc not in seen:
                seen.add(loc)
                unique_locations.append(loc)

        return unique_locations[:5]  # Limit to 5 most likely locations
