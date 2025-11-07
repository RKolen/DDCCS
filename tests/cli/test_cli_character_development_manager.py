"""Tests for `CharacterDevelopmentCLIManager` helpers.

Focuses on selection and validation methods that are safe to run in unit tests.
Tests validate series/story selection logic and character action validation.
"""

from tests.test_helpers import setup_test_environment, import_module

setup_test_environment()

cli_mod = import_module("src.cli.cli_character_development_manager")
CharacterDevelopmentCLIManager = cli_mod.CharacterDevelopmentCLIManager


class _FakeStoryManager:
    """Minimal fake story manager to satisfy constructor requirements."""

    def __init__(self, stories_path: str):
        self.stories_path = stories_path

    def get_story_series(self):
        """Return test series list."""
        return ["Campaign1", "Campaign2"]

    def get_story_files_in_series(self, _series_name: str):
        """Return test story files for a series."""
        if _series_name == "Campaign1":
            return ["001_beginning.md", "002_middle.md"]
        if _series_name == "Campaign2":
            return ["001_start.md"]
        return []


def test_validate_action_data_valid():
    """_validate_action_data should return True for valid action data."""
    fake_manager = _FakeStoryManager("")

    class _TestableCDCLIManager(CharacterDevelopmentCLIManager):
        def validate_action_data_public(self, action_data):
            """Public wrapper for testing."""
            return self._validate_action_data(action_data)

        def noop(self):
            """Satisfy too-few-public-methods."""
            return True

    manager = _TestableCDCLIManager(fake_manager, "")

    action_data = {
        "character": "Kael",
        "action": "Cast Fireball",
        "reasoning": "To defeat the dragons",
        "consistency": "Matches aggressive personality",
        "notes": "Character development note",
    }

    assert manager.validate_action_data_public(action_data) is True


def test_validate_action_data_missing_character():
    """_validate_action_data should return False when character is missing."""
    fake_manager = _FakeStoryManager("")

    class _TestableCDCLIManager(CharacterDevelopmentCLIManager):
        def validate_action_data_public(self, action_data):
            """Public wrapper for testing."""
            return self._validate_action_data(action_data)

        def noop(self):
            """Satisfy too-few-public-methods."""
            return True

    manager = _TestableCDCLIManager(fake_manager, "")

    action_data = {
        "character": "",
        "action": "Cast Fireball",
        "reasoning": "To defeat the dragons",
    }

    assert manager.validate_action_data_public(action_data) is False


def test_validate_action_data_missing_action():
    """_validate_action_data should return False when action is missing."""
    fake_manager = _FakeStoryManager("")

    class _TestableCDCLIManager(CharacterDevelopmentCLIManager):
        def validate_action_data_public(self, action_data):
            """Public wrapper for testing."""
            return self._validate_action_data(action_data)

        def noop(self):
            """Satisfy too-few-public-methods."""
            return True

    manager = _TestableCDCLIManager(fake_manager, "")

    action_data = {
        "character": "Kael",
        "action": "",
        "reasoning": "To defeat the dragons",
    }

    assert manager.validate_action_data_public(action_data) is False


def test_validate_action_data_missing_reasoning():
    """_validate_action_data should return False when reasoning is missing."""
    fake_manager = _FakeStoryManager("")

    class _TestableCDCLIManager(CharacterDevelopmentCLIManager):
        def validate_action_data_public(self, action_data):
            """Public wrapper for testing."""
            return self._validate_action_data(action_data)

        def noop(self):
            """Satisfy too-few-public-methods."""
            return True

    manager = _TestableCDCLIManager(fake_manager, "")

    action_data = {
        "character": "Kael",
        "action": "Cast Fireball",
        "reasoning": "",
    }

    assert manager.validate_action_data_public(action_data) is False


def test_select_story_from_series_no_stories():
    """_select_story_from_series should return None when no stories exist."""
    fake_manager = _FakeStoryManager("")

    class _TestableCDCLIManager(CharacterDevelopmentCLIManager):
        def select_story_from_series_public(self, series_name):
            """Public wrapper for testing."""
            return self._select_story_from_series(series_name)

        def noop(self):
            """Satisfy too-few-public-methods."""
            return True

    manager = _TestableCDCLIManager(fake_manager, "")

    # Series with no stories
    result = manager.select_story_from_series_public("NonExistent")
    assert result is None


def test_get_series_and_story_no_series():
    """get_series_and_story should return None when no series exist."""

    class _NoSeriesFakeManager:
        """Fake story manager with no series."""

        def get_story_series(self):
            """Return empty list."""
            return []

        def get_story_files_in_series(self, _series_name: str):
            """Return story files (not used in this test)."""
            return []

    manager = CharacterDevelopmentCLIManager(_NoSeriesFakeManager(), "")
    result = manager.get_series_and_story()
    assert result is None
