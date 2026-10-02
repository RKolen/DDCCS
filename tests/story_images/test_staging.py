"""Unit tests for src.story_images.staging and its console mirror."""

import pathlib
import re
from typing import Any

from tests.test_helpers import setup_test_environment, import_module

setup_test_environment()

staging = import_module("src.story_images.staging")
Setting = staging.Setting
SETTINGS = staging.SETTINGS
MOODS = staging.MOODS
resolve_setting = staging.resolve_setting
resolve_mood = staging.resolve_mood

FRONTEND = (pathlib.Path(__file__).resolve().parents[2]
            / "frontend/src/utils/storyImage.ts")


def _option_values(source: str, const: str) -> list:
    """Pull the `value:` strings out of one exported option table.

    Args:
        source: The TypeScript file's text.
        const: The exported constant's name.

    Returns:
        The values in declaration order, blank entries dropped.
    """
    body = source.split(f"export const {const}", 1)[1].split("];", 1)[0]
    return [v for v in re.findall(r"value:\s*'([^']*)'", body) if v]


def test_describe_orders_the_clauses() -> None:
    """Place and time lead, then ground, backdrop, light."""
    print("\n[TEST] Setting.describe - clause order")
    text = SETTINGS["castle"].describe()
    order = [text.index(part) for part in
             ("castle courtyard", "midday", "flagstone", "curtain wall",
              "overcast")]
    assert order == sorted(order), text
    print("  [OK] Ordered place, time, ground, backdrop, light")


def test_describe_drops_empty_fields() -> None:
    """A setting with no ground or backdrop has no stray commas."""
    print("\n[TEST] Setting.describe - empty fields")
    sparse = Setting(place="a cliff edge", time="dawn", ground="",
                     backdrop="", light="cold light", seat="", seat_noun="")
    assert sparse.describe() == "a cliff edge at dawn, cold light"
    print("  [OK] Empty clauses dropped")


def test_named_setting_is_returned_whole() -> None:
    """A key in the table resolves to that exact entry."""
    print("\n[TEST] resolve_setting - named")
    assert resolve_setting("forest") is SETTINGS["forest"]
    assert resolve_setting("  FOREST  ") is SETTINGS["forest"]
    print("  [OK] Matched, case- and space-insensitive")


def test_free_text_becomes_the_place() -> None:
    """Unknown text is the place, and takes no ground or backdrop with it.

    Those two are the clauses most likely to contradict a location they
    were not written for - bare earth under a ship's deck.
    """
    print("\n[TEST] resolve_setting - free text")
    made = resolve_setting("the deck of a ship")
    assert made.place == "the deck of a ship"
    assert made.ground == "" and made.backdrop == ""
    assert made.light == SETTINGS[staging.DEFAULT_SETTING].light
    assert "bare earth" not in made.describe()
    print("  [OK] Place kept, contradicting clauses dropped")


def test_every_setting_has_a_backdrop_and_a_seat() -> None:
    """A distant thing behind the figures, and something to sit on.

    Without a backdrop the ground runs to the horizon and any location
    reads as a plain; without a seat, a seated character's own caption
    asks for furniture the scene never paints.
    """
    print("\n[TEST] SETTINGS - required clauses")
    for name, setting in SETTINGS.items():
        assert setting.backdrop.strip(), name
        assert "behind the figures" in setting.backdrop, name
        assert setting.seat.strip() and setting.seat_noun.strip(), name
    print(f"  [OK] {len(SETTINGS)} settings carry a backdrop and a seat")


def test_mood_resolves_named_and_free() -> None:
    """A key gives its tone clause; anything else is used verbatim."""
    print("\n[TEST] resolve_mood")
    assert resolve_mood("grim") == MOODS["grim"]
    assert resolve_mood("neutral") == ""
    assert resolve_mood("sun-bleached and silent") == "sun-bleached and silent"
    assert resolve_mood("   ") == ""
    print("  [OK] Named, neutral, free text, and blank")


