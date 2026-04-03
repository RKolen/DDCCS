"""CLI interface for timeline tracking operations."""

import os
from typing import Optional

from src.timeline.event_extractor import EventExtractor
from src.timeline.timeline_display import TimelineDisplay
from src.timeline.timeline_store import TimelineStore
from src.utils.cli_utils import print_section_header


class TimelineCLIManager:
    """CLI manager for story timeline operations."""

    def __init__(self, workspace_path: str, campaign_name: str):
        """Initialize with workspace and campaign context.

        Args:
            workspace_path: Root path for game data.
            campaign_name: Currently active campaign name.
        """
        self.workspace_path = workspace_path
        self.campaign_name = campaign_name

    def get_store(self) -> TimelineStore:
        """Create and return a TimelineStore for the current campaign."""
        return TimelineStore(self.campaign_name, self.workspace_path)

    def timeline_menu(self) -> None:
        """Show the timeline management submenu."""
        store = self.get_store()
        display = TimelineDisplay(store)

        while True:
            print_section_header("TIMELINE TRACKING")
            print(f"Campaign: {self.campaign_name}")
            print("-" * 30)
            print("1. View campaign timeline")
            print("2. Extract events from story file")
            print("3. View character timeline")
            print("4. Export timeline to markdown")
            print("0. Back")

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                display.display_campaign_timeline(self.campaign_name)
            elif choice == "2":
                self._extract_from_story(store)
            elif choice == "3":
                self._view_character_timeline(display)
            elif choice == "4":
                self._export_timeline(display)
            elif choice == "0":
                break
            else:
                print("Invalid choice.")

    def _extract_from_story(self, store: TimelineStore) -> None:
        """Extract and store events from a story file."""
        story_file = input("\nPath to story file: ").strip()
        if not story_file or not os.path.exists(story_file):
            print("[ERROR] Story file not found.")
            return

        extractor = EventExtractor()
        events = extractor.extract_from_file(
            story_file,
            campaign_name=self.campaign_name,
            story_file=os.path.basename(story_file),
        )

        if not events:
            print("[INFO] No events detected in this story.")
            return

        for event in events:
            store.add_event(event)

        print(f"[OK] Extracted and saved {len(events)} event(s).")

    def _view_character_timeline(self, display: TimelineDisplay) -> None:
        """Display the timeline for a specific character."""
        name = input("\nCharacter name: ").strip()
        if not name:
            print("[ERROR] No name entered.")
            return
        display.display_character_timeline(name)

    def _export_timeline(self, display: TimelineDisplay) -> None:
        """Export the campaign timeline to a markdown file."""
        default_path = f"{self.campaign_name}_timeline.md"
        path = input(f"\nOutput path [{default_path}]: ").strip()
        if not path:
            path = default_path

        display.export_timeline_markdown(self.campaign_name, path)
        print(f"[OK] Timeline exported to {path}")


def get_or_prompt_campaign(
    story_manager, workspace_path: str
) -> Optional[str]:
    """Return the current campaign name or prompt the user to enter one.

    Args:
        story_manager: Story manager that may have a story_context attribute.
        workspace_path: Used to list available campaigns as a hint.

    Returns:
        Campaign name string, or None if the user cancels.
    """
    try:
        story_context = getattr(story_manager, "story_context", None)
        if story_context:
            name = getattr(story_context, "campaign_name", None)
            if name:
                return name
    except AttributeError:
        pass

    campaigns_dir = os.path.join(workspace_path, "game_data", "campaigns")
    if os.path.isdir(campaigns_dir):
        campaigns = sorted(
            e for e in os.listdir(campaigns_dir)
            if os.path.isdir(os.path.join(campaigns_dir, e))
        )
        if campaigns:
            print("\nAvailable campaigns:")
            for camp in campaigns:
                print(f"  {camp}")

    name = input("\nCampaign name: ").strip()
    return name if name else None
