"""Integration tests for EnhancedStoryManager.

These tests exercise the manager initialization and a handful of safe, file-
system-driven behaviors that don't require modifying `src/` files. They use a
temporary workspace so no project files are changed.
"""

import os
import sys
import tempfile
# json not required here; kept imports minimal

import test_helpers

# Configure test environment so `src` imports work during test execution.
project_root = test_helpers.setup_test_environment()
try:
    from src.utils.path_utils import (
        get_campaigns_dir,
        get_characters_dir,
        get_party_config_path,
    )
    from src.stories.enhanced_story_manager import EnhancedStoryManager
except ImportError as e:
    print(f"[ERROR] Failed to import required modules: {e}")
    print("[ERROR] Make sure you're running from the tests directory")
    sys.exit(1)


def test_init_creates_directories_and_paths():
    """EnhancedStoryManager should create characters and campaigns folders on init."""
    with tempfile.TemporaryDirectory() as tmp:
        esm = EnhancedStoryManager(tmp)
        assert esm is not None

        # Characters and campaigns dirs must exist
        assert os.path.isdir(get_characters_dir(tmp))
        assert os.path.isdir(get_campaigns_dir(tmp))


def test_party_config_path_default_and_campaign():
    """Party manager path should be global by default and campaign-local when set."""
    with tempfile.TemporaryDirectory() as tmp:
        esm_default = EnhancedStoryManager(tmp)
        expected_default = get_party_config_path(tmp, campaign_name=None)
        assert esm_default.party_manager.party_config_path == expected_default

        campaign = "MyCampaign"
        esm_campaign = EnhancedStoryManager(tmp, campaign_name=campaign)
        expected_campaign = get_party_config_path(tmp, campaign_name=campaign)
        assert esm_campaign.party_manager.party_config_path == expected_campaign


def test_get_story_series_and_files():
    """Create a series folder with numbered story files and verify discovery."""
    with tempfile.TemporaryDirectory() as tmp:
        campaigns_dir = get_campaigns_dir(tmp)
        os.makedirs(campaigns_dir, exist_ok=True)

        series_name = "SeriesA"
        series_path = os.path.join(campaigns_dir, series_name)
        os.makedirs(series_path, exist_ok=True)

        # Create two story files matching the expected naming pattern
        filenames = ["001_intro.md", "002_next.md"]
        for fn in filenames:
            with open(os.path.join(series_path, fn), "w", encoding="utf-8") as fh:
                fh.write(f"# {fn}\n\nStory content for {fn}\n")

        esm = EnhancedStoryManager(tmp)

        series = esm.get_story_series()
        assert series_name in series

        files = esm.get_story_files_in_series(series_name)
        # The manager returns filenames; check that our files are listed
        for fn in filenames:
            assert fn in files
