"""
Consultations CLI Module

Handles character consultations, DC suggestions, and DM narrative suggestions.
"""

import os
from typing import Dict, Any, Optional
from src.utils.cli_utils import select_character_from_list, get_non_empty_input
from src.utils.path_utils import get_campaign_path
from src.cli.party_config_manager import load_current_party


class ConsultationsCLI:
    """Manages consultation-related CLI operations."""

    def __init__(self, story_manager, dm_consultant):
        """
        Initialize consultations CLI manager.

        Args:
            story_manager: StoryManager instance
            dm_consultant: DMConsultant instance
        """
        self.story_manager = story_manager
        self.dm_consultant = dm_consultant

    def get_character_consultation(self):
        """Get character consultation for a situation."""
        characters = self.story_manager.get_character_list()
        if not characters:
            print("\n[ERROR] No characters found.")
            return

        print("\n CHARACTER CONSULTATION")
        print("-" * 30)
        print("Select a character:")

        result = select_character_from_list(characters)
        if not result:
            return

        _, character_name = result
        situation = get_non_empty_input("\nDescribe the situation: ")

        if situation:
            reaction = self.story_manager.suggest_character_reaction(
                character_name, situation
            )
            self._display_character_reaction(reaction)

    def _display_character_reaction(self, reaction: Dict[str, Any]):
        """Display character reaction suggestion."""
        if "error" in reaction:
            print(f"\n[ERROR] {reaction['error']}")
            return

        print(f"\n CHARACTER REACTION: {reaction['character']}")
        print("=" * 50)
        print(f"Class-based reaction: {reaction['class_reaction']}")
        print(f"Personality modifier: {reaction['personality_modifier']}")
        print(f"Suggested approach: {reaction['suggested_approach']}")
        print(f"Dialogue suggestion: {reaction['dialogue_suggestion']}")

        if reaction["relevant_motivations"]:
            print("\nRelevant motivations:")
            for motivation in reaction["relevant_motivations"]:
                print(f"  • {motivation}")

        if reaction["consistency_notes"]:
            print("\nConsistency notes:")
            for note in reaction["consistency_notes"]:
                print(f"  • {note}")

        input("\nPress Enter to continue...")

    def get_dc_suggestions(self):
        """Get DC suggestions for an action."""
        characters = self.story_manager.get_character_list()
        if not characters:
            print("\n[ERROR] No characters found.")
            return

        print("\n DC SUGGESTIONS")
        print("-" * 30)

        action = get_non_empty_input("Describe the action: ")
        if not action:
            return

        print("\nSelect character attempting the action:")
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

            self._display_dc_suggestion(character_name, action, suggestion)

        except ValueError:
            print("Invalid input.")

    def _display_dc_suggestion(
        self, character: str, action: str, suggestion: Dict[str, Any]
    ):
        """Display DC suggestion."""
        print(f"\n DC SUGGESTION FOR: {character}")
        print("=" * 50)
        print(f"Action: {action}")
        print(f"Action Type: {suggestion['action_type']}")
        print(f"Suggested DC: {suggestion['suggested_dc']}")
        print(f"Reasoning: {suggestion['reasoning']}")

        if suggestion.get("alternative_approaches"):
            print("\nAlternative Approaches:")
            for approach in suggestion["alternative_approaches"]:
                print(f"  • {approach}")

        if suggestion.get("character_advantage"):
            print("\nCharacter Advantages:")
            for advantage in suggestion["character_advantage"]:
                print(f"  • {advantage}")

        input("\nPress Enter to continue...")

    def get_dm_narrative_suggestions(self, series_name: Optional[str] = None):
        """Get DM narrative suggestions based on user prompt."""
        print("\n DM NARRATIVE SUGGESTIONS")
        print("-" * 40)

        # Get user prompt
        prompt = input("Describe the situation you need narrative help with: ").strip()
        if not prompt:
            print("Prompt cannot be empty.")
            return

        # Get characters and NPCs
        characters = self._get_party_for_series(series_name)
        npcs = self.dm_consultant.get_available_npcs()

        # Get selections from user
        characters_present = self._select_characters(characters)
        npcs_present = self._select_npcs(npcs)

        # Get and display narrative suggestions
        suggestions = self.dm_consultant.suggest_narrative(
            prompt, characters_present, npcs_present
        )
        self._display_dm_suggestions(suggestions)

    def _get_party_for_series(self, series_name: Optional[str] = None):
        """Get party members for a series (or overall party if not specified)."""
        characters = []
        if series_name:
            workspace_path = self.story_manager.workspace_path
            series_path = get_campaign_path(series_name, workspace_path)
            party_config_path = os.path.join(series_path, "current_party.json")
            if os.path.isfile(party_config_path):
                characters = load_current_party(party_config_path)

        if not characters:
            characters = self.story_manager.get_current_party()

        return characters

    def _select_characters(self, characters):
        """Prompt user to select party members (numbered list)."""
        characters_present = []
        if characters:
            print("\nParty Members:")
            for i, char in enumerate(characters, 1):
                print(f"{i}. {char}")
            char_input = input(
                "Enter character numbers (comma-separated), 'all', or leave blank: "
            ).strip()
            if char_input.lower() == "all":
                characters_present = characters
            elif char_input:
                try:
                    indices = [int(x.strip()) - 1 for x in char_input.split(",")]
                    characters_present = [
                        characters[i] for i in indices if 0 <= i < len(characters)
                    ]
                except (ValueError, IndexError):
                    pass

        return characters_present

    def _select_npcs(self, npcs):
        """Prompt user to select NPCs (numbered list)."""
        npcs_present = []
        if npcs:
            print("\nAvailable NPCs:")
            for i, npc in enumerate(npcs, 1):
                print(f"{i}. {npc}")
            npc_input = input(
                "Enter NPC numbers (comma-separated), or leave blank: "
            ).strip()
            if npc_input:
                try:
                    indices = [int(x.strip()) - 1 for x in npc_input.split(",")]
                    npcs_present = [npcs[i] for i in indices if 0 <= i < len(npcs)]
                except (ValueError, IndexError):
                    pass

        return npcs_present

    def _display_dm_suggestions(self, suggestions: Dict[str, Any]):
        """Display DM narrative suggestions."""
        print("\n NARRATIVE SUGGESTIONS")
        print("=" * 50)
        print(f"Situation: {suggestions['user_prompt']}")

        # Character insights
        if suggestions["character_insights"]:
            print("\n CHARACTER INSIGHTS:")
            for char_name, insight in suggestions["character_insights"].items():
                print(f"\n  {char_name}:")
                print(f"    Likely reaction: {insight['likely_reaction']}")
                print(f"    Reasoning: {insight['reasoning']}")
                if insight.get("class_expertise"):
                    print(f"    Class expertise: {insight['class_expertise']}")
                if insight.get("dialogue"):
                    print(f"    Suggested dialogue: {insight['dialogue']}")

        # NPC insights
        if suggestions["npc_insights"]:
            print("\n NPC INSIGHTS:")
            for npc_name, insight in suggestions["npc_insights"].items():
                print(f"\n  {npc_name}:")
                print(f"    Personality: {insight['personality']}")
                print(f"    Role: {insight['role']}")
                print(f"    Likely behavior: {insight['likely_behavior']}")
                if insight.get("relationships"):
                    print(f"    Relationships: {insight['relationships']}")

        # Narrative suggestions
        print("\n NARRATIVE SUGGESTIONS:")
        for i, suggestion in enumerate(suggestions["narrative_suggestions"], 1):
            print(f"  {i}. {suggestion}")

        # Consistency notes
        if suggestions["consistency_notes"]:
            print("\n[WARNING] CONSISTENCY REMINDERS:")
            for note in suggestions["consistency_notes"]:
                print(f"  • {note}")

        input("\nPress Enter to continue...")
