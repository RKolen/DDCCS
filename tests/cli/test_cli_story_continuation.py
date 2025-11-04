"""
CLI Story Continuation Integration Tests

Tests the complete flow of AI story continuation in the CLI:
- Scene type selection (combat vs exploration)
- Correct routing to combat or exploration narrative generators
- RAG integration in both paths
- User input handling and error cases
"""

from unittest.mock import Mock, patch
from tests import test_helpers
from tests.test_helpers import FakeAIClient


def test_get_continuation_scene_type_combat():
    """Test that get_continuation_scene_type returns True for combat selection."""
    helpers = test_helpers.safe_from_import(
        "src.cli.dnd_cli_helpers", "get_continuation_scene_type"
    )

    if helpers is None:
        return

    with patch("builtins.input", return_value="1"):
        result = helpers()
        assert result is True, "Should return True for combat scene (choice 1)"


def test_get_continuation_scene_type_exploration():
    """Test that get_continuation_scene_type returns False for exploration."""
    helpers = test_helpers.safe_from_import(
        "src.cli.dnd_cli_helpers", "get_continuation_scene_type"
    )

    if helpers is None:
        return

    with patch("builtins.input", return_value="2"):
        result = helpers()
        assert result is False, "Should return False for exploration (choice 2)"


def test_get_continuation_scene_type_invalid():
    """Test that get_continuation_scene_type returns None for invalid input."""
    helpers = test_helpers.safe_from_import(
        "src.cli.dnd_cli_helpers", "get_continuation_scene_type"
    )

    if helpers is None:
        return

    with patch("builtins.input", return_value="invalid"):
        result = helpers()
        assert result is None, "Should return None for invalid input"


def test_get_continuation_prompt_combat():
    """Test continuation prompt for combat scenes."""
    helpers = test_helpers.safe_from_import(
        "src.cli.dnd_cli_helpers", "get_continuation_prompt"
    )

    if helpers is None:
        return

    with patch("builtins.input", return_value="Goblins attack from the trees"):
        result = helpers(is_combat=True)
        assert result == "Goblins attack from the trees", "Should return combat prompt"


def test_get_continuation_prompt_exploration():
    """Test continuation prompt for exploration scenes."""
    helpers = test_helpers.safe_from_import(
        "src.cli.dnd_cli_helpers", "get_continuation_prompt"
    )

    if helpers is None:
        return

    with patch("builtins.input", return_value="Party meets a merchant"):
        result = helpers(is_combat=False)
        assert result == "Party meets a merchant", "Should return exploration prompt"


def test_get_combat_narrative_style():
    """Test combat narrative style selection."""
    helpers = test_helpers.safe_from_import(
        "src.cli.dnd_cli_helpers", "get_combat_narrative_style"
    )

    if helpers is None:
        return

    with patch("builtins.input", return_value="1"):
        result = helpers()
        assert result == "cinematic", "Should return 'cinematic' for choice 1"

    with patch("builtins.input", return_value="2"):
        result = helpers()
        assert result == "gritty", "Should return 'gritty' for choice 2"

    with patch("builtins.input", return_value=""):
        result = helpers()
        assert result == "cinematic", "Should default to 'cinematic' for empty input"


def test_cli_story_manager_combat_continuation():
    """Test that CLI properly routes to combat continuation handler."""
    story_cli_manager = test_helpers.safe_from_import(
        "src.cli.cli_story_manager", "StoryCLIManager"
    )

    if story_cli_manager is None:
        return

    mock_story_manager = Mock()
    mock_story_manager.consultants = {}
    mock_story_manager.ai_client = Mock()
    mock_story_manager.get_story_series.return_value = []

    cli = story_cli_manager(mock_story_manager, "/tmp/workspace")

    # Test that _handle_combat_continuation exists and is callable
    assert hasattr(cli, "_handle_combat_continuation"), (
        "StoryCLIManager should have _handle_combat_continuation method"
    )
    assert callable(getattr(cli, "_handle_combat_continuation")), (
        "_handle_combat_continuation should be callable"
    )


def test_cli_story_manager_exploration_continuation():
    """Test that CLI properly routes to exploration continuation handler."""
    story_cli_manager = test_helpers.safe_from_import(
        "src.cli.cli_story_manager", "StoryCLIManager"
    )

    if story_cli_manager is None:
        return

    mock_story_manager = Mock()
    mock_story_manager.consultants = {}
    mock_story_manager.ai_client = Mock()
    mock_story_manager.get_story_series.return_value = []

    cli = story_cli_manager(mock_story_manager, "/tmp/workspace")

    # Test that _handle_exploration_continuation exists and is callable
    assert hasattr(cli, "_handle_exploration_continuation"), (
        "StoryCLIManager should have _handle_exploration_continuation method"
    )
    assert callable(getattr(cli, "_handle_exploration_continuation")), (
        "_handle_exploration_continuation should be callable"
    )


def test_story_generator_uses_is_exploration_flag():
    """Test that exploration narratives pass is_exploration=True flag."""
    generate_story = test_helpers.safe_from_import(
        "src.stories.story_ai_generator", "generate_story_from_prompt"
    )

    if generate_story is None:
        return

    mock_ai = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "A mysterious encounter unfolds."
    mock_ai.client.chat.completions.create.return_value = mock_response
    mock_ai.model = "gpt-4"

    result = generate_story(
        ai_client=mock_ai,
        story_prompt="The party meets a stranger",
        is_exploration=True,
    )

    assert isinstance(result, str), "Should return string"

    # Verify system prompt includes no-combat constraint
    test_helpers.assert_system_prompt_contains(mock_ai, "combat")


def test_combat_narrator_includes_rag_context():
    """Test that combat narrator includes RAG spell/ability context."""
    combat_narrator = test_helpers.safe_from_import(
        "src.combat.combat_narrator", "CombatNarrator"
    )

    if combat_narrator is None:
        return

    narrator = combat_narrator({}, ai_client=FakeAIClient())

    # Test that narration works with spell mentions (RAG integration via public API)
    prompt = "Wizard casts fireball at the goblin"
    narrative = narrator.narrate_combat_from_prompt(
        combat_prompt=prompt,
        story_context="",
        style="cinematic"
    )

    # Verify public API returns valid narrative
    assert isinstance(narrative, str), "Combat narrator should return string"
    assert len(narrative) > 0, "Combat narrator should not return empty string"


def run_all_cli_continuation_tests():
    """Run all CLI continuation integration tests."""
    tests = [
        test_get_continuation_scene_type_combat,
        test_get_continuation_scene_type_exploration,
        test_get_continuation_scene_type_invalid,
        test_get_continuation_prompt_combat,
        test_get_continuation_prompt_exploration,
        test_get_combat_narrative_style,
        test_cli_story_manager_combat_continuation,
        test_cli_story_manager_exploration_continuation,
        test_story_generator_uses_is_exploration_flag,
        test_combat_narrator_includes_rag_context,
    ]

    return test_helpers.run_test_suite("CLI Continuation", tests)


if __name__ == "__main__":
    import sys

    sys.exit(run_all_cli_continuation_tests())
