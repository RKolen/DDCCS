"""
Story Suggestion Engine

Generates AI-powered suggestions for story development using the configured
AI client. Falls back to an empty list when AI is unavailable.
"""

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.ai.prompt_templates import LANGUAGE_INSTRUCTION
from src.stories.suggestion_types import (
    StorySuggestion,
    SuggestionContext,
    SuggestionSet,
    SuggestionType,
)

# ---------------------------------------------------------------------------
# Prompt templates (system + user) keyed by SuggestionType
# ---------------------------------------------------------------------------

_SYSTEM_PLOT_HOOK = (
    "You are a creative D&D adventure designer. Generate compelling plot hooks "
    "that DMs can use to develop their campaigns. Each hook should be specific, "
    "actionable, and tied to the existing story context. "
    "Format your response as a JSON array where each element has: "
    "'title', 'description', 'rationale', 'implementation_notes', "
    "and 'suggested_timing' fields."
)

_USER_PLOT_HOOK = (
    "Based on the following story context, generate {count} plot hook "
    "suggestions for a D&D campaign.\n\n"
    "STORY CONTEXT:\n{story_context}\n\n"
    "PARTY MEMBERS:\n{party_context}\n\n"
    "KNOWN NPCs:\n{npc_context}\n\n"
    "Generate plot hooks that:\n"
    "1. Connect to existing story elements\n"
    "2. Provide clear adventure opportunities\n"
    "3. Create opportunities for character development\n"
    "4. Are specific enough to use immediately\n\n"
    "Respond with a JSON array of suggestions."
)

_SYSTEM_CHARACTER_MOMENT = (
    "You are a D&D character development specialist. Suggest meaningful moments "
    "that highlight character personalities, backgrounds, and growth "
    "opportunities. Each suggestion should create roleplay opportunities and "
    "deepen character engagement. "
    "Format your response as a JSON array where each element has: "
    "'title', 'description', 'rationale', 'relevant_characters', "
    "and 'implementation_notes' fields."
)

_USER_CHARACTER_MOMENT = (
    "Based on the following characters and story context, suggest {count} "
    "character moment opportunities.\n\n"
    "CHARACTERS:\n{party_context}\n\n"
    "STORY CONTEXT:\n{story_context}\n\n"
    "Suggest moments that:\n"
    "1. Highlight each character's unique traits\n"
    "2. Create roleplay opportunities\n"
    "3. Connect to character backstories\n"
    "4. Allow for meaningful player choices\n\n"
    "Respond with a JSON array of suggestions."
)

_SYSTEM_PLOT_TWIST = (
    "You are a master of D&D plot twists and surprises. Generate unexpected "
    "narrative turns that recontextualize existing story elements. Twists should "
    "be surprising but fair, with proper foreshadowing opportunities. "
    "Format your response as a JSON array where each element has: "
    "'title', 'description', 'rationale', 'implementation_notes', "
    "and 'foreshadowing_hints' fields."
)

_USER_PLOT_TWIST = (
    "Based on the following story context, suggest {count} plot twist ideas.\n\n"
    "STORY CONTEXT:\n{story_context}\n\n"
    "PARTY MEMBERS:\n{party_context}\n\n"
    "Generate twists that:\n"
    "1. Recontextualize existing NPCs or events\n"
    "2. Create dramatic tension\n"
    "3. Have foreshadowing opportunities\n"
    "4. Maintain narrative coherence\n\n"
    "Respond with a JSON array of suggestions."
)

_SYSTEM_NARRATIVE_IMPROVEMENT = (
    "You are a D&D narrative writing coach. Suggest improvements to story "
    "descriptions, pacing, and atmosphere. Focus on making narratives more "
    "engaging and immersive. "
    "Format your response as a JSON array where each element has: "
    "'title', 'description', 'rationale', and 'implementation_notes' fields."
)

_USER_NARRATIVE_IMPROVEMENT = (
    "Review the following story content and suggest {count} narrative "
    "improvements.\n\n"
    "STORY CONTENT:\n{story_context}\n\n"
    "Suggest improvements for:\n"
    "1. Descriptive language and atmosphere\n"
    "2. Pacing and tension\n"
    "3. Character voice and dialogue\n"
    "4. Sensory details and immersion\n\n"
    "Respond with a JSON array of suggestions."
)

_SYSTEM_NPC_INTERACTION = (
    "You are a D&D NPC specialist. Generate dynamic NPC interaction ideas that "
    "create memorable encounters. Focus on NPC personality, motivations, and "
    "relationship dynamics. "
    "Format your response as a JSON array where each element has: "
    "'title', 'description', 'rationale', 'relevant_npcs', "
    "and 'implementation_notes' fields."
)

