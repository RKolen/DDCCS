"""
Story Hooks and Analysis Module

Handles story hooks generation, unresolved plot threads, and NPC suggestions.
This module is responsible for:
- Creating story hooks files with unresolved plot threads
- Generating NPC profile suggestions from story content
- Creating session ideas and follow-up opportunities
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.utils.file_io import write_text_file


def convert_ai_hooks_to_list(ai_hooks: Dict[str, Any]) -> List[str]:
    """
    Convert AI-generated hooks dictionary to hooks list.

    Args:
        ai_hooks: Dictionary with 'unresolved_threads' and/or
                  'next_session_ideas' keys

    Returns:
        Combined list of all hooks from both sections
    """
    hooks = []
    if ai_hooks.get("unresolved_threads"):
        hooks.extend(ai_hooks["unresolved_threads"])
    if ai_hooks.get("next_session_ideas"):
        hooks.extend(ai_hooks["next_session_ideas"])
    return hooks


def _build_hooks_content_from_dict(hooks_dict: Dict[str, Any]) -> str:
    """Build markdown content from structured hooks dictionary.

    Args:
        hooks_dict: Dictionary with AI-structured hooks

    Returns:
        Markdown content for hooks sections
    """
    content = ""

    # Add session ideas
    next_ideas = hooks_dict.get("next_session_ideas", [])
    if next_ideas:
        content += "### Session Ideas\n"
        for idea in next_ideas:
            content += f"- {idea}\n"
        content += "\n"

    # Add NPC follow-ups
    npc_followups = hooks_dict.get("npc_follow_ups", [])
    if npc_followups:
        content += "### NPC Follow-ups\n"
        for followup in npc_followups:
            content += f"- {followup}\n"
        content += "\n"

    # Add character-specific hooks
    char_hooks = hooks_dict.get("character_specific_hooks", {})
    if char_hooks:
        content += "### Character Development\n"
        for char_name, char_hook_list in char_hooks.items():
            content += f"#### {char_name}\n"
            for hook in char_hook_list:
                content += f"- {hook}\n"
            content += "\n"

    return content


def create_story_hooks_file(
    series_path: str,
    story_name: str,
    hooks: Any,
    session_date: Optional[str] = None,
    npc_suggestions: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Create a separate file for future story hooks and session suggestions.

    Args:
        series_path: Path to campaign folder
        story_name: Name of the story
        hooks: Either a Dict with AI-structured hooks or List of hook strings
        session_date: Date of session (defaults to today)
        npc_suggestions: Pre-detected NPC suggestions (if already scanned)
    """
    if session_date is None:
        session_date = datetime.now().strftime("%Y-%m-%d")

    filename = (
        f"story_hooks_{session_date}_{story_name.lower().replace(' ', '_')}.md"
    )
    filepath = os.path.join(series_path, filename)

    # Handle both structured dict (from AI) and simple list (from fallback)
    is_structured = isinstance(hooks, dict)
    if not is_structured and (not hooks or len(hooks) == 0):
        print("[WARNING] Empty hooks list provided to create_story_hooks_file")
        hooks = [
            "[Analyze story content to identify plot threads]",
            "[Review character actions for development opportunities]",
        ]

    content = f"""# Story Hooks & Future Sessions: {story_name}
**Date:** {session_date}

## Unresolved Plot Threads

"""

    # Handle structured dict from AI
    if is_structured:
        unresolved = hooks.get("unresolved_threads", [])
        for i, thread in enumerate(unresolved, 1):
            content += f"{i}. {thread}\n"
    else:
        # Handle simple list from fallback
        for i, hook in enumerate(hooks, 1):
            content += f"{i}. {hook}\n"

    # Add NPC suggestions if provided
    if npc_suggestions:
        content += "\n## NPC Profile Suggestions\n\n"
        content += (
            "The following NPCs appeared in this session and may "
            "warrant profile creation:\n\n"
        )

        for npc in npc_suggestions:
            content += f"### {npc['name']} ({npc['role']})\n\n"
            content += "**Context:** " + npc["context_excerpt"][:150] + "...\n\n"
            content += "**To create profile:**\n```python\n"
            content += f"# Generate profile for {npc['name']}\n"
            content += "npc_profile = story_manager.generate_npc_from_story(\n"
            content += f"    npc_name=\"{npc['name']}\",\n"
            content += "    context=story_text,\n"
            content += f"    role=\"{npc['role']}\"\n"
            content += ")\n"
            content += "story_manager.save_npc_profile(npc_profile)\n"
            content += (
                f"# This will create: game_data/npcs/{npc['filename']}\n"
            )
            content += "```\n\n"
            content += (
                "This NPC could be developed as a recurring character with "
                "personality traits, relationships, and story hooks.\n\n"
            )

    # Add Potential Next Sessions from structured AI data
    content += "\n## Potential Next Sessions\n\n"

    if is_structured:
        content += _build_hooks_content_from_dict(hooks)
    else:
        # Fallback template if not structured
        content += """### Session Ideas
- [Future session idea based on current events]

### NPC Follow-ups
- [NPCs that need attention]

### Location Hooks
- [Places hinted at but not yet explored]

### Faction Developments
- [Faction activities and consequences]
"""

    content += "\n"
    write_text_file(filepath, content)

    print(f"[SUCCESS] Created story hooks file: {filename}")
    if npc_suggestions:
        print(f"   Added {len(npc_suggestions)} NPC profile suggestion(s)")

    return filepath
