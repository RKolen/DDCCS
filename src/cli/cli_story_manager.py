"""
Story Management CLI Module

Handles all story-related menu interactions and operations.
"""

import os
import json
from typing import List, Optional
from datetime import datetime

from src.cli.party_config_manager import (
    save_current_party,
    load_current_party,
    load_party_with_profiles,
)
from src.stories.story_workflow_orchestrator import (
    coordinate_story_workflow,
    StoryWorkflowContext,
    WorkflowOptions,
)
from src.stories.story_ai_generator import generate_story_from_prompt
from src.stories.story_file_manager import (
    StoryFileContext,
    StoryCreationOptions,
    create_new_story_series,
    create_story_in_series,
)
from src.stories.story_updater import StoryUpdater
from src.stories.session_results_manager import (
    StorySession,
    create_session_results_file,
)
from src.stories.character_action_analyzer import extract_character_actions
from src.cli.story_amender_cli_handler import StoryAmenderCLIHandler
from src.characters.character_consistency import create_character_development_file
from src.utils.file_io import read_text_file
from src.utils.string_utils import truncate_at_sentence
from src.cli.dnd_cli_helpers import (
    get_continuation_scene_type,
    get_continuation_prompt,
)
from src.cli.cli_story_analysis import StoryAnalysisCLI
from src.cli.cli_consultations import ConsultationsCLI
from src.cli.cli_story_config_helper import (
    build_story_config,
    display_story_prompt_guidance,
)
from src.utils.terminal_display import display_story_file
from src.cli.cli_story_helpers import (
    CharacterSelectionHelper,
    StoryContinuationHelper,
)


