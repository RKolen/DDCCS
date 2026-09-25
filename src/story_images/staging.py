"""Named settings and moods for a story scene.

The shot analysis writes a setting and a mood as free prose, which is right
when nobody is watching and wrong the moment an operator wants the same
duel in a castle instead of a field. This module is the vocabulary they can
pick from: a small table of places, a smaller one of tones, and a rule for
anything not in either.

A setting is six fields rather than one sentence, because the order of the
clauses is load-bearing. CLIP reads a caption in sequence, so the same words
composed differently render a different picture, and a single prose blob
cannot be varied one part at a time.

``backdrop`` is the field that earns its keep. Something standing far behind
the figures is what gives the empty middle of the frame somewhere to go;
without one the ground runs to the horizon and a courtyard reads as a plain.

``seat`` and ``seat_noun`` are the same object said twice: once for the scene,
which paints it, and once for whoever is sitting on it, whose own caption
would otherwise ask for a stone bench in the middle of a forest.
"""

from dataclasses import dataclass, replace
from typing import Dict

# Kept out of the setting text. The scene prompt adds its own style tail, and
# a setting that carried one too would say it twice.
_JOIN = ", "


@dataclass(frozen=True)
class Setting:
    """One place a scene can happen in."""

    place: str
    time: str
    ground: str
    backdrop: str
    light: str
    seat: str
    seat_noun: str

    def describe(self) -> str:
        """The setting as one caption clause.

        Returns:
            Place, time, ground, backdrop and light, in that order, with
            empty fields dropped.
        """
        parts = (f"{self.place} at {self.time}" if self.time else self.place,
                 self.ground, self.backdrop, self.light)
        return _JOIN.join(part for part in parts if part)


SETTINGS: Dict[str, Setting] = {
    "yard": Setting(
        place="a deserted dirt sparring ground", time="late afternoon",
        ground="empty bare earth",
        backdrop="a distant stone boundary wall far behind the figures",
        light="long warm sunlight",
        seat="a low stone bench, weathered stone block, flat seat",
        seat_noun="a stone bench"),
    "castle": Setting(
        place="a deserted castle courtyard", time="midday",
        ground="worn flagstone paving",
        backdrop="a high battlemented curtain wall far behind the figures",
        light="overcast grey daylight, soft shadows",
        seat="a low stone bench, carved stone block, flat seat",
        seat_noun="a stone bench"),
    "forest": Setting(
        place="a deserted forest clearing", time="morning light",
        ground="moss and fallen leaves",
        backdrop="tall pine trunks far behind the figures",
        light="dappled green light through the canopy",
        seat="a fallen mossy log, rough bark, flat top",
        seat_noun="a fallen log"),
    "ruins": Setting(
        place="a deserted ruined temple floor", time="late afternoon",
        ground="cracked flagstones and rubble",
        backdrop="toppled columns far behind the figures",
        light="dusty shafts of low sunlight",
        seat="a broken column drum, weathered stone cylinder, flat top",
        seat_noun="a fallen column"),
    "snow": Setting(
        place="a deserted snowfield", time="winter dusk",
        ground="trampled snow",
        backdrop="a dark pine forest far behind the figures",
        light="flat cold light, pale sky",
        seat="a snow-covered boulder, rounded grey stone, flat top",
        seat_noun="a snowy boulder"),
    "hall": Setting(
        place="a deserted great hall", time="night",
        ground="a stone flagstone floor",
        backdrop="tall pillars and hanging banners far behind the figures",
        light="warm torchlight, deep shadow",
        seat="a long wooden bench, dark planks, flat seat",
        seat_noun="a wooden bench"),
    "tavern": Setting(
        place="a deserted tavern common room", time="evening",
        ground="a worn plank floor",
        backdrop="a stone hearth and shuttered windows behind the figures",
        light="low firelight, warm shadow",
        seat="a heavy wooden stool, turned legs, round top",
        seat_noun="a wooden stool"),
    "road": Setting(
        place="a deserted country road", time="early morning",
        ground="rutted dirt and grass verges",
        backdrop="low hills and hedgerows far behind the figures",
        light="thin pale sunlight, long shadows",
        seat="a mossy milestone, squared grey stone, flat top",
        seat_noun="a low stone"),
}

# Tone as light and colour. Deliberately nothing about who is in the frame:
# a mood belongs to the air of a place, and a phrase that reaches a figure
# repaints the figure.
MOODS: Dict[str, str] = {
    "neutral": "",
    "tense": "heavy still air, hard shadows, muted desaturated colour",
    "heroic": "bright rim light, clean saturated colour, wind in the air",
    "grim": "overcast gloom, drifting ash, cold desaturated colour",
    "warm": "golden hour glow, soft haze, warm saturated colour",
    "eerie": "thin mist, sickly green cast, long distorted shadows",
    "peaceful": "even soft light, gentle colour, still air",
}

DEFAULT_SETTING = "yard"


def resolve_setting(name: str) -> Setting:
    """A named preset, or free text used as the place.

    Anything not in the table is taken literally, so a one-off location
    needs no entry. It keeps the default's time, light and seat and drops
    the ground and backdrop - those are the two clauses most likely to
    contradict a place they were not written for.

    Args:
        name: A key in `SETTINGS`, or a free-text place description.

    Returns:
        The named setting, or one built around the given text.
    """
    known = SETTINGS.get(name.strip().lower())
    if known is not None:
        return known
    return replace(SETTINGS[DEFAULT_SETTING], place=name.strip(),
                   ground="", backdrop="")


def resolve_mood(name: str) -> str:
    """A named mood, or free text used as the tone clause.

    Args:
        name: A key in `MOODS`, or a free-text tone description.

    Returns:
        The tone clause, empty when nothing was asked for.
    """
    key = name.strip().lower()
    if key in MOODS:
        return MOODS[key]
    return name.strip()


def setting_names() -> list[str]:
    """Every named setting, for an operator to choose from.

    Returns:
        The preset keys, in table order.
    """
    return list(SETTINGS)


def mood_names() -> list[str]:
    """Every named mood, for an operator to choose from.

    Returns:
        The preset keys, in table order.
    """
    return list(MOODS)
