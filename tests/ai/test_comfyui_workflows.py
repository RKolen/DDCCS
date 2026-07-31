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
IdentityReference = test_helpers.safe_from_import(
    "src.ai.comfyui_workflows", "IdentityReference"
)
IpAdapterParams = test_helpers.safe_from_import(
    "src.ai.comfyui_workflows", "IpAdapterParams"
)
ipadapter_workflow = test_helpers.safe_from_import(
    "src.ai.comfyui_workflows", "ipadapter_workflow"
)


# Stand-in model names. Deliberately not real file names: the builders are
# asserted to thread whatever a deployment configures into the graph, and a
# plausible name here would read as configuration to keep in sync with .env.
_CHECKPOINT = "test-checkpoint"
_IPADAPTER_MODEL = "test-ipadapter-model"
_CLIP_VISION = "test-clip-vision"


def _ipadapter_params(weight: float = 0.8) -> object:
    """Build IpAdapterParams with a known identity reference."""
    return IpAdapterParams(
        checkpoint=_CHECKPOINT,
        positive="a brave ranger",
        negative="blurry",
        seed=7,
        identity=IdentityReference(
            image="identity_abc.png",
            ipadapter_model=_IPADAPTER_MODEL,
            clip_vision=_CLIP_VISION,
            weight=weight,
        ),
    )


def test_txt2img_workflow_patches_prompts_and_seed() -> None:
    """The builder threads prompts, seed, and checkpoint into the graph."""
    print("\n[TEST] txt2img_workflow - prompts/seed/checkpoint patched")
    params = Txt2ImgParams(
        checkpoint=_CHECKPOINT,
        positive="a brave ranger",
        negative="blurry",
        seed=42,
    )
    workflow = txt2img_workflow(params)

    assert workflow["4"]["inputs"]["ckpt_name"] == _CHECKPOINT
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


def test_ipadapter_workflow_keeps_the_text_to_image_graph() -> None:
    """The identity graph is the txt2img one with prompts and seed intact."""
    print("\n[TEST] ipadapter_workflow - text-to-image graph preserved")
    workflow = ipadapter_workflow(_ipadapter_params())

    assert workflow["4"]["inputs"]["ckpt_name"] == _CHECKPOINT
    assert workflow["6"]["inputs"]["text"] == "a brave ranger"
    assert workflow["7"]["inputs"]["text"] == "blurry"
    assert workflow["3"]["inputs"]["seed"] == 7
    assert workflow["9"]["class_type"] == "SaveImage"
    print("  [OK] Checkpoint, prompts, seed, and output node unchanged")


def test_ipadapter_workflow_adds_identity_chain() -> None:
    """The IPAdapter, CLIP-vision, and reference image nodes are added."""
    print("\n[TEST] ipadapter_workflow - identity chain nodes")
    workflow = ipadapter_workflow(_ipadapter_params())

    assert workflow["10"]["class_type"] == "IPAdapterModelLoader"
    assert workflow["10"]["inputs"]["ipadapter_file"] == _IPADAPTER_MODEL
    assert workflow["11"]["class_type"] == "CLIPVisionLoader"
    assert workflow["11"]["inputs"]["clip_name"] == _CLIP_VISION
    assert workflow["12"]["class_type"] == "LoadImage"
    assert workflow["12"]["inputs"]["image"] == "identity_abc.png"
    assert workflow["13"]["class_type"] == "IPAdapterAdvanced"
    print("  [OK] Loader, encoder, reference, and adapter nodes present")


def test_ipadapter_workflow_rewires_sampler_onto_patched_model() -> None:
    """The sampler reads the IPAdapter-patched model, not the raw checkpoint.

    Without this rewire the identity chain is built and silently ignored: the
    render comes back as a plain txt2img with no visible sign anything failed.
    """
    print("\n[TEST] ipadapter_workflow - sampler rewired to the patched model")
    workflow = ipadapter_workflow(_ipadapter_params())

    assert workflow["3"]["inputs"]["model"] == ["13", 0]
    assert workflow["13"]["inputs"]["model"] == ["4", 0]
    assert workflow["13"]["inputs"]["ipadapter"] == ["10", 0]
    assert workflow["13"]["inputs"]["clip_vision"] == ["11", 0]
    assert workflow["13"]["inputs"]["image"] == ["12", 0]
    print("  [OK] KSampler consumes the patched model output")


def test_ipadapter_workflow_applies_identity_weight() -> None:
    """The likeness weight reaches the adapter node."""
    print("\n[TEST] ipadapter_workflow - identity weight applied")
    workflow = ipadapter_workflow(_ipadapter_params(weight=0.55))

    assert workflow["13"]["inputs"]["weight"] == 0.55
    print("  [OK] Weight threaded into IPAdapterAdvanced")


def run_all_tests() -> None:
    """Run all ComfyUI workflow builder tests."""
    test_txt2img_workflow_patches_prompts_and_seed()
    test_txt2img_workflow_respects_size_overrides()
    test_txt2img_workflow_has_output_saveimage_node()
    test_ipadapter_workflow_keeps_the_text_to_image_graph()
    test_ipadapter_workflow_adds_identity_chain()
    test_ipadapter_workflow_rewires_sampler_onto_patched_model()
    test_ipadapter_workflow_applies_identity_weight()
    print("\n[PASS] All ComfyUI workflow tests passed.")


if __name__ == "__main__":
    run_all_tests()
