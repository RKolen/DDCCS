"""Storage for character arc data."""

import os
from typing import Dict, List, Optional

from src.character_arc.arc_data import ArcDataPoint, CharacterArc
from src.utils.file_io import ensure_directory, load_json_file, save_json_file
from src.utils.path_utils import get_game_data_path


class ArcStorage:
    """Manages storage of character arc data for a campaign."""

    _ARC_SUBDIR = "arcs"

    def __init__(
        self,
        campaign_name: str,
        workspace_path: Optional[str] = None,
    ):
        """Initialize arc storage for a campaign.

        Args:
            campaign_name: Name of the campaign.
            workspace_path: Optional workspace root path.
        """
        self.campaign_name = campaign_name
        self.workspace_path = workspace_path
        self._arcs: Dict[str, CharacterArc] = {}
        self._load_arcs()

    @property
    def arcs_dir(self) -> str:
        """Get the directory for arc storage."""
        return os.path.join(
            get_game_data_path(self.workspace_path),
            "campaigns",
            self.campaign_name,
            self._ARC_SUBDIR,
        )

    def _arc_file_path(self, character_name: str) -> str:
        """Return the path for a character's arc JSON file."""
        safe_name = character_name.lower().replace(" ", "_")
        return os.path.join(self.arcs_dir, f"{safe_name}_arc.json")

    def _load_arcs(self) -> None:
        """Load all arc files for the campaign."""
        if not os.path.isdir(self.arcs_dir):
            return

        for filename in os.listdir(self.arcs_dir):
            if not filename.endswith("_arc.json"):
                continue
            arc_file = os.path.join(self.arcs_dir, filename)
            data = load_json_file(arc_file)
            if data:
                try:
                    arc = CharacterArc.from_dict(data)
                    self._arcs[arc.character_name.lower()] = arc
                except (KeyError, TypeError):
                    pass

    def get_arc(self, character_name: str) -> Optional[CharacterArc]:
        """Get arc data for a character.

        Args:
            character_name: The character's name.

        Returns:
            CharacterArc if found, else None.
        """
        return self._arcs.get(character_name.lower())

    def save_arc(self, arc: CharacterArc) -> None:
        """Persist arc data to disk.

        Args:
            arc: CharacterArc to save.
        """
        self._arcs[arc.character_name.lower()] = arc
        ensure_directory(self.arcs_dir)
        arc_file = self._arc_file_path(arc.character_name)
        save_json_file(arc_file, arc.to_dict())

    def create_arc(
        self,
        character_name: str,
        baseline: Optional[Dict] = None,
    ) -> CharacterArc:
        """Create and persist a new arc for a character.

        Args:
            character_name: Name of the character.
            baseline: Optional baseline metric values from character profile.

        Returns:
            The newly created CharacterArc.
        """
        arc = CharacterArc(
            character_name=character_name,
            campaign_name=self.campaign_name,
            baseline=baseline or {},
        )
        self.save_arc(arc)
        return arc

    def add_data_point(
        self,
        character_name: str,
        data_point: ArcDataPoint,
    ) -> None:
        """Add a data point to a character's arc, creating it if needed.

        Args:
            character_name: Name of the character.
            data_point: The data point to append.
        """
        arc = self.get_arc(character_name)
        if not arc:
            arc = self.create_arc(character_name)
        arc.add_data_point(data_point)
        self.save_arc(arc)

    def get_all_arcs(self) -> List[CharacterArc]:
        """Return all character arcs for the campaign."""
        return list(self._arcs.values())

    def delete_arc(self, character_name: str) -> bool:
        """Delete an arc from storage.

        Args:
            character_name: Name of the character whose arc to delete.

        Returns:
            True if the arc was found and deleted, False otherwise.
        """
        arc = self._arcs.pop(character_name.lower(), None)
        if arc:
            arc_file = self._arc_file_path(arc.character_name)
            if os.path.exists(arc_file):
                os.remove(arc_file)
            return True
        return False
