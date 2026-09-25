"""Cut rendered figures out of their own canvas and place them in a scene.

Inpainting a character into a slice of a wide frame gives them almost no
latent area to exist in - a 192px column of a 1152px canvas is 24 latents
wide, and a face inside it about five - which is why those figures came back
waxy and flat no matter how well they were conditioned.

So each character is rendered alone at the checkpoint's native size, where
the sampler spends its whole budget on one person, then cut out and pasted
into the environment at the height their region asks for. Scale becomes a
compositing decision instead of something the prompt has to talk the model
into.
"""

import io
import logging
from typing import List, Optional, Sequence, Tuple

from PIL import Image
from rembg import remove

from src.story_images.regions import Region

logger = logging.getLogger(__name__)

# Alpha below this is treated as background when trimming to the subject.
ALPHA_FLOOR = 8

# How far a pasted figure is darkened towards the scene, so a bright cutout
# does not sit on a dim room looking like a sticker.
SHADOW_STRENGTH = 0.22

# Fraction of a portrait's height kept when cropping it down to the head.
# Portraits are framed head-up, so the top third holds the head on every one
# measured; more than this starts pulling in torso and backdrop again.
HEAD_FRACTION = 0.38


def cut_out(png: bytes) -> Optional[bytes]:
    """Remove the backdrop from a rendered figure.

    Args:
        png: The figure render.

    Returns:
        RGBA PNG bytes with the backdrop transparent, or None when removal
        failed.
    """
    try:
        cut = remove(png)
    except (OSError, ValueError, RuntimeError) as err:
        logger.warning("Background removal failed: %s", err)
        return None
    return bytes(cut) if cut else None


def trim_to_subject(rgba: bytes, name: str = "figure") -> Optional[Image.Image]:
    """Crop a cutout down to the pixels that are actually the figure.

    The render is a full canvas with a person somewhere in it; pasting that
    whole canvas would scale the empty margins as if they were the character.

    A subject touching the canvas edge was cut off by the render, and cropping
    hides that: the truncated body is scaled to full region height and stood on
    the ground line looking merely wrong rather than obviously broken. It is
    reported instead.

    Args:
        rgba: RGBA PNG bytes.
        name: Whose figure this is, for the warning.

    Returns:
        The cropped image, or None when nothing opaque remains.
    """
    with Image.open(io.BytesIO(rgba)) as image:
        figure = image.convert("RGBA")
        opaque = figure.getchannel("A").point(
            [0] * (ALPHA_FLOOR + 1) + [255] * (255 - ALPHA_FLOOR)
        )
        box = opaque.getbbox()
        if box is None:
            return None
        _warn_if_clipped(box, figure.size, name)
        return figure.crop(box)


def _warn_if_clipped(
    box: Tuple[int, int, int, int], size: Tuple[int, int], name: str
) -> None:
    """Report any canvas edge the subject runs off.

    Args:
        box: The subject's bounding box.
        size: The render canvas size.
        name: Whose figure this is.
    """
    left, top, right, bottom = box
    canvas_width, canvas_height = size
    edges = [
        edge
        for edge, touching in (
            ("top", top <= 0),
            ("bottom", bottom >= canvas_height),
            ("left", left <= 0),
            ("right", right >= canvas_width),
        )
        if touching
    ]
    if edges:
        logger.warning(
            "%s was cut off by the render canvas (%s); the cutout is a "
            "truncated body",
            name,
            ", ".join(edges),
        )


def place(
    scene_png: bytes, figures: Sequence[Tuple[Region, bytes]]
) -> Tuple[bytes, List[str]]:
    """Scale each cutout to its region and paste it into the scene.

    Height is matched to the region and width follows the figure's own aspect
    ratio, so a halfling ends up short rather than squashed.

    Args:
        scene_png: The rendered environment.
        figures: (region, rgba cutout) pairs, in paint order.

    Returns:
        (composited png, names placed).
    """
    with Image.open(io.BytesIO(scene_png)) as base:
        scene = base.convert("RGBA")

    placed: List[str] = []
    for region, rgba in figures:
        subject = trim_to_subject(rgba, region.name)
        if subject is None:
            logger.warning("Nothing to place for %s: cutout was empty", region.name)
            continue

        scale = region.height / subject.height
        width = max(1, int(subject.width * scale))
        sized = subject.resize((width, region.height), Image.Resampling.LANCZOS)

        # Centre on the region and stand on its floor, so everyone shares the
        # ground line the layout gave them.
        left = region.left + (region.width - width) // 2
        scene.alpha_composite(sized, (max(0, left), region.top))
        placed.append(region.name)

    buffer = io.BytesIO()
    scene.convert("RGB").save(buffer, format="PNG")
    return buffer.getvalue(), placed


def head_crop(png: bytes, fraction: float = HEAD_FRACTION) -> Optional[bytes]:
    """Crop a portrait to the head, squared around its centre.

    For a face the detector cannot find - a dragonborn's snout, a beast's
    muzzle - FaceID is unavailable and the whole-image adapter is all there
    is. Handed a whole portrait it copies the backdrop: a forest came across
    intact while the head arrived plated and featureless. Cropping to the head
    leaves that adapter something that is mostly face.

    Args:
        png: The portrait.
        fraction: How much of the height, from the top, holds the head.

    Returns:
        PNG bytes of the crop, or None when the image could not be read.
    """
    try:
        with Image.open(io.BytesIO(png)) as raw:
            image = raw.convert("RGB")
            keep = max(1, int(image.height * fraction))
            side = min(image.width, keep)
            left = (image.width - side) // 2
            cropped = image.crop((left, 0, left + side, keep))
            buffer = io.BytesIO()
            cropped.save(buffer, format="PNG")
            return buffer.getvalue()
    except (OSError, ValueError) as err:
        logger.warning("Could not crop a reference to its head: %s", err)
        return None