def test_moods_never_mention_people() -> None:
    """A mood is the air of a place, not an instruction to a figure.

    The scene caption is the one conditioning that is not masked. A tone
    clause naming a person would reach that person and repaint them.
    """
    print("\n[TEST] MOODS - no figures")
    banned = ("face", "figure", "person", "character", "hand", "eyes",
              "standing", "watching")
    for name, text in MOODS.items():
        assert not any(word in text.lower() for word in banned), name
    print(f"  [OK] {len(MOODS)} moods describe only light and colour")


def test_the_caption_gender_is_found_and_only_a_real_word() -> None:
    """"male" and "female" are read as words; "human" is not a man."""
    print("\n[TEST] caption_gender")
    gender = import_module("src.story_images.region_render").caption_gender
    cases = {
        "male, wood elf, long flowing black hair": "male",
        "human female, pale skin, round glasses": "female",
        "female tiefling, violet skin": "female",
        "a grizzled woman in a cloak": "female",
        "human, ranger, weathered cloak": "",
    }
    for caption, expected in cases.items():
        assert gender(caption) == expected, (caption, gender(caption))
    print(f"  [OK] {len(cases)} captions read correctly")


def test_a_male_elf_is_asked_for_as_a_man() -> None:
    """The prompt names the gender plainly and the negative bans the other.

    A lone "male" lost to "elf, long flowing black hair, green eyes", which
    SD 1.5 reads as a woman, and a male elf came back female.
    """
    print("\n[TEST] region_prompt / gender_negative")
    region_render = import_module("src.story_images.region_render")
    person_type = import_module("src.story_images.types").ShotPerson
    elf = person_type.from_dict({
        "name": "Aragorn", "appearance": "male, elf, long flowing black hair"})
    assert ", man, " in region_render.region_prompt(elf, ""), elf
    assert "woman" in region_render.gender_negative(elf)
    hobbit = person_type.from_dict({
        "name": "Frodo Baggins", "appearance": "female halfling, curly hair"})
    assert ", woman, " in region_render.region_prompt(hobbit, "")
    assert region_render.gender_negative(hobbit).startswith("man")
    plain = person_type.from_dict({
        "name": "Aragorn", "appearance": "human ranger, weathered cloak"})
    prompt = region_render.region_prompt(plain, "")
    assert ", man," not in prompt and ", woman," not in prompt, prompt
    assert region_render.gender_negative(plain) == ""
    print("  [OK] Named in the prompt, the other banned; nothing when unstated")


def test_each_character_can_face_a_different_way() -> None:
    """Facing is per character, and two of them differ.

    Every figure is rendered alone against grey and composited, so one angle
    for the whole cast cannot say a group walks away while somebody follows
    them. The composite path passed no angle at all, which is why a render
    came back as a row of people looking at the lens.
    """
    print("\n[TEST] facing - per character, not per scene")
    region_render = import_module("src.story_images.region_render")
    regions_mod = import_module("src.story_images.regions")
    staged = [
        regions_mod.Placement("Aragorn", stance=regions_mod.Stance(facing="behind")),
        regions_mod.Placement("Frodo Baggins",
                              stance=regions_mod.Stance(facing="front")),
    ]
    away, away_negative = region_render.figure_framing(staged, "Aragorn")
    toward, toward_negative = region_render.figure_framing(
        staged, "Frodo Baggins")
    assert "seen from behind" in away, away
    assert "facing the viewer" in toward, toward
    # The angle's own negative has to follow it, or the ban on "back turned"
    # that protects a front view forbids the figure asked to turn away.
    assert "back turned" not in away_negative, away_negative
    assert "back turned" in toward_negative, toward_negative
    print("  [OK] One turned away, one to the camera, negatives follow")


