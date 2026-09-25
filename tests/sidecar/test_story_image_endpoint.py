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
    # Explicit: a MagicMock attribute is truthy, so leaving this unset would
    # have every test in this file try to restart a real ComfyUI.
    cfg.comfyui.local.restart_after_scene = False
    # Real numbers: the staging layout does arithmetic with these, and a
    # MagicMock canvas size fails inside the layout rather than at the edge.
    cfg.comfyui.assets.scene.width = 1152
    cfg.comfyui.assets.scene.height = 768
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


def test_staging_lists_settings_and_moods() -> None:
    """The console can read the vocabulary rather than hardcode it."""
    print("\n[TEST] /story/staging - vocabulary")
    resp = _HTTP.get("/story/staging")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    names = [row["name"] for row in body["settings"]]
    assert "castle" in names and "forest" in names, names
    castle = next(r for r in body["settings"] if r["name"] == "castle")
    assert "curtain wall" in castle["description"]
    assert any(row["name"] == "grim" for row in body["moods"])
    print(f"  [OK] {len(names)} settings, {len(body['moods'])} moods")


def _scene_call(payload: dict, analysis: object) -> dict:
    """POST /story/scene with everything below the route mocked out.

    Args:
        payload: Extra request fields merged over a minimal valid body.
        analysis: The ShotAnalysis analyze_shot should return.

    Returns:
        The captured positive prompt and the people the route built.
    """
    captured: dict = {}

    def _capture(request: object) -> object:
        captured["request"] = request
        return SceneRenderResult(png=b"PNGDATA", leads=[], swapped=[])

    client = MagicMock()
    client.is_available.return_value = True
    with patch("src.sidecar.story_image_routes.load_config",
               return_value=_config()), patch(
        "src.sidecar.story_image_routes.ComfyUIClient", return_value=client
    ), patch(
        "src.sidecar.story_image_routes.analyze_shot", return_value=analysis
    ), patch(
        "src.sidecar.story_image_routes.fill_appearances",
        side_effect=lambda people, *_a, **_k: people,
    ), patch(
        "src.sidecar.story_image_routes.render_scene", side_effect=_capture
    ), patch(
        "src.sidecar.story_image_routes.get_story_image_ai_client",
        return_value=MagicMock()
    ):
        body = {"excerpt": "They met on the road.", "title": "Meeting"}
        body.update(payload)
        resp = _HTTP.post("/story/scene", json=body)
    assert resp.status_code == 200, resp.text
    return {"response": resp.json(), "request": captured["request"]}


def test_operator_setting_and_mood_outrank_the_analysis() -> None:
    """A named setting replaces whatever the model wrote."""
    print("\n[TEST] /story/scene - operator staging wins")
    types = import_module("src.story_images.types")
    analysis = types.ShotAnalysis(
        setting="a muddy field", action="they meet", mood="damp",
        people=[types.ShotPerson(name="Aragorn")],
    )
    out = _scene_call(
        {"setting": "castle", "mood": "grim",
         "people": [{"name": "Aragorn"}]},
        analysis,
    )
    body = out["response"]
    assert "castle courtyard" in body["setting"], body["setting"]
    assert "muddy field" not in body["setting"]
    assert "drifting ash" in body["mood"], body["mood"]
    print("  [OK] Setting and mood replaced")


def test_unstaged_scene_keeps_the_analysed_setting() -> None:
    """Choosing nothing leaves the analysis alone, as before."""
    print("\n[TEST] /story/scene - no staging chosen")
    types = import_module("src.story_images.types")
    analysis = types.ShotAnalysis(
        setting="a muddy field", action="they meet", mood="damp",
        people=[types.ShotPerson(name="Aragorn")],
    )
    body = _scene_call({"people": [{"name": "Aragorn"}]}, analysis)["response"]
    assert body["setting"] == "a muddy field"
    assert body["mood"] == "damp"
    print("  [OK] Analysis untouched")


def test_blank_person_action_falls_back_to_the_analysis() -> None:
    """The console sends a row per person whether it has an opinion or not.

    An untouched row must defer to the analysed action rather than erase it,
    while a filled one must win.
    """
    print("\n[TEST] /story/scene - per-person action fallback")
    types = import_module("src.story_images.types")
    analysis = types.ShotAnalysis(
        setting="Bree", action="they meet", mood="",
        people=[
            types.ShotPerson(name="Aragorn", action="drawing a sword"),
            types.ShotPerson(name="Frodo Baggins", action="hiding"),
        ],
    )
    out = _scene_call(
        {"people": [
            {"name": "Aragorn"},
            {"name": "Frodo Baggins", "action": "climbing a fence"},
        ]},
        analysis,
    )
    prompt = out["request"].prompts.positive
    assert "drawing a sword" in prompt, prompt
    assert "climbing a fence" in prompt, prompt
    assert "hiding" not in prompt, prompt
    print("  [OK] Blank row filled, typed row wins")


