"""
Spell and Ability Lookup Helper

Thin wrapper around RAGSystem.get_rules_context_for_prompt.
Retained for backward compatibility with existing callers.
"""

from src.ai.availability import RAG_AVAILABLE, get_rag_system


def lookup_spells_and_abilities(prompt: str) -> str:
    """
    Look up D&D spells and abilities mentioned in a prompt.

    Delegates to RAGSystem.get_rules_context_for_prompt which extracts
    capitalised entity names dynamically and queries the rules wiki.

    Args:
        prompt: Text that may contain spell/ability names

    Returns:
        Formatted context string with spell/ability descriptions, or empty string
    """
    if not RAG_AVAILABLE:
        return ""
    return get_rag_system().get_rules_context_for_prompt(prompt)
