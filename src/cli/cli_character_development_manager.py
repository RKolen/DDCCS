"""
Character Development Management CLI Module

Handles interactive recording of character development, actions, and
consistency analysis for D&D sessions.
"""

from typing import Optional, Dict, Any, List

from src.characters.character_consistency import create_character_development_file
from src.cli.base_story_interaction_manager import BaseStoryInteractionManager
from src.cli.dnd_cli_helpers import collect_generic_input


class CharacterDevelopmentCLIManager(BaseStoryInteractionManager):
    """Manages character development recording through CLI."""

    def _validate_action_data(self, action_data: Dict[str, Any]) -> bool:
        """Validate character action data.

        Args:
            action_data: Dictionary with action information

        Returns:
            True if valid, False otherwise
        """
        if not action_data.get("character"):
            print("Character name cannot be empty.")
            return False

        if not action_data.get("action"):
            print("Action cannot be empty.")
            return False

        if not action_data.get("reasoning"):
            print("Reasoning cannot be empty.")
            return False

        return True

    def validate_action_data(self, action_data: Dict[str, Any]) -> bool:
        """Public wrapper for action validation (for testing).

        Args:
            action_data: Dictionary with action information

        Returns:
            True if valid, False otherwise
        """
        return self._validate_action_data(action_data)

    def _collect_character_action(self) -> Optional[Dict[str, Any]]:
        """Collect a single character action from user input.

        Returns:
            Dictionary with action data, or None if user wants to stop
        """
        fields: list = [
            ("character", "\nCharacter name (or 'done'): ", None),
            ("action", "Action taken: ", None),
            ("reasoning", "Character reasoning (why they did this): ", None),
        ]

        required_data = collect_generic_input(fields)
        if required_data is None:
            return None

        consistency = input(
            "Consistency notes (optional, press Enter to skip): "
        ).strip()
        if not consistency:
            consistency = "To be analyzed"

        notes = input("Development notes (optional, press Enter to skip): ").strip()
        if not notes:
            notes = "Character action recorded"

        action_data = {
            "character": required_data["character"],
            "action": required_data["action"],
            "reasoning": required_data["reasoning"],
            "consistency": consistency,
            "notes": notes,
        }

        if not self._validate_action_data(action_data):
            return None

        return action_data

    def record_character_development(self) -> None:
        """Interactively record character development for a story."""
        result = self.initialize_recording_workflow("RECORD CHARACTER DEVELOPMENT")
        if result is None:
            return
        series_name, _story_filename, story_name = result

        # Collect character actions
        print("\nRecording character actions (type 'done' to finish):")
        character_actions: List[Dict[str, Any]] = []
        while True:
            action_data = self._collect_character_action()
            if action_data is None:
                break
            character_actions.append(action_data)
            print("[OK] Action recorded")

        if not character_actions:
            print("No character actions recorded. Cancelling.")
            return

        # Save character development file
        series_path = self.get_series_campaign_path(series_name)
        try:
            filepath = create_character_development_file(
                series_path, story_name, character_actions
            )
            print(f"\n[SUCCESS] Character development saved: {filepath}")
        except OSError as error:
            print(f"[ERROR] Error saving character development: {error}")
