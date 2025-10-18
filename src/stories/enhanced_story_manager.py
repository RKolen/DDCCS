"""
Enhanced Story Management System with User Choice and Character Agent Integration

Refactored to use composition pattern with specialized manager classes.
"""

import os
from typing import Dict, List, Any, Optional

from src.characters.consultants.character_profile import CharacterProfile
from src.utils.path_utils import get_campaigns_dir, get_characters_dir, get_party_config_path
from src.stories.party_manager import PartyManager
from src.stories.character_manager import CharacterManager
from src.stories.session_results_manager import StorySession, create_session_results_file
from src.npcs.npc_auto_detection import (
    detect_npc_suggestions,
    generate_npc_from_story,
    save_npc_profile,
)
from src.stories.story_file_manager import (
    get_existing_stories,
    get_story_series,
    get_story_files_in_series,
    create_new_story_series,
    create_story_in_series,
    create_new_story,
    create_pure_narrative_story,
    create_pure_story_file,
)
from src.stories.hooks_and_analysis import create_story_hooks_file
from src.characters.character_consistency import (
    create_character_development_file,
    get_available_recruits,
)


class EnhancedStoryManager:
    """Enhanced story manager using composition pattern.

    Coordinates specialized managers for party, characters, stories, NPCs, and sessions.
    Each manager handles a specific aspect of the story management system.
    """

    def __init__(
        self, workspace_path: str, party_config_path: str = None, ai_client=None
    ):
        """Initialize enhanced story manager with specialized managers.

        Args:
            workspace_path: Root workspace path
            party_config_path: Optional party config path
            ai_client: Optional AI client for enhanced features
        """
        self.workspace_path = workspace_path
        self.stories_path = get_campaigns_dir(workspace_path)
        self.characters_path = get_characters_dir(workspace_path)
        self.ai_client = ai_client

        # Initialize specialized managers
        party_config = party_config_path or get_party_config_path(workspace_path)
        self.party_manager = PartyManager(party_config)
        self.character_manager = CharacterManager(self.characters_path, ai_client)

        # Ensure directories exist
        os.makedirs(self.characters_path, exist_ok=True)
        os.makedirs(self.stories_path, exist_ok=True)

        # Load characters on initialization
        self.character_manager.load_characters()

    # ===== Party Management (delegates to PartyManager) =====

    def get_current_party(self) -> List[str]:
        """Get current party members from configuration."""
        return self.party_manager.get_current_party()

    def set_current_party(self, party_members: List[str]):
        """Set current party members and save to configuration."""
        self.party_manager.set_current_party(party_members)

    def add_party_member(self, character_name: str):
        """Add a character to the current party."""
        self.party_manager.add_party_member(character_name)

    def remove_party_member(self, character_name: str):
        """Remove a character from the current party."""
        self.party_manager.remove_party_member(character_name)

    # ===== Character Management (delegates to CharacterManager) =====

    def load_characters(self):
        """Load all character profiles and create consultants."""
        self.character_manager.load_characters()

    def get_character_list(self) -> List[str]:
        """Get list of all character names."""
        return self.character_manager.get_character_list()

    def get_character_profile(self, character_name: str) -> Optional[CharacterProfile]:
        """Get a specific character's profile."""
        return self.character_manager.get_character_profile(character_name)

    def get_available_recruits(
        self, exclude_characters: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Get available character agents for recruitment, excluding current party."""
        if exclude_characters is None:
            exclude_characters = self.get_current_party()
        return get_available_recruits(
            self.character_manager.consultants, exclude_characters
        )

    def _apply_spell_highlighting(self, text: str) -> str:
        """Apply spell name highlighting to narrative text (internal use)."""
        return self.character_manager.apply_spell_highlighting(text)

    # ===== Story File Management (delegates to story_file_manager module) =====

    def get_existing_stories(self) -> List[str]:
        """Get existing story files in the root directory (legacy stories)."""
        return get_existing_stories(self.stories_path)

    def get_story_series(self) -> List[str]:
        """Get available story series (folders with numbered stories)."""
        return get_story_series(self.stories_path)

    def get_story_files_in_series(self, series_name: str) -> List[str]:
        """Get story files within a specific series folder."""
        return get_story_files_in_series(self.stories_path, series_name)

    def create_new_story_series(
        self, series_name: str, first_story_name: str, description: str = ""
    ) -> str:
        """Create a new story series in its own folder."""
        return create_new_story_series(
            self.stories_path,
            self.workspace_path,
            series_name,
            first_story_name,
            description,
        )

    def create_story_in_series(
        self, series_name: str, story_name: str, description: str = ""
    ) -> str:
        """Create a new story in an existing series."""
        return create_story_in_series(
            self.stories_path,
            self.workspace_path,
            series_name,
            story_name,
            description,
        )

    def create_new_story(self, story_name: str, description: str = "") -> str:
        """Create new story file with next sequence number (legacy)."""
        return create_new_story(
            self.stories_path, self.workspace_path, story_name, description
        )

    def _get_story_files(self) -> List[str]:
        """Get all story files in sequence order (internal - legacy method)."""
        return self.get_existing_stories()

    def _create_pure_narrative_story(
        self, series_name: str, story_name: str, description: str = ""
    ) -> str:
        """Create a story file with pure narrative template (internal use)."""
        return create_pure_narrative_story(
            self.stories_path,
            self.workspace_path,
            series_name,
            story_name,
            description,
        )

    def _create_pure_story_file(
        self, series_path: str, story_name: str, narrative_content: str
    ) -> str:
        """Create a story file with pure narrative content only (internal use)."""
        return create_pure_story_file(series_path, story_name, narrative_content)

    # ===== Session Management (delegates to session_results_manager) =====

    def create_session_results_file(
        self, series_path: str, session: StorySession
    ) -> str:
        """Create a separate file for session results (rolls, mechanics, etc.)."""
        return create_session_results_file(series_path, session)

    def create_story_hooks_file(
        self, series_path: str, story_name: str, hooks: List[str], **kwargs
    ) -> str:
        """Create a separate file for future story hooks and session suggestions."""
        story_content = kwargs.get("story_content")
        session_date = kwargs.get("session_date")
        npc_suggestions = None
        if story_content:
            npc_suggestions = self.detect_npc_suggestions(story_content)

        return create_story_hooks_file(
            series_path, story_name, hooks, session_date, npc_suggestions
        )

    def _create_character_development_file(
        self,
        series_path: str,
        story_name: str,
        character_actions: List[Dict[str, str]],
        session_date: str = None,
    ) -> str:
        """Create file for character development suggestions (internal use)."""
        return create_character_development_file(
            series_path, story_name, character_actions, session_date
        )

    # ===== NPC Management (delegates to npc_auto_detection module) =====

    def detect_npc_suggestions(self, story_content: str) -> List[Dict[str, str]]:
        """Detect potential NPCs in story content that might need profiles created."""
        party_names = self.get_current_party()
        return detect_npc_suggestions(story_content, party_names, self.workspace_path)

    def _generate_npc_from_story(
        self, npc_name: str, context: str, role: str = ""
    ) -> Dict[str, Any]:
        """Generate an NPC profile based on story context using AI (internal use)."""
        return generate_npc_from_story(npc_name, context, role, self.ai_client)

    def _save_npc_profile(self, npc_profile: Dict[str, Any]) -> str:
        """Save an NPC profile to game_data/npcs/ directory (internal use)."""
        return save_npc_profile(npc_profile, self.workspace_path)

    # ===== Utility Methods =====

    @property
    def consultants(self):
        """Access to character consultants (for backward compatibility)."""
        return self.character_manager.consultants


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
            "\\n[WARNING] No available recruits - all characters are in the party!"
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
