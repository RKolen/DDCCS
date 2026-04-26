"""Batch operations for processing multiple characters, campaigns, or stories."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from src.utils.file_io import load_json_file, save_json_file
from src.utils.path_utils import get_characters_dir, get_game_data_path


@dataclass
class BatchResult:
    """Result of a single batch operation."""

    item: str
    success: bool
    message: str = ""
    data: Optional[Dict[str, Any]] = field(default=None)


class BatchProcessor:
    """Apply an operation to multiple characters, campaigns, or story files.

    Each process_* method accepts an optional list of names; when omitted it
    discovers all available items automatically.  An optional progress_callback
    is called after each item with signature (name, current_index, total).
    """

    def process_characters(
        self,
        operation: Callable[[str, Dict[str, Any]], BatchResult],
        character_names: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> List[BatchResult]:
        """Apply an operation to one or more character JSON files.

        Args:
            operation: Callable receiving (name, data) and returning a
                BatchResult.  Set result.data to the modified dict to persist
                changes; leave it as None to skip saving.
            character_names: Names to process.  Processes all characters when
                None.
            progress_callback: Optional callback invoked as
                (name, current, total) after each item is processed.

        Returns:
            List of BatchResult, one per character.
        """
        if character_names is None:
            characters_dir = Path(get_characters_dir())
            character_names = sorted(
                f.stem
                for f in characters_dir.glob("*.json")
                if not f.name.startswith(".")
            )

        results: List[BatchResult] = []
        total = len(character_names)
        for index, name in enumerate(character_names):
            if progress_callback:
                progress_callback(name, index + 1, total)
            results.append(self._run_character_op(name, operation))
        return results

    def _run_character_op(
        self,
        name: str,
        operation: Callable[[str, Dict[str, Any]], BatchResult],
    ) -> BatchResult:
        """Execute one operation on a single character file.

        Args:
            name: Character name (stem of the JSON file).
            operation: Callable receiving (name, data) and returning a
                BatchResult.

        Returns:
            BatchResult with the outcome of the operation.
        """
        char_path = Path(get_characters_dir()) / f"{name}.json"
        if not char_path.exists():
            return BatchResult(
                item=name, success=False, message="Character file not found"
            )
        try:
            char_data: Dict[str, Any] = load_json_file(str(char_path)) or {}
            result = operation(name, char_data)
            if result.success and result.data is not None:
                save_json_file(str(char_path), result.data)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            return BatchResult(item=name, success=False, message=str(exc))
        return result

    def process_campaigns(
        self,
        operation: Callable[[str, Path], BatchResult],
        campaign_names: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> List[BatchResult]:
        """Apply an operation to one or more campaign directories.

        Args:
            operation: Callable receiving (name, path) and returning a
                BatchResult.
            campaign_names: Names to process.  Processes all campaigns when
                None.
            progress_callback: Optional callback invoked as
                (name, current, total) after each item is processed.

        Returns:
            List of BatchResult, one per campaign.
        """
        if campaign_names is None:
            campaigns_dir = Path(get_game_data_path()) / "campaigns"
            campaign_names = sorted(
                d.name for d in campaigns_dir.iterdir() if d.is_dir()
            )

        results: List[BatchResult] = []
        total = len(campaign_names)
        for index, name in enumerate(campaign_names):
            if progress_callback:
                progress_callback(name, index + 1, total)
            results.append(self._run_campaign_op(name, operation))
        return results

    def _run_campaign_op(
        self,
        name: str,
        operation: Callable[[str, Path], BatchResult],
    ) -> BatchResult:
        """Execute one operation on a single campaign directory.

        Args:
            name: Campaign name.
            operation: Callable receiving (name, path) and returning a
                BatchResult.

        Returns:
            BatchResult with the outcome of the operation.
        """
        campaign_path = Path(get_game_data_path()) / "campaigns" / name
        if not campaign_path.exists():
            return BatchResult(item=name, success=False, message="Campaign not found")
        try:
            result = operation(name, campaign_path)
        except (OSError, ValueError) as exc:
            return BatchResult(item=name, success=False, message=str(exc))
        return result

    def process_stories(
        self,
        campaign_name: str,
        operation: Callable[[str, str], BatchResult],
        story_files: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[str, int, int], None]] = None,
    ) -> List[BatchResult]:
        """Apply an operation to story files within a campaign.

        Args:
            campaign_name: Name of the campaign folder.
            operation: Callable receiving (filename, full_path_str) and
                returning a BatchResult.
            story_files: File names to process.  Processes all .md files when
                None.
            progress_callback: Optional callback invoked as
                (filename, current, total) after each item is processed.

        Returns:
            List of BatchResult, one per story file.  Returns a single failure
            result when the campaign directory does not exist.
        """
        campaign_path = Path(get_game_data_path()) / "campaigns" / campaign_name
        if not campaign_path.exists():
            return [
                BatchResult(
                    item=campaign_name,
                    success=False,
                    message="Campaign not found",
                )
            ]

        if story_files is None:
            story_files = sorted(f.name for f in campaign_path.glob("*.md"))

        results: List[BatchResult] = []
        total = len(story_files)
        for index, story_file in enumerate(story_files):
            if progress_callback:
                progress_callback(story_file, index + 1, total)
            results.append(self._run_story_op(campaign_path, story_file, operation))
        return results

    def _run_story_op(
        self,
        campaign_path: Path,
        story_file: str,
        operation: Callable[[str, str], BatchResult],
    ) -> BatchResult:
        """Execute one operation on a single story file.

        Args:
            campaign_path: Path to the campaign directory.
            story_file: Story file name.
            operation: Callable receiving (filename, full_path_str) and
                returning a BatchResult.

        Returns:
            BatchResult with the outcome of the operation.
        """
        story_path = campaign_path / story_file
        if not story_path.exists():
            return BatchResult(
                item=story_file, success=False, message="Story file not found"
            )
        try:
            result = operation(story_file, str(story_path))
        except (OSError, ValueError) as exc:
            return BatchResult(item=story_file, success=False, message=str(exc))
        return result


def batch_level_up(amount: int = 1) -> Callable[[str, Dict[str, Any]], BatchResult]:
    """Create a level-up operation for use with BatchProcessor.process_characters.

    Args:
        amount: Number of levels to add per character.

    Returns:
        Operation callable that increments the 'level' field and returns a
        BatchResult with the updated character data.
    """

    def operation(name: str, data: Dict[str, Any]) -> BatchResult:
        """Increment a character's level.

        Args:
            name: Character name.
            data: Character data dictionary.

        Returns:
            BatchResult with updated data on success.
        """
        current_level = int(data.get("level", 1))
        new_level = current_level + amount
        data["level"] = new_level
        return BatchResult(
            item=name,
            success=True,
            message=f"Level {current_level} -> {new_level}",
            data=data,
        )

    return operation


def batch_add_item(
    item_name: str, quantity: int = 1
) -> Callable[[str, Dict[str, Any]], BatchResult]:
    """Create an add-item operation for use with BatchProcessor.process_characters.

    If the item already exists in the character's equipment list its quantity
    is incremented; otherwise a new entry is appended.

    Args:
        item_name: Name of the item to add.
        quantity: Quantity to add per character.

    Returns:
        Operation callable that appends or updates an equipment entry and
        returns a BatchResult with the updated character data.
    """

    def operation(name: str, data: Dict[str, Any]) -> BatchResult:
        """Add an item to a single character's equipment.

        Args:
            name: Character name.
            data: Character data dictionary.

        Returns:
            BatchResult with updated data on success.
        """
        equipment = data.get("equipment", [])
        if not isinstance(equipment, list):
            equipment = []

        found = False
        for item in equipment:
            if isinstance(item, dict) and item.get("name") == item_name:
                item["quantity"] = int(item.get("quantity", 1)) + quantity
                found = True
                break

        if not found:
            equipment.append({"name": item_name, "quantity": quantity})

        data["equipment"] = equipment
        return BatchResult(
            item=name,
            success=True,
            message=f"Added {quantity}x {item_name}",
            data=data,
        )

    return operation