def test_comfyui_is_restarted_only_when_configured() -> None:
    """The render recycles ComfyUI only where this host manages it.

    ComfyUI keeps the memory a render grew until the process ends, so the
    next job would start with none. Restarting before the response returns
    means the next job finds a clean one - but only ever for a ComfyUI this
    deployment started.
    """
    print("\n[TEST] /story/scene - restart gated on config")
    types = import_module("src.story_images.types")
    analysis = types.ShotAnalysis(setting="Bree", action="they meet", mood="")

    for enabled in (False, True):
        cfg = _config()
        cfg.comfyui.local.restart_after_scene = enabled
        client = MagicMock()
        client.is_available.return_value = True
        with patch("src.sidecar.story_image_routes.load_config",
                   return_value=cfg), patch(
            "src.sidecar.story_image_routes.ComfyUIClient", return_value=client
        ), patch(
            "src.sidecar.story_image_routes.analyze_shot", return_value=analysis
        ), patch(
            "src.sidecar.story_image_routes.fill_appearances",
            side_effect=lambda people, *_a, **_k: people,
        ), patch(
            "src.sidecar.story_image_routes.render_scene",
            return_value=SceneRenderResult(png=b"PNG", leads=[], swapped=[]),
        ), patch(
            "src.sidecar.story_image_routes.get_story_image_ai_client",
            return_value=MagicMock()
        ), patch(
            "src.sidecar.story_image_routes.restart_comfyui", return_value=True
        ) as restart:
            resp = _HTTP.post("/story/scene", json={
                "excerpt": "They met on the road.",
                "people": [{"name": "Aragorn"}],
            })
        assert resp.status_code == 200, resp.text
        assert restart.called is enabled, enabled
    print("  [OK] Off by default, called when COMFYUI_RESTART_AFTER_SCENE")


def test_stage_preview_returns_a_skeleton_and_its_boxes() -> None:
    """The staging can be seen before a render is paid for.

    A scene costs minutes and a ComfyUI restart; the staging that decides
    who stands where costs nothing to look at. The boxes come back with it
    so the console can hit-test a drag against the figure under the cursor.
    """
    print("\n[TEST] /story/stage - skeleton preview")
    with patch("src.sidecar.story_image_routes.load_config",
               return_value=_config()):
        resp = _HTTP.post("/story/stage", json={
            "people": [{"name": "Aragorn"}, {"name": "Frodo Baggins"}],
            "placements": [
                {"name": "Aragorn", "lateral": 0.3, "depth": 1.0,
                 "pose": "walking"},
                {"name": "Frodo Baggins", "lateral": 0.8, "depth": 2.0,
                 "pose": "standing"},
            ],
            "shot": "full",
        })
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert base64.b64decode(body["image_base64"])[:8] == b"\x89PNG\r\n\x1a\n"
    boxes = {row["name"]: row["box"] for row in body["placements"]}
    near, far = boxes["Aragorn"], boxes["Frodo Baggins"]
    # Distance is height and floor together. A halfling is shorter anyway,
    # so the feet are what prove depth was applied rather than species.
    assert far[1] + far[3] < near[1] + near[3], (near, far)
    assert "walking" in body["poses"] and len(body["poses"]) > 1
    print(f"  [OK] PNG, {len(boxes)} boxes, far figure's feet higher")


def test_stage_preview_needs_someone_in_the_shot() -> None:
    """An empty cast is a 422, not a blank canvas."""
    print("\n[TEST] /story/stage - empty cast rejected")
    with patch("src.sidecar.story_image_routes.load_config",
               return_value=_config()):
        resp = _HTTP.post("/story/stage", json={"people": []})
    assert resp.status_code == 422, resp.status_code
    print("  [OK] 422")


def run_all_tests() -> None:
    """Run all story-image endpoint tests."""
    test_events_empty_body_rejected()
    test_events_returns_parsed_list()
    test_scene_disabled_returns_503()
    test_scene_success_returns_png()
    test_staging_lists_settings_and_moods()
    test_operator_setting_and_mood_outrank_the_analysis()
    test_unstaged_scene_keeps_the_analysed_setting()
    test_blank_person_action_falls_back_to_the_analysis()
    test_comfyui_is_restarted_only_when_configured()
    test_stage_preview_returns_a_skeleton_and_its_boxes()
    test_stage_preview_needs_someone_in_the_shot()
    print("\n[PASS] All story-image endpoint tests passed.")


if __name__ == "__main__":
    run_all_tests()
