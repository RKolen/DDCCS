#!/usr/bin/env python3
"""
File Display Utility - View any file with rich formatting

A simple utility for viewing story files, character profiles, and markdown
documentation with beautiful terminal formatting.

Usage:
    python -m src.utils.display_file <filepath>
    python -m src.utils.display_file <campaign> <story_number>

Examples:
    python -m src.utils.display_file game_data/campaigns/Example_Campaign/001_opening.md
    python -m src.utils.display_file game_data/characters/aragorn.json
    python -m src.utils.display_file README.md
    python -m src.utils.display_file Example_Campaign 1
"""

import sys
import os
from typing import Optional
from src.utils.terminal_display import (
    display_any_file,
    print_info,
    print_error,
)

def find_story_file(campaign: str, story_number: str) -> Optional[str]:
    """Find a story file in a campaign directory.

    Args:
        campaign: Campaign name or path
        story_number: Story number (e.g., '1', '01', '001')

    Returns:
        Path to story file if found, else None
    """
    # Try different campaign path formats
    campaign_paths = [
        f"game_data/campaigns/{campaign}",
        f"game_data/campaigns/{campaign}_Campaign",
        f"game_data/campaigns/{campaign}_Quest",
        f"game_data/campaigns/{campaign}_Story",
        f"game_data/campaigns/{campaign}_Adventure",
    ]

    for campaign_path in campaign_paths:
        if not os.path.exists(campaign_path):
            continue

        # Normalize story number (1 -> 001)
        for padding in ['%03d', '%02d', '%d']:
            try:
                story_num = (
                    padding % int(story_number)
                    if story_number.isdigit()
                    else story_number
                )
            except ValueError:
                continue

            # Look for story file
            for entry in os.listdir(campaign_path):
                if entry.startswith(story_num) and entry.endswith('.md'):
                    return os.path.join(campaign_path, entry)

    return None


def show_available_campaigns() -> None:
    """Display available campaigns and their stories."""
    print_error("Campaign not found. Available campaigns:")
    campaigns_dir = "game_data/campaigns"
    if os.path.exists(campaigns_dir):
        for folder in os.listdir(campaigns_dir):
            folder_path = os.path.join(campaigns_dir, folder)
            if os.path.isdir(folder_path):
                stories = [
                    f.replace('.md', '') for f in os.listdir(folder_path)
                    if (f.endswith('.md') and not f.startswith('character_')
                        and not f.startswith('session_')
                        and not f.startswith('story_'))
                ]
                if stories:
                    print(f"  {folder}/ - {len(stories)} stories")


def main():
    """Display a file with rich formatting."""
    if len(sys.argv) < 2:
        print_info("D&D File Viewer - View files with rich formatting")
        print("\nUsage:")
        print("  python -m src.utils.display_file <filepath>")
        print("  python -m src.utils.display_file <campaign> <story_number>")
        print("\nExamples:")
        print("  python -m src.utils.display_file README.md")
        print("  python -m src.utils.display_file game_data/characters/aragorn.json")
        print("  python -m src.utils.display_file Example_Campaign 1")
        sys.exit(0)

    if len(sys.argv) == 2:
        # Direct filepath
        display_any_file(sys.argv[1])
    else:
        # Campaign + story number
        campaign = sys.argv[1]
        story_num = sys.argv[2]

        filepath = find_story_file(campaign, story_num)
        if not filepath:
            show_available_campaigns()
            sys.exit(1)

        display_any_file(filepath)


if __name__ == "__main__":
    main()
