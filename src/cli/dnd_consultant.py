"""
Main D&D Character Consultant Interface
VSCode-integrated system for story management and character consultation.
"""

import argparse
import os
from typing import Optional, Union

from src.ai.ai_client import get_client_for_task
from src.ai.availability import AI_AVAILABLE
from src.ai.task_router import ModelRegistry
from src.cli.cli_character_manager import CharacterCLIManager
from src.cli.cli_config import ConfigCLI
from src.cli.cli_enhancements import CLIEnhancementsMenu
from src.cli.cli_npc_manager import NpcCLIManager
from src.cli.cli_story_manager import StoryCLIManager
from src.cli.cli_story_reader import StoryReaderCLI
from src.cli.drupal_commands import run_sync_drupal
from src.cli.history import get_command_history
from src.cli.milvus_commands import run_milvus_status, run_reindex
from src.config.config_loader import load_config
from src.dm.dungeon_master import DMConsultant
from src.stories.enhanced_story_manager import EnhancedStoryManager
from src.stories.story_manager import StoryManager
from src.utils.cli_utils import display_selection_menu
from src.utils.errors import DnDError, handle_errors, wrap_exception, display_error


class DDConsultantCLI:
    """Command-line interface for the D&D Character Consultant system."""

    def __init__(self, workspace_path: str = "", campaign_name: str = ""):
        self.workspace_path = workspace_path or os.getcwd()

        # Initialize AI client if available
        # Uses lazy imports to avoid slow startup when AI is not configured
        ai_client = None
        if AI_AVAILABLE:
            try:
                ai_client = get_client_for_task("character_consultation")
            except (ValueError, OSError) as e:
                print(f"[WARNING] AI initialization failed: {e}")
                print("[INFO] Story generation will use templates only.")

        # By default use the original StoryManager to preserve existing
        # behavior. Only use the EnhancedStoryManager when a campaign name is
        # explicitly provided so the CLI's --campaign flag enables the richer
        # per-campaign behavior without changing the default runtime.
        # Enable lazy loading to improve startup time.
        self.story_manager: Union[StoryManager, EnhancedStoryManager]
        if campaign_name:
            self.story_manager = EnhancedStoryManager(
                self.workspace_path,
                campaign_name=campaign_name,
                ai_client=ai_client,
                lazy_load=True,
            )
        else:
            self.story_manager = StoryManager(
                self.workspace_path, ai_client=ai_client, lazy_load=True
            )
        dm_ai_client = None
        if AI_AVAILABLE:
            try:
                dm_ai_client = get_client_for_task("dc_evaluation")
            except (ValueError, OSError):
                pass
        self.dm_consultant = DMConsultant(
            self.workspace_path, ai_client=dm_ai_client, lazy_load=True
        )

        # Initialize manager modules
        self.character_manager = CharacterCLIManager(
            self.story_manager, None, self.dm_consultant
        )
        self.story_cli = StoryCLIManager(
            self.story_manager, self.workspace_path, self.dm_consultant
        )
        self.story_reader = StoryReaderCLI(self.workspace_path)
        self.npc_manager = NpcCLIManager(self.workspace_path)

    def run_interactive(self):
        """Run the interactive command-line interface."""
        print("[D&D] D&D Character Consultant System")
        print("=" * 50)
        print(f"Workspace: {self.workspace_path}")
        if self.story_manager.is_characters_loaded():
            print(f"Characters loaded: {len(self.story_manager.consultants)}")
        else:
            print("Characters: Not yet loaded (lazy loading enabled)")
        print()

        history = get_command_history()

        while True:
            self._show_main_menu()
            choice = input("Enter your choice: ").strip()

            if choice == "1":
                history.add_command("manage_characters")
                self.character_manager.manage_characters()
            elif choice == "2":
                history.add_command("manage_stories")
                self.story_cli.manage_stories()
            elif choice == "3":
                history.add_command("read_stories")
                self.story_reader.display_menu()
            elif choice == "4":
                history.add_command("manage_npcs")
                self.npc_manager.manage_npcs()
            elif choice == "5":
                history.add_command("configure_settings")
                config_cli = ConfigCLI()
                config_cli.run_config_menu()
            elif choice == "6":
                history.add_command("switch_model_profile")
                self._switch_model_profile_menu()
            elif choice == "7":
                history.add_command("tools_and_batch")
                CLIEnhancementsMenu().run()
            elif choice == "0":
                print("Goodbye! May your adventures be epic!")
                break
            else:
                print("Invalid choice. Please try again.")

    def run_command(self, command: str, story_file: Optional[str] = None):
        """
        Run a specific command non-interactively.

        Args:
            command: Command to execute (e.g., 'analyze')
            story_file: Optional story file path for commands that need it
        """
        if command == "analyze":
            if story_file:
                print(f"Analyzing story file: {story_file}")
            self.story_cli.analysis_cli.analyze_story()
        else:
            print(f"Unknown command: {command}")

    def _show_main_menu(self) -> None:
        """Display the main menu."""
        active = ModelRegistry.get_active_profile_name()
        print("\n[MENU] MAIN MENU")
        print("-" * 30)
        print("1. Manage Characters")
        print("2. Manage Stories")
        print("3. Read Stories")
        print("4. Manage NPCs")
        print("5. Configure Settings")
        print(f"6. Switch Model Profile  [active: {active}]")
        print("7. Tools & Batch Operations")
        print("0. Exit")
        print()

    def _switch_model_profile_menu(self) -> None:
        """Interactive menu for switching the active model profile."""
        profiles = ModelRegistry.list_profiles()
        if not profiles:
            print("[INFO] Model registry not initialized. Run with a config file"
                  " to enable profiles.")
            return

        active = ModelRegistry.get_active_profile_name()
        items = []
        names = []
        for name, prof in profiles.items():
            marker = " (active)" if name == active else ""
            desc = prof.description or f"{prof.provider} / {prof.model or 'env default'}"
            items.append(f"{name}{marker}  -  {desc}")
            names.append(name)

        idx = display_selection_menu(
            items,
            title="[SETTINGS] Switch Model Profile",
            prompt="Select profile",
            allow_zero_back=True,
        )
        if idx is None:
            print("No change.")
            return

        chosen = names[idx]
        if ModelRegistry.switch_profile(chosen):
            print(f"[OK] Active model profile switched to: {chosen}")
        else:
            print(f"[ERROR] Profile '{chosen}' not found in registry.")


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
    parser.add_argument(
        "--model",
        metavar="PROFILE",
        help="Activate a named model profile for this session (e.g. local, creative)",
    )
    parser.add_argument(
        "--reindex",
        action="store_true",
        help="Rebuild Milvus collections from all game_data files, then exit.",
    )
    parser.add_argument(
        "--milvus-status",
        action="store_true",
        help="Check Milvus connection and print collection statistics, then exit.",
    )
    parser.add_argument(
        "--sync-drupal",
        action="store_true",
        help=(
            "Push character and story updates to Drupal via JSON:API, then exit."
            " Requires DRUPAL_BASE_URL, DRUPAL_USER, and DRUPAL_PASSWORD."
            " Use with --campaign to also sync campaign story files."
        ),
    )

    args = parser.parse_args()

    workspace = args.workspace or os.getcwd()
    campaign = args.campaign or ""

    # Initialize model registry from config (session-only; never writes back to disk)
    _cfg = load_config()
    ModelRegistry.initialize(_cfg.model_registry)
    if args.model:
        if not ModelRegistry.switch_profile(args.model):
            print(f"[WARNING] Unknown model profile: '{args.model}'. Using default.")

    # Milvus utility commands exit immediately after running
    if args.reindex:
        run_reindex()
        return
    if args.milvus_status:
        run_milvus_status()
        return
    if args.sync_drupal:
        run_sync_drupal(campaign)
        return

    @handle_errors(OSError, ValueError, KeyError, AttributeError, default_return=None)
    def initialize_system(workspace: str, campaign: str):
        """Initialize the D&D Consultant system."""
        print("[INFO] Initializing D&D Character Consultant System...")
        return DDConsultantCLI(workspace, campaign)

    try:
        cli = initialize_system(workspace, campaign)

        if args.command == "analyze":
            # Non-interactive analyze command
            cli.run_command("analyze", args.story)
        else:
            # Default to interactive mode
            cli.run_interactive()

    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    except DnDError:
        # DnDError already handled by @handle_errors decorator
        pass
    except (RuntimeError, OSError, ValueError, KeyError, AttributeError, TypeError) as exc:
        # Wrap unknown exceptions
        dnd_error = wrap_exception(exc)
        display_error(dnd_error)
        print("Please check your setup and try again.")


if __name__ == "__main__":
    main()
