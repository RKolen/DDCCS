"""Unit tests for story-scene ComfyUI workflow builders and likeness split."""

from tests.test_helpers import setup_test_environment, import_module

setup_test_environment()

wf = import_module("src.ai.comfyui_workflows")
types = import_module("src.story_images.types")
render = import_module("src.story_images.render")

IdentityReference = wf.IdentityReference
SceneIpAdapterParams = wf.SceneIpAdapterParams
ReactorSwapParams = wf.ReactorSwapParams
scene_workflow = wf.scene_workflow
reactor_swap_workflow = wf.reactor_swap_workflow
SCENE_RENDER = wf.SCENE_RENDER
ShotPerson = types.ShotPerson
split_likeness = render.split_likeness

_CHECKPOINT = "test-checkpoint"
_IPADAPTER_MODEL = "test-ipadapter-model"
_CLIP_VISION = "test-clip-vision"


def _identity(name: str, weight: float) -> object:
    """Build an identity reference with a known filename."""
    return IdentityReference(
        image=name,
        ipadapter_model=_IPADAPTER_MODEL,
        clip_vision=_CLIP_VISION,
        weight=weight,
    )


def test_scene_workflow_defaults_to_landscape() -> None:
    """A scene without identities is txt2img at 768x512."""
    print("\n[TEST] scene_workflow - landscape defaults")
    workflow = scene_workflow(
        SceneIpAdapterParams(
            checkpoint=_CHECKPOINT,
            positive="a tavern",
            negative="blurry",
            seed=3,
            identities=[],
            render=SCENE_RENDER,
        )
    )
    assert workflow["5"]["inputs"]["width"] == 768
    assert workflow["5"]["inputs"]["height"] == 512
    assert workflow["9"]["inputs"]["filename_prefix"] == "scene"
    assert "13" not in workflow
    print("  [OK] 768x512, scene prefix, no adapter nodes")


def test_scene_workflow_chains_two_ipadapters() -> None:
    """Two identities patch the model in series; the sampler reads the last."""
    print("\n[TEST] scene_workflow - two IPAdapters chained")
    workflow = scene_workflow(
        SceneIpAdapterParams(
            checkpoint=_CHECKPOINT,
            positive="a tavern",
            negative="blurry",
            seed=3,
            identities=[_identity("lead_a.png", 0.65), _identity("lead_b.png", 0.5)],
        )
    )
    assert workflow["13"]["inputs"]["model"] == ["4", 0]
    assert workflow["15"]["inputs"]["model"] == ["13", 0]
    assert workflow["3"]["inputs"]["model"] == ["15", 0]
    assert workflow["12"]["inputs"]["image"] == "lead_a.png"
    assert workflow["14"]["inputs"]["image"] == "lead_b.png"
    print("  [OK] Sampler consumes the second adapter")


def test_scene_workflow_ignores_a_third_identity() -> None:
    """A third portrait is not stacked into the graph."""
    print("\n[TEST] scene_workflow - third identity ignored")
    workflow = scene_workflow(
        SceneIpAdapterParams(
            checkpoint=_CHECKPOINT,
            positive="p",
            negative="n",
            seed=1,
            identities=[
                _identity("a.png", 0.65),
                _identity("b.png", 0.5),
                _identity("c.png", 0.4),
            ],
        )
    )
    assert "16" not in workflow
    assert workflow["3"]["inputs"]["model"] == ["15", 0]
    print("  [OK] Only two adapters in the graph")


def test_reactor_swap_workflow_wires_one_face() -> None:
    """The swap graph loads the scene and one portrait, then saves."""
    print("\n[TEST] reactor_swap_workflow - one face")
    workflow = reactor_swap_workflow(
        ReactorSwapParams(
            scene_image="scene_cur.png",
            source_image="aragorn.png",
            swap_model="inswapper_128.onnx",
            face_index=2,
        )
    )
    assert workflow["3"]["class_type"] == "ReActorFaceSwap"
    assert workflow["3"]["inputs"]["input_faces_index"] == "2"
    assert workflow["3"]["inputs"]["swap_model"] == "inswapper_128.onnx"
    assert workflow["4"]["class_type"] == "SaveImage"
    print("  [OK] Face index and swap model patched")


def test_split_likeness_takes_two_leads() -> None:
    """The first two portraited likenesses are leads; the rest are swaps."""
    print("\n[TEST] split_likeness - two leads")
    people = [
        ShotPerson(name="Aragorn", portrait_url="a.png", use_likeness=True),
        ShotPerson(name="Frodo Baggins", portrait_url="f.png", use_likeness=True),
        ShotPerson(name="Gandalf the Grey", portrait_url="g.png", use_likeness=True),
        ShotPerson(name="a hooded stranger", use_likeness=True),
    ]
    leads, swaps = split_likeness(people)
    assert [person.name for person in leads] == ["Aragorn", "Frodo Baggins"]
    assert [person.name for person in swaps] == ["Gandalf the Grey"]
    print("  [OK] Extra without a portrait is not a swap target")


def run_all_tests() -> None:
    """Run all scene workflow tests."""
    test_scene_workflow_defaults_to_landscape()
    test_scene_workflow_chains_two_ipadapters()
    test_scene_workflow_ignores_a_third_identity()
    test_reactor_swap_workflow_wires_one_face()
    test_split_likeness_takes_two_leads()
    print("\n[PASS] All story-image workflow tests passed.")


if __name__ == "__main__":
    run_all_tests()
