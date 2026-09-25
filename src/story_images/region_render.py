"""Paint a scene one character at a time, each in their own region.

A single prompt naming several people cannot say which of them is the
halfling. Stable Diffusion has no mechanism to bind an attribute to one named
subject, so every tag lands on every figure - two names are enough to produce
the same face twice, and six produce six of the same elf in matching green.

So the scene is built in passes. First the environment with nobody in it,
then one masked inpaint per character whose prompt names only them. Nothing
can leak, because nothing else is in the prompt. Region height carries body
type as well: a halfling gets a shorter box than a dragonborn, which the
model cannot ignore the way it ignores the word.
"""

import hashlib
import logging
import struct
import zlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from src.ai.comfyui_client import ComfyUIClient
from src.ai.comfyui_workflows import (
    FigureParams,
    FaceIdSettings,
    IdentityReference,
    WardrobeReference,
    InpaintSettings,
    PoseControl,
    RegionImages,
    RegionInpaintParams,
    RegionPrompts,
    RenderSettings,
    figure_workflow,
    region_inpaint_workflow,
)
from src.config.config_types import ComfyUIConfig
from src.story_images.composite import cut_out, place
from src.story_images.pose import (
    figure_pose_png,
    openpose_png,
    pose_for_index,
    silhouette_png,
    visible_regions,
)
from src.story_images.framing import ANGLE_NEGATIVES, ANGLES
from src.story_images.regions import NEAR_DEPTH, Placement, Region, lay_out
from src.utils.string_utils import clip_tags
from src.story_images.types import ShotPerson

logger = logging.getLogger(__name__)

# Weight for a region's own portrait. Well above the whole-scene leads: there
# is no composition to protect when the render contains one person, so the
# adapter can be asked for the face rather than merely consulted about it.
REGION_IDENTITY_WEIGHT = 0.9

# Where the face adapter lets go. Held to the end it brings the portrait's
# whole backdrop with it, and a figure that arrives wrapped in its reference's
# scenery cannot be cut out cleanly.
FIGURE_IDENTITY_END = 0.7

# How far the mask is softened, in pixels, so no rectangle shows at the seam.
REGION_FEATHER = 24

# Extra mask above the figure, as a fraction of its height. The model paints
# at canvas scale rather than box scale, so a box sized exactly to a short
# character gets a full-size body with its head above the mask - painted
# nowhere, leaving the environment showing through at the neck.
REGION_HEADROOM = 0.22

# With a skeleton pinning the figure, denoise can be high enough to actually
# paint a person. Without one it had to stay low to protect the background,
# and half the regions came back as furniture.
REGION_DENOISE_POSED = 0.88
REGION_DENOISE_PLAIN = 0.72

# Canvas for a single figure. Native for SD 1.5, where the sampler is
# strongest, and roughly eight times the latent area a figure got when it was
# inpainted into a column of the scene.
FIGURE_RENDER = RenderSettings(width=512, height=768, steps=30, cfg=7.0)

# Asked of every figure render so the cutout has a clean edge to find. The
# ground matters as much as the backdrop: left to itself the model stands the
# character on a rock or a plinth, and background removal keeps it, so the
# figure arrives in the tavern on a little stone island.
# The style anchor matters more than anything else here. Without it the
# renderer has no reason to draw fantasy at all, and a wizard came back as a
# woman in a wool coat in a shopping centre. Wardrobe words are deliberately
# absent: "fully clothed, wearing boots" reads as modern dress.
# Short on purpose: every character here is spent from the same 77-token
# budget as the wardrobe. The head and costume clauses moved into
# region_prompt, which knows whether the wardrobe already covers the head.
# "dramatic lighting" is gone too - it threw contrast the cutout kept.
FIGURE_BACKDROP = (
    "plain grey backdrop, flat ground, fantasy illustration, digital painting, "
    "sharp focus"
)