def test_no_facing_adds_nothing() -> None:
    """Empty facing leaves the prompt exactly as it was.

    Every scene rendered so far passed no angle in this path. Turning that
    into a default would restage renders nobody asked to change.
    """
    print("\n[TEST] facing - empty is unchanged")
    region_render = import_module("src.story_images.region_render")
    regions_mod = import_module("src.story_images.regions")
    assert region_render.figure_framing([], "Aragorn") == ("", "")
    unset = [regions_mod.Placement("Aragorn")]
    assert region_render.figure_framing(unset, "Aragorn") == ("", "")
    print("  [OK] No angle terms when none was chosen")


def test_a_turned_skeleton_is_what_controlnet_obeys() -> None:
    """The facing turns the skeleton, not only the words.

    ControlNet obeys geometry. An openpose figure with both ears, both eyes
    and full-width shoulders IS a front view, and "side profile view" in the
    prompt lost to it in every render until the skeleton was turned too.
    """
    print("\n[TEST] facing - the skeleton turns")
    pose = import_module("src.story_images.pose")
    regions_mod = import_module("src.story_images.regions")
    box = regions_mod.Region(name="x", left=0, top=0, width=192, height=614)

    def drawn(facing: str) -> tuple:
        joints = pose.joints_for(box, "standing", facing)
        left, right = joints.get(pose.L_SHOULDER), joints.get(pose.R_SHOULDER)
        span = abs(left[0] - right[0]) if left and right else 0
        ears = sum(1 for e in (pose.L_EAR, pose.R_EAR) if e in joints)
        eyes = sum(1 for e in (pose.L_EYE, pose.R_EYE) if e in joints)
        return span, ears, eyes, pose.NOSE in joints

    front, side, behind = drawn("front"), drawn("side"), drawn("behind")
    assert side[0] < front[0], (front, side)
    # A profile shows one eye and one ear. Drawing both of each is the shape
    # of a head facing the camera, and the shape wins over the caption.
    assert side[1] == 1 and side[2] == 1, side
    assert front[1] == 2 and front[2] == 2, front
    # From behind there is no face at all, and the shoulders open back up.
    assert behind[3] is False and behind[2] == 0, behind
    assert behind[0] == front[0], (front, behind)
    print(f"  [OK] shoulders {front[0]}px front, {side[0]}px side; "
          "one ear and one eye in profile; no face from behind")


def test_no_facing_leaves_the_skeleton_alone() -> None:
    """An unstaged figure is drawn exactly as it always was."""
    print("\n[TEST] facing - skeleton unchanged when unset")
    pose = import_module("src.story_images.pose")
    regions_mod = import_module("src.story_images.regions")
    box = regions_mod.Region(name="x", left=0, top=0, width=192, height=614)
    assert pose.joints_for(box, "standing") == pose.joints_for(
        box, "standing", "")
    print("  [OK] Identical to the untouched skeleton")


def test_every_pose_draws_at_every_facing() -> None:
    """No combination of stance and facing may fail to draw.

    A turned head has no far eye and no far ear - openpose says "occluded"
    by leaving the keypoint out - and the limb loop indexed both endpoints
    without checking. The first profile staged in the console came back as
    `500 KeyError: 15`, the left eye, and lost the whole render.
    """
    print("\n[TEST] pose - every stance draws at every facing")
    pose = import_module("src.story_images.pose")
    regions_mod = import_module("src.story_images.regions")
    box = regions_mod.Region(name="x", left=0, top=0, width=192, height=614)
    drawn = 0
    for stance in pose.POSE_VARIANTS:
        for facing in ("", *pose.TURN_DEGREES):
            for toward in ("", *pose.TOWARD_SIGN):
                held = regions_mod.Stance(stance, facing, toward)
                spot = regions_mod.Placement(name=box.name, stance=held)
                assert pose.figure_pose_png(256, 384, held)
                assert pose.openpose_png(512, 384, [box], [spot])
                drawn += 1
    print(f"  [OK] {drawn} stance/facing/direction combinations all drew")


