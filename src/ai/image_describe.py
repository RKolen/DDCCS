"""Describe an existing portrait into a Stable Diffusion prompt (image->prompt).

Sends an image to a local Ollama vision model via the native ``/api/generate``
API and returns a concise, comma-separated visual descriptor suitable as an SD
positive prompt. The model is requested with ``keep_alive: 0`` so it unloads
right after, freeing RAM before Stable Diffusion loads its checkpoint on the
same CPU-only box.

Best-effort: every failure returns ``None`` so the caller degrades gracefully.
"""

import base64
from typing import Optional

import requests

_INSTRUCTION = (
    "Describe this character's appearance in detail: skin tone, face, hair, "
    "eyes, any eyewear or accessories, build, clothing, colours, and mood. "
    "List every visible detail; keep it to visual description only."
)

# Cap the context window so vision-language models (e.g. qwen2.5vl) do not
# allocate a 32k KV cache - that balloons RAM to many GB and stalls on CPU. A
# single image describe needs very little context.
_NUM_CTX = 4096


def fetch_image_bytes(image_url: str, timeout: float = 30.0) -> Optional[bytes]:
    """Fetch raw image bytes from a URL (public Drupal files need no auth).

    Args:
        image_url: The image URL to fetch.
        timeout: Request timeout in seconds.

    Returns:
        The image bytes, or ``None`` if the fetch fails or is empty.
    """
    try:
        resp = requests.get(image_url, timeout=timeout)
        resp.raise_for_status()
    except requests.RequestException:
        return None
    return resp.content or None


def describe_image(
    base_url: str,
    model: str,
    image_bytes: bytes,
    context: str = "",
    timeout: float = 300.0,
) -> Optional[str]:
    """Describe an image into an SD prompt using an Ollama vision model.

    Args:
        base_url: Native Ollama API base URL (composed from OLLAMA_HOST/PORT).
        model: The vision model name (IMAGE_TO_PROMPT_MODEL).
        image_bytes: The raw image bytes to describe.
        context: Known character context (e.g. "a Chthonic Tiefling") used to
            prime the model so it reads fantasy features correctly - horns not
            wings, feline Tabaxi features, pointed elf ears, and so on.
        timeout: Request timeout in seconds (CPU vision inference is slow).

    Returns:
        The comma-separated descriptor, or ``None`` on any failure.
    """
    if not base_url or not model or not image_bytes:
        return None
    prompt = _INSTRUCTION
    if context:
        prompt = (
            f"This character is {context}. Reflect that species' features "
            f"accurately in your description. {_INSTRUCTION}"
        )
    encoded = base64.b64encode(image_bytes).decode("ascii")
    try:
        resp = requests.post(
            f"{base_url.rstrip('/')}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "images": [encoded],
                "stream": False,
                "keep_alive": 0,
                "options": {"num_ctx": _NUM_CTX},
            },
            timeout=timeout,
        )
        resp.raise_for_status()
        payload = resp.json()
    except (requests.RequestException, ValueError):
        return None
    text = payload.get("response") if isinstance(payload, dict) else None
    if not isinstance(text, str):
        return None
    return " ".join(text.split()) or None
