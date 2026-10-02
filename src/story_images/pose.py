"""Draw an OpenPose skeleton so a region gets a person, not more scenery.

A rectangular mask over an empty room tells the renderer nothing about what
belongs there, so it is free to paint more room - which is what it did. At a
denoise high enough to force a figure, each region also reinvented its own
background; at a denoise low enough to keep the room, three regions in six
came back as furniture and foliage.

A skeleton removes the choice. It says a person of this height stands here,
in this stance, so the denoise can go back up without the background running
away: the structure is pinned by the control image rather than left to the
sampler.

Keypoints and colours follow the COCO-18 convention ControlNet's openpose
model was trained on. The colours are not decorative - the model reads limb
identity from them.
"""

import dataclasses
import io
import math
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from PIL import Image, ImageDraw

from src.story_images.regions import Placement, Region, Stance

# COCO-18 joint order.
NOSE, NECK = 0, 1
R_SHOULDER, R_ELBOW, R_WRIST = 2, 3, 4
L_SHOULDER, L_ELBOW, L_WRIST = 5, 6, 7
R_HIP, R_KNEE, R_ANKLE = 8, 9, 10
L_HIP, L_KNEE, L_ANKLE = 11, 12, 13
R_EYE, L_EYE, R_EAR, L_EAR = 14, 15, 16, 17

# The joints an operator may drag, by the name the console sends. The head is
# left out: its keypoints are placed round the skull by the facing, and a
# hand-moved eye would contradict the turn it belongs to.
LIMB_JOINTS: Dict[str, int] = {
    "r_shoulder": R_SHOULDER, "r_elbow": R_ELBOW, "r_wrist": R_WRIST,
    "l_shoulder": L_SHOULDER, "l_elbow": L_ELBOW, "l_wrist": L_WRIST,
    "r_hip": R_HIP, "r_knee": R_KNEE, "r_ankle": R_ANKLE,
    "l_hip": L_HIP, "l_knee": L_KNEE, "l_ankle": L_ANKLE,
}

# How far a moved joint may go, in layout units. Half a unit either side is
# the edge of a figure's own canvas; past it the render clips the hand.
LIMB_REACH = 0.5
LIMB_TOP, LIMB_BOTTOM = -0.1, 1.05

# Joint positions for a standing figure, as fractions of the box: x from its
# centre, y from its top. Proportioned on an eight-heads-tall figure.
STANDING: Dict[int, Tuple[float, float]] = {
    NOSE: (0.00, 0.055),
    NECK: (0.00, 0.135),
    R_SHOULDER: (-0.115, 0.150),
    R_ELBOW: (-0.150, 0.290),
    R_WRIST: (-0.165, 0.425),
    L_SHOULDER: (0.115, 0.150),
    L_ELBOW: (0.150, 0.290),
    L_WRIST: (0.165, 0.425),
    R_HIP: (-0.070, 0.480),
    R_KNEE: (-0.078, 0.700),
    R_ANKLE: (-0.082, 0.945),
    L_HIP: (0.070, 0.480),
    L_KNEE: (0.078, 0.700),
    L_ANKLE: (0.082, 0.945),
    R_EYE: (-0.028, 0.040),
    L_EYE: (0.028, 0.040),
    R_EAR: (-0.055, 0.048),
    L_EAR: (0.055, 0.048),
}

