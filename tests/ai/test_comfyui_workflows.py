"""Tests for the ComfyUI workflow builders (comfyui_workflows)."""

from tests import test_helpers

Txt2ImgParams = test_helpers.safe_from_import(
    "src.ai.comfyui_workflows", "Txt2ImgParams"
)
RenderSettings = test_helpers.safe_from_import(
    "src.ai.comfyui_workflows", "RenderSettings"
)
txt2img_workflow = test_helpers.safe_from_import(
    "src.ai.comfyui_workflows", "txt2img_workflow"
)


def test_txt2img_workflow_patches_prompts_and_seed() -> None:
    """The builder threads prompts, seed, and checkpoint into the graph."""
    print("\n[TEST] txt2img_workflow - prompts/seed/checkpoint patched")
    params = Txt2ImgParams(
        checkpoint="sd15.safetensors",
        positive="a brave ranger",
        negative="blurry",
        seed=42,
    )
    workflow = txt2img_workflow(params)

    assert workflow["4"]["inputs"]["ckpt_name"] == "sd15.safetensors"
    assert workflow["6"]["inputs"]["text"] == "a brave ranger"
    assert workflow["7"]["inputs"]["text"] == "blurry"
    assert workflow["3"]["inputs"]["seed"] == 42
    print("  [OK] Checkpoint, prompts, and seed patched into nodes")


def test_txt2img_workflow_respects_size_overrides() -> None:
    """Width/height overrides flow into the EmptyLatentImage node."""
    print("\n[TEST] txt2img_workflow - size overrides")
    params = Txt2ImgParams(
        checkpoint="ckpt",
        positive="p",
        negative="n",
        seed=1,
        render=RenderSettings(width=512, height=768),
    )
    workflow = txt2img_workflow(params)

    assert workflow["5"]["inputs"]["width"] == 512
    assert workflow["5"]["inputs"]["height"] == 768
    print("  [OK] SD 1.5-class size overrides applied")


def test_txt2img_workflow_has_output_saveimage_node() -> None:
    """The graph terminates in a SaveImage node so an output is produced."""
    print("\n[TEST] txt2img_workflow - SaveImage terminal node")
    params = Txt2ImgParams(checkpoint="c", positive="p", negative="n", seed=0)
    workflow = txt2img_workflow(params)

    assert workflow["9"]["class_type"] == "SaveImage"
    assert workflow["9"]["inputs"]["images"] == ["8", 0]
    print("  [OK] SaveImage node wired to the VAEDecode output")


def run_all_tests() -> None:
    """Run all ComfyUI workflow builder tests."""
    test_txt2img_workflow_patches_prompts_and_seed()
    test_txt2img_workflow_respects_size_overrides()
    test_txt2img_workflow_has_output_saveimage_node()
    print("\n[PASS] All ComfyUI workflow tests passed.")


if __name__ == "__main__":
    run_all_tests()
