"""Tests for src/stories/tools/story_search.py.

Uses the Example_Campaign story files under game_data/campaigns/
and temporary workspaces for isolation.
"""

import os
import shutil
import tempfile

from src.utils.path_utils import get_campaigns_dir
from src.stories.tools.story_search import (
    SearchOptions,
    SearchScope,
    SearchType,
    StorySearcher,
)


def _make_workspace_with_story(content: str, series: str = "TestSeries") -> str:
    """Create a temporary workspace with one numbered story file.

    Args:
        content: Story content to write.
        series: Campaign directory name.

    Returns:
        Path to the temporary workspace root.
    """
    tmp = tempfile.mkdtemp()
    series_dir = os.path.join(get_campaigns_dir(tmp), series)
    os.makedirs(series_dir)
    story_path = os.path.join(series_dir, "001_test.md")
    with open(story_path, "w", encoding="utf-8") as fh:
        fh.write(content)
    return tmp


def test_search_text_finds_match():
    """Text search should return results for a word present in the story."""
    tmp = _make_workspace_with_story("Aragorn drew his sword.")
    try:
        searcher = StorySearcher(tmp, campaign_name="TestSeries")
        results = searcher.search("sword", scope=SearchScope.CURRENT_SERIES)
        assert results.total_matches == 1
        assert results.results[0].line_content == "Aragorn drew his sword."
    finally:
        shutil.rmtree(tmp)


def test_search_case_insensitive_by_default():
    """Default search should be case-insensitive."""
    tmp = _make_workspace_with_story("Gandalf raised his Staff.")
    try:
        searcher = StorySearcher(tmp, campaign_name="TestSeries")
        results = searcher.search("staff", scope=SearchScope.CURRENT_SERIES)
        assert results.total_matches == 1
    finally:
        shutil.rmtree(tmp)


def test_search_case_sensitive_no_match():
    """Case-sensitive search should not find differently-cased text."""
    tmp = _make_workspace_with_story("Gandalf raised his Staff.")
    try:
        searcher = StorySearcher(tmp, campaign_name="TestSeries")
        opts = SearchOptions(case_sensitive=True)
        results = searcher.search(
            "staff",
            scope=SearchScope.CURRENT_SERIES,
            options=opts,
        )
        assert results.total_matches == 0
    finally:
        shutil.rmtree(tmp)


def test_search_whole_word_excludes_substrings():
    """Whole-word search should not match substrings."""
    tmp = _make_workspace_with_story("The swordsmith forged a sword.")
    try:
        searcher = StorySearcher(tmp, campaign_name="TestSeries")
        opts = SearchOptions(whole_word=True)
        results = searcher.search(
            "sword",
            scope=SearchScope.CURRENT_SERIES,
            options=opts,
        )
        assert results.total_matches == 1
        assert "sword." in results.results[0].line_content
    finally:
        shutil.rmtree(tmp)


def test_search_character_uses_whole_word():
    """Character search should find the name as a whole word."""
    tmp = _make_workspace_with_story("Frodo Baggins looked worried.")
    try:
        searcher = StorySearcher(tmp, campaign_name="TestSeries")
        results = searcher.search_character("Frodo", scope=SearchScope.CURRENT_SERIES)
        assert results.total_matches == 1
    finally:
        shutil.rmtree(tmp)


def test_search_location_finds_place():
    """Location search should find the location name."""
    tmp = _make_workspace_with_story("They arrived at the Prancing Pony Inn.")
    try:
        searcher = StorySearcher(tmp, campaign_name="TestSeries")
        results = searcher.search_location(
            "Prancing Pony", scope=SearchScope.CURRENT_SERIES
        )
        assert results.total_matches == 1
    finally:
        shutil.rmtree(tmp)


def test_search_by_regex():
    """Regex search should match patterns correctly."""
    tmp = _make_workspace_with_story("Roll 1d6 and roll 2d8 damage.")
    try:
        searcher = StorySearcher(tmp, campaign_name="TestSeries")
        results = searcher.search_by_regex(
            r"\d+d\d+", scope=SearchScope.CURRENT_SERIES
        )
        assert results.total_matches == 2
    finally:
        shutil.rmtree(tmp)


