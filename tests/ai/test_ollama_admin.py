"""Tests for the best-effort Ollama admin helpers (ollama_admin).

All tests mock ``requests`` so they run without a live Ollama server.
"""

from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import requests

from tests import test_helpers

list_loaded_models = test_helpers.safe_from_import(
    "src.ai.ollama_admin", "list_loaded_models"
)
unload_ollama_models = test_helpers.safe_from_import(
    "src.ai.ollama_admin", "unload_ollama_models"
)

# A stand-in base URL; requests are mocked, so this is never contacted. The
# reserved .test domain makes clear it is a fixture, not real configuration.
_BASE = "http://ollama.test"


def _resp(status: int = 200, json_data: Optional[Dict[str, Any]] = None) -> MagicMock:
    """Build a fake ``requests`` response object."""
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = json_data if json_data is not None else {}
    resp.raise_for_status.return_value = None
    return resp


def _ps(names: List[str]) -> Dict[str, Any]:
    """Build a fake ``/api/ps`` payload listing the given model names."""
    return {"models": [{"name": n} for n in names]}


def test_list_loaded_models_empty_base_url_returns_empty() -> None:
    """An empty base URL yields no models and makes no request."""
    print("\n[TEST] list_loaded_models - empty base URL")
    assert list_loaded_models("") == []
    print("  [OK] Empty list without a base URL")


def test_list_loaded_models_returns_names() -> None:
    """Resident model names are parsed from the /api/ps payload."""
    print("\n[TEST] list_loaded_models - two resident models")
    with patch(
        "src.ai.ollama_admin.requests.get",
        return_value=_resp(200, _ps(["llama3", "qwen2.5vl"])),
    ):
        assert list_loaded_models(_BASE) == ["llama3", "qwen2.5vl"]
    print("  [OK] Names extracted from /api/ps")


def test_list_loaded_models_unreachable_returns_empty() -> None:
    """An unreachable Ollama yields an empty list, not an exception."""
    print("\n[TEST] list_loaded_models - unreachable")
    with patch(
        "src.ai.ollama_admin.requests.get",
        side_effect=requests.RequestException("down"),
    ):
        assert list_loaded_models(_BASE) == []
    print("  [OK] Empty list when the request raises")


def test_unload_empty_base_url_returns_zero() -> None:
    """An empty base URL unloads nothing."""
    print("\n[TEST] unload_ollama_models - empty base URL")
    assert unload_ollama_models("") == 0
    print("  [OK] Zero without a base URL")


def test_unload_evicts_each_resident_model() -> None:
    """Every resident model is asked to unload; the count reflects successes."""
    print("\n[TEST] unload_ollama_models - two models evicted")
    with patch(
        "src.ai.ollama_admin.requests.get",
        return_value=_resp(200, _ps(["llama3", "qwen2.5vl"])),
    ), patch(
        "src.ai.ollama_admin.requests.post", return_value=_resp(200)
    ) as mock_post:
        assert unload_ollama_models(_BASE) == 2
    assert mock_post.call_count == 2
    for call in mock_post.call_args_list:
        assert call.kwargs["json"]["keep_alive"] == 0
    print("  [OK] Both models unloaded with keep_alive=0")


def test_unload_returns_zero_when_nothing_loaded() -> None:
    """No resident models means nothing to unload."""
    print("\n[TEST] unload_ollama_models - nothing loaded")
    with patch(
        "src.ai.ollama_admin.requests.get", return_value=_resp(200, _ps([]))
    ), patch("src.ai.ollama_admin.requests.post") as mock_post:
        assert unload_ollama_models(_BASE) == 0
    mock_post.assert_not_called()
    print("  [OK] Zero and no POST when nothing is resident")


def test_unload_skips_a_model_that_fails() -> None:
    """A failed eviction is skipped; other models still count."""
    print("\n[TEST] unload_ollama_models - partial failure")
    with patch(
        "src.ai.ollama_admin.requests.get",
        return_value=_resp(200, _ps(["good", "bad"])),
    ), patch(
        "src.ai.ollama_admin.requests.post",
        side_effect=[_resp(200), requests.RequestException("boom")],
    ):
        assert unload_ollama_models(_BASE) == 1
    print("  [OK] One success counted, the failure skipped")


def run_all_tests() -> None:
    """Run all Ollama admin helper tests."""
    test_list_loaded_models_empty_base_url_returns_empty()
    test_list_loaded_models_returns_names()
    test_list_loaded_models_unreachable_returns_empty()
    test_unload_empty_base_url_returns_zero()
    test_unload_evicts_each_resident_model()
    test_unload_returns_zero_when_nothing_loaded()
    test_unload_skips_a_model_that_fails()
    print("\n[PASS] All Ollama admin tests passed.")


if __name__ == "__main__":
    run_all_tests()
