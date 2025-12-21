"""Character Action Analysis Component

Analyzes character actions extracted from stories with personality trait awareness.
Provides insights on reasoning, consistency, and development opportunities by
considering each character's background story, personality, motivations, fears,
relationships, goals, and secrets.

Uses AI for personality-aware analysis when available, falls back to rule-based
analysis when AI is not configured.
"""

import re
from typing import Dict, List, Optional, Any

# Optional AI import - AIClient may not be available in all environments
try:
    from src.ai.ai_client import AIClient

    AI_AVAILABLE = True
except (ImportError, ModuleNotFoundError):
    AI_AVAILABLE = False


def _build_character_context_string(
    character_name: str, traits: Optional[Dict[str, Any]]
) -> str:
    """Build character context string from traits dictionary."""
    lines = [f"Character: {character_name}"]

    if traits is None:
        return "\n".join(lines) + "\n"

    # Support both new CharacterProfile field names and legacy JSON field names
    trait_mappings = [
        (("personality_summary", "personality_traits"), "Personality"),
        (("motivations", "bonds"), "Motivations"),
        (("goals", "ideals"), "Goals"),
        (("fears_weaknesses", "flaws"), "Fears/Weaknesses"),
    ]

    for trait_keys, label in trait_mappings:
        # Try new field name first, then legacy name
        if isinstance(trait_keys, tuple):
            value = traits.get(trait_keys[0]) or traits.get(trait_keys[1])
        else:
            value = traits.get(trait_keys)

        if value:
            # Handle lists vs strings
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            lines.append(f"{label}: {value}")

    # Support both background_story and backstory
    background = traits.get("background_story") or traits.get("backstory")
    if background:
        lines.append(f"Background: {background[:200]}")

    return "\n".join(lines) + "\n"


def _get_prompt_for_analysis(
    analysis_type: str,
    char_context: str,
    action_text: str,
    previous_actions: Optional[List[str]] = None,
) -> Optional[str]:
    """Build prompt for AI analysis based on type.

    Args:
        analysis_type: Type of analysis ("reasoning", "consistency", "development")
        char_context: Character profile context string
        action_text: The current action being analyzed
        previous_actions: Optional list of character's prior actions in this campaign

    Returns:
        Prompt string for AI, or None if analysis_type not recognized
    """
    base = f"{char_context}Story Action: {action_text}\n\n"

    # Build prior actions context if provided
    prior_actions_context = ""
    if previous_actions and len(previous_actions) > 0:
        prior_actions_context = (
            "\nPrior actions by this character in this campaign:\n"
            + "\n".join(f"- {action}" for action in previous_actions[:5])
            + "\n\n"
        )

    lang_note = (
        "RESPOND IN ENGLISH ONLY. "
        "Do not use any other languages. "
        "Do not include any Chinese, unicode, or special characters."
    )

    prompts = {
        "reasoning": (
            base + "Analyze this character's reasoning for this action. "
            "Consider their personality, motivations, and goals. "
            "Be specific and concise (1-2 sentences). " + lang_note
        ),
        "consistency": (
            base
            + prior_actions_context
            + "Assess if this action is consistent with the character's "
            "personality traits, motivations, and goals shown above. "
            "If prior actions are shown, also check consistency with their "
            "established behavior patterns. "
            "CRITICAL: This is a custom D&D campaign, NOT official lore. "
            "IGNORE any external canon (Lord of the Rings, novels, games, etc.). "
            "ONLY evaluate consistency against the character profile and their campaign history. "
            "Be specific (1-2 sentences). " + lang_note
        ),
        "development": (
            base
            + prior_actions_context
            + "Identify character development opportunities or growth themes "
            "from this action. How does this advance their story? "
            "Consider evolution based on prior actions in this campaign. "
            "Be specific (1-2 sentences). " + lang_note
        ),
    }

    return prompts.get(analysis_type)


