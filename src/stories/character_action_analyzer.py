"""Character Action Analysis Component

Analyzes character actions extracted from stories with personality trait awareness.
Provides insights on reasoning, consistency, and development opportunities by
considering each character's background story, personality, motivations, fears,
relationships, goals, and secrets.
"""

from typing import Dict, List, Optional, Any


def extract_reasoning(action_text: str, character_traits: Optional[Dict[str, Any]] = None) -> str:
    """Extract reasoning about character's motivation from action text.

    Considers character personality, motivations, goals, and backstory when available.

    Args:
        action_text: Description of the character's action
        character_traits: Optional dict with personality, motivations, goals, etc.

    Returns:
        String describing likely reasoning
    """
    action_lower = action_text.lower()
    traits = character_traits or {}

    word_patterns = [
        (["hesitant", "reluctant", "uncertain", "hesitated"],
         "uncertainty about course of action",
         "fears_weaknesses"),
        (["decided", "chose", "determined", "resolved"],
         "deliberate choice aligned with goals",
         "goals"),
        (["searching", "investigating", "examined", "looked"],
         "information gathering and problem-solving",
         "motivations"),
        (["spoke", "said", "asked", "replied", "told"],
         "communicating and engaging with others",
         "relationships"),
        (["moved", "walked", "ran", "traveled", "ventured"],
         "taking initiative and exploring situation",
         "personality_summary"),
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


def assess_consistency(action_text: str, character_traits: Optional[Dict[str, Any]] = None) -> str:
    """Assess if action is consistent with character's established traits.

    Checks action against personality summary, background, and behavior patterns.

    Args:
        action_text: Description of the character's action
        character_traits: Optional dict with personality, background, etc.

    Returns:
        String assessing consistency
    """
    action_lower = action_text.lower()
    traits = character_traits or {}

    consistency_patterns = [
        (["carefully", "cautiously", "strategically"],
         "Action consistent with tactical thinking"),
        (["boldly", "charged", "attacked", "aggressive"],
         "Action shows boldness"),
        (["wisely", "thoughtfully", "sage", "wisdom"],
         "Action consistent with experienced judgment"),
        (["secretly", "quietly", "stealthily"],
         "Action consistent with cunning/subtle approach"),
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
    character_traits: Optional[Dict[str, Any]] = None
) -> str:
    """Generate development notes considering character's personality and goals.

    Suggests growth opportunities based on character's background, motivations,
    goals, relationships, and established character arc.

    Args:
        action_text: Description of the character's action
        character_traits: Optional dict with personality, goals, relationships, etc.

    Returns:
        String with development suggestion
    """
    action_lower = action_text.lower()
    traits = character_traits or {}

    development_patterns = [
        (["hesitant", "uncertain", "doubted"],
         "fears",
         "Opportunity to face fears and advance goal",
         "Opportunity to explore character's fears"),
        (["discovered", "learned", "revealed"],
         "secrets",
         "Knowledge gained may connect to secrets",
         "Character gaining knowledge - track impact"),
        (["conflict", "disagreed", "argued"],
         "relationships",
         "Relationship development opportunity",
         "Character interaction offers development"),
        (["sacrifice", "risked", "endangered"],
         "motivations",
         "Character showing values aligned with",
         "Character showing important values"),
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
    char_traits: Dict[str, Any]
) -> Dict[str, str]:
    """Build a single character action dictionary.

    Args:
        party_member: Character name
        action_text: Description of action
        char_traits: Character personality traits

    Returns:
        Dictionary with character action details
    """
    return {
        "character": party_member,
        "action": action_text,
        "reasoning": extract_reasoning(action_text, char_traits),
        "consistency": assess_consistency(action_text, char_traits),
        "notes": generate_development_notes(action_text, char_traits)
    }


def extract_character_actions(
    story_content: str,
    party_names: List[str],
    truncate_func,
    character_profiles: Optional[Dict[str, Dict[str, Any]]] = None
) -> List[Dict[str, str]]:
    """Extract character actions from story narrative with personality awareness.

    Searches for character mentions and extracts surrounding context.
    Considers character personality, motivations, goals, and background when available.

    Args:
        story_content: Full story text
        party_names: List of party member names
        truncate_func: Function to truncate text at sentence boundary
        character_profiles: Optional dict mapping character names to their trait dicts

    Returns:
        List of character action dictionaries
    """
    profiles = character_profiles or {}
    actions = []
    lines = story_content.split("\n")

    for party_member in party_names:
        traits = profiles.get(party_member, {})
        found = False

        for i, line in enumerate(lines):
            if party_member not in line:
                continue

            ctx = " ".join(
                lines[max(0, i - 1):min(len(lines), i + 3)]
            )
            if not ctx.strip():
                continue

            text = ctx.strip()
            if len(text) > 500:
                text = truncate_func(text, 500)

            actions.append(
                _build_character_action_entry(party_member, text, traits)
            )
            found = True
            break

        if not found:
            actions.append({
                "character": party_member,
                "action": "Not mentioned in this story segment",
                "reasoning": "Character was absent from this scene",
                "consistency": "N/A - no actions to evaluate",
                "notes": "No interaction recorded - consider opportunities"
            })

    return actions
