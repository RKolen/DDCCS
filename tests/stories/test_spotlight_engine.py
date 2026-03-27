"""Tests for spotlight_engine.py SpotlightEngine and display_spotlight_report.

Uses real game_data from Example_Campaign. All tests work offline without
an AI connection.
"""

import os
import tempfile
from pathlib import Path

from src.config.config_types import SpotlightConfig
from src.stories.spotlight_engine import SpotlightEngine, display_spotlight_report
from src.stories.spotlight_types import SpotlightEntry, SpotlightReport

project_root = Path(__file__).parent.parent.parent.resolve()
_CAMPAIGN_NAME = "Example_Campaign"


# ---------------------------------------------------------------------------
# SpotlightEngine.generate_report tests
# ---------------------------------------------------------------------------


def test_generate_report_returns_spotlight_report():
    """generate_report returns a SpotlightReport instance."""
    engine = SpotlightEngine()
    report = engine.generate_report(_CAMPAIGN_NAME, workspace_path=str(project_root))

    assert isinstance(report, SpotlightReport), "Should return SpotlightReport"


def test_generate_report_has_campaign_name():
    """SpotlightReport carries the correct campaign name."""
    engine = SpotlightEngine()
    report = engine.generate_report(_CAMPAIGN_NAME, workspace_path=str(project_root))

    assert report.campaign_name == _CAMPAIGN_NAME


def test_generate_report_has_generated_at():
    """SpotlightReport has a non-empty generated_at timestamp."""
    engine = SpotlightEngine()
    report = engine.generate_report(_CAMPAIGN_NAME, workspace_path=str(project_root))

    assert report.generated_at, "generated_at should not be empty"


def test_generate_report_entries_are_spotlight_entries():
    """All entries in the report are SpotlightEntry instances."""
    engine = SpotlightEngine()
    report = engine.generate_report(_CAMPAIGN_NAME, workspace_path=str(project_root))

    for entry in report.entries:
        assert isinstance(entry, SpotlightEntry), (
            f"Entry {entry} should be SpotlightEntry"
        )


def test_generate_report_entries_have_valid_entity_types():
    """All entries have entity_type of 'character' or 'npc'."""
    engine = SpotlightEngine()
    report = engine.generate_report(_CAMPAIGN_NAME, workspace_path=str(project_root))

    for entry in report.entries:
        assert entry.entity_type in {"character", "npc"}, (
            f"Unexpected entity_type: {entry.entity_type}"
        )


def test_generate_report_entries_scores_within_range():
    """All entry scores are between 0 and 100."""
    engine = SpotlightEngine()
    report = engine.generate_report(_CAMPAIGN_NAME, workspace_path=str(project_root))

    for entry in report.entries:
        assert 0 <= entry.score <= 100, (
            f"{entry.name} has out-of-range score: {entry.score}"
        )


def test_generate_report_entries_sorted_descending():
    """Entries in the report are sorted by score descending."""
    engine = SpotlightEngine()
    report = engine.generate_report(_CAMPAIGN_NAME, workspace_path=str(project_root))

    scores = [e.score for e in report.entries]
    assert scores == sorted(scores, reverse=True), "Entries should be sorted descending"


def test_generate_report_nonexistent_campaign_returns_spotlight_report():
    """A non-existent campaign name returns a valid SpotlightReport without raising."""
    engine = SpotlightEngine()
    report = engine.generate_report(
        "NonExistent_Campaign_XYZ", workspace_path=str(project_root)
    )

    assert isinstance(report, SpotlightReport), "Should return SpotlightReport"
    assert report.campaign_name == "NonExistent_Campaign_XYZ"


# ---------------------------------------------------------------------------
# SpotlightReport.top_characters / top_npcs tests
# ---------------------------------------------------------------------------


def test_top_characters_returns_only_character_entries():
    """top_characters returns only entries with entity_type == 'character'."""
    engine = SpotlightEngine()
    report = engine.generate_report(_CAMPAIGN_NAME, workspace_path=str(project_root))

    top = report.top_characters(10)
    for entry in top:
        assert entry.entity_type == "character"


def test_top_npcs_returns_only_npc_entries():
    """top_npcs returns only entries with entity_type == 'npc'."""
    engine = SpotlightEngine()
    report = engine.generate_report(_CAMPAIGN_NAME, workspace_path=str(project_root))

    top = report.top_npcs(10)
    for entry in top:
        assert entry.entity_type == "npc"