def _leg_spread(pose_mod: Any, box: Any, stance: str, facing: str,
                toward: str = "") -> int:
    """How far apart the ankles are on screen, in pixels.

    Args:
        pose_mod: The pose module.
        box: The region to stand the figure in.
        stance: Which stance to draw.
        facing: How far the figure is turned.
        toward: Which way that turn points.

    Returns:
        The horizontal distance between the two ankles.
    """
    joints = pose_mod.joints_for(box, stance, facing, toward)
    feet = [joints[pose_mod.R_ANKLE][0], joints[pose_mod.L_ANKLE][0]]
    return max(feet) - min(feet)


def test_a_walk_strides_widest_when_it_is_turned() -> None:
    """A stride is fore-aft, so turning a walker must reveal it, not hide it.

    The walking stance used to splay the legs sideways, because a flat
    layout has nowhere to put a step. That reads from the front and nowhere
    else: the splay is lateral, so a figure staged in profile had it
    squeezed away and came back standing to attention - which is exactly
    what a whole cast set to side profile was asked to avoid.
    """
    print("\n[TEST] pose - a walk strides when turned to profile")
    pose = import_module("src.story_images.pose")
    regions_mod = import_module("src.story_images.regions")
    box = regions_mod.Region(name="x", left=0, top=0, width=200, height=480)
    walking = _leg_spread(pose, box, "walking", "side")
    standing = _leg_spread(pose, box, "standing", "side")
    assert walking > standing * 2, (walking, standing)
    # Both directions are the same walk seen from either side. Joints land
    # on whole pixels, so the mirror can differ by one.
    mirrored = _leg_spread(pose, box, "walking", "side", "left")
    assert abs(mirrored - walking) <= 1, (walking, mirrored)
    print(f"  [OK] Profile stride {walking}px against {standing}px standing, "
          "same both ways")


def test_a_turn_can_point_either_way() -> None:
    """Facing says how far round; direction says which way.

    A cast all set to side profile faced the same way, so a group and the
    person walking up to meet them were drawn in single file.
    """
    print("\n[TEST] pose - left and right are mirror images")
    pose = import_module("src.story_images.pose")
    regions_mod = import_module("src.story_images.regions")
    box = regions_mod.Region(name="x", left=0, top=0, width=200, height=480)
    centre = box.left + box.width / 2
    for facing in ("three_quarter", "side"):
        right = pose.joints_for(box, "standing", facing, "right")
        left = pose.joints_for(box, "standing", facing, "left")
        assert right.keys() != left.keys(), facing
        # The nose leads the face, so it says which way the figure looks.
        assert right[pose.NOSE][0] > centre, facing
        assert left[pose.NOSE][0] < centre, facing
    # Blank keeps whichever way staging already pointed.
    assert (pose.joints_for(box, "standing", "side")
            == pose.joints_for(box, "standing", "side", pose.DEFAULT_TOWARD))
    print("  [OK] Noses point opposite ways, blank is unchanged")


def test_a_back_view_mirrors_left_and_right() -> None:
    """From behind, someone's right arm is on the viewer's right.

    Openpose reads limb identity from colour, so an unmirrored back view
    tells it the figure faces forward with its arms crossed over.
    """
    print("\n[TEST] pose - a back view swaps the sides")
    pose = import_module("src.story_images.pose")
    regions_mod = import_module("src.story_images.regions")
    box = regions_mod.Region(name="x", left=0, top=0, width=200, height=480)
    centre = box.left + box.width / 2
    front = pose.joints_for(box, "standing", "front")
    behind = pose.joints_for(box, "standing", "behind")
    assert front[pose.R_SHOULDER][0] < centre < front[pose.L_SHOULDER][0]
    assert behind[pose.L_SHOULDER][0] < centre < behind[pose.R_SHOULDER][0]
    print("  [OK] Shoulders swap sides between front and back")


