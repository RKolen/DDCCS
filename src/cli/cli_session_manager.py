"""
Session Results Management CLI Module

Handles interactive recording of session results, rolls, and character actions.
"""

from datetime import datetime
from typing import Dict, Any, Optional

from src.stories.session_results_manager import StorySession, create_session_results_file
from src.cli.base_story_interaction_manager import BaseStoryInteractionManager
from src.cli.dnd_cli_helpers import collect_generic_input


class SessionCLIManager(BaseStoryInteractionManager):
    """Manages session results recording through CLI."""

    def record_session_results(self) -> None:
        """Interactively record session results for a story."""
        result = self.initialize_recording_workflow("RECORD SESSION RESULTS")
        if result is None:
            return
        series_name, _story_filename, story_name = result

        # Get session date
        session_date = input("\nSession date (YYYY-MM-DD) [today]: ").strip()
        if not session_date:
            session_date = datetime.now().strftime("%Y-%m-%d")

        # Create session
        session = StorySession(story_name, session_date)

        # Collect rolls
        print("\nRecording rolls (type 'done' to finish):")
        while True:
            roll_data = self._collect_roll_data()
            if roll_data is None:
                break
            session.add_roll_result(roll_data)
            print("[OK] Roll recorded")

        # Save session results
        series_path = self.get_series_campaign_path(series_name)
        try:
            filepath = create_session_results_file(series_path, session)
            print(f"\n[SUCCESS] Session results saved: {filepath}")
        except OSError as error:
            print(f"[ERROR] Error saving session results: {error}")

    def validate_roll_data(self, roll_data: Dict[str, Any]) -> bool:
        """Public wrapper for roll validation (for testing).

        Args:
            roll_data: Dictionary with roll information

        Returns:
            True if valid, False otherwise
        """
        return self._validate_roll_data(roll_data)

    def _validate_roll_data(self, roll_data: Dict[str, Any]) -> bool:
        """Validate roll data fields.

        Args:
            roll_data: Dictionary with roll information

        Returns:
            True if valid, False otherwise
        """
        if roll_data['roll_type'] not in ('attack', 'ability', 'save'):
            print("Roll type must be: attack, ability, or save")
            return False
        if roll_data['outcome'] not in ('success', 'failure', 'mixed'):
            print("Outcome must be: success, failure, or mixed")
            return False
        return True

    def _collect_roll_data(self) -> Optional[Dict[str, Any]]:
        """Collect a single roll result from user input.

        Returns:
            Dictionary with roll data, or None if user wants to stop
        """
        fields: list = [
            ("character", "\nCharacter name (or 'done'): ", None),
            ("action", "Action taken: ", None),
            ("roll_type", "Roll type (attack/ability/save): ", None),
        ]

        basic_data = collect_generic_input(fields)
        if basic_data is None:
            return None

        # Collect numeric values
        try:
            roll_value = int(input("Roll result: "))
            dc = int(input("DC: "))
        except ValueError:
            print("Roll values must be numbers.")
            return None

        outcome = input("Outcome (success/failure/mixed): ").strip().lower()

        roll_data = {
            "character": basic_data["character"],
            "action": basic_data["action"],
            "roll_type": basic_data["roll_type"].lower(),
            "roll_value": roll_value,
            "dc": dc,
            "outcome": outcome,
        }

        if not self._validate_roll_data(roll_data):
            return None

        return roll_data