def _get_ai_analysis(
    analysis_type: str,
    action_text: str,
    character_name: str,
    character_traits: Optional[Dict[str, Any]] = None,
    previous_actions: Optional[List[str]] = None,
) -> Optional[str]:
    """Get AI-based analysis for character action with personality awareness.

    Args:
        analysis_type: Type of analysis ("reasoning", "consistency", "development")
        action_text: Description of the character's action
        character_name: Name of the character
        character_traits: Optional dict with personality, goals, background, etc.
        previous_actions: Optional list of character's prior actions in this campaign

    Returns:
        AI-generated analysis string, or None if AI is not available
    """
    if not AI_AVAILABLE:
        return None

    # Check if AI is enabled
    ai_config = character_traits.get("ai_config") if character_traits else None
    if isinstance(ai_config, dict) and not ai_config.get("enabled", True):
        return None

    try:
        ai_client = AIClient()
        char_context = _build_character_context_string(character_name, character_traits)
        prompt = _get_prompt_for_analysis(
            analysis_type, char_context, action_text, previous_actions
        )

        if not prompt:
            return None

        response = ai_client.chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "SYSTEM INSTRUCTIONS - CRITICAL:\n"
                        "You are a D&D character analysis assistant.\n"
                        "YOU MUST respond ONLY in English.\n"
                        "DO NOT generate ANY Chinese characters.\n"
                        "DO NOT generate ANY non-ASCII characters.\n"
                        "DO NOT generate ANY special Unicode sequences.\n"
                        "ONLY ASCII English text is acceptable.\n"
                        "If you cannot respond in English, respond with: "
                        "'Unable to generate response.'"
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=150,
        )
        response_text = response.strip() if response else None

        # Validate response contains no Chinese/Unicode characters
        if response_text:
            # Check for common Chinese character ranges
            for char in response_text:
                code = ord(char)
                # Chinese characters are typically in ranges: 0x4E00-0x9FFF, 0x3400-0x4DBF
                if (
                    0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF or code > 127
                ):  # Reject any non-ASCII except common punctuation
                    # If Chinese detected, return None to trigger fallback
                    return None

        return response_text

    except (AttributeError, ValueError, ConnectionError, TimeoutError):
        # AI failed, will use rule-based fallback
        return None


def extract_reasoning(
    action_text: str, character_traits: Optional[Dict[str, Any]] = None
) -> str:
    """Extract reasoning about character's motivation from action text.

    Considers character personality, motivations, goals, and backstory when available.
    Uses AI for personality-aware analysis when available, falls back to rule-based.

    Args:
        action_text: Description of the character's action
        character_traits: Optional dict with personality, motivations, goals, etc.

    Returns:
        String describing likely reasoning
    """
    if character_traits:
        # Try AI-based analysis first
        ai_reasoning = _get_ai_analysis(
            "reasoning",
            action_text,
            character_traits.get("name", "Character"),
            character_traits,
        )
        if ai_reasoning:
            return ai_reasoning

    # Fall back to rule-based analysis
    action_lower = action_text.lower()
    traits = character_traits or {}

    word_patterns = [
        (
            ["hesitant", "reluctant", "uncertain", "hesitated"],
            "uncertainty about course of action",
            "fears_weaknesses",
        ),
        (
            ["decided", "chose", "determined", "resolved"],
            "deliberate choice aligned with goals",
            "goals",
        ),
        (
            ["searching", "investigating", "examined", "looked"],
            "information gathering and problem-solving",
            "motivations",
        ),
        (
            ["spoke", "said", "asked", "replied", "told"],
            "communicating and engaging with others",
            "relationships",
        ),
        (
            ["moved", "walked", "ran", "traveled", "ventured"],
            "taking initiative and exploring situation",
            "personality_summary",
        ),
    ]

    for words, base_msg, trait_key in word_patterns:
        if any(word in action_lower for word in words):
            if traits.get(trait_key):
                trait_val = traits[trait_key]
                if trait_key == "relationships":
                    trait_val = list(trait_val.keys())[0]
                elif trait_key == "personality_summary":
                    trait_val = trait_val[:50]
                return f"Character {base_msg}: {trait_val}"
            return f"Character {base_msg}"

    return "Character taking action based on current situation"


