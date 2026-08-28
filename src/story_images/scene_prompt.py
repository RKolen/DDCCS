"""Build a Stable Diffusion prompt for a story-scene illustration."""

from typing import List, Sequence, Tuple

from src.story_images.types import ShotAnalysis, ShotPerson
from src.utils.string_utils import clip_to_budget

_BASE_STYLE = (
    "cinematic wide shot, fantasy illustration, digital painting, "
    "dramatic lighting, sharp focus, full scene"
)
_NEGATIVE = (
    "lowres, blurry, deformed, extra limbs, extra heads, mutated hands, "
    "bad anatomy, watermark, text, signature, cropped faces, "
    "portrait close-up, head and shoulders only"
)

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
) -> Tuple[str, str]:
    """Build (positive, negative) SD prompts for a scene.

    Not a portrait prompt: the negative does not ban multiple people, and the
    style is a wide shot. People without likeness still appear as prompt tags
    so unnamed extras and known faces share the same picture.

    Args:
        analysis: Setting, action, and mood from the shot analysis.
        people: Who the operator left in frame.

    Returns:
        A (positive_prompt, negative_prompt) pair.
    """
    parts: List[str] = [_BASE_STYLE]
    if analysis.setting.strip():
        parts.append(clip_to_budget(analysis.setting, MAX_TAG_CHARS))
    if analysis.action.strip():
        parts.append(clip_to_budget(analysis.action, 160))
    if analysis.mood.strip():
        parts.append(clip_to_budget(analysis.mood, MAX_TAG_CHARS))

    in_frame = [_person_tags(person) for person in people if person.name]
    if in_frame:
        parts.append("featuring " + "; ".join(in_frame[:8]))

    positive = clip_to_budget(", ".join(parts), MAX_PROMPT_CHARS)
    return positive, _NEGATIVE
