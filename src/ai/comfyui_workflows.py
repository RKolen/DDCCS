"""ComfyUI workflow (API JSON) builders for portrait generation.

Rather than shipping an exported workflow file, the standard SDXL graph is built
programmatically so the prompt, seed, checkpoint, and size can be patched at
call time. The node ids/shape match ComfyUI's default text-to-image graph.
"""

from typing import Any, Dict


def txt2img_workflow(
    checkpoint: str,
    positive: str,
    negative: str,
    seed: int,
    width: int = 832,
    height: int = 1216,
    steps: int = 30,
    cfg: float = 7.0,
) -> Dict[str, Any]:
    """Build a standard SDXL text-to-image workflow in ComfyUI API-JSON form.

    Args:
        checkpoint: The SDXL checkpoint filename as ComfyUI sees it.
        positive: The positive prompt.
        negative: The negative prompt.
        seed: The sampler seed.
        width: Output width (SDXL portrait default).
        height: Output height (SDXL portrait default).
        steps: Sampler steps.
        cfg: Classifier-free guidance scale.

    Returns:
        The workflow as a node-id -> node dict, ready to POST to /prompt.
    """
    return {
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": checkpoint},
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": width, "height": height, "batch_size": 1},
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": positive, "clip": ["4", 1]},
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": negative, "clip": ["4", 1]},
        },
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
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
