"""
Story Formatting Utilities.

Utility functions for generating formatted markdown sections from analysis results.
"""

from typing import Dict, Any


def generate_consultant_notes(analysis: Dict[str, Any]) -> str:
    """
    Generate the consultant notes section content.

    Args:
        analysis: Analysis results dictionary

    Returns:
        Formatted consultant notes content
    """
    notes = []

    # DC Suggestions
    if analysis.get("dc_suggestions"):
        notes.append("### DC Suggestions\n")
        for request, suggestions in analysis["dc_suggestions"].items():
            notes.append(f"**{request}:**\n")
            for character, suggestion in suggestions.items():
                notes.append(
                    f"- {character}: DC {suggestion['suggested_dc']} "
                    f"({suggestion['reasoning']})"
                )
                if suggestion.get("alternative_approaches"):
                    notes.append(
                        f"  - Alternatives: "
                        f"{', '.join(suggestion['alternative_approaches'])}"
                    )
            notes.append("")

    # Character-specific consultant advice
    if analysis.get("consultant_analyses"):
        notes.append("### Character Behavior Guidance\n")
        for character, char_analysis in analysis["consultant_analyses"].items():
            if char_analysis.get("suggestions"):
                notes.append(f"**{character}:**")
                for suggestion in char_analysis["suggestions"]:
                    notes.append(f"- {suggestion}")
                notes.append("")

    return "\n".join(notes) if notes else "*No consultant notes generated.*"


def generate_consistency_section(analysis: Dict[str, Any]) -> str:
    """
    Generate the consistency analysis section content.

    Args:
        analysis: Analysis results dictionary

    Returns:
        Formatted consistency section content
    """
    sections = []

    # Overall summary
    overall = analysis.get("overall_consistency", {})
    sections.append(f"### Overall Consistency: {overall.get('rating', 'Unknown')}")
    sections.append(f"**Score:** {overall.get('score', 0)}/1.0")
    sections.append(
        f"**Summary:** {overall.get('summary', 'No analysis available')}"
    )
    sections.append("")

    # Individual character analyses
    if analysis.get("consultant_analyses"):
        sections.append("### Individual Character Analysis\n")

        for character, char_analysis in analysis["consultant_analyses"].items():
            sections.append(
                f"**{character}** - {char_analysis.get('overall_rating', 'Unknown')}"
            )
            sections.append(
                f"Score: {char_analysis.get('consistency_score', 0)}/1.0\n"
            )

            if char_analysis.get("positive_notes"):
                sections.append("✅ **Positive aspects:**")
                for note in char_analysis["positive_notes"]:
                    sections.append(f"- {note}")
                sections.append("")

            if char_analysis.get("issues"):
                sections.append("⚠️ **Issues to address:**")
                for issue in char_analysis["issues"]:
                    sections.append(f"- {issue}")
                sections.append("")

            sections.append("---\n")

    return (
        "\n".join(sections) if sections else "*No consistency analysis available.*"
    )
