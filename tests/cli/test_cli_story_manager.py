"""Tests for `StoryCLIManager` helpers that are safe to run in unit tests.

Focuses on `_display_story_info` by creating a temporary story file and
verifying the method reads and prints file metadata without raising.
 
"""

from tests.test_helpers import setup_test_environment, import_module

setup_test_environment()

cli_mod = import_module("src.cli.cli_story_manager")
StoryCLIManager = cli_mod.StoryCLIManager


class _FakeStoryManager:
    """Minimal fake story manager to satisfy constructor requirements."""

    def __init__(self, stories_path: str):
        self.stories_path = stories_path

    def get_story_files(self):
        """Return an empty list of story files (convenience for some tests)."""
        return []

    def get_story_series(self):
        """Return an empty list of story series (convenience for tests)."""
        return []


def test_display_story_info_reads_file(tmp_path):
    """_display_story_info should read and print basic file metadata."""
    # Create a small temporary story file
    story_file = tmp_path / "001_test_story.md"
    content = "# Chapter Title\nFirst line of story\nSecond line\n"
    story_file.write_text(content, encoding="utf-8")

    fake_manager = _FakeStoryManager(str(tmp_path))

    # Subclass StoryCLIManager to expose a public wrapper for the protected
    # _display_story_info method so tests can exercise behavior without
    # triggering protected-access lint warnings.
    class _TestableStoryCLIManager(StoryCLIManager):
        def display_story_info_public(self, story_path: str, display_name: str):
            """Public wrapper that delegates to the protected display helper."""
            return self._display_story_info(story_path, display_name)

        def noop(self):
            """Small public helper to satisfy pylint too-few-public-methods."""
            return True

    cli = _TestableStoryCLIManager(fake_manager, str(tmp_path))
    cli.display_story_info_public(str(story_file), "001_test_story.md")
