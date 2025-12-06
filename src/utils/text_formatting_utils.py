"""
Text Formatting Utilities

Handles text wrapping and formatting for story narratives.
"""

import textwrap
import re
from typing import Optional
from src.utils.spell_highlighter import (
    highlight_spells_in_text,
    extract_spells_from_prompt,
)


def _wrap_preserving_markdown(text: str, width: int = 80) -> str:
    """Wrap text while preserving markdown formatting (bold, italics, etc).

    Prevents line breaks inside markdown-wrapped text like **spell names**.

    Args:
        text: Text to wrap
        width: Maximum line width

    Returns:
        Wrapped text with markdown preserved
    """
    # Split by paragraphs first
    paragraphs = text.split("\n\n")
    wrapped_paragraphs = []
    markdown_pattern = re.compile(r"\*\*([^*]+)\*\*")

    for para in paragraphs:
        if para.strip().startswith("#") or para.strip().startswith("**"):
            wrapped_paragraphs.append(para)
            continue

        # Replace markdown-wrapped content with placeholders
        wrapped_paragraphs.append(_wrap_single_paragraph(para, markdown_pattern, width))

    return "\n\n".join(wrapped_paragraphs)


def _wrap_single_paragraph(para: str, pattern, width: int) -> str:
    """Wrap single paragraph while preserving markdown."""
    placeholders = {}
    counter = [0]

    def replace_with_placeholder(match):
        placeholder = f"__MARKDOWN_{counter[0]}__"
        placeholders[placeholder] = match.group(0)
        counter[0] += 1
        return placeholder

    para_with_placeholders = pattern.sub(replace_with_placeholder, para)
    wrapped = textwrap.fill(para_with_placeholders.strip(), width=width)

    for placeholder, original in placeholders.items():
        wrapped = wrapped.replace(placeholder, original)

    return wrapped


def wrap_narrative_text(
    text: str,
    width: int = 80,
    apply_spell_highlighting: bool = True,
    known_spells: "Optional[set]" = None,
    prompt: Optional[str] = None,
) -> str:
    """
    Wrap narrative text to specified width while preserving paragraphs.
    Optionally applies spell name highlighting.

    Args:
        text (str): The text to wrap
        width (int): Maximum line width (default 80 characters)
        apply_spell_highlighting (bool): Whether to highlight spell names (default True)
        known_spells (set): Set of known spell names for better matching
        prompt (str): User prompt to extract spells from (overrides known_spells)

    Returns:
        str: Text wrapped to specified width with optional spell highlighting
    """
    # Extract spells from prompt if provided (takes precedence)
    if prompt and apply_spell_highlighting:
        known_spells = extract_spells_from_prompt(prompt)

    # Apply spell highlighting first if requested
    if apply_spell_highlighting:
        text = highlight_spells_in_text(text, known_spells)

    # Wrap while preserving markdown formatting
    return _wrap_preserving_markdown(text, width=width)
