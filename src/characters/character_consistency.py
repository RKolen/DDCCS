"""
Character Consistency and Development Module

Handles character development tracking and consistency analysis.
This module is responsible for:
- Creating character development files
- Tracking character actions and reasoning
- Consistency checking against established character traits
- Generating development notes and suggestions
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime

def create_character_development_file(
    series_path: str,
    story_name: str,
    character_actions: List[Dict[str, str]],
    session_date: Optional[str] = None,
) -> str:
    """
    Create a separate file for character development suggestions.

    Args:
        series_path: Path to campaign folder
        story_name: Name of the story
        character_actions: List of character action dictionaries
        session_date: Date of session (defaults to today)
    """
    if session_date is None:
        session_date = datetime.now().strftime("%Y-%m-%d")

    filename = (
        f"character_development_{session_date}_"
        f"{story_name.lower().replace(' ', '_')}.md"
    )
    filepath = os.path.join(series_path, filename)

    content = f"""# Character Development: {story_name}
**Date:** {session_date}

## Character Actions & Reasoning

"""
    for action in character_actions:
        content += f"""### CHARACTER: {action.get('character', 'Unknown')}
**ACTION:** {action.get('action', 'No action recorded')}
**REASONING:** {action.get('reasoning', 'No reasoning provided')}

**Consistency Check:** {action.get('consistency', 'To be analyzed')}
**Development Notes:** {action.get('notes', 'No notes')}

---

"""

    with open(filepath, "w", encoding="utf-8") as dev_file:
        dev_file.write(content)

    print(f"[SUCCESS] Created character development file: {filename}")
    return filepath


def get_available_recruits(
    consultants: Dict[str, Any],
    exclude_characters: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Get available character agents for recruitment, excluding specified characters.

    Args:
        consultants: Dictionary of character consultants
        exclude_characters: List of character names to exclude

    Returns:
        List of available recruit dictionaries with character info
    """
    if exclude_characters is None:
        exclude_characters = []

    recruits = []
    for name, consultant in consultants.items():
        if name not in exclude_characters:
            recruits.append(
                {
                    "name": name,
                    "class": consultant.profile.character_class.value,
                    "level": consultant.profile.level,
                    "personality": consultant.profile.personality_summary,
                    "background": consultant.profile.background_story,
                }
            )
    return recruits
