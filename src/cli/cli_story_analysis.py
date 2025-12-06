"""
Story Analysis CLI Module

Handles story analysis and combat conversion operations.
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

# Optional AI client import
try:
    from src.ai.ai_client import AIClient

    AI_CLIENT_AVAILABLE = True
except ImportError:
    AIClient = None
    AI_CLIENT_AVAILABLE = False

from src.combat.combat_narrator import CombatNarrator
from src.cli.dnd_cli_helpers import (
    get_multi_line_combat_input,
    select_narrative_style,
    select_target_story_for_combat,
    save_combat_narrative,
)
from src.cli.party_config_manager import load_current_party
from src.stories.character_action_analyzer import extract_character_actions
from src.stories.story_consistency_analyzer import StoryConsistencyAnalyzer
from src.utils.path_utils import get_campaign_path
from src.utils.file_io import write_text_file, read_text_file
from src.utils.string_utils import truncate_at_sentence
from src.cli.cli_story_config_helper import extract_context_from_stories


class StoryAnalysisCLI:
    """Manages story analysis and combat conversion operations."""

    def __init__(self, story_manager, workspace_path):
        """
        Initialize story analysis CLI manager.

        Args:
            story_manager: StoryManager instance
            workspace_path: Root workspace path
        """
        self.story_manager = story_manager
        self.workspace_path = workspace_path
        self.ai_client = None
        self.combat_narrator = CombatNarrator(story_manager.consultants)

    def analyze_story(self, series_name: "Optional[str]" = None):
        """Analyze a story file.

        Args:
            series_name: Optional series name to analyze stories within that series
        """
        if series_name:
            story_files = self.story_manager.get_story_files_in_series(series_name)
            base_path = get_campaign_path(series_name, self.workspace_path)
        else:
            story_files = self.story_manager.get_story_files()
            base_path = self.story_manager.stories_path

        if not story_files:
            print("\n[ERROR] No story files found.")
            return

        print("\n ANALYZE STORY FILE")
        print("-" * 30)
        for i, filename in enumerate(story_files, 1):
            print(f"{i}. {filename}")

        try:
            choice = int(input("Enter file number: ")) - 1
            if 0 <= choice < len(story_files):
                filename = story_files[choice]
                filepath = os.path.join(base_path, filename)

                print(f"\n Analyzing {filename}...")
                analysis = self.story_manager.analyze_story_file(filepath)

                if "error" in analysis:
                    print(f"[ERROR] {analysis['error']}")
                    return

                self._display_story_analysis(analysis)

                # Save to session results file instead of updating story
                save = (
                    input("\nSave analysis to session results file? (y/n): ")
                    .strip()
                    .lower()
                )
                if save == "y":
                    self.save_analysis_to_session_results(analysis, base_path, filename)
            else:
                print("Invalid file number.")
        except ValueError:
            print("Invalid input.")

    def save_analysis_to_session_results(
        self, analysis: Dict[str, Any], series_path: str, story_filename: str
    ) -> None:
        """Save analysis results to a session results file.

        Creates or appends to session_results_YYYY-MM-DD_storyname.md file.

        Args:
            analysis: Analysis results dictionary
            series_path: Path to the series directory
            story_filename: Name of the analyzed story file
        """
        # Extract story name from filename (remove extension and numbering)
        story_slug = os.path.splitext(story_filename)[0]
        if "_" in story_slug:
            story_slug = story_slug.split("_", 1)[1]
        story_slug = story_slug.replace(" ", "_").lower()

        today = datetime.now().strftime("%Y-%m-%d")
        session_filename = f"session_results_{today}_{story_slug}.md"
        session_filepath = os.path.join(series_path, session_filename)

        # Build analysis content
        analysis_content = self.format_analysis_for_session(analysis, story_filename)

        # Check if file exists
        if os.path.exists(session_filepath):
            # Append to existing file
            with open(session_filepath, "r", encoding="utf-8") as f:
                existing = f.read()
            content = existing + "\n" + analysis_content
            print(f"[SUCCESS] Appended analysis to: {session_filename}")
        else:
            # Create new file
            header = f"# Session Results: {story_slug}\n**Date:** {today}\n\n"
            content = header + analysis_content
            print(f"[SUCCESS] Created session results file: {session_filename}")

        write_text_file(session_filepath, content)

    def format_analysis_for_session(
        self, analysis: Dict[str, Any], story_filename: str
    ) -> str:
        """Format analysis results as markdown for session results file.

        Args:
            analysis: Analysis results dictionary
            story_filename: Name of the analyzed story

        Returns:
            Formatted markdown content
        """
        lines = []
        lines.append(f"## Analysis: {story_filename}")
        lines.append(f"**Time:** {datetime.now().strftime('%H:%M:%S')}")
        lines.append("")

        # Overall consistency
        overall = analysis.get("overall_consistency", {})
        lines.append("### Overall Consistency")
        lines.append(f"- **Rating:** {overall.get('rating', 'Unknown')}")
        lines.append(f"- **Score:** {overall.get('score', 0)}/1.0")
        lines.append(f"- **Summary:** {overall.get('summary', 'No analysis')}")
        lines.append("")

        # Character analyses
        if analysis.get("consultant_analyses"):
            lines.append("### Character Analyses")
            for character, char_analysis in analysis["consultant_analyses"].items():
                lines.append(f"\n**{character}**")
                lines.append(
                    f"- **Rating:** {char_analysis.get('overall_rating', 'Unknown')}"
                )
                lines.append(
                    f"- **Score:** {char_analysis.get('consistency_score', 0)}/1.0"
                )

                if char_analysis.get("positive_notes"):
                    lines.append(
                        f"- **Positives:** {len(char_analysis['positive_notes'])} noted"
                    )

                if char_analysis.get("issues"):
                    lines.append(f"- **Issues:** {len(char_analysis['issues'])} noted")
                    for issue in char_analysis["issues"][:2]:
                        lines.append(f"  - {issue}")
            lines.append("")

        # DC suggestions
        if analysis.get("dc_suggestions"):
            lines.append("### DC Suggestions")
            for request, suggestions in analysis["dc_suggestions"].items():
                lines.append(f"\n**{request}**")
                for character, suggestion in suggestions.items():
                    dc_value = suggestion.get("suggested_dc", "Unknown")
                    reasoning = suggestion.get("reasoning", "No reasoning provided")
                    lines.append(f"  - {character}: DC {dc_value} ({reasoning})")
            lines.append("")

        return "\n".join(lines)

    def _display_story_analysis(self, analysis: Dict[str, Any]):
        """Display story analysis results."""
        print(f"\n[Stats] STORY ANALYSIS: {analysis['story_file']}")
        print("=" * 50)

        # Overall consistency
        overall = analysis.get("overall_consistency", {})
        print(f"Overall Consistency: {overall.get('rating', 'Unknown')}")
        print(f"Score: {overall.get('score', 0)}/1.0")
        print(f"Summary: {overall.get('summary', 'No analysis')}")

        # Character analyses
        if analysis.get("consultant_analyses"):
            print("\n CHARACTER ANALYSES:")
            for character, char_analysis in analysis["consultant_analyses"].items():
                print(f"\n• {character}: {char_analysis['overall_rating']}")
                print(f"  Score: {char_analysis['consistency_score']}/1.0")

                if char_analysis.get("positive_notes"):
                    print(
                        f"  [SUCCESS] Positives: {len(char_analysis['positive_notes'])}"
                    )

                if char_analysis.get("issues"):
                    print(f"  [WARNING] Issues: {len(char_analysis['issues'])}")
                    for issue in char_analysis["issues"][:2]:  # Show first 2
                        print(f"    - {issue}")

        # DC suggestions
        if analysis.get("dc_suggestions"):
            print("\n DC SUGGESTIONS:")
            for request, suggestions in analysis["dc_suggestions"].items():
                print(f"\n• {request}")
                for character, suggestion in suggestions.items():
                    print(
                        f"  {character}: DC {suggestion['suggested_dc']}"
                        f" ({suggestion['reasoning']})"
                    )

        input("\nPress Enter to continue...")

    def convert_combat(self):
        """Convert combat description to narrative."""
        print("\n CONVERT COMBAT TO NARRATIVE")
        print("-" * 50)
        print("Describe what happened in combat tactically. Example:")
        print("  Theron charges forward and strikes the goblin with his longsword.")
        print("  Mira sneaks behind an enemy and backstabs with her dagger.")
        print("  Garrick swings his warhammer, crushing the goblin's shield.")
        print()

        # Get combat description from user
        combat_prompt = get_multi_line_combat_input()
        if not combat_prompt:
            print("No combat description provided.")
            return

        # Select narrative style
        style = select_narrative_style()

        # Select target story file and get context
        target_story_path, story_context = select_target_story_for_combat(
            self.workspace_path, self.story_manager
        )

        print(f"\n Converting to {style} narrative...")

        # Initialize AI client if needed
        self._ensure_ai_client_initialized()

        # Recreate combat narrator with AI client
        self.combat_narrator = CombatNarrator(
            self.story_manager.consultants, self.ai_client
        )

        # Generate combat title automatically
        print("  Generating combat title...")
        combat_title = self.combat_narrator.generate_combat_title(
            combat_prompt, story_context
        )
        print(f"   Title: {combat_title}")

        # Generate narrative
        narrative = self.combat_narrator.narrate_combat_from_prompt(
            combat_prompt=combat_prompt, story_context=story_context, style=style
        )

        print("\n COMBAT NARRATIVE:")
        print("=" * 70)
        print(narrative)
        print("=" * 70)

        # Save or append the narrative
        save_combat_narrative(
            narrative, combat_title, target_story_path, self.workspace_path
        )

    def _ensure_ai_client_initialized(self):
        """Ensure AI client is initialized, or set to None if unavailable."""
        if not hasattr(self, "ai_client") or self.ai_client is None:
            if AI_CLIENT_AVAILABLE:
                try:
                    self.ai_client = AIClient()
                except (AttributeError, ValueError) as e:
                    print(f"[WARNING]  Could not initialize AI client: {e}")
                    print("   Using fallback mode...")
                    self.ai_client = None
            else:
                print("[WARNING]  AI client not available")
                print("   Using fallback mode...")
                self.ai_client = None

    def extract_context_from_previous_stories(
        self,
        campaign_dir: str,
        story_files: list,
        party_names: Optional[List] = None,
        npc_names: Optional[List] = None,
    ) -> str:
        """Extract location and setting context from previous stories.

        Delegates to helper module to avoid code duplication.
        """
        return extract_context_from_stories(
            self.workspace_path,
            campaign_dir,
            story_files,
            party_names=party_names,
            npc_names=npc_names,
        )

    def analyze_series_consistency(self, series_name: str, series_stories: List[str]):
        """Analyze entire story series for character consistency.

        Args:
            series_name: Name of the story series
            series_stories: List of story files in the series
        """
        print("\n STORY SERIES CONSISTENCY ANALYSIS")
        print("-" * 50)
        print("This will analyze all stories for character behavioral")
        print("consistency and tactical appropriateness.")
        print("This may take several minutes with AI analysis...\n")

        # Load party members for this series
        try:
            party_members = load_current_party(
                workspace_path=self.workspace_path, campaign_name=series_name
            )
        except (ImportError, OSError, ValueError):
            print("[ERROR] Could not load party configuration for this series.")
            return

        if not party_members:
            print("[ERROR] No party members found in current_party.json")
            return

        print(f"Party Members: {', '.join(party_members)}")
        print(f"Stories to Analyze: {len(series_stories)}\n")

        confirm = input("Proceed with analysis? (y/n): ").strip().lower()
        if confirm != "y":
            print("Analysis cancelled.")
            return

        # Create analyzer and run analysis
        analyzer = StoryConsistencyAnalyzer(
            workspace_path=self.workspace_path, ai_client=self.story_manager.ai_client
        )

        try:
            print("\n[INFO] Analyzing stories...")
            results = analyzer.analyze_series(
                series_name=series_name,
                story_files=series_stories,
                party_members=party_members,
            )

            # Display results
            print("\n" + "=" * 50)
            print("ANALYSIS COMPLETE")
            print("=" * 50)
            print(f"Stories Analyzed: {results['stories_analyzed']}")
            print(f"Total Issues Found: {results['total_issues']}")
            print("\nDetailed report saved to:")
            print(f"  {results['report_path']}")
            print("\nOpen the report file to see detailed analysis.")

        except (OSError, ValueError, KeyError, AttributeError) as e:
            print(f"\n[ERROR] Analysis failed: {e}")

    def analyze_character_development_series(
        self, series_name: str, series_stories: List[str]
    ):
        """Analyze character development across the entire series.

        Args:
            series_name: Name of the story series
            series_stories: List of story files in the series
        """
        print("\n CHARACTER DEVELOPMENT ANALYSIS (SERIES)")
        print("-" * 50)
        print("This will analyze all stories to track character development,")
        print("consistency, and arc progression against their profiles.")
        print("This process involves heavy AI usage and may take some time.\n")

        # Load party members for this series
        try:
            party_members = load_current_party(
                workspace_path=self.workspace_path, campaign_name=series_name
            )
        except (ImportError, OSError, ValueError):
            print("[ERROR] Could not load party configuration for this series.")
            return

        if not party_members:
            print("[ERROR] No party members found in current_party.json")
            return

        print(f"Party Members: {', '.join(party_members)}")
        print(f"Stories to Analyze: {len(series_stories)}\n")

        confirm = input("Proceed with analysis? (y/n): ").strip().lower()
        if confirm != "y":
            print("Analysis cancelled.")
            return

        print("\n[INFO] Loading character profiles...")
        profiles = self._load_character_profiles(party_members)

        print("[INFO] Analyzing stories...")
        series_path = get_campaign_path(series_name, self.workspace_path)
        all_actions = {}

        for story_file in series_stories:
            print(f"  - Processing {story_file}...")
            story_path = os.path.join(series_path, story_file)
            story_content = read_text_file(story_path)

            if not story_content:
                continue

            actions = extract_character_actions(
                story_content,
                party_members,
                truncate_at_sentence,
                character_profiles=profiles,
            )

            for action in actions:
                char_name = action["character"]
                if char_name not in all_actions:
                    all_actions[char_name] = []

                # Add story context
                action["story_file"] = story_file
                all_actions[char_name].append(action)

        print("\n[INFO] Generating development report...")
        self._generate_development_report(
            series_name, series_path, all_actions, profiles
        )

    def _load_character_profiles(self, party_names: List[str]) -> Dict[str, Any]:
        """Load character profiles for analysis."""
        profiles = {}
        chars_dir = os.path.join(self.workspace_path, "game_data", "characters")

        for name in party_names:
            # Try exact match first
            normalized = name.lower().replace(" ", "_")
            path = os.path.join(chars_dir, f"{normalized}.json")

            if not os.path.exists(path):
                # Try first name
                first_name = name.split()[0].lower()
                path = os.path.join(chars_dir, f"{first_name}.json")

            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        profiles[name] = json.load(f)
                except (OSError, ValueError):
                    pass

        return profiles

    def _generate_development_report(
        self,
        series_name: str,
        series_path: str,
        all_actions: Dict[str, List[Dict[str, str]]],
        profiles: Dict[str, Any],
    ):
        """Generate markdown report for series character development."""
        timestamp = datetime.now().strftime("%Y-%m-%d")
        report_filename = f"character_development_analysis_{timestamp}.md"
        report_path = os.path.join(series_path, report_filename)

        lines = [
            f"# Character Development Analysis: {series_name}",
            f"**Date:** {timestamp}",
            f"**Characters Analyzed:** {', '.join(all_actions.keys())}",
            "",
            "## Overview",
            "This report tracks character behavior, consistency, and development arcs",
            "across the entire story series, comparing actions against established traits.",
            "",
        ]

        for char_name in sorted(all_actions.keys()):
            lines.extend(
                self._format_character_development_section(
                    char_name, all_actions[char_name], profiles.get(char_name, {})
                )
            )

        write_text_file(report_path, "\n".join(lines))
        print(f"\n[SUCCESS] Report generated: {report_filename}")
        print(f"Location: {report_path}")

    def _format_character_development_section(
        self, char_name: str, actions: List[Dict[str, str]], profile: Dict[str, Any]
    ) -> List[str]:
        """Format development section for a single character."""
        lines = [f"## {char_name}"]

        if profile:
            char_class = profile.get("dnd_class", "Unknown")
            level = profile.get("level", "?")
            background = profile.get("background_story") or profile.get(
                "backstory", "Unknown"
            )

            lines.append(f"**Class:** {char_class} (Level {level})")
            lines.append(f"**Background:** {background[:100]}...")

        lines.append("")
        lines.append(f"### Action Log ({len(actions)} actions recorded)")

        for action in actions:
            # Skip "Not mentioned" entries if they are just placeholders
            if action["action"] == "Not mentioned in this story segment":
                continue

            lines.append(f"**Story:** {action['story_file']}")
            lines.append(f"- **Action:** {action['action']}")
            lines.append(f"- **Reasoning:** {action['reasoning']}")
            lines.append(f"- **Consistency:** {action['consistency']}")
            lines.append(f"- **Development Notes:** {action['notes']}")
            lines.append("")

        lines.append("---")
        lines.append("")
        return lines
