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
from typing import Any, Dict


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
    # How strongly the reference pulls the render towards the original face.
    # Above ~0.9 the prompt stops mattering and every render is the reference
    # again; below ~0.5 the likeness washes out. 0.8 keeps the face while the
    # prompt still moves pose, clothing, and mood.
    weight: float = 0.8


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
