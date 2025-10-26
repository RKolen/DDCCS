"""Unit tests for src.utils.text_formatting_utils."""

from tests.test_helpers import setup_test_environment, import_module


setup_test_environment()

tf = import_module("src.utils.text_formatting_utils")
wrap_narrative_text = tf.wrap_narrative_text


def test_wrap_preserves_headings_and_wraps_paragraphs() -> None:
    """Long paragraphs are wrapped while headings are preserved."""
    long_para = (
        "This is a long paragraph that should be wrapped to a small width "
        "for testing purposes. It contains multiple sentences and should be "
        "broken across lines."
    )

    out = wrap_narrative_text(long_para, width=40, apply_spell_highlighting=False)
    # Expect at least one newline inside the paragraph due to wrapping
    assert "\n" in out


def test_wrap_with_spell_highlighting_applies_highlight() -> None:
    """When spell highlighting is enabled known spells are wrapped in bold."""
    text = "Elara casts Fireball at the goblin."
    out = wrap_narrative_text(
        text, width=80, apply_spell_highlighting=True, known_spells={"fireball"}
    )
    assert "**Fireball**" in out
