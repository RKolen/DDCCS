"""
Spell Highlighting System for D&D Stories

This module provides automatic highlighting of spell names in story text.
Spell names are wrapped in bold markdown (**spell name**) for better readability.

Detection Strategy:
- Pattern matching for common spell contexts (cast, casts, casting, uses, channels)
- Capitalized words/phrases in spell contexts
- Integration with RAG system for official D&D 5e spells (future enhancement)
"""

import re
from typing import List, Set


# Common spell-related context words
SPELL_CONTEXTS = [
    r'\bcast(?:s|ing)?\b',
    r'\bchannels?\b',
    r'\binvokes?\b',
    r'\bconjures?\b',
    r'\bsummons?\b',
    r'\bweaves?\b',
    r'\bpreps?\b',
    r'\bprepares?\b',
    r'\bcompletes?\b',
    r'\bconcentrates? on\b',
    r'\bmaintains?\b',
    r'\breleases?\b',
]

# Pattern to match capitalized spell-like names after spell contexts
# Matches: "casts Fireball", "channels Divine Smite", "uses Eldritch Blast"
# Matches 1-3 capitalized words after spell context
SPELL_PATTERN = re.compile(
    r'(?P<context>' + '|'.join(SPELL_CONTEXTS) + r')\s+(?P<spell>[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})',
    re.IGNORECASE
)

# Pattern to match spell names in parentheses (already formatted by storytellers)
# Matches: "(Fireball)", "(Divine Smite)"
PARENTHETICAL_SPELL = re.compile(r'\(([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\)')

# Common false positives (character names, places, etc.) that should NOT be highlighted
# Add more as needed based on your campaign
FALSE_POSITIVES = {
    'The', 'A', 'An', 'Their', 'His', 'Her', 'My', 'Your',
    'He', 'She', 'They', 'I', 'We', 'You',
}


def highlight_spells_in_text(text: str, known_spells: Set[str] = None) -> str:
    """
    Highlight spell names in story text by wrapping them in bold markdown.
    
    Args:
        text: Story text to process
        known_spells: Optional set of known spell names for more accurate matching
        
    Returns:
        Text with spell names wrapped in **bold**
        
    Example:
        >>> text = "Elara casts Fireball at the goblin."
        >>> highlight_spells_in_text(text)
        "Elara casts **Fireball** at the goblin."
    """
    if not text:
        return text
    
    known_spells = known_spells or set()
    result = text
    highlighted_spells = set()
    
    # First pass: Find spells in spell contexts (cast, channels, etc.)
    def replace_spell_context(match):
        context = match.group('context')
        spell_full = match.group('spell')
        
        # Split spell into words and try different combinations
        # "Divine Smite Through His" -> try "Divine Smite", then "Divine"
        words = spell_full.split()
        spell = None
        
        # Try 2-word combinations first (most spells are 1-2 words)
        if len(words) >= 2:
            two_word = ' '.join(words[:2])
            # Check if this looks like a spell
            if (two_word.lower() in {s.lower() for s in known_spells} or
                words[1].lower().endswith(('bolt', 'blast', 'ray', 'ward', 'shield', 'strike', 'smite', 'touch', 'word', 'hand', 'wall', 'arrow', 'missile'))):
                spell = two_word
        
        # Try single word if no 2-word match
        if not spell and len(words) >= 1:
            one_word = words[0]
            # Check if this looks like a spell
            if (one_word.lower() in {s.lower() for s in known_spells} or
                one_word.lower().endswith(('bolt', 'blast', 'ray', 'ward', 'shield', 'strike', 'smite', 'touch', 'ball', 'storm', 'wave'))):
                spell = one_word
        
        # No spell found
        if not spell or spell in FALSE_POSITIVES:
            return match.group(0)
        
        # Skip if already highlighted
        if spell.lower() in highlighted_spells:
            return match.group(0)
        
        highlighted_spells.add(spell.lower())
        # Return context + highlighted spell + rest of the matched text
        rest = spell_full[len(spell):]
        return f"{context} **{spell}**{rest}"
    
    result = SPELL_PATTERN.sub(replace_spell_context, result)
    
    # Second pass: Find spells in parentheses (common storytelling convention)
    def replace_parenthetical_spell(match):
        spell = match.group(1)
        
        # Skip false positives
        if spell in FALSE_POSITIVES:
            return match.group(0)
        
        # Skip if already highlighted
        if spell.lower() in highlighted_spells:
            return match.group(0)
        
        highlighted_spells.add(spell.lower())
        return f"(**{spell}**)"
    
    result = PARENTHETICAL_SPELL.sub(replace_parenthetical_spell, result)
    
    return result


def extract_known_spells_from_characters(characters: List[dict]) -> Set[str]:
    """
    Extract all known spells from character profiles.
    
    Args:
        characters: List of character profile dictionaries
        
    Returns:
        Set of known spell names
    """
    known_spells = set()
    
    for char in characters:
        # From character sheet if available
        if 'character_sheet' in char:
            sheet = char['character_sheet']
            if 'known_spells' in sheet:
                known_spells.update(spell.lower() for spell in sheet['known_spells'])
        
        # From spellcasting_notes in profile
        if 'spellcasting_notes' in char:
            # Extract spell names from notes (simple pattern matching)
            notes = char['spellcasting_notes']
            # Look for capitalized words that might be spells
            potential_spells = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', notes)
            known_spells.update(spell.lower() for spell in potential_spells)
    
    return known_spells


def highlight_spells_in_story_sections(story_data: dict, known_spells: Set[str] = None) -> dict:
    """
    Apply spell highlighting to all narrative sections of a story.
    
    Args:
        story_data: Story dictionary with various sections
        known_spells: Optional set of known spell names
        
    Returns:
        Story dictionary with highlighted spell names
    """
    if not story_data:
        return story_data
    
    # Sections that should have spell highlighting
    narrative_sections = [
        'story_narrative',
        'narrative',
        'session_summary',
        'combat_narrative',
        'scene_description',
    ]
    
    for section in narrative_sections:
        if section in story_data and isinstance(story_data[section], str):
            story_data[section] = highlight_spells_in_text(story_data[section], known_spells)
    
    return story_data


# Example usage and testing
if __name__ == "__main__":
    # Test cases
    test_texts = [
        "Elara casts Fireball at the approaching goblins.",
        "The paladin channels Divine Smite through his weapon.",
        "She uses Eldritch Blast to attack from range.",
        "The wizard prepares Counterspell, ready to interrupt.",
        "He concentrates on Haste, maintaining the spell.",
        "The cleric invokes Healing Word (2nd level) to save his ally.",
        "With a gesture, she summons a Wall of Fire.",
    ]
    
    print("Spell Highlighting Test:\n")
    for text in test_texts:
        highlighted = highlight_spells_in_text(text)
        if highlighted != text:
            print(f"Original:  {text}")
            print(f"Highlighted: {highlighted}")
            print()