# Negatives specific to a figure rendered alone for cutting out.
# "bare head" was here and cost every figure their clothes and shoes: the
# model reads "bare" as skin and applies it to the body, not the scalp.
# The backdrop terms earn their place: asked only for "plain grey", the
# model still drew a glowing mandala behind one figure and a heavy vignette
# behind another, and both are what rembg has to cut against. The signature
# terms are for the fake artist's mark it likes to letter into the corner.
FIGURE_NEGATIVE = (
    "pedestal, plinth, boulder, platform, podium, scenery, landscape, "
    "barefoot, nude, topless, undressed, "
    "modern clothing, contemporary, street clothes, coat, jeans, photograph, "
    "other people, crowd, bystanders, background figures, "
    "magic circle, glowing runes behind, halo, mandala, ornate background, "
    "vignette, patterned backdrop, "
    "watermark, signature, artist name, text, lettering, logo, border, frame, "
    "cropped feet, cut off feet, cropped head, feet out of frame"
)

# Said to every region. The framing negative bans rear views; this bans the
# other ways a figure goes wrong: arriving without a head, or with one nobody
# can see. A class word like "Fighter" pulls a full helm, and the face it
# hides is the face likeness and swapping both need.
# Kept narrow on purpose. "face mask" and "face covered" were here and made
# every face worse - and suppressed non-human features like a tiefling's -
# because a negative that vague pulls against faces in general.
REGION_NEGATIVE = (
    "cropped head, headless, out of frame, cut off at the neck, "
    "helmet, full helm, visor"
)


@dataclass
class RegionFraming:
    """How the figures are framed, shared by the layout and every region.

    ``placements`` is the operator's staging: where each character stands and
    how far back. Empty means evenly spaced at the front, which is what the
    layout did before staging existed - and which rendered every cast as a
    row of figures on one floor.
    """

    shot: str = "full"
    angle_terms: str = ""
    placements: Sequence[Placement] = field(default_factory=tuple)


@dataclass
class RegionInputs:
    """The images a region pass works from.

    ``portraits`` maps a character name to the filename their portrait was
    uploaded under, so each region conditions on its own face and no other.
    """

    scene_png: bytes
    portraits: Dict[str, str] = field(default_factory=dict)
    # Head crops of the same portraits, used only when FaceID finds no face.
    heads: Dict[str, str] = field(default_factory=dict)


@dataclass
class RegionRenderRequest:
    """Inputs for painting a cast into an already-rendered environment."""

    client: ComfyUIClient
    comfyui: ComfyUIConfig
    inputs: RegionInputs
    people: Sequence[ShotPerson]
    negative: str
    seed: int
    framing: RegionFraming = field(default_factory=RegionFraming)


def _chunk(tag: bytes, payload: bytes) -> bytes:
    """Frame one PNG chunk with its length and CRC.

    Args:
        tag: The four-byte chunk type.
        payload: The chunk body.

    Returns:
        The framed chunk.
    """
    return (
        struct.pack(">I", len(payload))
        + tag
        + payload
        + struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF)
    )


def mask_png(width: int, height: int, region: Region) -> bytes:
    """Render a white-on-black 8-bit greyscale mask marking one region.

    Written by hand rather than with an imaging library: the mask is two flat
    tones and a rectangle, which is not worth a dependency. Building it as an
    image still beats assembling one from mask nodes - one upload instead of a
    subgraph, and inspectable when a region lands somewhere unexpected.

    Args:
        width: Canvas width.
        height: Canvas height.
        region: The box to paint white.

    Returns:
        PNG bytes of the mask.
    """
    dark = bytes(width)
    rows = []
    for y in range(height):
        if region.top <= y < region.bottom:
            row = bytearray(dark)
            row[region.left : region.right] = b"\xff" * (region.right - region.left)
            rows.append(b"\x00" + bytes(row))
        else:
            rows.append(b"\x00" + dark)
    header = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", header)
        + _chunk(b"IDAT", zlib.compress(b"".join(rows), 6))
        + _chunk(b"IEND", b"")
    )


def png_size(data: bytes) -> Tuple[int, int]:
    """Read a PNG's pixel dimensions straight from its IHDR.

    Args:
        data: PNG bytes.

    Returns:
        (width, height).

    Raises:
        ValueError: When the bytes are not a PNG.
    """
    if len(data) < 24 or not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("not a PNG")
    width, height = struct.unpack(">II", data[16:24])
    return int(width), int(height)


