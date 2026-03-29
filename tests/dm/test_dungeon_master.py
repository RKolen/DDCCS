"""Unit tests for `src.dm.dungeon_master.DMConsultant`.

These tests focus on public behaviors and fallback paths. They avoid
heavy integration with character files or NPC agents by using empty
workspace directories and the shared `test_helpers` fakes where needed.
"""

import json
import os
import tempfile
from pathlib import Path

from src.ai.rag_system import RAGSystem
from tests.test_helpers import (
    setup_test_environment,
    import_module,
    DM_DUNGEON_MASTER,
    sample_major_npc_data,
)

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


def test_get_available_major_npcs_empty():
    """get_available_major_npcs returns empty list when no major NPCs are loaded."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dm = DMConsultant(workspace_path=tmpdir, ai_client=None)
        result = dm.get_available_major_npcs()
        assert isinstance(result, list)
        assert result == []


def test_major_npc_context_in_npc_context_build():
    """_build_npc_context enriches output for major NPCs with tactics."""
    major_data = sample_major_npc_data(
        name="Arch Villain",
        overrides={
            "notes": "Final boss.",
            "encounter_tactics": ["Opens with Cloudkill", "Targets healers"],
            "legendary_actions": None,
            "lair_actions": None,
            "regional_effects": None,
        },
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        npcs_dir = os.path.join(tmpdir, "game_data", "npcs")
        os.makedirs(npcs_dir)
        npc_path = Path(npcs_dir) / "major_arch_villain.json"
        npc_path.write_text(json.dumps(major_data), encoding="utf-8")

        dm = DMConsultant(workspace_path=tmpdir, ai_client=None)
        context_lines = dm._build_npc_context(["Arch Villain"])  # pylint: disable=protected-access

        assert context_lines, "Context should not be empty for a loaded major NPC"
        combined = "\n".join(context_lines)
        assert "Arch Villain" in combined
        assert "Opens with Cloudkill" in combined


def test_rag_get_major_npc_context_for_prompt():
    """get_major_npc_context_for_prompt returns context when NPC name in prompt."""
    rag = RAGSystem()
    statuses = [
        {
            "name": "Arch Villain",
            "role": "Primary Antagonist",
            "notes": "The final boss of the campaign.",
            "relationships": {},
            "plot_hooks": ["A scout reports the villain has been seen near the capital"],
            "defeat_conditions": ["Destroy the phylactery"],
        }
    ]

    context = rag.get_major_npc_context_for_prompt(
        "The party encounters Arch Villain at the dark tower.", statuses
    )
    assert "Arch Villain" in context
    assert "final boss" in context
    assert "phylactery" in context


def test_rag_get_major_npc_context_no_match():
    """get_major_npc_context_for_prompt returns empty string when no NPC matches."""
    rag = RAGSystem()
    statuses = [
        {
            "name": "Arch Villain",
            "role": "Primary Antagonist",
            "notes": "The final boss.",
            "relationships": {},
            "plot_hooks": [],
            "defeat_conditions": [],
        }
    ]

    context = rag.get_major_npc_context_for_prompt(
        "The party explores a peaceful village market.", statuses
    )
    assert context == ""
