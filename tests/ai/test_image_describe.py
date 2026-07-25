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

_BASE = "http://ollama.test"
_MODEL = "qwen2.5vl:3b"


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
    test_describe_image_none_on_error()
    test_describe_image_none_on_bad_payload()
    print("\n[PASS] All image_describe tests passed.")


if __name__ == "__main__":
    run_all_tests()
