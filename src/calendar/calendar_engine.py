"""In-world calendar engine for D&D campaign date tracking."""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.utils.file_io import load_json_file
from src.utils.path_utils import get_game_data_path


@dataclass
class Month:
    """Represents a month in a calendar."""

    name: str
    days: int
    nickname: str = ""
    month_type: str = "standard"


@dataclass
class Season:
    """Represents a season in a calendar."""

    name: str
    start_month: str
    start_day: int
    end_month: str
    end_day: int


@dataclass
class Holiday:
    """Represents a holiday in a calendar."""

    name: str
    month: str
    day: int
    description: str = ""


@dataclass
class CalendarMeta:
    """Scalar metadata parsed from a calendar definition file."""

    year_length: int = 365
    epoch_abbrev: str = ""
    week_days: List[str] = field(default_factory=list)


@dataclass
class InWorldDate:
    """Represents an in-world campaign date."""

    year: int
    month: str
    day: int
    epoch: str = ""
    calendar_id: str = "generic"

    def __str__(self) -> str:
        """Return formatted date string."""
        if self.epoch:
            return f"{self.day} {self.month}, {self.year} {self.epoch}"
        return f"{self.day} {self.month}, {self.year}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "year": self.year,
            "month": self.month,
            "day": self.day,
            "epoch": self.epoch,
            "calendar_id": self.calendar_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InWorldDate":
        """Create from dictionary.

        Args:
            data: Dictionary with year, month, day, epoch, calendar_id keys.

        Returns:
            InWorldDate instance.
        """
        return cls(
            year=data["year"],
            month=data["month"],
            day=data["day"],
            epoch=data.get("epoch", ""),
            calendar_id=data.get("calendar_id", "generic"),
        )


