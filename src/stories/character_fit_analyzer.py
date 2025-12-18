"""Character Fit Analysis for Story Amendment

Analyzes how well characters fit specific story actions and suggests
alternatives based on class abilities, personality traits, motivations,
and prior actions in the campaign.

Enables Story Amender feature to recommend character reassignments
for improved narrative consistency and character utilization.
"""

from typing import Dict, List, Optional, Any, Tuple


def _extract_character_abilities(
    character_traits: Optional[Dict[str, Any]],
) -> List[str]:
    """Extract all abilities from character profile dynamically.

    Args:
        character_traits: Character profile dictionary

    Returns:
        List of ability strings (lowercase)
    """
    if not character_traits:
        return []

    abilities = []

    # Extract class abilities
    class_abilities = character_traits.get("class_abilities", [])
    if isinstance(class_abilities, list):
        abilities.extend([str(a).lower() for a in class_abilities])

    # Extract specialized abilities (handle both list and dict)
    specialized = character_traits.get("specialized_abilities", [])
    if isinstance(specialized, dict):
        abilities.extend([str(k).lower() for k in specialized.keys()])
    elif isinstance(specialized, list):
        abilities.extend([str(a).lower() for a in specialized])

    # Extract spells
    known_spells = character_traits.get("known_spells", [])
    if isinstance(known_spells, list):
        abilities.extend([str(s).lower() for s in known_spells])

    # Extract feats
    feats = character_traits.get("feats", [])
    if isinstance(feats, list):
        abilities.extend([str(f).lower() for f in feats])

    return abilities


def _score_class_ability_match(
    action_text: str, character_traits: Optional[Dict[str, Any]]
) -> float:
    """Score how well an action matches character's class abilities.

    Args:
        action_text: Description of the action
        character_traits: Character profile dictionary

    Returns:
        Score 0.0-1.0 indicating fit (1.0 = perfect match)
    """
    if not character_traits:
        return 0.0

    action_lower = action_text.lower()
    abilities = _extract_character_abilities(character_traits)

    if not abilities:
        return 0.0

    # Check for keyword matches in abilities
    matches = 0
    for ability in abilities:
        # Split ability into keywords for broader matching
        ability_keywords = ability.split()
        if any(keyword in action_lower for keyword in ability_keywords):
            matches += 1

    return min(1.0, matches / max(1, len(abilities) // 2))


def _score_personality_fit(
    action_text: str, character_traits: Optional[Dict[str, Any]]
) -> float:
    """Score how well action aligns with personality traits.

    Args:
        action_text: Description of the action
        character_traits: Character profile with personality info

    Returns:
        Score 0.0-1.0 indicating fit (1.0 = perfect alignment)
    """
    if not character_traits:
        return 0.0

    personality = character_traits.get("personality_summary", "").lower()
    motivations = character_traits.get("motivations", [])
    goals = character_traits.get("goals", [])

    action_lower = action_text.lower()
    score = 0.0
    total_factors = 0

    # Check personality alignment
    if personality:
        personality_keywords = personality.split()
        if any(word in action_lower for word in personality_keywords[:3]):
            score += 0.3
        total_factors += 0.3

    # Check motivation alignment
    if motivations:
        motivations_text = " ".join(motivations).lower()
        if any(word in action_lower for word in motivations_text.split()[:3]):
            score += 0.35
        total_factors += 0.35

    # Check goal alignment
    if goals:
        goals_text = " ".join(goals).lower()
        if any(word in action_lower for word in goals_text.split()[:3]):
            score += 0.35
        total_factors += 0.35

    if total_factors == 0:
        return 0.0

    return min(1.0, score)


def _score_prior_actions_fit(
    action_text: str, previous_actions: Optional[List[str]]
) -> float:
    """Score how consistent action is with character's established pattern.

    Args:
        action_text: Description of the action
        previous_actions: List of character's prior actions in campaign

    Returns:
        Score 0.0-1.0 (1.0 = consistent with pattern)
    """
    if not previous_actions:
        return 0.5

    action_lower = action_text.lower()
    match_count = 0

    # Look for similar keywords in prior actions
    for prior_action in previous_actions:
        prior_lower = prior_action.lower()
        prior_words = set(prior_lower.split())
        action_words = set(action_lower.split())

        # Check for word overlap
        common_words = prior_words & action_words
        if len(common_words) > 2:
            match_count += 1

    if not previous_actions:
        return 0.5

    consistency_score = match_count / len(previous_actions)
    return min(1.0, consistency_score)


def score_character_fit(
    action_text: str,
    character_traits: Optional[Dict[str, Any]],
    previous_actions: Optional[List[str]] = None,
) -> float:
    """Calculate overall fit score for a character performing an action.

    Combines:
    - Class ability match (40% weight)
    - Personality alignment (35% weight)
    - Prior action consistency (25% weight)

    Args:
        action_text: Description of the action
        character_traits: Character profile dictionary
        previous_actions: Optional list of character's prior actions

    Returns:
        Overall fit score 0.0-1.0 (1.0 = excellent fit)
    """
    class_score = _score_class_ability_match(action_text, character_traits)
    personality_score = _score_personality_fit(action_text, character_traits)
    consistency_score = _score_prior_actions_fit(action_text, previous_actions)

    overall_score = (
        (class_score * 0.40) + (personality_score * 0.35) + (consistency_score * 0.25)
    )

    return min(1.0, overall_score)


def find_best_character_fit(
    action_text: str,
    character_profiles: Dict[str, Dict[str, Any]],
    previous_actions_map: Optional[Dict[str, List[str]]] = None,
) -> List[Tuple[str, float]]:
    """Find best party member fit for an action.

    Args:
        action_text: Description of the action
        character_profiles: Dict mapping character names to profiles
        previous_actions_map: Dict mapping character names to prior action lists

    Returns:
        List of (character_name, fit_score) tuples sorted by score (descending)
    """
    previous_actions_map = previous_actions_map or {}
    scores = []

    for member_name, traits in character_profiles.items():
        prior_actions = previous_actions_map.get(member_name)

        fit_score = score_character_fit(action_text, traits, prior_actions)
        scores.append((member_name, fit_score))

    # Sort by score descending
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


def suggest_character_amendment(
    actual_character: str,
    action_text: str,
    character_profiles: Dict[str, Dict[str, Any]],
    previous_actions_map: Optional[Dict[str, List[str]]] = None,
    confidence_threshold: float = 0.15,
) -> Optional[Dict[str, Any]]:
    """Suggest alternative character if better fit exists.

    Args:
        actual_character: Name of character who performed action
        action_text: Description of the action
        character_profiles: Dict mapping character names to profiles
        previous_actions_map: Dict mapping character names to prior actions
        confidence_threshold: Min score difference to suggest (0.0-1.0)

    Returns:
        Dict with suggestion details, or None if current character is best fit
    """
    scores = find_best_character_fit(
        action_text, character_profiles, previous_actions_map
    )

    if not scores:
        return None

    # Find score of actual character
    actual_score = next((s for name, s in scores if name == actual_character), 0.0)

    # Check if better fit exists
    best_name, best_score = scores[0]

    if best_name == actual_character:
        return None

    score_difference = best_score - actual_score

    if score_difference < confidence_threshold:
        return None

    # Build suggestion
    suggestion = {
        "action": action_text,
        "current_character": actual_character,
        "current_fit_score": round(actual_score, 3),
        "suggested_character": best_name,
        "suggested_fit_score": round(best_score, 3),
        "score_difference": round(score_difference, 3),
        "top_alternatives": [(name, round(score, 3)) for name, score in scores[:3]],
    }

    return suggestion
