"""
Series-Wide Analysis CLI Module

Handles CLI operations for analyzing entire story series for character development
and narrative patterns across multiple files.
"""

import os
from typing import List
from datetime import datetime

from src.utils.path_utils import get_campaign_path
from src.stories.party_manager import PartyManager
from src.stories.series_analyzer import (
    SeriesAnalyzer,
    CharacterAnalysisContext,
    SeriesAnalysisContext,
)


class SeriesAnalysisCLI:
    """Manages series-wide analysis CLI operations."""

    def __init__(self, story_manager, workspace_path):
        """Initialize series analysis CLI manager.

        Args:
            story_manager: StoryManager instance
            workspace_path: Root workspace path
        """
        self.story_manager = story_manager
        self.workspace_path = workspace_path

    @staticmethod
    def _get_character_dev_output_path(campaign_path: str) -> str:
        """Get character development output file path.

        Args:
            campaign_path: Campaign directory path

        Returns:
            Full path for character development file
        """
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"series_character_development_{today}.md"
        return os.path.join(campaign_path, filename)

    def generate_character_development_for_series(
        self, series_name: str, stories: List[str], truncate_func, load_profiles_func
    ) -> None:
        """Generate character development for entire story series.

        Aggregates character actions across all narratives to show character
        arc progression throughout the series. File created at start and
        updated incrementally as each story is analyzed.

        Args:
            series_name: Name of the story series (campaign)
            stories: List of story files in the series
            truncate_func: Function to truncate text at sentence boundary
            load_profiles_func: Function to load character profiles
        """
        try:
            if not stories:
                print("[ERROR] No stories in this series.")
                return

            campaign_path = get_campaign_path(series_name, self.workspace_path)
            party_manager = PartyManager(campaign_path)
            party_members = party_manager.get_current_party()
            if not party_members:
                print("[WARNING] No party members configured for this series.")
                return

            print(f"[INFO] Analyzing {len(stories)} story files for {series_name}...")
            print("[INFO] This may take a while...")

            character_profiles = load_profiles_func(party_members, campaign_path)
            output_filepath = self._get_character_dev_output_path(campaign_path)

            analyzer = SeriesAnalyzer(self.story_manager)
            analysis_context = CharacterAnalysisContext(
                stories=stories,
                campaign_path=campaign_path,
                party_members=party_members,
                character_profiles=character_profiles,
                truncate_func=truncate_func,
            )
            all_character_actions, _ = (
                analyzer.analyze_character_development_for_series(
                    analysis_context, output_filepath
                )
            )

            if not all_character_actions:
                print("[WARNING] No character actions found across series.")
                return

            # File already created and updated incrementally
            print(f"\n[SUCCESS] Series character development saved: {output_filepath}")
            print(
                f"[INFO] Analyzed {len(all_character_actions)} character actions "
                f"across {len(stories)} stories"
            )

        except (OSError, AttributeError, ValueError) as e:
            print(f"[ERROR] Failed to generate series character development: {e}")

    def analyze_entire_series(
        self,
        series_name: str,
        stories: List[str],
        truncate_func=None,
        load_profiles_func=None,
    ) -> None:
        """Analyze entire story series for narrative patterns.

        Identifies major plot points, character relationships, and narrative
        themes across all stories in the series. File created at start and
        updated incrementally as each story is analyzed. Filters to party members only.

        Args:
            series_name: Name of the story series (campaign)
            stories: List of story files in the series
            truncate_func: Optional function to truncate text at sentence boundary
            load_profiles_func: Optional function to load character profiles
        """
        try:
            if not stories:
                print("[ERROR] No stories in this series.")
                return

            campaign_path = get_campaign_path(series_name, self.workspace_path)
            party_manager = PartyManager(campaign_path)
            party_members = party_manager.get_current_party()
            if not party_members:
                print("[WARNING] No party members configured for this series.")
                return

            print(f"\n[INFO] Analyzing {len(stories)} story files...")
            print("[INFO] This may take a while...")

            # Construct output filepath
            output_filepath = self._get_series_analysis_output_path(campaign_path)

            # Load character profiles if function provided
            character_profiles = {}
            if load_profiles_func:
                character_profiles = load_profiles_func(party_members, campaign_path)

            # Create analysis context
            analysis_context = SeriesAnalysisContext(
                stories=stories,
                campaign_path=campaign_path,
                party_members=party_members,
                character_profiles=character_profiles,
                truncate_func=truncate_func or (lambda x, y: x),
            )

            # Delegate to SeriesAnalyzer with output filepath for incremental updates
            analyzer = SeriesAnalyzer(self.story_manager)
            series_analysis = analyzer.analyze_entire_series_narrative(
                series_name, analysis_context, output_filepath
            )

            if not series_analysis["stories_analyzed"]:
                print("[WARNING] No analysis results generated.")
                return

            # File already created and updated incrementally
            print(f"\n[SUCCESS] Series analysis saved: {output_filepath}")
            print(
                f"[INFO] Analyzed {len(series_analysis['stories_analyzed'])} stories "
                f"for narrative patterns and themes"
            )

        except (OSError, AttributeError, ValueError) as e:
            print(f"[ERROR] Failed to analyze series: {e}")

    @staticmethod
    def _get_series_analysis_output_path(campaign_path: str) -> str:
        """Get series analysis output file path.

        Args:
            campaign_path: Campaign directory path

        Returns:
            Full path for series analysis file
        """
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"series_analysis_{today}.md"
        return os.path.join(campaign_path, filename)
