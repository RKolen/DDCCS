"""Unit tests for src.story_images.shot and scene_prompt."""

import json

from tests.ai_fixtures import ScriptedAIClient
from tests.test_helpers import setup_test_environment, import_module

setup_test_environment()

types = import_module("src.story_images.types")
shot = import_module("src.story_images.shot")
prompt = import_module("src.story_images.scene_prompt")

RosterEntry = types.RosterEntry
ShotPerson = types.ShotPerson
ShotAnalysis = types.ShotAnalysis
apply_roster = types.apply_roster
build_shot_prompt = shot.build_shot_prompt
parse_shot = shot.parse_shot
analyze_shot = shot.analyze_shot
build_scene_prompt = prompt.build_scene_prompt
SceneFraming = import_module("src.story_images.framing").SceneFraming

ROSTER = [
    RosterEntry(
        name="Aragorn",
        character_id="pc-1",
        portrait_url="https://drupal.test/aragorn.png",
        appearance="weathered ranger",
        is_npc=False,
    ),
    RosterEntry(
        name="Barliman Butterbur",
        character_id="npc-1",
        portrait_url="https://drupal.test/barliman.png",
        appearance="stout innkeeper",
        is_npc=True,
    ),
]


def test_shot_prompt_lists_roster_spellings() -> None:
    """Known names are offered so the model can match Drupal spelling."""
    print("\n[TEST] build_shot_prompt - roster spellings")
    text = build_shot_prompt("Aragorn asked for a room.", "At the Pony", ["Aragorn"])
    assert "Aragorn" in text
    assert "At the Pony" in text
    assert '"people"' in text
    print("  [OK] Event, excerpt, and roster present")


def test_parse_shot_matches_known_names() -> None:
    """A roster name is marked known and gets its portrait."""
    print("\n[TEST] parse_shot - known match")
    raw = json.dumps(
        {
            "setting": "the Prancing Pony common room",
            "action": "Aragorn asks Barliman Butterbur for a room",
            "mood": "firelit, wary",
            "people": [
                {"name": "Aragorn", "role": "asking for lodging"},
                {"name": "Barliman Butterbur", "role": "behind the bar"},
            ],
        }
    )
    analysis = parse_shot(raw, ROSTER)
    assert analysis.setting.startswith("the Prancing Pony")
    assert analysis.people[0].known is True
    assert analysis.people[0].portrait_url.endswith("aragorn.png")
    assert analysis.people[1].is_npc is True
    print("  [OK] Setting and matched portraits")


def test_parse_shot_keeps_unknown_names() -> None:
    """A name not on the roster stays in the shot without likeness."""
    print("\n[TEST] parse_shot - unknown extra")
    raw = json.dumps(
        {
            "setting": "the common room",
            "action": "a stranger watches",
            "mood": "tense",
            "people": [{"name": "a hooded stranger", "role": "watching from a corner"}],
        }
    )
    analysis = parse_shot(raw, ROSTER)
    assert analysis.people[0].known is False
    assert analysis.people[0].portrait_url == ""
    print("  [OK] Unknown extra has no portrait")


def test_analyze_shot_without_ai_is_empty() -> None:
    """No client means an empty analysis, not an error."""
    print("\n[TEST] analyze_shot - no client")
    analysis = analyze_shot(None, "Aragorn waited.", "Watch", ROSTER)
    assert analysis.people == []
    print("  [OK] Empty shot")


def test_analyze_shot_calls_the_model() -> None:
    """A scripted client yields a parsed shot."""
    print("\n[TEST] analyze_shot - scripted client")
    raw = json.dumps(
        {
            "setting": "Bree",
            "action": "Aragorn waits",
            "mood": "rain",
            "people": [{"name": "Aragorn", "role": "waiting"}],
        }
    )
    analysis = analyze_shot(ScriptedAIClient(raw), "Aragorn waits in Bree.", "Watch", ROSTER)
    assert analysis.people[0].name == "Aragorn"
    print("  [OK] Parsed from the scripted response")


