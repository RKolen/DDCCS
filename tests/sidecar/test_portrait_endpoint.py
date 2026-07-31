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

# Stand-in model names. Deliberately not real file names: what is under test is
# that whatever a deployment configures reaches the workflow, not which models
# this box happens to run. A plausible-looking name here reads as configuration
# and invites someone to keep it in sync with .env, which it must never be.
_CHECKPOINT = "test-checkpoint"
_IPADAPTER_MODEL = "test-ipadapter-model"
_CLIP_VISION = "test-clip-vision"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _config(
    enabled: bool = True,
    checkpoint: str = _CHECKPOINT,
    identity: bool = False,
) -> MagicMock:
    """Build a mock config whose comfyui section has known values.

    ``identity`` decides whether the IPAdapter models look configured. It must
    be set explicitly: on a bare MagicMock every attribute is truthy, so an
    unset assets section would silently claim identity support it does not have.
    """
    cfg = MagicMock()
    cfg.comfyui.enabled = enabled
    cfg.comfyui.assets.checkpoint = checkpoint
    cfg.comfyui.assets.supports_identity.return_value = identity
    cfg.comfyui.assets.ipadapter_model = _IPADAPTER_MODEL if identity else ""
    cfg.comfyui.assets.clip_vision = _CLIP_VISION if identity else ""
    return cfg


def _client(
    available: bool = True, png: Any = b"PNGDATA", upload: Any = "identity_abc.png"
) -> MagicMock:
    """Build a mock ComfyUIClient."""
    client = MagicMock()
    client.is_available.return_value = available
    client.generate.return_value = png
    client.free.return_value = True
    client.upload_image.return_value = upload
    return client


def _post(cfg: MagicMock, client: Any, body: Any = None, reference: Any = b"REF") -> Any:
    """POST to the portrait endpoint with config, client, and fetch patched.

    ``reference`` stands in for the bytes of an existing portrait; None
    simulates a reference URL that cannot be fetched.
    """
    payload = body if body is not None else {"profile": _PROFILE}
    with patch("src.sidecar.app.load_config", return_value=cfg), patch(
        "src.sidecar.app._get_comfyui_client", return_value=client
    ), patch("src.sidecar.app.fetch_image_bytes", return_value=reference):
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
    assert workflow["4"]["inputs"]["ckpt_name"] == _CHECKPOINT
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
# identity conditioning (IPAdapter)
# ---------------------------------------------------------------------------


_WITH_REFERENCE = {
    "profile": _PROFILE,
    "reference_image_url": "https://drupal.test/portrait.png",
}


def test_portrait_conditions_on_reference_when_ipadapter_configured() -> None:
    """A reference portrait plus configured models yields the IPAdapter graph."""
    print("\n[TEST] portrait - reference builds the IPAdapter workflow")
    client = _client()
    resp = _post(_config(identity=True), client, body=_WITH_REFERENCE)

    assert resp.status_code == 200, resp.text
    assert resp.json()["used_reference"] is True
    client.upload_image.assert_called_once()
    workflow = client.generate.call_args.args[0]
    assert workflow["13"]["class_type"] == "IPAdapterAdvanced"
    assert workflow["3"]["inputs"]["model"] == ["13", 0]
    assert workflow["12"]["inputs"]["image"] == "identity_abc.png"
    # The configured model names must reach the graph: getting these from
    # config rather than a literal is the whole point of the assets section.
    assert workflow["10"]["inputs"]["ipadapter_file"] == _IPADAPTER_MODEL
    assert workflow["11"]["inputs"]["clip_name"] == _CLIP_VISION
    print("  [OK] Reference uploaded and the sampler reads the patched model")


def test_portrait_identity_weight_reaches_the_adapter() -> None:
    """An explicit likeness weight is threaded into the graph."""
    print("\n[TEST] portrait - identity weight honoured")
    client = _client()
    resp = _post(
        _config(identity=True),
        client,
        body={**_WITH_REFERENCE, "identity_weight": 0.6},
    )

    assert resp.status_code == 200, resp.text
    workflow = client.generate.call_args.args[0]
    assert workflow["13"]["inputs"]["weight"] == 0.6
    print("  [OK] Weight patched into IPAdapterAdvanced")


def test_portrait_ignores_reference_without_ipadapter_models() -> None:
    """Unconfigured IPAdapter models degrade to text-to-image, not an error."""
    print("\n[TEST] portrait - reference ignored without IPAdapter models")
    client = _client()
    resp = _post(_config(identity=False), client, body=_WITH_REFERENCE)

    assert resp.status_code == 200, resp.text
    assert resp.json()["used_reference"] is False
    client.upload_image.assert_not_called()
    assert "13" not in client.generate.call_args.args[0]
    print("  [OK] Plain text-to-image render, no upload attempted")


def test_portrait_falls_back_when_reference_cannot_be_fetched() -> None:
    """An unfetchable reference still produces a portrait, without likeness."""
    print("\n[TEST] portrait - unfetchable reference degrades to txt2img")
    client = _client()
    resp = _post(
        _config(identity=True), client, body=_WITH_REFERENCE, reference=None
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["used_reference"] is False
    client.upload_image.assert_not_called()
    assert "13" not in client.generate.call_args.args[0]
    print("  [OK] Render succeeded as text-to-image")


def test_portrait_falls_back_when_reference_upload_fails() -> None:
    """A failed upload degrades to text-to-image rather than a broken graph."""
    print("\n[TEST] portrait - failed upload degrades to txt2img")
    client = _client(upload=None)
    resp = _post(_config(identity=True), client, body=_WITH_REFERENCE)

    assert resp.status_code == 200, resp.text
    assert resp.json()["used_reference"] is False
    assert "13" not in client.generate.call_args.args[0]
    print("  [OK] Render succeeded without the identity chain")


def test_portrait_without_reference_stays_text_to_image() -> None:
    """No reference URL means no upload and no identity nodes."""
    print("\n[TEST] portrait - no reference stays text-to-image")
    client = _client()
    resp = _post(_config(identity=True), client)

    assert resp.status_code == 200, resp.text
    assert resp.json()["used_reference"] is False
    client.upload_image.assert_not_called()
    print("  [OK] Identity path not taken for a first render")


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
    test_portrait_conditions_on_reference_when_ipadapter_configured()
    test_portrait_identity_weight_reaches_the_adapter()
    test_portrait_ignores_reference_without_ipadapter_models()
    test_portrait_falls_back_when_reference_cannot_be_fetched()
    test_portrait_falls_back_when_reference_upload_fails()
    test_portrait_without_reference_stays_text_to_image()
    test_portrait_empty_profile_rejected()
    print("\n[PASS] All portrait endpoint tests passed.")


if __name__ == "__main__":
    run_all_tests()
