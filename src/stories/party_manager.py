"""
Party Management for Story System

Handles current party configuration, adding/removing members,
and party validation operations.
"""

from typing import List, Optional
from src.cli.party_config_manager import load_current_party, save_current_party

class PartyManager:
    """Manages party member configuration and operations."""

    def __init__(self, campaign_name: Optional[str], workspace_path: Optional[str] = None):
        """Initialize party manager with campaign context.

        Args:
            campaign_name: Name of the campaign. Pass None when no campaign
                is selected; all operations will return empty results.
            workspace_path: Optional workspace root path.
        """
        self.campaign_name = campaign_name
        self.workspace_path = workspace_path

    def get_current_party(self) -> List[str]:
        """Get current party members from configuration."""
        if not self.campaign_name:
            return []
        return load_current_party(self.campaign_name, self.workspace_path)

    def set_current_party(self, party_members: List[str]) -> None:
        """Set current party members and save to configuration."""
        if not self.campaign_name:
            return
        save_current_party(party_members, self.campaign_name, self.workspace_path)

    def add_party_member(self, character_name: str) -> None:
        """Add a character to the current party."""
        party_members = self.get_current_party()
        if character_name not in party_members:
            party_members.append(character_name)
            self.set_current_party(party_members)
            print(f"[SUCCESS] Added {character_name} to the party")
        else:
            print(f"[WARNING] {character_name} is already in the party")

    def remove_party_member(self, character_name: str) -> None:
        """Remove a character from the current party."""
        party_members = self.get_current_party()
        if character_name in party_members:
            party_members.remove(character_name)
            self.set_current_party(party_members)
            print(f"[SUCCESS] Removed {character_name} from the party")
        else:
            print(f"[WARNING] {character_name} is not in the party")
