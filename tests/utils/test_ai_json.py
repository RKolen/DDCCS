"""Unit tests for src.utils.ai_json."""

import json

from tests.test_helpers import setup_test_environment, import_module


setup_test_environment()

aj = import_module("src.utils.ai_json")
extract_json_object = aj.extract_json_object


def test_reads_a_plain_object() -> None:
    """A bare JSON object decodes."""
    assert extract_json_object('{"a": 1}') == {"a": 1}


def test_reads_a_fenced_object() -> None:
    """A fenced code block is unwrapped first."""
    assert extract_json_object('```json\n{"a": 1}\n```') == {"a": 1}


def test_ignores_prose_around_the_object() -> None:
    """A model that prefaces its answer still parses."""
    assert extract_json_object('Sure:\n{"a": 1}\nHope that helps.') == {"a": 1}


def test_returns_none_for_no_json() -> None:
    """Prose with no object yields nothing."""
    assert extract_json_object("no json at all") is None
    assert extract_json_object("") is None


def test_returns_none_for_a_json_array() -> None:
    """Only an object is accepted; a bare array is not one."""
    assert extract_json_object("[1, 2, 3]") is None


def test_salvages_a_truncated_list() -> None:
    """A response cut off mid-value keeps every complete entry.

    This is the failure that lost a whole cast: the model returned seven NPCs,
    the seventh name was cut in half by the token budget, and a strict parse
    threw away all seven.
    """
    truncated = (
        '{"npcs": [{"name": "Barliman Butterbur", "role": "Innkeeper"}, '
        '{"name": "Bill Ferny", "role": "Sold a pony"}, {"name": "Tobias'
    )
    out = extract_json_object(truncated)
    assert out is not None
    assert [n["name"] for n in out["npcs"]] == ["Barliman Butterbur", "Bill Ferny"]


def test_salvages_a_truncated_trailing_string() -> None:
    """A cut inside a string value still keeps the entries before it."""
    truncated = '{"relations": [{"source": "Aragorn", "target": "Frodo Baggins"}, {"source": "Gan'
    out = extract_json_object(truncated)
    assert out is not None
    assert len(out["relations"]) == 1


def test_salvage_keeps_escaped_quotes_intact() -> None:
    """A quote inside a string must not be read as the end of that string."""
    truncated = '{"npcs": [{"name": "Bill", "role": "Said \\"no\\" twice"}, {"name": "Tob'
    out = extract_json_object(truncated)
    assert out is not None
    assert out["npcs"][0]["role"] == 'Said "no" twice'


def test_returns_none_when_nothing_ever_completed() -> None:
    """A fragment with no finished nested value has nothing to salvage."""
    assert extract_json_object('{"npcs": [{"name": "Barlim') is None


def test_complete_response_is_preferred_over_salvage() -> None:
    """A well-formed response is parsed whole, not trimmed."""
    payload = {"npcs": [{"name": "A"}, {"name": "B"}, {"name": "C"}]}
    out = extract_json_object(json.dumps(payload))
    assert out == payload
