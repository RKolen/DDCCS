"""Unit tests for the ComfyUI portrait endpoint in src.sidecar.app.

All tests mock the ComfyUI client and config, so they run without a live
ComfyUI instance and never load a Stable Diffusion checkpoint.
"""

import base64
from typing import Any
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from tests.test_helpers import setup_test_environment, import_module

setup_test_environment()

_app_mod = import_module("src.sidecar.app")
app = _app_mod.app

_HTTP = TestClient(app)

_ENDPOINT = "/character/portrait"
_PROFILE = {
    "name": "Aragorn",
    "species": "human",
    "lineage": "Dunedain",
    "character_class": "Ranger",
}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _config(enabled: bool = True, checkpoint: str = "sd15.safetensors") -> MagicMock:
    """Build a mock config whose comfyui section has known values."""
    cfg = MagicMock()
    cfg.comfyui.enabled = enabled
    cfg.comfyui.assets.checkpoint = checkpoint
    return cfg


def _client(
    available: bool = True, png: Any = b"PNGDATA"
) -> MagicMock:
    """Build a mock ComfyUIClient."""
    client = MagicMock()
    client.is_available.return_value = available
    client.generate.return_value = png
    client.free.return_value = True
    return client


def _post(cfg: MagicMock, client: Any, body: Any = None) -> Any:
    """POST to the portrait endpoint with config and client patched."""
    payload = body if body is not None else {"profile": _PROFILE}
    with patch("src.sidecar.app.load_config", return_value=cfg), patch(
        "src.sidecar.app._get_comfyui_client", return_value=client
    ):
        return _HTTP.post(_ENDPOINT, json=payload)


# ---------------------------------------------------------------------------
# feature-flag / availability behaviour (graceful degradation)
# ---------------------------------------------------------------------------


def test_portrait_disabled_returns_503() -> None:
    """A disabled feature flag yields 503, not an error page."""
    print("\n[TEST] portrait - disabled returns 503")
    resp = _post(_config(enabled=False), _client())
    assert resp.status_code == 503, resp.status_code
    assert "COMFYUI_ENABLED" in resp.json()["detail"]
    print("  [OK] 503 with a message naming the flag")


def test_portrait_unconfigured_client_returns_503() -> None:
    """No resolvable base URL yields 503."""
    print("\n[TEST] portrait - unconfigured client returns 503")
    resp = _post(_config(), None)
    assert resp.status_code == 503, resp.status_code
    assert "base URL" in resp.json()["detail"]
    print("  [OK] 503 when the client cannot be built")


def test_portrait_missing_checkpoint_returns_503() -> None:
    """A missing checkpoint yields 503 rather than a ComfyUI failure."""
    print("\n[TEST] portrait - missing checkpoint returns 503")
    resp = _post(_config(checkpoint=""), _client())
    assert resp.status_code == 503, resp.status_code
    assert "COMFYUI_CHECKPOINT" in resp.json()["detail"]
    print("  [OK] 503 naming the checkpoint setting")


def test_portrait_unreachable_returns_503() -> None:
    """An unreachable ComfyUI yields 503."""
    print("\n[TEST] portrait - unreachable returns 503")
    resp = _post(_config(), _client(available=False))
    assert resp.status_code == 503, resp.status_code
    assert "not reachable" in resp.json()["detail"]
    print("  [OK] 503 when the availability probe fails")


def test_portrait_generation_failure_returns_500() -> None:
    """A failed or timed-out generation yields 500."""
    print("\n[TEST] portrait - generation failure returns 500")
    resp = _post(_config(), _client(png=None))
    assert resp.status_code == 500, resp.status_code
    assert "failed or timed out" in resp.json()["detail"]
    print("  [OK] 500 when generate() returns None")


# ---------------------------------------------------------------------------
# success path
# ---------------------------------------------------------------------------


def test_portrait_success_returns_base64_png() -> None:
    """A successful render returns the base64 PNG plus seed, prompt, and alt."""
    print("\n[TEST] portrait - success returns base64 PNG")
    client = _client()
    resp = _post(_config(), client)

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert base64.b64decode(body["image_base64"]) == b"PNGDATA"
    assert isinstance(body["seed"], int)
    assert "Ranger" in body["prompt"]
    assert body["alt"] == "Portrait of Aragorn, a Dunedain human Ranger"
    print("  [OK] base64 PNG, seed, prompt, and alt returned")


def test_portrait_uses_requested_seed_and_size() -> None:
    """An explicit seed and size are threaded into the workflow."""
    print("\n[TEST] portrait - explicit seed and size honoured")
    client = _client()
    resp = _post(
        _config(),
        client,
        body={"profile": _PROFILE, "seed": 1234, "width": 512, "height": 768},
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["seed"] == 1234
    workflow = client.generate.call_args.args[0]
    assert workflow["3"]["inputs"]["seed"] == 1234
    assert workflow["5"]["inputs"]["width"] == 512
    assert workflow["5"]["inputs"]["height"] == 768
    assert workflow["4"]["inputs"]["ckpt_name"] == "sd15.safetensors"
    print("  [OK] seed, size, and checkpoint patched into the workflow")


def test_portrait_frees_models_after_generation() -> None:
    """Models are unloaded after a run (CPU-only OOM guard)."""
    print("\n[TEST] portrait - models freed after generation")
    client = _client()
    _post(_config(), client)
    client.free.assert_called_once()
    print("  [OK] free() called once after a successful render")


def test_portrait_frees_models_when_generation_fails() -> None:
    """Models are unloaded even when generation fails."""
    print("\n[TEST] portrait - models freed on failure")
    client = _client(png=None)
    _post(_config(), client)
    client.free.assert_called_once()
    print("  [OK] free() called even on the failure path")


# ---------------------------------------------------------------------------
# request validation
# ---------------------------------------------------------------------------


def test_portrait_empty_profile_rejected() -> None:
    """An empty profile is rejected before any generation is attempted."""
    print("\n[TEST] portrait - empty profile rejected")
    client = _client()
    resp = _post(_config(), client, body={"profile": {}})
    assert resp.status_code == 422, resp.status_code
    client.generate.assert_not_called()
    print("  [OK] 422 and no generation attempted")


def run_all_tests() -> None:
    """Run all portrait endpoint tests."""
    test_portrait_disabled_returns_503()
    test_portrait_unconfigured_client_returns_503()
    test_portrait_missing_checkpoint_returns_503()
    test_portrait_unreachable_returns_503()
    test_portrait_generation_failure_returns_500()
    test_portrait_success_returns_base64_png()
    test_portrait_uses_requested_seed_and_size()
    test_portrait_frees_models_after_generation()
    test_portrait_frees_models_when_generation_fails()
    test_portrait_empty_profile_rejected()
    print("\n[PASS] All portrait endpoint tests passed.")


if __name__ == "__main__":
    run_all_tests()
