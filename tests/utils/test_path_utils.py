"""Tests for path utility functions."""

import os
import sys
import tempfile
import test_helpers

# Configure test environment so 'src' package can be imported
test_helpers.setup_test_environment()

try:
    from src.utils.path_utils import get_party_config_path
except ImportError as e:
    print(f"[ERROR] Failed to import required modules: {e}")
    print("[ERROR] Make sure you're running from the tests directory")
    sys.exit(1)


def test_get_party_config_path_global():
    """Test that get_party_config_path returns the global current party JSON path
    when no campaign is specified.

    Uses a temporary directory as the base root and expects the function to return
    "<root>/game_data/current_party/current_party.json". Verifies that when
    campaign_name is None the function falls back to the global current party
    storage location.
    """
    with tempfile.TemporaryDirectory() as tmp:
        # No campaign -> global path under game_data/current_party/current_party.json
        expected = os.path.join(tmp, "game_data", "current_party", "current_party.json")
        result = get_party_config_path(tmp, campaign_name=None)
        assert result == expected


def test_get_party_config_path_campaign():
    """
    Test that get_party_config_path returns the correct file path when a campaign name is provided.

    This test uses a temporary base directory and a sample campaign name to verify that the
    function constructs the path to the "current_party.json" file inside:
        <base_dir>/game_data/campaigns/<campaign_name>/current_party.json

    It asserts that the returned path exactly equals the expected path constructed with
    os.path.join.
    """
    with tempfile.TemporaryDirectory() as tmp:
        campaign = "My Campaign"
        expected = os.path.join(tmp, "game_data", "campaigns", campaign, "current_party.json")
        result = get_party_config_path(tmp, campaign_name=campaign)
        assert result == expected