def assess_consistency(
    action_text: str,
    character_traits: Optional[Dict[str, Any]] = None,
    previous_actions: Optional[List[str]] = None,
) -> str:
    """Assess if action is consistent with character's established traits.

    Checks action against personality summary, background, and behavior patterns.
    Also considers prior actions in this campaign to check for consistent behavior.
    Uses AI for personality-aware analysis when available, falls back to rule-based.

    Args:
        action_text: Description of the character's action
        character_traits: Optional dict with personality, background, etc.
        previous_actions: Optional list of character's prior actions in this campaign

    Returns:
        String assessing consistency
    """
    if character_traits:
        # Try AI-based analysis first
        ai_consistency = _get_ai_analysis(
            "consistency",
            action_text,
            character_traits.get("name", "Character"),
            character_traits,
            previous_actions,
        )
        if ai_consistency:
            return ai_consistency

    # Fall back to rule-based analysis
    action_lower = action_text.lower()
    traits = character_traits or {}

    consistency_patterns = [
        (
            ["carefully", "cautiously", "strategically"],
            "Action consistent with tactical thinking",
        ),
        (["boldly", "charged", "attacked", "aggressive"], "Action shows boldness"),
        (
            ["wisely", "thoughtfully", "sage", "wisdom"],
            "Action consistent with experienced judgment",
        ),
        (
            ["secretly", "quietly", "stealthily"],
            "Action consistent with cunning/subtle approach",
        ),
    ]

    for words, msg in consistency_patterns:
        if any(word in action_lower for word in words):
            return msg

    if traits.get("personality_summary"):
        pers = traits["personality_summary"][:60]
        return f"Check against personality: {pers}"

    return "Action warrants character consistency review"


def generate_development_notes(
    action_text: str,
    character_traits: Optional[Dict[str, Any]] = None,
    previous_actions: Optional[List[str]] = None,
) -> str:
    """Generate development notes considering character's personality and goals.

    Suggests growth opportunities based on character's background, motivations,
    goals, relationships, and established character arc. Also considers how this
    action develops them relative to their prior actions in this campaign.
    Uses AI for personality-aware analysis when available, falls back to rule-based.

    Args:
        action_text: Description of the character's action
        character_traits: Optional dict with personality, goals, relationships, etc.
        previous_actions: Optional list of character's prior actions in this campaign

    Returns:
        String with development suggestion
    """
    if character_traits:
        # Try AI-based analysis first
        ai_notes = _get_ai_analysis(
            "development",
            action_text,
            character_traits.get("name", "Character"),
            character_traits,
            previous_actions,
        )
        if ai_notes:
            return ai_notes

    # Fall back to rule-based analysis
    action_lower = action_text.lower()
    traits = character_traits or {}

    development_patterns = [
        (
            ["hesitant", "uncertain", "doubted"],
            "fears",
            "Opportunity to face fears and advance goal",
            "Opportunity to explore character's fears",
        ),
        (
            ["discovered", "learned", "revealed"],
            "secrets",
            "Knowledge gained may connect to secrets",
            "Character gaining knowledge - track impact",
        ),
        (
            ["conflict", "disagreed", "argued"],
            "relationships",
            "Relationship development opportunity",
            "Character interaction offers development",
        ),
        (
            ["sacrifice", "risked", "endangered"],
            "motivations",
            "Character showing values aligned with",
            "Character showing important values",
        ),
    ]

    for words, trait_key, with_trait_msg, fallback_msg in development_patterns:
        if any(word in action_lower for word in words):
            if traits.get(trait_key):
                trait_val = traits[trait_key]
                if trait_key == "relationships":
                    trait_val = list(trait_val.keys())[0]
                return f"{with_trait_msg}: {trait_val}"
            return fallback_msg

    if traits.get("background_story"):
        return "Track how this action connects to character's background"

    return "Review action against character's established personality"


