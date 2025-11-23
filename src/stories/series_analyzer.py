"""
Series-Wide Story Analysis

Handles analysis of entire story series for character development and
narrative patterns across multiple files.
"""

import os
import sys
import traceback
from typing import Dict, List, Any, Callable, NamedTuple
from datetime import datetime

from src.utils.file_io import write_text_file, file_exists, read_text_file
from src.utils.text_formatting_utils import wrap_narrative_text
from src.stories.character_action_analyzer import extract_character_actions



class CharacterAnalysisContext(NamedTuple):
    """Context for character development analysis across series."""

    stories: List[str]
    campaign_path: str
    party_members: List[str]
    character_profiles: Dict[str, Any]
    truncate_func: Callable


class SeriesAnalysisContext(NamedTuple):
    """Context for narrative series analysis."""

    stories: List[str]
    campaign_path: str
    party_members: List[str]
    character_profiles: Dict[str, Any]
    truncate_func: Callable


class SeriesAnalyzer:
    """Analyzes character development and narrative across entire story series."""

    def __init__(self, story_manager):
        """Initialize series analyzer.

        Args:
            story_manager: StoryManager instance for analysis operations
        """
        self.story_manager = story_manager

    def analyze_character_development_for_series(
        self,
        analysis_context: CharacterAnalysisContext,
        output_filepath: str = None,
    ) -> tuple:
        """Analyze character development across entire series.

        Filters to only party members and analyzes each story sequentially.
        If output_filepath provided, creates file at start and updates
        incrementally after each story.

        Args:
            analysis_context: Context containing analysis parameters
            output_filepath: Optional path to save results incrementally

        Returns:
            Tuple of (character_actions_list, consultant_analyses_by_story)
        """
        all_character_actions: List[Dict[str, str]] = []
        all_consultant_analyses: Dict[str, Dict[str, Any]] = {}

        party_members = set(analysis_context.party_members)
        if output_filepath:
            print(f"[DEBUG] Creating file header at: {output_filepath}")
            sys.stdout.flush()
            self._create_character_development_file_header(
                output_filepath,
                len(analysis_context.stories),
            )
            print("[DEBUG] File header created")
            sys.stdout.flush()

        for processed_count, story_file in enumerate(
            analysis_context.stories, start=1
        ):
            story_path = os.path.join(
                analysis_context.campaign_path, story_file
            )
            if not file_exists(story_path):
                continue

            story_analysis = self.story_manager.analyze_story_file(story_path)
            story_actions_for_series = (
                self._extract_party_actions_from_story(
                    story_analysis,
                    story_file,
                    party_members,
                )
            )

            all_character_actions.extend(story_actions_for_series)

            # Store consultant analyses for party members only
            if "consultant_analyses" in story_analysis:
                for char_name, consultant_data in story_analysis[
                    "consultant_analyses"
                ].items():
                    if char_name not in party_members:
                        continue

                    if story_file not in all_consultant_analyses:
                        all_consultant_analyses[story_file] = {}
                    all_consultant_analyses[story_file][char_name] = (
                        consultant_data
                    )

            print(
                f"  [{processed_count}/{len(analysis_context.stories)}] {story_file}"
            )

            # Update file incrementally after each story if filepath provided
            if output_filepath and story_actions_for_series:
                print(
                    f"[DEBUG] Appending {len(story_actions_for_series)} "
                    f"actions for {story_file}"
                )
                self._append_story_section(
                    output_filepath,
                    story_file,
                    story_actions_for_series,
                )
            elif output_filepath:
                print(f"[DEBUG] No actions for {story_file}")

        return all_character_actions, all_consultant_analyses

    @staticmethod
    def _extract_party_actions_from_story(
        story_analysis: Dict[str, Any],
        story_file: str,
        party_members: set,
    ) -> List[Dict[str, str]]:
        """Extract character actions for party members from story analysis.

        Args:
            story_analysis: Story analysis result dictionary
            story_file: Name of the story file
            party_members: Set of party member names to include

        Returns:
            List of character actions for party members
        """
        actions = []
        if "character_actions" not in story_analysis:
            return actions

        for action in story_analysis["character_actions"]:
            char_name = action.get("character")
            if char_name not in party_members:
                continue

            action_with_source = action.copy()
            action_with_source["source_story"] = story_file
            actions.append(action_with_source)

        return actions

    @staticmethod
    def _create_character_development_file_header(
        filepath: str,
        story_count: int,
    ) -> None:
        """Create character development file with header.

        Args:
            filepath: Path to save file
            story_count: Total number of stories to analyze
        """
        try:
            print(f"[DEBUG] File path: {filepath}")
            print(f"[DEBUG] File directory: {os.path.dirname(filepath)}")

            today = datetime.now().strftime("%Y-%m-%d")
            lines = []
            lines.append("# Series Character Development\n")
            lines.append(f"**Generated:** {today}\n")
            lines.append(
                f"**Total Stories to Analyze:** {story_count}\n"
            )
            lines.append("")

            content = "\n".join(lines)
            print(f"[DEBUG] Content to write: {repr(content[:50])}")
            write_text_file(filepath, content)
            print("[DEBUG] write_text_file completed")

            # Verify file was created
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                print(f"[DEBUG] File created successfully. Size: {file_size} bytes")
            else:
                print("[ERROR] File was not created after write_text_file call")

        except (OSError, IOError) as e:
            print(f"[ERROR] Failed to create header file: {e}")
            traceback.print_exc()

    @staticmethod
    def _append_story_section(
        filepath: str,
        story_file: str,
        story_actions: List[Dict[str, str]],
    ) -> None:
        """Append a story section to character development file.

        Args:
            filepath: Path to file to update
            story_file: Name of the story file
            story_actions: List of character actions for this story
        """
        lines = []
        lines.append(f"## {story_file}\n")

        for action in story_actions:
            formatted_entry = SeriesAnalyzer._format_character_action_entry(
                action
            )
            lines.append(formatted_entry)

        # Append to existing file
        with open(filepath, "a", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def analyze_entire_series_narrative(
        self,
        series_name: str,
        analysis_context: SeriesAnalysisContext,
        output_filepath: str = None,
    ) -> Dict[str, Any]:
        """Analyze narrative patterns across entire series.

        Filters to only party members and creates improvement suggestions.
        If output_filepath provided, creates file at start and updates
        incrementally after each story.

        Args:
            series_name: Name of the series (used for labeling output)
            analysis_context: SeriesAnalysisContext with analysis parameters
            output_filepath: Optional path to save results incrementally

        Returns:
            Dictionary with series analysis results
        """
        series_analysis: Dict[str, Any] = {
            "series_name": series_name,
            "story_count": len(analysis_context.stories),
            "stories_analyzed": [],
            "major_plot_points": [],
            "character_relationships": {},
            "themes": [],
        }

        # Create file at start if filepath provided
        if output_filepath:
            print(f"[DEBUG] Creating file header at: {output_filepath}")
            sys.stdout.flush()
            self._create_series_analysis_file_header(
                output_filepath, len(analysis_context.stories)
            )
            print("[DEBUG] File header created")
            sys.stdout.flush()

        processed_count = 0

        for story_file in analysis_context.stories:
            story_path = os.path.join(analysis_context.campaign_path, story_file)
            if not file_exists(story_path):
                continue

            # Read story content
            story_content = read_text_file(story_path)
            if not story_content:
                continue

            # Extract character actions for party members only
            character_actions = extract_character_actions(
                story_content,
                analysis_context.party_members,
                analysis_context.truncate_func,
                character_profiles=analysis_context.character_profiles,
            )

            story_analysis = {
                "file": story_file,
                "character_actions": character_actions,
            }
            series_analysis["stories_analyzed"].append(story_analysis)

            # Append story analysis incrementally if filepath provided
            if output_filepath:
                self._append_story_analysis_section(
                    output_filepath,
                    story_file,
                    character_actions,
                    analysis_context.character_profiles,
                    analysis_context.truncate_func,
                )

            processed_count += 1
            print(f"  [{processed_count}/{len(analysis_context.stories)}] {story_file}")

        return series_analysis

    @staticmethod
    def _create_series_analysis_file_header(
        filepath: str,
        story_count: int,
    ) -> None:
        """Create series analysis file with header.

        Args:
            filepath: Path to save file
            story_count: Total number of stories in series
        """
        today = datetime.now().strftime("%Y-%m-%d")
        header = f"""# Series Analysis
**Total Stories:** {story_count}
**Generated:** {today}

"""
        try:
            write_text_file(filepath, header)
            file_size = os.path.getsize(filepath)
            print(f"[DEBUG] File created successfully. Size: {file_size} bytes")
        except (OSError, IOError) as e:
            print(f"[ERROR] Failed to create analysis file header: {e}")
            traceback.print_exc()

    @staticmethod
    def _append_story_analysis_section(
        filepath: str,
        story_file: str,
        character_actions: List[Dict[str, Any]],
        character_profiles: Dict[str, Any] = None,
        truncate_func: Callable = None,
    ) -> None:
        """Append a story analysis section to series analysis file.

        Args:
            filepath: Path to file to update
            story_file: Name of the story file
            character_actions: List of character action dictionaries
            character_profiles: Optional dict of character profiles
            truncate_func: Optional function to truncate text
        """
        if not character_actions:
            return

        profiles = character_profiles or {}

        # Build header and actions section
        lines = [f"\n## Story: {story_file}\n", "### Character Actions\n"]
        for action in character_actions:
            lines.append(
                f"**{action.get('character', 'Unknown')}:** "
                f"{wrap_narrative_text(action.get('action', 'No action'), width=80)}\n"
            )

        # Build suggestions section
        lines.append("\n### Improvement Suggestions\n")
        for action in character_actions:
            char_name = action.get("character", "Unknown")
            reasoning = action.get("reasoning", "")

            # Use reasoning if available, otherwise use personality
            if reasoning:
                text = f"**{char_name}:** {reasoning}"
            else:
                personality = profiles.get(char_name, {}).get(
                    "personality_summary", ""
                )
                personality_desc = (
                    personality.lower() if personality else "their character"
                )
                text = (
                    f"**{char_name}:** Consider enhancing their role based on "
                    f"{personality_desc}."
                )

            # Truncate and wrap
            if truncate_func:
                text = truncate_func(text, 200)
            lines.append(f"- {wrap_narrative_text(text, width=80)}\n")

        try:
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write("\n".join(lines))
        except (OSError, IOError) as e:
            print(f"[ERROR] Failed to append analysis section: {e}")
            traceback.print_exc()

    @staticmethod
    def _format_character_action_entry(action: Dict[str, str]) -> str:
        """Format a single character action entry with text wrapping.

        Args:
            action: Character action dictionary

        Returns:
            Formatted markdown string for the action entry
        """
        char_name = action.get("character", "Unknown")
        lines = []
        lines.append(f"### Character: {char_name}\n")

        # Wrap action text to 80 chars for readability
        action_text = action.get("action", "No action")
        wrapped_action = wrap_narrative_text(action_text, width=80)
        lines.append(f"**Action:** {wrapped_action}\n")

        # Wrap reasoning
        reasoning_text = action.get("reasoning", "N/A")
        wrapped_reasoning = wrap_narrative_text(reasoning_text, width=80)
        lines.append(f"**Reasoning:** {wrapped_reasoning}\n")

        # Wrap consistency
        consistency_text = action.get("consistency", "N/A")
        wrapped_consistency = wrap_narrative_text(
            consistency_text, width=80
        )
        lines.append(f"**Consistency:** {wrapped_consistency}\n")

        # Wrap notes
        notes_text = action.get("notes", "N/A")
        wrapped_notes = wrap_narrative_text(notes_text, width=80)
        lines.append(f"**Notes:** {wrapped_notes}\n")
        lines.append("")

        return "".join(lines)

    def save_character_development(
        self,
        campaign_path: str,
        character_actions: List[Dict[str, str]],
    ) -> str:
        """Save series character development to file.

        Creates file with headers first, then content organized by story.
        Wraps text to 80 characters per line for readability.

        Args:
            campaign_path: Path to campaign directory
            character_actions: Character development data (includes source_story)

        Returns:
            Path to saved file
        """
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"series_character_development_{today}.md"
        filepath = os.path.join(campaign_path, filename)

        # Organize actions by story for better readability
        actions_by_story: Dict[str, List[Dict[str, str]]] = {}
        for action in character_actions:
            story_file = action.get("source_story", "Unknown")
            if story_file not in actions_by_story:
                actions_by_story[story_file] = []
            actions_by_story[story_file].append(action)

        # Build content with proper structure
        lines = []
        lines.append("# Series Character Development\n")
        lines.append(f"**Generated:** {today}\n")
        lines.append(
            f"**Total Stories Analyzed:** {len(actions_by_story)}\n"
        )
        lines.append("")

        # Process each story in order
        for story_file in sorted(actions_by_story.keys()):
            story_actions = actions_by_story[story_file]
            lines.append(f"## {story_file}\n")

            for action in story_actions:
                formatted_entry = self._format_character_action_entry(
                    action
                )
                lines.append(formatted_entry)

        content = "".join(lines)
        write_text_file(filepath, content)
        return filepath

    def save_series_analysis(
        self, campaign_path: str, series_name: str, series_analysis: Dict[str, Any]
    ) -> str:
        """Save series analysis results to file.

        Args:
            campaign_path: Path to campaign directory
            series_name: Name of series
            series_analysis: Analysis results

        Returns:
            Path to saved file
        """
        today = datetime.now().strftime("%Y-%m-%d")
        session_filename = (
            f"series_analysis_{today}_{series_name.replace(' ', '_').lower()}.md"
        )
        session_filepath = os.path.join(campaign_path, session_filename)

        # Format analysis for output
        analysis_content = self._format_series_analysis(series_analysis)

        write_text_file(session_filepath, analysis_content)
        return session_filepath
    @staticmethod
    def _format_series_analysis(series_analysis: Dict[str, Any]) -> str:
        """Format series analysis results as markdown.

        Args:
            series_analysis: Analysis results dictionary

        Returns:
            Formatted markdown string
        """
        lines = []
        lines.append(f"# Series Analysis: {series_analysis['series_name']}\n")
        lines.append(f"**Stories Analyzed:** {series_analysis['story_count']}\n")

        if series_analysis["stories_analyzed"]:
            lines.append("## Stories Overview\n")
            for story_info in series_analysis["stories_analyzed"]:
                lines.append(f"- {story_info['file']}")
            lines.append("")

        lines.append("## Analysis Results\n")
        lines.append("*Character development analysis by story:*\n")

        # Include analysis from each story organized by party member
        return "\n".join(lines)
