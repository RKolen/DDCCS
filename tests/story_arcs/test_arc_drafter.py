"""Unit tests for src.story_arcs.arc_drafter."""

import json
from typing import Any, Dict

from tests.ai_fixtures import ScriptedAIClient
from tests.test_helpers import setup_test_environment, import_module


setup_test_environment()

adt = import_module("src.story_arcs.arc_draft_types")
ad = import_module("src.story_arcs.arc_drafter")

SessionRecap = adt.SessionRecap
ArcRoster = adt.ArcRoster
build_draft_prompt = ad.build_draft_prompt
parse_draft = ad.parse_draft
draft_arc = ad.draft_arc

PARTY = ["Aragorn", "Frodo Baggins", "Gandalf the Grey"]
NPCS = ["Barliman Butterbur", "Tom Bombadil"]

RECAPS = [
    SessionRecap(story_number=1, summary="The party met at the Prancing Pony in Bree."),
    SessionRecap(story_number=2, summary="They fled Bree with riders on the road behind."),
]


def _response(**fields: Any) -> str:
    """Wrap draft fields in the JSON envelope the parser expects.

    Args:
        **fields: Draft field values.

    Returns:
        A JSON response string.
    """
    payload: Dict[str, Any] = {
        "title": "Shadow Over Bree",
        "premise": "A quiet town turns dangerous as riders close in.",
        "overall_plot": ["The party gathers.", "The road turns hostile."],
        "faction": "The Nine",
        "key_npcs": ["Barliman Butterbur"],
    }
    payload.update(fields)
    return json.dumps(payload)


def test_prompt_carries_sessions_and_roster() -> None:
    """The prompt names the campaign, every session, and the NPC roster."""
    prompt = build_draft_prompt("Example Campaign", RECAPS, NPCS)
    assert "Example Campaign" in prompt
    assert "Session 1:" in prompt
    assert "Prancing Pony" in prompt
    assert "Barliman Butterbur" in prompt


def test_prompt_omits_roster_line_without_npcs() -> None:
    """With no NPCs on record the prompt does not offer an empty list."""
    prompt = build_draft_prompt("Example Campaign", RECAPS, [])
    assert "NPCs on record" not in prompt


def test_parse_reads_a_full_draft() -> None:
    """A well-formed response becomes a populated draft."""
    draft = parse_draft(_response(), PARTY, NPCS)
    assert draft is not None
    assert draft.title == "Shadow Over Bree"
    assert draft.faction == "The Nine"
    assert draft.roster.party == PARTY
    assert draft.roster.npcs == ["Barliman Butterbur"]


def test_prompt_never_asks_for_fluid_planning_fields() -> None:
    """Level range and story count are the DM's to set, not the model's."""
    prompt = build_draft_prompt("Example Campaign", RECAPS, NPCS)
    assert "level_range" not in prompt
    assert "target_stories" not in prompt


def test_parse_joins_act_spine_one_act_per_line() -> None:
    """A list of acts is rendered as newline-separated text."""
    draft = parse_draft(_response(), PARTY, NPCS)
    assert draft is not None
    assert draft.overall_plot == "The party gathers.\nThe road turns hostile."


def test_parse_drops_invented_npcs() -> None:
    """An NPC that was never offered is dropped rather than stored."""
    draft = parse_draft(_response(key_npcs=["Barliman Butterbur", "Saruman"]), PARTY, NPCS)
    assert draft is not None
    assert draft.roster.npcs == ["Barliman Butterbur"]


def test_parse_reads_fenced_json() -> None:
    """A fenced code block is unwrapped before decoding."""
    draft = parse_draft(f"Sure:\n```json\n{_response()}\n```", PARTY, NPCS)
    assert draft is not None
    assert draft.title == "Shadow Over Bree"


def test_parse_rejects_draft_without_title_or_premise() -> None:
    """A draft missing either half is not worth showing."""
    assert parse_draft(_response(title=""), PARTY, NPCS) is None
    assert parse_draft(_response(premise=""), PARTY, NPCS) is None
    assert parse_draft("not json at all", PARTY, NPCS) is None


def test_draft_arc_returns_none_without_ai_or_recaps() -> None:
    """No client, or nothing played yet, yields no draft and no model call."""
    client = ScriptedAIClient(_response())
    assert draft_arc(None, "Example Campaign", RECAPS, ArcRoster(PARTY, NPCS)) is None
    assert draft_arc(client, "Example Campaign", [], ArcRoster(PARTY, NPCS)) is None
    assert client.call_count() == 0


def test_draft_arc_ignores_blank_recaps() -> None:
    """A campaign whose recaps are all blank has nothing to draft from."""
    client = ScriptedAIClient(_response())
    blank = [SessionRecap(story_number=1, summary="  ")]
    assert draft_arc(client, "Example Campaign", blank, ArcRoster(PARTY, NPCS)) is None


def test_draft_arc_degrades_when_the_model_fails() -> None:
    """A model error yields no draft rather than propagating."""
    client = ScriptedAIClient(error=RuntimeError("model offline"))
    assert draft_arc(client, "Example Campaign", RECAPS, ArcRoster(PARTY, NPCS)) is None


def test_draft_arc_returns_the_parsed_draft() -> None:
    """A successful call returns the draft the model described."""
    client = ScriptedAIClient(_response())
    draft = draft_arc(client, "Example Campaign", RECAPS, ArcRoster(PARTY, NPCS))
    assert draft is not None
    assert draft.title == "Shadow Over Bree"
    assert client.call_count() == 1
