"""Per-campaign in-world date tracking, persisted in the campaign timeline.json."""

import os
from typing import Any, Dict, Optional

from src.calendar.calendar_engine import CalendarEngine, InWorldDate
from src.utils.file_io import load_json_file, save_json_file
from src.utils.path_utils import get_game_data_path


class DateTracker:
    """Tracks the current in-world date for a campaign.

    Reads and writes only the ``current_date`` and ``calendar_id`` keys at the
    top level of the campaign's ``timeline.json``.  All other keys (events,
    last_updated, etc.) are preserved unchanged.
    """

    _TIMELINE_FILE = "timeline.json"

    def __init__(
        self,
        campaign_name: str,
        calendar_id: str = "generic",
        workspace_path: Optional[str] = None,
    ):
        """Initialize date tracker for a campaign.

        Args:
            campaign_name: Name of the campaign directory under campaigns/.
            calendar_id: Calendar ID to use (must match a file in game_data/calendars/).
            workspace_path: Optional workspace root for testing.
        """
        self.campaign_name = campaign_name
        self._workspace_path = workspace_path
        self._current_date: Optional[InWorldDate] = None
        self._load()
        resolved_id = self._persisted_calendar_id() or calendar_id
        self.calendar = CalendarEngine(resolved_id, workspace_path)

    def _timeline_path(self) -> str:
        """Return the absolute path to the campaign timeline.json."""
        return os.path.join(
            get_game_data_path(self._workspace_path),
            "campaigns",
            self.campaign_name,
            self._TIMELINE_FILE,
        )

    def _read_timeline_data(self) -> Dict[str, Any]:
        """Load existing timeline.json or return an empty dict."""
        path = self._timeline_path()
        if os.path.exists(path):
            return load_json_file(path) or {}
        return {}

    def _persisted_calendar_id(self) -> str:
        """Return the calendar_id stored in timeline.json, or empty string."""
        return self._read_timeline_data().get("calendar_id", "")

    def _load(self) -> None:
        """Load current_date from the campaign timeline.json."""
        data = self._read_timeline_data()
        raw_date = data.get("current_date")
        if raw_date:
            try:
                self._current_date = InWorldDate.from_dict(raw_date)
            except (KeyError, TypeError):
                self._current_date = None

    def _save(self) -> None:
        """Persist current_date and calendar_id into the campaign timeline.json.

        Existing keys (events, last_updated, campaign_name, etc.) are preserved.
        """
        data = self._read_timeline_data()
        data["campaign_name"] = self.campaign_name
        data["calendar_id"] = self.calendar.calendar_id
        data["current_date"] = (
            self._current_date.to_dict() if self._current_date else None
        )
        save_json_file(self._timeline_path(), data)

    def get_current_date(self) -> Optional[InWorldDate]:
        """Return the current in-world date, or None if not set.

        Returns:
            Current InWorldDate or None.
        """
        return self._current_date

    def set_current_date(self, date: InWorldDate) -> None:
        """Set the current in-world date and persist it.

        Args:
            date: New in-world date to record as the current date.
        """
        self._current_date = date
        self._save()

    def advance_days(self, days: int) -> Optional[InWorldDate]:
        """Advance the current date by a number of days.

        Args:
            days: Number of days to advance (may be negative to go back).

        Returns:
            Updated InWorldDate, or None if no current date was set.
        """
        if self._current_date is None:
            return None
        self._current_date = self.calendar.add_days(self._current_date, days)
        self._save()
        return self._current_date

    def get_date_context_for_prompt(self) -> str:
        """Return a formatted date context string for AI prompt injection.

        Returns:
            Multi-line string with date and season, or empty string if no date set.
        """
        if self._current_date is None:
            return ""

        ctx = self.calendar.get_date_context(self._current_date)
        lines = [
            f"Current In-World Date: {ctx['formatted']}",
            f"Season: {ctx['season'] or 'Unknown'}",
        ]
        if ctx.get("holiday"):
            holiday = ctx["holiday"]
            lines.append(f"Holiday: {holiday['name']} - {holiday['description']}")

        return "\n".join(lines)