def test_top_characters_respects_n_limit():
    """top_characters(n) returns at most n entries."""
    engine = SpotlightEngine()
    report = engine.generate_report(_CAMPAIGN_NAME, workspace_path=str(project_root))

    for limit in [1, 2, 3]:
        top = report.top_characters(limit)
        assert len(top) <= limit, f"Expected at most {limit} entries"


# ---------------------------------------------------------------------------
# SpotlightEngine.get_prompt_injection tests
# ---------------------------------------------------------------------------


def test_get_prompt_injection_returns_string():
    """get_prompt_injection always returns a string."""
    engine = SpotlightEngine()
    result = engine.get_prompt_injection(
        _CAMPAIGN_NAME, workspace_path=str(project_root)
    )

    assert isinstance(result, str)


def test_get_prompt_injection_contains_header_when_populated():
    """When there are spotlight entries, the injection contains the header line."""
    engine = SpotlightEngine()
    result = engine.get_prompt_injection(
        _CAMPAIGN_NAME, workspace_path=str(project_root)
    )

    if result:
        assert "Narratively important" in result, (
            "Non-empty injection should contain header line"
        )


def test_get_prompt_injection_empty_for_no_signals():
    """get_prompt_injection returns empty string when no signals exist."""
    with tempfile.TemporaryDirectory() as tmp:
        # Create campaign with a story that mentions all characters
        campaigns_dir = os.path.join(tmp, "game_data", "campaigns", "SingleSession")
        os.makedirs(campaigns_dir)
        story_path = os.path.join(campaigns_dir, "001_only.md")
        with open(story_path, "w", encoding="utf-8") as fh:
            fh.write("A story with no known characters or NPCs.\n")

        engine = SpotlightEngine()
        # No character files -> no names -> no signals
        result = engine.get_prompt_injection("SingleSession", workspace_path=tmp)

    assert result == "", "Should return empty string when no signals exist"


# ---------------------------------------------------------------------------
# SpotlightEngine custom weights
# ---------------------------------------------------------------------------


def test_generate_report_custom_weights():
    """Custom weights are reflected in entry scores."""
    engine = SpotlightEngine()
    low_cfg = SpotlightConfig(
        recency_weight=5.0,
        thread_weight=5.0,
        dc_weight=5.0,
        tension_weight=5.0,
    )
    high_cfg = SpotlightConfig(
        recency_weight=30.0,
        thread_weight=30.0,
        dc_weight=30.0,
        tension_weight=30.0,
    )
    report_low = engine.generate_report(
        _CAMPAIGN_NAME, workspace_path=str(project_root), config=low_cfg
    )
    report_high = engine.generate_report(
        _CAMPAIGN_NAME, workspace_path=str(project_root), config=high_cfg
    )

    if report_low.entries and report_high.entries:
        max_low = max(e.score for e in report_low.entries)
        max_high = max(e.score for e in report_high.entries)
        assert max_high >= max_low, "Higher weights should not produce lower scores"


# ---------------------------------------------------------------------------
# display_spotlight_report smoke test
# ---------------------------------------------------------------------------


def test_display_spotlight_report_does_not_raise():
    """display_spotlight_report completes without raising an exception."""
    engine = SpotlightEngine()
    report = engine.generate_report(_CAMPAIGN_NAME, workspace_path=str(project_root))

    # Should not raise
    display_spotlight_report(report)


if __name__ == "__main__":
    test_generate_report_returns_spotlight_report()
    test_generate_report_has_campaign_name()
    test_generate_report_has_generated_at()
    test_generate_report_entries_are_spotlight_entries()
    test_generate_report_entries_have_valid_entity_types()
    test_generate_report_entries_scores_within_range()
    test_generate_report_entries_sorted_descending()
    test_generate_report_nonexistent_campaign_returns_spotlight_report()
    test_top_characters_returns_only_character_entries()
    test_top_npcs_returns_only_npc_entries()
    test_top_characters_respects_n_limit()
    test_get_prompt_injection_returns_string()
    test_get_prompt_injection_contains_header_when_populated()
    test_get_prompt_injection_empty_for_no_signals()
    test_generate_report_custom_weights()
    test_display_spotlight_report_does_not_raise()
    print("\nAll spotlight_engine tests passed.")
