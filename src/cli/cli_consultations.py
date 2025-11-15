"""
Consultations CLI Module

Handles character consultations, DC suggestions, and DM narrative suggestions.
"""

from typing import Dict, Any
from src.utils.cli_utils import select_character_from_list, get_non_empty_input


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

    def get_dm_narrative_suggestions(self):
        """Get DM narrative suggestions based on user prompt."""
        print("\n DM NARRATIVE SUGGESTIONS")
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
            print(f"\nAvailable characters: {', '.join(characters)}")
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
            print(f"\nAvailable NPCs: {', '.join(npcs)}")
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
        self._display_dm_suggestions(suggestions)

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
                if insight["class_expertise"]:
                    print(f"    Class expertise: {insight['class_expertise']}")

        # NPC insights
        if suggestions["npc_insights"]:
            print("\n NPC INSIGHTS:")
            for npc_name, insight in suggestions["npc_insights"].items():
                print(f"\n  {npc_name}:")
                print(f"    Personality: {insight['personality']}")
                print(f"    Role: {insight['role']}")
                print(f"    Likely behavior: {insight['likely_behavior']}")
                if insight["relationships"]:
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
