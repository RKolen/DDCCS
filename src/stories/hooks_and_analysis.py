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
from src.utils.file_io import write_text_file, read_text_file
from src.utils.string_utils import sanitize_filename, get_session_date, get_time_only


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


def _build_unresolved_threads_section(hooks: Any, is_structured: bool) -> str:
    """Build unresolved threads section from hooks.

    Args:
        hooks: Either structured dict or list of hooks
        is_structured: Whether hooks is a dict

    Returns:
        Markdown content for unresolved threads
    """
    content = ""
    if is_structured:
        unresolved = hooks.get("unresolved_threads", [])
        for i, thread in enumerate(unresolved, 1):
            content += f"{i}. {thread}\n"
    else:
        for i, hook in enumerate(hooks, 1):
            content += f"{i}. {hook}\n"
    return content


def _build_npc_suggestions_section(npc_suggestions: List[Dict[str, Any]]) -> str:
    """Build NPC profile suggestions section.

    Args:
        npc_suggestions: List of NPC suggestions

    Returns:
        Markdown content for NPC suggestions
    """
    content = "\n## NPC Profile Suggestions\n\n"
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
        content += f"# This will create: game_data/npcs/{npc['filename']}\n"
        content += "```\n\n"
        content += (
            "This NPC could be developed as a recurring character with "
            "personality traits, relationships, and story hooks.\n\n"
        )
    return content


def create_story_hooks_file(
    series_path: str,
    story_name: str,
    hooks: Any,
    session_date: Optional[str] = None,
    npc_suggestions: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Create or append to story hooks file for future sessions.

    If file exists on same day, appends new content instead of overwriting.

    Args:
        series_path: Path to campaign folder
        story_name: Name of the story
        hooks: Either a Dict with AI-structured hooks or List of hook strings
        session_date: Date of session (defaults to today)
        npc_suggestions: Pre-detected NPC suggestions (if already scanned)
    """
    if session_date is None:
        session_date = get_session_date()

    filename = f"story_hooks_{session_date}_{sanitize_filename(story_name)}.md"
    filepath = os.path.join(series_path, filename)

    # Handle both structured dict (from AI) and simple list (from fallback)
    is_structured = isinstance(hooks, dict)
    if not is_structured and (not hooks or len(hooks) == 0):
        print("[WARNING] Empty hooks list provided to create_story_hooks_file")
        hooks = [
            "[Analyze story content to identify plot threads]",
            "[Review character actions for development opportunities]",
        ]

    # Check if file exists - if so, append new hooks section
    file_exists = os.path.exists(filepath)

    if file_exists:
        _append_to_hooks_file(filepath, hooks, is_structured)
    else:
        config = {
            "filepath": filepath,
            "story_name": story_name,
            "session_date": session_date,
            "hooks": hooks,
            "is_structured": is_structured,
            "npc_suggestions": npc_suggestions,
        }
        _create_new_hooks_file(config)

    return filepath


def _append_to_hooks_file(filepath: str, hooks: Any, is_structured: bool) -> None:
    """Append new hooks section to existing hooks file.

    Args:
        filepath: Path to the hooks file
        hooks: Either structured dict or list of hooks
        is_structured: Whether hooks is a dict
    """
    existing_content = read_text_file(filepath) or ""

    # Build new hooks section to append
    append_content = "\n## Updated Session Hooks\n"
    append_content += f"**Updated:** {get_time_only()}\n\n"

    # Add unresolved threads update
    unresolved_section = _build_unresolved_threads_section(hooks, is_structured)
    if unresolved_section:
        append_content += "### New Plot Threads\n"
        append_content += unresolved_section
        append_content += "\n"

    # Add updated session ideas if structured
    if is_structured:
        next_ideas = hooks.get("next_session_ideas", [])
        if next_ideas:
            append_content += "### Updated Session Ideas\n"
            for idea in next_ideas:
                append_content += f"- {idea}\n"
            append_content += "\n"

    write_text_file(filepath, existing_content + append_content)
    filename = os.path.basename(filepath)
    print(f"[SUCCESS] Appended to story hooks file: {filename}")


def _create_new_hooks_file(config: Dict[str, Any]) -> None:
    """Create a new story hooks file.

    Args:
        config: Configuration dict with keys:
            - filepath: Path to create file at
            - story_name: Name of the story
            - session_date: Session date string
            - hooks: Either structured dict or list of hooks
            - is_structured: Whether hooks is a dict
            - npc_suggestions: Optional NPC suggestions
    """
    filepath = config["filepath"]
    story_name = config["story_name"]
    session_date = config["session_date"]
    hooks = config["hooks"]
    is_structured = config["is_structured"]
    npc_suggestions = config["npc_suggestions"]

    content = f"""# Story Hooks & Future Sessions: {story_name}
**Date:** {session_date}

## Unresolved Plot Threads

"""

    # Add unresolved threads
    content += _build_unresolved_threads_section(hooks, is_structured)

    # Add NPC suggestions if provided
    if npc_suggestions:
        content += _build_npc_suggestions_section(npc_suggestions)

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

    filename = os.path.basename(filepath)
    print(f"[SUCCESS] Created story hooks file: {filename}")
    if npc_suggestions:
        print(f"   Added {len(npc_suggestions)} NPC profile suggestion(s)")
