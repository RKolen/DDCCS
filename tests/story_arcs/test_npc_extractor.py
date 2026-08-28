"""Unit tests for src.story_arcs.npc_extractor."""

import json
from typing import Any, List

from tests.ai_fixtures import ScriptedAIClient
from tests.test_helpers import setup_test_environment, import_module


setup_test_environment()

adt = import_module("src.story_arcs.arc_draft_types")
ne = import_module("src.story_arcs.npc_extractor")

SessionRecap = adt.SessionRecap
ArcRoster = adt.ArcRoster
MAX_DISCOVERED_NPCS = adt.MAX_DISCOVERED_NPCS
build_npc_prompt = ne.build_npc_prompt
parse_npcs = ne.parse_npcs
extract_npcs = ne.extract_npcs

PARTY = ["Aragorn", "Frodo Baggins"]
KNOWN = ["Barliman Butterbur"]

RECAPS = [
    SessionRecap(story_number=1, summary="Barliman Butterbur served them at the Pony."),
    SessionRecap(story_number=2, summary="A ranger named Strider watched from the corner."),
]


def _response(*npcs: Any) -> str:
    """Wrap NPC entries in the JSON envelope the parser expects.

    Args:
        *npcs: NPC entries, as dictionaries or bare strings.

    Returns:
        A JSON response string.
    """
    return json.dumps({"npcs": list(npcs)})


def test_prompt_lists_sessions_and_excludes_the_party() -> None:
    """The prompt carries the recaps and names the PCs to keep them out."""
    prompt = build_npc_prompt("Example Campaign", RECAPS, PARTY)
    assert "Session 1:" in prompt
    assert "Barliman Butterbur served them" in prompt
    assert "never list these" in prompt
    assert "Aragorn" in prompt


def test_prompt_omits_party_line_when_there_is_no_party() -> None:
    """With no PCs on record the prompt does not offer an empty exclusion."""
    assert "never list these" not in build_npc_prompt("Example Campaign", RECAPS, [])


def test_parse_marks_known_and_unknown_names() -> None:
    """A name already on record is known; one that is not is offered new."""
    raw = _response(
        {"name": "Barliman Butterbur", "role": "Innkeeper at the Pony"},
        {"name": "Bill Ferny", "role": "Sold a pony at a bad price"},
    )
    out = parse_npcs(raw, KNOWN)
    assert [n.name for n in out] == ["Barliman Butterbur", "Bill Ferny"]
    assert out[0].known is True
    assert out[1].known is False
    assert out[1].role == "Sold a pony at a bad price"


def test_parse_matches_known_names_case_insensitively() -> None:
    """Roster matching does not depend on the model's capitalisation."""
    out = parse_npcs(_response({"name": "barliman butterbur"}), KNOWN)
    assert out[0].known is True


def test_parse_accepts_bare_string_entries() -> None:
    """A model that answers with names rather than objects still parses."""
    out = parse_npcs(_response("Bill Ferny"), KNOWN)
    assert out[0].name == "Bill Ferny"
    assert out[0].role == ""


def test_parse_excludes_the_party_whatever_the_model_says() -> None:
    """A PC returned as an NPC is dropped: the prompt alone does not hold."""
    raw = _response({"name": "Aragorn", "role": "Ranger"}, {"name": "Bill Ferny"})
    out = parse_npcs(raw, KNOWN, PARTY)
    assert [n.name for n in out] == ["Bill Ferny"]


def test_parse_excludes_the_party_case_insensitively() -> None:
    """The exclusion does not depend on the model's capitalisation."""
    assert parse_npcs(_response({"name": "aragorn"}), KNOWN, PARTY) == []


def test_extract_passes_the_party_through_as_an_exclusion() -> None:
    """The party reaches the parser, not just the prompt."""
    client = ScriptedAIClient(_response({"name": "Frodo Baggins"}, {"name": "Bill Ferny"}))
    out = extract_npcs(client, "Example Campaign", RECAPS, ArcRoster(PARTY, KNOWN))
    assert [n.name for n in out] == ["Bill Ferny"]


def test_parse_deduplicates_and_drops_nameless_entries() -> None:
    """The same NPC twice is one, and an entry with no name is dropped."""
    raw = _response({"name": "Bill Ferny"}, {"name": "bill ferny"}, {"role": "no name"}, 42)
    out = parse_npcs(raw, KNOWN)
    assert [n.name for n in out] == ["Bill Ferny"]


def test_parse_caps_the_returned_cast() -> None:
    """A model listing every name ever spoken is trimmed to a usable set."""
    many: List[Any] = [{"name": f"Villager {i}"} for i in range(MAX_DISCOVERED_NPCS + 5)]
    assert len(parse_npcs(_response(*many), KNOWN)) == MAX_DISCOVERED_NPCS


def test_parse_rejects_unusable_responses() -> None:
    """Prose, or a payload with no npcs list, yields nothing."""
    assert parse_npcs("no json here", KNOWN) == []
    assert parse_npcs(json.dumps({"npcs": "Bill Ferny"}), KNOWN) == []


def test_extract_returns_none_without_ai_or_recaps() -> None:
    """No client, or nothing played yet, yields no cast and no model call."""
    client = ScriptedAIClient(_response({"name": "Bill Ferny"}))
    assert extract_npcs(None, "Example Campaign", RECAPS, ArcRoster(PARTY, KNOWN)) == []
    assert extract_npcs(client, "Example Campaign", [], ArcRoster(PARTY, KNOWN)) == []
    assert client.call_count() == 0


def test_extract_degrades_when_the_model_fails() -> None:
    """A model error yields an empty cast rather than propagating."""
    client = ScriptedAIClient(error=RuntimeError("model offline"))
    assert extract_npcs(client, "Example Campaign", RECAPS, ArcRoster(PARTY, KNOWN)) == []


def test_extract_returns_the_parsed_cast() -> None:
    """A successful call returns the NPCs the sessions named."""
    client = ScriptedAIClient(_response({"name": "Bill Ferny", "role": "Bree local"}))
    out = extract_npcs(client, "Example Campaign", RECAPS, ArcRoster(PARTY, KNOWN))
    assert [n.name for n in out] == ["Bill Ferny"]
    assert client.call_count() == 1
