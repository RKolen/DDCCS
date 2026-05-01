"""Tests for src/calendar/calendar_engine.py."""

import unittest

from tests.calendar.calendar_test_helpers import CalendarEngine, InWorldDate, make_date


class TestInWorldDate(unittest.TestCase):
    """Tests for InWorldDate dataclass."""

    def test_str_with_epoch(self) -> None:
        """Test string representation includes epoch when present."""
        date = make_date(year=1492, month="March", day=15, epoch="DR")
        self.assertIn("DR", str(date))
        self.assertIn("1492", str(date))

    def test_str_without_epoch(self) -> None:
        """Test string representation without epoch."""
        date = make_date(year=100, month="June", day=1)
        self.assertNotIn("DR", str(date))
        self.assertIn("100", str(date))

    def test_to_dict_roundtrip(self) -> None:
        """Test that to_dict and from_dict are inverses."""
        date = make_date(year=1492, month="March", day=15, epoch="DR", calendar_id="generic")
        restored = InWorldDate.from_dict(date.to_dict())
        self.assertEqual(date.year, restored.year)
        self.assertEqual(date.month, restored.month)
        self.assertEqual(date.day, restored.day)
        self.assertEqual(date.epoch, restored.epoch)
        self.assertEqual(date.calendar_id, restored.calendar_id)


class TestCalendarEngineGeneric(unittest.TestCase):
    """Tests for CalendarEngine loading and month/holiday/weekday with generic calendar."""

    def setUp(self) -> None:
        """Set up CalendarEngine with actual game_data/calendars/."""
        self.engine = CalendarEngine("generic")

    def test_months_loaded(self) -> None:
        """Test that 12 standard months are loaded."""
        self.assertEqual(len(self.engine.list_month_names()), 12)

    def test_known_month_found(self) -> None:
        """Test that a known month can be retrieved."""
        month = self.engine.get_month("March")
        self.assertIsNotNone(month)
        self.assertEqual(month.days, 31)

    def test_unknown_month_returns_none(self) -> None:
        """Test that an unknown month returns None."""
        self.assertIsNone(self.engine.get_month("Flamerule"))

    def test_no_holiday_generic(self) -> None:
        """Test that generic calendar has no holidays."""
        date = make_date(year=1, month="January", day=1)
        self.assertIsNone(self.engine.get_holiday(date))

    def test_weekday_cycles(self) -> None:
        """Test that weekday wraps correctly over 7 days."""
        date = make_date(year=1, month="January", day=1)
        day0 = self.engine.get_week_day(date)
        date7 = make_date(year=1, month="January", day=8)
        day7 = self.engine.get_week_day(date7)
        self.assertEqual(day0, day7)

    def test_date_to_ordinal_and_back(self) -> None:
        """Test that date_to_ordinal and ordinal_to_date are inverses."""
        date = make_date(year=3, month="July", day=4)
        ordinal = self.engine.date_to_ordinal(date)
        restored = self.engine.ordinal_to_date(ordinal, date.calendar_id, date.epoch)
        self.assertEqual(restored.year, date.year)
        self.assertEqual(restored.month, date.month)
        self.assertEqual(restored.day, date.day)

    def test_default_epoch_generic(self) -> None:
        """Test that the generic calendar returns the CE epoch abbreviation."""
        self.assertEqual(self.engine.default_epoch(), "CE")

    def test_unknown_calendar_falls_back_to_generic(self) -> None:
        """Test that an unknown calendar_id falls back to generic."""
        engine = CalendarEngine("nonexistent_calendar_xyz")
        self.assertGreater(len(engine.list_month_names()), 0)

    def test_get_date_context_keys(self) -> None:
        """Test that get_date_context returns all expected keys."""
        date = make_date(year=1, month="June", day=21)
        ctx = self.engine.get_date_context(date)
        for key in ("date", "formatted", "season", "weekday", "holiday", "year", "month", "day"):
            self.assertIn(key, ctx)


class TestCalendarEngineSeasons(unittest.TestCase):
    """Tests for season detection with the generic calendar."""

    def setUp(self) -> None:
        """Set up CalendarEngine."""
        self.engine = CalendarEngine("generic")

    def test_season_spring(self) -> None:
        """Test season detection for a spring date."""
        self.assertEqual(self.engine.get_season(make_date(year=1, month="April", day=15)), "Spring")

    def test_season_summer(self) -> None:
        """Test season detection for a summer date."""
        self.assertEqual(self.engine.get_season(make_date(year=1, month="July", day=15)), "Summer")

    def test_season_autumn(self) -> None:
        """Test season detection for an autumn date."""
        self.assertEqual(
            self.engine.get_season(make_date(year=1, month="October", day=15)), "Autumn"
        )

    def test_season_winter(self) -> None:
        """Test season detection for a winter date."""
        self.assertEqual(
            self.engine.get_season(make_date(year=1, month="January", day=15)), "Winter"
        )

    def test_season_winter_year_boundary(self) -> None:
        """Test that winter is detected on both sides of the year boundary."""
        self.assertEqual(
            self.engine.get_season(make_date(year=1, month="December", day=25)), "Winter"
        )
        self.assertEqual(
            self.engine.get_season(make_date(year=2, month="January", day=5)), "Winter"
        )


