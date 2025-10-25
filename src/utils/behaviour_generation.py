"""Utilities to generate character `CharacterBehavior` instances from
personality-like fields.

This module provides a single, well-typed function that uses the project's
AI client to synthesize a `CharacterBehavior` dataclass for in-memory use.
The function falls back to a deterministic heuristic if the AI client is
unavailable or returns non-JSON output.

Design notes:
- All imports are top-level to satisfy pylint (no imports inside functions).
- The function never mutates JSON files; it returns a `CharacterBehavior`
  instance for runtime use.
"""

from typing import Dict, List
import logging

from src.characters.consultants.character_profile import CharacterBehavior

try:
    from src.ai.ai_client import call_ai_for_behavior_block

    AI_AVAILABLE = True
except ImportError:
    call_ai_for_behavior_block = None
    AI_AVAILABLE = False

LOGGER = logging.getLogger(__name__)


def _heuristic_behavior(
    personality_traits: List[str],
    ideals: List[str],
    bonds: List[str],
    flaws: List[str],
    backstory: str,
) -> Dict:
    """Deterministic fallback to synthesize a behavior dict from fields.

    This is intentionally simple: it maps common keywords to a few canned
    choices so downstream code always gets a valid structure.
    """
    strategies: List[str] = []
    reactions: Dict[str, str] = {}
    patterns: List[str] = []

    traits = {t.lower() for t in personality_traits}

    # Use ideals to influence preferred strategies
    for ideal in ideals:
        low = ideal.lower()
        if "protect" in low or "defend" in low:
            strategies.append("prioritize protection of allies")
        if "freedom" in low or "liberty" in low:
            strategies.append("avoid unnecessary constraints")
        if "justice" in low or "honor" in low:
            strategies.append("act to uphold justice")

    # Bonds typically create protective or cooperative strategies
    for bond in bonds:
        if bond:
            strategies.append(f"protect {bond}")

    # Flaws introduce likely internal struggles or reaction tendencies
    for flaw in flaws:
        low = flaw.lower()
        if "fear" in low or "coward" in low:
            reactions.setdefault("fear", "hesitate or avoid")
        if "temptation" in low or "greed" in low:
            reactions.setdefault("temptation", "struggle and weigh consequences")

    # Backstory can influence speech patterns (refer to origins or role)
    if backstory:
        if "ranger" in backstory.lower() or "tracker" in backstory.lower():
            patterns.append("uses pragmatic, fieldwise language")
        if "heir" in backstory.lower() or "noble" in backstory.lower():
            patterns.append("formal and measured")

    if "stoic" in traits or "reserved" in traits:
        patterns.append("measured and quiet")
        strategies.append("assess before acting")
        reactions.setdefault("threat", "hold position and evaluate")

    if "wise" in traits or "sage" in traits or "intelligent" in traits:
        patterns.append("thoughtful and advisory")
        strategies.append("seek counsel and gather information")
        reactions.setdefault("mystery", "gather information and advise")

    if "compassionate" in traits or "kind" in traits:
        patterns.append("warm and reassuring")
        strategies.append("protect the vulnerable")
        reactions.setdefault("injury", "offer aid and comfort")

    if "wary of power" in traits or "cautious" in traits:
        patterns.append("cautious about authority")
        strategies.append("avoid unnecessary displays of power")
        reactions.setdefault("temptation", "reflect on duty and resist")

    # Generic fallbacks to ensure non-empty lists
    if not strategies:
        strategies = ["act according to ideals", "support allies"]
    if not patterns:
        patterns = ["speaks plainly"]
    if not reactions:
        reactions = {
            "threat": "respond proportionally",
            "opportunity": "consider benefits",
        }

    return {
        "preferred_strategies": strategies,
        "typical_reactions": reactions,
        "speech_patterns": patterns,
        "decision_making_style": "informed by personality and ideals",
    }


def generate_behavior_from_personality(
    personality_traits: List[str],
    ideals: List[str],
    bonds: List[str],
    flaws: List[str],
    backstory: str,
) -> CharacterBehavior:
    """
    Generate a `CharacterBehavior` instance from the given character fields.

    The function will use the AI client if available; otherwise it falls back
    to a simple heuristic. The returned object is for in-memory use only and
    is not written back to any JSON files.

    Args:
            personality_traits: list of personality strings from the profile
            ideals: list of ideals from the profile
            bonds: list of bonds from the profile
            flaws: list of flaws from the profile
            backstory: free-form backstory string

    Returns:
            CharacterBehavior: dataclass populated from AI output or heuristic
    """
    behavior_dict = None
    if AI_AVAILABLE and call_ai_for_behavior_block is not None:
        try:
            prompt = (
                f"Given the following D&D character profile fields:\n"
                f"- Personality Traits: {personality_traits}\n"
                f"- Ideals: {ideals}\n"
                f"- Bonds: {bonds}\n"
                f"- Flaws: {flaws}\n"
                f"- Backstory: {backstory}\n"
                "Return a JSON object matching the CharacterBehavior dataclass."
            )
            behavior_dict = call_ai_for_behavior_block(prompt)
        except (ValueError, TypeError, ConnectionError, TimeoutError, RuntimeError) as exc:
            LOGGER.warning("AI behavior generation failed: %s", exc)
            behavior_dict = None

    if not behavior_dict:
        behavior_dict = _heuristic_behavior(
            personality_traits, ideals, bonds, flaws, backstory
        )

    # Defensive coercion: ensure returned values are the expected types
    preferred = behavior_dict.get("preferred_strategies") or []
    if not isinstance(preferred, list):
        preferred = [str(preferred)]

    reactions = behavior_dict.get("typical_reactions") or {}
    if not isinstance(reactions, dict):
        # If reactions are returned as a string or list, normalize to a dict
        reactions = {"default": str(reactions)}

    speech = behavior_dict.get("speech_patterns") or []
    if not isinstance(speech, list):
        speech = [str(speech)]

    decision = behavior_dict.get("decision_making_style") or ""
    if not isinstance(decision, str):
        decision = str(decision)

    return CharacterBehavior(
        preferred_strategies=list(preferred),
        typical_reactions=dict(reactions),
        speech_patterns=list(speech),
        decision_making_style=decision,
    )
