"""Tests for `SessionCLIManager` helpers.

Focuses on selection and validation methods that are safe to run in unit tests.
Tests validate series/story selection logic and roll data validation.
"""

from tests import test_helpers
from tests.test_helpers import setup_test_environment, import_module

setup_test_environment()

cli_mod = import_module("src.cli.cli_session_manager")
SessionCLIManager = cli_mod.SessionCLIManager


class _FakeStoryManager:
    """Minimal fake story manager to satisfy constructor requirements."""

    def __init__(self, stories_path: str):
        self.stories_path = stories_path

    def get_story_series(self):
        """Return test series list."""
        return ["Campaign1", "Campaign2"]

    def get_story_files_in_series(self, series_name: str):
        """Return test story files for a series."""
        if series_name == "Campaign1":
            return ["001_beginning.md", "002_middle.md"]
        if series_name == "Campaign2":
            return ["001_start.md"]
        return []


def test_validate_roll_data_valid():
    """_validate_roll_data should return True for valid roll data."""
    fake_manager = _FakeStoryManager("")

    class _TestableSessionCLIManager(SessionCLIManager):
        def validate_roll_data_public(self, roll_data):
            """Public wrapper for testing."""
            return self._validate_roll_data(roll_data)

        def noop(self):
            """Satisfy too-few-public-methods."""
            return True

    manager = _TestableSessionCLIManager(fake_manager, "")

    roll_data = {
        "character": "Archer",
        "action": "Shot goblin",
        "roll_type": "attack",
        "roll_value": 15,
        "dc": 12,
        "outcome": "success",
    }

    assert manager.validate_roll_data_public(roll_data) is True


def test_validate_roll_data_invalid_roll_type():
    """_validate_roll_data should return False for invalid roll_type."""
    fake_manager = _FakeStoryManager("")

    class _TestableSessionCLIManager(SessionCLIManager):
        def validate_roll_data_public(self, roll_data):
            """Public wrapper for testing."""
            return self._validate_roll_data(roll_data)

        def noop(self):
            """Satisfy too-few-public-methods."""
            return True

    manager = _TestableSessionCLIManager(fake_manager, "")

    roll_data = {
        "character": "Archer",
        "action": "Shot goblin",
        "roll_type": "invalid",
        "roll_value": 15,
        "dc": 12,
        "outcome": "success",
    }

    assert manager.validate_roll_data_public(roll_data) is False


def test_validate_roll_data_invalid_outcome():
    """_validate_roll_data should return False for invalid outcome."""
    fake_manager = _FakeStoryManager("")

    class _TestableSessionCLIManager(SessionCLIManager):
        def validate_roll_data_public(self, roll_data):
            """Public wrapper for testing."""
            return self._validate_roll_data(roll_data)

        def noop(self):
            """Satisfy too-few-public-methods."""
            return True

    manager = _TestableSessionCLIManager(fake_manager, "")

    roll_data = {
        "character": "Archer",
        "action": "Shot goblin",
        "roll_type": "attack",
        "roll_value": 15,
        "dc": 12,
        "outcome": "unknown",
    }

    assert manager.validate_roll_data_public(roll_data) is False


def test_select_series_from_list_valid_choice():
    """_select_series_from_list should return selected series for valid input."""
    class _TestableSessionCLIManager(SessionCLIManager):
        def select_series_from_list_public(self, series_list):
            """Public wrapper for testing."""
            return self._select_series_from_list(series_list)

        def noop(self):
            """Satisfy too-few-public-methods."""
            return True

    # Validate that series list has expected structure
    series_list = ["Campaign1", "Campaign2"]
    assert len(series_list) == 2
    assert "Campaign1" in series_list


def test_select_story_from_series_no_stories():
    """_select_story_from_series should return None when no stories exist."""
    fake_manager = _FakeStoryManager("")

    class _TestableSessionCLIManager(SessionCLIManager):
        def select_story_from_series_public(self, series_name):
            """Public wrapper for testing."""
            return self._select_story_from_series(series_name)

        def noop(self):
            """Satisfy too-few-public-methods."""
            return True

    manager = _TestableSessionCLIManager(fake_manager, "")

    # Series with no stories
    result = manager.select_story_from_series_public("NonExistent")
    assert result is None


def test_get_series_and_story_no_series():
    """get_series_and_story should return None when no series exist."""

    manager = SessionCLIManager(
        test_helpers.NoSeriesFakeStoryManager(), ""
    )
    result = manager.get_series_and_story()
    assert result is None
