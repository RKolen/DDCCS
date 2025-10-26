"""Test that `DMConsultant.suggest_narrative` includes character
insights when character consultants are present."""

import test_helpers

from test_helpers import setup_test_environment, DM_DUNGEON_MASTER

setup_test_environment()

# Import DM module (use pre-import if available)
dm_module = DM_DUNGEON_MASTER or test_helpers.import_module("src.dm.dungeon_master")
DMConsultant = dm_module.DMConsultant


def test_suggest_narrative_with_character_insights():
    """When character consultants are present,
    suggest_narrative should include character_insights."""
    dm = DMConsultant(workspace_path=None, ai_client=None)

    # Create a fake consultant that returns a structured reaction dict
    reaction = {
        "suggested_reaction": "Defend the innocent",
        "reasoning": "They have a strong sense of justice",
        "class_expertise": "fighter",
    }

    fake_consultant = test_helpers.FakeConsultant(reaction)

    # Inject into DMConsultant
    dm.character_consultants = {"Aragorn": fake_consultant}

    out = dm.suggest_narrative("A street urchin is being harassed.", characters_present=["Aragorn"])
    assert "Aragorn" in out.get("character_insights", {})
    insights = out["character_insights"]["Aragorn"]
    assert insights["likely_reaction"] == "Defend the innocent"
    assert "reasoning" in insights
