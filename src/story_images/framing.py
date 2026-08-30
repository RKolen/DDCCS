"""How the shot is framed: how much of the figures, and from what side.

Nothing in the prompt used to say either, so every render came back a wide
shot of backs walking away - and a face swap on a face nobody can see costs
CPU minutes and changes zero pixels. Framing is the operator's call, not the
model's, so it is asked for explicitly and defaults to the answer that makes
the rest of the pipeline work.

Both are scene-wide. Per-character direction needs regional conditioning
(ControlNet pose), not prompt text: SD 1.5 does not bind an attribute to one
named subject when six are listed.
"""

from dataclasses import dataclass
from typing import Dict, Tuple

# Positive terms per shot type, and how much of the frame the figures fill.
SHOTS: Dict[str, str] = {
    "wide": "cinematic wide shot, full scene, figures small in the frame",
    "full": "full body shot, complete figures head to toe",
    "medium": "medium shot, figures from the waist up",
    "close": "close shot, head and shoulders",
}

# Positive terms per camera angle.
ANGLES: Dict[str, str] = {
    "front": "facing the viewer, faces clearly visible, front view",
    "three_quarter": "three-quarter view, faces visible, turned slightly away",
    "side": "side profile view, faces in profile",
    "behind": "seen from behind, backs to the viewer",
}

# Extra negative terms per angle. Asking for a front view is not enough on its
# own: the base style pulls towards backs walking into scenery, so the rear
# view has to be banned outright.
ANGLE_NEGATIVES: Dict[str, str] = {
    "front": "from behind, back turned, facing away, back of head",
    "three_quarter": "from behind, back turned, back of head",
    "side": "from behind, back of head",
    "behind": "",
}

DEFAULT_SHOT = "full"
DEFAULT_ANGLE = "three_quarter"


@dataclass
class SceneFraming:
    """How much of the figures to show, and from which side."""

    shot: str = DEFAULT_SHOT
    angle: str = DEFAULT_ANGLE

    def terms(self) -> Tuple[str, str]:
        """Resolve to (positive terms, extra negative terms).

        An unknown value falls back to the default rather than dropping out,
        so a stale console never silently renders an unframed shot.

        Returns:
            The positive framing phrase and any negative terms it needs.
        """
        positive = ", ".join(
            (
                SHOTS.get(self.shot, SHOTS[DEFAULT_SHOT]),
                ANGLES.get(self.angle, ANGLES[DEFAULT_ANGLE]),
            )
        )
        negative = ANGLE_NEGATIVES.get(self.angle, ANGLE_NEGATIVES[DEFAULT_ANGLE])
        return positive, negative
