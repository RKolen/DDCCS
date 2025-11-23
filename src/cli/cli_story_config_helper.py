"""
Story Configuration Helper Module

Handles building story configuration context for AI generation,
including party loading, NPC retrieval, and previous story analysis.
"""

import os
from typing import List, Dict, Any, Optional
from src.cli.party_config_manager import load_party_with_profiles
from src.utils.npc_lookup_helper import load_relevant_npcs_for_prompt
from src.utils.file_io import read_text_file


def _extract_locations(story_text: str) -> Optional[str]:
    """Extract location mention from story text by looking for capitalized place names."""
    # Extract potential locations by looking for capitalized words that appear in story
    # Common patterns: "the X", "at X", "in X", "to X" where X is capitalized
    words = story_text.split()
    locations = []

    for i, word in enumerate(words):
        # Look for capitalized words (likely proper nouns/locations)
        if word and word[0].isupper() and len(word) > 2:
            # Check context - likely location if preceded by "the", "at", "in", "to"
            if i > 0:
                prev_word = words[i - 1].lower()
                if prev_word in ['the', 'at', 'in', 'to', 'from', 'near']:
                    locations.append(word.strip('.,;:!?'))

    if locations:
        # Return the most recent/last mentioned location
        return f"Previous scene: {locations[-1]}"
    return None


def _extract_mentioned_names(story_text: str, names: List[str], label: str) -> Optional[str]:
    """Extract names mentioned in story text."""
    if not names:
        return None
    mentioned = [name for name in names if name.lower() in story_text]
    if mentioned:
        return f"{label}: {', '.join(mentioned)}"
    return None


def extract_context_from_stories(
    workspace_path: str, campaign_dir: str, story_files: List[str],
    party_names: Optional[List[str]] = None, npc_names: Optional[List[str]] = None
) -> str:
    """Extract location and setting context from previous stories."""
    context_parts = []
    stories_base = os.path.join(workspace_path, "game_data", "campaigns")

    # Read most recent story files
    md_files = [
        f for f in story_files if f.endswith('.md') and
        not any(f.startswith(prefix) for prefix in
               ['character_development_', 'story_hooks_', 'session_results_'])
    ]

    for story_file in sorted(md_files)[-2:]:
        try:
            story_path = os.path.join(stories_base, campaign_dir, story_file)
            if not os.path.exists(story_path):
                continue

            content = read_text_file(story_path)
            story_text = " ".join(content.split('\n')[:10]).lower()

            # Extract locations
            location = _extract_locations(story_text)
            if location:
                context_parts.append(location)

            # Extract mentioned names
            if party_names:
                parties = _extract_mentioned_names(story_text, party_names, "Party")
                if parties:
                    context_parts.append(parties)

            if npc_names:
                npcs = _extract_mentioned_names(story_text, npc_names, "NPCs")
                if npcs:
                    context_parts.append(npcs)
        except (OSError, ValueError):
            pass

    return ". ".join(context_parts) if context_parts else ""


def build_story_config(
    workspace_path: str,
    series_name: Optional[str],
    campaign_dir: Optional[str],
    previous_stories: Optional[List[str]],
    story_prompt: str,
) -> Dict[str, Any]:
    """Build story configuration with context."""
    story_config: Dict[str, Any] = {}

    if not series_name or not campaign_dir:
        return story_config

    # Load party members and extract names
    party_names = []
    try:
        party_chars = load_party_with_profiles(campaign_dir, workspace_path)
        story_config["party_characters"] = party_chars
        party_names = list(party_chars.keys())
    except (ImportError, OSError, ValueError):
        pass

    # Load relevant NPCs for this prompt and extract names
    npc_names = []
    try:
        known_npcs = load_relevant_npcs_for_prompt(story_prompt, workspace_path)
        story_config["known_npcs"] = known_npcs
        npc_names = [npc.get("name", "") for npc in known_npcs]
    except (ImportError, OSError, ValueError):
        pass

    # Extract context from previous stories with dynamic data
    if previous_stories and (party_names or npc_names):
        prev_context = extract_context_from_stories(
            workspace_path, campaign_dir, previous_stories,
            party_names=party_names, npc_names=npc_names
        )
        if prev_context:
            story_config["campaign_context"] = prev_context

    return story_config


def display_story_prompt_guidance(story_type: str):
    """Display guidance for story prompt input.

    Args:
        story_type: Type of story (initial or continuation)
    """
    if story_type == "initial":
        print("\nDescribe the story you want to create.")
        print("Example: 'The party arrives at a mysterious inn during a storm'")
    else:
        print("\nDescribe the story continuation.")
        print("Example: 'A courier arrives with urgent news'")
