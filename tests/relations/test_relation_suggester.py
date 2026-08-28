"""Unit tests for src.relations.relation_suggester."""

import json
from typing import Any, Dict

from tests.ai_fixtures import ScriptedAIClient
from tests.test_helpers import setup_test_environment, import_module


setup_test_environment()

rt = import_module("src.relations.relation_types")
rs = import_module("src.relations.relation_suggester")

CharacterDigest = rt.CharacterDigest
RelationSuggestion = rt.RelationSuggestion
build_prompt = rs.build_prompt
parse_suggestions = rs.parse_suggestions
merge_suggestions = rs.merge_suggestions
split_into_batches = rs.split_into_batches
suggest_relations_for_subject = rs.suggest_relations_for_subject


ARAGORN = CharacterDigest(
    name="Aragorn",
    summary="Ranger of the North",
    origin="Rivendell",
    hooks=["Heir of Isildur"],
)
FRODO = CharacterDigest(
    name="Frodo Baggins",
    summary="Hobbit",
    origin="the Shire",
    hooks=["Bears the One Ring"],
)
GANDALF = CharacterDigest(name="Gandalf the Grey", summary="Wizard")


def _response(*relations: Dict[str, Any]) -> str:
    """Wrap relation dicts in the response envelope the parser expects.

    Args:
        *relations: Relation dictionaries.

    Returns:
        A JSON response string.
    """
    return json.dumps({"relations": list(relations)})


def test_prompt_names_subject_and_candidates() -> None:
    """The prompt carries the subject and every candidate line."""
    prompt = build_prompt(ARAGORN, [FRODO, GANDALF], "party")
    assert "Subject: Aragorn" in prompt
    assert "Frodo Baggins" in prompt
    assert "Gandalf the Grey" in prompt
    assert "relations" in prompt


def test_prompt_includes_context_for_npc_side() -> None:
    """Arc context reaches the prompt when supplied."""
    prompt = build_prompt(ARAGORN, [GANDALF], "npc", context="A bell rings in Bree.")
    assert "A bell rings in Bree." in prompt


def test_parse_keeps_valid_suggestion() -> None:
    """A well-formed suggestion survives parsing."""
    raw = _response(
        {
            "source": "Aragorn",
            "target": "Frodo Baggins",
            "relation_type": "sworn protector",
            "tier": 1,
            "note": "He guards the Ring-bearer on the road.",
        }
    )
    out = parse_suggestions(raw, "Aragorn", ["Frodo Baggins"])
    assert len(out) == 1
    assert out[0].source == "Aragorn"
    assert out[0].target == "Frodo Baggins"
    assert out[0].tier == 1


def test_parse_drops_invented_characters() -> None:
    """A name that was never offered is dropped rather than stored."""
    raw = _response(
        {"source": "Aragorn", "target": "Tom Bombadil", "tier": 1, "note": "x"}
    )
    assert parse_suggestions(raw, "Aragorn", ["Frodo Baggins"]) == []


def test_parse_drops_self_pair_and_bad_json() -> None:
    """Self-pairs and unparseable responses yield nothing."""
    raw = _response({"source": "Aragorn", "target": "Aragorn", "note": "x"})
    assert parse_suggestions(raw, "Aragorn", ["Frodo Baggins"]) == []
    assert parse_suggestions("not json at all", "Aragorn", ["Frodo Baggins"]) == []


def test_parse_reads_fenced_json() -> None:
    """A fenced code block is unwrapped before decoding."""
    inner = _response(
        {"source": "Aragorn", "target": "Frodo Baggins", "tier": 2, "note": "y"}
    )
    out = parse_suggestions(f"Here you go:\n```json\n{inner}\n```", "Aragorn", ["Frodo Baggins"])
    assert len(out) == 1


def test_parse_normalises_case_to_roster_spelling() -> None:
    """Names are rewritten to the roster's spelling."""
    raw = _response(
        {"source": "aragorn", "target": "frodo baggins", "tier": 3, "note": "z"}
    )
    out = parse_suggestions(raw, "Aragorn", ["Frodo Baggins"])
    assert out[0].source == "Aragorn"
    assert out[0].target == "Frodo Baggins"


def test_parse_defaults_out_of_range_tier() -> None:
    """A tier outside 1-3 falls back to the thematic default."""
    raw = _response(
        {"source": "Aragorn", "target": "Frodo Baggins", "tier": 9, "note": "q"}
    )
    assert parse_suggestions(raw, "Aragorn", ["Frodo Baggins"])[0].tier == 2


def test_merge_collapses_reciprocal_pairs() -> None:
    """The same bond proposed from both ends becomes one relation."""
    forward = RelationSuggestion("Aragorn", "Frodo Baggins", "protector", 2, "short")
    reverse = RelationSuggestion("Frodo Baggins", "Aragorn", "protected", 1, "longer note")
    merged = merge_suggestions([[forward], [reverse]])
    assert len(merged) == 1
    assert merged[0].tier == 1


def test_merge_prefers_longer_note_at_equal_tier() -> None:
    """At the same tier the more detailed suggestion is kept."""
    short = RelationSuggestion("Aragorn", "Frodo Baggins", "a", 2, "short")
    long_note = RelationSuggestion("Frodo Baggins", "Aragorn", "b", 2, "a much longer note")
    merged = merge_suggestions([[short], [long_note]])
    assert merged[0].note == "a much longer note"


def test_split_party_batches_exclude_self() -> None:
    """A party subject is never offered itself as a candidate."""
    batches = split_into_batches([ARAGORN, FRODO], [ARAGORN, FRODO], "party")
    assert len(batches) == 2
    for batch in batches:
        names = [o.name for o in batch["others"]]
        assert batch["subject"].name not in names


def test_split_npc_batches_share_the_pool() -> None:
    """NPC batches offer every subject the same candidates."""
    batches = split_into_batches([ARAGORN, FRODO], [GANDALF], "npc")
    assert len(batches) == 2
    assert all([o.name for o in b["others"]] == ["Gandalf the Grey"] for b in batches)


def test_suggest_returns_empty_without_client() -> None:
    """No AI client means no suggestions, not an error."""
    assert suggest_relations_for_subject(None, ARAGORN, [FRODO]) == []


def test_suggest_uses_the_client_once() -> None:
    """One subject costs exactly one model call."""
    client = ScriptedAIClient(
        _response(
            {
                "source": "Aragorn",
                "target": "Frodo Baggins",
                "relation_type": "sworn protector",
                "tier": 1,
                "note": "He guards the Ring-bearer.",
            }
        )
    )
    out = suggest_relations_for_subject(client, ARAGORN, [FRODO], "party")
    assert client.calls == 1
    assert len(out) == 1


def test_suggest_survives_a_failing_client() -> None:
    """A model error degrades to no suggestions rather than raising."""
    client = ScriptedAIClient(error=RuntimeError("model down"))
    assert suggest_relations_for_subject(client, ARAGORN, [FRODO]) == []
    assert client.call_count() == 1
