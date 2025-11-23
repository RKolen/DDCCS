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
    r"\bcast(?:s|ing)?\b",
    r"\bchannels?\b",
    r"\binvokes?\b",
    r"\bconjures?\b",
    r"\bsummons?\b",
    r"\bweaves?\b",
    r"\bpreps?\b",
    r"\bprepares?\b",
    r"\bcompletes?\b",
    r"\bconcentrates? on\b",
    r"\bmaintains?\b",
    r"\breleases?\b",
]

# Pattern to match capitalized spell-like names after spell contexts
# Matches: "casts Fireball", "channels Divine Smite", "uses Eldritch Blast"
# Also matches lowercase: "prepares fireball", "cast detect magic"
# Also matches articles: "prepares a fireball", "casts an Eldritch Blast"
# Lookahead prevents matching following action words (e.g., "fireball and" -> "fireball")
# Matches 1-2 words after spell context (capitalized or lowercase)
SPELL_PATTERN = re.compile(
    r"(?P<context>"
    + "|".join(SPELL_CONTEXTS)
    + r")\s+(?:a\s+|an\s+|the\s+)?(?P<spell>\b[A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+)?\b)"
    + r"(?=\s*(?:[,.\"]|and\b|to\b|the\b|in\b|on\b|$))",
    re.IGNORECASE,
)

# Pattern to match spell names in parentheses (already formatted by storytellers)
# Matches: "(Fireball)", "(Divine Smite)"
PARENTHETICAL_SPELL = re.compile(r"\(([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\)")

# Common false positives (character names, places, etc.) that should NOT be highlighted
# Add more as needed based on your campaign
FALSE_POSITIVES = {
    "The",
    "A",
    "An",
    "Their",
    "His",
    "Her",
    "My",
    "Your",
    "He",
    "She",
    "They",
    "I",
    "We",
    "You",
}


def extract_spells_from_prompt(prompt: str) -> Set[str]:
    """Extract spell/ability names mentioned in a user prompt.

    Searches for spells/abilities in spell contexts (casts, channels, uses, etc.)
    and returns the set of identified spells for use in highlighting.
    Capitalizes spell names properly (Fireball, Detect Magic, etc.).

    Args:
        prompt: User prompt text (e.g., "aragorn shoots an arrow, gandalf casts
                fireball")

    Returns:
        Set of spell/ability names found in the prompt

    Example:
        >>> extract_spells_from_prompt("aragorn shoots a fireball")
        {'Fireball'}
    """
    if not prompt:
        return set()

    spells = set()

    # Find all spell contexts and their following spell names
    for match in SPELL_PATTERN.finditer(prompt):
        spell_full = match.group("spell")
        words = spell_full.split()

        # Try to find valid spell name (1-3 words)
        # Prioritize 2-word spells, then 1-word
        for spell_candidate in [
            " ".join(words[:2]) if len(words) >= 2 else words[0],
            words[0],
        ]:
            if spell_candidate and spell_candidate not in FALSE_POSITIVES:
                # Capitalize spell name properly (Title Case)
                spell_title = spell_candidate.title()
                spells.add(spell_title)
                break

    return spells


def highlight_spells_in_text(text: str, known_spells: Set[str] = None) -> str:
    """
    Highlight spell names in story text by wrapping them in bold markdown.

    When known_spells is provided (from user prompt), ONLY those spells are highlighted.
    When known_spells is empty, falls back to pattern-based detection.

    Args:
        text: Story text to process
        known_spells: Optional set of known spell names for more accurate matching

    Returns:
        Text with spell names wrapped in **bold**

    Example:
        >>> text = "Elara casts Fireball at the goblin."
        >>> highlight_spells_in_text(text, {"Fireball"})
        "Elara casts **Fireball** at the goblin."
    """
    if not text:
        return text

    known_spells = known_spells or set()
    result_text = text
    highlighted_spells = set()

    # If we have known spells from the prompt, ONLY highlight those
    # This prevents false positives like "arrow" being highlighted
    if known_spells:
        for spell in known_spells:
            if spell.lower() in highlighted_spells:
                continue

            # Create case-insensitive pattern to find the spell in text
            # Use word boundaries to avoid partial matches
            # But avoid matching if already wrapped in ** (already highlighted)
            pattern = re.compile(
                r"(?<!\*)\b" + re.escape(spell) + r"\b(?!\*)",
                re.IGNORECASE
            )

            def replace_known_spell(match):
                return f"**{match.group(0)}**"

            result_text = pattern.sub(replace_known_spell, result_text)
            highlighted_spells.add(spell.lower())

        return result_text

    # Fallback: Pattern-based detection when no known spells provided
    def replace_spell_context(match):
        context = match.group("context")
        spell_full = match.group("spell")

        # Split spell into words and try different combinations
        # "Divine Smite Through His" -> try "Divine Smite", then "Divine"
        words = spell_full.split()
        spell = None

        # Try 2-word combinations first (most spells are 1-2 words)
        if len(words) >= 2:
            two_word = " ".join(words[:2])
            # Check if this looks like a spell
            if two_word.lower() in {s.lower() for s in known_spells} or words[
                1
            ].lower().endswith(
                (
                    "bolt",
                    "blast",
                    "ray",
                    "ward",
                    "shield",
                    "strike",
                    "smite",
                    "touch",
                    "word",
                    "hand",
                    "wall",
                    "missile",
                )
            ):
                spell = two_word

        # Try single word if no 2-word match
        if not spell and len(words) >= 1:
            one_word = words[0]
            # Check if this looks like a spell
            if one_word.lower() in {
                s.lower() for s in known_spells
            } or one_word.lower().endswith(
                (
                    "bolt",
                    "blast",
                    "ray",
                    "ward",
                    "shield",
                    "strike",
                    "smite",
                    "touch",
                    "ball",
                    "storm",
                    "wave",
                )
            ):
                spell = one_word

        # No spell found
        if not spell or spell in FALSE_POSITIVES:
            return match.group(0)

        # Skip if already highlighted
        if spell.lower() in highlighted_spells:
            return match.group(0)

        highlighted_spells.add(spell.lower())
        # Return context + highlighted spell + rest of the matched text
        rest = spell_full[len(spell) :]
        return f"{context} **{spell}**{rest}"

    result_text = SPELL_PATTERN.sub(replace_spell_context, result_text)

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

    result_text = PARENTHETICAL_SPELL.sub(replace_parenthetical_spell, result_text)

    return result_text


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
        if "character_sheet" in char:
            sheet = char["character_sheet"]
            if "known_spells" in sheet:
                known_spells.update(spell.lower() for spell in sheet["known_spells"])

        # From spellcasting_notes in profile
        if "spellcasting_notes" in char:
            # Extract spell names from notes (simple pattern matching)
            notes = char["spellcasting_notes"]
            # Look for capitalized words that might be spells
            potential_spells = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", notes)
            known_spells.update(spell.lower() for spell in potential_spells)

    return known_spells


def highlight_spells_in_story_sections(
    story_data: dict, known_spells: Set[str] = None
) -> dict:
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
        "story_narrative",
        "narrative",
        "session_summary",
        "combat_narrative",
        "scene_description",
    ]

    for section in narrative_sections:
        if section in story_data and isinstance(story_data[section], str):
            story_data[section] = highlight_spells_in_text(
                story_data[section], known_spells
            )

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
    for test_line in test_texts:
        highlighted = highlight_spells_in_text(test_line)
        if highlighted != test_line:
            print(f"Original:  {test_line}")
            print(f"Highlighted: {highlighted}")
            print()
