"""
Story Amender CLI Handler

Handles the interactive character action amendment workflow.
"""

import os
from typing import List, Dict, Any, Optional
from src.utils.file_io import read_text_file
from src.stories import story_amender
from src.cli.party_config_manager import load_current_party


class StoryAmenderCLIHandler:
    """Handles story amendment CLI interactions."""

    def __init__(self, workspace_path: str, load_profiles_fn):
        self.workspace_path = workspace_path
        self.load_profiles_fn = load_profiles_fn

    def handle_amendment(self, series_name: str, stories: List[str], select_story_fn):
        """Interactive story character action amendment."""
        try:
            selected = select_story_fn(stories, series_name)
            if not selected:
                return

            # Load story and party data
            story_path = os.path.join(selected[2], selected[0])
            content = read_text_file(story_path)

            if not content:
                print("[ERROR] Story file is empty.")
                return

            party = load_current_party(
                workspace_path=self.workspace_path, campaign_name=series_name
            )

            if not party:
                print("[ERROR] No party configured. Set up party first.")
                return

            target_char = self._select_character(party)
            if not target_char:
                return

            profiles = self.load_profiles_fn(party, selected[2])

            print(f"\n[INFO] Identifying actions for {target_char}...")
            actions = story_amender.identify_character_actions(content, target_char)

            if not actions:
                print(f"[INFO] No actions found for {target_char} in this story.")
                return

            print("[INFO] Analyzing character fits and suggesting amendments...")
            prev_actions_map = {
                name: profile.get("major_plot_actions", [])
                for name, profile in profiles.items()
            }

            analyzed = story_amender.analyze_amendments(
                actions, target_char, profiles, prev_actions_map
            )

            suggestions = [a for a in analyzed if "suggestion" in a]

            if not suggestions:
                print("\n[INFO] No character reassignment suggestions found.")
                return

            self._process_suggestions(suggestions, story_path)

        except (ValueError, OSError) as e:
            print(f"[ERROR] Amendment process failed: {e}")

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
                print("[ERROR] Failed to update story file.")
        else:
            print("[INFO] Suggestion skipped.")
