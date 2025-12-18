"""Story Amender - Interactive Story Modification

Provides functionality to identify character action mismatches in stories
and suggest replacements with better-fitting characters based on class
abilities, personality, and prior actions.
"""

from typing import Dict, List, Optional, Any
from src.utils.file_io import read_text_file, write_text_file
from src.stories.character_fit_analyzer import suggest_character_amendment
from src.stories.character_action_analyzer import _build_character_name_patterns


def identify_character_actions(
    story_content: str,
    character_name: str,
) -> List[Dict[str, Any]]:
    """Identify specific action segments for a character in the story.

    Args:
        story_content: Full story text
        character_name: Name of the character to find actions for

    Returns:
        List of action segment dictionaries with text and line info
    """
    lines = story_content.split("\n")
    patterns = _build_character_name_patterns(character_name)
    actions = []

    for i, line in enumerate(lines):
        # Check if any pattern matches this line
        matches = any(pattern.search(line) for pattern in patterns)

        if not matches:
            continue

        # Extract context (current line and surrounding lines)
        start_idx = max(0, i - 1)
        end_idx = min(len(lines), i + 2)
        context_lines = lines[start_idx:end_idx]
        context_text = " ".join(context_lines).strip()

        if context_text:
            actions.append(
                {
                    "text": context_text,
                    "line_start": start_idx,
                    "line_end": end_idx,
                    "original_line": line,
                    "line_index": i,
                }
            )

    return actions


def analyze_amendments(
    actions: List[Dict[str, Any]],
    current_character: str,
    character_profiles: Dict[str, Dict[str, Any]],
    previous_actions_map: Optional[Dict[str, List[str]]] = None,
) -> List[Dict[str, Any]]:
    """Analyze identified actions for potential character amendments.

    Args:
        actions: List of identified action segments
        current_character: Name of the character currently performing actions
        character_profiles: Dict mapping names to profiles
        previous_actions_map: Dict mapping names to prior actions

    Returns:
        List of actions with amendment suggestions added
    """
    results = []
    for action in actions:
        suggestion = suggest_character_amendment(
            actual_character=current_character,
            action_text=action["text"],
            character_profiles=character_profiles,
            previous_actions_map=previous_actions_map,
        )

        if suggestion:
            action["suggestion"] = suggestion

        results.append(action)

    return results


def generate_amended_text(
    original_line: str,
    current_character: str,
    suggested_character: str,
) -> str:
    """Generate amended text by swapping characters.

    Args:
        original_line: The original line of text
        current_character: Name of the character to replace
        suggested_character: Name of the replacement character

    Returns:
        Amended line of text
    """
    # Try full name first
    amended = original_line.replace(current_character, suggested_character)

    # Try first name
    current_first = current_character.split()[0]
    suggested_first = suggested_character.split()[0]

    if current_first != current_character:
        amended = amended.replace(current_first, suggested_first)

    return amended


def apply_amendment_to_file(
    filepath: str,
    line_index: int,
    new_line: str,
) -> bool:
    """Apply a single line amendment to a story file.

    Args:
        filepath: Path to the story file
        line_index: Index of the line to replace
        new_line: The new text for that line

    Returns:
        True if successful, False otherwise
    """
    content = read_text_file(filepath)
    if not content:
        return False

    lines = content.split("\n")
    if 0 <= line_index < len(lines):
        lines[line_index] = new_line
        updated_content = "\n".join(lines)
        write_text_file(filepath, updated_content)
        return True

    return False