# Per-pose joint overrides, applied on top of STANDING. A row of identical
# front-facing figures reads as a police line-up however good each one is, so
# a cast is dealt poses from here rather than all getting the same one.
POSE_VARIANTS: Dict[str, Dict[int, Tuple[float, float]]] = {
    "standing": {},
    "arms_crossed": {
        R_ELBOW: (-0.140, 0.300),
        R_WRIST: (0.010, 0.330),
        L_ELBOW: (0.140, 0.300),
        L_WRIST: (-0.010, 0.360),
    },
    "hand_on_hip": {
        R_ELBOW: (-0.165, 0.300),
        R_WRIST: (-0.090, 0.455),
        L_ELBOW: (0.160, 0.300),
        L_WRIST: (0.150, 0.430),
    },
    "gesturing": {
        R_ELBOW: (-0.180, 0.250),
        R_WRIST: (-0.230, 0.150),
        L_ELBOW: (0.150, 0.300),
        L_WRIST: (0.160, 0.430),
    },
    "leaning": {
        NOSE: (0.045, 0.060),
        NECK: (0.035, 0.140),
        R_SHOULDER: (-0.080, 0.155),
        L_SHOULDER: (0.150, 0.155),
        R_HIP: (-0.040, 0.480),
        L_HIP: (0.100, 0.480),
        R_KNEE: (-0.050, 0.700),
        L_KNEE: (0.115, 0.700),
        R_ANKLE: (-0.055, 0.945),
        L_ANKLE: (0.120, 0.945),
        R_EYE: (0.017, 0.045),
        L_EYE: (0.073, 0.045),
        R_EAR: (-0.010, 0.053),
        L_EAR: (0.100, 0.053),
    },
    "holding": {
        R_ELBOW: (-0.150, 0.300),
        R_WRIST: (-0.080, 0.380),
        L_ELBOW: (0.150, 0.300),
        L_WRIST: (0.080, 0.380),
    },
    # The three below move the hips and knees, not just the arms. A stance
    # built from arm overrides alone still reads as standing to attention,
    # which is what made six varied poses look like one row.
    "sitting": {
        R_HIP: (-0.075, 0.585),
        L_HIP: (0.075, 0.585),
        R_KNEE: (-0.135, 0.645),
        L_KNEE: (0.135, 0.645),
        R_ANKLE: (-0.115, 0.930),
        L_ANKLE: (0.115, 0.930),
        R_ELBOW: (-0.145, 0.330),
        R_WRIST: (-0.100, 0.520),
        L_ELBOW: (0.145, 0.330),
        L_WRIST: (0.100, 0.520),
    },
    # A stride is fore-aft, and a flat layout has nowhere to put it, so this
    # used to splay the legs sideways instead and call it walking. That reads
    # from the front and nowhere else: the splay is lateral, so turning the
    # figure squeezes it away exactly when a real stride would be widest.
    # The lateral part is kept small and the stride proper lives in
    # POSE_DEPTH, where turning brings it into view instead of removing it.
    # Left leg leads, so the right arm swings forward with it.
    "walking": {
        R_HIP: (-0.068, 0.480),
        L_HIP: (0.072, 0.480),
        R_KNEE: (-0.072, 0.690),
        L_KNEE: (0.068, 0.705),
        R_ANKLE: (-0.060, 0.930),
        L_ANKLE: (0.055, 0.945),
        R_ELBOW: (-0.155, 0.285),
        R_WRIST: (-0.125, 0.405),
        L_ELBOW: (0.140, 0.300),
        L_WRIST: (0.150, 0.415),
    },
    "laughing": {
        NOSE: (0.010, 0.062),
        NECK: (0.000, 0.140),
        R_ELBOW: (-0.175, 0.295),
        R_WRIST: (-0.105, 0.235),
        L_ELBOW: (0.160, 0.305),
        L_WRIST: (0.095, 0.400),
        R_EYE: (-0.018, 0.048),
        L_EYE: (0.038, 0.048),
        R_EAR: (-0.048, 0.052),
        L_EAR: (0.062, 0.052),
    },
}

