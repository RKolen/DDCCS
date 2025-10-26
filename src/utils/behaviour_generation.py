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

from typing import Dict, List, Tuple, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    # Import for type checking only; avoid runtime import to prevent cyclic
    # dependency with src.characters.consultants.character_profile.
    from src.characters.consultants.character_profile import CharacterBehavior
try:
    from src.ai.ai_client import call_ai_for_behavior_block

    AI_AVAILABLE = True
except ImportError:
    call_ai_for_behavior_block = None
    AI_AVAILABLE = False

LOGGER = logging.getLogger(__name__)


def _lower_set(items: List[str]) -> set:
    """Return a set of lowercase, non-empty strings."""
    return {it.lower() for it in items if it}


def _strategies_from_ideals(ideals_list: List[str]) -> List[str]:
    out: List[str] = []
    for ideal in ideals_list:
        low = ideal.lower()
        if "protect" in low or "defend" in low:
            out.append("prioritize protection of allies")
        if "freedom" in low or "liberty" in low:
            out.append("avoid unnecessary constraints")
        if "justice" in low or "honor" in low:
            out.append("act to uphold justice")
    return out


def _strategies_from_bonds(bonds_list: List[str]) -> List[str]:
    return [f"protect {b}" for b in bonds_list if b]


def _reactions_from_flaws(flaws_list: List[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for flaw in flaws_list:
        low = flaw.lower()
        if "fear" in low or "coward" in low:
            out.setdefault("fear", "hesitate or avoid")
        if "temptation" in low or "greed" in low:
            out.setdefault("temptation", "struggle and weigh consequences")
    return out


def _patterns_from_backstory(back: str) -> List[str]:
    out: List[str] = []
    if not back:
        return out
    low = back.lower()
    if "ranger" in low or "tracker" in low:
        out.append("uses pragmatic, fieldwise language")
    if "heir" in low or "noble" in low:
        out.append("formal and measured")
    return out


def _traits_influence(traits_set: set) -> Tuple[List[str], List[str], Dict[str, str]]:
    pats: List[str] = []
    strs: List[str] = []
    reacts: Dict[str, str] = {}
    if "stoic" in traits_set or "reserved" in traits_set:
        pats.append("measured and quiet")
        strs.append("assess before acting")
        reacts.setdefault("threat", "hold position and evaluate")
    if "wise" in traits_set or "sage" in traits_set or "intelligent" in traits_set:
        pats.append("thoughtful and advisory")
        strs.append("seek counsel and gather information")
        reacts.setdefault("mystery", "gather information and advise")
    if "compassionate" in traits_set or "kind" in traits_set:
        pats.append("warm and reassuring")
        strs.append("protect the vulnerable")
        reacts.setdefault("injury", "offer aid and comfort")
    if "wary of power" in traits_set or "cautious" in traits_set:
        pats.append("cautious about authority")
        strs.append("avoid unnecessary displays of power")
        reacts.setdefault("temptation", "reflect on duty and resist")
    return pats, strs, reacts


def _heuristic_behavior(
    personality_traits: List[str],
    ideals: List[str],
    bonds: List[str],
    flaws: List[str],
    backstory: str,
) -> Dict:
    strategies: List[str] = []
    reactions: Dict[str, str] = {}
    patterns: List[str] = []

    traits = _lower_set(personality_traits)

    strategies.extend(_strategies_from_ideals(ideals))
    strategies.extend(_strategies_from_bonds(bonds))
    for k, v in _reactions_from_flaws(flaws).items():
        reactions.setdefault(k, v)
    patterns.extend(_patterns_from_backstory(backstory))

    t_pats, t_strs, t_reacts = _traits_influence(traits)
    patterns.extend(t_pats)
    strategies.extend(t_strs)
    for k, v in t_reacts.items():
        reactions.setdefault(k, v)

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
) -> Dict:
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

    # Return a plain dict so callers (typically CharacterProfile) can
    # decide how to convert into a dataclass. This avoids importing the
    # CharacterProfile module here and prevents cyclic imports.
    return {
        "preferred_strategies": list(preferred),
        "typical_reactions": dict(reactions),
        "speech_patterns": list(speech),
        "decision_making_style": decision,
    }
