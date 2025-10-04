"""
History Check Helper with RAG Integration

Provides campaign lore information when characters make successful History checks.
Integrates with wiki RAG system to fetch accurate campaign setting information.
"""

from typing import Optional, Dict, Any

try:
    from rag_system import get_rag_system
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


def handle_history_check(topic: str, check_result: int, character_name: str = None) -> Dict[str, Any]:
    """
    Handle a character's History check with RAG-enhanced lore retrieval.
    
    Args:
        topic: What the character is trying to recall (location, event, person, etc.)
        check_result: The d20 + modifier result
        character_name: Name of character making the check (optional)
        
    Returns:
        Dictionary with:
            - success: bool
            - dc: int (difficulty class that was needed)
            - information: str (what the character recalls)
            - source: str ('wiki' if from RAG, 'fallback' otherwise)
    """
    # Determine DC based on topic complexity
    dc = _estimate_dc_for_topic(topic)
    success = check_result >= dc
    
    if not success:
        return {
            'success': False,
            'check_result': check_result,
            'dc': dc,
            'information': f"You struggle to recall specific details about {topic}.",
            'source': 'failure'
        }
    
    # Try to get information from RAG system
    if RAG_AVAILABLE:
        rag_system = get_rag_system()
        if rag_system and rag_system.enabled:
            info = rag_system.get_history_check_info(topic, check_result)
            if info:
                char_prefix = f"{character_name} recalls: " if character_name else "You recall: "
                return {
                    'success': True,
                    'check_result': check_result,
                    'dc': dc,
                    'information': char_prefix + info,
                    'source': 'wiki',
                    'detail_level': _get_detail_level(check_result)
                }
    
    # Fallback if RAG not available or no info found
    return {
        'success': True,
        'check_result': check_result,
        'dc': dc,
        'information': _generate_fallback_information(topic, check_result),
        'source': 'fallback',
        'detail_level': _get_detail_level(check_result)
    }


def _estimate_dc_for_topic(topic: str) -> int:
    """
    Estimate DC for recalling information about a topic.
    
    Common knowledge: DC 10
    Uncommon knowledge: DC 15
    Obscure knowledge: DC 20
    Ancient/Secret knowledge: DC 25
    """
    topic_lower = topic.lower()
    
    # Common topics (DC 10)
    common_keywords = ['tavern', 'inn', 'common', 'well-known', 'famous', 'recent']
    if any(word in topic_lower for word in common_keywords):
        return 10
    
    # Obscure topics (DC 20)
    obscure_keywords = ['ancient', 'lost', 'forgotten', 'secret', 'hidden', 'mysterious']
    if any(word in topic_lower for word in obscure_keywords):
        return 20
    
    # Very obscure (DC 25)
    very_obscure = ['primordial', 'primeval', 'legendary', 'mythical', 'forbidden']
    if any(word in topic_lower for word in very_obscure):
        return 25
    
    # Default: Uncommon knowledge (DC 15)
    return 15


def _get_detail_level(check_result: int) -> str:
    """Determine level of detail based on check result."""
    if check_result < 10:
        return 'vague'
    elif check_result < 15:
        return 'basic'
    elif check_result < 20:
        return 'detailed'
    else:
        return 'comprehensive'


def _generate_fallback_information(topic: str, check_result: int) -> str:
    """
    Generate basic information when RAG system is unavailable.
    """
    detail_level = _get_detail_level(check_result)
    
    if detail_level == 'vague':
        return f"You have heard of {topic} before, but can't recall specific details."
    elif detail_level == 'basic':
        return f"You know some basic facts about {topic}. [DM provides 1-2 key facts]"
    elif detail_level == 'detailed':
        return f"You recall quite a bit about {topic}. [DM provides 3-4 significant details]"
    else:  # comprehensive
        return f"Your knowledge of {topic} is extensive. [DM provides comprehensive information including history, significance, and connections]"


def search_lore(query: str, pages_to_search: list = None) -> Optional[str]:
    """
    Direct lore search function for DMs to look up campaign information.
    
    Args:
        query: What to search for
        pages_to_search: Optional list of specific pages to search
        
    Returns:
        Formatted lore information or None if not found
    """
    if not RAG_AVAILABLE:
        return "⚠️  RAG system not available. Install with: pip install requests beautifulsoup4"
    
    rag_system = get_rag_system()
    if not rag_system or not rag_system.enabled:
        return "⚠️  RAG system not enabled. Set RAG_ENABLED=true in .env"
    
    if not pages_to_search:
        # Try to search the query term directly as a page
        return rag_system.get_context_for_location(query)
    
    return rag_system.get_context_for_query(query, pages_to_search)


# Example usage for DMs
def demo_history_check():
    """Demo function showing how to use history checks with RAG."""
    print("=== History Check Demo ===\n")
    
    # Example 1: Basic check
    result = handle_history_check("Tal'Dorei", check_result=18, character_name="Lysara")
    print(f"Check Result: {result['check_result']} vs DC {result['dc']}")
    print(f"Success: {result['success']}")
    print(f"Information: {result['information']}")
    print(f"Source: {result['source']}\n")
    
    # Example 2: Failed check
    result = handle_history_check("Ancient Primordial Ruins", check_result=12)
    print(f"Check Result: {result['check_result']} vs DC {result['dc']}")
    print(f"Success: {result['success']}")
    print(f"Information: {result['information']}\n")
    
    # Example 3: Direct lore search
    print("=== Direct Lore Search ===")
    lore = search_lore("Whitestone", pages_to_search=["Whitestone", "Tal'Dorei"])
    if lore:
        print(lore[:200] + "...")


if __name__ == "__main__":
    demo_history_check()
