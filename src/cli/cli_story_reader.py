"""
CLI Story Reader Manager

Handles interactive file reading from the terminal for stories, characters,
and related analysis files.
"""

import json
import os
from typing import List

from src.utils.terminal_display import display_any_file, display_story_file, print_error
from src.cli.party_config_manager import load_current_party


class StoryReaderCLI:
    """Manages interactive story and file reading from terminal."""

    def __init__(self, workspace_path: str):
        """Initialize story reader.

        Args:
            workspace_path: Root workspace path
        """
        self.workspace_path = workspace_path

    def display_menu(self):
        """Display main story reader menu and handle navigation."""
        self.read_story()

    def read_story(self):
        """Interactive story reading menu."""
        print("\n READ STORIES")
        print("-" * 30)

        # Get available campaigns
        campaigns_dir = os.path.join(self.workspace_path, "game_data", "campaigns")
        if not os.path.exists(campaigns_dir):
            print_error("No campaigns directory found.")
            return

        campaigns = [
            d
            for d in os.listdir(campaigns_dir)
            if os.path.isdir(os.path.join(campaigns_dir, d))
        ]

        if not campaigns:
            print_error("No campaigns found.")
            return

        # Select campaign
        print("\nAvailable campaigns:")
        for i, campaign in enumerate(campaigns, 1):
            print(f"{i}. {campaign}")

        try:
            choice = int(input("\nSelect campaign (0 to back): "))
            if choice == 0:
                return
            if 1 <= choice <= len(campaigns):
                selected_campaign = campaigns[choice - 1]
                self._read_from_campaign(selected_campaign)
            else:
                print_error("Invalid choice.")
        except ValueError:
            print_error("Invalid input.")

    def _read_from_campaign(self, campaign_name: str):
        """Read files from a specific campaign.

        Args:
            campaign_name: Name of the campaign
        """
        campaign_path = os.path.join(
            self.workspace_path, "game_data", "campaigns", campaign_name
        )

        # Get party members for this campaign
        party_members = []
        try:
            party_members = load_current_party(
                workspace_path=self.workspace_path, campaign_name=campaign_name
            )
        except (ImportError, OSError, ValueError):
            pass

        while True:
            print(f"\n CAMPAIGN: {campaign_name}")
            print("-" * (len(campaign_name) + 12))
            print("1. Read Story File")
            print("2. Read Character Profile(s)")
            print("3. Read Session Results")
            print("4. Read Character Development")
            print("0. Back")

            choice = input("\nSelect file type (0 to back): ").strip()

            if choice == "0":
                return

            if choice == "1":
                self._read_story_files(campaign_path, campaign_name)
            elif choice == "2":
                self._read_character_profiles(party_members)
            elif choice == "3":
                self._read_session_results(campaign_path)
            elif choice == "4":
                self._read_development_files(campaign_path)
            else:
                print_error("Invalid choice.")

    def _read_story_files(self, campaign_path: str, campaign_name: str):
        """Read story files from campaign.

        Args:
            campaign_path: Path to campaign directory
            campaign_name: Name of campaign
        """
        stories = [
            f
            for f in os.listdir(campaign_path)
            if f.endswith(".md")
            and not f.startswith(("character_", "session_", "story_"))
        ]

        if not stories:
            print_error("No story files found.")
            return

        print(f"\nStories in {campaign_name}:")
        for i, story in enumerate(sorted(stories), 1):
            print(f"{i}. {story}")

        try:
            choice = int(input("\nSelect story (0 to back): "))
            if choice == 0:
                return
            if 1 <= choice <= len(stories):
                story_file = sorted(stories)[choice - 1]
                filepath = os.path.join(campaign_path, story_file)

                # Ask if user wants narration
                narrate_choice = (
                    input("\nNarrate this story with TTS? (y/n, default n): ")
                    .strip()
                    .lower()
                )
                should_narrate = narrate_choice == "y"

                # Display with optional narration
                if should_narrate:
                    display_story_file(filepath, narrate=True)
                else:
                    display_any_file(filepath)
            else:
                print_error("Invalid choice.")
        except ValueError:
            print_error("Invalid input.")

    def _read_character_profiles(self, party_members: List[str]):
        """Read character profiles for party members.

        Args:
            party_members: List of party member names
        """
        if not party_members:
            print_error("No party members configured for this campaign.")
            return

        chars_dir = os.path.join(self.workspace_path, "game_data", "characters")

        # Find character files by matching JSON name field
        available_chars = []
        try:
            for char_file in os.listdir(chars_dir):
                if not char_file.endswith(".json"):
                    continue

                filepath = os.path.join(chars_dir, char_file)
                with open(filepath, "r", encoding="utf-8") as f:
                    char_data = json.load(f)
                    char_name = char_data.get("name", "")

                    # Check if this character is in the party
                    if char_name in party_members:
                        available_chars.append((char_name, filepath))
        except (OSError, ValueError):
            pass

        if not available_chars:
            print_error("No character profile files found for party members.")
            return

        print("\nParty Character Profiles:")
        for i, (name, _) in enumerate(available_chars, 1):
            print(f"{i}. {name}")

        try:
            choice = int(input("\nSelect character (0 to back): "))
            if choice == 0:
                return
            if 1 <= choice <= len(available_chars):
                _, char_file = available_chars[choice - 1]
                display_any_file(char_file)
            else:
                print_error("Invalid choice.")
        except ValueError:
            print_error("Invalid input.")

    def _read_session_results(self, campaign_path: str):
        """Read session results files.

        Args:
            campaign_path: Path to campaign directory
        """
        results = [
            f
            for f in os.listdir(campaign_path)
            if f.startswith("session_results_") and f.endswith(".md")
        ]

        if not results:
            print_error("No session results files found.")
            return

        print("\nSession Results:")
        for i, result in enumerate(sorted(results), 1):
            print(f"{i}. {result}")

        try:
            choice = int(input("\nSelect session (0 to back): "))
            if choice == 0:
                return
            if 1 <= choice <= len(results):
                result_file = sorted(results)[choice - 1]
                filepath = os.path.join(campaign_path, result_file)
                display_any_file(filepath)
            else:
                print_error("Invalid choice.")
        except ValueError:
            print_error("Invalid input.")

    def _read_development_files(self, campaign_path: str):
        """Read character development files.

        Args:
            campaign_path: Path to campaign directory
        """
        dev_files = [
            f
            for f in os.listdir(campaign_path)
            if f.startswith("character_development_") and f.endswith(".md")
        ]

        if not dev_files:
            print_error("No character development files found.")
            return

        print("\nCharacter Development Files:")
        for i, dev_file in enumerate(sorted(dev_files), 1):
            print(f"{i}. {dev_file}")

        try:
            choice = int(input("\nSelect file (0 to back): "))
            if choice == 0:
                return
            if 1 <= choice <= len(dev_files):
                dev_file = sorted(dev_files)[choice - 1]
                filepath = os.path.join(campaign_path, dev_file)
                display_any_file(filepath)
            else:
                print_error("Invalid choice.")
        except ValueError:
            print_error("Invalid input.")
