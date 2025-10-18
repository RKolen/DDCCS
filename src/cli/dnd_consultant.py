"""
Main D&D Character Consultant Interface
VSCode-integrated system for story management and character consultation.
"""

import argparse
import os
from typing import Dict, List, Any
from src.stories.story_manager import StoryManager
from src.combat.combat_narrator import CombatNarrator
from src.characters.consultants.character_profile import CharacterProfile
from src.dm.dungeon_master import DMConsultant
from src.cli.dnd_cli_helpers import edit_character_profile_interactive

# Optional AI client import
try:
    from src.ai.ai_client import AIClient
    AI_CLIENT_AVAILABLE = True
except ImportError:
    AIClient = None
    AI_CLIENT_AVAILABLE = False


class DDConsultantCLI:
    """Command-line interface for the D&D Character Consultant system."""

    def __init__(self, workspace_path: str = None):
        self.workspace_path = workspace_path or os.getcwd()
        self.story_manager = StoryManager(self.workspace_path)
        self.combat_narrator = CombatNarrator(self.story_manager.consultants)
        self.dm_consultant = DMConsultant(self.workspace_path)
        self.ai_client = None

    def run_interactive(self):
        """Run the interactive command-line interface."""
        print("🐉 D&D Character Consultant System 🐉")
        print("=" * 50)
        print(f"Workspace: {self.workspace_path}")
        print(f"Characters loaded: {len(self.story_manager.consultants)}")
        print()

        while True:
            self.show_main_menu()
            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self.manage_characters()
            elif choice == "2":
                self.manage_stories()
            elif choice == "3":
                self.get_character_consultation()
            elif choice == "4":
                self.analyze_story()
            elif choice == "5":
                self.convert_combat()
            elif choice == "6":
                self.get_dc_suggestions()
            elif choice == "7":
                self.get_dm_narrative_suggestions()
            elif choice == "0":
                print("Goodbye! May your adventures be epic! 🎲")
                break
            else:
                print("Invalid choice. Please try again.")

    def show_main_menu(self):
        """Display the main menu."""
        print("\\n📋 MAIN MENU")
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

    def manage_characters(self):
        """Character management submenu."""
        while True:
            print("\\n👥 CHARACTER MANAGEMENT")
            print("-" * 30)
            print("1. List Characters")
            print("2. Create Default 12-Character Party")
            print("3. Edit Character Profile")
            print("4. View Character Details")
            print("0. Back to Main Menu")

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self.list_characters()
            elif choice == "2":
                self.create_default_party()
            elif choice == "3":
                self.edit_character()
            elif choice == "4":
                self.view_character_details()
            elif choice == "0":
                break
            else:
                print("Invalid choice. Please try again.")

    def list_characters(self):
        """List all characters."""
        characters = self.story_manager.get_character_list()
        if not characters:
            print("\\n❌ No characters found. Create the default party first.")
            return

        print(f"\\n📜 CHARACTERS ({len(characters)})")
        print("-" * 40)
        for i, name in enumerate(characters, 1):
            profile = self.story_manager.get_character_profile(name)
            if profile:
                print(
                    f"{i}. {name} ({profile.character_class.value} Level {profile.level})"
                )
                if profile.personality_summary:
                    print(f"   {profile.personality_summary}")
        print()

    def create_default_party(self):
        """Create the default 12-character party."""
        print("\\n🎭 Creating default 12-character party...")

        default_profiles = self.story_manager.create_default_party()

        for profile in default_profiles:
            self.story_manager.save_character_profile(profile)

        # Reload consultants
        self.story_manager.load_characters()
        self.combat_narrator = CombatNarrator(self.story_manager.consultants)

        print(f"\\n✅ Created {len(default_profiles)} characters!")
        print("\\nYou can now edit their backgrounds and personalities using option 3.")

    def edit_character(self):
        """Edit a character profile."""
        characters = self.story_manager.get_character_list()
        if not characters:
            print("\\n❌ No characters found. Create the default party first.")
            return

        print("\\n✏️ EDIT CHARACTER")
        print("-" * 20)
        for i, name in enumerate(characters, 1):
            print(f"{i}. {name}")

        try:
            choice = int(input("Enter character number: ")) - 1
            if 0 <= choice < len(characters):
                character_name = characters[choice]
                profile = self.story_manager.get_character_profile(character_name)
                if profile:
                    self.edit_character_profile(profile)
            else:
                print("Invalid character number.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    def edit_character_profile(self, profile: CharacterProfile):
        """Edit a specific character profile."""
        profile = edit_character_profile_interactive(profile)
        self.story_manager.save_character_profile(profile)

    def view_character_details(self):
        """View detailed character information."""
        characters = self.story_manager.get_character_list()
        if not characters:
            print("\\n❌ No characters found.")
            return

        print("\\n👁️ VIEW CHARACTER DETAILS")
        print("-" * 30)
        for i, name in enumerate(characters, 1):
            print(f"{i}. {name}")

        try:
            choice = int(input("Enter character number: ")) - 1
            if 0 <= choice < len(characters):
                character_name = characters[choice]
                profile = self.story_manager.get_character_profile(character_name)
                if profile:
                    self.display_character_details(profile)
            else:
                print("Invalid character number.")
        except ValueError:
            print("Invalid input.")

    def display_character_details(self, profile: CharacterProfile):
        """Display detailed character information."""
        print(f"\\n📋 CHARACTER DETAILS: {profile.name}")
        print("=" * 50)
        print(f"Class: {profile.character_class.value}")
        print(f"Level: {profile.level}")
        print(f"\\nPersonality: {profile.personality_summary}")
        print(f"\\nBackground Story:\\n{profile.background_story}")

        if profile.motivations:
            print("\\nMotivations:")
            for motivation in profile.motivations:
                print(f"  • {motivation}")

        if profile.goals:
            print("\\nGoals:")
            for goal in profile.goals:
                print(f"  • {goal}")

        if profile.fears_weaknesses:
            print("\\nFears/Weaknesses:")
            for fear in profile.fears_weaknesses:
                print(f"  • {fear}")

        if profile.speech_patterns:
            print("\\nSpeech Patterns:")
            for pattern in profile.speech_patterns:
                print(f"  • {pattern}")

        if profile.decision_making_style:
            print(f"\\nDecision Making Style: {profile.decision_making_style}")

        input("\\nPress Enter to continue...")

    def manage_stories(self):
        """Story management submenu."""
        while True:
            print("\\n📚 STORY MANAGEMENT")
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
            print("4. Analyze Story File")
            print("0. Back to Main Menu")

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self.manage_existing_stories()
            elif choice == "2":
                self.create_new_story_series()
            elif choice == "3":
                self.manage_story_series()
            elif choice == "4":
                self.analyze_story()
            elif choice == "0":
                break
            else:
                print("Invalid choice.")

    def manage_existing_stories(self):
        """Manage existing stories in root directory."""
        while True:
            print("\\n📖 EXISTING STORIES")
            print("-" * 25)

            existing_stories = self.story_manager.get_existing_stories()

            if not existing_stories:
                print("No existing stories found.")
                print("1. Create New Story (in root)")
                print("0. Back")

                choice = input("Enter your choice: ").strip()
                if choice == "1":
                    self.create_new_story()
                elif choice == "0":
                    break
                continue

            print("Stories:")
            for i, filename in enumerate(existing_stories, 1):
                print(f"{i}. {filename}")

            print("\\nOptions:")
            print("1. Create New Story (in root)")
            print("2. View Story Details")
            print("0. Back")

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self.create_new_story()
            elif choice == "2":
                self.view_story_details(existing_stories)
            elif choice == "0":
                break
            else:
                print("Invalid choice.")

    def manage_story_series(self):
        """Manage story series folders."""
        story_series = self.story_manager.get_story_series()

        if not story_series:
            print("\\n📂 No story series found.")
            print("Create a new story series from the main story menu.")
            return

        print("\\n📂 STORY SERIES")
        print("-" * 20)
        for i, series in enumerate(story_series, 1):
            series_stories = self.story_manager.get_story_files_in_series(series)
            print(f"{i}. {series}/ ({len(series_stories)} stories)")

        try:
            choice = int(input("\\nSelect series to manage (0 to back): "))
            if choice == 0:
                return
            if 1 <= choice <= len(story_series):
                selected_series = story_series[choice - 1]
                self.manage_single_series(selected_series)
            else:
                print("Invalid choice.")
        except ValueError:
            print("Invalid input.")

    def manage_single_series(self, series_name: str):
        """Manage a single story series."""
        while True:
            print(f"\\n📂 SERIES: {series_name}")
            print("-" * (len(series_name) + 10))

            series_stories = self.story_manager.get_story_files_in_series(series_name)

            if series_stories:
                print("Stories in series:")
                for i, story in enumerate(series_stories, 1):
                    print(f"{i}. {story}")
            else:
                print("No stories in this series yet.")

            print("\\nOptions:")
            print("1. Add New Story to Series")
            print("2. View Story Details")
            print("0. Back")

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self.create_story_in_series(series_name)
            elif choice == "2" and series_stories:
                self.view_story_details_in_series(series_name, series_stories)
            elif choice == "0":
                break
            else:
                print("Invalid choice.")

    def create_new_story_series(self):
        """Create a new story series."""
        print("\\n� CREATE NEW STORY SERIES")
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
            print(f"\\n✅ Created story series: {series_name}")
            print(f"   First story: {first_story_name}")
            print(f"   Location: {filepath}")
        except (OSError, ValueError, KeyError) as e:
            print(f"❌ Error creating story series: {e}")

    def create_story_in_series(self, series_name: str):
        """Create a new story in an existing series."""
        story_name = input(f"\\nEnter story name for series '{series_name}': ").strip()
        if not story_name:
            print("Story name cannot be empty.")
            return

        description = input("Enter story description (optional): ").strip()

        try:
            filepath = self.story_manager.create_story_in_series(
                series_name, story_name, description
            )
            print(f"\\n✅ Created story in {series_name}")
            print(f"   Location: {filepath}")
        except (OSError, ValueError, KeyError) as e:
            print(f"❌ Error creating story: {e}")

    def view_story_details(self, stories: List[str]):
        """View details of a story from a list."""
        try:
            choice = int(input(f"\\nSelect story to view (1-{len(stories)}): "))
            if 1 <= choice <= len(stories):
                story_file = stories[choice - 1]
                story_path = os.path.join(self.story_manager.stories_path, story_file)
                self.display_story_info(story_path, story_file)
            else:
                print("Invalid choice.")
        except ValueError:
            print("Invalid input.")

    def view_story_details_in_series(self, series_name: str, stories: List[str]):
        """View details of a story within a series."""
        try:
            choice = int(input(f"\\nSelect story to view (1-{len(stories)}): "))
            if 1 <= choice <= len(stories):
                story_file = stories[choice - 1]
                story_path = os.path.join(
                    self.story_manager.stories_path, series_name, story_file
                )
                self.display_story_info(story_path, f"{series_name}/{story_file}")
            else:
                print("Invalid choice.")
        except ValueError:
            print("Invalid input.")

    def display_story_info(self, story_path: str, display_name: str):
        """Display information about a story file."""
        try:
            with open(story_path, "r", encoding="utf-8") as f:
                content = f.read()

            print(f"\\n📖 STORY: {display_name}")
            print("-" * (len(display_name) + 10))

            lines = content.split("\\n")
            if lines:
                title_line = lines[0].strip()
                if title_line.startswith("#"):
                    print(f"Title: {title_line}")
                else:
                    print(f"Title: {title_line}")

            print(f"File size: {len(content)} characters")
            print(f"Lines: {len(lines)}")

            # Show first few lines as preview
            print("\\nPreview (first 3 lines):")
            for line in lines[:3]:
                if line.strip():
                    print(f"  {line[:100]}...")

        except OSError as e:
            print(f"❌ Error reading story: {e}")

    def create_new_story(self):
        """Create a new story file."""
        story_name = input("\\nEnter story name: ").strip()
        if not story_name:
            print("Story name cannot be empty.")
            return

        description = input("Enter story description (optional): ").strip()

        filepath = self.story_manager.create_new_story(story_name, description)
        print(f"\\n✅ Created story file: {os.path.basename(filepath)}")
        print(f"📁 Location: {filepath}")
        print("\\nYou can now open this file in VSCode and start writing your story!")

    def get_character_consultation(self):
        """Get character consultation for a situation."""
        characters = self.story_manager.get_character_list()
        if not characters:
            print("\\n❌ No characters found.")
            return

        print("\\n🤔 CHARACTER CONSULTATION")
        print("-" * 30)
        print("Select a character:")
        for i, name in enumerate(characters, 1):
            print(f"{i}. {name}")

        try:
            choice = int(input("Enter character number: ")) - 1
            if 0 <= choice < len(characters):
                character_name = characters[choice]
                situation = input("\\nDescribe the situation: ").strip()

                if situation:
                    reaction = self.story_manager.suggest_character_reaction(
                        character_name, situation
                    )
                    self.display_character_reaction(reaction)
            else:
                print("Invalid character number.")
        except ValueError:
            print("Invalid input.")

    def display_character_reaction(self, reaction: Dict[str, Any]):
        """Display character reaction suggestion."""
        if "error" in reaction:
            print(f"\\n❌ {reaction['error']}")
            return

        print(f"\\n🎭 CHARACTER REACTION: {reaction['character']}")
        print("=" * 50)
        print(f"Class-based reaction: {reaction['class_reaction']}")
        print(f"Personality modifier: {reaction['personality_modifier']}")
        print(f"Suggested approach: {reaction['suggested_approach']}")
        print(f"Dialogue suggestion: {reaction['dialogue_suggestion']}")

        if reaction["relevant_motivations"]:
            print("\\nRelevant motivations:")
            for motivation in reaction["relevant_motivations"]:
                print(f"  • {motivation}")

        if reaction["consistency_notes"]:
            print("\\nConsistency notes:")
            for note in reaction["consistency_notes"]:
                print(f"  • {note}")

        input("\\nPress Enter to continue...")

    def analyze_story(self):
        """Analyze a story file."""
        story_files = self.story_manager.get_story_files()

        if not story_files:
            print("\\n❌ No story files found.")
            return

        print("\\n🔍 ANALYZE STORY FILE")
        print("-" * 30)
        for i, filename in enumerate(story_files, 1):
            print(f"{i}. {filename}")

        try:
            choice = int(input("Enter file number: ")) - 1
            if 0 <= choice < len(story_files):
                filename = story_files[choice]
                filepath = os.path.join(self.story_manager.stories_path, filename)

                print(f"\\n🔄 Analyzing {filename}...")
                analysis = self.story_manager.analyze_story_file(filepath)

                if "error" in analysis:
                    print(f"❌ {analysis['error']}")
                    return

                self.display_story_analysis(analysis)

                # Ask if they want to update the file
                update = (
                    input("\\nUpdate story file with analysis? (y/n): ").strip().lower()
                )
                if update == "y":
                    self.story_manager.update_story_with_analysis(filepath, analysis)
            else:
                print("Invalid file number.")
        except ValueError:
            print("Invalid input.")

    def display_story_analysis(self, analysis: Dict[str, Any]):
        """Display story analysis results."""
        print(f"\\n📊 STORY ANALYSIS: {analysis['story_file']}")
        print("=" * 50)

        # Overall consistency
        overall = analysis.get("overall_consistency", {})
        print(f"Overall Consistency: {overall.get('rating', 'Unknown')}")
        print(f"Score: {overall.get('score', 0)}/1.0")
        print(f"Summary: {overall.get('summary', 'No analysis')}")

        # Character analyses
        if analysis.get("consultant_analyses"):
            print("\\n👥 CHARACTER ANALYSES:")
            for character, char_analysis in analysis["consultant_analyses"].items():
                print(f"\\n• {character}: {char_analysis['overall_rating']}")
                print(f"  Score: {char_analysis['consistency_score']}/1.0")

                if char_analysis.get("positive_notes"):
                    print(f"  ✅ Positives: {len(char_analysis['positive_notes'])}")

                if char_analysis.get("issues"):
                    print(f"  ⚠️ Issues: {len(char_analysis['issues'])}")
                    for issue in char_analysis["issues"][:2]:  # Show first 2
                        print(f"    - {issue}")

        # DC suggestions
        if analysis.get("dc_suggestions"):
            print("\\n🎲 DC SUGGESTIONS:")
            for request, suggestions in analysis["dc_suggestions"].items():
                print(f"\\n• {request}")
                for character, suggestion in suggestions.items():
                    print(
                        f"  {character}: DC {suggestion['suggested_dc']}"
                        f" ({suggestion['reasoning']})"
                    )

        input("\\nPress Enter to continue...")

    def convert_combat(self):
        """Convert combat description to narrative."""
        print("\\n⚔️ CONVERT COMBAT TO NARRATIVE")
        print("-" * 50)
        print("Describe what happened in combat tactically. Example:")
        print("  Theron charges forward and strikes the goblin with his longsword.")
        print("  Mira sneaks behind an enemy and backstabs with her dagger.")
        print("  Garrick swings his warhammer, crushing the goblin's shield.")
        print()
        print("Enter your combat description (end with '###' on a new line):")

        lines = []
        while True:
            line = input()
            if line.strip() == "###":
                break
            lines.append(line)

        combat_prompt = "\\n".join(lines).strip()

        if not combat_prompt:
            print("No combat description provided.")
            return

        # Ask for style
        print("\\n🎨 Choose narrative style:")
        print("1. Cinematic (epic, movie-like)")
        print("2. Gritty (realistic, visceral)")
        print("3. Heroic (valorous, inspirational)")
        print("4. Tactical (clear, precise)")

        style_choice = input(
            "Enter choice (1-4, or press Enter for Cinematic): "
        ).strip()
        style_map = {
            "1": "cinematic",
            "2": "gritty",
            "3": "heroic",
            "4": "tactical",
            "": "cinematic",
        }
        style = style_map.get(style_choice, "cinematic")

        # Ask which story to append to
        print("\\n📖 Which story should this combat be added to?")
        story_series = self.story_manager.get_story_series()

        target_story_path = None
        story_context = ""

        if story_series:
            print("\\nStory Series:")
            for i, series in enumerate(story_series, 1):
                print(f"{i}. {series}")

            series_choice = input(
                "\\nSelect series number (or press Enter to skip): "
            ).strip()
            if series_choice.isdigit():
                idx = int(series_choice) - 1
                if 0 <= idx < len(story_series):
                    series_name = story_series[idx]
                    series_path = os.path.join(self.workspace_path, series_name)
                    story_files = self.story_manager.get_story_files_in_series(
                        series_name
                    )

                    if story_files:
                        print(f"\\nStories in {series_name}:")
                        for i, story_file in enumerate(story_files, 1):
                            print(f"{i}. {story_file}")

                        story_choice = input("\\nSelect story number: ").strip()
                        if story_choice.isdigit():
                            idx2 = int(story_choice) - 1
                            if 0 <= idx2 < len(story_files):
                                target_story_path = os.path.join(
                                    series_path, story_files[idx2]
                                )

        # Read story context if file selected
        if target_story_path and os.path.exists(target_story_path):
            with open(target_story_path, "r", encoding="utf-8") as f:
                story_context = f.read()

        print(f"\\n🔄 Converting to {style} narrative...")

        # Initialize AI client if needed
        if not hasattr(self, "ai_client") or self.ai_client is None:
            if AI_CLIENT_AVAILABLE:
                try:
                    self.ai_client = AIClient()
                except (AttributeError, ValueError) as e:
                    print(f"⚠️  Could not initialize AI client: {e}")
                    print("   Using fallback mode...")
                    self.ai_client = None
            else:
                print("⚠️  AI client not available")
                print("   Using fallback mode...")
                self.ai_client = None

        # Recreate combat narrator with AI client
        self.combat_narrator = CombatNarrator(
            self.story_manager.consultants, self.ai_client
        )

        # Generate combat title automatically
        print("🏷️  Generating combat title...")
        combat_title = self.combat_narrator.generate_combat_title(
            combat_prompt, story_context
        )
        print(f"   Title: {combat_title}")

        # Generate narrative
        narrative = self.combat_narrator.narrate_combat_from_prompt(
            combat_prompt=combat_prompt, story_context=story_context, style=style
        )

        print("\\n📝 COMBAT NARRATIVE:")
        print("=" * 70)
        print(narrative)
        print("=" * 70)

        # Append to story file if selected
        if target_story_path:
            append = (
                input(f"\\nAppend to {os.path.basename(target_story_path)}? (y/n): ")
                .strip()
                .lower()
            )
            if append == "y":
                with open(target_story_path, "a", encoding="utf-8") as f:
                    f.write(f"\\n\\n### {combat_title}\\n\\n")
                    f.write(narrative)
                print(f"✅ Appended to: {target_story_path}")
        else:
            # Save to separate file if no story selected
            save = input("\\nSave to separate file? (y/n): ").strip().lower()
            if save == "y":
                filename = input("Enter filename (without extension): ").strip()
                if filename:
                    filepath = os.path.join(self.workspace_path, f"{filename}.md")
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(f"# {combat_title}\\n\\n")
                        f.write(narrative)
                    print(f"✅ Saved to: {filepath}")

    def get_dc_suggestions(self):
        """Get DC suggestions for an action."""
        characters = self.story_manager.get_character_list()
        if not characters:
            print("\\n❌ No characters found.")
            return

        print("\\n🎲 DC SUGGESTIONS")
        print("-" * 30)

        action = input("Describe the action: ").strip()
        if not action:
            print("Action description cannot be empty.")
            return

        print("\\nSelect character attempting the action:")
        for i, name in enumerate(characters, 1):
            print(f"{i}. {name}")
        print(f"{len(characters) + 1}. General (no specific character)")

        try:
            choice = int(input("Enter character number: ")) - 1

            if choice == len(characters):
                # General suggestion
                first_consultant = next(iter(self.story_manager.consultants.values()))
                suggestion = first_consultant.suggest_dc_for_action(action)
                character_name = "General"
            elif 0 <= choice < len(characters):
                character_name = characters[choice]
                consultant = self.story_manager.consultants[character_name]
                suggestion = consultant.suggest_dc_for_action(action)
            else:
                print("Invalid choice.")
                return

            self.display_dc_suggestion(character_name, action, suggestion)

        except ValueError:
            print("Invalid input.")

    def display_dc_suggestion(
        self, character: str, action: str, suggestion: Dict[str, Any]
    ):
        """Display DC suggestion."""
        print(f"\\n🎯 DC SUGGESTION FOR: {character}")
        print("=" * 50)
        print(f"Action: {action}")
        print(f"Action Type: {suggestion['action_type']}")
        print(f"Suggested DC: {suggestion['suggested_dc']}")
        print(f"Reasoning: {suggestion['reasoning']}")

        if suggestion.get("alternative_approaches"):
            print("\\nAlternative Approaches:")
            for approach in suggestion["alternative_approaches"]:
                print(f"  • {approach}")

        if suggestion.get("character_advantage"):
            print("\\nCharacter Advantages:")
            for advantage in suggestion["character_advantage"]:
                print(f"  • {advantage}")

        input("\\nPress Enter to continue...")

    def get_dm_narrative_suggestions(self):
        """Get DM narrative suggestions based on user prompt."""
        print("\\n🎭 DM NARRATIVE SUGGESTIONS")
        print("-" * 40)

        # Get user prompt
        prompt = input("Describe the situation you need narrative help with: ").strip()
        if not prompt:
            print("Prompt cannot be empty.")
            return

        # Get available characters and NPCs
        characters = self.dm_consultant.get_available_characters()
        npcs = self.dm_consultant.get_available_npcs()

        # Let user select which characters are present
        characters_present = []
        if characters:
            print(f"\\nAvailable characters: {', '.join(characters)}")
            char_input = input(
                "Enter character names present (comma-separated, or 'all', or leave blank): "
            ).strip()
            if char_input.lower() == "all":
                characters_present = characters
            elif char_input:
                characters_present = [
                    name.strip()
                    for name in char_input.split(",")
                    if name.strip() in characters
                ]

        # Let user select which NPCs are present
        npcs_present = []
        if npcs:
            print(f"\\nAvailable NPCs: {', '.join(npcs)}")
            npc_input = input(
                "Enter NPC names present (comma-separated, or leave blank): "
            ).strip()
            if npc_input:
                npcs_present = [
                    name.strip()
                    for name in npc_input.split(",")
                    if name.strip() in npcs
                ]

        # Get narrative suggestions
        suggestions = self.dm_consultant.suggest_narrative(
            prompt, characters_present, npcs_present
        )
        self.display_dm_suggestions(suggestions)

    def display_dm_suggestions(self, suggestions: Dict[str, Any]):
        """Display DM narrative suggestions."""
        print("\\n🎭 NARRATIVE SUGGESTIONS")
        print("=" * 50)
        print(f"Situation: {suggestions['user_prompt']}")

        # Character insights
        if suggestions["character_insights"]:
            print("\\n👥 CHARACTER INSIGHTS:")
            for char_name, insight in suggestions["character_insights"].items():
                print(f"\\n  {char_name}:")
                print(f"    Likely reaction: {insight['likely_reaction']}")
                print(f"    Reasoning: {insight['reasoning']}")
                if insight["class_expertise"]:
                    print(f"    Class expertise: {insight['class_expertise']}")

        # NPC insights
        if suggestions["npc_insights"]:
            print("\\n🗣️ NPC INSIGHTS:")
            for npc_name, insight in suggestions["npc_insights"].items():
                print(f"\\n  {npc_name}:")
                print(f"    Personality: {insight['personality']}")
                print(f"    Role: {insight['role']}")
                print(f"    Likely behavior: {insight['likely_behavior']}")
                if insight["relationships"]:
                    print(f"    Relationships: {insight['relationships']}")

        # Narrative suggestions
        print("\\n📚 NARRATIVE SUGGESTIONS:")
        for i, suggestion in enumerate(suggestions["narrative_suggestions"], 1):
            print(f"  {i}. {suggestion}")

        # Consistency notes
        if suggestions["consistency_notes"]:
            print("\\n⚠️ CONSISTENCY REMINDERS:")
            for note in suggestions["consistency_notes"]:
                print(f"  • {note}")

        input("\\nPress Enter to continue...")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="D&D Character Consultant System")
    parser.add_argument("--workspace", help="Workspace directory path", default=None)
    parser.add_argument(
        "--command",
        help="Command to run",
        choices=["interactive", "analyze", "create-party"],
    )
    parser.add_argument("--story", help="Story file to analyze")

    args = parser.parse_args()

    workspace = args.workspace or os.getcwd()

    try:
        cli = DDConsultantCLI(workspace)

        if args.command == "create-party":
            # Quick command to create default party
            default_profiles = cli.story_manager.create_default_party()
            for profile in default_profiles:
                cli.story_manager.save_character_profile(profile)
            print(f"✅ Created default 12-character party in {workspace}")

        elif args.command == "analyze" and args.story:
            # Quick command to analyze a story
            filepath = os.path.join(workspace, args.story)
            analysis = cli.story_manager.analyze_story_file(filepath)
            cli.display_story_analysis(analysis)

        else:
            # Default to interactive mode
            cli.run_interactive()

    except KeyboardInterrupt:
        print("\\n\\nGoodbye! 🎲")
    except (OSError, ValueError, KeyError, AttributeError) as e:
        print(f"\\n❌ Error: {e}")
        print("Please check your setup and try again.")


if __name__ == "__main__":
    main()
