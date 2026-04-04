"""Tests for src/stories/tools/story_statistics.py.

Uses temporary workspaces and the real Example_Campaign data.
"""

import os
import shutil
import tempfile

from src.utils.path_utils import get_campaigns_dir
from src.stories.tools.story_statistics import SeriesMetrics, StoryMetrics, StoryStatistics


def _write_story(directory: str, filename: str, content: str) -> str:
    """Write a story file and return its path.

    Args:
        directory: Directory to write in.
        filename: File name.
        content: Story content.

    Returns:
        Absolute path to the written file.
    """
    path = os.path.join(directory, filename)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return path


def _make_series(content_map: dict[str, str]) -> tuple[str, str]:
    """Create a temporary workspace with a series of story files.

    Args:
        content_map: Mapping of filename to story content.

    Returns:
        Tuple of (workspace_path, series_name).
    """
    tmp = tempfile.mkdtemp()
    series_name = "TestSeries"
    series_dir = os.path.join(get_campaigns_dir(tmp), series_name)
    os.makedirs(series_dir)
    for filename, content in content_map.items():
        _write_story(series_dir, filename, content)
    return tmp, series_name


def _assert_story_metrics(metrics: StoryMetrics) -> None:
    """Assert that a StoryMetrics object has the expected nested structure.

    Args:
        metrics: StoryMetrics to check.
    """
    assert hasattr(metrics, "counts")
    assert hasattr(metrics, "breakdown")
    assert hasattr(metrics.counts, "word_count")
    assert hasattr(metrics.counts, "reading_time_minutes")


def _assert_series_metrics(metrics: SeriesMetrics) -> None:
    """Assert that a SeriesMetrics object has the expected nested structure.

    Args:
        metrics: SeriesMetrics to check.
    """
    assert hasattr(metrics, "summary")
    assert hasattr(metrics.summary, "total_stories")
    assert hasattr(metrics.summary, "total_word_count")


def test_word_count_basic():
    """Word count should equal the number of whitespace-separated tokens."""
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_story(tmp, "story.md", "One two three four five.")
        stats = StoryStatistics(tmp)
        metrics = stats.calculate_story_metrics(path)
        assert metrics.counts.word_count == 5


def test_empty_file_metrics():
    """An empty file should return zero word count and not crash."""
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_story(tmp, "story.md", "")
        stats = StoryStatistics(tmp)
        metrics = stats.calculate_story_metrics(path)
        assert metrics.counts.word_count == 0
        assert metrics.counts.reading_time_minutes == 0.0


def test_reading_time_proportional_to_word_count():
    """Reading time should increase with word count (200 wpm base)."""
    words = " ".join(["word"] * 400)
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_story(tmp, "story.md", words)
        stats = StoryStatistics(tmp)
        metrics = stats.calculate_story_metrics(path)
        assert metrics.counts.reading_time_minutes == 2.0


