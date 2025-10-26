"""Unit tests for `src.dm.dungeon_master.DMConsultant`.

These tests focus on public behaviors and fallback paths. They avoid
heavy integration with character files or NPC agents by using empty
workspace directories and the shared `test_helpers` fakes where needed.
"""

import tempfile

from test_helpers import setup_test_environment, import_module, DM_DUNGEON_MASTER

# Configure test environment and import the DM module via shared helpers
setup_test_environment()
dm_module = DM_DUNGEON_MASTER or import_module("src.dm.dungeon_master")
DMConsultant = dm_module.DMConsultant


def test_generate_narrative_fallback_when_no_ai():
    """When no AI client is provided, DMConsultant should return fallback narrative."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dm = DMConsultant(workspace_path=tmpdir, ai_client=None)

        result = dm.generate_narrative_content(
            "A small tavern brawl breaks out.", characters_present=["Aragorn"],
                npcs_present=["Innkeeper"]
        )

        assert isinstance(result, str)
        assert "The Story Begins" in result
        assert "## The Adventurers" in result
        assert "Aragorn" in result


def test_create_scene_description_via_suggestions():
    """Request narrative suggestions and verify scene-setting content is present."""
    dm = DMConsultant(workspace_path=None, ai_client=None)

    # Request narrative suggestions and verify the scene-setting suggestion
    out = dm.suggest_narrative("A noisy tavern at closing time")
    suggestions = out.get("narrative_suggestions", [])
    assert any("Setting the scene" in s for s in suggestions)
    # The tavern description should mention hearth/warmth in the generated suggestion
    assert any("hearth" in s.lower() or "warm glow" in s.lower() for s in suggestions)


def test_suggest_npc_interaction_not_found():
    """Requesting suggestions for a missing NPC should return an error dict."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dm = DMConsultant(workspace_path=tmpdir, ai_client=None)
        res = dm.suggest_npc_interaction("Nonexistent NPC", "gives a warning")
        assert isinstance(res, dict)
        assert "error" in res


def test_suggest_narrative_structure():
    """suggest_narrative should return expected top-level keys in its result."""
    dm = DMConsultant(workspace_path=None, ai_client=None)
    out = dm.suggest_narrative("Test prompt")
    # Ensure top-level keys exist
    assert set(out.keys()) >= {"user_prompt", "character_insights", "npc_insights",
                               "narrative_suggestions", "consistency_notes"}