def _with_headroom(region: Region, canvas_height: int) -> Region:
    """Grow a region upward so the figure's head has somewhere to land.

    Args:
        region: The figure's box.
        canvas_height: Canvas height, so the mask cannot run off the top.

    Returns:
        The region with headroom added above.
    """
    extra = int(region.height * REGION_HEADROOM)
    top = max(0, region.top - extra)
    return Region(
        name=region.name,
        left=region.left,
        top=top,
        width=region.width,
        height=min(region.bottom - top, canvas_height - top),
    )


# SD 1.5's text encoder reads 77 tokens. Past that ComfyUI splits the prompt
# into chunks and averages them, so every tag's pull is diluted - a 150-token
# prompt asked for a wardrobe and got half of one. Roughly four characters to
# a token, minus room for the fixed tail below.
# Budget for the wardrobe itself. The tail below and FIGURE_BACKDROP are
# spent from the same 77 tokens, so they are kept terse to leave the
# character description the larger share.
PROMPT_BUDGET_CHARS = 170

# Garments that cover a head. Deliberately about clothing only: "curved
# horns", "reptilian head" and "scales" are anatomy, and treating them as
# headwear would drop the guard that keeps a dragonborn's face visible.
HEADWEAR_WORDS = (
    "hat", "hood", "helm", "cap", "crown", "circlet", "veil", "coif",
    "turban", "headdress", "mask",
)


def covers_head(appearance: str) -> bool:
    """Whether a wardrobe description puts something on the head.

    Args:
        appearance: Comma-separated appearance tags.

    Returns:
        True when the tags name headwear.
    """
    low = appearance.lower()
    return any(word in low for word in HEADWEAR_WORDS)


def region_prompt(
    person: ShotPerson, angle_terms: str, posed: bool = False
) -> str:
    """Build the prompt for one region: this character and nobody else.

    Kept inside the encoder's budget, and stripped of the two contradictions
    that were fighting the wardrobe. "head uncovered" existed to stop a class
    word pulling a full helm over the face, but it argues with every hat and
    hood a caption names - so it is dropped when the wardrobe has one, and
    the face is asked for directly instead. "standing" is dropped when a pose
    skeleton is driving, which it contradicted outright.

    Args:
        person: The character to paint.
        angle_terms: Framing terms shared with the base scene.
        posed: Whether a pose skeleton conditions this render.

    Returns:
        A single-subject prompt within the token budget.
    """
    subject = person.appearance.strip() or person.action.strip()
    tail = ["solo", "full body in frame"]
    if not posed:
        tail.insert(1, "standing")
    tail.append("face visible" if covers_head(subject) else
                "head uncovered, face visible")
    if angle_terms:
        tail.append(angle_terms)
    fixed = ", ".join(tail)

    return ", ".join(
        bit for bit in (clip_tags(subject, PROMPT_BUDGET_CHARS), fixed) if bit
    )




def paint_regions(request: RegionRenderRequest) -> Tuple[bytes, List[str]]:
    """Paint each character into their own region of the scene.

    A failed region leaves the scene as it was and the run continues: one
    character who would not paint is better than losing the whole picture.

    Args:
        request: Client, config, the environment PNG, the cast, and framing.

    Returns:
        (final_png, names_painted).
    """
    width, height = png_size(request.inputs.scene_png)

    regions = lay_out(request.people, width, height, request.framing.shot,
                      request.framing.placements or None)
    pose_name = _upload_pose(request, width, height, regions)
    denoise = REGION_DENOISE_POSED if pose_name else REGION_DENOISE_PLAIN
    current = request.inputs.scene_png
    painted: List[str] = []

    for index, (person, region) in enumerate(zip(request.people, regions)):
        scene_name = _upload(request.client, current, f"region_scene{index}")
        # With a skeleton to follow, mask the figure rather than its box: a
        # rectangle repaints the backdrop too, and six of them side by side
        # read as six panels instead of one room.
        mask_bytes = (
            silhouette_png(width, height, region)
            if pose_name
            else mask_png(width, height, _with_headroom(region, height))
        )
        mask_name = _upload(request.client, mask_bytes, f"region_mask{index}")
        if scene_name is None or mask_name is None:
            logger.warning("Skipping %s: upload failed", person.name)
            continue

        result = request.client.generate_then_free(
            region_inpaint_workflow(
                RegionInpaintParams(
                    checkpoint=request.comfyui.assets.checkpoint,
                    images=RegionImages(scene=scene_name, mask=mask_name),
                    prompts=RegionPrompts(
                        positive=region_prompt(
                            person, request.framing.angle_terms,
                            posed=pose_name is not None,
                        ),
                        negative=f"{request.negative}, {REGION_NEGATIVE}",
                    ),
                    seed=request.seed + index,
                    settings=InpaintSettings(
                        feather=REGION_FEATHER, denoise=denoise
                    ),
                    identity=_identity_for(request, person),
                    pose=_pose_for(request, pose_name),
                )
            )
        )
        if result is None:
            logger.warning("Region paint failed for %s; scene left as it was", person.name)
            continue
        current = result
        painted.append(person.name)
        logger.info(
            "Painted %s into %dx%d at (%d,%d)",
            person.name,
            region.width,
            region.height,
            region.left,
            region.top,
        )
    return current, painted


