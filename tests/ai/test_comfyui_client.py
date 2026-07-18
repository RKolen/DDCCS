"""Tests for the ComfyUI HTTP workflow client (comfyui_client).

All tests mock ``requests`` so they run without a live ComfyUI server.
"""

from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

import requests

from tests import test_helpers

ComfyUIClient = test_helpers.safe_from_import(
    "src.ai.comfyui_client", "ComfyUIClient"
)


def _resp(
    status: int = 200,
    json_data: Optional[Dict[str, Any]] = None,
    content: bytes = b"",
) -> MagicMock:
    """Build a fake ``requests`` response object."""
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = json_data if json_data is not None else {}
    resp.content = content
    resp.raise_for_status.return_value = None
    return resp


def _make_client() -> Any:
    """Return a client pointed at a stable fake base URL."""
    return ComfyUIClient("http://localhost:8188/", timeout=5.0)


def test_is_available_true_on_200() -> None:
    """is_available returns True when the stats probe returns 200."""
    print("\n[TEST] ComfyUIClient.is_available - reachable")
    client = _make_client()
    with patch("src.ai.comfyui_client.requests.get", return_value=_resp(200)):
        assert client.is_available() is True
    print("  [OK] True when /system_stats returns 200")


def test_is_available_false_on_error() -> None:
    """is_available returns False when the probe raises."""
    print("\n[TEST] ComfyUIClient.is_available - unreachable")
    client = _make_client()
    with patch(
        "src.ai.comfyui_client.requests.get",
        side_effect=requests.RequestException("down"),
    ):
        assert client.is_available() is False
    print("  [OK] False when the request raises")


def test_free_returns_true_on_200() -> None:
    """free posts to /free and returns True on success."""
    print("\n[TEST] ComfyUIClient.free - success")
    client = _make_client()
    with patch(
        "src.ai.comfyui_client.requests.post", return_value=_resp(200)
    ) as post:
        assert client.free() is True
        assert post.call_args.args[0] == "http://localhost:8188/free"
    print("  [OK] Posts to /free and reports success")


def test_free_returns_false_on_error() -> None:
    """free returns False when ComfyUI is unreachable."""
    print("\n[TEST] ComfyUIClient.free - failure")
    client = _make_client()
    with patch(
        "src.ai.comfyui_client.requests.post",
        side_effect=requests.RequestException("down"),
    ):
        assert client.free() is False
    print("  [OK] False when the free request raises")


def test_upload_image_returns_stored_name() -> None:
    """upload_image returns the filename ComfyUI reports."""
    print("\n[TEST] ComfyUIClient.upload_image - stored name")
    client = _make_client()
    with patch(
        "src.ai.comfyui_client.requests.post",
        return_value=_resp(200, {"name": "ref.png"}),
    ):
        assert client.upload_image("ref.png", b"bytes") == "ref.png"
    print("  [OK] Returns the reported stored filename")


def test_generate_happy_path_returns_png_bytes() -> None:
    """generate queues, polls history, and fetches the output image bytes."""
    print("\n[TEST] ComfyUIClient.generate - happy path")
    client = _make_client()
    history = {
        "abc": {
            "outputs": {
                "9": {
                    "images": [
                        {
                            "filename": "portrait_0001.png",
                            "subfolder": "",
                            "type": "output",
                        }
                    ]
                }
            }
        }
    }
    with patch(
        "src.ai.comfyui_client.requests.post",
        return_value=_resp(200, {"prompt_id": "abc"}),
    ), patch(
        "src.ai.comfyui_client.requests.get",
        side_effect=[_resp(200, history), _resp(200, content=b"PNGDATA")],
    ):
        result = client.generate({"1": {"class_type": "x", "inputs": {}}})

    assert result == b"PNGDATA"
    print("  [OK] Returns PNG bytes from the output node")


def test_generate_returns_none_when_queue_fails() -> None:
    """generate returns None when the workflow cannot be queued."""
    print("\n[TEST] ComfyUIClient.generate - queue failure")
    client = _make_client()
    with patch(
        "src.ai.comfyui_client.requests.post",
        side_effect=requests.RequestException("no queue"),
    ):
        assert client.generate({"1": {}}) is None
    print("  [OK] None returned when /prompt fails")


def run_all_tests() -> None:
    """Run all ComfyUIClient tests."""
    test_is_available_true_on_200()
    test_is_available_false_on_error()
    test_free_returns_true_on_200()
    test_free_returns_false_on_error()
    test_upload_image_returns_stored_name()
    test_generate_happy_path_returns_png_bytes()
    test_generate_returns_none_when_queue_fails()
    print("\n[PASS] All ComfyUIClient tests passed.")


if __name__ == "__main__":
    run_all_tests()