# How far fore or aft of the body's own centre a joint sits, per pose. The
# layout above is flat: (dx, dy) is what the camera sees head-on, and a stride
# or a reaching arm has no width to see from there, so a walk has to be faked
# sideways. Turn that figure to profile and the fake is squeezed away exactly
# when the real stride would be at its widest - a side-on walker came back
# standing to attention.
#
# Positive is the way the figure faces. Only the poses with real fore-aft
# movement are listed; the rest are flat and stay flat.
POSE_DEPTH: Dict[str, Dict[int, float]] = {
    "walking": {
        NOSE: 0.030, NECK: 0.025,
        # Left leg leads. Each sign matches that leg's lateral offset, so the
        # stride grows as the figure turns instead of cancelling against it.
        #
        # Deliberately wider than a real step. These were half this size and
        # read as a natural walk in the skeleton, which is the wrong judge:
        # the ControlNet weighed a 14%-of-height stride against its own prior
        # that a lone figure stands still, and the prior won at every strength
        # up to 1.6. Doubled, the same prompt and seed walk at 0.85.
        L_HIP: 0.028, L_KNEE: 0.085, L_ANKLE: 0.165,
        R_HIP: -0.028, R_KNEE: -0.095, R_ANKLE: -0.180,
        # The arms swing against the legs; matching them reads as a shuffle.
        R_ELBOW: 0.070, R_WRIST: 0.135,
        L_ELBOW: -0.062, L_WRIST: -0.125,
    },
    "sitting": {
        R_KNEE: 0.120, R_ANKLE: 0.100,
        L_KNEE: 0.120, L_ANKLE: 0.100,
        R_WRIST: 0.040, L_WRIST: 0.040,
    },
    "gesturing": {
        R_ELBOW: 0.040, R_WRIST: 0.080,
    },
    "holding": {
        R_ELBOW: 0.030, R_WRIST: 0.070,
        L_ELBOW: 0.030, L_WRIST: 0.070,
    },
    "arms_crossed": {
        R_WRIST: 0.040, L_WRIST: 0.040,
    },
}

# Canvas left free above the crown and below the ankles when a figure is
# rendered alone, as fractions of the canvas height.
HEAD_ROOM = 0.14
FOOT_ROOM = 0.12

# Canvas left free either side. A skeleton is a stick figure; the render
# hangs a cloak, a spread arm and a scabbard off it, and those ran past the
# frame. A clipped figure is worse than a small one: rembg treats the
# edge-touching region as foreground, so the cutout comes back a rectangle
# of backdrop and the scene gets a grey box pasted into it.
SIDE_ROOM = 0.25


# Dealt in this order so neighbours never share a stance.
POSE_ORDER: Sequence[str] = (
    "hand_on_hip",
    "arms_crossed",
    "standing",
    "gesturing",
    "leaning",
    "holding",
)


def pose_for_index(index: int) -> str:
    """Pick a stance for the nth character in the cast.

    Args:
        index: Position in the cast.

    Returns:
        A key into POSE_VARIANTS.
    """
    return POSE_ORDER[index % len(POSE_ORDER)]


# (joint a, joint b, colour) in the order the openpose renderer draws them.
LIMBS: Sequence[Tuple[int, int, Tuple[int, int, int]]] = (
    (NECK, R_SHOULDER, (255, 0, 0)),
    (NECK, L_SHOULDER, (255, 85, 0)),
    (R_SHOULDER, R_ELBOW, (255, 170, 0)),
    (R_ELBOW, R_WRIST, (255, 255, 0)),
    (L_SHOULDER, L_ELBOW, (170, 255, 0)),
    (L_ELBOW, L_WRIST, (85, 255, 0)),
    (NECK, R_HIP, (0, 255, 0)),
    (R_HIP, R_KNEE, (0, 255, 85)),
    (R_KNEE, R_ANKLE, (0, 255, 170)),
    (NECK, L_HIP, (0, 255, 255)),
    (L_HIP, L_KNEE, (0, 170, 255)),
    (L_KNEE, L_ANKLE, (0, 85, 255)),
    (NECK, NOSE, (0, 0, 255)),
    (NOSE, R_EYE, (85, 0, 255)),
    (R_EYE, R_EAR, (170, 0, 255)),
    (NOSE, L_EYE, (255, 0, 255)),
    (L_EYE, L_EAR, (255, 0, 170)),
)

JOINT_COLOURS: Dict[int, Tuple[int, int, int]] = {
    NOSE: (255, 0, 0), NECK: (255, 85, 0),
    R_SHOULDER: (255, 170, 0), R_ELBOW: (255, 255, 0), R_WRIST: (170, 255, 0),
    L_SHOULDER: (85, 255, 0), L_ELBOW: (0, 255, 0), L_WRIST: (0, 255, 85),
    R_HIP: (0, 255, 170), R_KNEE: (0, 255, 255), R_ANKLE: (0, 170, 255),
    L_HIP: (0, 85, 255), L_KNEE: (0, 0, 255), L_ANKLE: (85, 0, 255),
    R_EYE: (170, 0, 255), L_EYE: (255, 0, 255),
    R_EAR: (255, 0, 170), L_EAR: (255, 0, 85),
}


