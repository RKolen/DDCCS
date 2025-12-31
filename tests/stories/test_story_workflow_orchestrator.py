"""
Story Workflow Orchestrator Tests

Tests for the story_workflow_orchestrator module which coordinates calling
existing file creation functions (NPC detection, story hooks, character
development, session results) in a unified workflow.
"""

import tempfile
from unittest.mock import Mock

from tests.test_helpers import run_test_suite
from src.stories.story_workflow_orchestrator import (
    coordinate_story_workflow,
    StoryWorkflowContext,
    WorkflowOptions,
)


def test_story_workflow_context_creation():
    """Test that StoryWorkflowContext dataclass initializes correctly."""
    print("\n[TEST] StoryWorkflowContext Creation")

    ctx = StoryWorkflowContext(
        story_name="Test Story",
        story_content="Test content with NPCs",
        series_path="/test/series",
        workspace_path="/test/workspace",
        party_names=["Alice", "Bob"],
    )

    assert ctx.story_name == "Test Story"
    assert ctx.story_content == "Test content with NPCs"
    assert ctx.series_path == "/test/series"
    assert ctx.workspace_path == "/test/workspace"
    assert ctx.party_names == ["Alice", "Bob"]
    assert ctx.ai_client is None
    assert isinstance(ctx.results, dict)
    assert "npcs_created" in ctx.results
    assert "npcs_suggested" in ctx.results
    assert "hooks_file" in ctx.results
    assert "character_dev_file" in ctx.results
    assert "session_file" in ctx.results
    assert "errors" in ctx.results

    print("[PASS] StoryWorkflowContext Creation")


def test_workflow_options_creation():
    """Test that WorkflowOptions dataclass initializes correctly."""
    print("\n[TEST] WorkflowOptions Creation")

    # Test with defaults
    opts_default = WorkflowOptions()
    assert opts_default.create_npc_profiles is True
    assert opts_default.create_hooks_file is True
    assert opts_default.create_character_dev_file is True
    assert opts_default.create_session_file is True
    assert opts_default.ai_client is None

    # Test with custom values
    mock_ai = Mock()
    opts_custom = WorkflowOptions(
        create_npc_profiles=False,
        create_hooks_file=True,
        create_character_dev_file=False,
        create_session_file=True,
        ai_client=mock_ai,
    )
    assert opts_custom.create_npc_profiles is False
    assert opts_custom.create_hooks_file is True
    assert opts_custom.create_character_dev_file is False
    assert opts_custom.create_session_file is True
    assert opts_custom.ai_client is mock_ai

    print("[PASS] WorkflowOptions Creation")


def test_coordinate_story_workflow_minimal():
    """Test workflow orchestration with all features disabled."""
    print("\n[TEST] Coordinate Story Workflow (Minimal)")

    with tempfile.TemporaryDirectory() as tmpdir:
        ctx = StoryWorkflowContext(
            story_name="Test Story",
            story_content="A simple test story",
            series_path=tmpdir,
            workspace_path=tmpdir,
            party_names=["Hero"],
        )

        opts = WorkflowOptions(
            create_npc_profiles=False,
            create_hooks_file=False,
            create_character_dev_file=False,
            create_session_file=False,
            ai_client=None,
        )

        # This should not error even with all features disabled
        results = coordinate_story_workflow(ctx, options=opts)

        assert isinstance(results, dict)
        assert "npcs_created" in results
        assert "npcs_suggested" in results
        assert "hooks_file" in results
        assert "character_dev_file" in results
        assert "session_file" in results
        assert "errors" in results

    print("[PASS] Coordinate Story Workflow (Minimal)")


def test_coordinate_story_workflow_default_options():
    """Test workflow orchestration with default options."""
    print("\n[TEST] Coordinate Story Workflow (Default Options)")

    with tempfile.TemporaryDirectory() as tmpdir:
        ctx = StoryWorkflowContext(
            story_name="Test Story",
            story_content="A test story",
            series_path=tmpdir,
            workspace_path=tmpdir,
            party_names=["Hero"],
        )

        # Call with default options (None)
        results = coordinate_story_workflow(ctx)

        assert isinstance(results, dict)
        assert "npcs_created" in results
        assert isinstance(results["npcs_created"], list)

    print("[PASS] Coordinate Story Workflow (Default Options)")


