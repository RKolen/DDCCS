"""
Main D&D Character Consultant Interface
VSCode-integrated system for story management and character consultation.
"""

import argparse
import os
from src.stories.enhanced_story_manager import EnhancedStoryManager
from src.stories.story_manager import StoryManager
from src.dm.dungeon_master import DMConsultant
from src.cli.cli_character_manager import CharacterCLIManager
from src.cli.cli_story_manager import StoryCLIManager
from src.cli.cli_consultations import ConsultationsCLI
from src.cli.cli_story_analysis import StoryAnalysisCLI
from src.ai.availability import AI_AVAILABLE
from src.ai.ai_client import AIClient


class DDConsultantCLI:
    """Command-line interface for the D&D Character Consultant system."""

    def __init__(self, workspace_path: str = None, campaign_name: str = None):
        self.workspace_path = workspace_path or os.getcwd()

        # Initialize AI client if available
        ai_client = None
        if AI_AVAILABLE:
            try:
                ai_client = AIClient()
            except (OSError, ValueError) as e:
                print(f"[INFO] AI client initialization failed: {e}")
                print("[INFO] Continuing with AI features disabled.")

        # By default use the original StoryManager to preserve existing
        # behavior. Only use the EnhancedStoryManager when a campaign name is
        # explicitly provided so the CLI's --campaign flag enables the richer
        # per-campaign behavior without changing the default runtime.
        if campaign_name:
            self.story_manager = EnhancedStoryManager(
                self.workspace_path, campaign_name=campaign_name, ai_client=ai_client
            )
        else:
            self.story_manager = StoryManager(self.workspace_path, ai_client=ai_client)
        self.dm_consultant = DMConsultant(self.workspace_path)

        # Initialize manager modules
        self.character_manager = CharacterCLIManager(
            self.story_manager, None  # combat_narrator passed separately
        )
        self.story_cli = StoryCLIManager(self.story_manager, self.workspace_path)
        self.consultations = ConsultationsCLI(self.story_manager, self.dm_consultant)
        self.story_analysis = StoryAnalysisCLI(
            self.story_manager, self.workspace_path
        )

    def run_interactive(self):
        """Run the interactive command-line interface."""
        print("[D&D] D&D Character Consultant System")
        print("=" * 50)
        print(f"Workspace: {self.workspace_path}")
        print(f"Characters loaded: {len(self.story_manager.consultants)}")
        print()

        while True:
            self._show_main_menu()
            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self.character_manager.manage_characters()
            elif choice == "2":
                self.story_cli.manage_stories()
            elif choice == "3":
                self.consultations.get_character_consultation()
            elif choice == "4":
                self.story_analysis.analyze_story()
            elif choice == "5":
                self.story_analysis.convert_combat()
            elif choice == "6":
                self.consultations.get_dc_suggestions()
            elif choice == "7":
                self.consultations.get_dm_narrative_suggestions()
            elif choice == "0":
                print("Goodbye! May your adventures be epic!")
                break
            else:
                print("Invalid choice. Please try again.")

    def run_command(self, command: str, story_file: str = None):
        """
        Run a specific command non-interactively.

        Args:
            command: Command to execute (e.g., 'analyze')
            story_file: Optional story file path for commands that need it
        """
        if command == "analyze":
            if story_file:
                print(f"Analyzing story file: {story_file}")
            self.story_analysis.analyze_story()
        else:
            print(f"Unknown command: {command}")

    def _show_main_menu(self):
        """Display the main menu."""
        print("\n[MENU] MAIN MENU")
        print("-" * 30)
        print("1. Manage Characters")
        print("2. Manage Stories")
        print("3. Get Character Consultation")
        print("4. Analyze Story File")
        print("5. Convert Combat Summary")
        print("6. Get DC Suggestions")
        print("7. Get DM Narrative Suggestions")
        print("0. Exit")
        print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="D&D Character Consultant System")
    parser.add_argument("--workspace", help="Workspace directory path", default=None)
    parser.add_argument(
        "--campaign",
        help="Campaign name to use for campaign-local settings (uses game_data/campaigns/<name>/)",
        default=None,
    )
    parser.add_argument(
        "--command",
        help="Command to run",
        choices=["interactive", "analyze"],
    )
    parser.add_argument("--story", help="Story file to analyze")

    args = parser.parse_args()

    workspace = args.workspace or os.getcwd()
    campaign = args.campaign

    try:
        # Inform the user that game data is being prepared; this can take a
        # short while on first run while characters and caches are loaded.
        print("[INFO] Setting up game data and loading resources — this may take a while...")
        cli = DDConsultantCLI(workspace, campaign)

        if args.command == "analyze":
            # Non-interactive analyze command
            cli.run_command("analyze", args.story)
        else:
            # Default to interactive mode
            cli.run_interactive()

    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    except (OSError, ValueError, KeyError, AttributeError) as e:
        print(f"\n[ERROR] Error: {e}")
        print("Please check your setup and try again.")


if __name__ == "__main__":
    main()
