"""
Story Parsing Utilities.

Utility functions for extracting information from story markdown files.
"""

import re
from typing import Dict, List

def extract_character_actions(content: str, character_names: List[str]) -> Dict[str, List[str]]:
    """
    Extract character actions from story content.

    Args:
        content: Story file content
        character_names: List of known character names

    Returns:
        Dictionary mapping character names to their actions
    """
    actions = {}

    # Look for Character Action Log sections
    action_pattern = (
        r"CHARACTER:\s*([^\n]+)\nACTION:\s*([^\n]+)"
        r"(?:\nREASONING:\s*([^\n]+))?"
    )
    matches = re.findall(action_pattern, content, re.MULTILINE)

    for match in matches:
        character = match[0].strip()
        action = match[1].strip()
        reasoning = match[2].strip() if len(match) > 2 else ""

        if character not in actions:
            actions[character] = []

        action_with_reasoning = (
            f"{action} (Reasoning: {reasoning})" if reasoning else action
        )
        actions[character].append(action_with_reasoning)

    # Also look for narrative mentions of characters
    for character_name in character_names:
        if character_name in content and character_name not in actions:
            # Find sentences mentioning this character
            sentences = re.findall(
                f"[^.!?]*{re.escape(character_name)}[^.!?]*[.!?]", content
            )
            if sentences:
                actions[character_name] = sentences[:3]  # Limit to first 3 mentions

    return actions


def extract_dc_requests(content: str) -> List[str]:
    """
    Extract DC suggestion requests from story content.

    Args:
        content: Story file content

    Returns:
        List of DC request strings
    """
    # Look for DC Suggestions Needed section
    dc_section_match = re.search(
        r"## DC Suggestions Needed\s*\n([^#]*)", content, re.MULTILINE
    )
    if not dc_section_match:
        return []

    dc_section = dc_section_match.group(1)

    # Extract individual requests (lines that aren't empty or just whitespace)
    requests = []
    for line in dc_section.split("\n"):
        line = line.strip()
        if line and not line.startswith("*") and line != "*":
            # Remove markdown formatting
            line = re.sub(r"[*_`]", "", line)
            requests.append(line)

    return requests
