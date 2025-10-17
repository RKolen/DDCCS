"""
Enhanced Story Management System with User Choice and Character Agent Integration
"""

import os
import json
from typing import Dict, List, Any, Optional
from character_consultants import CharacterConsultant, CharacterProfile
from spell_highlighter import highlight_spells_in_text
from party_config_manager import load_current_party, save_current_party
from session_results_manager import StorySession, create_session_results_file
from npc_auto_detection import (
    detect_npc_suggestions,
    generate_npc_from_story,
    save_npc_profile,
)
from story_file_manager import (
    get_existing_stories,
    get_story_series,
    get_story_files_in_series,
    validate_series_name,
    create_story_template,
    create_new_story_series,
    create_story_in_series,
    create_new_story,
    create_pure_narrative_story,
    create_pure_story_file,
)
from hooks_and_analysis import create_story_hooks_file
from character_consistency import (
    create_character_development_file,
    get_available_recruits,
)

# Optional validator import (fail-safe if not available)
try:
    from character_validator import validate_character_file
    VALIDATOR_AVAILABLE = True
except ImportError:
    VALIDATOR_AVAILABLE = False
    validate_character_file = None


class EnhancedStoryManager:  # pylint: disable=too-many-public-methods
    """Enhanced story manager with user choice and better organization.
    
    Note: High method count is intentional - provides comprehensive API for
    story management, party management, character consultations, and NPC operations.
    """

    def __init__(
        self, workspace_path: str, party_config_path: str = None, ai_client=None
    ):
        self.workspace_path = workspace_path
        self.stories_path = os.path.join(workspace_path, "game_data", "campaigns")
        self.characters_path = os.path.join(workspace_path, "game_data", "characters")
        self.party_config_path = party_config_path or os.path.join(
            workspace_path, "game_data", "current_party", "current_party.json"
        )
        self.ai_client = ai_client  # AI client for enhanced features
        self.consultants = {}
        self.known_spells = set()  # Initialize known spells cache

        # Ensure directories exist
        os.makedirs(self.characters_path, exist_ok=True)
        os.makedirs(self.stories_path, exist_ok=True)

        # Load existing characters
        self.load_characters()

    def get_current_party(self) -> List[str]:
        """Get current party members from configuration."""
        return load_current_party(self.party_config_path)

    def set_current_party(self, party_members: List[str]):
        """Set current party members and save to configuration."""
        save_current_party(party_members, self.party_config_path)

    def add_party_member(self, character_name: str):
        """Add a character to the current party."""
        party_members = self.get_current_party()
        if character_name not in party_members:
            party_members.append(character_name)
            self.set_current_party(party_members)
            print(f"[SUCCESS] Added {character_name} to the party")
        else:
            print(f"[WARNING] {character_name} is already in the party")

    def remove_party_member(self, character_name: str):
        """Remove a character from the current party."""
        party_members = self.get_current_party()
        if character_name in party_members:
            party_members.remove(character_name)
            self.set_current_party(party_members)
            print(f"[SUCCESS] Removed {character_name} from the party")
        else:
            print(f"[WARNING] {character_name} is not in the party")

    def load_characters(self):
        """Load all character profiles and create consultants."""
        if not os.path.exists(self.characters_path):
            return

        for filename in os.listdir(self.characters_path):
            # Skip template and example files
            if (
                filename.endswith(".json")
                and not filename.startswith("class.example")
                and not filename.endswith(".example.json")
                and not filename.startswith("template")
            ):

                filepath = os.path.join(self.characters_path, filename)

                # Validate character JSON before loading
                if VALIDATOR_AVAILABLE:
                    is_valid, errors = validate_character_file(filepath)
                    if not is_valid:
                        print(f"✗ Validation failed for {filename}:")
                        for error in errors:
                            print(f"  - {error}")
                        continue

                try:
                    profile = CharacterProfile.load_from_file(filepath)
                    self.consultants[profile.name] = CharacterConsultant(
                        profile, ai_client=self.ai_client
                    )
                    if VALIDATOR_AVAILABLE:
                        print(f"✓ Loaded and validated: {filename}")
                except (FileNotFoundError, json.JSONDecodeError, KeyError, ValueError) as e:
                    print(f"Warning: Could not load character {filename}: {e}")

        # Extract known spells from all loaded characters
        self._update_known_spells()

    def _update_known_spells(self):
        """Extract and cache known spells from all loaded characters."""
        self.known_spells = set()
        for consultant in self.consultants.values():
            # Add known spells from profile
            if consultant.profile.known_spells:
                self.known_spells.update(
                    spell.lower() for spell in consultant.profile.known_spells
                )

            # Add known spells from character sheet if available
            if (
                hasattr(consultant.profile, "character_sheet")
                and consultant.profile.character_sheet
            ):
                if hasattr(consultant.profile.character_sheet, "known_spells"):
                    self.known_spells.update(
                        spell.lower()
                        for spell in consultant.profile.character_sheet.known_spells
                    )

    def apply_spell_highlighting(self, text: str) -> str:
        """Apply spell name highlighting to narrative text."""
        return highlight_spells_in_text(text, self.known_spells)

    def should_create_new_story_file(
        self, series_name: str, session_results: StorySession
    ) -> bool:
        """Ask user if they want to create a new story file or continue existing one."""
        print(f"\\nSession results for '{session_results.story_name}':")
        print(f"- {len(session_results.roll_results)} dice rolls recorded")
        print(f"- {len(session_results.character_actions)} character actions")
        print(f"- {len(session_results.narrative_events)} story events")

        while True:
            choice = input("\\nCreate new story file? (y/n/continue): ").strip().lower()
            if choice in ["y", "yes"]:
                return True
            if choice in ["n", "no"]:
                return False
            if choice in ["c", "continue"]:
                return self._continue_existing_story(series_name)
            print(
                "Please enter 'y' for yes, 'n' for no, or 'continue' to update existing file"
            )

    def _continue_existing_story(self, series_name: str) -> bool:
        """Handle continuing an existing story file."""
        existing_stories = self.get_story_files_in_series(series_name)
        if not existing_stories:
            print("No existing stories found. Creating new file.")
            return True

        print("\\nExisting stories:")
        for i, story in enumerate(existing_stories, 1):
            print(f"{i}. {story}")

        try:
            choice = int(input("\\nSelect story to update (number): "))
            if 1 <= choice <= len(existing_stories):
                return False  # Don't create new, update existing
            print("Invalid choice. Creating new story.")
            return True
        except ValueError:
            print("Invalid input. Creating new story.")
            return True

    def get_available_recruits(
        self, exclude_characters: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Get available character agents for recruitment, excluding current party."""
        if exclude_characters is None:
            exclude_characters = self.get_current_party()

        return get_available_recruits(self.consultants, exclude_characters)

    def get_existing_stories(self) -> List[str]:
        """Get existing story files in the root directory (legacy stories)."""
        return get_existing_stories(self.stories_path)

    def get_story_series(self) -> List[str]:
        """Get available story series (folders with numbered stories)."""
        return get_story_series(self.stories_path)

    def get_story_files_in_series(self, series_name: str) -> List[str]:
        """Get story files within a specific series folder."""
        return get_story_files_in_series(self.stories_path, series_name)

    def get_story_files(self) -> List[str]:
        """Get all story files in sequence order (legacy method for backward compatibility)."""
        return self.get_existing_stories()

    def _validate_series_name(self, series_name: str) -> str:
        """Validate and ensure series name has proper suffix."""
        return validate_series_name(series_name)

    def create_new_story_series(
        self, series_name: str, first_story_name: str, description: str = ""
    ) -> str:
        """
        Create a new story series in its own folder.

        Series name MUST end with: _Campaign, _Quest, _Story, or _Adventure
        """
        return create_new_story_series(
            self.stories_path, self.workspace_path, series_name,
            first_story_name, description
        )

    def create_story_in_series(
        self, series_name: str, story_name: str, description: str = ""
    ) -> str:
        """Create a new story in an existing series."""
        return create_story_in_series(
            self.stories_path, self.workspace_path, series_name,
            story_name, description
        )

    def create_new_story(self, story_name: str, description: str = "") -> str:
        """Create new story file with next sequence number (for legacy stories in root)."""
        return create_new_story(
            self.stories_path, self.workspace_path, story_name, description
        )

    def _create_story_template(
        self, story_name: str, description: str, use_template: bool = False
    ) -> str:
        """Create a markdown template for a new story."""
        return create_story_template(
            story_name, description, use_template, self.workspace_path
        )

    def create_pure_narrative_story(
        self, series_name: str, story_name: str, description: str = ""
    ) -> str:
        """Create a story file with pure narrative template (no guidance sections)."""
        return create_pure_narrative_story(
            self.stories_path, self.workspace_path, series_name,
            story_name, description
        )

    def get_character_list(self) -> List[str]:
        """Get list of all character names."""
        return list(self.consultants.keys())

    def get_character_profile(self, character_name: str) -> Optional[CharacterProfile]:
        """Get a specific character's profile."""
        consultant = self.consultants.get(character_name)
        return consultant.profile if consultant else None

    def create_pure_story_file(
        self, series_path: str, story_name: str, narrative_content: str
    ) -> str:
        """Create a story file with pure narrative content only."""
        return create_pure_story_file(series_path, story_name, narrative_content)

    def create_session_results_file(
        self, series_path: str, session: StorySession
    ) -> str:
        """
        Create a separate file for session results (rolls, mechanics, etc.).

        Delegates to session_results_manager module.
        """
        return create_session_results_file(series_path, session)

    def create_character_development_file(
        self,
        series_path: str,
        story_name: str,
        character_actions: List[Dict[str, str]],
        session_date: str = None,
    ) -> str:
        """Create a separate file for character development suggestions."""
        return create_character_development_file(
            series_path, story_name, character_actions, session_date
        )

    def detect_npc_suggestions(self, story_content: str) -> List[Dict[str, str]]:
        """
        Detect potential NPCs in story content that might need profiles created.

        Delegates to npc_auto_detection module.

        Args:
            story_content: The story text to analyze

        Returns:
            List of dictionaries with NPC suggestions (name, role, context_excerpt)
        """
        party_names = self.get_current_party()
        return detect_npc_suggestions(
            story_content, party_names, self.workspace_path
        )

    def create_story_hooks_file(
        self, series_path: str, story_name: str, hooks: List[str], **kwargs
    ) -> str:
        """
        Create a separate file for future story hooks and session suggestions.

        Args:
            series_path: Path to campaign folder
            story_name: Name of the story
            hooks: List of story hook strings
            **kwargs: Optional args (session_date, story_content)
        """
        # Detect NPC suggestions if story content provided
        story_content = kwargs.get('story_content')
        session_date = kwargs.get('session_date')
        npc_suggestions = None
        if story_content:
            npc_suggestions = self.detect_npc_suggestions(story_content)

        return create_story_hooks_file(
            series_path, story_name, hooks, session_date, npc_suggestions
        )

    def generate_npc_from_story(
        self, npc_name: str, context: str, role: str = ""
    ) -> Dict[str, Any]:
        """
        Generate an NPC profile based on story context using AI.

        Delegates to npc_auto_detection module.

        Args:
            npc_name: Name of the NPC
            context: Story context where NPC appears
            role: Optional role hint (e.g., "innkeeper", "merchant")

        Returns:
            NPC profile dictionary ready to save as JSON
        """
        return generate_npc_from_story(npc_name, context, role, self.ai_client)

    def save_npc_profile(self, npc_profile: Dict[str, Any]) -> str:
        """
        Save an NPC profile to the game_data/npcs/ directory.

        Delegates to npc_auto_detection module.

        Args:
            npc_profile: NPC profile dictionary

        Returns:
            Path to saved NPC file
        """
        return save_npc_profile(npc_profile, self.workspace_path)


def create_improved_recruitment_system(active_party: List[str] = None):
    """Demonstration of improved recruitment using existing character agents."""
    print("\\n=== IMPROVED RECRUITMENT SYSTEM ===")

    story_mgr = EnhancedStoryManager(".")

    # Use provided party or load from configuration
    if active_party is None:
        active_party = story_mgr.get_current_party()

    available_recruits = story_mgr.get_available_recruits()

    print(f"\\nCurrent party: {', '.join(active_party)}")
    print(f"Party size: {len(active_party)}")
    print(f"Available recruits from character agents: {len(available_recruits)}")

    if available_recruits:
        print("\\nSuggested recruits based on party needs:")
        for recruit in available_recruits[:3]:  # Show top 3 suggestions
            print(f"- {recruit['name']} ({recruit['class']}) Level {recruit['level']}")
            print(f"  Personality: {recruit['personality']}")
            print(f"  Background: {recruit['background'][:100]}...")
            print()
    else:
        print(
            "\\n[WARNING] No available recruits - all characters are already in the party!"
        )

    return available_recruits


if __name__ == "__main__":
    # Demo the improved system
    print("=== PARTY MANAGEMENT DEMO ===")

    manager = EnhancedStoryManager(".")

    # Show current party
    party_list = manager.get_current_party()
    print(f"Current party loaded from config: {party_list}")

    # Demo recruitment system
    create_improved_recruitment_system()

    # Demo party management
    print("\\n=== PARTY MANAGEMENT ===")
    print("Available commands:")
    print("- story_manager.add_party_member('Character Name')")
    print("- story_manager.remove_party_member('Character Name')")
    print("- story_manager.get_current_party()")
    print("- story_manager.set_current_party(['Name1', 'Name2', ...])")
    print("\\nParty configuration is saved to 'current_party.json'")
