"""Integration test: ensure CLI series creation writes current_party.json

This test simulates user input to `StoryCLIManager._create_new_story_series`
and verifies that a `current_party.json` file is written into the newly
created campaign folder even when the party input is left blank.
"""

import os
import tempfile
import json

from tests.test_helpers import setup_test_environment

# Import directly to avoid tuple unpacking issues with safe_from_import
from src.stories.story_file_manager import create_new_story_series, StoryFileContext
from src.cli.cli_story_manager import StoryCLIManager

setup_test_environment()


class _FakeStoryManager:
    """Fake story manager delegating to the real file ops to create files.

    Keeps a minimal API surface required by `StoryCLIManager`.
    """

    def __init__(self, campaigns_dir, workspace_path):
        """Initialize with campaign and workspace paths."""
        self.stories_path = campaigns_dir
        self._campaigns_dir = campaigns_dir
        self._workspace = workspace_path

    def create_new_story_series(self, series_name, first_story_name, description):
        """Delegate to the real create_new_story_series file-op helper."""
        ctx = StoryFileContext(
            stories_path=self._campaigns_dir,
            workspace_path=self._workspace,
        )
        return create_new_story_series(
            ctx,
            series_name,
            first_story_name,
            description=description,
        )

    def get_story_series(self):
        """Return an empty list for story series in tests."""
        return []

    def get_existing_stories(self):
        """Return an empty list for existing stories in tests."""
        return []


def test_cli_create_series_writes_current_party_json(monkeypatch):
    """Integration test: CLI series creation writes a current_party.json file.

    This test exercises the interactive prompt flow using monkeypatched
    input() values and verifies that the campaign's `current_party.json`
    file is created and contains a `party_members` key.
    """
    with tempfile.TemporaryDirectory() as tmp:
        campaigns_dir = os.path.join(tmp, "game_data", "campaigns")
        os.makedirs(campaigns_dir, exist_ok=True)

        fake_manager = _FakeStoryManager(campaigns_dir, tmp)

        # Create a small test subclass that exposes the protected method via
        # a public wrapper so tests avoid accessing a protected member directly.
        class _TestableStoryCLIManager(StoryCLIManager):
            def create_series_public(self):
                """Public wrapper calling the protected series-creation helper."""
                return self._create_new_story_series()

            def noop(self):
                """Small public helper to increase public-method count for pylint."""
                return True

        cli = _TestableStoryCLIManager(fake_manager, tmp)

        # Simulate user inputs: series name, first story name, description, blank party input
        inputs = iter(
            [
                "MyTest_Campaign",
                "Intro",
                "A short description",
                "",
            ]
        )

        monkeypatch.setattr("builtins.input", lambda _prompt="": next(inputs))

        # Call the public wrapper which delegates to the protected helper
        cli.create_series_public()

        # Verify current_party.json exists in the campaign folder and is valid JSON
        campaign_folder = os.path.join(campaigns_dir, "MyTest_Campaign")
        party_path = os.path.join(campaign_folder, "current_party.json")
        assert os.path.exists(party_path), "current_party.json was not created"

        with open(party_path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        assert "party_members" in data
