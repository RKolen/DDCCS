"""Run a story-scene ComfyUI render: two IPAdapters, then staggered swaps."""

import hashlib
import logging
from dataclasses import dataclass, replace
from typing import List, Optional, Sequence, Tuple

from src.ai.comfyui_client import ComfyUIClient
from src.ai.comfyui_workflows import (
    IdentityReference,
    ReactorSwapParams,
    SCENE_RENDER,
    SceneIpAdapterParams,
    reactor_swap_workflow,
    scene_workflow,
)
from src.ai.image_describe import fetch_image_bytes
from src.config.config_types import ComfyUIConfig
from src.story_images.types import ShotPerson

logger = logging.getLogger(__name__)

# Scene weights, deliberately below portrait strength. IPAdapter transfers
# composition as well as identity, so a portrait reference at 0.65 rebuilds
# the portrait - its framing, its pose, and any animal companion standing in
# it - instead of placing that face in the scene the prompt describes.
LEAD_WEIGHTS = (0.4, 0.3)


@dataclass
class SceneRenderResult:
    """What one scene render produced, and who got a likeness how.

    Two mechanisms put faces in a scene and they are not interchangeable, so
    the console has to be able to say which applied to whom: ``leads`` came
    from the IPAdapter (at most two), ``swapped`` from ReActor afterwards.
    """

    png: Optional[bytes]
    leads: List[str]
    swapped: List[str]


@dataclass
class SceneRenderRequest:
    """Inputs for one serialized scene render."""

    client: ComfyUIClient
    comfyui: ComfyUIConfig
    positive: str
    negative: str
    seed: int
    people: Sequence[ShotPerson]
    ca_bundle: str


def _upload_portrait(
    client: ComfyUIClient, url: str, ca_bundle: str, prefix: str
) -> Optional[str]:
    """Fetch a portrait URL and upload it to ComfyUI.

    Args:
        client: The ComfyUI client.
        url: The Drupal file URL.
        ca_bundle: CA bundle for local HTTPS.
        prefix: Filename prefix so leads and swaps do not collide.

    Returns:
        The stored ComfyUI filename, or None when fetch or upload failed.
    """
    image_bytes = fetch_image_bytes(url, ca_bundle=ca_bundle)
    if image_bytes is None:
        logger.warning("Could not fetch scene reference %s", url)
        return None
    digest = hashlib.sha256(image_bytes).hexdigest()[:16]
    return client.upload_image(f"{prefix}_{digest}.png", image_bytes)


def _upload_png(
    client: ComfyUIClient, data: bytes, prefix: str
) -> Optional[str]:
    """Upload raw PNG bytes to ComfyUI's input directory.

    Args:
        client: The ComfyUI client.
        data: PNG bytes.
        prefix: Filename prefix.

    Returns:
        The stored filename, or None on failure.
    """
    digest = hashlib.sha256(data).hexdigest()[:16]
    return client.upload_image(f"{prefix}_{digest}.png", data)


def split_likeness(
    people: Sequence[ShotPerson],
) -> Tuple[List[ShotPerson], List[ShotPerson]]:
    """Split checked likenesses into two IPAdapter leads and the swap rest.

    Args:
        people: The operator's in-frame list.

    Returns:
        (leads, swap_targets). Leads are at most two people with a portrait
        URL. Swap targets are the remaining likenesses that also have a URL.
    """
    eligible = [
        person
        for person in people
        if person.use_likeness and person.portrait_url
    ]
    return eligible[:2], eligible[2:]


