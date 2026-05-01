"""Tests for src/calendar/date_tracker.py."""

import json
import os
import tempfile
import unittest

from tests.calendar.calendar_test_helpers import DateTracker, make_date


def _make_workspace(tmp_dir: str, campaign: str = "Test_Campaign") -> str:
    """Create a minimal workspace structure under tmp_dir.

    Args:
        tmp_dir: Temporary directory root.
        campaign: Campaign subdirectory name.

    Returns:
        Absolute path to the workspace root.
    """
    campaign_dir = os.path.join(tmp_dir, "game_data", "campaigns", campaign)
    calendars_dir = os.path.join(tmp_dir, "game_data", "calendars")
    os.makedirs(campaign_dir, exist_ok=True)
    os.makedirs(calendars_dir, exist_ok=True)

    real_calendars = os.path.join(
        os.path.dirname(__file__), "..", "..", "game_data", "calendars"
    )
    for filename in ("generic.json", "forgotten_realms_dr.json"):
        src = os.path.join(real_calendars, filename)
        dst = os.path.join(calendars_dir, filename)
        if os.path.exists(src):
            with open(src, encoding="utf-8") as fobj:
                data = fobj.read()
            with open(dst, "w", encoding="utf-8") as fobj:
                fobj.write(data)

    return tmp_dir


class TestDateTrackerSetAndGet(unittest.TestCase):
    """Tests for DateTracker set/get operations."""

    def setUp(self) -> None:
        """Create an isolated temp workspace per test."""
        self.tmp = tempfile.mkdtemp()
        _make_workspace(self.tmp, "Test_Campaign")
        self.tracker = DateTracker(
            "Test_Campaign",
            calendar_id="generic",
            workspace_path=self.tmp,
        )

    def test_initial_date_is_none(self) -> None:
        """Test that a fresh tracker has no current date."""
        self.assertIsNone(self.tracker.get_current_date())

    def test_set_and_get_current_date(self) -> None:
        """Test that set_current_date persists and can be retrieved."""
        date = make_date(year=1492, month="March", day=15)
        self.tracker.set_current_date(date)
        result = self.tracker.get_current_date()
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 1492)
        self.assertEqual(result.month, "March")
        self.assertEqual(result.day, 15)

    def test_date_survives_reload(self) -> None:
        """Test that the date is persisted and survives a new DateTracker instance."""
        date = make_date(year=1492, month="June", day=1)
        self.tracker.set_current_date(date)

        reloaded = DateTracker("Test_Campaign", workspace_path=self.tmp)
        result = reloaded.get_current_date()
        self.assertIsNotNone(result)
        self.assertEqual(result.year, 1492)
        self.assertEqual(result.month, "June")


class TestDateTrackerAdvance(unittest.TestCase):
    """Tests for DateTracker.advance_days."""

    def setUp(self) -> None:
        """Create isolated temp workspace and set an initial date."""
        self.tmp = tempfile.mkdtemp()
        _make_workspace(self.tmp, "Test_Campaign")
        self.tracker = DateTracker("Test_Campaign", workspace_path=self.tmp)
        self.tracker.set_current_date(make_date(year=1, month="January", day=1))

    def test_advance_days_forward(self) -> None:
        """Test advancing the date forward."""
        result = self.tracker.advance_days(10)
        self.assertIsNotNone(result)
        self.assertEqual(result.day, 11)

    def test_advance_days_cross_month(self) -> None:
        """Test advancing across a month boundary."""
        result = self.tracker.advance_days(31)
        self.assertIsNotNone(result)
        self.assertEqual(result.month, "February")

    def test_advance_days_negative(self) -> None:
        """Test retreating the date with a negative value."""
        self.tracker.set_current_date(make_date(year=1, month="February", day=5))
        result = self.tracker.advance_days(-5)
        self.assertIsNotNone(result)
        self.assertEqual(result.month, "January")
        self.assertEqual(result.day, 31)

    def test_advance_without_date_returns_none(self) -> None:
        """Test that advance_days returns None when no date is set."""
        empty_dir = os.path.join(self.tmp, "game_data", "campaigns", "Empty_Campaign")
        os.makedirs(empty_dir, exist_ok=True)
        tracker = DateTracker("Empty_Campaign", workspace_path=self.tmp)
        self.assertIsNone(tracker.advance_days(5))


class TestDateTrackerPromptContext(unittest.TestCase):
    """Tests for DateTracker.get_date_context_for_prompt."""

    def setUp(self) -> None:
        """Create isolated temp workspace."""
        self.tmp = tempfile.mkdtemp()
        _make_workspace(self.tmp, "Test_Campaign")
        self.tracker = DateTracker("Test_Campaign", workspace_path=self.tmp)

    def test_no_date_returns_empty_string(self) -> None:
        """Test that prompt context is empty when no date is set."""
        self.assertEqual(self.tracker.get_date_context_for_prompt(), "")

    def test_with_date_returns_non_empty(self) -> None:
        """Test that prompt context is non-empty when a date is set."""
        self.tracker.set_current_date(make_date(year=1, month="April", day=15))
        ctx = self.tracker.get_date_context_for_prompt()
        self.assertTrue(len(ctx) > 0)
        self.assertIn("April", ctx)

    def test_prompt_context_includes_season(self) -> None:
        """Test that the prompt context string includes a season reference."""
        self.tracker.set_current_date(make_date(year=1, month="July", day=15))
        ctx = self.tracker.get_date_context_for_prompt()
        self.assertIn("Season", ctx)


class TestDateTrackerPreservesEvents(unittest.TestCase):
    """Tests that DateTracker does not overwrite existing timeline events."""

    def setUp(self) -> None:
        """Create isolated temp workspace with pre-existing timeline.json."""
        self.tmp = tempfile.mkdtemp()
        _make_workspace(self.tmp, "Test_Campaign")
        self.timeline_path = os.path.join(
            self.tmp, "game_data", "campaigns", "Test_Campaign", "timeline.json"
        )
        existing = {
            "campaign_name": "Test_Campaign",
            "events": [
                {
                    "event_id": "evt_001",
                    "title": "Pre-existing event",
                    "event_type": "combat",
                    "description": "A battle",
                    "in_world_date": None,
                    "real_world_date": None,
                    "location": "",
                    "region": "",
                    "characters_involved": [],
                    "npcs_involved": [],
                    "campaign_name": "Test_Campaign",
                    "story_file": "",
                    "session_id": "",
                    "story_section": "",
                    "linked_events": [],
                    "parent_event": None,
                    "tags": [],
                    "organizations_involved": [],
                    "priority": "normal",
                    "consequences": [],
                    "foreshadowing": [],
                    "extraction_confidence": 0.8,
                    "manually_verified": False,
                }
            ],
        }
        with open(self.timeline_path, "w", encoding="utf-8") as fobj:
            json.dump(existing, fobj, indent=2)

    def test_events_preserved_after_set_date(self) -> None:
        """Test that existing events are preserved when DateTracker saves a date."""
        tracker = DateTracker("Test_Campaign", workspace_path=self.tmp)
        tracker.set_current_date(make_date(year=1492, month="March", day=1))

        with open(self.timeline_path, encoding="utf-8") as fobj:
            data = json.load(fobj)

        self.assertEqual(len(data["events"]), 1)
        self.assertEqual(data["events"][0]["event_id"], "evt_001")
        self.assertIsNotNone(data.get("current_date"))


if __name__ == "__main__":
    unittest.main()
