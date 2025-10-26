"""Tests for combat conversion pipeline (parsed actions -> narrative).

This test simulates a parsed combat sequence (as might be produced by a
Fantasy Grounds parser) and verifies that `CombatDescriptor` produces
character-aware narrative fragments that can be combined into a story.
"""
from pathlib import Path
import test_helpers

# Configure test environment for imports
test_helpers.setup_test_environment()

try:
    from src.combat.narrator_descriptions import CombatDescriptor
    from src.characters.consultants.character_profile import CharacterProfile
    from src.characters.consultants.consultant_core import CharacterConsultant
except ImportError as exc:
    print(f"[ERROR] Import failed: {exc}")
    raise


def _load_fixture(name: str) -> CharacterConsultant:
    base = Path(__file__).parent.parent.parent
    fp = base / "game_data" / "characters" / f"{name}.json"
    profile = CharacterProfile.load_from_file(str(fp))
    return CharacterConsultant(profile)


def test_parsed_actions_convert_to_narrative():
    """A small parsed combat sequence should convert into readable narrative."""
    # Load character consultants
    aragorn = _load_fixture("aragorn")
    frodo = _load_fixture("frodo")

    consultants = {aragorn.profile.name: aragorn, frodo.profile.name: frodo}

    descriptor = CombatDescriptor(consultants)

    # Simulated parsed actions
    actions = [
        {"type": "attack", "actor": "Aragorn", "target": "goblin", "roll": 12, "damage": 7},
        {"type": "spell", "actor": "Frodo", "spell": "Healing Word", "healing": 5},
        {"type": "damage", "actor": "goblin", "amount": 3},
    ]

    # Convert each action to narrative using the actor's consultant when available
    fragments = []
    for action in actions:
        actor = action.get("actor")
        consultant = consultants.get(actor)
        frag = descriptor.describe_action(action, consultant=consultant, style="cinematic")
        fragments.append(frag)

    narrative = " ".join(fragments)

    # Assertions: expect character-aware phrasing and amounts preserved
    assert "strikes at goblin" in narrative
    assert "casts Healing Word" in narrative or "casts Healing" in narrative
    assert "a light wound" in narrative or "(3 damage)" in narrative
