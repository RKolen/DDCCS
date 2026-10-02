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

from PIL import Image, ImageDraw, ImageFilter, ImageStat
from rembg import remove

from src.story_images.regions import Region

logger = logging.getLogger(__name__)

# Alpha below this is treated as background when trimming to the subject.
ALPHA_FLOOR = 8

# How far a figure's colour is pulled towards the scene behind it. Every
# figure is rendered under even studio light on grey, so pasted unchanged a
# cast stood in a night street lit like a catalogue shoot. Not 1.0: a subject
# reads as the subject because it is a little brighter than its backdrop.
LIGHT_MATCH = 0.5
# Brightness gain limits, so a near-black scene dims a figure without
# erasing it and a bright one cannot bleach it.
MIN_GAIN, MAX_GAIN = 0.35, 1.1

# The contact shadow: a soft dark ellipse where the feet meet the ground.
# Without one nothing connects a cutout to the floor, which is most of what
# makes it look like it is floating. Sized from the feet, not the figure, so
# a spread cloak does not cast a puddle.
SHADOW_OPACITY = 150
SHADOW_SPREAD = 1.4
SHADOW_FLATNESS = 0.16
FEET_BAND = 0.04

# A one-pixel erode and a slight blur on the cutout's alpha. rembg's edge is
# crisper than anything the scene renderer paints, and the hard line reads as
# a sticker even when the light matches.
EDGE_BLUR = 0.8

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
        left = max(0, region.left + (region.width - width) // 2)
        sized = match_light(soften_edge(sized), scene, (left, region.top))
        cast_contact_shadow(scene, sized, (left, region.top))
        scene.alpha_composite(sized, (left, region.top))
        placed.append(region.name)

    buffer = io.BytesIO()
    scene.convert("RGB").save(buffer, format="PNG")
    return buffer.getvalue(), placed


def soften_edge(figure: Image.Image) -> Image.Image:
    """Take the cut-out line off a figure's edge.

    Args:
        figure: An RGBA cutout.

    Returns:
        The same figure with its alpha eroded a pixel and feathered.
    """
    alpha = figure.getchannel("A").filter(ImageFilter.MinFilter(3))
    softened = figure.copy()
    softened.putalpha(alpha.filter(ImageFilter.GaussianBlur(EDGE_BLUR)))
    return softened


def match_light(
    figure: Image.Image, scene: Image.Image, at: Tuple[int, int],
    strength: float = LIGHT_MATCH,
) -> Image.Image:
    """Pull a figure's colour towards the part of the scene it stands in.

    Brightness moves `strength` of the way to the backdrop's, by one gain
    shared by every channel. Hue is never touched: matching channels
    separately, or borrowing the backdrop's colour cast, turned a purple skin
    green or grey against a dark blue alley, and skin colour is part of who a
    character is.

    Args:
        figure: An RGBA cutout, already at its pasted size.
        scene: The RGBA scene it will be pasted into.
        at: Where its top-left corner will land.
        strength: 0 leaves the figure alone, 1 matches the backdrop's mean.

    Returns:
        The relit figure, alpha unchanged.
    """
    alpha = figure.getchannel("A")
    if alpha.getbbox() is None:
        return figure
    left, top = at
    behind = scene.crop((left, top, left + figure.width, top + figure.height))
    gain = _brightness_gain(
        ImageStat.Stat(figure.convert("RGB"), mask=alpha).mean,
        ImageStat.Stat(behind.convert("RGB")).mean,
        strength,
    )
    relit = figure.convert("RGB").point(
        [min(255, int(value * gain)) for value in range(256)] * 3).convert("RGBA")
    relit.putalpha(alpha)
    return relit


def _brightness(rgb: Sequence[float]) -> float:
    """Perceived brightness of an (r, g, b) mean, Rec. 601 weights."""
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def _brightness_gain(
    own: Sequence[float], around: Sequence[float], strength: float,
) -> float:
    """The one multiplier that moves a figure's brightness towards a scene's.

    Args:
        own: The figure's mean per channel.
        around: The backdrop's mean per channel.
        strength: How far of the way to move.

    Returns:
        A gain held inside MIN_GAIN..MAX_GAIN; 1.0 for a black figure.
    """
    mine, theirs = _brightness(own), _brightness(around)
    if mine <= 0:
        return 1.0
    return min(max((mine + (theirs - mine) * strength) / mine, MIN_GAIN), MAX_GAIN)


def _feet_span(figure: Image.Image) -> Optional[Tuple[int, int]]:
    """Where a figure's feet are across its width.

    Args:
        figure: An RGBA cutout.

    Returns:
        (left, right) of the opaque pixels in its bottom band, or None.
    """
    band = max(2, int(figure.height * FEET_BAND))
    feet = figure.getchannel("A").crop(
        (0, figure.height - band, figure.width, figure.height)).getbbox()
    return None if feet is None else (feet[0], feet[2])


def _shadow_sprite(wide: int) -> Image.Image:
    """A soft, flat, dark ellipse `wide` pixels across, with blur room.

    Args:
        wide: Width of the ellipse before blurring.

    Returns:
        The RGBA shadow, its centre being the ellipse's centre.
    """
    tall = max(2, int(wide * SHADOW_FLATNESS))
    blur = max(1, tall // 2)
    pad = blur * 3
    shadow = Image.new("RGBA", (wide + pad * 2, tall + pad * 2), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).ellipse(
        (pad, pad, pad + wide, pad + tall), fill=(0, 0, 0, SHADOW_OPACITY))
    return shadow.filter(ImageFilter.GaussianBlur(blur))


def cast_contact_shadow(
    scene: Image.Image, figure: Image.Image, at: Tuple[int, int],
) -> None:
    """Darken the ground where a figure's feet touch it, in place.

    Args:
        scene: The RGBA scene, drawn on directly.
        figure: The RGBA cutout about to be pasted.
        at: Where its top-left corner will land.
    """
    feet = _feet_span(figure)
    if feet is None:
        return
    shadow = _shadow_sprite(max(4, int((feet[1] - feet[0]) * SHADOW_SPREAD)))
    centre = at[0] + (feet[0] + feet[1]) // 2
    ground = at[1] + figure.height
    scene.alpha_composite(
        shadow, (max(0, centre - shadow.width // 2),
                 max(0, ground - shadow.height // 2)))


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