# How far a figure is turned from the camera, per facing name. The skeleton
# is what ControlNet actually obeys: a prompt saying "side profile view" lost
# to a front-facing skeleton in every render, because an openpose figure with
# both ears, both eyes and full-width shoulders IS a front view and no words
# outvote it.
TURN_DEGREES: Dict[str, float] = {
    "front": 0.0,
    "three_quarter": 40.0,
    "side": 90.0,
    "behind": 180.0,
}

# Where each head keypoint sits around the skull, in degrees from the nose.
# Turning the head is then a rotation: a keypoint is drawn only while it is
# still on the near side, which is what gives a profile one eye and one ear.
HEAD_BEARINGS: Dict[int, float] = {
    NOSE: 0.0,
    L_EYE: 30.0,
    R_EYE: -30.0,
    L_EAR: 90.0,
    R_EAR: -90.0,
}

# Half the head's width in layout units, taken from where the ears sit.
HEAD_RADIUS = 0.055

# A true cos(90) collapses the body to a vertical line, which openpose reads
# as no figure at all. Real side views keep a readable shoulder: the staging
# lab's profile guard measured 0.84 of full width, so the floor is generous.
MIN_FORESHORTEN = 0.45

# Anything at or in front of this is still on the near side of the skull.
# Exactly zero would drop the nose at a perfect profile, where it should be
# the leading point of the face.
_NEAR_SIDE = -0.05

# Which way along the frame a turned figure is pointed. The facing says how
# far round they are; this says whether that is to the left or the right, and
# without it a cast all set to profile faces the same way - a conga line, when
# what the scene needed was one person walking up to the rest of them.
TOWARD_SIGN: Dict[str, float] = {"right": 1.0, "left": -1.0}

# Empty means this, so existing staging keeps the direction it already had.
DEFAULT_TOWARD = "right"


def _turn_factors(turn: float) -> Tuple[float, float, float]:
    """The three multipliers one turn angle contributes.

    Args:
        turn: Degrees clockwise from facing the camera.

    Returns:
        (true cosine, floored signed cosine, sine). The floored form keeps a
        joint with nothing but width off the centre line; the true one is for
        joints that have their own fore-aft position to supply width.
    """
    radians = math.radians(turn)
    cosine = math.cos(radians)
    return (
        cosine,
        math.copysign(max(abs(cosine), MIN_FORESHORTEN), cosine),
        math.sin(radians),
    )


def _head_offset(joint: int, turn: float) -> Optional[float]:
    """Where one head keypoint lands once the skull has turned.

    Args:
        joint: A key in `HEAD_BEARINGS`.
        turn: Degrees clockwise from facing the camera.

    Returns:
        Its offset from the head's centre, or None once it has gone round to
        the far side - which is how openpose says a keypoint is occluded.
    """
    angle = math.radians(HEAD_BEARINGS[joint] + turn)
    if math.cos(angle) <= _NEAR_SIDE:
        return None
    return HEAD_RADIUS * math.sin(angle)


def turn_layout(
    layout: Dict[int, Tuple[float, float]],
    facing: str,
    depths: Optional[Mapping[int, float]] = None,
    toward: str = "",
) -> Dict[int, Tuple[float, float]]:
    """Rotate a skeleton about its own vertical axis.

    A joint has a width offset the camera sees head-on and a fore-aft offset
    it does not; turning trades one for the other. The head keypoints are
    carried round the skull instead, so the far eye and far ear disappear.
    Together those are what make an openpose figure read as turned - the
    prompt only names it.

    Args:
        layout: Joint index -> (dx, dy) in layout units.
        facing: A key in `TURN_DEGREES`, or empty for no turn.
        depths: Joint index -> fore-aft offset, positive toward the front.
        toward: A key in `TOWARD_SIGN`; empty means `DEFAULT_TOWARD`.

    Returns:
        The turned layout, unchanged when no facing was given.
    """
    turn = TURN_DEGREES.get(facing, 0.0) * TOWARD_SIGN.get(
        toward or DEFAULT_TOWARD, TOWARD_SIGN[DEFAULT_TOWARD])
    if not facing or turn == 0.0:
        return layout
    # Signed, so a back view mirrors: from behind, someone's right arm is on
    # the viewer's right, and openpose reads limb identity from colour - an
    # unmirrored back view tells it the figure faces forward with its arms
    # crossed over.
    cosine, across, along = _turn_factors(turn)
    fore = depths or {}
    turned: Dict[int, Tuple[float, float]] = {}
    for joint, (dx, dy) in layout.items():
        if joint in HEAD_BEARINGS:
            offset = _head_offset(joint, turn)
            if offset is not None:
                turned[joint] = (offset, dy)
            continue
        # The floored cosine is a crutch for joints with nothing but width.
        # A joint that knows its fore-aft position has real width when turned
        # and does not need it, and holding 45% of a stance's lateral splay
        # against the stride is what left a side-on walker standing still.
        depth = fore.get(joint)
        turned[joint] = (
            (dx * across) if depth is None
            else (dx * cosine + depth * along), dy,
        )
    return turned


