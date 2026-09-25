"""ComfyUI workflow (API JSON) builders for portrait generation.

Rather than shipping an exported workflow file, the standard SDXL graph is built
programmatically so the prompt, seed, checkpoint, and size can be patched at
call time. The node ids/shape match ComfyUI's default text-to-image graph.

Two graphs are built here: plain text-to-image, and the same graph with IPAdapter
identity conditioning spliced in front of the sampler so a regeneration keeps the
character's likeness. See ``ipadapter_workflow`` for why that is a separate path
rather than an option on the first.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence


@dataclass
class RenderSettings:
    """Size and sampler settings for a portrait render.

    Defaults target an SDXL portrait; for an SD 1.5-class checkpoint on CPU,
    lower ``width``/``height`` (e.g. 512x768) to keep generation bounded.
    """

    width: int = 832
    height: int = 1216
    steps: int = 30
    cfg: float = 7.0


@dataclass
class Txt2ImgParams:
    """Per-request parameters for a text-to-image portrait workflow."""

    checkpoint: str
    positive: str
    negative: str
    seed: int
    render: RenderSettings = field(default_factory=RenderSettings)


# FaceID variant used for figure likeness. Plus v2 keeps the face while the
# prompt still decides wardrobe and pose.
FACEID_PRESET = "FACEID PLUS V2"


@dataclass
class FaceIdSettings:
    """How strongly the face-embedding adapter is applied."""

    preset: str = FACEID_PRESET
    lora_strength: float = 0.6


@dataclass
class WardrobeReference:
    """The whole-image adapter that carries palette and fabric.

    Deliberately weaker and released earlier than the face: held to the end
    it reproduces the reference's background rather than its clothes.
    """

    model: str
    weight: float = 0.45
    end_at: float = 0.55


@dataclass
class IdentityReference:
    """An uploaded reference portrait and the models that read its likeness.

    ``image`` is the filename ComfyUI returned from ``/upload/image``, not a
    path: the graph's LoadImage node resolves it inside ComfyUI's own input
    directory. The two model names are file names inside ComfyUI's
    ``models/ipadapter/`` and ``models/clip_vision/`` directories, configured
    per deployment (COMFYUI_IPADAPTER_MODEL / COMFYUI_CLIP_VISION) because the
    right pair depends on the checkpoint family.
    """

    image: str
    ipadapter_model: str
    clip_vision: str
    # Take likeness from a detected face's embedding rather than from the
    # whole reference image. A portrait where the face is a fiftieth of the
    # frame gave the CLIP-vision adapter almost no face to read, so it copied
    # the backdrop instead; FaceID finds the face itself, and carries no
    # scenery with it. It needs a face to find, so a non-human head - a
    # dragonborn's snout - raises "No face detected" and the caller falls
    # back to the whole-image adapter on a cropped reference.
    # Set to take likeness from a detected face's embedding instead of the
    # whole image; None uses the whole-image adapter alone.
    faceid: Optional[FaceIdSettings] = None
    # Whole-image adapter chained after FaceID, so the render keeps the
    # portrait's palette and fabric as well as its face. FaceID carries a
    # face embedding and nothing else: on its own it dressed a character
    # from the caption alone - "black coat" for a navy one - and its
    # human-face LoRA pulled an orc's green skin back towards human. The
    # wardrobe reference is what puts the picture back in.
    wardrobe: Optional[WardrobeReference] = None
    # How strongly the reference pulls the render towards the original face.
    # Above ~0.9 the prompt stops mattering and every render is the reference
    # again; below ~0.5 the likeness washes out. 0.8 keeps the face while the
    # prompt still moves pose, clothing, and mood.
    weight: float = 0.8
    # Fraction of the schedule after which the adapter lets go. Held to the
    # end it drags the reference's whole atmosphere across - a portrait's
    # arcane backdrop and all - which is exactly what a figure being cut out
    # of its background must not have.
    end_at: float = 1.0


@dataclass
class IpAdapterParams:
    """Per-request parameters for an identity-preserving portrait workflow."""

    checkpoint: str
    positive: str
    negative: str
    seed: int
    identity: IdentityReference
    render: RenderSettings = field(default_factory=RenderSettings)


def txt2img_workflow(params: Txt2ImgParams) -> Dict[str, Any]:
    """Build a standard SDXL text-to-image workflow in ComfyUI API-JSON form.

    Args:
        params: The checkpoint, prompts, seed, and sampler settings to patch
            into the graph.

    Returns:
        The workflow as a node-id -> node dict, ready to POST to /prompt.
    """
    return {
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": params.checkpoint},
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": params.render.width,
                "height": params.render.height,
                "batch_size": 1,
            },
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": params.positive, "clip": ["4", 1]},
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": params.negative, "clip": ["4", 1]},
        },
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": params.seed,
                "steps": params.render.steps,
                "cfg": params.render.cfg,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
            },
        },
        "8": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
        },
        "9": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": "portrait", "images": ["8", 0]},
        },
    }


def ipadapter_workflow(params: IpAdapterParams) -> Dict[str, Any]:
    """Build a text-to-image workflow conditioned on a reference portrait.

    This is the "same character, new picture" graph. A text prompt alone cannot
    hold a likeness - describing a portrait and re-rendering the description is
    lossy, and the face drifts a little further with every pass. IPAdapter
    instead conditions the model on the reference image's own CLIP-vision
    embedding, so identity survives regeneration while the prompt still steers
    pose, clothing, and mood.

    The graph is the text-to-image one with the identity chain spliced between
    the checkpoint and the sampler: the sampler's model input is rewired from the
    raw checkpoint to the IPAdapter-patched model. Everything else - prompts,
    latent, decode, save - is unchanged, which is why this builds on top of
    ``txt2img_workflow`` rather than restating it.

    Requires the ComfyUI-IPAdapter-plus custom nodes and both model files to be
    present in the ComfyUI install; callers check that before choosing this
    path, since a missing node fails the whole queued prompt.

    Args:
        params: The checkpoint, prompts, seed, sampler settings, and the
            uploaded reference image with its IPAdapter/CLIP-vision models.

    Returns:
        The workflow as a node-id -> node dict, ready to POST to /prompt.
    """
    workflow = txt2img_workflow(
        Txt2ImgParams(
            checkpoint=params.checkpoint,
            positive=params.positive,
            negative=params.negative,
            seed=params.seed,
            render=params.render,
        )
    )
    workflow.update(
        {
            "10": {
                "class_type": "IPAdapterModelLoader",
                "inputs": {"ipadapter_file": params.identity.ipadapter_model},
            },
            "11": {
                "class_type": "CLIPVisionLoader",
                "inputs": {"clip_name": params.identity.clip_vision},
            },
            "12": {
                "class_type": "LoadImage",
                "inputs": {"image": params.identity.image},
            },
            "13": {
                "class_type": "IPAdapterAdvanced",
                "inputs": {
                    "model": ["4", 0],
                    "ipadapter": ["10", 0],
                    "image": ["12", 0],
                    "clip_vision": ["11", 0],
                    "weight": params.identity.weight,
                    # Flat weight across the diffusion: the scheduled variants
                    # ("ease in/out") trade likeness for prompt adherence, which
                    # is the opposite of what this path is for.
                    "weight_type": "linear",
                    "combine_embeds": "concat",
                    "start_at": 0.0,
                    "end_at": 1.0,
                    "embeds_scaling": "V only",
                },
            },
        }
    )
    # Rewire the sampler onto the identity-patched model. Without this the
    # IPAdapter chain is built and then ignored - the render would come back
    # looking like a plain txt2img and the failure would be invisible.
    workflow["3"]["inputs"]["model"] = ["13", 0]

    return workflow


# Landscape scene size: larger than a 512x768 portrait, still SD 1.5-class so
# this CPU box can finish without loading an SDXL checkpoint.
SCENE_RENDER = RenderSettings(width=768, height=512, steps=30, cfg=7.0)
MAX_SCENE_IDENTITIES = 2


@dataclass
class SceneIpAdapterParams:
    """Per-request parameters for a scene with up to two identity references."""

    checkpoint: str
    positive: str
    negative: str
    seed: int
    identities: Sequence[IdentityReference]
    render: RenderSettings = field(default_factory=lambda: SCENE_RENDER)


@dataclass
class ReactorSwapParams:
    """Per-request parameters for one ReActor face swap.

    ``scene_image`` and ``source_image`` are ComfyUI input filenames, the same
    contract as ``IdentityReference.image``. ``face_index`` selects which
    detected face in the scene to replace (0-based, largest first).
    """

    scene_image: str
    source_image: str
    swap_model: str
    face_index: int = 0
    face_detection: str = "retinaface_resnet50"
    node_type: str = "ReActorFaceSwap"


def _adapter_node(
    model_ref: List[Any],
    image_node: str,
    weight: float,
    end_at: float = 1.0,
) -> Dict[str, Any]:
    """Build one IPAdapterAdvanced node dict.

    Args:
        model_ref: The previous model output, either the checkpoint or an
            earlier adapter.
        image_node: Node id of the LoadImage holding this identity.
        weight: How strongly this reference pulls the render.
        end_at: Fraction of the schedule after which the adapter lets go.

    Returns:
        The node dictionary.
    """
    return {
        "class_type": "IPAdapterAdvanced",
        "inputs": {
            "model": model_ref,
            "ipadapter": ["10", 0],
            "image": [image_node, 0],
            "clip_vision": ["11", 0],
            "weight": weight,
            "weight_type": "linear",
            "combine_embeds": "concat",
            "start_at": 0.0,
            "end_at": end_at,
            "embeds_scaling": "V only",
        },
    }


def scene_workflow(params: SceneIpAdapterParams) -> Dict[str, Any]:
    """Build a landscape text-to-image graph, optionally with two IPAdapters.

    The first two identities are chained: each adapter patches the previous
    model. A third identity is ignored here - remaining likenesses are applied
    afterwards by ``reactor_swap_workflow``, one face at a time, so the
    checkpoint and twenty-odd portraits are never resident together.

    Args:
        params: Checkpoint, prompts, seed, and zero to two identities.

    Returns:
        The workflow as a node-id -> node dict, ready to POST to /prompt.
    """
    workflow = txt2img_workflow(
        Txt2ImgParams(
            checkpoint=params.checkpoint,
            positive=params.positive,
            negative=params.negative,
            seed=params.seed,
            render=params.render,
        )
    )
    workflow["9"]["inputs"]["filename_prefix"] = "scene"

    identities = list(params.identities)[:MAX_SCENE_IDENTITIES]
    if not identities:
        return workflow

    first = identities[0]
    workflow["10"] = {
        "class_type": "IPAdapterModelLoader",
        "inputs": {"ipadapter_file": first.ipadapter_model},
    }
    workflow["11"] = {
        "class_type": "CLIPVisionLoader",
        "inputs": {"clip_name": first.clip_vision},
    }
    workflow["12"] = {
        "class_type": "LoadImage",
        "inputs": {"image": first.image},
    }
    workflow["13"] = _adapter_node(["4", 0], "12", first.weight)
    last_adapter = "13"

    if len(identities) > 1:
        second = identities[1]
        workflow["14"] = {
            "class_type": "LoadImage",
            "inputs": {"image": second.image},
        }
        workflow["15"] = _adapter_node(["13", 0], "14", second.weight)
        last_adapter = "15"

    workflow["3"]["inputs"]["model"] = [last_adapter, 0]
    return workflow


def reactor_swap_workflow(params: ReactorSwapParams) -> Dict[str, Any]:
    """Build a one-face ReActor swap graph.

    Load the current scene and one portrait, swap a single detected face, save.
    Callers run this once per remaining likeness and unload models between
    calls. A missing ReActor node fails the queued prompt, so callers must
    check ``supports_reactor`` first and treat a failed generate as "skip the
    rest", never as a failed scene.

    Args:
        params: Scene filename, portrait filename, swap model, and face index.

    Returns:
        The workflow as a node-id -> node dict, ready to POST to /prompt.
    """
    return {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": params.scene_image},
        },
        "2": {
            "class_type": "LoadImage",
            "inputs": {"image": params.source_image},
        },
        "3": {
            "class_type": params.node_type,
            "inputs": {
                "enabled": True,
                "input_image": ["1", 0],
                "source_image": ["2", 0],
                "swap_model": params.swap_model,
                "facedetection": params.face_detection,
                "face_restore_model": "none",
                "face_restore_visibility": 1.0,
                "codeformer_weight": 0.5,
                "detect_gender_source": "no",
                "detect_gender_input": "no",
                "input_faces_index": str(params.face_index),
                "source_faces_index": "0",
                "console_log_level": 1,
            },
        },
        "4": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": "scene_swap", "images": ["3", 0]},
        },
    }

@dataclass
class RegionImages:
    """The scene being painted into, and the mask marking where."""

    scene: str
    mask: str


@dataclass
class InpaintSettings:
    """Sampler and mask settings for one region pass."""

    # Below the level where the region is regenerated rather than edited. At
    # 0.92 each pass repainted its own background and the environment came
    # back as a different room in every box.
    denoise: float = 0.72
    steps: int = 28
    cfg: float = 7.0
    feather: int = 24


@dataclass
class RegionPrompts:
    """The single-character prompts for one region pass."""

    positive: str
    negative: str


@dataclass
class PoseControl:
    """An OpenPose control image and how hard it constrains the render."""

    image: str
    model: str
    strength: float = 0.85


@dataclass
class RegionInpaintParams:
    """One character painted into one region of an existing scene.

    ``conditioning`` bundles what steers the pass: the prompts, the optional
    portrait, and the optional skeleton. Region rendering only works because
    the prompt here names one person - anything shared across characters
    leaks onto all of them.
    """

    checkpoint: str
    images: RegionImages
    prompts: RegionPrompts
    seed: int
    settings: InpaintSettings = field(default_factory=InpaintSettings)
    identity: Optional[IdentityReference] = None
    pose: Optional[PoseControl] = None


def region_inpaint_workflow(params: RegionInpaintParams) -> Dict[str, Any]:
    """Repaint one masked region from a prompt naming a single character.

    This is what makes per-character attributes stick. A prompt listing six
    people gives Stable Diffusion no way to bind "halfling" to one of them, so
    every tag lands on every figure - two named people are enough to produce
    the same face twice. Here the prompt describes one person and only their
    region is denoised, so nothing can leak onto anyone else.

    The mask is feathered: a hard boundary leaves a visible rectangle where
    the new figure meets the scene it was painted into.

    Node ids 10-13 are the identity chain, matching ``scene_workflow``, since
    ``_adapter_node`` refers to the loaders at those ids.

    Args:
        params: Scene and mask filenames, the single-character prompts, seed,
            and an optional portrait to condition likeness on.

    Returns:
        The workflow as a node-id -> node dict, ready to POST to /prompt.
    """
    workflow: Dict[str, Any] = {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": params.checkpoint},
        },
        "2": {"class_type": "LoadImage", "inputs": {"image": params.images.scene}},
        "3": {
            "class_type": "LoadImageMask",
            "inputs": {"image": params.images.mask, "channel": "red"},
        },
        "4": {
            "class_type": "FeatherMask",
            "inputs": {
                "mask": ["3", 0],
                "left": params.settings.feather,
                "top": params.settings.feather,
                "right": params.settings.feather,
                "bottom": params.settings.feather,
            },
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": params.prompts.positive, "clip": ["1", 1]},
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": params.prompts.negative, "clip": ["1", 1]},
        },
        "7": {
            "class_type": "VAEEncode",
            "inputs": {"pixels": ["2", 0], "vae": ["1", 2]},
        },
        "8": {
            "class_type": "SetLatentNoiseMask",
            "inputs": {"samples": ["7", 0], "mask": ["4", 0]},
        },
        "9": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0],
                "positive": ["5", 0],
                "negative": ["6", 0],
                "latent_image": ["8", 0],
                "seed": params.seed,
                "steps": params.settings.steps,
                "cfg": params.settings.cfg,
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "denoise": params.settings.denoise,
            },
        },
        "14": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["9", 0], "vae": ["1", 2]},
        },
        "15": {
            "class_type": "SaveImage",
            "inputs": {"filename_prefix": "scene_region", "images": ["14", 0]},
        },
    }

    pose = params.pose
    if pose is not None:
        # The skeleton is what stops a masked rectangle over an empty room
        # from being filled with more room: it asserts a figure of a given
        # height stands here, so denoise can rise without the background
        # following it.
        workflow["16"] = {
            "class_type": "ControlNetLoader",
            "inputs": {"control_net_name": pose.model},
        }
        workflow["17"] = {
            "class_type": "LoadImage",
            "inputs": {"image": pose.image},
        }
        workflow["18"] = {
            "class_type": "ControlNetApplyAdvanced",
            "inputs": {
                "positive": ["5", 0],
                "negative": ["6", 0],
                "control_net": ["16", 0],
                "image": ["17", 0],
                "strength": pose.strength,
                "start_percent": 0.0,
                "end_percent": 1.0,
            },
        }
        workflow["9"]["inputs"]["positive"] = ["18", 0]
        workflow["9"]["inputs"]["negative"] = ["18", 1]

    identity = params.identity
    if identity is not None:
        workflow["10"] = {
            "class_type": "IPAdapterModelLoader",
            "inputs": {"ipadapter_file": identity.ipadapter_model},
        }
        workflow["11"] = {
            "class_type": "CLIPVisionLoader",
            "inputs": {"clip_name": identity.clip_vision},
        }
        workflow["12"] = {
            "class_type": "LoadImage",
            "inputs": {"image": identity.image},
        }
        workflow["13"] = _adapter_node(["1", 0], "12", identity.weight)
        # Mask the adapter to the same region, or this portrait conditions the
        # whole canvas and undoes the isolation the mask just bought.
        workflow["13"]["inputs"]["attn_mask"] = ["4", 0]
        workflow["9"]["inputs"]["model"] = ["13", 0]

    return workflow

@dataclass
class FigureParams:
    """One character rendered alone, at the checkpoint's native resolution.

    Inpainting a character into a slice of a wide canvas gives them almost no
    latent area - a 192px column of a 1152px frame is 24 latents wide, and a
    face inside it about five. That is why those figures came out waxy and
    flat however good the conditioning was. Rendering each one on their own
    full-size canvas gives the sampler its whole budget for a single person;
    scale and placement become a compositing step afterwards.
    """

    checkpoint: str
    positive: str
    negative: str
    seed: int
    render: RenderSettings = field(default_factory=lambda: SCENE_RENDER)
    identity: Optional[IdentityReference] = None
    pose: Optional[PoseControl] = None


def figure_workflow(params: FigureParams) -> Dict[str, Any]:
    """Build a single-character text-to-image graph on a plain backdrop.

    The backdrop is asked for flatly so the figure can be cut out cleanly and
    composited into a scene rendered separately.

    Args:
        params: Checkpoint, single-subject prompts, seed, size, and optional
            identity and pose conditioning.

    Returns:
        The workflow as a node-id -> node dict, ready to POST to /prompt.
    """
    workflow = txt2img_workflow(
        Txt2ImgParams(
            checkpoint=params.checkpoint,
            positive=params.positive,
            negative=params.negative,
            seed=params.seed,
            render=params.render,
        )
    )
    workflow["9"]["inputs"]["filename_prefix"] = "figure"

    if params.pose is not None:
        workflow["16"] = {
            "class_type": "ControlNetLoader",
            "inputs": {"control_net_name": params.pose.model},
        }
        workflow["17"] = {
            "class_type": "LoadImage",
            "inputs": {"image": params.pose.image},
        }
        workflow["18"] = {
            "class_type": "ControlNetApplyAdvanced",
            "inputs": {
                "positive": ["6", 0],
                "negative": ["7", 0],
                "control_net": ["16", 0],
                "image": ["17", 0],
                "strength": params.pose.strength,
                "start_percent": 0.0,
                "end_percent": 1.0,
            },
        }
        workflow["3"]["inputs"]["positive"] = ["18", 0]
        workflow["3"]["inputs"]["negative"] = ["18", 1]

    identity = params.identity
    if identity is not None and identity.faceid is not None:
        workflow["12"] = {
            "class_type": "LoadImage",
            "inputs": {"image": identity.image},
        }
        workflow["20"] = {
            "class_type": "IPAdapterUnifiedLoaderFaceID",
            "inputs": {
                "model": ["4", 0],
                "preset": identity.faceid.preset,
                "lora_strength": identity.faceid.lora_strength,
                # Insightface detection on the GPU faulted the ROCm context
                # ("illegal memory access") and took the next render with it.
                # It is a small detector; CPU costs a moment and cannot.
                "provider": "CPU",
            },
        }
        workflow["21"] = {
            "class_type": "IPAdapterFaceID",
            "inputs": {
                "model": ["20", 0],
                "ipadapter": ["20", 1],
                "image": ["12", 0],
                "weight": identity.weight,
                "weight_faceidv2": identity.weight * 2.0,
                "weight_type": "linear",
                "combine_embeds": "concat",
                "start_at": 0.0,
                "end_at": identity.end_at,
                "embeds_scaling": "V only",
            },
        }
        workflow["3"]["inputs"]["model"] = ["21", 0]
        wardrobe = identity.wardrobe
        if wardrobe is not None:
            workflow["10"] = {
                "class_type": "IPAdapterModelLoader",
                "inputs": {"ipadapter_file": wardrobe.model},
            }
            workflow["11"] = {
                "class_type": "CLIPVisionLoader",
                "inputs": {"clip_name": identity.clip_vision},
            }
            workflow["13"] = _adapter_node(
                ["21", 0], "12", wardrobe.weight, wardrobe.end_at
            )
            workflow["3"]["inputs"]["model"] = ["13", 0]
        return workflow

    if identity is not None:
        workflow["10"] = {
            "class_type": "IPAdapterModelLoader",
            "inputs": {"ipadapter_file": identity.ipadapter_model},
        }
        workflow["11"] = {
            "class_type": "CLIPVisionLoader",
            "inputs": {"clip_name": identity.clip_vision},
        }
        workflow["12"] = {
            "class_type": "LoadImage",
            "inputs": {"image": identity.image},
        }
        workflow["13"] = _adapter_node(
            ["4", 0], "12", identity.weight, identity.end_at
        )
        workflow["3"]["inputs"]["model"] = ["13", 0]

    return workflow