def test_scene_prompt_is_a_wide_shot_not_a_portrait() -> None:
    """The negative must not ban multiple people."""
    print("\n[TEST] build_scene_prompt - wide shot")
    analysis = ShotAnalysis(
        setting="the Prancing Pony",
        action="Aragorn speaks with Barliman Butterbur",
        mood="firelit",
    )
    people = [
        ShotPerson(name="Aragorn", appearance="weathered ranger"),
        ShotPerson(name="Barliman Butterbur", appearance="stout innkeeper"),
    ]
    positive, negative = build_scene_prompt(analysis, people)
    # Default framing shows whole figures rather than a portrait crop, and the
    # negative must never ban the crowd a scene is supposed to contain.
    assert "full body shot" in positive
    assert "Aragorn" in positive
    assert "Barliman Butterbur" in positive
    assert "multiple people" not in negative
    assert "two people" not in negative
    print("  [OK] Whole figures, named people, crowd not banned")


def test_scene_prompt_framing_bans_rear_views() -> None:
    """Asking for faces must also ban the back view that SD defaults to."""
    print("\n[TEST] build_scene_prompt - framing")
    analysis = ShotAnalysis(setting="a lamplit street", action="the group walks out")
    people = [ShotPerson(name="Aragorn", appearance="weathered ranger")]

    positive, negative = build_scene_prompt(
        analysis, people, SceneFraming(shot="full", angle="front")
    )
    assert "full body shot" in positive
    assert "faces clearly visible" in positive
    assert "back turned" in negative

    # Choosing "behind" must not then ban itself in the negative.
    _, behind_negative = build_scene_prompt(
        analysis, people, SceneFraming(shot="wide", angle="behind")
    )
    assert "back turned" not in behind_negative
    print("  [OK] Framing terms applied, rear view banned only when unwanted")


def test_apply_roster_fills_likeness_when_a_portrait_exists() -> None:
    """Matching a portraited character turns likeness on."""
    print("\n[TEST] apply_roster - likeness from portrait")
    person = apply_roster(ShotPerson(name="aragorn"), ROSTER)
    assert person.known is True
    assert person.use_likeness is True
    assert person.character_id == "pc-1"
    print("  [OK] Portrait implies likeness")


def test_parse_shot_reads_action_under_either_key() -> None:
    """The model may answer with "action" or the older "role".

    The field has always held "one line on what they are doing in this
    shot"; only the name changed. A payload written against the old key
    must keep working, or a cached prompt silently loses every action.
    """
    print("\n[TEST] parse_shot - action and legacy role key")
    modern = parse_shot(json.dumps({
        "setting": "a road", "action": "they meet", "mood": "",
        "people": [{"name": "Aragorn", "action": "drawing a sword"}],
    }), ROSTER)
    legacy = parse_shot(json.dumps({
        "setting": "a road", "action": "they meet", "mood": "",
        "people": [{"name": "Aragorn", "role": "drawing a sword"}],
    }), ROSTER)
    assert modern.people[0].action == "drawing a sword"
    assert legacy.people[0].action == "drawing a sword"
    print("  [OK] Both keys land in action")


def test_scene_prompt_names_appearance_and_action() -> None:
    """A person tag carries both, not one or the other.

    With appearance alone a cast renders standing in a row; the
    scene-level action cannot say who is doing what once there are more
    than two of them.
    """
    print("\n[TEST] build_scene_prompt - appearance and action together")
    analysis = ShotAnalysis(setting="a road", action="they meet", mood="")
    people = [
        ShotPerson(name="Aragorn", appearance="Human, Ranger",
                   action="drawing a sword"),
        ShotPerson(name="Frodo Baggins", appearance="Halfling, Rogue",
                   action="hiding behind a cart"),
    ]
    positive, _ = build_scene_prompt(analysis, people)
    for fragment in ("Human, Ranger", "drawing a sword",
                     "Halfling, Rogue", "hiding behind a cart"):
        assert fragment in positive, positive
    print("  [OK] Both halves of both people are in the prompt")


