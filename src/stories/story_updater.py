"""
Story Updater Component.

Handles updating story files with analysis results, including consultant notes
and consistency sections.
"""

import os
from typing import Dict, Any
from src.utils.file_io import read_text_file, write_text_file, file_exists
from src.utils.markdown_utils import update_markdown_section
from src.utils.story_formatting_utils import (
    generate_consultant_notes,
    generate_consistency_section
)

class StoryUpdater:
    """Updates story files with consultant analysis and consistency notes."""

    def update_story_with_analysis(self, filepath: str, analysis: Dict[str, Any]):
        """
        Update story file with consultant analysis.

        Args:
            filepath: Path to the story file
            analysis: Analysis results dictionary
        """
        if not file_exists(filepath):
            return

        content = read_text_file(filepath)

        # Generate sections using formatting utilities
        consultant_notes = generate_consultant_notes(analysis)
        consistency_section = generate_consistency_section(analysis)

        # Replace or add the consultant sections
        content = update_markdown_section(
            content, "Character Consultant Notes", consultant_notes
        )
        content = update_markdown_section(
            content, "Consistency Analysis", consistency_section
        )

        # Write back to file
        write_text_file(filepath, content)

        print(
            f"[SUCCESS] Updated story file with consultant analysis: "
            f"{os.path.basename(filepath)}"
        )

    def append_combat_narrative(self, filepath: str, narrative: str):
        """
        Append combat narrative to story file.

        Args:
            filepath: Path to the story file
            narrative: Combat narrative text to append
        """
        if not file_exists(filepath):
            return

        content = read_text_file(filepath)

        # Add combat section
        combat_section = f"\n\n## Combat Scene\n\n{narrative}\n"
        content += combat_section

        write_text_file(filepath, content)

        print(
            f"[SUCCESS] Appended combat narrative to story file: "
            f"{os.path.basename(filepath)}"
        )