def _upload_pose(
    request: RegionRenderRequest,
    width: int,
    height: int,
    regions: Sequence[Region],
) -> Optional[str]:
    """Draw and upload one skeleton image covering every region.

    All figures share a single control image: ControlNet conditions the whole
    frame, so one image per region would erase the others.

    Args:
        request: The render request.
        width: Canvas width.
        height: Canvas height.
        regions: The boxes to stand figures in.

    Returns:
        The uploaded filename, or None when pose control is unavailable.
    """
    if not request.comfyui.assets.pose.model:
        return None
    drawable = visible_regions(regions)
    if not drawable:
        return None
    return _upload(request.client, openpose_png(width, height, drawable), "region_pose")


def _pose_for(
    request: RegionRenderRequest, pose_name: Optional[str]
) -> Optional[PoseControl]:
    """Build the pose control for a region pass, when one is available.

    Args:
        request: The render request.
        pose_name: The uploaded skeleton filename, or None.

    Returns:
        The pose control, or None.
    """
    if pose_name is None:
        return None
    return PoseControl(
        image=pose_name,
        model=request.comfyui.assets.pose.model,
        strength=request.comfyui.assets.pose.strength,
    )


def _figure_pose(
    request: RegionRenderRequest, stance: str, index: int, facing: str = "",
    toward: str = "",
) -> Optional[PoseControl]:
    """Build the pose control for one figure's own canvas.

    The facing turns the skeleton itself. ControlNet obeys geometry, not
    adjectives: a figure drawn with both ears, both eyes and full-width
    shoulders is a front view, and "side profile view" in the prompt lost to
    it in every render until the skeleton was turned too.

    Args:
        request: The render request.
        stance: Which stance this character takes.
        index: Their position in the cast, to keep uploads distinct.
        facing: Which way they are turned, or empty to face the camera.
        toward: Which way along the frame that turn points.

    Returns:
        The pose control, or None when pose conditioning is unavailable.
    """
    if not request.comfyui.assets.pose.model:
        return None
    uploaded = _upload(
        request.client,
        figure_pose_png(FIGURE_RENDER.width, FIGURE_RENDER.height, stance,
                        facing, toward),
        f"figure_pose{index}",
    )
    if uploaded is None:
        return None
    return PoseControl(
        image=uploaded,
        model=request.comfyui.assets.pose.model,
        strength=request.comfyui.assets.pose.strength,
    )


def _identity_for(
    request: RegionRenderRequest, person: ShotPerson
) -> Optional[IdentityReference]:
    """Build the masked identity reference for one region, when there is one.

    Args:
        request: The render request, carrying uploaded portrait filenames.
        person: The character being painted.

    Returns:
        An identity reference, or None when this person has no usable portrait.
    """
    assets = request.comfyui.assets
    uploaded = request.inputs.portraits.get(person.name)
    if not uploaded or not person.use_likeness or not assets.supports_scene_identity():
        return None
    return IdentityReference(
        image=uploaded,
        ipadapter_model=assets.scene.ipadapter_model,
        clip_vision=assets.clip_vision,
        weight=REGION_IDENTITY_WEIGHT,
        end_at=FIGURE_IDENTITY_END,
        faceid=FaceIdSettings(),
        wardrobe=(
            WardrobeReference(model=assets.ipadapter_model)
            if assets.ipadapter_model
            else None
        ),
    )


