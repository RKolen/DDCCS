"""
Character Management CLI Module

Handles all character-related menu interactions and operations.
"""

from src.characters.consultants.character_profile import CharacterProfile
from src.cli.dnd_cli_helpers import edit_character_profile_interactive
from src.utils.cli_utils import select_character_from_list


class CharacterCLIManager:
    """Manages character-related CLI operations."""

    def __init__(self, story_manager, combat_narrator):
        """
        Initialize character CLI manager.

        Args:
            story_manager: StoryManager instance
            combat_narrator: CombatNarrator instance
        """
        self.story_manager = story_manager
        self.combat_narrator = combat_narrator

    def manage_characters(self):
        """Character management submenu."""
        while True:
            print("\n CHARACTER MANAGEMENT")
            print("-" * 30)
            print("1. List Characters")
            print("2. Edit Character Profile")
            print("3. View Character Details")
            print("0. Back to Main Menu")

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self.list_characters()
            elif choice == "2":
                self.edit_character()
            elif choice == "3":
                self.view_character_details()
            elif choice == "0":
                break
            else:
                print("Invalid choice. Please try again.")

    def list_characters(self):
        """List all characters."""
        characters = self.story_manager.get_character_list()
        if not characters:
            print("\n[ERROR] No characters found. Create the default party first.")
            return

        print(f"\n CHARACTERS ({len(characters)})")
        print("-" * 40)
        for i, name in enumerate(characters, 1):
            profile = self.story_manager.get_character_profile(name)
            if profile:
                print(
                    f"{i}. {name} ({profile.character_class.value} "
                    f"Level {profile.level})"
                )
                if profile.personality_summary:
                    print(f"   {profile.personality_summary}")
        print()

    def edit_character(self):
        """Edit a character profile."""
        characters = self.story_manager.get_character_list()
        if not characters:
            print("\n[ERROR] No characters found. Create the default party first.")
            return

        print("\n EDIT CHARACTER")
        print("-" * 20)

        result = select_character_from_list(characters)
        if result:
            _, character_name = result
            profile = self.story_manager.get_character_profile(character_name)
            if profile:
                self._edit_character_profile(profile)

    def _edit_character_profile(self, profile: CharacterProfile):
        """Edit a specific character profile."""
        character_name = profile.name
        edited_profile, should_save = edit_character_profile_interactive(profile)
        if should_save:
            self.story_manager.save_character_profile(edited_profile)
        else:
            # Clear the cache and reload from disk to discard in-memory changes
            self.story_manager.reload_character_from_disk(character_name)
            print("Profile reloaded from disk - changes discarded.")

    def view_character_details(self):
        """View detailed character information."""
        characters = self.story_manager.get_character_list()
        if not characters:
            print("\n[ERROR] No characters found.")
            return

        print("\n VIEW CHARACTER DETAILS")
        print("-" * 30)

        result = select_character_from_list(characters)
        if result:
            _, character_name = result
            profile = self.story_manager.get_character_profile(character_name)
            if profile:
                self._display_character_details(profile)

    def _display_character_details(self, profile: CharacterProfile):
        """Display detailed character information."""
        print(f"\n[MENU] CHARACTER DETAILS: {profile.name}")
        print("=" * 50)
        print(f"Class: {profile.character_class.value}")
        print(f"Level: {profile.level}")
        print(f"\nPersonality: {profile.personality_summary}")
        print(f"\nBackground Story:\n{profile.background_story}")

        if profile.motivations:
            print("\nMotivations:")
            for motivation in profile.motivations:
                print(f"  • {motivation}")

        if profile.goals:
            print("\nGoals:")
            for goal in profile.goals:
                print(f"  • {goal}")

        if profile.fears_weaknesses:
            print("\nFears/Weaknesses:")
            for fear in profile.fears_weaknesses:
                print(f"  • {fear}")

        # Behavior: speech patterns and decision making style (nested dataclass)
        if getattr(profile, "behavior", None) and profile.behavior.speech_patterns:
            print("\nSpeech Patterns:")
            for pattern in profile.behavior.speech_patterns:
                print(f"  • {pattern}")

        if getattr(profile, "behavior", None) and profile.behavior.decision_making_style:
            print(f"\nDecision Making Style: {profile.behavior.decision_making_style}")

        input("\nPress Enter to continue...")
