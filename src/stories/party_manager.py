"""
Party Management for Story System

Handles current party configuration, adding/removing members,
and party validation operations.
"""

from typing import List

from src.cli.party_config_manager import load_current_party, save_current_party


class PartyManager:
    """Manages party member configuration and operations."""

    def __init__(self, party_config_path: str):
        """Initialize party manager with config path.

        Args:
            party_config_path: Path to party configuration JSON file
        """
        self.party_config_path = party_config_path

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