def moved_joints(
    limbs: Optional[Mapping[str, Tuple[float, float]]],
) -> Dict[int, Tuple[float, float]]:
    """Turn the operator's named limb moves into joint overrides.

    Args:
        limbs: Joint name -> (dx, dy) in layout units. Unknown names are
            dropped, and every position is held inside the figure's reach.

    Returns:
        Joint index -> (dx, dy), ready for `figure_layout`.
    """
    return {
        LIMB_JOINTS[name]: (min(max(dx, -LIMB_REACH), LIMB_REACH),
                            min(max(dy, LIMB_TOP), LIMB_BOTTOM))
        for name, (dx, dy) in (limbs or {}).items() if name in LIMB_JOINTS
    }


def figure_layout(stance: Stance) -> Dict[int, Tuple[float, float]]:
    """A skeleton in layout units: stance, then turn, then the operator.

    Hand-moved limbs land after the turn, not before it. They were placed on
    the turned skeleton the console drew, so applying them to the flat one
    and turning again would put every hand somewhere nobody dragged it.

    Args:
        stance: Pose (unknown names fall back to standing), facing,
            direction and any moved limbs.

    Returns:
        Joint index -> (dx, dy): x from the box centre, y from its top.
    """
    layout = dict(STANDING)
    layout.update(POSE_VARIANTS.get(stance.pose, {}))
    layout = turn_layout(layout, stance.facing, POSE_DEPTH.get(stance.pose),
                         stance.toward)
    layout.update(moved_joints(stance.limbs))
    return layout


def joints_for(
    region: Region, pose: str = "standing", facing: str = "",
    toward: str = "", limbs: Optional[Mapping[str, Tuple[float, float]]] = None,
) -> Dict[int, Tuple[int, int]]:
    """Place a skeleton's joints inside one region.

    Args:
        region: The character's box.
        pose: A key into POSE_VARIANTS; unknown names fall back to standing.
        facing: Which way the figure is turned, or empty to face the camera.
        toward: Which way along the frame that turn points.
        limbs: Joint name -> (dx, dy) the operator moved, if any.

    Returns:
        Joint index -> (x, y) in canvas pixels.
    """
    layout = figure_layout(Stance(pose, facing, toward, limbs or {}))
    centre = region.left + region.width / 2
    return {
        joint: (
            int(centre + dx * region.width * 2.0),
            int(region.top + dy * region.height),
        )
        for joint, (dx, dy) in layout.items()
    }


