"""
Spell and Ability Lookup Helper

Shared utility for D&D spell/ability lookup via RAG system integration.
Used by both combat narration and story generation to provide accurate
mechanical descriptions from dnd5e.wikidot.com.
"""

import re
from src.ai.availability import AI_AVAILABLE

# Import RAG system for D&D rules lookup
try:
    from src.ai.rag_system import RAGSystem

    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


def lookup_spells_and_abilities(prompt: str) -> str:
    """
    Look up D&D spells and abilities mentioned in a prompt.

    Uses dnd5e.wikidot.com via RAG system for accurate descriptions.
    Supports both combat and non-combat contexts (roleplay, social, exploration).

    Args:
        prompt: Text that may contain spell/ability names

    Returns:
        Formatted context string with spell/ability descriptions, or empty string
    """
    if not RAG_AVAILABLE or not AI_AVAILABLE:
        return ""

    dnd_rag = None
    try:
        dnd_rag = RAGSystem()
    except (ImportError, AttributeError, KeyError, OSError):
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
        matches = re.finditer(pattern, prompt, re.IGNORECASE)
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
                result = dnd_rag.search_rules_wiki(page, max_results=1)
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
