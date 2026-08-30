"""Build a Stable Diffusion prompt for a story-scene illustration."""

from typing import List, Optional, Sequence, Tuple

from src.story_images.framing import SceneFraming
from src.story_images.types import ShotAnalysis, ShotPerson
from src.utils.string_utils import clip_to_budget

_BASE_STYLE = (
    "fantasy illustration, digital painting, dramatic lighting, sharp focus"
)
_NEGATIVE = (
    "lowres, blurry, deformed, extra limbs, extra heads, mutated hands, "
    "bad anatomy, watermark, text, signature, cropped faces, "
    "character sheet, plain background"
)

# Attention multiplier on the analysed action. High enough to survive the
# scene and style tokens around it, low enough not to deform the figure.
ACTION_WEIGHT = "1.35"

# How many people the prompt names. Beyond this the tag list crowds out the
# action and the setting; the rest are still in frame as unnamed figures.
MAX_NAMED_PEOPLE = 12

MAX_PROMPT_CHARS = 480
MAX_TAG_CHARS = 80


def _person_tags(person: ShotPerson) -> str:
    """A short visual tag for one person in the shot.

    Args:
        person: Someone in frame.

    Returns:
        A comma-free tag, empty when there is nothing visual to say.
    """
    bits = [person.name]
    appearance = clip_to_budget(person.appearance, MAX_TAG_CHARS)
    if appearance:
        bits.append(appearance)
    elif person.role:
        bits.append(clip_to_budget(person.role, MAX_TAG_CHARS))
    return ", ".join(bits)


def build_scene_prompt(
    analysis: ShotAnalysis,
    people: Sequence[ShotPerson],
    framing: Optional[SceneFraming] = None,
) -> Tuple[str, str]:
    """Build (positive, negative) SD prompts for a scene.

    Not a portrait prompt: the negative does not ban multiple people, and the
    style is a wide shot. People without likeness still appear as prompt tags
    so unnamed extras and known faces share the same picture.

    Ordered subject, action, setting, mood, style - and the action carries an
    explicit attention weight, because it is the part a render most readily
    drops in favour of simply posing the character somewhere plausible.

    Args:
        analysis: Setting, action, and mood from the shot analysis.
        people: Who the operator left in frame.
        framing: How much of the figures to show and from which side.

    Returns:
        A (positive_prompt, negative_prompt) pair.
    """
    # Subject and action lead, style trails. Stable Diffusion weights early
    # tokens most, so a seven-word style preamble in front of the action left
    # the figure standing in the right place doing nothing in particular.
    parts: List[str] = []
    in_frame = [_person_tags(person) for person in people if person.name]
    if in_frame:
        parts.append("; ".join(in_frame[:MAX_NAMED_PEOPLE]))
    if analysis.action.strip():
        parts.append(f"({clip_to_budget(analysis.action, 160)}:{ACTION_WEIGHT})")
    if analysis.setting.strip():
        parts.append(clip_to_budget(analysis.setting, MAX_TAG_CHARS))
    if analysis.mood.strip():
        parts.append(clip_to_budget(analysis.mood, MAX_TAG_CHARS))
    shot_terms, shot_negative = (framing or SceneFraming()).terms()
    parts.append(shot_terms)
    parts.append(_BASE_STYLE)

    positive = clip_to_budget(", ".join(parts), MAX_PROMPT_CHARS)
    negative = f"{_NEGATIVE}, {shot_negative}" if shot_negative else _NEGATIVE
    return positive, negative
