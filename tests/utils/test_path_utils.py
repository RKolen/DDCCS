"""Tests for path utility functions."""

import os
import tempfile
from src.utils.path_utils import get_party_config_path, get_all_campaign_party_paths


def test_get_party_config_path_requires_campaign():
    """Test that get_party_config_path raises ValueError when campaign_name is empty.

    Party configuration is campaign-specific. Passing an empty string must raise
    ValueError to enforce that a campaign is selected before accessing party data.
    """
    raised = False
    try:
        with tempfile.TemporaryDirectory() as tmp:
            get_party_config_path("", tmp)
    except ValueError:
        raised = True
    assert raised, "Expected ValueError for empty campaign_name"


def test_get_party_config_path_campaign():
    """Test that get_party_config_path returns the correct campaign-specific path.

    Uses a temporary base directory and a sample campaign name to verify that the
    function constructs the path to the current_party.json file inside:
        <workspace>/game_data/campaigns/<campaign_name>/current_party.json
    """
    with tempfile.TemporaryDirectory() as tmp:
        campaign = "My Campaign"
        expected = os.path.join(
            tmp, "game_data", "campaigns", campaign, "current_party.json"
        )
        result = get_party_config_path(campaign, tmp)
        assert result == expected


def test_get_all_campaign_party_paths_empty():
    """Test get_all_campaign_party_paths returns empty list when no party files exist."""
    with tempfile.TemporaryDirectory() as tmp:
        paths = get_all_campaign_party_paths(tmp)
        assert not paths


def test_get_all_campaign_party_paths_with_files():
    """Test get_all_campaign_party_paths discovers party files across campaigns."""
    with tempfile.TemporaryDirectory() as tmp:
        for campaign_name in ["CampaignA", "CampaignB"]:
            party_path = get_party_config_path(campaign_name, tmp)
            os.makedirs(os.path.dirname(party_path), exist_ok=True)
            with open(party_path, "w", encoding="utf-8") as f:
                f.write("{}")

        paths = get_all_campaign_party_paths(tmp)
        assert len(paths) == 2