def _build_character_action_entry(
    party_member: str,
    action_text: str,
    char_traits: Dict[str, Any],
    previous_actions: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Build a single character action dictionary.

    Args:
        party_member: Character name
        action_text: Description of action
        char_traits: Character personality traits
        previous_actions: Optional list of character's prior actions in this campaign

    Returns:
        Dictionary with character action details
    """
    return {
        "character": party_member,
        "action": action_text,
        "reasoning": extract_reasoning(action_text, char_traits),
        "consistency": assess_consistency(action_text, char_traits, previous_actions),
        "notes": generate_development_notes(action_text, char_traits, previous_actions),
    }


def _build_character_name_patterns(character_name: str) -> List:
    """Build regex patterns for character name variations.

    Args:
        character_name: Full character name (e.g., "Frodo Baggins")

    Returns:
        List of compiled regex patterns for matching variations
    """
    patterns = []

    # Exact match for full name
    patterns.append(
        re.compile(r"\b" + re.escape(character_name) + r"\b", re.IGNORECASE)
    )

    # Match first name only
    first_name = character_name.split()[0]
    if first_name:
        patterns.append(
            re.compile(r"\b" + re.escape(first_name) + r"\b", re.IGNORECASE)
        )

    # Match last name if multi-word name
    if " " in character_name:
        last_name = character_name.split()[-1]
        patterns.append(re.compile(r"\b" + re.escape(last_name) + r"\b", re.IGNORECASE))

    return patterns


def _search_character_in_lines(
    patterns: List,
    search_context: Dict[str, Any],
) -> Optional[Dict[str, str]]:
    """Search for character in story lines and build action entry.

    Args:
        patterns: List of compiled regex patterns for name matching
        search_context: Dict containing:
            - lines: List of story lines
            - party_member: Character name
            - traits: Character trait dictionary
            - truncate_func: Function to truncate text
            - previous_actions: Optional list of character's prior actions

    Returns:
        Character action dictionary or None if not found
    """
    lines = search_context["lines"]
    party_member = search_context["party_member"]
    traits = search_context["traits"]
    truncate_func = search_context["truncate_func"]
    previous_actions = search_context.get("previous_actions")

    for i, line in enumerate(lines):
        # Check if any pattern matches this line
        matches = any(pattern.search(line) for pattern in patterns)

        if not matches:
            continue

        ctx = " ".join(lines[max(0, i - 1) : min(len(lines), i + 3)])
        if not ctx.strip():
            continue

        text = ctx.strip()
        if len(text) > 500:
            text = truncate_func(text, 500)

        return _build_character_action_entry(
            party_member, text, traits, previous_actions
        )

    return None


def extract_character_actions(
    story_content: str,
    party_names: List[str],
    truncate_func,
    character_profiles: Optional[Dict[str, Dict[str, Any]]] = None,
    previous_actions_map: Optional[Dict[str, List[str]]] = None,
) -> List[Dict[str, str]]:
    """Extract character actions from story narrative with personality awareness.

    Searches for character mentions (including name variations) and extracts
    surrounding context. Handles full names, first names, and last names.
    Considers character personality, motivations, goals, and background when
    available. Also evaluates consistency against prior actions in this campaign.

    Args:
        story_content: Full story text
        party_names: List of party member names (e.g., "Frodo Baggins")
        truncate_func: Function to truncate text at sentence boundary
        character_profiles: Optional dict mapping character names to their trait
                          dicts
        previous_actions_map: Optional dict mapping character names to lists of
                            their prior actions from earlier stories

    Returns:
        List of character action dictionaries
    """
    profiles = character_profiles or {}
    previous_actions_map = previous_actions_map or {}
    actions = []
    lines = story_content.split("\n")

    for party_member in party_names:
        traits = profiles.get(party_member, {})
        previous_actions = previous_actions_map.get(party_member, None)

        # Build patterns for character name variations
        patterns = _build_character_name_patterns(party_member)

        # Build search context for character name search
        search_context = {
            "lines": lines,
            "party_member": party_member,
            "traits": traits,
            "truncate_func": truncate_func,
            "previous_actions": previous_actions,
        }

        # Search for character in lines
        action = _search_character_in_lines(patterns, search_context)

        if action:
            actions.append(action)
        else:
            actions.append(
                {
                    "character": party_member,
                    "action": "Not mentioned in this story segment",
                    "reasoning": "Character was absent from this scene",
                    "consistency": "N/A - no actions to evaluate",
                    "notes": "No interaction recorded - consider opportunities",
                }
            )

    return actions