def _big_cast() -> list:
    """Six people with full-length appearance tags, as Drupal supplies them."""
    return [
        ShotPerson(name="Aragorn", action="walking",
                   appearance="male, human, ranger, weathered cloak, "
                              "long dark hair, stubble, worn leather"),
        ShotPerson(name="Frodo Baggins", action="walking",
                   appearance="male, halfling, curly brown hair, bare feet, "
                              "small stature, green waistcoat"),
        ShotPerson(name="Gandalf the Grey", action="walking",
                   appearance="male, human, wizard, long grey beard, "
                              "pointed hat, grey robes, tall staff"),
        ShotPerson(name="Barliman Butterbur", action="walking",
                   appearance="male, human, innkeeper, red face, apron, "
                              "balding, stout build"),
        ShotPerson(name="Tobias Stone", action="walking",
                   appearance="male, human, stonemason, broad shoulders, "
                              "dusty tunic, short beard"),
        ShotPerson(name="Rosie Cotton", action="approaching the group",
                   appearance="female, halfling, auburn hair, apron, "
                              "freckles, small stature"),
    ]


def test_a_large_cast_never_clips_the_scene_away() -> None:
    """Setting, mood and style survive however many people are named.

    Six people at a hundred characters each came to 604 against a 480
    budget, and the joined string was then clipped from the end - which is
    where the setting, the mood, the framing and the style all live. The
    render came back as one character in a forest: no port, no night, no
    group, and the sixth person cut off mid-word.
    """
    print("\n[TEST] build_scene_prompt - a large cast keeps the scene")
    analysis = ShotAnalysis(
        setting="the streets of a port city at night",
        action="a group steps out into the cool night air",
        mood="cool, companionable",
    )
    positive, _ = build_scene_prompt(analysis, _big_cast())
    assert len(positive) <= prompt.MAX_PROMPT_CHARS, len(positive)
    for fragment in ("port city", "night air", "cool, companionable",
                     "fantasy illustration"):
        assert fragment in positive, positive
    print("  [OK] Setting, action, mood and style all present")


def test_a_large_cast_names_everyone_or_nobody_by_halves() -> None:
    """Nobody is left as a fragment of a tag.

    "piercing green eyes,, teal" spends tokens on pieces the model has to
    guess at, and the guess put a tiefling's colour on an elf.
    """
    print("\n[TEST] build_scene_prompt - no half-written person")
    analysis = ShotAnalysis(setting="a port city", action="they walk",
                            mood="cool")
    positive, _ = build_scene_prompt(analysis, _big_cast())
    assert ",," not in positive and "; ," not in positive
    assert not positive.rstrip().endswith((",", ";"))
    # Whoever is named is named in full: a bare trailing name is allowed,
    # a half-finished tag is not.
    print("  [OK] No dangling fragments")


def test_small_cast_still_gets_rich_descriptions() -> None:
    """Two people keep their whole appearance; the budget only bites later."""
    print("\n[TEST] build_scene_prompt - small cast unaffected")
    analysis = ShotAnalysis(setting="a port city at night", action="they meet",
                            mood="cool")
    pair = _big_cast()[:2]
    positive, _ = build_scene_prompt(analysis, pair)
    assert "weathered cloak" in positive, positive
    assert "green waistcoat" in positive, positive
    print("  [OK] Full appearance kept for a small cast")


def run_all_tests() -> None:
    """Run all shot and prompt tests."""
    test_shot_prompt_lists_roster_spellings()
    test_parse_shot_matches_known_names()
    test_parse_shot_keeps_unknown_names()
    test_analyze_shot_without_ai_is_empty()
    test_analyze_shot_calls_the_model()
    test_scene_prompt_is_a_wide_shot_not_a_portrait()
    test_scene_prompt_framing_bans_rear_views()
    test_apply_roster_fills_likeness_when_a_portrait_exists()
    test_parse_shot_reads_action_under_either_key()
    test_scene_prompt_names_appearance_and_action()
    test_a_large_cast_never_clips_the_scene_away()
    test_a_large_cast_names_everyone_or_nobody_by_halves()
    test_small_cast_still_gets_rich_descriptions()
    print("\n[PASS] All story-image shot tests passed.")


if __name__ == "__main__":
    run_all_tests()