def test_find_dialogue_by_character():
    """Dialogue search should find quoted speech near character name."""
    tmp = _make_workspace_with_story(
        'Aragorn said "We must move quickly." and prepared.'
    )
    try:
        searcher = StorySearcher(tmp, campaign_name="TestSeries")
        results = searcher.find_dialogue_by_character(
            "Aragorn", scope=SearchScope.CURRENT_SERIES
        )
        assert results.total_matches == 1
    finally:
        shutil.rmtree(tmp)


def test_search_no_match_returns_empty():
    """Search with no matches should return an empty results collection."""
    tmp = _make_workspace_with_story("A peaceful meadow.")
    try:
        searcher = StorySearcher(tmp, campaign_name="TestSeries")
        results = searcher.search("dragon", scope=SearchScope.CURRENT_SERIES)
        assert results.total_matches == 0
        assert not results.results
    finally:
        shutil.rmtree(tmp)


def test_search_all_campaigns_traverses_multiple():
    """ALL_CAMPAIGNS scope should search across multiple campaign directories."""
    tmp = tempfile.mkdtemp()
    try:
        for campaign in ("Alpha", "Beta"):
            series_dir = os.path.join(get_campaigns_dir(tmp), campaign)
            os.makedirs(series_dir)
            with open(
                os.path.join(series_dir, "001_story.md"), "w", encoding="utf-8"
            ) as fh:
                fh.write(f"The hero of {campaign} rode forth.")
        searcher = StorySearcher(tmp)
        results = searcher.search("hero", scope=SearchScope.ALL_CAMPAIGNS)
        assert results.total_matches == 2
        assert results.files_searched == 2
    finally:
        shutil.rmtree(tmp)


def test_group_by_file_groups_correctly():
    """group_by_file should group search results by their file path."""
    tmp = tempfile.mkdtemp()
    try:
        series_dir = os.path.join(get_campaigns_dir(tmp), "Camp")
        os.makedirs(series_dir)
        for num, text in [("001", "The sword shone."), ("002", "A new sword appears.")]:
            with open(
                os.path.join(series_dir, f"{num}_story.md"), "w", encoding="utf-8"
            ) as fh:
                fh.write(text)
        searcher = StorySearcher(tmp, campaign_name="Camp")
        results = searcher.search("sword", scope=SearchScope.CURRENT_SERIES)
        grouped = results.group_by_file()
        assert len(grouped) == 2
        assert all(len(v) == 1 for v in grouped.values())
    finally:
        shutil.rmtree(tmp)


def test_search_result_has_match_span():
    """SearchResult should expose match_span as a (start, end) tuple."""
    tmp = _make_workspace_with_story("Aragorn stood tall.")
    try:
        searcher = StorySearcher(tmp, campaign_name="TestSeries")
        results = searcher.search("Aragorn", scope=SearchScope.CURRENT_SERIES)
        assert results.total_matches == 1
        span = results.results[0].match_span
        assert isinstance(span, tuple)
        assert span[0] == 0
        assert span[1] == 7
    finally:
        shutil.rmtree(tmp)


def test_search_example_campaign_exists():
    """Smoke test: searching the real Example_Campaign should not raise."""
    workspace = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..")
    )
    searcher = StorySearcher(workspace, campaign_name="Example_Campaign")
    results = searcher.search("Aragorn", scope=SearchScope.CURRENT_SERIES)
    assert isinstance(results.total_matches, int)


def test_search_type_character_smoke():
    """SearchType.CHARACTER passed explicitly should still work."""
    tmp = _make_workspace_with_story("Gandalf the Grey arrived.")
    try:
        searcher = StorySearcher(tmp, campaign_name="TestSeries")
        results = searcher.search(
            "Gandalf",
            search_type=SearchType.CHARACTER,
            scope=SearchScope.CURRENT_SERIES,
        )
        assert results.total_matches >= 1
    finally:
        shutil.rmtree(tmp)