class CalendarEngine:
    """Manages calendar definitions and date calculations."""

    def __init__(
        self,
        calendar_id: str = "generic",
        workspace_path: Optional[str] = None,
    ):
        """Initialize calendar engine with the specified calendar.

        Args:
            calendar_id: ID matching a file in game_data/calendars/.
            workspace_path: Optional workspace root for testing.
        """
        self.calendar_id = calendar_id
        self._calendars_dir_path = os.path.join(
            get_game_data_path(workspace_path), "calendars"
        )
        self._months: List[Month] = []
        self._seasons: List[Season] = []
        self._holidays: List[Holiday] = []
        self._meta = CalendarMeta()
        self._load_calendar()

    def _load_calendar(self) -> None:
        """Load calendar definition from file, falling back to generic."""
        calendar_path = os.path.join(
            self._calendars_dir_path, f"{self.calendar_id}.json"
        )
        if not os.path.exists(calendar_path):
            calendar_path = os.path.join(self._calendars_dir_path, "generic.json")
        if os.path.exists(calendar_path):
            calendar_data: Dict[str, Any] = load_json_file(calendar_path) or {}
            self._parse_calendar(calendar_data)

    def _parse_calendar(self, data: Dict[str, Any]) -> None:
        """Parse raw calendar JSON into structured objects.

        Args:
            data: Parsed calendar JSON dictionary.
        """
        self._meta.year_length = data.get("year_length", 365)

        for month_data in data.get("months", []):
            if month_data.get("frequency") == "leap_year":
                continue
            self._months.append(Month(
                name=month_data["name"],
                days=month_data["days"],
                nickname=month_data.get("nickname", ""),
                month_type=month_data.get("type", "standard"),
            ))

        for season_data in data.get("seasons", []):
            self._seasons.append(Season(
                name=season_data["name"],
                start_month=season_data["start_month"],
                start_day=season_data["start_day"],
                end_month=season_data["end_month"],
                end_day=season_data["end_day"],
            ))

        for holiday_data in data.get("holidays", []):
            self._holidays.append(Holiday(
                name=holiday_data["name"],
                month=holiday_data["month"],
                day=holiday_data["day"],
                description=holiday_data.get("description", ""),
            ))

        week_data = data.get("week", {})
        self._meta.week_days = week_data.get("days", [])

        epochs: List[Dict[str, Any]] = data.get("epochs", [])
        self._meta.epoch_abbrev = epochs[0].get("abbreviation", "") if epochs else ""

    def list_month_names(self) -> List[str]:
        """Return the names of all standard (non-leap-year) months in order.

        Returns:
            List of month name strings.
        """
        return [m.name for m in self._months]

    def default_epoch(self) -> str:
        """Return the abbreviation for the first defined epoch, or empty string.

        Returns:
            Epoch abbreviation such as "DR" or "CE".
        """
        return self._default_epoch()

    def get_month(self, month_name: str) -> Optional[Month]:
        """Get a month by name (case-insensitive).

        Args:
            month_name: Name of the month to find.

        Returns:
            Month instance or None if not found.
        """
        for month in self._months:
            if month.name.lower() == month_name.lower():
                return month
        return None

    def _month_day_of_year(self, month_name: str, day: int) -> int:
        """Return the 0-indexed day-of-year for a month and day.

        Args:
            month_name: Name of the month.
            day: 1-indexed day within the month.

        Returns:
            0-indexed day of year.
        """
        accumulated = 0
        for month in self._months:
            if month.name.lower() == month_name.lower():
                return accumulated + day - 1
            accumulated += month.days
        return accumulated + day - 1

    def get_season(self, date: InWorldDate) -> Optional[str]:
        """Get the season name for a given date.

        Args:
            date: The in-world date to check.

        Returns:
            Season name or None if no season matches.
        """
        date_doy = self._month_day_of_year(date.month, date.day)
        for season in self._seasons:
            if self._date_in_season(date_doy, season):
                return season.name
        return None

    def _date_in_season(self, date_doy: int, season: Season) -> bool:
        """Check whether a day-of-year value falls within a season.

        Handles seasons that cross the year boundary (e.g. Winter).

        Args:
            date_doy: 0-indexed day of year for the date being tested.
            season: Season to check against.

        Returns:
            True if the date falls within the season.
        """
        start_doy = self._month_day_of_year(season.start_month, season.start_day)
        end_doy = self._month_day_of_year(season.end_month, season.end_day)
        if start_doy <= end_doy:
            return start_doy <= date_doy <= end_doy
        return date_doy >= start_doy or date_doy <= end_doy

    def get_holiday(self, date: InWorldDate) -> Optional[Holiday]:
        """Get the holiday for a specific date, if any.

        Args:
            date: The in-world date to check.

        Returns:
            Holiday instance or None.
        """
        for holiday in self._holidays:
            if holiday.month.lower() == date.month.lower() and holiday.day == date.day:
                return holiday
        return None

    def get_week_day(self, date: InWorldDate) -> Optional[str]:
        """Get the day of the week for a date.

        Args:
            date: The in-world date.

        Returns:
            Weekday name or None if the calendar has no week definition.
        """
        if not self._meta.week_days:
            return None
        return self._meta.week_days[self.date_to_ordinal(date) % len(self._meta.week_days)]

    def date_to_ordinal(self, date: InWorldDate) -> int:
        """Convert a date to an absolute 0-indexed day number.

        Args:
            date: The in-world date to convert.

        Returns:
            0-indexed ordinal day number.
        """
        total = date.year * self._meta.year_length
        for month in self._months:
            if month.name.lower() == date.month.lower():
                return total + date.day - 1
            total += month.days
        return total + date.day - 1

    def ordinal_to_date(
        self,
        ordinal: int,
        calendar_id: str = "",
        epoch: str = "",
    ) -> InWorldDate:
        """Convert an absolute day number back to a date.

        Args:
            ordinal: 0-indexed absolute day number.
            calendar_id: Calendar ID for the resulting date (defaults to self).
            epoch: Epoch abbreviation for the resulting date (defaults to first epoch).

        Returns:
            InWorldDate corresponding to the ordinal.
        """
        year = ordinal // self._meta.year_length
        remaining = ordinal % self._meta.year_length
        resolved_epoch = epoch or self._default_epoch()
        resolved_id = calendar_id or self.calendar_id

        accumulated = 0
        for month in self._months:
            if accumulated + month.days > remaining:
                day = remaining - accumulated + 1
                return InWorldDate(
                    year=year,
                    month=month.name,
                    day=day,
                    epoch=resolved_epoch,
                    calendar_id=resolved_id,
                )
            accumulated += month.days

        last = self._months[-1] if self._months else Month("January", 31)
        return InWorldDate(
            year=year,
            month=last.name,
            day=last.days,
            epoch=resolved_epoch,
            calendar_id=resolved_id,
        )

    def _default_epoch(self) -> str:
        """Return the stored epoch abbreviation, or empty string."""
        return self._meta.epoch_abbrev

    def add_days(self, date: InWorldDate, days: int) -> InWorldDate:
        """Add a number of days to a date.

        Args:
            date: Starting date.
            days: Days to add (may be negative).

        Returns:
            New InWorldDate after adding days.
        """
        return self.ordinal_to_date(
            self.date_to_ordinal(date) + days,
            date.calendar_id,
            date.epoch,
        )

    def days_between(self, date1: InWorldDate, date2: InWorldDate) -> int:
        """Return the absolute number of days between two dates.

        Args:
            date1: First date.
            date2: Second date.

        Returns:
            Absolute day difference.
        """
        return abs(self.date_to_ordinal(date1) - self.date_to_ordinal(date2))

    def format_date(self, date: InWorldDate, format_type: str = "long") -> str:
        """Format a date in various styles.

        Args:
            date: Date to format.
            format_type: One of "long", "short", or "narrative".

        Returns:
            Formatted date string.
        """
        if format_type == "short":
            return f"{date.day} {date.month[:3]} {date.year}"
        if format_type == "narrative":
            return self._format_narrative(date)
        return str(date)

    def _format_narrative(self, date: InWorldDate) -> str:
        """Return a narrative-style description of a date."""
        season = self.get_season(date)
        weekday = self.get_week_day(date)
        holiday = self.get_holiday(date)

        parts: List[str] = []
        if weekday:
            parts.append(weekday)
        parts.append(f"the {_ordinal(date.day)} of {date.month}")
        if season:
            parts.append(f"in {season}")
        if holiday:
            parts.append(f"({holiday.name})")
        return " ".join(parts)

    def get_date_context(self, date: InWorldDate) -> Dict[str, Any]:
        """Return full date context suitable for AI prompt injection.

        Args:
            date: The in-world date.

        Returns:
            Dictionary with date, formatted, season, weekday, holiday, year,
            month, and day keys.
        """
        holiday = self.get_holiday(date)
        return {
            "date": str(date),
            "formatted": self.format_date(date, "narrative"),
            "season": self.get_season(date),
            "weekday": self.get_week_day(date),
            "holiday": holiday.__dict__ if holiday else None,
            "year": date.year,
            "month": date.month,
            "day": date.day,
        }


def _ordinal(number: int) -> str:
    """Return the ordinal string for a number (e.g. 1st, 2nd, 3rd).

    Args:
        number: Positive integer to convert.

    Returns:
        Ordinal string such as "1st", "12th", "23rd".
    """
    if 10 <= number % 100 <= 20:
        suffix = "th"
    elif number % 10 == 1:
        suffix = "st"
    elif number % 10 == 2:
        suffix = "nd"
    elif number % 10 == 3:
        suffix = "rd"
    else:
        suffix = "th"
    return f"{number}{suffix}"
