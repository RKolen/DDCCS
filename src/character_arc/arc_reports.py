"""Generate reports from character arc data."""

from datetime import datetime
from typing import Dict, List, Optional

from src.character_arc.arc_analyzer import ArcAnalyzer
from src.character_arc.arc_data import CharacterArc
from src.character_arc.arc_storage import ArcStorage
from src.utils.cli_utils import print_section_header
from src.utils.terminal_display import print_info


class ArcReporter:
    """Generates reports from character arc data."""

    def __init__(
        self,
        storage: ArcStorage,
        analyzer: Optional[ArcAnalyzer] = None,
    ):
        """Initialize reporter.

        Args:
            storage: Arc storage instance.
            analyzer: Optional arc analyzer (uses defaults if omitted).
        """
        self.storage = storage
        self.analyzer = analyzer or ArcAnalyzer()

    def generate_character_report(
        self,
        character_name: str,
        output_format: str = "markdown",
    ) -> str:
        """Generate a detailed report for a single character.

        Args:
            character_name: Name of the character.
            output_format: "markdown" or "text".

        Returns:
            Formatted report string, or an error message.
        """
        arc = self.storage.get_arc(character_name)
        if not arc:
            return f"No arc data found for {character_name}."

        analysis = self.analyzer.analyze_arc_progression(arc)

        if output_format == "markdown":
            return self._format_markdown_report(arc, analysis)
        return self._format_text_report(arc, analysis)

    def _format_markdown_report(
        self,
        arc: CharacterArc,
        analysis: Dict,
    ) -> str:
        """Format report as markdown."""
        generated = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [
            f"# Character Arc Report: {arc.character_name}",
            "",
            f"**Campaign:** {arc.campaign_name}",
            f"**Generated:** {generated}",
            "",
            "## Overview",
            "",
            f"- **Arc Direction:** {analysis['direction']}",
            f"- **Arc Stage:** {analysis['stage']}",
            f"- **Stories Analyzed:** {len(arc.data_points)}",
            "",
            "## Summary",
            "",
            analysis["summary"],
            "",
            "## Dimension Analysis",
            "",
        ]

        for dim_analysis in analysis.get("dimension_analyses", []):
            if not dim_analysis["observations"]:
                continue
            lines.append(f"### {dim_analysis['dimension'].title()}")
            lines.append("")
            lines.append(f"- **Direction:** {dim_analysis['direction']}")
            lines.append(f"- **Confidence:** {dim_analysis['confidence']:.0%}")
            lines.append("")
            lines.append("**Observations:**")
            for obs in dim_analysis["observations"]:
                lines.append(f"- {obs}")
            lines.append("")

        if arc.relationships:
            lines.append("## Relationships")
            lines.append("")
            for target_name, rel_arc in arc.relationships.items():
                lines.append(f"### {target_name}")
                lines.append(f"- **Type:** {rel_arc.relationship_type}")
                lines.append(f"- **Strength:** {rel_arc.strength}/10")
                lines.append(f"- **Trust:** {rel_arc.trust}/10")
                lines.append("")

        if arc.goals:
            lines.extend(self._format_goals_lines(arc))

        lines.extend(self._format_timeline_lines(arc))
        return "\n".join(lines)

    def _format_goals_lines(self, arc: CharacterArc) -> List[str]:
        """Build markdown lines for the goals section."""
        lines = ["## Goals", ""]
        for goal in arc.goals:
            status = goal.get("status", "active")
            progress = goal.get("progress", 0)
            description = goal.get("description", "Unknown goal")
            lines.append(f"- **{description}**")
            lines.append(f"  - Status: {status}")
            lines.append(f"  - Progress: {progress}%")
            lines.append("")
        return lines

    def _format_timeline_lines(self, arc: CharacterArc) -> List[str]:
        """Build markdown lines for the timeline section."""
        lines = ["## Timeline", ""]
        for i, data_point in enumerate(arc.data_points, 1):
            lines.append(f"### Story {i}: {data_point.story_file}")
            lines.append("")
            if data_point.ai_analysis:
                lines.append(data_point.ai_analysis)
                lines.append("")
            if data_point.key_events:
                lines.append("**Key Events:**")
                for event in data_point.key_events:
                    lines.append(f"- {event}")
                lines.append("")
        return lines

    def _format_text_report(
        self,
        arc: CharacterArc,
        analysis: Dict,
    ) -> str:
        """Format report as plain text."""
        generated = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [
            f"CHARACTER ARC REPORT: {arc.character_name.upper()}",
            "=" * 50,
            "",
            f"Campaign: {arc.campaign_name}",
            f"Generated: {generated}",
            "",
            "OVERVIEW",
            "-" * 20,
            f"Direction: {analysis['direction']}",
            f"Stage: {analysis['stage']}",
            f"Stories: {len(arc.data_points)}",
            "",
            "SUMMARY",
            "-" * 20,
            analysis["summary"],
            "",
        ]

        for data_point in arc.data_points:
            if data_point.key_events:
                lines.append(f"Story: {data_point.story_file}")
                for event in data_point.key_events:
                    lines.append(f"  - {event}")
                lines.append("")

        return "\n".join(lines)

    def generate_campaign_report(self) -> str:
        """Generate a summary report for all characters in the campaign."""
        arcs = self.storage.get_all_arcs()
        if not arcs:
            return "No character arc data found for this campaign."

        generated = datetime.now().strftime("%Y-%m-%d %H:%M")
        lines = [
            f"# Campaign Arc Summary: {self.storage.campaign_name}",
            "",
            f"**Generated:** {generated}",
            "",
            f"**Characters:** {len(arcs)}",
            "",
            "## Character Summaries",
            "",
        ]

        for arc in arcs:
            analysis = self.analyzer.analyze_arc_progression(arc)
            summary_preview = analysis["summary"][:100]
            lines.append(f"### {arc.character_name}")
            lines.append("")
            lines.append(f"- **Direction:** {analysis['direction']}")
            lines.append(f"- **Stage:** {analysis['stage']}")
            lines.append(f"- **Stories:** {len(arc.data_points)}")
            lines.append(f"- **Summary:** {summary_preview}...")
            lines.append("")

        return "\n".join(lines)

    def display_character_summary(self, character_name: str) -> None:
        """Display a brief arc summary in the terminal.

        Args:
            character_name: Name of the character to display.
        """
        arc = self.storage.get_arc(character_name)
        if not arc:
            print_info(f"No arc data found for {character_name}.")
            return

        analysis = self.analyzer.analyze_arc_progression(arc)
        print_section_header(f"Character Arc: {character_name}")
        print(f"Direction: {analysis['direction']}")
        print(f"Stage: {analysis['stage']}")
        print(f"Stories: {len(arc.data_points)}")
        print()
        print(analysis["summary"])

    def export_report(
        self,
        character_name: str,
        output_path: str,
        format_type: str = "markdown",
    ) -> None:
        """Export a character report to a file.

        Args:
            character_name: Name of the character.
            output_path: Destination file path.
            format_type: "markdown" or "text".
        """
        report = self.generate_character_report(character_name, format_type)
        with open(output_path, "w", encoding="utf-8") as report_file:
            report_file.write(report)

    def _build_analysis_display_lines(
        self, analysis: Dict
    ) -> List[str]:
        """Build terminal display lines for dimension analyses.

        Args:
            analysis: Result dict from ArcAnalyzer.analyze_arc_progression.

        Returns:
            List of formatted strings.
        """
        lines = []
        for dim in analysis.get("dimension_analyses", []):
            if not dim["observations"]:
                continue
            lines.append(f"  {dim['dimension'].title()}: {dim['direction']}")
            for obs in dim["observations"]:
                lines.append(f"    - {obs}")
        return lines
