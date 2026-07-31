"""Describe an existing portrait into a Stable Diffusion prompt (image->prompt).

Sends an image to a local Ollama vision model via the native ``/api/generate``
API and returns a concise, comma-separated visual descriptor suitable as an SD
positive prompt. The model is requested with ``keep_alive: 0`` so it unloads
right after, freeing RAM before Stable Diffusion loads its checkpoint on the
same CPU-only box.

Best-effort: every failure returns ``None`` so the caller degrades gracefully.
"""

import base64
import logging
import re
from typing import Optional, Union

import requests

logger = logging.getLogger(__name__)

# Do not extend this instruction without testing it against a real image: some
# phrasings crash the vision model outright. See src/README.md (image->prompt).
_INSTRUCTION = (
    "Describe this character as a comma-separated list of short visual tags. "
    "No sentences."
)

# Impressions rather than anything drawable.
_NON_VISUAL_TAGS = frozenset({
    "intricate details", "majestic presence", "mythical creature",
    "fantasy setting", "fantasy art", "regal attire", "high quality",
    "detailed", "intricate", "majestic", "regal", "elegant", "beautiful",
    "stunning", "impressive", "masterpiece", "best quality",
    "grand", "opulent", "opulent setting", "luxurious", "atmospheric",
})

# Words naming the setting rather than the character. A portrait prompt that
# spends tags on the room gets a picture of the room: the subject shrinks and the
# species washes out.
_SCENE_WORDS = (
    "hall", "room", "chamber", "background", "backdrop", "setting", "chandelier",
    "audience", "crowd", "pillar", "column", "archway", "arch", "window",
    "curtain", "throne", "floor", "ceiling", "wall", "forest", "landscape",
    "sky", "dust", "glow", "lighting", "frame",
)

# Commentary the model narrates around what it sees.
_COMMENTARY_PREFIXES = (
    "reflecting", "adding", "matching", "creating", "suggesting", "typical",
    "which", "that ", "giving", "indicating", "highlighting", "capturing",
    "exuding", "conveying", "emphasising", "emphasizing", "making", "showing",
    "this description", "here is", "overall",
)

_MARKUP_RE = re.compile(r"[*_#`>]+")
_BULLET_RE = re.compile(r"^\s*[-*•]+\s*")

# A leading label such as "Skin Tone:" or "Eyewear or Accessories:".
_LABEL_RE = re.compile(r"^[A-Za-z][A-Za-z /&'-]{0,28}:\s*")

# "the skin is a rich" -> "rich skin": predicate before subject reads as a tag.
_COPULA_RE = re.compile(
    r"^(?P<subject>[\w'-]+(?:\s+[\w'-]+){0,2}?)\s+"
    r"(?:is|are|was|were|appears?|seems?|looks?|has|have)\s+"
    r"(?:a|an|the)?\s*(?P<predicate>.+)$",
    re.I,
)

# Subjects that say nothing: the tag is the predicate alone.
_EMPTY_SUBJECTS = frozenset({"character", "it", "they", "she", "he", "there", "figure", "person"})

# "with a slightly curved snout" -> "slightly curved snout".
_CONNECTIVE_RE = re.compile(r"^(?:with|in|wearing|holding)\s+(?:a|an|the)?\s*", re.I)

# Beyond this a fragment is narration. Dropped rather than truncated, which would
# invent a phrase the model never wrote.
_MAX_TAG_WORDS = 8

_PREAMBLE_RE = re.compile(r"^.{0,200}?\b(?:description|appearance|tags?)\b[^:]{0,40}:\s*", re.S)

# Commas, semicolons, sentence ends, newlines, bullets. Sentence ends matter as
# much as commas, or a clause and the next sentence merge and both tags are lost.
_SPLIT_RE = re.compile(r"[,;\n]+|\.\s+|\s+[-*•]\s+")

_ARTICLE_RE = re.compile(r"^(?:the|a|an|its|their|his|her)\s+", re.I)

# Roughly one 77-token encoder window, which is what keeps the prompt adhered to.
_MAX_TAGS = 18

# Cap the context window so vision-language models (e.g. qwen2.5vl) do not
# allocate a 32k KV cache - that balloons RAM to many GB and stalls on CPU. A
# single image describe needs very little context.
_NUM_CTX = 4096