def _fallback_identity(
    request: RegionRenderRequest, person: ShotPerson
) -> Optional[IdentityReference]:
    """Build the whole-image reference used when no face was detected.

    Args:
        request: The render request, carrying uploaded head crops.
        person: The character being painted.

    Returns:
        An identity reference over the head crop, or None when there is none.
    """
    assets = request.comfyui.assets
    head = request.inputs.heads.get(person.name)
    if not head or not person.use_likeness or not assets.supports_scene_identity():
        return None
    return IdentityReference(
        image=head,
        ipadapter_model=assets.scene.ipadapter_model,
        clip_vision=assets.clip_vision,
        weight=REGION_IDENTITY_WEIGHT,
        end_at=FIGURE_IDENTITY_END,
    )


def _upload(client: ComfyUIClient, data: bytes, prefix: str) -> Optional[str]:
    """Upload PNG bytes to ComfyUI's input directory.

    Args:
        client: The ComfyUI client.
        data: PNG bytes.
        prefix: Filename prefix.

    Returns:
        The stored filename, or None on failure.
    """
    digest = hashlib.sha256(data).hexdigest()[:16]
    return client.upload_image(f"{prefix}_{digest}.png", data)

def paint_order(
    cutouts: Sequence[Tuple[int, float, int, Region, bytes]]
) -> List[Tuple[Region, bytes]]:
    """Order figures furthest first, so a nearer one overdraws them.

    `place` pastes in sequence, so the last figure in wins every overlap.
    That used to be cast order, which meant whoever happened to be ticked
    last was painted on top - a character staged at the back could be pasted
    over one at the front, at a fraction of their height.

    An operator's number outranks depth. Depth decides apparent size, and
    apparent size is not distance here: a halfling at the front of the scene
    is smaller than an orc at the back, so pushing the small character
    forward to stop them being swallowed also shrinks everyone else's sense
    of the room. The two controls are separate because the two problems are.

    A figure nobody numbered sorts behind every numbered one and falls back
    to depth. Cast order breaks the last tie, so the same staging always
    paints the same way.

    Args:
        cutouts: (order, depth, cast index, region, rgba cutout) per figure,
            where order is 1 for the front-most and 0 for "use depth".

    Returns:
        (region, cutout) pairs, furthest first.
    """
    return [(region, cut) for _, _, _, region, cut in sorted(
        cutouts,
        key=lambda row: (1 if row[0] else 0, -row[0], -row[1], row[2]),
    )]


def placement_for(
    placements: Sequence[Placement], name: str
) -> Optional[Placement]:
    """One character's staging, or None when nobody staged them.

    Args:
        placements: The staging, which may say nothing about this person.
        name: The character's name.

    Returns:
        Their placement, or None.
    """
    return next((spot for spot in placements if spot.name == name), None)


def figure_framing(
    placements: Sequence[Placement], name: str
) -> Tuple[str, str]:
    """The angle terms and matching negative for one character.

    Per character, never one angle for the cast: each figure is rendered
    alone against grey, so its facing is the only thing saying which way it
    is turned once composited. The negative has to travel with it - the ban
    on "back turned" that protects a front view would otherwise forbid the
    figure asked to walk away.

    Args:
        placements: The staging, which may say nothing about this person.
        name: The character's name.

    Returns:
        (positive terms, extra negative terms). Both empty when no facing
        was chosen, which adds nothing and leaves the stance to decide.
    """
    spot = placement_for(placements, name)
    facing = spot.facing if spot else ""
    if not facing:
        return "", ""
    return ANGLES.get(facing, ""), ANGLE_NEGATIVES.get(facing, "")


