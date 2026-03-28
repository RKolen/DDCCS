"""
Session Results Management Module

Handles session results, roll tracking, and result file generation for D&D sessions.
"""

import os
from typing import List, Dict, Any, Optional
from src.stories.spotlight_types import SpotlightReport
from src.utils.file_io import write_text_file
from src.utils.string_utils import sanitize_filename, get_session_date, get_time_only


class StorySession:
    """Represents a single story session with results separate from narrative."""

    def __init__(self, story_name: str, session_date: Optional[str] = None):
        """
        Initialize a story session.

        Args:
            story_name: Name of the story/session
            session_date: Date of the session (defaults to today)
        """
        self.story_name = story_name
        self.session_date = session_date or get_session_date()
        self.roll_results: list[dict[str, Any]] = []
        self.character_actions: list[str] = []
        self.narrative_events: list[str] = []
        self.recruiting_pool: list[dict[str, Any]] = []
        self.spotlighted_characters: list[dict[str, Any]] = []

    def set_spotlight_from_report(
        self, report: SpotlightReport, max_characters: int = 3, max_npcs: int = 3
    ) -> None:
        """Populate spotlighted_characters from a SpotlightReport.

        Args:
            report: SpotlightReport instance from SpotlightEngine.
            max_characters: Maximum number of top characters to include.
            max_npcs: Maximum number of top NPCs to include.
        """
        self.spotlighted_characters = []
        for entry in report.top_characters(max_characters):
            self.spotlighted_characters.append({
                "name": entry.name,
                "entity_type": "character",
                "score": entry.score,
                "reasons": [s.description for s in entry.signals],
            })
        for entry in report.top_npcs(max_npcs):
            self.spotlighted_characters.append({
                "name": entry.name,
                "entity_type": "npc",
                "score": entry.score,
                "reasons": [s.description for s in entry.signals],
            })

    def add_roll_result(self, roll_data: Optional[Dict[str, Any]] = None, **kwargs):
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
        roll_value = data["roll_value"]
        dc = data["dc"]

        self.roll_results.append(
            {
                "character": data["character"],
                "action": data["action"],
                "roll_type": data["roll_type"],
                "roll_value": roll_value,
                "dc": dc,
                "success": roll_value >= dc,
                "outcome": data["outcome"],
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


def _format_spotlight_lines(entries: list) -> str:
    """Format spotlighted character entries as markdown list lines.

    Args:
        entries: List of spotlight dicts with name, entity_type, score, reasons.

    Returns:
        Formatted markdown string, or empty string when entries is empty.
    """
    if not entries:
        return ""
    lines = []
    for entry in entries:
        label = "NPC" if entry["entity_type"] == "npc" else "Character"
        reasons = "; ".join(entry["reasons"])
        lines.append(
            f"- **{entry['name']}** ({label}, score {entry['score']:.0f}): {reasons}"
        )
    return "\n".join(lines) + "\n"


def _build_append_content(session: StorySession) -> str:
    """Build the markdown block appended to an existing session results file.

    Args:
        session: StorySession with current session data.

    Returns:
        Formatted markdown string for appending.
    """
    content = "\n## Session Update\n"
    content += f"**Updated:** {get_time_only()}\n\n"

    if session.roll_results:
        content += "### New Roll Results\n"
        for roll in session.roll_results:
            success_text = "SUCCESS" if roll["success"] else "FAILURE"
            content += (
                f"- **{roll['character']}** - {roll['action']}\n"
                f"  - Roll: {roll['roll_value']} vs DC {roll['dc']} - {success_text}\n"
                f"  - Outcome: {roll['outcome']}\n"
            )

    if session.character_actions:
        content += "\n### New Character Actions\n"
        for action in session.character_actions:
            content += f"- {action}\n"

    if session.spotlighted_characters:
        content += "\n### Spotlighted Characters\n"
        content += _format_spotlight_lines(session.spotlighted_characters)

    return content


def _build_new_file_content(session: StorySession) -> str:
    """Build the full markdown content for a new session results file.

    Args:
        session: StorySession with current session data.

    Returns:
        Full formatted markdown string.
    """
    content = (
        f"# Session Results: {session.story_name}\n"
        f"**Date:** {session.session_date}\n\n## Roll Results\n"
    )

    for roll in session.roll_results:
        success_text = "SUCCESS" if roll["success"] else "FAILURE"
        content += (
            f"\n### {roll['character']} - {roll['action']}\n"
            f"- **Roll Type:** {roll['roll_type']}\n"
            f"- **Roll Value:** {roll['roll_value']} vs DC {roll['dc']}\n"
            f"- **Result:** {success_text}\n"
            f"- **Outcome:** {roll['outcome']}\n"
        )

    if session.recruiting_pool:
        content += "\n## Available Recruits\n"
        for recruit in session.recruiting_pool:
            content += f"- **{recruit['name']}** ({recruit['class']}) - "
            content += f"{recruit['personality']}\n"

    if session.spotlighted_characters:
        content += "\n## Spotlighted Characters\n"
        content += _format_spotlight_lines(session.spotlighted_characters)

    content += "\n## Character Actions\n"
    for action in session.character_actions:
        content += f"- {action}\n"

    return content


def create_session_results_file(series_path: str, session: StorySession) -> str:
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
    story_slug = sanitize_filename(session.story_name)
    filename = f"session_results_{session.session_date}_{story_slug}.md"
    filepath = os.path.join(series_path, filename)

    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            existing_content = f.read()
        write_text_file(filepath, existing_content + _build_append_content(session))
        print(f"[SUCCESS] Appended to session results file: {filename}")
    else:
        write_text_file(filepath, _build_new_file_content(session))
        print(f"[SUCCESS] Created session results file: {filename}")

    return filepath


def populate_session_from_ai_results(
    session: "StorySession", ai_results: Dict[str, Any]
) -> None:
    """
    Populate session with AI-generated character actions and narrative events.

    Extracts character_actions and narrative_events from AI results dict and
    appends them to the provided session object.

    Args:
        session: StorySession object to populate
        ai_results: Dictionary with character_actions and narrative_events keys
    """
    if ai_results:
        for action in ai_results.get("character_actions", []):
            session.character_actions.append(action)
        for event in ai_results.get("narrative_events", []):
            session.narrative_events.append(event)