def test_coordinate_story_workflow_with_mock_ai():
    """Test workflow orchestration with mocked AI client."""
    print("\n[TEST] Coordinate Story Workflow (With Mock AI)")

    with tempfile.TemporaryDirectory() as tmpdir:
        mock_ai = Mock()

        ctx = StoryWorkflowContext(
            story_name="Test Story",
            story_content="A test story",
            series_path=tmpdir,
            workspace_path=tmpdir,
            party_names=["Hero"],
            ai_client=mock_ai,
        )

        opts = WorkflowOptions(
            create_npc_profiles=False,
            create_hooks_file=False,
            create_character_dev_file=False,
            create_session_file=False,
            ai_client=mock_ai,
        )

        # Should work with AI client provided
        results = coordinate_story_workflow(ctx, options=opts)

        assert isinstance(results, dict)

    print("[PASS] Coordinate Story Workflow (With Mock AI)")


def test_context_add_error():
    """Test that StoryWorkflowContext.add_error method works."""
    print("\n[TEST] Context Add Error Method")

    ctx = StoryWorkflowContext(
        story_name="Test",
        story_content="content",
        series_path="/test",
        workspace_path="/test",
        party_names=["Hero"],
    )

    assert len(ctx.results["errors"]) == 0

    ctx.add_error("Test error 1")
    assert len(ctx.results["errors"]) == 1
    assert ctx.results["errors"][0] == "Test error 1"

    ctx.add_error("Test error 2")
    assert len(ctx.results["errors"]) == 2
    assert ctx.results["errors"][1] == "Test error 2"

    print("[PASS] Context Add Error Method")


def test_workflow_results_structure():
    """Test that workflow results have expected structure."""
    print("\n[TEST] Workflow Results Structure")

    with tempfile.TemporaryDirectory() as tmpdir:
        ctx = StoryWorkflowContext(
            story_name="Test Story",
            story_content="Test content",
            series_path=tmpdir,
            workspace_path=tmpdir,
            party_names=["Hero"],
        )

        opts = WorkflowOptions(
            create_npc_profiles=False,
            create_hooks_file=False,
            create_character_dev_file=False,
            create_session_file=False,
        )

        results = coordinate_story_workflow(ctx, options=opts)

        # Verify all expected keys are present
        expected_keys = {
            "npcs_created",
            "npcs_suggested",
            "hooks_file",
            "character_dev_file",
            "session_file",
            "errors",
        }
        assert set(results.keys()) == expected_keys

        # Verify types
        assert isinstance(results["npcs_created"], list)
        assert isinstance(results["npcs_suggested"], list)
        assert results["hooks_file"] is None or isinstance(results["hooks_file"], str)
        assert results["character_dev_file"] is None or isinstance(
            results["character_dev_file"], str
        )
        assert results["session_file"] is None or isinstance(
            results["session_file"], str
        )
        assert isinstance(results["errors"], list)

    print("[PASS] Workflow Results Structure")


def test_coordinate_story_workflow_keyword_only_options():
    """Test that options parameter is keyword-only."""
    print("\n[TEST] Keyword-Only Options Parameter")

    with tempfile.TemporaryDirectory() as tmpdir:
        ctx = StoryWorkflowContext(
            story_name="Test",
            story_content="content",
            series_path=tmpdir,
            workspace_path=tmpdir,
            party_names=["Hero"],
        )

        opts = WorkflowOptions()

        # Should work with keyword argument
        results = coordinate_story_workflow(ctx, options=opts)
        assert isinstance(results, dict)

        # Should work with default (no options arg)
        results2 = coordinate_story_workflow(ctx)
        assert isinstance(results2, dict)

    print("[PASS] Keyword-Only Options Parameter")


def run_all_workflow_orchestrator_tests():
    """Run all workflow orchestrator tests."""
    tests = [
        test_story_workflow_context_creation,
        test_workflow_options_creation,
        test_coordinate_story_workflow_minimal,
        test_coordinate_story_workflow_default_options,
        test_coordinate_story_workflow_with_mock_ai,
        test_context_add_error,
        test_workflow_results_structure,
        test_coordinate_story_workflow_keyword_only_options,
    ]
    return run_test_suite("Story Workflow Orchestrator", tests)


if __name__ == "__main__":
    import sys

    sys.exit(run_all_workflow_orchestrator_tests())
