"""
NPC Lookup Helper Utility

Provides location-based NPC lookup for AI story generation. Matches NPCs to
story locations and extracts relevant NPC profiles to inject into AI prompts.

Functions:
- load_relevant_npcs_for_prompt(): Main entry point for NPC matching
- extract_location_keywords(): Parse location mentions from prompts
- match_npc_to_location(): Match NPCs by location or role
"""

from pathlib import Path
from typing import List, Dict, Any
from src.utils.path_utils import get_npcs_dir
from src.npcs.npc_agents import create_npc_agents


# Location keywords and their common role associations
LOCATION_TYPES = {
    "tavern": ["innkeeper", "bartender", "proprietor", "owner"],
    "inn": ["innkeeper", "proprietor", "owner", "manager"],
    "bar": ["bartender", "innkeeper", "proprietor"],
    "pub": ["bartender", "proprietor"],
    "castle": ["captain", "guard captain", "lord", "steward", "castellan"],
    "fortress": ["captain", "guard captain", "commander"],
    "guard_post": ["guard captain", "captain", "commander"],
    "blacksmith": ["blacksmith", "smith", "armorer"],
    "shop": ["merchant", "shopkeeper", "proprietor"],
    "market": ["merchant", "vendor", "trader"],
    "temple": ["cleric", "priest", "priestess", "acolyte"],
    "church": ["cleric", "priest", "priestess"],
    "library": ["scholar", "librarian", "sage"],
    "sage": ["sage", "scholar"],
    "wizard": ["wizard", "mage", "sorcerer", "archmage"],
}


def extract_location_keywords(prompt: str) -> List[str]:
    """
    Extract location keywords and place names from a story prompt.

    Looks for:
    - Named locations (capitalized words, phrases in quotes)
    - Common location types (tavern, inn, castle, etc.)
    - Location descriptors

    Args:
        prompt: Story prompt text to parse

    Returns:
        List of location keywords/names found in the prompt
    """
    keywords = []
    prompt_lower = prompt.lower()

    # Check for common location types
    for location_type in LOCATION_TYPES:
        if location_type in prompt_lower:
            keywords.append(location_type)

    # Extract capitalized proper nouns (likely place names)
    words = prompt.split()
    for i, word in enumerate(words):
        # Look for capitalized words that might be location names
        if word and word[0].isupper():
            # Skip if it's clearly not a location (short common words)
            if word.lower() not in ["the", "and", "or", "a", "an", "of", "is",
                                     "are", "at", "in"]:
                # Multi-word locations (e.g., "The Prancing Pony")
                full_name = word
                if i + 1 < len(words) and words[i + 1][0].isupper():
                    full_name = f"{word} {words[i + 1]}"
                keywords.append(full_name)

    return list(set(keywords))  # Remove duplicates


def match_npc_to_location(
    npc_profiles: List[Dict[str, Any]],
    location_keywords: List[str]
) -> List[Dict[str, Any]]:
    """
    Match NPC profile dicts to location keywords using notes and role fields.

    Matches by:
    1. Exact location name match in NPC notes field
    2. Role type match (e.g., innkeeper for tavern/inn locations)
    3. Proximity matching (if location keyword contains NPC location substring)

    Args:
        npc_profiles: List of NPC status dicts (from get_status())
        location_keywords: List of location keywords extracted from prompt

    Returns:
        List of dicts with matched NPC info: name, role, location, personality
    """
    matched_npcs = []

    for npc_status in npc_profiles:
        npc_notes = npc_status.get("notes", "").lower()
        npc_role = npc_status.get("role", "").lower()

        # Check each location keyword
        for keyword in location_keywords:
            keyword_lower = keyword.lower()

            # Check 1: Exact location match in notes
            if keyword_lower in npc_notes:
                matched_npcs.append({
                    "name": npc_status.get("name", "Unknown"),
                    "role": npc_status.get("role", "NPC"),
                    "personality": npc_status.get("personality", ""),
                    "location": keyword,
                    "notes": npc_status.get("notes", ""),
                })
                break  # Found match, move to next NPC

            # Check 2: Role type match for common locations
            if keyword_lower in LOCATION_TYPES:
                expected_roles = LOCATION_TYPES[keyword_lower]
                for role in expected_roles:
                    if role in npc_role:
                        matched_npcs.append({
                            "name": npc_status.get("name", "Unknown"),
                            "role": npc_status.get("role", "NPC"),
                            "personality": npc_status.get("personality", ""),
                            "location": keyword,
                            "notes": npc_status.get("notes", ""),
                        })
                        break
                if matched_npcs and matched_npcs[-1]["name"] == \
                   npc_status.get("name"):
                    break  # Found match, move to next NPC

    # Remove duplicates (same NPC matched multiple times)
    unique_npcs = {}
    for npc_info in matched_npcs:
        key = npc_info["name"]
        if key not in unique_npcs:
            unique_npcs[key] = npc_info

    return list(unique_npcs.values())


def load_relevant_npcs_for_prompt(
    prompt: str,
    workspace_path: str
) -> List[Dict[str, Any]]:
    """
    Load and match NPCs relevant to a story prompt.

    Main entry point for NPC lookup. Extracts location keywords from the
    prompt, loads all NPC profiles from game_data/npcs/, and matches them
    to the prompt's locations.

    Args:
        prompt: Story prompt text to analyze
        workspace_path: Path to workspace root directory

    Returns:
        List of matched NPC dicts with fields:
        - name: NPC name
        - role: NPC role/title
        - personality: Personality description
        - location: Associated location from prompt
        - notes: Additional NPC notes

    Returns empty list if no NPCs match or if NPC directory doesn't exist.
    """
    # Extract location keywords from prompt
    location_keywords = extract_location_keywords(prompt)

    if not location_keywords:
        return []

    # Load all NPC profiles
    npcs_dir = Path(get_npcs_dir(workspace_path))

    if not npcs_dir.exists():
        return []

    # Create NPC agents (loads all NPC JSON files)
    npc_agents = create_npc_agents(npcs_dir)

    if not npc_agents:
        return []

    # Match NPCs to locations
    matched_npcs = match_npc_to_location(
        [agent.get_status() for agent in npc_agents],
        location_keywords
    )

    return matched_npcs
