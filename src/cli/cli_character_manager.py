"""Character Management CLI Module

Handles all character-related menu interactions and operations.
"""

import json
from pathlib import Path
from typing import Optional, Union
from src.characters.consultants.character_profile import CharacterProfile
from src.cli.dnd_cli_helpers import edit_character_profile_interactive
from src.cli.cli_consultations import ConsultationsCLI
from src.utils.cli_utils import select_character_from_list, get_multiline_text
from src.utils.ascii_art import (
    display_character_portrait,
    create_character_portrait,
)
from src.utils.string_utils import sanitize_filename


class CharacterCLIManager:
    """Manages character-related CLI operations."""

    def __init__(self, story_manager, combat_narrator, dm_consultant=None):
        """
        Initialize character CLI manager.

        Args:
            story_manager: StoryManager instance
            combat_narrator: CombatNarrator instance
            dm_consultant: DMConsultant instance for consultations
        """
        self.story_manager = story_manager
        self.combat_narrator = combat_narrator
        self.dm_consultant = dm_consultant
        self.consultations = None
        if story_manager:
            self.consultations = ConsultationsCLI(story_manager, dm_consultant)

    def manage_characters(self):
        """Character management submenu."""
        while True:
            print("\n CHARACTER MANAGEMENT")
            print("-" * 30)
            print("1. List Characters")
            print("2. Edit Character Profile")
            print("3. View Character Details")
            print("4. Get Character Consultation")
            print("5. Customize ASCII Art")
            print("0. Back to Main Menu")

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self.list_characters()
            elif choice == "2":
                self.edit_character()
            elif choice == "3":
                self.view_character_details()
            elif choice == "4":
                self._get_character_consultation()
            elif choice == "5":
                self._customize_ascii_art()
            elif choice == "0":
                break
            else:
                print("Invalid choice. Please try again.")

    def list_characters(self):
        """List all characters."""
        # Ensure characters are loaded before listing (lazy loading)
        if not self.story_manager.is_characters_loaded():
            print("\n[INFO] Loading characters... This may take a while.")
        self.story_manager.ensure_characters_loaded()
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
        # Ensure characters are loaded before editing (lazy loading)
        self.story_manager.ensure_characters_loaded()
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
        # Ensure characters are loaded before viewing (lazy loading)
        self.story_manager.ensure_characters_loaded()
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
        # Display ASCII art portrait if available
        custom_art = getattr(profile, "ascii_art", None)
        backstory = getattr(profile, "background_story", None)

        # Generate from backstory by default if no custom art
        generate_from_backstory = custom_art is None

        display_character_portrait(
            profile.name,
            profile.character_class.value,
            profile.level,
            custom_art=custom_art,
            backstory=backstory,
            generate_from_backstory=generate_from_backstory,
            style="cyan",
        )

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

        if (
            getattr(profile, "behavior", None)
            and profile.behavior.decision_making_style
        ):
            print(f"\nDecision Making Style: {profile.behavior.decision_making_style}")

        # Offer ASCII art customization
        print("\n" + "-" * 50)
        choice = (
            input("\nCustomize ASCII art for this character? (y/n): ").strip().lower()
        )
        if choice == "y":
            self._set_character_ascii_art(profile.name)

    def _get_character_consultation(self):
        """Get character consultation from the consultations CLI."""
        # Ensure characters are loaded before consultation (lazy loading)
        self.story_manager.ensure_characters_loaded()
        if not self.consultations:
            print("[ERROR] Consultations not available.")
            return
        self.consultations.get_character_consultation()

    def _customize_ascii_art(self):
        """Customize ASCII art for a character."""
        # Ensure characters are loaded
        self.story_manager.ensure_characters_loaded()
        characters = self.story_manager.get_character_list()
        if not characters:
            print("\n[ERROR] No characters found.")
            return

        print("\n CUSTOMIZE ASCII ART")
        print("-" * 40)
        for i, name in enumerate(characters, 1):
            print(f"{i}. {name}")

        choice = input("\nSelect character (0 to cancel): ").strip()
        if choice == "0":
            return

        try:
            index = int(choice) - 1
            if 0 <= index < len(characters):
                character_name = characters[index]
                self._set_character_ascii_art(character_name)
            else:
                print("[ERROR] Invalid selection.")
        except ValueError:
            print("[ERROR] Invalid input.")

    def _set_character_ascii_art(self, character_name: str):
        """Set custom ASCII art for a character."""
        print(f"\n CUSTOMIZE ASCII ART: {character_name}")
        print("-" * 50)
        print("\nOptions:")
        print("1. Generate from backstory using AI (recommended)")
        print("2. Enter custom ASCII art manually")
        print("3. Use default class-based art")

        choice = input("\nSelect option (1-3): ").strip()

        custom_art = self._get_ascii_art_from_choice(choice, character_name)
        if custom_art is False:  # False means cancelled/error
            return

        # At this point custom_art is str or None (False case handled above)
        assert isinstance(custom_art, (str, type(None)))
        self._save_ascii_art_to_file(character_name, custom_art)

    def _get_ascii_art_from_choice(
        self, choice: str, character_name: str
    ) -> Union[str, None, bool]:
        """Get ASCII art based on user choice.

        Args:
            choice: User's menu selection (1-3)
            character_name: Name of character

        Returns:
            ASCII art string, None for default, or False for cancelled/error
        """
        if choice == "1":
            return self._generate_art_from_backstory(character_name)
        if choice == "2":
            return self._get_manual_ascii_art()
        if choice == "3":
            print("\n[INFO] Using default class-based ASCII art.")
            return None
        print("[ERROR] Invalid choice.")
        return False

    def _generate_art_from_backstory(self, character_name: str) -> Union[str, bool]:
        """Generate ASCII art from character backstory.

        Args:
            character_name: Name of character

        Returns:
            Generated ASCII art or False if cancelled/error
        """
        profile = self.story_manager.get_character_profile(character_name)
        if not profile or not hasattr(profile, "background_story"):
            print("[ERROR] No backstory available for this character.")
            return False

        print("\n[INFO] Generating ASCII art from backstory...")
        art = create_character_portrait(
            profile.name,
            profile.character_class.value,
            profile.level,
            custom_art=None,
            backstory=profile.background_story,
            generate_from_backstory=True,
        )

        print("\nGenerated ASCII Art:")
        print("-" * 50)
        print(art)
        print("-" * 50)

        confirm = input("\nSave this ASCII art? (y/n): ").strip().lower()
        if confirm == "y":
            return art
        print("[INFO] ASCII art not saved.")
        return False

    def _get_manual_ascii_art(self) -> Union[str, bool]:
        """Get manually entered ASCII art from user.

        Returns:
            ASCII art string or False if cancelled
        """
        art = get_multiline_text("\nEnter custom ASCII art (end with an empty line):")
        if art:
            return art
        print("\n[INFO] No ASCII art entered.")
        return False

    def _save_ascii_art_to_file(self, character_name: str, custom_art: Optional[str]):
        """Save ASCII art to character JSON file.

        Args:
            character_name: Name of character
            custom_art: ASCII art to save (None for default)
        """
        char_file = (
            Path(self.story_manager.base_path)
            / "game_data"
            / "characters"
            / f"{sanitize_filename(character_name)}.json"
        )

        if not char_file.exists():
            print(f"[ERROR] Character file not found: {char_file}")
            return

        try:
            with open(char_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if custom_art:
                data["ascii_art"] = custom_art
            else:
                data.pop("ascii_art", None)

            with open(char_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"\n[SUCCESS] ASCII art updated for {character_name}")

            # Preview the art
            profile = self.story_manager.get_character_profile(character_name)
            if profile:
                custom_art = getattr(profile, "ascii_art", None)
                display_character_portrait(
                    profile.name,
                    profile.character_class.value,
                    profile.level,
                    custom_art=custom_art,
                    style="cyan",
                )
        except (OSError, json.JSONDecodeError) as e:
            print(f"[ERROR] Failed to update character file: {e}")