def test_a_moved_limb_is_drawn_where_it_was_put() -> None:
    """A dragged joint overrides the stance, and only that joint moves.

    Nine stances cannot say "sword raised, off hand out for balance", so the
    operator can move a limb by hand. The move lands after the turn: it was
    made on the turned skeleton the console drew, and turning it again would
    put the hand somewhere nobody dragged it.
    """
    print("\n[TEST] pose - a moved limb lands where it was put")
    pose = import_module("src.story_images.pose")
    regions_mod = import_module("src.story_images.regions")
    box = regions_mod.Region(name="x", left=0, top=0, width=200, height=600)
    for facing in ("", "side", "behind"):
        plain = pose.joints_for(box, "walking", facing)
        moved = pose.joints_for(box, "walking", facing,
                                limbs={"r_wrist": (0.2, 0.05), "tail": (0, 0)})
        assert moved[pose.R_WRIST] == (100 + 80, 30), (facing, moved[pose.R_WRIST])
        changed = {j for j in plain if plain.get(j) != moved.get(j)}
        assert changed == {pose.R_WRIST}, (facing, changed)
    print("  [OK] Exact position at every facing; nothing else moved")


def test_a_moved_limb_stays_in_reach() -> None:
    """A joint dragged off the figure is held at the edge of its canvas."""
    print("\n[TEST] pose - moved limbs are clamped")
    pose = import_module("src.story_images.pose")
    held = pose.moved_joints({"l_ankle": (9.0, -9.0), "l_knee": (-9.0, 9.0)})
    assert held[pose.L_ANKLE] == (pose.LIMB_REACH, pose.LIMB_TOP), held
    assert held[pose.L_KNEE] == (-pose.LIMB_REACH, pose.LIMB_BOTTOM), held
    stance_type = import_module("src.story_images.regions").Stance
    for stance in pose.POSE_VARIANTS:
        assert pose.figure_pose_png(
            256, 384, stance_type(stance, limbs={"r_elbow": (0.4, -0.1)}))
    print("  [OK] Both extremes held; every stance draws with a move")


def test_console_limb_limits_match_the_renderer() -> None:
    """The joint handles stop where the renderer's clamp does."""
    print("\n[TEST] LIMB_REACH / LIMB_TOP / LIMB_BOTTOM mirror pose.py")
    pose = import_module("src.story_images.pose")
    source = FRONTEND.read_text(encoding="utf-8")
    for name in ("LIMB_REACH", "LIMB_TOP", "LIMB_BOTTOM"):
        found = re.search(rf"export const {name} = (-?[0-9.]+);", source)
        assert found is not None, name
        assert float(found.group(1)) == getattr(pose, name), name
    print("  [OK] All three limits match src/story_images/pose.py")


def test_console_offers_exactly_these_poses() -> None:
    """The wizard's stance list matches the renderer's variants.

    Action text only ever reached the prompt, and a skeleton drawn standing
    beats the word "walking", so a scene asked for on the move came back as
    a line-up. The stance itself had to become a control, and a name the
    console offers that the renderer does not know falls silently back to
    standing.
    """
    print("\n[TEST] POSE_OPTIONS mirrors POSE_VARIANTS")
    pose = import_module("src.story_images.pose")
    source = FRONTEND.read_text(encoding="utf-8")
    assert _option_values(source, "POSE_OPTIONS") == list(pose.POSE_VARIANTS)
    print(f"  [OK] {len(pose.POSE_VARIANTS)} stances, same names and order")


def test_console_offers_exactly_these_directions() -> None:
    """The wizard's turn directions match the renderer's."""
    print("\n[TEST] TOWARD_OPTIONS mirrors TOWARD_SIGN")
    pose = import_module("src.story_images.pose")
    source = FRONTEND.read_text(encoding="utf-8")
    assert _option_values(source, "TOWARD_OPTIONS") == list(pose.TOWARD_SIGN)
    found = re.search(r"export const DEFAULT_TOWARD = '([a-z]+)';", source)
    assert found is not None
    assert found.group(1) == pose.DEFAULT_TOWARD
    print("  [OK] Both directions, and the same default")


