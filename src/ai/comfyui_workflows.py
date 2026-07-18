"""ComfyUI workflow (API JSON) builders for portrait generation.

Rather than shipping an exported workflow file, the standard SDXL graph is built
programmatically so the prompt, seed, checkpoint, and size can be patched at
call time. The node ids/shape match ComfyUI's default text-to-image graph.
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