_USER_NPC_INTERACTION = (
    "Based on the following NPCs and story context, suggest {count} NPC "
    "interaction opportunities.\n\n"
    "NPCs:\n{npc_context}\n\n"
    "STORY CONTEXT:\n{story_context}\n\n"
    "Suggest interactions that:\n"
    "1. Showcase NPC personalities\n"
    "2. Create roleplay opportunities\n"
    "3. Advance plot threads\n"
    "4. Build relationships with party members\n\n"
    "Respond with a JSON array of suggestions."
)

_SYSTEM_FORESHADOWING = (
    "You are a D&D foreshadowing expert. Suggest subtle hints and setup for "
    "future story developments. Focus on creating mystery and anticipation "
    "without revealing too much. "
    "Format your response as a JSON array where each element has: "
    "'title', 'description', 'rationale', 'implementation_notes', "
    "and 'payoff_timing' fields."
)

_USER_FORESHADOWING = (
    "Based on the following story context, suggest {count} foreshadowing "
    "opportunities.\n\n"
    "STORY CONTEXT:\n{story_context}\n\n"
    "CAMPAIGN DIRECTION:\n{campaign_direction}\n\n"
    "Suggest foreshadowing that:\n"
    "1. Hints at future events subtly\n"
    "2. Creates mystery and anticipation\n"
    "3. Can be paid off in future sessions\n"
    "4. Rewards attentive players\n\n"
    "Respond with a JSON array of suggestions."
)

# Decision table mapping SuggestionType to (system_prompt, user_template)
_PROMPT_TABLE: Dict[SuggestionType, tuple] = {
    SuggestionType.PLOT_HOOK: (_SYSTEM_PLOT_HOOK, _USER_PLOT_HOOK),
    SuggestionType.CHARACTER_MOMENT: (_SYSTEM_CHARACTER_MOMENT, _USER_CHARACTER_MOMENT),
    SuggestionType.PLOT_TWIST: (_SYSTEM_PLOT_TWIST, _USER_PLOT_TWIST),
    SuggestionType.NARRATIVE_IMPROVEMENT: (
        _SYSTEM_NARRATIVE_IMPROVEMENT,
        _USER_NARRATIVE_IMPROVEMENT,
    ),
    SuggestionType.NPC_INTERACTION: (_SYSTEM_NPC_INTERACTION, _USER_NPC_INTERACTION),
    SuggestionType.FORESHADOWING: (_SYSTEM_FORESHADOWING, _USER_FORESHADOWING),
}

_MAX_STORY_CONTEXT_CHARS = 2000
_MAX_BACKGROUND_CHARS = 100


@dataclass
class SuggestionConfig:
    """Configuration for a comprehensive suggestion generation run.

    Attributes:
        campaign_name: Name of the campaign.
        story_content: Full text of the story being analysed.
        story_file: Optional filename of the story (for metadata).
        party_profiles: Mapping of character name to profile dict.
        npc_data: List of NPC profile dicts.
        suggestion_types: Types to generate; defaults to all types when None.
        count_per_type: Number of suggestions to generate per type.
    """

    campaign_name: str
    story_content: str
    story_file: Optional[str] = None
    party_profiles: Dict[str, Any] = field(default_factory=dict)
    npc_data: List[Dict[str, Any]] = field(default_factory=list)
    suggestion_types: Optional[List[SuggestionType]] = None
    count_per_type: int = 2


