"""
Session Results Management Module

Handles session results, roll tracking, and result file generation for D&D sessions.
"""

import os
from typing import List, Dict, Any
from datetime import datetime
from src.utils.file_io import write_text_file

class StorySession:
    """Represents a single story session with results separate from narrative."""

    def __init__(self, story_name: str, session_date: str = None):
        """
        Initialize a story session.

        Args:
            story_name: Name of the story/session
            session_date: Date of the session (defaults to today)
        """
        self.story_name = story_name
        self.session_date = session_date or datetime.now().strftime("%Y-%m-%d")
        self.roll_results = []
        self.character_actions = []
        self.narrative_events = []
        self.recruiting_pool = []

    def add_roll_result(
        self,
        roll_data: Dict[str, Any] = None,
        **kwargs
    ):
        """
        Add a roll result to this session.

        Args:
            roll_data: Dictionary with roll information (character, action, roll_type,
                      roll_value, dc, outcome)
            **kwargs: Alternative way to pass roll data as keyword arguments

        Accepts either roll_data dict or keyword arguments:
            character, action, roll_type, roll_value, dc, outcome
        """
        data = roll_data if roll_data else kwargs
        roll_value = data['roll_value']
        dc = data['dc']

        self.roll_results.append(
            {
                "character": data['character'],
                "action": data['action'],
                "roll_type": data['roll_type'],
                "roll_value": roll_value,
                "dc": dc,
                "success": roll_value >= dc,
                "outcome": data['outcome'],
            }
        )

    def suggest_recruits_from_agents(
        self, story_manager, exclude_names: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Suggest recruit characters from existing character agents.

        Args:
            story_manager: EnhancedStoryManager instance
            exclude_names: Names to exclude from suggestions

        Returns:
            List of available recruit dictionaries
        """
        available_agents = []
        for name, consultant in story_manager.consultants.items():
            if name not in exclude_names:
                available_agents.append(
                    {
                        "name": name,
                        "class": consultant.profile.character_class.value,
                        "personality": consultant.profile.personality_summary,
                        "level": consultant.profile.level,
                    }
                )
        return available_agents


def create_session_results_file(
    series_path: str, session: StorySession
) -> str:
    """
    Create or append to session results file.

    If file exists on same day, appends new session results instead of
    overwriting.

    Args:
        series_path: Path to the story series directory
        session: StorySession instance with session data

    Returns:
        Path to the created or updated file
    """
    story_slug = session.story_name.lower().replace(' ', '_')
    filename = f"session_results_{session.session_date}_{story_slug}.md"
    filepath = os.path.join(series_path, filename)

    # Check if file exists - if so, append new session results
    file_exists = os.path.exists(filepath)

    if file_exists:
        # Append mode: read existing and add new section
        with open(filepath, "r", encoding="utf-8") as f:
            existing_content = f.read()

        # Build new session section to append
        append_content = "\n## Session Update\n"
        append_content += f"**Updated:** {datetime.now().strftime('%H:%M:%S')}\n\n"

        # Add roll results
        if session.roll_results:
            append_content += "### New Roll Results\n"
            for roll in session.roll_results:
                success_text = "SUCCESS" if roll['success'] else "FAILURE"
                append_content += f"""- **{roll['character']}** - {roll['action']}
  - Roll: {roll['roll_value']} vs DC {roll['dc']} - {success_text}
  - Outcome: {roll['outcome']}
"""

        # Add character actions
        if session.character_actions:
            append_content += "\n### New Character Actions\n"
            for action in session.character_actions:
                append_content += f"- {action}\n"

        write_text_file(filepath, existing_content + append_content)
        print(f"[SUCCESS] Appended to session results file: {filename}")
    else:
        # Create new file
        content = f"""# Session Results: {session.story_name}
**Date:** {session.session_date}

## Roll Results
"""
        for roll in session.roll_results:
            success_text = "SUCCESS" if roll['success'] else "FAILURE"
            content += f"""
### {roll['character']} - {roll['action']}
- **Roll Type:** {roll['roll_type']}
- **Roll Value:** {roll['roll_value']} vs DC {roll['dc']}
- **Result:** {success_text}
- **Outcome:** {roll['outcome']}
"""

        if session.recruiting_pool:
            content += "\n## Available Recruits\n"
            for recruit in session.recruiting_pool:
                content += f"- **{recruit['name']}** ({recruit['class']}) - "
                content += f"{recruit['personality']}\n"

        content += """
## Character Actions
"""
        for action in session.character_actions:
            content += f"- {action}\n"

        write_text_file(filepath, content)
        print(f"[SUCCESS] Created session results file: {filename}")

    return filepath
