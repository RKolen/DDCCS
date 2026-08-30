"""Unit tests for the story-image sidecar endpoints.

All tests mock the AI client and ComfyUI, so they run without Ollama or a
checkpoint.
"""

import base64
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from tests.test_helpers import setup_test_environment, import_module

setup_test_environment()

SceneRenderResult = import_module(
    "src.story_images.render"
).SceneRenderResult

_app_mod = import_module("src.sidecar.app")
app = _app_mod.app
_HTTP = TestClient(app)

_CHECKPOINT = "test-checkpoint"


def _config(enabled: bool = True, checkpoint: str = _CHECKPOINT) -> MagicMock:
    """Build a mock config whose comfyui section has known values."""
    cfg = MagicMock()
    cfg.comfyui.enabled = enabled
    cfg.comfyui.assets.checkpoint = checkpoint
    cfg.comfyui.get_base_url.return_value = "http://comfy.test"
    cfg.comfyui.scene_timeout = 1800.0
    cfg.comfyui.ollama_url = ""
    cfg.drupal.ca_bundle = ""
    return cfg


def test_events_empty_body_rejected() -> None:
    """A blank body is rejected before any model call."""
    print("\n[TEST] /story/events - empty body rejected")
    resp = _HTTP.post("/story/events", json={"body": "  ", "title": "Arrival"})
    assert resp.status_code == 422, resp.status_code
    print("  [OK] 422")


def test_events_returns_parsed_list() -> None:
    """A scripted extractor result is returned as events."""
    print("\n[TEST] /story/events - parsed list")
    types = import_module("src.story_images.types")
    event = types.StoryEvent("Arrival", "They reach Bree.", "Aragorn reached Bree.")
    with patch(
        "src.sidecar.story_image_routes.extract_events", return_value=[event]
    ), patch(
        "src.sidecar.story_image_routes.get_story_image_ai_client", return_value=MagicMock()
    ):
        resp = _HTTP.post(
            "/story/events",
            json={"body": "Aragorn reached Bree.", "title": "The Arrival"},
        )
    assert resp.status_code == 200, resp.text
    assert resp.json()["events"][0]["title"] == "Arrival"
    print("  [OK] Event list returned")


def test_scene_disabled_returns_503() -> None:
    """A disabled feature flag yields 503."""
    print("\n[TEST] /story/scene - disabled returns 503")
    with patch("src.sidecar.story_image_routes.load_config", return_value=_config(enabled=False)):
        resp = _HTTP.post(
            "/story/scene", json={"excerpt": "Aragorn waited in Bree.", "title": "Watch"}
        )
    assert resp.status_code == 503, resp.status_code
    print("  [OK] 503")


def test_scene_success_returns_png() -> None:
    """A successful render returns the base64 PNG and prompt metadata."""
    print("\n[TEST] /story/scene - success")
    types = import_module("src.story_images.types")
    analysis = types.ShotAnalysis(
        setting="Bree",
        action="Aragorn waits",
        mood="rain",
        people=[types.ShotPerson(name="Aragorn", character_id="pc-1", portrait_url="a.png")],
    )
    cfg = _config()
    client = MagicMock()
    client.is_available.return_value = True
    with patch("src.sidecar.story_image_routes.load_config", return_value=cfg), patch(
        "src.sidecar.story_image_routes.ComfyUIClient", return_value=client
    ), patch(
        "src.sidecar.story_image_routes.analyze_shot", return_value=analysis
    ), patch(
        "src.sidecar.story_image_routes.render_scene",
        return_value=SceneRenderResult(
            png=b"PNGDATA",
            leads=["Aragorn"],
            swapped=["Gandalf the Grey"],
        ),
    ), patch(
        "src.sidecar.story_image_routes.get_story_image_ai_client", return_value=MagicMock()
    ):
        resp = _HTTP.post(
            "/story/scene",
            json={
                "excerpt": "Aragorn waited in Bree.",
                "title": "Watch",
                "seed": 9,
                "people": [{"name": "Aragorn", "use_likeness": True, "portrait_url": "a.png"}],
            },
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert base64.b64decode(body["image_base64"]) == b"PNGDATA"
    assert body["seed"] == 9
    assert body["used_ipadapter"] == 1
    # Both likeness paths are named: a count beside a name list reads as a
    # contradiction to whoever has to review the picture.
    assert body["lead_faces"] == ["Aragorn"]
    assert body["swapped_faces"] == ["Gandalf the Grey"]
    print("  [OK] PNG, seed, and both likeness paths named")


def run_all_tests() -> None:
    """Run all story-image endpoint tests."""
    test_events_empty_body_rejected()
    test_events_returns_parsed_list()
    test_scene_disabled_returns_503()
    test_scene_success_returns_png()
    print("\n[PASS] All story-image endpoint tests passed.")


if __name__ == "__main__":
    run_all_tests()