def test_character_appearances_tracked():
    """Characters mentioned by name should appear in character_appearances."""
    content = (
        "Aragorn raised his sword. Frodo trembled. "
        "Aragorn spoke to Frodo about courage."
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_story(tmp, "story.md", content)
        stats = StoryStatistics(tmp)
        metrics = stats.calculate_story_metrics(path, ["Aragorn", "Frodo"])
        assert "Aragorn" in metrics.character_appearances
        assert "Frodo" in metrics.character_appearances
        assert metrics.character_appearances["Aragorn"].mention_count == 3
        assert metrics.character_appearances["Frodo"].mention_count == 2


def test_character_not_present_excluded():
    """Characters not in the text should not appear in character_appearances."""
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_story(tmp, "story.md", "The forest was dark.")
        stats = StoryStatistics(tmp)
        metrics = stats.calculate_story_metrics(path, ["Gandalf"])
        assert "Gandalf" not in metrics.character_appearances


def test_dialogue_percentage_nonzero_for_quoted_text():
    """Dialogue percentage should be positive when story contains quoted speech."""
    content = 'Gandalf said "You shall not pass!" and stood firm.\nThe bridge held.'
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_story(tmp, "story.md", content)
        stats = StoryStatistics(tmp)
        metrics = stats.calculate_story_metrics(path)
        assert metrics.breakdown.dialogue_percentage > 0.0


def test_series_metrics_aggregates_stories():
    """Series metrics total_word_count should equal sum of story word counts."""
    workspace, series_name = _make_series(
        {
            "001_first.md": "alpha beta gamma",
            "002_second.md": "delta epsilon",
        }
    )
    try:
        stats = StoryStatistics(workspace)
        series_m = stats.calculate_series_metrics(series_name)
        assert series_m.summary.total_stories == 2
        assert series_m.summary.total_word_count == 5
        assert series_m.summary.average_story_length == 2.5
    finally:
        shutil.rmtree(workspace)


def test_series_metrics_empty_series():
    """Empty campaign directory should produce zero totals."""
    with tempfile.TemporaryDirectory() as tmp:
        stats = StoryStatistics(tmp)
        series_m = stats.calculate_series_metrics("NonExistentSeries")
        assert series_m.summary.total_stories == 0
        assert series_m.summary.total_word_count == 0


def test_character_appearance_timeline_returns_one_entry_per_story():
    """Timeline should have one entry per story in the series."""
    workspace, series_name = _make_series(
        {
            "001_a.md": "Aragorn walked the path.",
            "002_b.md": "The valley was quiet.",
        }
    )
    try:
        stats = StoryStatistics(workspace)
        timeline = stats.get_character_appearance_timeline("Aragorn", series_name)
        assert len(timeline) == 2
        assert timeline[0]["mention_count"] == 1
        assert timeline[1]["mention_count"] == 0
    finally:
        shutil.rmtree(workspace)


def test_readability_score_returns_expected_keys():
    """Readability score should return flesch_reading_ease and flesch_kincaid_grade."""
    content = "The brave knight rode across the dark forest at dawn."
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_story(tmp, "story.md", content)
        stats = StoryStatistics(tmp)
        scores = stats.calculate_readability_score(path)
        assert "flesch_reading_ease" in scores
        assert "flesch_kincaid_grade" in scores
        assert isinstance(scores["flesch_reading_ease"], float)


def test_generate_statistics_report_markdown():
    """Report in markdown format should start with a level-2 heading."""
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_story(tmp, "001_story.md", "Short story with words.")
        stats = StoryStatistics(tmp)
        metrics = stats.calculate_story_metrics(path)
        report = stats.generate_statistics_report(metrics, output_format="markdown")
        assert report.startswith("## Story Statistics")


def test_generate_statistics_report_text():
    """Report in text format should not contain markdown headers."""
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_story(tmp, "001_story.md", "A simple narrative passage.")
        stats = StoryStatistics(tmp)
        metrics = stats.calculate_story_metrics(path)
        report = stats.generate_statistics_report(metrics, output_format="text")
        assert not report.startswith("##")
        assert "Words:" in report


def test_story_metrics_structure():
    """StoryMetrics should have counts and breakdown nested dataclasses."""
    with tempfile.TemporaryDirectory() as tmp:
        path = _write_story(tmp, "story.md", "A sentence here.")
        stats = StoryStatistics(tmp)
        metrics = stats.calculate_story_metrics(path)
        _assert_story_metrics(metrics)


def test_series_metrics_structure():
    """SeriesMetrics should have a summary nested dataclass."""
    workspace, series_name = _make_series({"001_story.md": "Words here."})
    try:
        stats = StoryStatistics(workspace)
        series_m = stats.calculate_series_metrics(series_name)
        _assert_series_metrics(series_m)
    finally:
        shutil.rmtree(workspace)


def test_example_campaign_smoke_test():
    """Calculating metrics for the real Example_Campaign should not raise."""
    workspace = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    )
    example_story = os.path.join(
        workspace, "game_data", "campaigns", "Example_Campaign", "001_start.md"
    )
    if not os.path.isfile(example_story):
        return
    stats = StoryStatistics(workspace)
    metrics = stats.calculate_story_metrics(example_story, ["Aragorn", "Frodo"])
    assert metrics.counts.word_count > 0
