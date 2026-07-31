"""Tests for the image->prompt vision helper (image_describe).

All tests mock ``requests`` so they run without a live Ollama server.
"""

from unittest.mock import patch

import requests

from tests import test_helpers
from tests.test_helpers import make_fake_response as _resp

fetch_image_bytes = test_helpers.safe_from_import(
    "src.ai.image_describe", "fetch_image_bytes"
)
describe_image = test_helpers.safe_from_import(
    "src.ai.image_describe", "describe_image"
)
condense_to_tags = test_helpers.safe_from_import(
    "src.ai.image_describe", "condense_to_tags"
)

_BASE = "http://ollama.test"
# A stand-in, not the model a deployment runs: the tests assert that whatever
# IMAGE_TO_PROMPT_MODEL names is passed through, so a real name here would be a
# second copy of config that someone would feel obliged to keep in sync.
_MODEL = "test-vision-model"


def test_fetch_image_bytes_returns_content() -> None:
    """A successful GET yields the raw image bytes."""
    print("\n[TEST] fetch_image_bytes - success")
    with patch("src.ai.image_describe.requests.get", return_value=_resp(content=b"PNGDATA")):
        assert fetch_image_bytes("http://x/y.png") == b"PNGDATA"
    print("  [OK] Bytes returned")


def test_fetch_image_bytes_none_on_error() -> None:
    """An unreachable URL yields None, not an exception."""
    print("\n[TEST] fetch_image_bytes - unreachable")
    with patch("src.ai.image_describe.requests.get",
               side_effect=requests.RequestException("down")):
        assert fetch_image_bytes("http://x/y.png") is None
    print("  [OK] None on failure")


def test_describe_image_empty_inputs_return_none() -> None:
    """Missing base URL, model, or bytes short-circuits to None."""
    print("\n[TEST] describe_image - empty inputs")
    assert describe_image("", _MODEL, b"x") is None
    assert describe_image(_BASE, "", b"x") is None
    assert describe_image(_BASE, _MODEL, b"") is None
    print("  [OK] None without required inputs")


def test_describe_image_returns_description() -> None:
    """A successful vision call returns the collapsed response text."""
    print("\n[TEST] describe_image - success")
    with patch("src.ai.image_describe.requests.post",
               return_value=_resp(json_data={"response": "  human ranger,\n weathered  "})):
        assert describe_image(_BASE, _MODEL, b"img") == "human ranger, weathered"
    print("  [OK] Description parsed and whitespace collapsed")


def test_describe_image_leads_with_known_species() -> None:
    """The character's own species leads the tags, not the model's reading.

    A small vision model reports what it thinks it sees - golden hair on a
    scaled head - so the species from the record has to win.
    """
    print("\n[TEST] describe_image - species leads")
    with patch("src.ai.image_describe.requests.post",
               return_value=_resp(json_data={"response": "golden hair, blue robe"})):
        result = describe_image(_BASE, _MODEL, b"img", context="a Gold Dragonborn")
    assert result is not None
    assert result.startswith("gold dragonborn, ")
    print(f"  [OK] {result}")


def test_condense_to_tags_compresses_prose() -> None:
    """Prose collapses to tags that fit one encoder window, species first.

    This is the case that produced a human woman from a gold dragonborn: the
    species survived as one word in ~250 tokens of human-shaped prose.
    """
    print("\n[TEST] condense_to_tags - prose")
    prose = (
        "The character is a Female Gold Dragonborn. Here is a detailed "
        "description of their appearance: - **Skin Tone**: The skin is a rich, "
        "golden hue, reflecting the noble lineage, dragonscaled. - **Face**: "
        "The face is elongated, with a slightly curved snout. The eyes are "
        "piercing and golden, matching the overall colour scheme."
    )
    tags = condense_to_tags(prose, lead="gold dragonborn")
    assert tags.startswith("gold dragonborn, ")
    # The load-bearing anatomy survives, the narration does not.
    assert "slightly curved snout" in tags
    assert "dragonscaled" in tags
    assert "reflecting" not in tags
    assert "matching" not in tags
    assert "detailed description" not in tags
    assert "**" not in tags
    assert len(tags.split()) < len(prose.split()) / 2
    print(f"  [OK] {tags}")


def test_condense_to_tags_is_near_identity_for_tags() -> None:
    """Input that is already tags passes through, with no duplicated lead."""
    print("\n[TEST] condense_to_tags - already tags")
    tags = condense_to_tags(
        "gold dragonborn, curved horns, no hair, full body", lead="gold dragonborn"
    )
    assert tags == "gold dragonborn, curved horns, no hair, full body"
    print(f"  [OK] {tags}")


def test_condense_to_tags_caps_the_prompt() -> None:
    """A runaway answer is capped so the prompt stays inside one window."""
    print("\n[TEST] condense_to_tags - capped")
    tags = condense_to_tags(", ".join(f"tag{i}" for i in range(60)))
    assert tags.count(",") + 1 == 18
    print(f"  [OK] capped to {tags.count(',') + 1} tags")


def test_condense_to_tags_empty_input() -> None:
    """Nothing usable yields an empty string rather than junk."""
    print("\n[TEST] condense_to_tags - empty")
    assert condense_to_tags("") == ""
    assert condense_to_tags("Here is a detailed description of the appearance:") == ""
    print("  [OK] Empty string when there is nothing to keep")


def test_describe_image_none_on_error() -> None:
    """An unreachable Ollama yields None."""
    print("\n[TEST] describe_image - unreachable")
    with patch("src.ai.image_describe.requests.post",
               side_effect=requests.RequestException("down")):
        assert describe_image(_BASE, _MODEL, b"img") is None
    print("  [OK] None when the request raises")


def test_describe_image_none_on_bad_payload() -> None:
    """A response without a string 'response' field yields None."""
    print("\n[TEST] describe_image - bad payload")
    with patch("src.ai.image_describe.requests.post",
               return_value=_resp(json_data={"unexpected": 1})):
        assert describe_image(_BASE, _MODEL, b"img") is None
    print("  [OK] None when the payload lacks a response")


def run_all_tests() -> None:
    """Run all image_describe tests."""
    test_fetch_image_bytes_returns_content()
    test_fetch_image_bytes_none_on_error()
    test_describe_image_empty_inputs_return_none()
    test_describe_image_returns_description()
    test_describe_image_leads_with_known_species()
    test_describe_image_none_on_error()
    test_describe_image_none_on_bad_payload()
    test_condense_to_tags_compresses_prose()
    test_condense_to_tags_is_near_identity_for_tags()
    test_condense_to_tags_caps_the_prompt()
    test_condense_to_tags_empty_input()
    print("\n[PASS] All image_describe tests passed.")


if __name__ == "__main__":
    run_all_tests()