def _figure_params(
    request: RegionRenderRequest,
    person: ShotPerson,
    index: int,
    pose: Optional[PoseControl],
    identity: Optional[IdentityReference],
) -> FigureParams:
    """Assemble one figure's render parameters.

    Args:
        request: The render request.
        person: The character being painted.
        index: Their position in the cast, which offsets the seed.
        pose: The stance control image, when there is one.
        identity: The likeness reference, when there is one.

    Returns:
        Parameters for figure_workflow.
    """
    # Per character, never one angle for the cast. A figure is rendered
    # alone against grey, so its facing is the only thing that says which
    # way it is turned once composited - and this passed no angle at all,
    # which is why every render came back as a row of people facing the
    # lens. Empty is still allowed and still means "let the stance decide".
    turned, away = figure_framing(request.framing.placements, person.name)
    return FigureParams(
        checkpoint=request.comfyui.assets.checkpoint,
        positive=", ".join(
            part for part in (
                region_prompt(person, turned, posed=pose is not None),
                FIGURE_BACKDROP,
            ) if part
        ),
        negative=", ".join(
            part for part in
            (request.negative, REGION_NEGATIVE, FIGURE_NEGATIVE, away) if part
        ),
        seed=request.seed + index,
        render=FIGURE_RENDER,
        identity=identity,
        pose=pose,
    )


def _render_figure(
    request: RegionRenderRequest,
    person: ShotPerson,
    index: int,
    pose: Optional[PoseControl],
) -> Optional[bytes]:
    """Render one figure, taking likeness from their face where there is one.

    FaceID reads a detected face's embedding, which is far stronger than the
    whole-image adapter and carries none of the portrait's background. It only
    works on a face the detector recognises, so a non-human head raises "No
    face detected" - before sampling, so the attempt costs almost nothing -
    and the render is retried against a head crop instead.

    Args:
        request: The render request.
        person: The character being painted.
        index: Their position in the cast.
        pose: The stance control image, when there is one.

    Returns:
        The rendered PNG, or None when both paths failed.
    """
    identity = _identity_for(request, person)
    if identity is not None:
        rendered = request.client.generate_then_free(
            figure_workflow(_figure_params(request, person, index, pose, identity))
        )
        if rendered is not None:
            return rendered
        logger.info(
            "No face found for %s; falling back to a head-cropped reference",
            person.name,
        )

    fallback = _fallback_identity(request, person)
    return request.client.generate_then_free(
        figure_workflow(_figure_params(request, person, index, pose, fallback))
    )


def paint_figures(request: RegionRenderRequest) -> Tuple[bytes, List[str]]:
    """Render each character alone at full size, then composite them in.

    The alternative - inpainting each into a column of the scene - leaves a
    figure roughly 24 latents wide, which is not enough to build a face out
    of. Rendering alone and compositing trades a seam for a real person.

    Args:
        request: Client, config, the environment PNG, the cast, and framing.

    Returns:
        (final_png, names placed).
    """
    width, height = png_size(request.inputs.scene_png)
    regions = lay_out(request.people, width, height, request.framing.shot,
                      request.framing.placements or None)

    cutouts: List[Tuple[int, float, int, Region, bytes]] = []
    for index, (person, region) in enumerate(zip(request.people, regions)):
        # The operator's stance and facing outrank the rotating default.
        # `pose_for_index` exists so a cast is not six identical statues;
        # it was overriding the staging rather than standing in for it.
        spot = placement_for(request.framing.placements, person.name)
        stance = (spot.pose if spot and spot.pose else pose_for_index(index))
        pose = _figure_pose(request, stance, index,
                            spot.facing if spot else "",
                            spot.toward if spot else "")
        rendered = _render_figure(request, person, index, pose)
        if rendered is None:
            logger.warning("Figure render failed for %s", person.name)
            continue
        cut = cut_out(rendered)
        if cut is None:
            logger.warning("Could not cut %s out of their backdrop", person.name)
            continue
        cutouts.append((spot.order if spot else 0,
                        spot.depth if spot else NEAR_DEPTH,
                        index, region, cut))
        logger.info(
            "Rendered %s (%s) at %dx%d for a %dx%d slot",
            person.name,
            stance,
            FIGURE_RENDER.width,
            FIGURE_RENDER.height,
            region.width,
            region.height,
        )

    return place(request.inputs.scene_png, paint_order(cutouts))
