"""Build a Stable Diffusion prompt for a story-scene illustration."""

import logging
from typing import List, Optional, Sequence, Tuple

from src.story_images.framing import SceneFraming
from src.story_images.types import ShotAnalysis, ShotPerson
from src.utils.string_utils import clip_tags, clip_to_budget

logger = logging.getLogger(__name__)

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

# How many people the prompt names. The real limit is the character budget
# below; this only stops a very large roster building a pointless string.
MAX_NAMED_PEOPLE = 12

# A person tag has to reach their species to be worth its tokens. Measured on
# a six-person cast: at 28 characters everyone was named and the dragonborn
# came out as "male", which renders a man; at 44 he keeps "green dragonborn"
# and two of the six are dropped instead. Naming fewer people correctly beats
# naming all of them uselessly - and a cast this size belongs in region mode,
# where each figure has a prompt to itself.
MIN_TAG_CHARS = 44

MAX_PROMPT_CHARS = 480
MAX_TAG_CHARS = 80

# A staged setting is five clauses - place, time, ground, backdrop, light -
# and 80 characters cuts it after the ground, which is exactly the half that
# says where the frame ends. A person tag stays at 80.
MAX_SETTING_CHARS = 170


def _person_tags(person: ShotPerson, budget: int = MAX_TAG_CHARS) -> str:
    """A short visual tag for one person in the shot.

    Both appearance and action, not one or the other. Appearance says who
    they are and action says what they are doing here; with only the first,
    a cast rendered standing in a row looking at the camera, and the
    scene-level action cannot say who is doing what once there are more
    than two of them.

    Args:
        person: Someone in frame.
        budget: Characters this person may use, name included.

    Returns:
        Their name, appearance and action, comma-joined and within budget.
    """
    detail = ", ".join(
        part for part in (person.appearance.strip(), person.action.strip())
        if part
    )
    room = budget - len(person.name) - 2
    kept = clip_tags(detail, room)
    return f"{person.name}, {kept}" if kept else person.name


def _fit_cast(people: Sequence[ShotPerson], room: int) -> str:
    """Name as many people as the remaining budget describes usefully.

    Six people at a hundred characters each came to 604 against a 480
    budget, and the tail is where the setting, the mood and the style live -
    so the render came back as one character in a forest, with no port, no
    night and no group, and the sixth person cut off mid-word. Sharing the
    room out and dropping whoever does not fit keeps the scene intact and
    fails visibly rather than silently.

    Args:
        people: Everyone in frame.
        room: Characters available for the whole cast.

    Returns:
        Semicolon-separated person tags, empty when nobody fits.
    """
    in_frame = [person for person in people if person.name]
    named = in_frame[:MAX_NAMED_PEOPLE]
    share = 0
    while named:
        share = (room - 2 * (len(named) - 1)) // len(named)
        if share >= MIN_TAG_CHARS:
            break
        named.pop()
    if len(named) < len(in_frame):
        # Said out loud. Dropping people quietly is how a scene came back
        # with one character in it and nothing in the job to explain why.
        logger.warning(
            "Scene prompt names %d of %d people - %s do not fit the "
            "character budget. A cast this size belongs in region mode, "
            "where each figure gets a prompt to itself.",
            len(named), len(in_frame),
            ", ".join(person.name for person in in_frame[len(named):]),
        )
    if not named:
        return ""
    return "; ".join(_person_tags(person, share) for person in named)


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
    # The scene is built first and kept whole. Subject and action still lead
    # in the finished string - Stable Diffusion weights early tokens most -
    # but they no longer get to spend the budget the setting needs. Clipping
    # the joined string from the end, which is what this used to do, deleted
    # the setting, the mood, the framing and the style outright as soon as
    # the cast grew past about four people.
    shot_terms, shot_negative = (framing or SceneFraming()).terms()
    scene: List[str] = []
    if analysis.action.strip():
        scene.append(f"({clip_to_budget(analysis.action, 160)}:{ACTION_WEIGHT})")
    if analysis.setting.strip():
        scene.append(clip_to_budget(analysis.setting, MAX_SETTING_CHARS))
    if analysis.mood.strip():
        scene.append(clip_to_budget(analysis.mood, MAX_TAG_CHARS))
    scene.append(shot_terms)
    scene.append(_BASE_STYLE)
    scene_text = ", ".join(part for part in scene if part)

    cast = _fit_cast(people, MAX_PROMPT_CHARS - len(scene_text) - 2)
    positive = f"{cast}, {scene_text}" if cast else scene_text
    negative = f"{_NEGATIVE}, {shot_negative}" if shot_negative else _NEGATIVE
    return positive, negative

def build_environment_prompt(
    analysis: ShotAnalysis, framing: Optional[SceneFraming] = None
) -> str:
    """Build the prompt for the empty scene the cast is painted into.

    Deliberately names nobody. The figures arrive one masked pass at a time,
    and anyone the model puts here first is someone a region has to paint
    over - so this asks for the place and the mood, not the people.

    Args:
        analysis: Setting, action, and mood from the shot analysis.
        framing: Shot type and camera angle, so the empty room is framed the
            same way the figures will be.

    Returns:
        The positive prompt for the environment pass.
    """
    parts: List[str] = []
    if analysis.setting.strip():
        parts.append(clip_to_budget(analysis.setting, MAX_SETTING_CHARS))
    if analysis.mood.strip():
        parts.append(clip_to_budget(analysis.mood, MAX_TAG_CHARS))
    shot_terms, _ = (framing or SceneFraming()).terms()
    parts.append(shot_terms)
    parts.append("empty room, no people, deserted")
    parts.append(_BASE_STYLE)
    return clip_to_budget(", ".join(parts), MAX_PROMPT_CHARS)
