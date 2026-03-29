"""Tests for story suggestion types, engine, and storage.

All tests work offline without an AI connection. The engine tests use
a mock AI client to verify prompt construction and JSON parsing. Storage
tests use a temporary directory to avoid touching real campaign data.
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

from src.stories.suggestion_engine import SuggestionConfig, SuggestionEngine
from src.stories.suggestion_storage import (
    clear_old_suggestions,
    get_pending_suggestions,
    get_suggestions_by_type,
    load_suggestions,
    save_suggestions,
    update_suggestion_status,
)
from src.stories.suggestion_types import (
    StorySuggestion,
    SuggestionContext,
    SuggestionPriority,
    SuggestionReview,
    SuggestionSet,
    SuggestionType,
)

project_root = Path(__file__).parent.parent.parent.resolve()
_CAMPAIGN_NAME = "Example_Campaign"


# ---------------------------------------------------------------------------
# StorySuggestion tests
# ---------------------------------------------------------------------------


def test_create_suggestion_defaults():
    """StorySuggestion has expected defaults."""
    suggestion = StorySuggestion(
        suggestion_type=SuggestionType.PLOT_HOOK,
        title="The Ancient Ruin",
        description="Ruins to explore",
        rationale="Provides adventure",
    )

    assert suggestion.suggestion_type == SuggestionType.PLOT_HOOK
    assert suggestion.title == "The Ancient Ruin"
    assert suggestion.priority == SuggestionPriority.MEDIUM
    assert suggestion.review.accepted is None
    assert suggestion.context.relevant_characters == []
    assert suggestion.context.relevant_npcs == []


def test_suggestion_to_dict_round_trips():
    """StorySuggestion serializes and deserializes correctly."""
    original = StorySuggestion(
        suggestion_type=SuggestionType.CHARACTER_MOMENT,
        title="Backstory Reveal",
        description="A moment that reveals the past",
        rationale="Deepens connection",
        priority=SuggestionPriority.HIGH,
        context=SuggestionContext(
            relevant_characters=["Aragorn", "Gandalf"],
            implementation_notes="Do it at the inn",
            suggested_timing="next session",
            created_at=datetime(2026, 3, 1, 12, 0, 0),
        ),
        review=SuggestionReview(
            accepted=True,
            user_notes="Love this idea",
        ),
    )

    data = original.to_dict()
    restored = StorySuggestion.from_dict(data)

    assert restored.suggestion_type == SuggestionType.CHARACTER_MOMENT
    assert restored.title == "Backstory Reveal"
    assert restored.priority == SuggestionPriority.HIGH
    assert restored.context.relevant_characters == ["Aragorn", "Gandalf"]
    assert restored.review.accepted is True
    assert restored.review.user_notes == "Love this idea"
    assert restored.context.suggested_timing == "next session"


def test_suggestion_from_dict_missing_optional_fields():
    """StorySuggestion.from_dict handles missing optional fields gracefully."""
    data = {
        "suggestion_type": "plot_twist",
        "title": "The Betrayal",
        "description": "An ally turns",
        "rationale": "Dramatic tension",
        "created_at": "2026-01-01T00:00:00",
    }

    suggestion = StorySuggestion.from_dict(data)

    assert suggestion.suggestion_type == SuggestionType.PLOT_TWIST
    assert suggestion.priority == SuggestionPriority.MEDIUM
    assert suggestion.context.implementation_notes is None
    assert suggestion.review.accepted is None


def test_suggestion_to_dict_contains_all_keys():
    """StorySuggestion.to_dict returns all expected keys."""
    suggestion = StorySuggestion(
        suggestion_type=SuggestionType.FORESHADOWING,
        title="Ominous Sign",
        description="A dark omen",
        rationale="Sets mood",
    )
    data = suggestion.to_dict()

    expected_keys = {
        "suggestion_type", "title", "description", "rationale", "priority",
        "source_story", "relevant_characters", "relevant_npcs",
        "implementation_notes", "suggested_timing", "created_at",
        "accepted", "user_notes",
    }
    assert expected_keys == set(data.keys())


# ---------------------------------------------------------------------------
# SuggestionSet tests
# ---------------------------------------------------------------------------


def test_empty_suggestion_set():
    """SuggestionSet starts empty."""
    suggestion_set = SuggestionSet(campaign_name="TestCamp", story_file=None)

    assert len(suggestion_set.suggestions) == 0
    assert suggestion_set.campaign_name == "TestCamp"


def test_add_suggestion_increments_count():
    """add_suggestion adds to the list."""
    suggestion_set = SuggestionSet(campaign_name="TestCamp", story_file=None)
    suggestion_set.add_suggestion(
        StorySuggestion(
            suggestion_type=SuggestionType.PLOT_HOOK,
            title="A hook",
            description="Hook desc",
            rationale="Reason",
        )
    )

    assert len(suggestion_set.suggestions) == 1


def test_get_by_type_filters_correctly():
    """get_by_type returns only matching types."""
    suggestion_set = SuggestionSet(campaign_name="TestCamp", story_file=None)

    for stype in [SuggestionType.PLOT_HOOK, SuggestionType.CHARACTER_MOMENT]:
        suggestion_set.add_suggestion(
            StorySuggestion(
                suggestion_type=stype,
                title="Test",
                description="Test",
                rationale="Test",
            )
        )

    hooks = suggestion_set.get_by_type(SuggestionType.PLOT_HOOK)

    assert len(hooks) == 1
    assert hooks[0].suggestion_type == SuggestionType.PLOT_HOOK


def test_get_accepted_returns_accepted_only():
    """get_accepted returns only accepted suggestions."""
    accepted_suggestion = StorySuggestion(
        suggestion_type=SuggestionType.PLOT_HOOK,
        title="Accepted",
        description="Test",
        rationale="Test",
    )
    accepted_suggestion.review.accepted = True

    pending_suggestion = StorySuggestion(
        suggestion_type=SuggestionType.PLOT_HOOK,
        title="Pending",
        description="Test",
        rationale="Test",
    )

    suggestion_set = SuggestionSet(campaign_name="TestCamp", story_file=None)
    suggestion_set.suggestions = [accepted_suggestion, pending_suggestion]

    accepted = suggestion_set.get_accepted()

    assert len(accepted) == 1
    assert accepted[0].title == "Accepted"


def test_get_pending_returns_unreviewed_only():
    """get_pending returns only suggestions with accepted=None."""
    suggestion_set = SuggestionSet(campaign_name="TestCamp", story_file=None)

    for accepted_value in [True, False, None]:
        sugg = StorySuggestion(
            suggestion_type=SuggestionType.NPC_INTERACTION,
            title=f"Status {accepted_value}",
            description="Test",
            rationale="Test",
        )
        sugg.review.accepted = accepted_value
        suggestion_set.suggestions.append(sugg)

    pending = suggestion_set.get_pending()

    assert len(pending) == 1
    assert pending[0].title == "Status None"


def test_suggestion_set_round_trips():
    """SuggestionSet serializes and deserializes with suggestions intact."""
    sugg = StorySuggestion(
        suggestion_type=SuggestionType.PLOT_TWIST,
        title="Twist",
        description="Plot twist",
        rationale="Drama",
        context=SuggestionContext(created_at=datetime(2026, 2, 1, 10, 0, 0)),
    )
    suggestion_set = SuggestionSet(
        campaign_name="TestCamp",
        story_file="001_test.md",
    )
    suggestion_set.add_suggestion(sugg)

    data = suggestion_set.to_dict()
    restored = SuggestionSet.from_dict(data)

    assert restored.campaign_name == "TestCamp"
    assert restored.story_file == "001_test.md"
    assert len(restored.suggestions) == 1
    assert restored.suggestions[0].suggestion_type == SuggestionType.PLOT_TWIST


# ---------------------------------------------------------------------------
# SuggestionEngine tests (no AI required)
# ---------------------------------------------------------------------------


def test_engine_returns_empty_without_ai():
    """SuggestionEngine.generate_suggestions returns [] when ai_client is None."""
    engine = SuggestionEngine(ai_client=None)
    result = engine.generate_suggestions(
        suggestion_type=SuggestionType.PLOT_HOOK,
        story_context="An adventure begins.",
    )

    assert not result


def test_engine_parse_valid_json_array():
    """_parse_suggestions parses a JSON array into StorySuggestion objects."""
    engine = SuggestionEngine(ai_client=None)
    response = json.dumps([
        {
            "title": "The Hidden Passage",
            "description": "A secret door leads to ancient ruins.",
            "rationale": "Provides exploration opportunity.",
            "implementation_notes": "Place in the tavern basement.",
            "suggested_timing": "next session",
        }
    ])

    suggestions = engine.parse_suggestions(response, SuggestionType.PLOT_HOOK)

    assert len(suggestions) == 1
    assert suggestions[0].title == "The Hidden Passage"
    assert suggestions[0].suggestion_type == SuggestionType.PLOT_HOOK
    assert suggestions[0].context.suggested_timing == "next session"


def test_engine_parse_single_json_object():
    """_parse_suggestions wraps a single JSON object in a list."""
    engine = SuggestionEngine(ai_client=None)
    response = json.dumps({
        "title": "Dark Secret",
        "description": "An NPC hides something.",
        "rationale": "Creates mystery.",
    })

    suggestions = engine.parse_suggestions(response, SuggestionType.NPC_INTERACTION)

    assert len(suggestions) == 1
    assert suggestions[0].title == "Dark Secret"


def test_engine_parse_json_with_code_fence():
    """_parse_suggestions strips Markdown code fences before parsing."""
    engine = SuggestionEngine(ai_client=None)
    inner = json.dumps([{"title": "Fenced", "description": "D", "rationale": "R"}])
    response = f"```json\n{inner}\n```"

    suggestions = engine.parse_suggestions(response, SuggestionType.PLOT_TWIST)

    assert len(suggestions) == 1
    assert suggestions[0].title == "Fenced"


def test_engine_falls_back_on_invalid_json():
    """_parse_suggestions falls back to a raw-text suggestion on invalid JSON."""
    engine = SuggestionEngine(ai_client=None)

    suggestions = engine.parse_suggestions("Not valid JSON at all", SuggestionType.PLOT_HOOK)

    assert len(suggestions) == 1
    assert "Not valid JSON" in suggestions[0].description


def test_engine_build_party_context_empty():
    """_build_party_context returns a safe string for an empty profile dict."""
    engine = SuggestionEngine(ai_client=None)
    result = engine.build_party_context({})

    assert "No party" in result


def test_engine_build_party_context_with_profiles():
    """_build_party_context returns a line per character."""
    engine = SuggestionEngine(ai_client=None)
    profiles = {
        "Aragorn": {"dnd_class": "Ranger", "level": 10, "personality_summary": "Brave"},
        "Frodo": {"dnd_class": "Rogue", "level": 5},
    }

    result = engine.build_party_context(profiles)

    assert "Aragorn" in result
    assert "Frodo" in result
    assert "Ranger" in result


def test_engine_build_npc_context_empty():
    """_build_npc_context returns a safe string for an empty NPC list."""
    engine = SuggestionEngine(ai_client=None)
    result = engine.build_npc_context([])

    assert "No NPCs" in result


def test_engine_build_npc_context_with_npcs():
    """_build_npc_context returns a line per NPC."""
    engine = SuggestionEngine(ai_client=None)
    npcs = [
        {"name": "Barliman", "role": "Innkeeper", "location": "Bree", "personality": "Forgetful"},
    ]

    result = engine.build_npc_context(npcs)

    assert "Barliman" in result
    assert "Innkeeper" in result


def test_engine_uses_ai_client_on_generate():
    """SuggestionEngine calls ai_client.chat_completion when AI is available."""
    mock_client = MagicMock()
    mock_client.chat_completion.return_value = json.dumps([
        {"title": "AI Hook", "description": "An AI plot hook.", "rationale": "Reason"}
    ])

    engine = SuggestionEngine(ai_client=mock_client)
    suggestions = engine.generate_suggestions(
        suggestion_type=SuggestionType.PLOT_HOOK,
        story_context="The party rests at the inn.",
        count=1,
    )

    mock_client.chat_completion.assert_called_once()
    assert len(suggestions) == 1
    assert suggestions[0].title == "AI Hook"


def test_engine_returns_empty_on_ai_exception():
    """SuggestionEngine returns [] when ai_client raises an exception."""
    mock_client = MagicMock()
    mock_client.chat_completion.side_effect = RuntimeError("AI down")

    engine = SuggestionEngine(ai_client=mock_client)
    suggestions = engine.generate_suggestions(
        suggestion_type=SuggestionType.PLOT_HOOK,
        story_context="Party rests.",
    )

    assert not suggestions


def test_engine_generate_comprehensive_uses_all_types():
    """generate_comprehensive_suggestions generates for every SuggestionType."""
    mock_client = MagicMock()
    mock_client.chat_completion.return_value = json.dumps([
        {"title": "Hook", "description": "Desc", "rationale": "Reason"}
    ])

    engine = SuggestionEngine(ai_client=mock_client)
    result = engine.generate_comprehensive_suggestions(
        SuggestionConfig(
            campaign_name="TestCamp",
            story_content="Adventure begins.",
            party_profiles={},
            npc_data=[],
            count_per_type=1,
        )
    )

    expected_calls = len(list(SuggestionType))
    assert mock_client.chat_completion.call_count == expected_calls
    assert len(result.suggestions) == expected_calls


# ---------------------------------------------------------------------------
# Suggestion storage tests (use temp directory)
# ---------------------------------------------------------------------------


def _make_campaign_dir(base_tmp: str, campaign_name: str) -> str:
    """Create a mock campaign directory inside a temp folder.

    Args:
        base_tmp: Temporary directory base path.
        campaign_name: Campaign folder name to create.

    Returns:
        Path to the mock workspace root.
    """
    campaigns_dir = os.path.join(base_tmp, "game_data", "campaigns", campaign_name)
    os.makedirs(campaigns_dir, exist_ok=True)
    return base_tmp


def test_load_suggestions_returns_empty_set_when_no_file():
    """load_suggestions returns empty SuggestionSet when no file exists."""
    with tempfile.TemporaryDirectory() as tmp:
        workspace = _make_campaign_dir(tmp, "NewCampaign")
        result = load_suggestions("NewCampaign", workspace)

    assert isinstance(result, SuggestionSet)
    assert len(result.suggestions) == 0


def test_save_and_load_suggestions():
    """save_suggestions persists a SuggestionSet; load_suggestions restores it."""
    with tempfile.TemporaryDirectory() as tmp:
        workspace = _make_campaign_dir(tmp, "SaveTest")
        sugg = StorySuggestion(
            suggestion_type=SuggestionType.PLOT_HOOK,
            title="Saved Hook",
            description="A saved suggestion",
            rationale="Test",
        )
        suggestion_set = SuggestionSet(
            campaign_name="SaveTest",
            story_file=None,
            suggestions=[sugg],
        )

        save_result = save_suggestions(suggestion_set, workspace)
        loaded = load_suggestions("SaveTest", workspace)

    assert save_result is True
    assert len(loaded.suggestions) == 1
    assert loaded.suggestions[0].title == "Saved Hook"


def test_save_suggestions_merges_with_existing():
    """Saving twice accumulates suggestions rather than overwriting."""
    with tempfile.TemporaryDirectory() as tmp:
        workspace = _make_campaign_dir(tmp, "MergeTest")

        for title in ["First", "Second"]:
            suggestion_set = SuggestionSet(
                campaign_name="MergeTest",
                story_file=None,
                suggestions=[
                    StorySuggestion(
                        suggestion_type=SuggestionType.PLOT_TWIST,
                        title=title,
                        description="Desc",
                        rationale="R",
                    )
                ],
            )
            save_suggestions(suggestion_set, workspace)

        loaded = load_suggestions("MergeTest", workspace)

    assert len(loaded.suggestions) == 2


def test_update_suggestion_status_accept():
    """update_suggestion_status marks a suggestion as accepted."""
    with tempfile.TemporaryDirectory() as tmp:
        workspace = _make_campaign_dir(tmp, "AcceptTest")
        sugg = StorySuggestion(
            suggestion_type=SuggestionType.FORESHADOWING,
            title="Foreshadow",
            description="A hint",
            rationale="R",
        )
        suggestion_set = SuggestionSet(
            campaign_name="AcceptTest",
            story_file=None,
            suggestions=[sugg],
        )
        save_suggestions(suggestion_set, workspace)

        result = update_suggestion_status(
            "AcceptTest", 0, accepted=True, user_notes="Great idea", workspace_path=workspace
        )
        loaded = load_suggestions("AcceptTest", workspace)

    assert result is True
    assert loaded.suggestions[0].review.accepted is True
    assert loaded.suggestions[0].review.user_notes == "Great idea"


def test_update_suggestion_status_invalid_index():
    """update_suggestion_status returns False for out-of-range index."""
    with tempfile.TemporaryDirectory() as tmp:
        workspace = _make_campaign_dir(tmp, "BadIdx")
        save_suggestions(
            SuggestionSet(campaign_name="BadIdx", story_file=None), workspace
        )

        result = update_suggestion_status("BadIdx", 99, accepted=True, workspace_path=workspace)

    assert result is False


def test_get_pending_suggestions_filters_correctly():
    """get_pending_suggestions returns only unreviewed suggestions."""
    with tempfile.TemporaryDirectory() as tmp:
        workspace = _make_campaign_dir(tmp, "PendTest")

        suggestions = []
        for idx, accepted_val in enumerate([None, True, None, False]):
            sugg = StorySuggestion(
                suggestion_type=SuggestionType.NARRATIVE_IMPROVEMENT,
                title=f"Sugg {idx}",
                description="Desc",
                rationale="R",
            )
            sugg.review.accepted = accepted_val
            suggestions.append(sugg)

        save_suggestions(
            SuggestionSet(
                campaign_name="PendTest", story_file=None, suggestions=suggestions
            ),
            workspace,
        )

        pending = get_pending_suggestions("PendTest", workspace)

    assert len(pending) == 2


def test_get_suggestions_by_type_filters():
    """get_suggestions_by_type returns only the requested type."""
    with tempfile.TemporaryDirectory() as tmp:
        workspace = _make_campaign_dir(tmp, "TypeFilter")

        suggestions = [
            StorySuggestion(
                suggestion_type=SuggestionType.PLOT_HOOK,
                title="Hook",
                description="D",
                rationale="R",
            ),
            StorySuggestion(
                suggestion_type=SuggestionType.CHARACTER_MOMENT,
                title="Moment",
                description="D",
                rationale="R",
            ),
        ]
        save_suggestions(
            SuggestionSet(
                campaign_name="TypeFilter", story_file=None, suggestions=suggestions
            ),
            workspace,
        )

        hooks = get_suggestions_by_type("TypeFilter", SuggestionType.PLOT_HOOK, workspace)

    assert len(hooks) == 1
    assert hooks[0].title == "Hook"


def test_clear_old_suggestions_removes_stale_pending():
    """clear_old_suggestions removes old pending suggestions but keeps reviewed ones."""
    with tempfile.TemporaryDirectory() as tmp:
        workspace = _make_campaign_dir(tmp, "OldTest")

        old_pending = StorySuggestion(
            suggestion_type=SuggestionType.PLOT_HOOK,
            title="Old Pending",
            description="D",
            rationale="R",
            context=SuggestionContext(created_at=datetime(2020, 1, 1)),
        )
        old_accepted = StorySuggestion(
            suggestion_type=SuggestionType.PLOT_HOOK,
            title="Old Accepted",
            description="D",
            rationale="R",
            context=SuggestionContext(created_at=datetime(2020, 1, 1)),
        )
        old_accepted.review.accepted = True
        new_pending = StorySuggestion(
            suggestion_type=SuggestionType.PLOT_HOOK,
            title="New Pending",
            description="D",
            rationale="R",
        )

        save_suggestions(
            SuggestionSet(
                campaign_name="OldTest",
                story_file=None,
                suggestions=[old_pending, old_accepted, new_pending],
            ),
            workspace,
        )

        removed = clear_old_suggestions("OldTest", days_old=30, workspace_path=workspace)
        remaining = load_suggestions("OldTest", workspace)

    assert removed == 1  # only old_pending removed
    titles = {s.title for s in remaining.suggestions}
    assert "Old Accepted" in titles
    assert "New Pending" in titles
    assert "Old Pending" not in titles