class TestCalendarEngineArithmetic(unittest.TestCase):
    """Tests for date arithmetic with the generic calendar."""

    def setUp(self) -> None:
        """Set up CalendarEngine."""
        self.engine = CalendarEngine("generic")

    def test_add_days_within_month(self) -> None:
        """Test adding days that stay within the same month."""
        result = self.engine.add_days(make_date(year=1, month="January", day=1), 9)
        self.assertEqual(result.month, "January")
        self.assertEqual(result.day, 10)

    def test_add_days_cross_month(self) -> None:
        """Test adding days that cross a month boundary."""
        result = self.engine.add_days(make_date(year=1, month="January", day=28), 5)
        self.assertEqual(result.month, "February")
        self.assertEqual(result.day, 2)

    def test_add_days_cross_year(self) -> None:
        """Test adding days that cross a year boundary."""
        result = self.engine.add_days(make_date(year=1, month="December", day=30), 5)
        self.assertEqual(result.year, 2)

    def test_subtract_days(self) -> None:
        """Test subtracting days via negative add_days."""
        result = self.engine.add_days(make_date(year=1, month="February", day=5), -5)
        self.assertEqual(result.month, "January")
        self.assertEqual(result.day, 31)

    def test_days_between(self) -> None:
        """Test days_between for adjacent months."""
        date1 = make_date(year=1, month="January", day=1)
        date2 = make_date(year=1, month="February", day=1)
        self.assertEqual(self.engine.days_between(date1, date2), 31)

    def test_days_between_symmetry(self) -> None:
        """Test that days_between is symmetric."""
        date1 = make_date(year=1, month="March", day=1)
        date2 = make_date(year=1, month="June", day=1)
        self.assertEqual(
            self.engine.days_between(date1, date2),
            self.engine.days_between(date2, date1),
        )


class TestCalendarEngineFormatting(unittest.TestCase):
    """Tests for date formatting with the generic calendar."""

    def setUp(self) -> None:
        """Set up CalendarEngine."""
        self.engine = CalendarEngine("generic")

    def test_format_long(self) -> None:
        """Test long date format."""
        result = self.engine.format_date(make_date(year=1492, month="March", day=15), "long")
        self.assertIn("March", result)
        self.assertIn("1492", result)

    def test_format_short(self) -> None:
        """Test short date format uses 3-char month abbreviation."""
        result = self.engine.format_date(make_date(year=1492, month="March", day=15), "short")
        self.assertIn("Mar", result)
        self.assertNotIn("March", result)

    def test_format_narrative(self) -> None:
        """Test narrative format includes ordinal and season."""
        result = self.engine.format_date(make_date(year=1492, month="April", day=3), "narrative")
        self.assertIn("3rd", result)
        self.assertIn("April", result)


class TestCalendarEngineForgottenRealms(unittest.TestCase):
    """Tests for CalendarEngine with the Forgotten Realms calendar."""

    def setUp(self) -> None:
        """Set up CalendarEngine with the forgotten_realms_dr calendar."""
        self.engine = CalendarEngine("forgotten_realms_dr")

    def test_fr_months_loaded(self) -> None:
        """Test that FR calendar skips Shieldmeet (leap-year-only month)."""
        names = self.engine.list_month_names()
        self.assertNotIn("Shieldmeet", names)
        self.assertIn("Hammer", names)
        self.assertIn("Nightal", names)

    def test_fr_year_length(self) -> None:
        """Test that the FR year is 365 days."""
        date = make_date(year=1, month="Hammer", day=1)
        date_next = self.engine.ordinal_to_date(self.engine.date_to_ordinal(date) + 365)
        self.assertEqual(date_next.year, 2)

    def test_fr_winter_crosses_year(self) -> None:
        """Test that FR winter is detected on both sides of the year boundary."""
        self.assertEqual(
            self.engine.get_season(make_date(year=1492, month="Uktar", day=20)), "Winter"
        )
        self.assertEqual(
            self.engine.get_season(make_date(year=1493, month="Ches", day=5)), "Winter"
        )

    def test_fr_spring_in_ches(self) -> None:
        """Test that late Ches is in Spring (after Ches 15)."""
        self.assertEqual(
            self.engine.get_season(make_date(year=1492, month="Ches", day=20)), "Spring"
        )

    def test_fr_holiday_midwinter(self) -> None:
        """Test that Midwinter day is detected as a holiday."""
        date = make_date(year=1492, month="Midwinter", day=1)
        holiday = self.engine.get_holiday(date)
        self.assertIsNotNone(holiday)
        self.assertEqual(holiday.name, "Midwinter")

    def test_fr_epoch_abbreviation(self) -> None:
        """Test that the FR calendar epoch abbreviation is DR."""
        self.assertEqual(self.engine.default_epoch(), "DR")

    def test_fr_add_days_cross_festival(self) -> None:
        """Test adding days across a festival month."""
        result = self.engine.add_days(make_date(year=1492, month="Hammer", day=30), 2)
        self.assertEqual(result.month, "Alturiak")
        self.assertEqual(result.day, 1)


if __name__ == "__main__":
    unittest.main()
