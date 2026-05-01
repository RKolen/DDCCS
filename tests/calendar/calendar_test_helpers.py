"""Shared helpers and imports for calendar tests."""

from typing import Any

from tests import test_helpers

CalendarEngine = test_helpers.safe_from_import(
    "src.calendar.calendar_engine",
    "CalendarEngine",
)
InWorldDate = test_helpers.safe_from_import(
    "src.calendar.calendar_engine",
    "InWorldDate",
)
DateTracker = test_helpers.safe_from_import(
    "src.calendar.date_tracker",
    "DateTracker",
)


def make_date(
    year: int = 1492,
    month: str = "January",
    day: int = 1,
    epoch: str = "",
    calendar_id: str = "generic",
) -> Any:
    """Create an InWorldDate for use in tests.

    Args:
        year: In-world year.
        month: Month name matching the calendar.
        day: Day of month (1-indexed).
        epoch: Epoch abbreviation (e.g. "DR").
        calendar_id: Calendar identifier.

    Returns:
        InWorldDate instance.
    """
    return InWorldDate(
        year=year,
        month=month,
        day=day,
        epoch=epoch,
        calendar_id=calendar_id,
    )
