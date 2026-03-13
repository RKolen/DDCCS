"""
Story Amender CLI Handler

Handles the interactive character action amendment workflow.
"""

import os
from typing import List, Dict, Any, Optional
from src.utils.file_io import read_text_file
from src.utils.errors import display_error, DnDError
from src.utils.cli_utils import require_story_with_content, require_party
from src.stories import story_amender


class StoryAmenderCLIHandler:
    """Handles story amendment CLI interactions."""

    def __init__(self, workspace_path: str, load_profiles_fn):
        self.workspace_path = workspace_path
        self.load_profiles_fn = load_profiles_fn

    def _load_amendment_context(
        self, selected: list, series_name: str
    ) -> Optional[tuple]:
        """Load story content and party info for amendment.

        Returns:
            Tuple of (story_path, content, party, target_char, profiles) or None.
        """
        story_path = os.path.join(selected[2], selected[0])
        content = read_text_file(story_path)
        if content is None or not require_story_with_content(content, selected[0]):
            return None
        party = require_party(self.workspace_path, series_name)
        if not party:
            return None
        target_char = self._select_character(party)
        if not target_char:
            return None
        profiles = self.load_profiles_fn(party, selected[2])
        return story_path, content, party, target_char, profiles

    def _run_amendment_analysis(self, ctx: tuple) -> Optional[list]:
        """Run the amendment analysis returning suggestions or None if nothing found."""
        _, content, _party, target_char, profiles = ctx
        print(f"\n[INFO] Identifying actions for {target_char}...")
        actions = story_amender.identify_character_actions(content, target_char)
        if not actions:
            print(f"[INFO] No actions found for {target_char} in this story.")
            return None
        print("[INFO] Analyzing character fits and suggesting amendments...")
        plot_map = {
            name: profile.get("major_plot_actions", [])
            for name, profile in profiles.items()
        }
        analyzed = story_amender.analyze_amendments(actions, target_char, profiles, plot_map)
        suggestions = [a for a in analyzed if "suggestion" in a]
        if not suggestions:
            print("\n[INFO] No character reassignment suggestions found.")
            return None
        return suggestions

    def handle_amendment(self, series_name: str, stories: List[str], select_story_fn):
        """Interactive story character action amendment."""
        try:
            selected = select_story_fn(stories, series_name)
            if not selected:
                return

            ctx = self._load_amendment_context(selected, series_name)
            if ctx is None:
                return

            story_path = ctx[0]
            suggestions = self._run_amendment_analysis(ctx)
            if suggestions is not None:
                self._process_suggestions(suggestions, story_path)

        except (ValueError, OSError) as e:
            error = DnDError(
                message=f"Amendment process failed: {e}",
                user_guidance="Check the story file and try again."
            )
            display_error(error)

    def validate_setup(self) -> bool:
        """Check if the handler is properly configured."""
        return bool(self.workspace_path and self.load_profiles_fn)

    def _select_character(self, party_members: List[str]) -> Optional[str]:
        """Select character to analyze for action fit."""
        print("\nSelect character to analyze for action fit:")
        for i, name in enumerate(party_members, 1):
            print(f"{i}. {name}")

        char_choice = input("\nEnter choice (0 to cancel): ").strip()
        if char_choice == "0" or not char_choice.isdigit():
            return None

        char_idx = int(char_choice) - 1
        if not 0 <= char_idx < len(party_members):
            print("Invalid choice.")
            return None

        return party_members[char_idx]

    def _process_suggestions(self, suggestions: List[Dict[str, Any]], story_path: str):
        """Display suggestions and handle user selection for amendment."""
        print(f"\nFound {len(suggestions)} potential character reassignments:")
        for i, action in enumerate(suggestions, 1):
            sugg = action["suggestion"]
            print(f"\n{i}. Action: \"{action['text'][:100]}...\"")
            print(
                f"   Current: {sugg['current_character']} (Score: {sugg['current_fit_score']})"
            )
            print(
                f"   Suggested: {sugg['suggested_character']} "
                f"(Score: {sugg['suggested_fit_score']})"
            )
            print(f"   Difference: +{sugg['score_difference']}")

        sugg_choice = input("\nSelect suggestion to apply (0 to cancel): ").strip()
        if sugg_choice == "0" or not sugg_choice.isdigit():
            return

        sugg_idx = int(sugg_choice) - 1
        if not 0 <= sugg_idx < len(suggestions):
            print("Invalid choice.")
            return

        selected_action = suggestions[sugg_idx]
        sugg = selected_action["suggestion"]

        # Generate amended text
        new_line = story_amender.generate_amended_text(
            selected_action["original_line"],
            sugg["current_character"],
            sugg["suggested_character"],
        )

        print("\nPROPOSED CHANGE:")
        print(f"OLD: {selected_action['original_line']}")
        print(f"NEW: {new_line}")

        confirm = input("\nApply this change? (y/n): ").strip().lower()
        if confirm == "y":
            success = story_amender.apply_amendment_to_file(
                story_path, selected_action["line_index"], new_line
            )
            if success:
                print("[SUCCESS] Story file updated.")
            else:
                error = DnDError(
                    message="Failed to update story file",
                    user_guidance="Check file permissions."
                )
                display_error(error)
        else:
            print("[INFO] Suggestion skipped.")
