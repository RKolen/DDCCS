"""Where each character stands in the frame, and how tall they are.

One prompt naming six people cannot say which of them is the halfling: Stable
Diffusion has no way to bind an attribute to one named subject, so every tag
smears across every figure - six near-identical elves in matching green.

Giving each character their own region fixes that at the root. A region is
rendered from a prompt describing one person, so nothing can leak. It also
buys body type for free: a halfling gets a shorter box than a dragonborn, and
apparent height follows from the box rather than from a word the model may
ignore.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from src.story_images.types import ShotPerson

# Height as a fraction of a human's, by species word found in the appearance
# tags. Only differences worth a pixel are listed; anything unlisted is 1.0.
SPECIES_HEIGHT: Dict[str, float] = {
    "halfling": 0.62,
    "gnome": 0.60,
    "dwarf": 0.72,
    "goblin": 0.62,
    "kobold": 0.58,
    "orc": 1.12,
    "half-orc": 1.10,
    "goliath": 1.30,
    "dragonborn": 1.22,
    "firbolg": 1.28,
    "centaur": 1.30,
}

# Fraction of the canvas height a full-height figure occupies, per shot type.
SHOT_FIGURE_HEIGHT: Dict[str, float] = {
    "wide": 0.45,
    "full": 0.80,
    "medium": 1.05,
    "close": 1.60,
}

# Ground line as a fraction of canvas height: where the nearest feet sit.
GROUND_LINE = 0.92

# Where the ground meets the sky. A figure twice as far away is half as tall
# AND stands half as far down from here, which is what makes distance read as
# distance rather than as a short person. Without it everyone shared one floor
# and a cast came out as a police line-up - which the old layout's own
# docstring worried about while producing one.
HORIZON = 0.55

# Depth 1.0 is the front of the scene. Nothing may be nearer, or a figure
# grows past the frame; the far cap keeps a distant figure above the floor a
# renderable number of pixels tall.
NEAR_DEPTH = 1.0
FAR_DEPTH = 3.0

# Region width relative to its height. Wide enough for a cloak and a stance.
WIDTH_RATIO = 0.42


@dataclass(frozen=True)
class Stance:
    """How one figure holds itself, as opposed to where it stands.

    ``pose`` names the stance, or is empty to let the renderer choose one.

    ``facing`` is which way this one character is turned, and it is per
    character on purpose. Each figure is rendered alone against grey and
    composited, so a single camera angle for the whole cast cannot say that
    a group walks away while someone follows them - and the composite path
    passed no angle at all, which is why every render came back as a row of
    people looking at the lens. Empty keeps that behaviour: the stance sets
    the orientation and nothing argues with it.

    ``toward`` is which way along the frame that turn points, left or right.
    Facing alone cannot say it, so a cast all set to profile faced the same
    way - the group and the person walking up to meet them included.

    ``limbs`` is where the operator dragged individual joints, by name, in
    the figure's own layout units after the turn. A stance is a starting
    point; nine of them cannot say "sword raised, off hand out for balance".
    """

    pose: str = ""
    facing: str = ""
    toward: str = ""
    limbs: Mapping[str, Tuple[float, float]] = field(default_factory=dict)


@dataclass
class Placement:
    """Where one character stands, before it becomes pixels.

    ``lateral`` is 0.0 at the left edge of the frame and 1.0 at the right,
    measured at the figure's centre. ``depth`` is 1.0 at the front of the
    scene and larger further back. ``stance`` is how they hold themselves.

    ``order`` is who is in front when two figures overlap: 1 is nearest the
    camera and is painted last, so it comes out whole. 0 means the operator
    has no opinion and depth decides. It is separate from depth on purpose -
    apparent size already does not follow distance here, because a halfling
    at the front of the scene is smaller than an orc at the back, so the
    figure that should win an overlap is not always the nearest one.

    This is the operator's handle on staging: the console shows it as a
    skeleton that can be dragged, and the same numbers drive the render, so
    what was previewed is what is painted.
    """

    name: str
    lateral: float = 0.5
    depth: float = NEAR_DEPTH
    stance: Stance = field(default_factory=Stance)
    order: int = 0

    def clamped(self) -> "Placement":
        """The same placement with lateral and depth inside their limits.

        Returns:
            A placement safe to turn into a region.
        """
        return Placement(
            name=self.name,
            lateral=min(max(self.lateral, 0.0), 1.0),
            depth=min(max(self.depth, NEAR_DEPTH), FAR_DEPTH),
            stance=self.stance,
            order=self.order,
        )


@dataclass
class Region:
    """One character's box in the frame, in pixels."""

    name: str
    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        """Right edge, exclusive."""
        return self.left + self.width

    @property
    def bottom(self) -> int:
        """Bottom edge, exclusive."""
        return self.top + self.height


