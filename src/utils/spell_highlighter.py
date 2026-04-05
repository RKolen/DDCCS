"""
Spell Highlighting System for D&D Stories

This module provides automatic highlighting of spell names in story text.
Spell names are wrapped in bold markdown (**spell name**) for better readability.

Detection Strategy:
- Known spells from character profiles are highlighted exactly.
- Custom/homebrew spells from the SpellRegistry are always highlighted.
- Pattern matching detects common spell contexts (cast, channels, uses, etc.)
  as a fallback when no known spell list is provided.
"""

import re
from typing import List, Optional, Set

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


def _get_registry_spell_names() -> Set[str]:
    """Get all custom spell names from the registry (graceful no-op on failure).

    Returns:
        Set of lowercase name variants from the custom spell registry,
        or an empty set if the registry cannot be loaded.
    """
    try:
        from src.spells.spell_registry import get_spell_registry  # pylint: disable=import-outside-toplevel
        return get_spell_registry().get_all_spell_names()
    except (ImportError, OSError, KeyError, ValueError):
        return set()


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

    spells: Set[str] = set()
    registry_names = _get_registry_spell_names()

    for match in SPELL_PATTERN.finditer(prompt):
        spell_full = match.group("spell")
        words = spell_full.split()

        for spell_candidate in [
            " ".join(words[:2]) if len(words) >= 2 else words[0],
            words[0],
        ]:
            if spell_candidate and spell_candidate not in FALSE_POSITIVES:
                if spell_candidate.lower() in registry_names:
                    spells.add(spell_candidate.title())
                else:
                    spells.add(spell_candidate.title())
                break

    return spells


def highlight_spells_in_text(text: str, known_spells: Optional[Set[str]] = None) -> str:
    """Highlight spell names in story text by wrapping them in bold markdown.

    Priority order:
    1. If known_spells provided, highlight those exactly.
    2. Always additionally highlight custom spells from the registry.
    3. Fall back to pattern-based detection for any remaining contexts.

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
    registry_names = _get_registry_spell_names()

    # Merge character-known spells with registry spells for highlighting
    all_known = known_spells | registry_names
    result_text = text
    highlighted_spells: Set[str] = set()

    # Pass 1: Highlight all known/registry spells by exact name match
    if all_known:
        for spell in sorted(all_known, key=len, reverse=True):
            if spell.lower() in highlighted_spells:
                continue
            if spell in FALSE_POSITIVES:
                continue
            pattern = re.compile(
                r"(?<!\*)\b" + re.escape(spell) + r"\b(?!\*)", re.IGNORECASE
            )

            def _make_replacer(matched_spell: str):
                def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
                    return f"**{match.group(0)}**"
                _ = matched_spell  # captured for clarity
                return _replace

            result_text = pattern.sub(_make_replacer(spell), result_text)
            highlighted_spells.add(spell.lower())

        # If we had known_spells (character list), skip pattern fallback
        if known_spells:
            return result_text

    # Pass 2: Pattern-based detection for remaining spell contexts
    def replace_spell_context(match: re.Match) -> str:  # type: ignore[type-arg]
        context = match.group("context")
        spell_full = match.group("spell")
        words = spell_full.split()
        spell = None

        if len(words) >= 2:
            two_word = " ".join(words[:2])
            if two_word.lower() in all_known or words[1].lower().endswith(
                ("bolt", "blast", "ray", "ward", "shield", "strike",
                 "smite", "touch", "word", "hand", "wall", "missile")
            ):
                spell = two_word

        if not spell and words:
            one_word = words[0]
            if one_word.lower() in all_known or one_word.lower().endswith(
                ("bolt", "blast", "ray", "ward", "shield", "strike",
                 "smite", "touch", "ball", "storm", "wave")
            ):
                spell = one_word

        if not spell or spell in FALSE_POSITIVES:
            return match.group(0)

        if spell.lower() in highlighted_spells:
            return match.group(0)

        highlighted_spells.add(spell.lower())
        rest = spell_full[len(spell):]
        return f"{context} **{spell}**{rest}"

    result_text = SPELL_PATTERN.sub(replace_spell_context, result_text)

    # Pass 3: Parenthetical spells
    def replace_parenthetical_spell(match: re.Match) -> str:  # type: ignore[type-arg]
        spell = match.group(1)
        if spell in FALSE_POSITIVES:
            return match.group(0)
        if spell.lower() in highlighted_spells:
            return match.group(0)
        # Only highlight if it is a registry spell or looks like a known spell
        if spell.lower() not in all_known:
            return match.group(0)
        highlighted_spells.add(spell.lower())
        return f"(**{spell}**)"

    result_text = PARENTHETICAL_SPELL.sub(replace_parenthetical_spell, result_text)

    return result_text


def extract_known_spells_from_characters(characters: List[dict]) -> Set[str]:
    """Extract all known spells from character profiles.

    Args:
        characters: List of character profile dictionaries

    Returns:
        Set of known spell names
    """
    known_spells: Set[str] = set()

    # Include custom registry spells
    known_spells.update(_get_registry_spell_names())

    for char in characters:
        if "character_sheet" in char:
            sheet = char["character_sheet"]
            if "known_spells" in sheet:
                known_spells.update(spell.lower() for spell in sheet["known_spells"])

        if "spellcasting_notes" in char:
            notes = char["spellcasting_notes"]
            potential_spells = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", notes)
            known_spells.update(spell.lower() for spell in potential_spells)

    return known_spells


def highlight_spells_in_story_sections(
    story_data: dict, known_spells: Optional[Set[str]] = None
) -> dict:
    """Apply spell highlighting to all narrative sections of a story.

    Args:
        story_data: Story dictionary with various sections
        known_spells: Optional set of known spell names

    Returns:
        Story dictionary with highlighted spell names
    """
    if not story_data:
        return story_data

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
