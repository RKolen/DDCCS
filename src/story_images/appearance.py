"""Fill in what a character looks like when the record does not say.

A scene prompt describes each person from their ``appearance`` tags. Those
come from the character's own record, which is the right source: it is what
the operator wrote down. But a record can be blank, and then the only visual
words reaching the renderer are lineage and class - "human wizard" - so
anything the portrait shows and the record omits (spectacles, a scar, a
particular hat) cannot survive into the scene.

The portrait itself is the fallback. Captioning it costs one vision call per
person, so it runs only for someone actually in frame whose record says
nothing, and never for someone the record already describes.
"""

import logging
from typing import List, Optional, Sequence

from src.ai.image_describe import condense_to_tags, describe_image, fetch_image_bytes
from src.config.config_types import ComfyUIConfig
from src.story_images.types import ShotPerson
from src.utils.string_utils import clip_to_budget

logger = logging.getLogger(__name__)

MAX_APPEARANCE_CHARS = 140


def _caption(
    comfyui: ComfyUIConfig, url: str, ca_bundle: str, context: str
) -> Optional[str]:
    """Caption one portrait into comma-separated visual tags.

    Args:
        comfyui: Config carrying the Ollama URL, vision model, and timeout.
        url: The portrait URL.
        ca_bundle: CA bundle for the local HTTPS certificate.
        context: Known facts about the character, to outrank a misreading.

    Returns:
        Tag text, or None when anything on the path failed.
    """
    image_bytes = fetch_image_bytes(url, ca_bundle=ca_bundle)
    if image_bytes is None:
        logger.warning("Could not fetch portrait for appearance: %s", url)
        return None
    described = describe_image(
        comfyui.ollama_url,
        comfyui.assets.image_to_prompt_model,
        image_bytes,
        context=context,
        timeout=comfyui.timeout,
    )
    if not described:
        return None
    return clip_to_budget(condense_to_tags(described), MAX_APPEARANCE_CHARS)


def fill_appearances(
    people: Sequence[ShotPerson], comfyui: ComfyUIConfig, ca_bundle: str
) -> List[ShotPerson]:
    """Describe portraits for in-frame people whose record says nothing.

    Args:
        people: The confirmed cast.
        comfyui: Config carrying the Ollama URL, vision model, and timeout.
        ca_bundle: CA bundle for the local HTTPS certificate.

    Returns:
        The same people, with blank appearances filled where possible. A
        person is returned unchanged when they already have an appearance,
        have no portrait, or the vision model is unavailable.
    """
    usable = bool(comfyui.ollama_url) and bool(comfyui.assets.image_to_prompt_model)
    out: List[ShotPerson] = []
    for person in people:
        if not usable or person.appearance.strip() or not person.portrait_url:
            out.append(person)
            continue
        tags = _caption(comfyui, person.portrait_url, ca_bundle, person.name)
        if tags:
            logger.info("Described %s from their portrait: %s", person.name, tags)
            person.appearance = tags
        out.append(person)
    return out
