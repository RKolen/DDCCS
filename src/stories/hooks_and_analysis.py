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

def create_story_hooks_file(
    series_path: str,
    story_name: str,
    hooks: List[str],
    session_date: Optional[str] = None,
    npc_suggestions: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Create a separate file for future story hooks and session suggestions.

    Args:
        series_path: Path to campaign folder
        story_name: Name of the story
        hooks: List of story hook strings
        session_date: Date of session (defaults to today)
        npc_suggestions: Pre-detected NPC suggestions (if already scanned)
    """
    if session_date is None:
        session_date = datetime.now().strftime("%Y-%m-%d")

    filename = (
        f"story_hooks_{session_date}_{story_name.lower().replace(' ', '_')}.md"
    )
    filepath = os.path.join(series_path, filename)

    content = f"""# Story Hooks & Future Sessions: {story_name}
**Date:** {session_date}

## Unresolved Plot Threads

"""
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

    content += """
## Potential Next Sessions

### Session Ideas
- [Future session idea based on current events]

### NPC Follow-ups
- [NPCs that need attention]

### Location Hooks
- [Places hinted at but not yet explored]

### Faction Developments
- [Faction activities and consequences]

"""

    write_text_file(filepath, content)

    print(f"[SUCCESS] Created story hooks file: {filename}")
    if npc_suggestions:
        print(f"   Added {len(npc_suggestions)} NPC profile suggestion(s)")

    return filepath