def render_scene(request: SceneRenderRequest) -> SceneRenderResult:
    """Generate a scene PNG, applying likeness in series.

    Unloads ComfyUI after the base render and after every swap. A failed swap
    stops further swaps but still returns the last good PNG.

    Args:
        request: Client, config, prompts, seed, cast, and CA bundle.

    Returns:
        The PNG with the names that took each likeness path. ``png`` is None
        when the base render failed.
    """
    leads, swap_targets = split_likeness(request.people)
    identities = _upload_leads(request, leads)
    workflow = scene_workflow(
        SceneIpAdapterParams(
            checkpoint=request.comfyui.assets.checkpoint,
            positive=request.positive,
            negative=request.negative,
            seed=request.seed,
            identities=identities,
            render=replace(
                SCENE_RENDER,
                width=request.comfyui.assets.scene.width,
                height=request.comfyui.assets.scene.height,
            ),
        )
    )
    lead_names = [person.name for person in leads[: len(identities)]]
    png = request.client.generate_then_free(workflow)
    if png is None:
        return SceneRenderResult(png=None, leads=lead_names, swapped=[])
    if not request.comfyui.assets.supports_reactor() or not swap_targets:
        return SceneRenderResult(png=png, leads=lead_names, swapped=[])
    last_png, swapped = _swap_remaining(request, png, identities, swap_targets)
    return SceneRenderResult(png=last_png, leads=lead_names, swapped=swapped)


def _upload_leads(
    request: SceneRenderRequest, leads: Sequence[ShotPerson]
) -> List[IdentityReference]:
    """Upload up to two lead portraits for IPAdapter.

    Args:
        request: The render request (client and assets).
        leads: People selected as IPAdapter leads.

    Returns:
        Identity references that uploaded successfully.
    """
    identities: List[IdentityReference] = []
    # A scene needs the face adapter, never the full-image one: see
    # ComfyUIScene.ipadapter_model. With none configured the scene is
    # rendered from its prompt, which is right-without-likeness rather than
    # wrong-with-it.
    if not request.comfyui.assets.supports_scene_identity():
        return identities
    for index, person in enumerate(leads):
        uploaded = _upload_portrait(
            request.client, person.portrait_url, request.ca_bundle, f"scene_id{index}"
        )
        if uploaded is None:
            continue
        identities.append(
            IdentityReference(
                image=uploaded,
                ipadapter_model=request.comfyui.assets.scene.ipadapter_model,
                clip_vision=request.comfyui.assets.clip_vision,
                weight=LEAD_WEIGHTS[min(index, len(LEAD_WEIGHTS) - 1)],
            )
        )
    return identities


def _swap_remaining(
    request: SceneRenderRequest,
    png: bytes,
    identities: Sequence[IdentityReference],
    swap_targets: Sequence[ShotPerson],
) -> Tuple[bytes, List[str]]:
    """Apply ReActor swaps one face at a time.

    Args:
        request: The render request.
        png: The last good scene PNG.
        identities: IPAdapter leads already applied (for face index offset).
        swap_targets: Remaining likenesses with portraits.

    Returns:
        (last_png, names_successfully_swapped).
    """
    current = png
    swapped: List[str] = []
    reactor = request.comfyui.assets.reactor
    for index, person in enumerate(swap_targets):
        scene_name = _upload_png(request.client, current, "scene_cur")
        source_name = _upload_portrait(
            request.client, person.portrait_url, request.ca_bundle, f"scene_swap{index}"
        )
        if scene_name is None or source_name is None:
            logger.warning("Skipping swap for %s: upload failed", person.name)
            break
        result = request.client.generate_then_free(
            reactor_swap_workflow(
                ReactorSwapParams(
                    scene_image=scene_name,
                    source_image=source_name,
                    swap_model=reactor.swap_model,
                    face_index=len(identities) + index,
                    face_detection=reactor.face_detection,
                    node_type=reactor.node,
                )
            )
        )
        if result is None:
            logger.warning(
                "ReActor swap failed for %s; keeping the last scene", person.name
            )
            break
        # ReActor returns its input untouched when it finds no face at that
        # index - which is what a scene shot from behind gives it. Reporting
        # that as a likeness hid the failure behind a name in the review note.
        if result == current:
            logger.warning(
                "ReActor found no face at index %d for %s; nothing was swapped",
                len(identities) + index,
                person.name,
            )
            continue
        current = result
        swapped.append(person.name)
    return current, swapped