def height_factor(person: ShotPerson) -> float:
    """Relative height for one person, read from their appearance tags.

    Args:
        person: Someone in frame.

    Returns:
        A multiplier on human height; 1.0 when nothing is recognised.
    """
    haystack = f"{person.appearance} {person.action}".lower()
    for species, factor in SPECIES_HEIGHT.items():
        if species in haystack:
            return factor
    return 1.0


def default_placements(people: Sequence[ShotPerson]) -> List[Placement]:
    """Evenly spaced across the frame, all at the front.

    The layout this replaced, expressed as data: it is what an operator sees
    before they move anybody, and reproduces the old behaviour exactly.

    Args:
        people: Who is in frame, in the order they should appear.

    Returns:
        One placement per person, left to right.
    """
    count = len(people)
    return [
        Placement(name=person.name, lateral=(index + 0.5) / count)
        for index, person in enumerate(people)
    ]


def lay_out(
    people: Sequence[ShotPerson],
    width: int,
    height: int,
    shot: str = "full",
    placements: Optional[Sequence[Placement]] = None,
) -> List[Region]:
    """Place everyone along the frame, standing on a common ground line.

    Boxes are evenly spaced across the width and share a floor, so a short
    character reads as short rather than as a distant one. They may touch at
    the edges - figures in a group overlap, and a hard gap between every pair
    looks like a police line-up.

    Args:
        people: Who is in frame, in the order they should appear.
        width: Canvas width in pixels.
        height: Canvas height in pixels.
        shot: Shot type, which sets how much of the frame a figure fills.
        placements: Where each person stands. Defaults to evenly spaced at
            the front, which is what this did before staging existed.

    Returns:
        One region per person, left to right. Empty when nobody is in frame.
    """
    if not people:
        return []

    full_height = height * SHOT_FIGURE_HEIGHT.get(shot, SHOT_FIGURE_HEIGHT["full"])
    staged = {spot.name: spot.clamped()
              for spot in (placements or default_placements(people))}
    slot = width / len(people)
    defaults = default_placements(people)
    return [
        _region_for(
            person,
            staged.get(person.name, defaults[index]),
            (width, height),
            full_height * height_factor(person),
            slot,
        )
        for index, person in enumerate(people)
    ]


def _region_for(
    person: ShotPerson,
    spot: Placement,
    canvas: Tuple[int, int],
    figure_height: float,
    slot: float,
) -> Region:
    """Turn one placement into the box that character is painted in.

    Args:
        person: Who this is.
        spot: Where they stand, already clamped.
        canvas: (width, height) in pixels.
        figure_height: Their full height at the front of the scene.
        slot: The widest a figure may be without overrunning a neighbour.

    Returns:
        Their region.
    """
    width, height = canvas
    horizon = height * HORIZON
    # Height and floor recede toward the horizon by the same factor, so a
    # figure at depth 2 is half as tall AND stands halfway up to it. Scaling
    # only the height makes a distant person look like a short one standing
    # at your feet - which is what the flat layout did to a whole cast.
    ground = int(horizon + (height * GROUND_LINE - horizon) / spot.depth)
    # Capped on the space above this figure's own ground line, never on the
    # canvas: a taller figure would otherwise be pushed down off the floor.
    tall = min(int(figure_height / spot.depth), ground)
    # Never wider than a slot: six figures at their natural width overrun
    # their neighbours, and each pass then paints over the one before it.
    wide = max(min(int(tall * WIDTH_RATIO), int(slot)), 1)
    left = max(0, min(int(width * spot.lateral) - wide // 2, width - wide))
    top = max(0, ground - tall)
    return Region(
        name=person.name,
        left=left,
        top=top,
        width=min(wide, width - left),
        height=min(tall, height - top),
    )
