"""Character Action Analysis Component

Analyzes character actions extracted from stories and provides insights on
reasoning, consistency, and development opportunities.
"""

from typing import Dict, List


def extract_reasoning(action_text: str) -> str:
    """Extract reasoning about character's motivation from action text.

    Args:
        action_text: Description of the character's action

    Returns:
        String describing likely reasoning
    """
    action_lower = action_text.lower()

    uncertainty_words = ["hesitant", "reluctant", "uncertain", "hesitated"]
    if any(word in action_lower for word in uncertainty_words):
        return "Character showing uncertainty or doubt about course of action"

    decision_words = ["decided", "chose", "determined", "resolved"]
    if any(word in action_lower for word in decision_words):
        return "Character making deliberate choice aligned with goals"

    search_words = ["searching", "investigating", "examined", "looked"]
    if any(word in action_lower for word in search_words):
        return "Character pursuing information gathering and problem-solving"

    talk_words = ["spoke", "said", "asked", "replied", "told"]
    if any(word in action_lower for word in talk_words):
        return "Character communicating and engaging with others"

    movement_words = ["moved", "walked", "ran", "traveled", "ventured"]
    if any(word in action_lower for word in movement_words):
        return "Character taking initiative and exploring situation"

    return "Character taking action based on current situation"


def assess_consistency(action_text: str) -> str:
    """Assess if action is consistent with typical character archetypes.

    Args:
        action_text: Description of the character's action

    Returns:
        String assessing consistency
    """
    action_lower = action_text.lower()

    tactical_words = ["carefully", "cautiously", "strategically"]
    if any(word in action_lower for word in tactical_words):
        return "Action consistent with tactical thinking"

    bold_words = ["boldly", "charged", "attacked", "aggressive"]
    if any(word in action_lower for word in bold_words):
        return "Action consistent with courageous/direct approach"

    wisdom_words = ["wisely", "thoughtfully", "sage", "wisdom"]
    if any(word in action_lower for word in wisdom_words):
        return "Action consistent with experienced judgment"

    stealth_words = ["secretly", "quietly", "stealthily"]
    if any(word in action_lower for word in stealth_words):
        return "Action consistent with cunning/subtle approach"

    return "Action warrants character consistency review"


def generate_development_notes(action_text: str) -> str:
    """Generate development notes suggesting character growth opportunities.

    Args:
        action_text: Description of the character's action

    Returns:
        String with development suggestion
    """
    action_lower = action_text.lower()

    doubt_words = ["hesitant", "uncertain", "doubted"]
    if any(word in action_lower for word in doubt_words):
        return "Opportunity to explore character's fears and build confidence"

    learning_words = ["discovered", "learned", "revealed"]
    if any(word in action_lower for word in learning_words):
        return "Character gaining knowledge - track impact on future decisions"

    conflict_words = ["conflict", "disagreed", "argued"]
    if any(word in action_lower for word in conflict_words):
        return "Character interaction offers chance for relationship development"

    sacrifice_words = ["sacrifice", "risked", "endangered"]
    if any(word in action_lower for word in sacrifice_words):
        return "Character showing values - important for motivation and arcs"

    refusal_words = ["refused", "rejected", "denied"]
    if any(word in action_lower for word in refusal_words):
        return "Character setting boundaries - track moral stance and convictions"

    return "Review action against character's established personality and goals"


def extract_character_actions(
    story_content: str,
    party_names: List[str],
    truncate_func
) -> List[Dict[str, str]]:
    """Extract character actions from story narrative.

    Searches for character mentions and extracts surrounding context.

    Args:
        story_content: Full story text
        party_names: List of party member names
        truncate_func: Function to truncate text at sentence boundary

    Returns:
        List of character action dictionaries
    """
    character_actions = []
    lines = story_content.split("\n")
    max_action_length = 500

    for party_member in party_names:
        action_found = False
        for i, line in enumerate(lines):
            if party_member in line:
                context_start = max(0, i - 1)
                context_end = min(len(lines), i + 3)
                context = " ".join(lines[context_start:context_end])

                if context.strip():
                    action_text = context.strip()
                    if len(action_text) > max_action_length:
                        action_text = truncate_func(action_text,
                                                     max_action_length)

                    character_actions.append({
                        "character": party_member,
                        "action": action_text,
                        "reasoning": extract_reasoning(action_text),
                        "consistency": assess_consistency(action_text),
                        "notes": generate_development_notes(action_text)
                    })
                    action_found = True
                    break

        if not action_found:
            character_actions.append({
                "character": party_member,
                "action": "Not mentioned in this story segment",
                "reasoning": "Character was absent from this scene",
                "consistency": "N/A - no actions to evaluate",
                "notes": "No interaction recorded - consider opportunities"
            })

    return character_actions