def fetch_image_bytes(
    image_url: str,
    timeout: float = 30.0,
    ca_bundle: Optional[str] = None,
) -> Optional[bytes]:
    """Fetch raw image bytes from a URL (public Drupal files need no auth).

    Args:
        image_url: The image URL to fetch.
        timeout: Request timeout in seconds.
        ca_bundle: CA bundle to verify TLS against. The local Drupal's
            certificate is not in the default trust store, so without this an
            ``https://`` file URL fails verification.

    Returns:
        The image bytes, or ``None`` if the fetch fails or is empty.
    """
    verify: Union[bool, str] = ca_bundle if ca_bundle else True
    try:
        resp = requests.get(image_url, timeout=timeout, verify=verify)
        resp.raise_for_status()
    except requests.exceptions.SSLError as exc:
        # Logged distinctly: to the caller a cert failure is indistinguishable
        # from a missing file. Usually MKCERT_CA naming the wrong CA.
        logger.warning(
            "TLS verification failed fetching %s (CA bundle: %s): %s",
            image_url,
            ca_bundle or "system default",
            exc,
        )
        return None
    except requests.RequestException as exc:
        logger.warning("Could not fetch %s: %s", image_url, exc)
        return None
    return resp.content or None


def _tag_from_fragment(fragment: str) -> Optional[str]:
    """Turn one split fragment into a tag.

    Args:
        fragment: One comma/bullet-separated piece of the model's answer.

    Returns:
        The cleaned tag, or ``None`` for commentary, scenery, or narration.
    """
    text = _BULLET_RE.sub("", fragment.strip())
    text = _LABEL_RE.sub("", text).strip()
    text = _ARTICLE_RE.sub("", text).strip(" .")
    text = " ".join(text.split())
    if not text:
        return None

    lowered = text.lower()
    if lowered.startswith(_COMMENTARY_PREFIXES) or lowered in _NON_VISUAL_TAGS:
        return None
    if any(word in lowered for word in _SCENE_WORDS):
        return None

    match = _COPULA_RE.match(text)
    if match is not None:
        subject = match.group("subject").strip()
        predicate = match.group("predicate").strip(" .")
        text = predicate if subject.lower() in _EMPTY_SUBJECTS else f"{predicate} {subject}"

    text = _CONNECTIVE_RE.sub("", text).strip(" .")
    if not text or len(text.split()) > _MAX_TAG_WORDS:
        return None

    return text


def condense_to_tags(text: str, lead: str = "") -> str:
    """Reduce a vision model's answer to a short comma-separated tag prompt.

    Prose is normalised rather than trusted: a small vision model emits
    sentences, markdown, and preambles whatever the instruction says, and a long
    prompt dilutes the species until a dragonborn renders as a human. See
    src/README.md (image->prompt) for the measurements behind the limits.

    Args:
        text: The raw model output, in any shape.
        lead: Authoritative tags to place first (e.g. "green dragonborn"), taken
            from the character's own record and never dropped.

    Returns:
        A comma-separated tag prompt, or an empty string when nothing is usable.
    """
    body = _PREAMBLE_RE.sub("", _MARKUP_RE.sub("", text), count=1)

    tags: list[str] = []
    seen: set[str] = set()
    for raw in _SPLIT_RE.split(body):
        tag = _tag_from_fragment(raw)
        if tag is None:
            continue
        lowered = tag.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        tags.append(tag)

    leading = [part.strip() for part in lead.split(",") if part.strip()]
    for part in reversed(leading):
        if part.lower() in seen:
            tags.remove(next(t for t in tags if t.lower() == part.lower()))
        tags.insert(0, part)

    return ", ".join(tags[:_MAX_TAGS])


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
        context: Known character context (e.g. "a Chthonic Tiefling"), used to
            prime the model and placed first in the returned tags. It comes from
            the character's record, so it outranks the model's reading - which
            will report golden hair on a scaled head.
        timeout: Request timeout in seconds (CPU vision inference is slow).

    Returns:
        The comma-separated tag prompt, or ``None`` on any failure.
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
    except requests.RequestException as exc:
        logger.warning("Could not reach the vision model at %s: %s", base_url, exc)
        return None

    # Body before status: Ollama reports a dead runner as HTTP 500 with an
    # "error" key naming the cause, and raising on status discards it.
    try:
        payload = resp.json()
    except ValueError:
        payload = None

    if isinstance(payload, dict) and payload.get("error"):
        logger.error("Vision model %s failed: %s", model, payload["error"])
        return None
    if not resp.ok:
        logger.error("Vision model %s returned HTTP %s: %s", model, resp.status_code,
                     resp.text[:300])
        return None

    text = payload.get("response") if isinstance(payload, dict) else None
    if not isinstance(text, str):
        return None

    # "a Gold Dragonborn" -> "gold dragonborn": the article is not a tag.
    lead = _ARTICLE_RE.sub("", context.strip()).lower()

    return condense_to_tags(text, lead=lead) or None
