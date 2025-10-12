"""
Text Formatting Utilities

Handles text wrapping and formatting for story narratives.
"""

import textwrap
from spell_highlighter import highlight_spells_in_text


def wrap_narrative_text(
    text: str,
    width: int = 80,
    apply_spell_highlighting: bool = True,
    known_spells: set = None,
) -> str:
    """
    Wrap narrative text to specified width while preserving paragraphs.
    Optionally applies spell name highlighting.

    Args:
        text (str): The text to wrap
        width (int): Maximum line width (default 80 characters)
        apply_spell_highlighting (bool): Whether to highlight spell names (default True)
        known_spells (set): Set of known spell names for better matching

    Returns:
        str: Text wrapped to specified width with optional spell highlighting
    """
    # Apply spell highlighting first if requested
    if apply_spell_highlighting:
        text = highlight_spells_in_text(text, known_spells)

    # Split into paragraphs
    paragraphs = text.split("\n\n")
    wrapped_paragraphs = []

    for para in paragraphs:
        # Skip if it's a heading or special line
        if para.strip().startswith("#") or para.strip().startswith("**"):
            wrapped_paragraphs.append(para)
        else:
            # Wrap the paragraph
            wrapped = textwrap.fill(para.strip(), width=width)
            wrapped_paragraphs.append(wrapped)

    return "\n\n".join(wrapped_paragraphs)
