"""Build Stable Diffusion prompts for character portraits from a profile."""

from typing import Any, Dict, List, Tuple

_BASE_STYLE = (
    "fantasy character portrait, digital painting, highly detailed, "
    "dramatic lighting, head and shoulders, sharp focus"
)
_NEGATIVE = (
    "lowres, blurry, deformed, extra limbs, bad anatomy, watermark, text, "
    "signature, multiple people, out of frame"
)


def build_portrait_prompt(profile: Dict[str, Any]) -> Tuple[str, str]:
    """Build (positive, negative) SD prompts from a character profile.

    Args:
        profile: Character fields such as species, lineage, character_class,
            pronouns, background, personality_traits, appearance, arc_summary.

    Returns:
        A (positive_prompt, negative_prompt) pair.

    """
    descriptor = " ".join(
        value
        for value in (
            str(profile.get("lineage") or ""),
            str(profile.get("species") or ""),
            str(profile.get("character_class") or ""),
        )
        if value
    ).strip()

    parts: List[str] = [_BASE_STYLE]
    if descriptor:
        parts.append(descriptor)

    pronouns = str(profile.get("pronouns") or "")
    if pronouns:
        parts.append(f"{pronouns}")

    background = str(profile.get("background") or "")
    if background:
        parts.append(f"{background} background")

    traits = profile.get("personality_traits")
    if isinstance(traits, list) and traits:
        parts.append(", ".join(str(trait) for trait in traits[:3] if trait))

    # Appearance / arc / backstory add flavour; keep it bounded for the encoder.
    flavour = str(
        profile.get("appearance")
        or profile.get("arc_summary")
        or profile.get("backstory")
        or ""
    ).strip()
    if flavour:
        parts.append(flavour[:280])

    positive = ", ".join(part for part in parts if part)
    return positive, _NEGATIVE