class StoryCLIManager:
    """Manages story-related CLI operations."""

    def __init__(self, story_manager, workspace_path, dm_consultant=None):
        """Initialize story CLI manager."""
        self.story_manager = story_manager
        self.workspace_path = workspace_path
        self.story_updater = StoryUpdater()
        self.analysis_cli = StoryAnalysisCLI(story_manager, workspace_path)
        self.consultations_cli = ConsultationsCLI(story_manager, dm_consultant)
        self.char_helper = CharacterSelectionHelper(workspace_path)
        self.cont_helper = StoryContinuationHelper(story_manager, workspace_path)

    def get_series_count(self) -> int:
        """Return number of story series available."""
        return len(self.story_manager.get_story_series())

    def _list_available_characters(self) -> List[str]:
        """Return names of available characters from game_data/characters."""
        return self.char_helper.list_available_characters()

    def _select_party_members(
        self, available: List[str], series_name: str
    ) -> List[str]:
        """Prompt user to select party members from available list."""
        return self.char_helper.select_party_members(available, series_name)

    def manage_stories(self):
        """Story management submenu."""
        while True:
            print("\n STORY MANAGEMENT")
            print("-" * 30)

            # Show current existing stories
            existing_stories = self.story_manager.get_existing_stories()
            story_series = self.story_manager.get_story_series()

            if existing_stories:
                print(f" Existing Stories ({len(existing_stories)})")
                for story in existing_stories:
                    print(f"   • {story}")
                print()

            if story_series:
                print(f" Story Series ({len(story_series)})")
                for series in story_series:
                    series_stories = self.story_manager.get_story_files_in_series(
                        series
                    )
                    print(f"   • {series}/ ({len(series_stories)} stories)")
                print()

            print("1. Create New Story Series")
            print("2. Work with Story Series")
            print("0. Back to Main Menu")

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self._create_new_story_series()
            elif choice == "2":
                self._manage_story_series()
            elif choice == "0":
                break
            else:
                print("Invalid choice.")

    def _manage_story_series(self):
        """Manage story series folders."""
        story_series = self.story_manager.get_story_series()

        if not story_series:
            print("\n No story series found.")
            print("Create a new story series from the main story menu.")
            return

        print("\n STORY SERIES")
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
            print(f"\n SERIES: {series_name}")
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
            print("3. Generate Session Results")
            print("4. Generate Character Development")
            print("5. Analyze Story File")
            print("6. Convert Combat to Narrative")
            print("7. Get DC Suggestions")
            print("8. Get DM Narrative Suggestions")
            print("9. Story Analysis (Slow)")
            print("10. Character Analysis (Slow)")
            print("11. Amend Story Character Actions")
            print("0. Back")

            choice = input("Enter your choice: ").strip()
            if choice == "0":
                break
            self._dispatch_series_choice(choice, series_name, series_stories)

    def _dispatch_series_choice(
        self, choice: str, series_name: str, series_stories: List[str]
    ):
        """Dispatch series management menu choice to appropriate handler.

        Uses decision table to avoid branch complexity.

        Args:
            choice: User menu choice
            series_name: Selected series name
            series_stories: List of story files in series
        """
        story_operations = [
            ("1", False, "_create_story_in_series"),
            ("2", True, "_view_story_details_in_series"),
            ("3", True, "_generate_session_results_for_story"),
            ("4", True, "_generate_character_development_for_story"),
            ("5", False, "_analyze_story_cli"),
            ("6", False, "_convert_combat_cli"),
            ("7", False, "_get_dc_suggestions_cli"),
            ("8", False, "_get_dm_narrative_cli"),
            ("9", True, "_analyze_series_consistency"),
            ("10", True, "_analyze_character_development_series"),
            ("11", True, "_amend_story_actions"),
        ]

        for op_choice, requires_stories, method_name in story_operations:
            if choice == op_choice:
                if requires_stories and not series_stories:
                    print("No stories in this series to perform this action.")
                    return
                self._execute_series_operation(method_name, series_name, series_stories)
                return

        print("Invalid choice.")

    def _execute_series_operation(
        self, method_name: str, series_name: str, series_stories: List[str]
    ):
        """Execute specified series operation.

        Args:
            method_name: Name of the operation method
            series_name: Selected series name
            series_stories: List of story files in series
        """
        if method_name == "_create_story_in_series":
            self._create_story_in_series(series_name)
        elif method_name == "_view_story_details_in_series":
            self._view_story_details_in_series(series_name, series_stories)
        elif method_name == "_generate_session_results_for_story":
            self._generate_session_results_for_story(series_name, series_stories)
        elif method_name == "_generate_character_development_for_story":
            self._generate_character_development_for_story(series_name, series_stories)
        elif method_name == "_analyze_story_cli":
            self.analysis_cli.analyze_story()
        elif method_name == "_convert_combat_cli":
            self.analysis_cli.convert_combat()
        elif method_name == "_get_dc_suggestions_cli":
            self.consultations_cli.get_dc_suggestions()
        elif method_name == "_get_dm_narrative_cli":
            self.consultations_cli.get_dm_narrative_suggestions()
        elif method_name == "_analyze_series_consistency":
            self.analysis_cli.analyze_series_consistency(series_name, series_stories)
        elif method_name == "_analyze_character_development_series":
            self.analysis_cli.analyze_character_development_series(
                series_name, series_stories
            )
        elif method_name == "_amend_story_actions":
            self._amend_story_actions(series_name, series_stories)

    def _orchestrate_story_creation(
        self, story_path: str, series_path: str, party_names: List[str]
    ) -> None:
        """Execute workflow orchestration after story file creation."""
        try:
            story_content = read_text_file(story_path)
            if not story_content:
                print(f"[WARNING] Could not read story file: {story_path}")
                return
        except OSError as e:
            print(f"[WARNING] Could not read story file: {e}")
            return

        # Extract story name
        story_filename = os.path.basename(story_path)
        story_name = os.path.splitext(story_filename)[0]

        # Clean metadata (Created, Description) and generate title
        story_content = self.story_updater.clean_story_content(story_content)
        with open(story_path, "w", encoding="utf-8") as f:
            f.write(story_content)

        self._generate_story_title_if_available(story_path)

        # Re-read final content
        try:
            story_content = read_text_file(story_path)
            if not story_content:
                story_content = ""
        except OSError:
            story_content = ""

        # Build context and run orchestrator
        ctx = StoryWorkflowContext(
            story_name=story_name,
            story_content=story_content,
            series_path=series_path,
            workspace_path=self.workspace_path,
            party_names=party_names,
            ai_client=self.story_manager.ai_client,
        )

        try:
            options = WorkflowOptions(ai_client=self.story_manager.ai_client)
            results = coordinate_story_workflow(ctx, options=options)

            # Display results to user
            if results.get("npcs_suggested"):
                npcs = results["npcs_suggested"]
                print(f"\n[INFO] Auto-detected {len(npcs)} NPCs in your story:")
                for npc in npcs:
                    print(f"   - {npc}")

            if results.get("hooks_file"):
                print("[OK] Story hooks file created")
            if results.get("character_dev_file"):
                print("[OK] Character development file created")
            if results.get("session_file"):
                print("[OK] Session results file created")

            if results.get("errors"):
                print("\n[WARNINGS]")
                for err in results["errors"]:
                    print(f"   - {err}")
        except (ValueError, OSError, KeyError, AttributeError) as e:
            print(f"[WARNING] Workflow orchestration encountered issues: {e}")

    def _generate_story_title_if_available(self, story_path: str) -> None:
        """Generate and update story title if AI client is available.

        Args:
            story_path: Path to the story file
        """
        if not self.story_manager.ai_client:
            return

        try:
            content = read_text_file(story_path)
            if not content:
                return

            # Generate title from content
            generated_title = self.story_updater.extract_narrative_title(
                content, self.story_manager.ai_client
            )
            if not generated_title or generated_title == "Story Continuation":
                return

            # Replace H1 header with generated title
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("# "):
                    lines[i] = f"# {generated_title}"
                    updated_content = "\n".join(lines)
                    with open(story_path, "w", encoding="utf-8") as f:
                        f.write(updated_content)
                    print(f"[SUCCESS] Generated story title: {generated_title}")
                    return
        except (OSError, AttributeError) as e:
            print(f"[DEBUG] Could not generate story title: {e}")

    def _collect_story_creation_options(
        self,
        series_name: str = "",
        campaign_dir: Optional[str] = None,
        previous_stories: Optional[List[str]] = None,
        party_members: Optional[List[str]] = None,
    ) -> StoryCreationOptions:
        """Collect template and AI generation options from user."""
        # Ensure only needed characters are loaded for profile lookup
        # If party_members provided, use load_party_characters instead of loading all
        if party_members:
            if not self.story_manager.is_characters_loaded():
                print(
                    f"\n[INFO] Loading {len(party_members)}"
                    " party members... this may take a moment."
                )
                self.story_manager.load_party_characters(party_members)
                print(f"[OK] Loaded party: {', '.join(party_members)}")
        else:
            if not self.story_manager.is_characters_loaded():
                print(
                    "[INFO] Loading all characters for story generation... this may take a moment."
                )
                self.story_manager.ensure_characters_loaded()

        use_template = False
        template_choice = (
            input("\nUse story template with guidance? (y/n): ").strip().lower()
        )
        if template_choice == "y":
            use_template = True

        ai_generated_content = ""
        if not self.story_manager.ai_client:
            return StoryCreationOptions(
                use_template=use_template,
                ai_generated_content=ai_generated_content,
            )

        ai_choice = input("Generate initial story with AI? (y/n): ").strip().lower()
        if ai_choice != "y":
            return StoryCreationOptions(
                use_template=use_template,
                ai_generated_content=ai_generated_content,
            )

        # Prompt for story
        display_story_prompt_guidance("initial")
        story_prompt = input("Story prompt: ").strip()
        if not story_prompt:
            return StoryCreationOptions(
                use_template=use_template,
                ai_generated_content=ai_generated_content,
            )

        # Generate with context
        try:
            story_config = build_story_config(
                self.workspace_path,
                series_name,
                campaign_dir,
                previous_stories,
                story_prompt,
                party_members=party_members,
                story_manager=self.story_manager,
            )
            ai_generated_content = (
                generate_story_from_prompt(
                    self.story_manager.ai_client,
                    story_prompt,
                    story_config if story_config else None,
                )
                or ""
            )
        except (ValueError, AttributeError) as e:
            print(f"[WARNING] AI generation failed: {e}")

        return StoryCreationOptions(
            use_template=use_template,
            ai_generated_content=ai_generated_content,
        )

    def _create_new_story_series(self):
        """Create a new story series with optional AI generation and templates."""
        print("\n CREATE NEW STORY SERIES")
        print("-" * 30)

        # Ask for series name first and validate immediately
        series_name = self._get_validated_series_name()
        if not series_name:
            return

        first_story_name = input("Enter first story name: ").strip()
        if not first_story_name:
            print("Story name cannot be empty.")
            return

        description = input("Enter story description (optional): ").strip()

        # Party members prompt — list available characters and select members
        available = self._list_available_characters()
        party_members = self._select_party_members(available, series_name)

        # Collect template and AI options from user
        # Campaign dir doesn't exist yet, but pass party_members directly
        campaign_dir = os.path.join(
            self.workspace_path, "game_data", "campaigns", series_name
        )
        options = self._collect_story_creation_options(
            series_name=series_name,
            campaign_dir=campaign_dir,
            party_members=party_members,
        )

        try:
            # Create story with context
            ctx = StoryFileContext(
                stories_path=self.workspace_path,
                workspace_path=self.workspace_path,
            )
            filepath = create_new_story_series(
                ctx,
                series_name,
                first_story_name,
                description=description,
                options=options,
            )

            # Save party configuration into campaign folder (always write a file,
            # even if the user accepted defaults or left the input blank)
            campaign_folder = os.path.dirname(filepath)
            party_config_path = os.path.join(campaign_folder, "current_party.json")
            save_current_party(party_members, config_path=party_config_path)

            print(f"\n[SUCCESS] Created story series: {series_name}")
            print(f"   First story: {first_story_name}")
            print(f"   Location: {filepath}")
            print(f"   Current party saved: {party_config_path}")

            # Run workflow orchestration to create auxiliary files
            print("\n[INFO] Processing story for NPCs, hooks, and analysis...")
            self._orchestrate_story_creation(filepath, campaign_folder, party_members)
        except (OSError, ValueError, KeyError) as e:
            print(f"[ERROR] Error creating story series: {e}")

    def _get_validated_series_name(self) -> str:
        """Prompt user for series name and validate it has proper suffix.

        Returns:
            Validated series name or empty string if user cancels
        """
        valid_suffixes = ["_Campaign", "_Quest", "_Story", "_Adventure"]

        while True:
            series_name = input(
                "Enter series name (must end with: _Campaign, _Quest, _Story, or _Adventure): "
            ).strip()

            if not series_name:
                print("Series name cannot be empty.")
                continue

            if any(series_name.endswith(suf) for suf in valid_suffixes):
                return series_name

            suggestion = f"{series_name}_Campaign"
            print(
                "Series name MUST end with: _Campaign, _Quest, _Story, or _Adventure."
            )
            print(f"Suggestion: '{suggestion}'")
            response = input("Use suggested name? (y/n): ").strip().lower()
            if response == "y":
                return suggestion
            print("Please try again with a valid suffix.\n")

    def _create_story_in_series(self, series_name: str):
        """Create a new story in an existing series with optional AI generation."""
        # Load party members for this series (lazy loading - only loads what's needed)
        party_members = []
        try:
            party_members = load_current_party(
                workspace_path=self.workspace_path, campaign_name=series_name
            )
            print(f"[DEBUG] Loaded party config: {party_members}")
        except (ImportError, OSError, ValueError) as e:
            print(f"[DEBUG] Could not load party config: {e}")

        print(f"[DEBUG] party_members: {party_members}")
        print(
            f"[DEBUG] is_characters_loaded: {self.story_manager.is_characters_loaded()}"
        )

        # Load only the party members for this campaign (faster than loading all)
        if party_members and not self.story_manager.is_characters_loaded():
            print(
                f"[INFO] Loading {len(party_members)} party members for story generation..."
            )
            self.story_manager.load_party_characters(party_members)
        elif not self.story_manager.is_characters_loaded():
            # Fallback: no party config, load all characters
            print("[INFO] Loading characters for story generation...")
            self.story_manager.ensure_characters_loaded()

        story_name = input(f"\nEnter story name for series '{series_name}': ").strip()
        if not story_name:
            print("Story name cannot be empty.")
            return

        description = input("Enter story description (optional): ").strip()

        # Get existing stories in series for context
        series_path = os.path.join(
            self.workspace_path, "game_data", "campaigns", series_name
        )
        existing_stories = []
        if os.path.exists(series_path):
            existing_stories = [
                f
                for f in os.listdir(series_path)
                if os.path.isfile(os.path.join(series_path, f))
            ]

        # Collect template and AI options with series context
        options = self._collect_story_creation_options(
            series_name=series_name,
            campaign_dir=series_path,
            previous_stories=existing_stories,
        )

        try:
            # Create story with context
            ctx = StoryFileContext(
                stories_path=self.workspace_path,
                workspace_path=self.workspace_path,
            )
            filepath = create_story_in_series(
                ctx,
                series_name,
                story_name,
                description=description,
                options=options,
            )
            print(f"\n[SUCCESS] Created story in {series_name}")
            print(f"   Location: {filepath}")

            # Load party members for this series
            series_path = os.path.dirname(filepath)
            party_names = []
            try:
                party_names = load_current_party(
                    workspace_path=self.workspace_path, campaign_name=series_name
                )
            except (ImportError, OSError, ValueError):
                pass

            # Run workflow orchestration to create auxiliary files
            print("\n[INFO] Processing story for NPCs, hooks, and analysis...")
            self._orchestrate_story_creation(filepath, series_path, party_names)
        except (OSError, ValueError, KeyError) as e:
            print(f"[ERROR] Error creating story: {e}")

    def _view_story_details(self, stories: List[str]):
        """View details of a story from a list."""
        try:
            choice = int(input(f"\nSelect story to view (1-{len(stories)}): "))
            if 1 <= choice <= len(stories):
                story_file = stories[choice - 1]
                stories_base = os.path.join(
                    self.workspace_path, "game_data", "campaigns"
                )
                story_path = os.path.join(stories_base, story_file)
                self._display_story_info(story_path, story_file)
            else:
                print("Invalid choice.")
        except ValueError:
            print("Invalid input.")

    def _view_story_details_in_series(self, series_name: str, stories: List[str]):
        """View details of a story within a series."""
        try:
            print("\nStories available:")
            for i, story in enumerate(stories, 1):
                print(f"  {i}. {story}")

            choice = int(input(f"\nSelect story to view (1-{len(stories)}): "))
            if 1 <= choice <= len(stories):
                story_file = stories[choice - 1]
                stories_base = os.path.join(
                    self.workspace_path, "game_data", "campaigns"
                )
                story_path = os.path.join(stories_base, series_name, story_file)
                self._display_story_info(story_path, f"{series_name}/{story_file}")
            else:
                print("Invalid choice.")
        except ValueError:
            print("Invalid input.")

    def _display_story_info(self, story_path: str, display_name: str):
        """Display information about a story file and offer AI continuation."""
        try:
            with open(story_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Ask if user wants rich formatted display
            use_rich = input("\nView with rich formatting? (y/n): ").strip().lower()

            if use_rich == "y":
                display_story_file(story_path, story_name=display_name)
            else:
                # Plain text display
                print(f"\n STORY: {display_name}")
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

            # Initialize AI client on-demand if needed
            if not self.story_manager.ai_client:
                print("\n[INFO] Initializing AI client...")
                try:
                    self.story_manager.ai_client = AIClient()
                    print("[SUCCESS] AI client ready")
                except (ImportError, ValueError) as e:
                    print(f"[ERROR] Failed to initialize AI client: {e}")
                    return

            # Offer AI continuation
            print("\n" + "=" * 60)
            add_content = (
                input("\nGenerate AI continuation for this story? (y/n): ")
                .strip()
                .lower()
            )
            if add_content == "y":
                self._add_ai_continuation_to_story(story_path, display_name)

        except OSError as e:
            print(f"[ERROR] Error reading story: {e}")

    def _add_ai_continuation_to_story(self, story_path: str, display_name: str):
        """Add AI-generated continuation to an existing story.

        Prompts user to select continuation type (combat or exploration/social),
        then generates AI content using appropriate generator and party context.
        Appends to story file with supporting files.

        Args:
            story_path: Full path to the story file
            display_name: Display name for the story (for messages)
        """
        print("\n GENERATE AI CONTINUATION")
        print("-" * 40)

        # Get scene type from user
        is_combat = get_continuation_scene_type()
        if is_combat is None:
            return

        # Get continuation prompt from user
        story_prompt = get_continuation_prompt(is_combat)
        if not story_prompt:
            return

        print("\n[INFO] Generating story continuation with AI...")
        try:
            campaign_dir = os.path.dirname(story_path)

            if is_combat:
                self._handle_combat_continuation(story_path, display_name, story_prompt)
            else:
                self._handle_exploration_continuation(
                    story_path, display_name, story_prompt, campaign_dir
                )

        except (ValueError, AttributeError, OSError) as e:
            print(f"[ERROR] Failed to generate continuation: {e}")

    def _handle_combat_continuation(
        self, story_path: str, display_name: str, story_prompt: str
    ):
        """Handle combat narrative generation."""
        self.cont_helper.handle_combat_continuation(
            story_path, display_name, story_prompt
        )

    def _handle_exploration_continuation(
        self,
        story_path: str,
        display_name: str,
        story_prompt: str,
        campaign_dir: str,
    ):
        """Handle exploration/social narrative generation."""
        self.cont_helper.handle_exploration_continuation(
            story_path, display_name, story_prompt, campaign_dir
        )

    def _generate_session_results_for_story(self, series_name: str, stories: List[str]):
        """Generate session results for a story in the series.

        Args:
            series_name: Name of the story series (campaign)
            stories: List of story files in the series
        """
        try:
            selected_story = self._select_story_from_list(stories, series_name)
            if not selected_story:
                return

            story_file, story_name, campaign_path = selected_story

            # Load story content
            story_path = os.path.join(campaign_path, story_file)
            story_content = read_text_file(story_path)

            if not story_content:
                print("[ERROR] Story file is empty.")
                return

            # Load party members
            party_members = load_current_party(
                workspace_path=self.workspace_path, campaign_name=series_name
            )

            if not party_members:
                print("[ERROR] No party configured. Set up party first.")
                return

            print(f"\nParty members: {', '.join(party_members)}")

            # Load party with profiles for AI context
            party_characters = load_party_with_profiles(
                campaign_path, self.workspace_path
            )

            # Generate session results using AI (same as automated generation)
            print("\n[INFO] Analyzing story and generating session results...")

            session = StorySession(story_name, datetime.now().strftime("%Y-%m-%d"))

            # Use AI to analyze story if available
            if self.story_manager.ai_client:
                self._populate_session_with_ai_analysis(
                    session, story_content, party_characters
                )
            else:
                print("[WARNING] AI not available. Using basic session structure.")

            # Save session results
            try:
                filepath = create_session_results_file(campaign_path, session)
                print(f"\n[SUCCESS] Session results saved: {filepath}")
            except OSError as error:
                print(f"[ERROR] Error saving session results: {error}")

        except ValueError:
            print("Invalid input.")
        except (OSError, AttributeError) as e:
            print(f"[ERROR] Failed to generate session results: {e}")

    def _generate_character_development_for_story(
        self, series_name: str, stories: List[str]
    ):
        """Generate character development analysis for a story in the series.

        Args:
            series_name: Name of the story series (campaign)
            stories: List of story files in the series
        """
        try:
            selected_story = self._select_story_from_list(stories, series_name)
            if not selected_story:
                return

            story_file, story_name, campaign_path = selected_story

            # Load story content
            story_path = os.path.join(campaign_path, story_file)
            story_content = read_text_file(story_path)

            if not story_content:
                print("[ERROR] Story file is empty.")
                return

            # Load party members
            party_members = load_current_party(
                workspace_path=self.workspace_path, campaign_name=series_name
            )

            if not party_members:
                print("[ERROR] No party configured. Set up party first.")
                return

            print(f"\nParty members: {', '.join(party_members)}")

            # Generate character development
            print("\n[INFO] Analyzing story and generating character development...")

            # Extract character actions using personality-aware analysis
            character_actions = extract_character_actions(
                story_content,
                party_members,
                truncate_at_sentence,
                character_profiles=self._load_character_profiles_for_analysis(
                    party_members, campaign_path
                ),
            )

            if not character_actions:
                print("[WARNING] No character actions found in story.")
                return

            # Save character development file
            try:
                filepath = create_character_development_file(
                    campaign_path, story_name, character_actions
                )
                print(f"[SUCCESS] Character development saved to: {filepath}")
            except (OSError, AttributeError) as e:
                print(f"[ERROR] Failed to save character development: {e}")

        except ValueError:
            print("Invalid input.")
        except (OSError, AttributeError) as e:
            print(f"[ERROR] Failed to generate character development: {e}")

    def _amend_story_actions(self, series_name: str, stories: List[str]):
        """Interactive story character action amendment.

        Args:
            series_name: Name of the story series (campaign)
            stories: List of story files in the series
        """
        handler = StoryAmenderCLIHandler(
            self.workspace_path, self._load_character_profiles_for_analysis
        )
        handler.handle_amendment(series_name, stories, self._select_story_from_list)

    def _load_character_profiles_for_analysis(
        self, party_names: List[str], _campaign_path: str
    ) -> dict:
        """Load character profiles for personality-aware analysis."""
        profiles = {}
        for character_name in party_names:
            # Use first name (first word) as filename convention
            first_name = character_name.split()[0].lower()
            # Try to find character profile in workspace
            char_path = os.path.join(
                self.workspace_path, "game_data", "characters", f"{first_name}.json"
            )
            if os.path.exists(char_path):
                try:
                    with open(char_path, "r", encoding="utf-8") as f:
                        profiles[character_name] = json.load(f)
                except (OSError, json.JSONDecodeError):
                    pass
        return profiles

    def _select_story_from_list(self, stories: List[str], series_name: str):
        """Select a story from a list and return its details.

        Args:
            stories: List of story files
            series_name: Name of the series/campaign

        Returns:
            Tuple of (story_file, story_name, campaign_path) or None if invalid
        """
        print("\nStories available:")
        for i, story in enumerate(stories, 1):
            print(f"  {i}. {story}")

        choice_input = input(f"\nSelect story (1-{len(stories)}): ").strip()
        choice = int(choice_input)

        if choice < 1 or choice > len(stories):
            print("Invalid choice.")
            return None

        story_file = stories[choice - 1]
        story_name = os.path.splitext(story_file)[0]
        campaign_path = os.path.join(
            self.workspace_path, "game_data", "campaigns", series_name
        )

        return (story_file, story_name, campaign_path)

    def _populate_session_with_ai_analysis(
        self, session: StorySession, story_content: str, party_characters: dict
    ):
        """Populate session with AI-analyzed character actions and events."""
        self.cont_helper.populate_session_with_ai_analysis(
            session, story_content, party_characters
        )

    def _create_new_story(self):
        """Create a new story file."""
        story_name = input("\nEnter story name: ").strip()
        if not story_name:
            print("Story name cannot be empty.")
            return

        description = input("Enter story description (optional): ").strip()

        filepath = self.story_manager.create_new_story(story_name, description)
        print(f"\n[SUCCESS] Created story file: {os.path.basename(filepath)}")
        print(f" Location: {filepath}")
        print("\nYou can now open this file in VSCode and start writing your story!")