class SuggestionEngine:
    """Generates AI-powered story suggestions.

    Uses the supplied AI client to call the configured LLM with structured
    prompts. Returns empty lists when AI is unavailable or the request fails.

    Attributes:
        ai_client: An initialized AIClient instance, or None.
    """

    def __init__(self, ai_client: Optional[Any]) -> None:
        """Initialize the suggestion engine.

        Args:
            ai_client: Initialized AIClient instance, or None to disable AI.
        """
        self.ai_client = ai_client

    def generate_suggestions(
        self,
        suggestion_type: SuggestionType,
        story_context: str,
        extra_context: Optional[Dict[str, str]] = None,
        count: int = 3,
    ) -> List[StorySuggestion]:
        """Generate suggestions of a specific type.

        Args:
            suggestion_type: Type of suggestions to generate.
            story_context: Current story content or summary.
            extra_context: Optional dict with keys 'party_context',
                'npc_context', 'campaign_direction'.
            count: Number of suggestions to generate.

        Returns:
            List of StorySuggestion objects, empty on failure or no AI.
        """
        if self.ai_client is None:
            return []

        pair = _PROMPT_TABLE.get(suggestion_type)
        if pair is None:
            return []

        ctx = extra_context or {}
        base_system_prompt, user_template = pair
        system_prompt = f"{base_system_prompt} {LANGUAGE_INSTRUCTION}"
        user_prompt = user_template.format(
            count=count,
            story_context=story_context or "No story context available.",
            party_context=ctx.get("party_context") or "No party information available.",
            npc_context=ctx.get("npc_context") or "No NPC information available.",
            campaign_direction=(
                ctx.get("campaign_direction") or "No campaign direction specified."
            ),
        )

        try:
            response = self.ai_client.chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.9,
                max_tokens=2000,
            )
            return self.parse_suggestions(response, suggestion_type)
        except (AttributeError, TypeError, KeyError, ValueError, RuntimeError) as exc:
            print(f"[WARNING] Failed to generate suggestions: {exc}")
            return []

    def generate_comprehensive_suggestions(
        self,
        config: SuggestionConfig,
    ) -> SuggestionSet:
        """Generate a comprehensive set of suggestions from a SuggestionConfig.

        Args:
            config: SuggestionConfig with all campaign and context data.

        Returns:
            SuggestionSet populated with all generated suggestions.
        """
        suggestion_set = SuggestionSet(
            campaign_name=config.campaign_name,
            story_file=config.story_file,
        )

        types_to_run = config.suggestion_types or list(SuggestionType)
        extra_context = {
            "party_context": self.build_party_context(config.party_profiles),
            "npc_context": self.build_npc_context(config.npc_data),
        }
        truncated_story = config.story_content[:_MAX_STORY_CONTEXT_CHARS]

        for suggestion_type in types_to_run:
            suggestions = self.generate_suggestions(
                suggestion_type=suggestion_type,
                story_context=truncated_story,
                extra_context=extra_context,
                count=config.count_per_type,
            )
            for suggestion in suggestions:
                suggestion.context.source_story = config.story_file
                suggestion_set.add_suggestion(suggestion)

        return suggestion_set

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def parse_suggestions(
        self,
        response: str,
        suggestion_type: SuggestionType,
    ) -> List[StorySuggestion]:
        """Parse an AI response string into StorySuggestion objects.

        Args:
            response: Raw string returned by the AI client.
            suggestion_type: The type to assign to parsed suggestions.

        Returns:
            List of StorySuggestion objects.
        """
        suggestions: List[StorySuggestion] = []

        # Strip Markdown code fences if present
        cleaned = response.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            # Drop first and last fence lines
            inner = lines[1:-1] if lines[-1].strip() == "```" else lines[1:]
            cleaned = "\n".join(inner)

        try:
            data = json.loads(cleaned)
            if not isinstance(data, list):
                data = [data]

            for item in data:
                suggestion = StorySuggestion(
                    suggestion_type=suggestion_type,
                    title=item.get("title", "Untitled Suggestion"),
                    description=item.get("description", ""),
                    rationale=item.get("rationale", ""),
                    context=SuggestionContext(
                        implementation_notes=item.get("implementation_notes"),
                        suggested_timing=(
                            item.get("suggested_timing") or item.get("payoff_timing")
                        ),
                        relevant_characters=item.get("relevant_characters", []),
                        relevant_npcs=item.get("relevant_npcs", []),
                    ),
                )
                suggestions.append(suggestion)

        except json.JSONDecodeError:
            # Fallback: wrap the raw text as a single suggestion
            suggestions.append(
                StorySuggestion(
                    suggestion_type=suggestion_type,
                    title="AI Suggestion",
                    description=response,
                    rationale="Generated from AI analysis",
                )
            )

        return suggestions

    def build_party_context(self, party_profiles: Dict[str, Any]) -> str:
        """Build a compact context string from party profiles.

        Args:
            party_profiles: Mapping of character name to profile dict.

        Returns:
            Multi-line string summarising the party.
        """
        if not party_profiles:
            return "No party members available."

        lines = []
        for name, profile in party_profiles.items():
            if isinstance(profile, dict):
                char_class = profile.get("dnd_class", "Unknown")
                level = profile.get("level", "?")
                personality = profile.get("personality_summary", "")
                background = profile.get("background_story", "")[:_MAX_BACKGROUND_CHARS]
                lines.append(
                    f"- {name}: Level {level} {char_class}. {personality} {background}"
                )

        return "\n".join(lines)

    def build_npc_context(self, npc_data: List[Dict[str, Any]]) -> str:
        """Build a compact context string from NPC data.

        Args:
            npc_data: List of NPC profile dicts.

        Returns:
            Multi-line string summarising the NPCs.
        """
        if not npc_data:
            return "No NPCs available."

        lines = []
        for npc in npc_data:
            name = npc.get("name", "Unknown")
            role = npc.get("role", "NPC")
            location = npc.get("location", "Unknown location")
            personality = npc.get("personality", "")
            lines.append(f"- {name} ({role} at {location}): {personality}")

        return "\n".join(lines)
