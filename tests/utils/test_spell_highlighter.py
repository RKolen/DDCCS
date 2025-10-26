"""Unit tests for src.utils.spell_highlighter."""

from typing import List, Dict

from test_helpers import setup_test_environment, import_module


setup_test_environment()

sp_mod = import_module("src.utils.spell_highlighter")
highlight_spells_in_text = sp_mod.highlight_spells_in_text
extract_known_spells_from_characters = sp_mod.extract_known_spells_from_characters
highlight_spells_in_story_sections = sp_mod.highlight_spells_in_story_sections


def test_highlight_simple_and_parenthetical() -> None:
    """Simple spell contexts and parenthetical spells should be highlighted."""
    text = "Elara casts Fireball at the goblin. The cleric says (Divine Smite) under his breath."
    out = highlight_spells_in_text(text)
    assert "**Fireball**" in out
    assert "(**Divine Smite**)" in out


def test_extract_known_spells_from_profiles() -> None:
    """Known spells should be pulled from character sheet and notes."""
    characters: List[Dict] = [
        {"character_sheet": {"known_spells": ["Fireball", "Eldritch Blast"]}},
        {"spellcasting_notes": "Learnt Misty Step during training."},
    ]

    known = extract_known_spells_from_characters(characters)
    # Lowercased in the implementation
    assert "fireball" in known
    assert "eldritch blast" in known
    assert "misty step" in known


def test_highlight_spells_in_story_sections() -> None:
    """Applying highlighting to story sections should modify the narrative fields."""
    story = {"story_narrative": "He casts Fireball as the orcs charge."}
    out = highlight_spells_in_story_sections(story, known_spells={"fireball"})
    assert "**Fireball**" in out["story_narrative"]
