"""
Story Management CLI Module

Handles all story-related menu interactions and operations.
"""

import os
from typing import List


class StoryCLIManager:
    """Manages story-related CLI operations."""

    def __init__(self, story_manager, workspace_path):
        """
        Initialize story CLI manager.

        Args:
            story_manager: StoryManager instance
            workspace_path: Root workspace path
        """
        self.story_manager = story_manager
        self.workspace_path = workspace_path

    def manage_stories(self):
        """Story management submenu."""
        while True:
            print("\n STORY MANAGEMENT")
            print("-" * 30)

            # Show current existing stories
            existing_stories = self.story_manager.get_existing_stories()
            story_series = self.story_manager.get_story_series()

            if existing_stories:
                print(f"📖 Existing Stories ({len(existing_stories)})")
                for story in existing_stories:
                    print(f"   • {story}")
                print()

            if story_series:
                print(f"📂 Story Series ({len(story_series)})")
                for series in story_series:
                    series_stories = self.story_manager.get_story_files_in_series(
                        series
                    )
                    print(f"   • {series}/ ({len(series_stories)} stories)")
                print()

            print("1. Work with Existing Stories")
            print("2. Create New Story Series")
            print("3. Work with Story Series")
            print("0. Back to Main Menu")

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self._manage_existing_stories()
            elif choice == "2":
                self._create_new_story_series()
            elif choice == "3":
                self._manage_story_series()
            elif choice == "0":
                break
            else:
                print("Invalid choice.")

    def create_new_story(self):
        """Create a new story file (public API for external callers)."""
        self._create_new_story()

    def _manage_existing_stories(self):
        """Manage existing stories in root directory."""
        while True:
            print("\n📖 EXISTING STORIES")
            print("-" * 25)

            existing_stories = self.story_manager.get_existing_stories()

            if not existing_stories:
                print("No existing stories found.")
                print("1. Create New Story (in root)")
                print("0. Back")

                choice = input("Enter your choice: ").strip()
                if choice == "1":
                    self._create_new_story()
                elif choice == "0":
                    break
                continue

            print("Stories:")
            for i, filename in enumerate(existing_stories, 1):
                print(f"{i}. {filename}")

            print("\nOptions:")
            print("1. Create New Story (in root)")
            print("2. View Story Details")
            print("0. Back")

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self._create_new_story()
            elif choice == "2":
                self._view_story_details(existing_stories)
            elif choice == "0":
                break
            else:
                print("Invalid choice.")

    def _manage_story_series(self):
        """Manage story series folders."""
        story_series = self.story_manager.get_story_series()

        if not story_series:
            print("\n📂 No story series found.")
            print("Create a new story series from the main story menu.")
            return

        print("\n📂 STORY SERIES")
        print("-" * 20)
        for i, series in enumerate(story_series, 1):
            series_stories = self.story_manager.get_story_files_in_series(series)
            print(f"{i}. {series}/ ({len(series_stories)} stories)")

        try:
            choice = int(input("\nSelect series to manage (0 to back): "))
            if choice == 0:
                return
            if 1 <= choice <= len(story_series):
                selected_series = story_series[choice - 1]
                self._manage_single_series(selected_series)
            else:
                print("Invalid choice.")
        except ValueError:
            print("Invalid input.")

    def _manage_single_series(self, series_name: str):
        """Manage a single story series."""
        while True:
            print(f"\n📂 SERIES: {series_name}")
            print("-" * (len(series_name) + 10))

            series_stories = self.story_manager.get_story_files_in_series(series_name)

            if series_stories:
                print("Stories in series:")
                for i, story in enumerate(series_stories, 1):
                    print(f"{i}. {story}")
            else:
                print("No stories in this series yet.")

            print("\nOptions:")
            print("1. Add New Story to Series")
            print("2. View Story Details")
            print("0. Back")

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self._create_story_in_series(series_name)
            elif choice == "2" and series_stories:
                self._view_story_details_in_series(series_name, series_stories)
            elif choice == "0":
                break
            else:
                print("Invalid choice.")

    def _create_new_story_series(self):
        """Create a new story series."""
        print("\n📁 CREATE NEW STORY SERIES")
        print("-" * 30)

        series_name = input("Enter series name: ").strip()
        if not series_name:
            print("Series name cannot be empty.")
            return

        first_story_name = input("Enter first story name: ").strip()
        if not first_story_name:
            print("Story name cannot be empty.")
            return

        description = input("Enter story description (optional): ").strip()

        try:
            filepath = self.story_manager.create_new_story_series(
                series_name, first_story_name, description
            )
            print(f"\n[SUCCESS] Created story series: {series_name}")
            print(f"   First story: {first_story_name}")
            print(f"   Location: {filepath}")
        except (OSError, ValueError, KeyError) as e:
            print(f"[ERROR] Error creating story series: {e}")

    def _create_story_in_series(self, series_name: str):
        """Create a new story in an existing series."""
        story_name = input(
            f"\nEnter story name for series '{series_name}': "
        ).strip()
        if not story_name:
            print("Story name cannot be empty.")
            return

        description = input("Enter story description (optional): ").strip()

        try:
            filepath = self.story_manager.create_story_in_series(
                series_name, story_name, description
            )
            print(f"\n[SUCCESS] Created story in {series_name}")
            print(f"   Location: {filepath}")
        except (OSError, ValueError, KeyError) as e:
            print(f"[ERROR] Error creating story: {e}")

    def _view_story_details(self, stories: List[str]):
        """View details of a story from a list."""
        try:
            choice = int(input(f"\nSelect story to view (1-{len(stories)}): "))
            if 1 <= choice <= len(stories):
                story_file = stories[choice - 1]
                story_path = os.path.join(self.story_manager.stories_path, story_file)
                self._display_story_info(story_path, story_file)
            else:
                print("Invalid choice.")
        except ValueError:
            print("Invalid input.")

    def _view_story_details_in_series(self, series_name: str, stories: List[str]):
        """View details of a story within a series."""
        try:
            choice = int(input(f"\nSelect story to view (1-{len(stories)}): "))
            if 1 <= choice <= len(stories):
                story_file = stories[choice - 1]
                story_path = os.path.join(
                    self.story_manager.stories_path, series_name, story_file
                )
                self._display_story_info(story_path, f"{series_name}/{story_file}")
            else:
                print("Invalid choice.")
        except ValueError:
            print("Invalid input.")

    def _display_story_info(self, story_path: str, display_name: str):
        """Display information about a story file."""
        try:
            with open(story_path, "r", encoding="utf-8") as f:
                content = f.read()

            print(f"\n📖 STORY: {display_name}")
            print("-" * (len(display_name) + 10))

            lines = content.split("\n")
            if lines:
                title_line = lines[0].strip()
                if title_line.startswith("#"):
                    print(f"Title: {title_line}")
                else:
                    print(f"Title: {title_line}")

            print(f"File size: {len(content)} characters")
            print(f"Lines: {len(lines)}")

            # Show first few lines as preview
            print("\nPreview (first 3 lines):")
            for line in lines[:3]:
                if line.strip():
                    print(f"  {line[:100]}...")

        except OSError as e:
            print(f"[ERROR] Error reading story: {e}")

    def _create_new_story(self):
        """Create a new story file."""
        story_name = input("\nEnter story name: ").strip()
        if not story_name:
            print("Story name cannot be empty.")
            return

        description = input("Enter story description (optional): ").strip()

        filepath = self.story_manager.create_new_story(story_name, description)
        print(f"\n[SUCCESS] Created story file: {os.path.basename(filepath)}")
        print(f"📁 Location: {filepath}")
        print("\nYou can now open this file in VSCode and start writing your story!")