def openpose_png(
    width: int,
    height: int,
    regions: Sequence[Region],
    staging: Optional[Sequence[Placement]] = None,
) -> bytes:
    """Draw every region's skeleton onto one black canvas.

    All figures go on a single control image: ControlNet conditions the whole
    frame at once, so one pass per region would erase the others.

    Args:
        width: Canvas width.
        height: Canvas height.
        regions: The boxes to stand a figure in.
        staging: The placements those boxes came from, matched by name. The
            stance used to be hardcoded to "standing" and the facing was
            never passed at all, so the console preview drew a row of
            identical front views for a staging the render then posed and
            turned - a preview that promised what it would not paint.

    Returns:
        PNG bytes of the pose control image.
    """
    image = Image.new("RGB", (width, height), (0, 0, 0))
    draw = ImageDraw.Draw(image)
    staged = {spot.name: spot for spot in (staging or ())}
    for region in regions:
        stance = staged[region.name].stance if region.name in staged else Stance()
        _draw_figure(draw, region,
                     dataclasses.replace(stance, pose=stance.pose or "standing"))

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _draw_figure(
    draw: ImageDraw.ImageDraw, region: Region, stance: Stance,
) -> None:
    """Draw one skeleton into its region.

    Args:
        draw: The canvas to draw on.
        region: The box to stand the figure in.
        stance: Pose, facing, direction and any moved limbs.
    """
    joints = joints_for(region, stance.pose, stance.facing, stance.toward,
                        stance.limbs)
    limb_width = max(2, region.width // 28)
    for start, end, colour in LIMBS:
        # A turned head has no far eye and no far ear, and openpose says
        # "occluded" by leaving the keypoint out. Drawing a limb to one that
        # is not there raised KeyError: 15 - the left eye - and failed the
        # whole render the moment anybody was staged in profile.
        if start not in joints or end not in joints:
            continue
        draw.line([joints[start], joints[end]], fill=colour, width=limb_width)
    radius = max(2, region.width // 34)
    for joint, (x, y) in joints.items():
        draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            fill=JOINT_COLOURS[joint],
        )


def silhouette_png(width: int, height: int, region: Region) -> bytes:
    """Draw a white mask following one figure's skeleton, not its box.

    A rectangular mask hands the sampler a slab of canvas to fill, and at a
    denoise high enough to paint a person it repaints the backdrop too - six
    boxes side by side then read as six panels rather than one room. The
    skeleton already says where the body is, so masking a fattened version of
    it leaves the scene between and behind the figures untouched.

    Args:
        width: Canvas width.
        height: Canvas height.
        region: The character's box.

    Returns:
        PNG bytes of the mask.
    """
    image = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(image)
    joints = joints_for(region)

    # Wide enough to carry a body rather than a stick: limbs get roughly a
    # sixth of the figure's width, the torso and head considerably more.
    limb = max(6, int(region.width * 0.17))
    for start, end, _ in LIMBS:
        draw.line([joints[start], joints[end]], fill=255, width=limb)

    torso = [joints[R_SHOULDER], joints[L_SHOULDER], joints[L_HIP], joints[R_HIP]]
    draw.polygon(torso, fill=255)

    head_r = max(8, int(region.width * 0.20))
    hx, hy = joints[NOSE]
    draw.ellipse([hx - head_r, hy - head_r, hx + head_r, hy + head_r], fill=255)

    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="PNG")
    return buffer.getvalue()


def figure_pose_png(width: int, height: int, stance: Stance) -> bytes:
    """Draw one skeleton filling a single-figure canvas.

    The scene-wide control image is no use to a figure rendered alone: it is
    the wrong size and carries everyone else's skeletons.

    Args:
        width: Figure canvas width.
        height: Figure canvas height.
        stance: Pose, facing, direction and any moved limbs.

    Returns:
        PNG bytes of the pose control image.
    """
    # The skeleton is not the silhouette. A boot extends below the ankle
    # joint, hair and horns above the crown, so a box drawn to the joints
    # and pushed to the canvas edge renders a figure whose feet are cut
    # flat - and trim_to_subject then scales that severed body to full
    # height without ever reporting it. Headroom above and footroom below
    # are what the joints do not account for.
    top = int(height * HEAD_ROOM)
    box = Region(
        name=stance.pose,
        left=int(width * SIDE_ROOM),
        top=top,
        width=int(width * (1.0 - SIDE_ROOM * 2)),
        height=int(height * (1.0 - HEAD_ROOM - FOOT_ROOM)),
    )
    image = Image.new("RGB", (width, height), (0, 0, 0))
    _draw_figure(ImageDraw.Draw(image), box, stance)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def visible_regions(regions: Sequence[Region]) -> List[Region]:
    """Drop boxes too small to carry a readable skeleton.

    Args:
        regions: Candidate boxes.

    Returns:
        Those wide and tall enough to draw a figure into.
    """
    return [
        region for region in regions if region.width >= 48 and region.height >= 96
    ]