def test_console_depth_limits_match_the_layout() -> None:
    """The drag canvas maps travel to the renderer's own depth range."""
    print("\n[TEST] NEAR_DEPTH / FAR_DEPTH mirror the layout")
    regions_mod = import_module("src.story_images.regions")
    source = FRONTEND.read_text(encoding="utf-8")
    for name, value in (("NEAR_DEPTH", regions_mod.NEAR_DEPTH),
                        ("FAR_DEPTH", regions_mod.FAR_DEPTH)):
        found = re.search(rf"export const {name} = ([0-9.]+);", source)
        assert found is not None, name
        assert float(found.group(1)) == value, (name, found.group(1), value)
    print("  [OK] Near and far match src/story_images/regions.py")


def test_console_offers_exactly_these_facings() -> None:
    """The wizard's facing list matches the renderer's angles."""
    print("\n[TEST] FACING_OPTIONS mirrors ANGLES")
    framing = import_module("src.story_images.framing")
    source = FRONTEND.read_text(encoding="utf-8")
    assert _option_values(source, "FACING_OPTIONS") == list(framing.ANGLES)
    print(f"  [OK] {len(framing.ANGLES)} angles, same names and order")


def test_console_offers_exactly_these_settings() -> None:
    """The wizard's setting list matches the renderer's table.

    A name the console offers and the renderer does not know would fall
    through `resolve_setting` to free text and quietly render something
    else - the same failure as a stale enum, with no error.
    """
    print("\n[TEST] SETTING_OPTIONS mirrors SETTINGS")
    source = FRONTEND.read_text(encoding="utf-8")
    assert _option_values(source, "SETTING_OPTIONS") == list(SETTINGS)
    print(f"  [OK] {len(SETTINGS)} settings, same names and order")


def test_console_offers_exactly_these_moods() -> None:
    """The wizard's mood list matches the renderer's table."""
    print("\n[TEST] MOOD_OPTIONS mirrors MOODS")
    source = FRONTEND.read_text(encoding="utf-8")
    assert _option_values(source, "MOOD_OPTIONS") == list(MOODS)
    print(f"  [OK] {len(MOODS)} moods, same names and order")


def run_all_tests() -> None:
    """Run every staging test.

    Without this and the __main__ block below, the subsystem runner starts
    the module with `python -m`, nothing executes, the process exits 0, and
    the suite reports a pass for tests that never ran.
    """
    test_describe_orders_the_clauses()
    test_describe_drops_empty_fields()
    test_named_setting_is_returned_whole()
    test_free_text_becomes_the_place()
    test_every_setting_has_a_backdrop_and_a_seat()
    test_mood_resolves_named_and_free()
    test_moods_never_mention_people()
    test_the_caption_gender_is_found_and_only_a_real_word()
    test_a_male_elf_is_asked_for_as_a_man()
    test_each_character_can_face_a_different_way()
    test_no_facing_adds_nothing()
    test_a_turned_skeleton_is_what_controlnet_obeys()
    test_no_facing_leaves_the_skeleton_alone()
    test_every_pose_draws_at_every_facing()
    test_a_walk_strides_widest_when_it_is_turned()
    test_a_turn_can_point_either_way()
    test_a_back_view_mirrors_left_and_right()
    test_a_moved_limb_is_drawn_where_it_was_put()
    test_a_moved_limb_stays_in_reach()
    test_console_limb_limits_match_the_renderer()
    test_console_offers_exactly_these_poses()
    test_console_offers_exactly_these_directions()
    test_console_depth_limits_match_the_layout()
    test_console_offers_exactly_these_facings()
    test_console_offers_exactly_these_settings()
    test_console_offers_exactly_these_moods()
    print("\n[PASS] All staging tests passed.")


if __name__ == "__main__":
    run_all_tests()
