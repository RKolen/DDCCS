"""Tests for `src.encounters.encounter_scaler`."""

from tests import test_helpers  # configures environment on import

from src.encounters.encounter_scaler import (
    EncounterDifficulty,
    EncounterScaler,
    PartyMember,
    build_party_from_characters,
)
from src.utils.dnd_rules import DifficultyTier

# Suppress unused-import warning; test_helpers is imported for side-effects only
_ = test_helpers


def _make_party(count: int = 4, level: int = 5) -> list:
    """Build a standard test party of Fighter members.

    Args:
        count: Number of party members.
        level: Level for each member.

    Returns:
        List of PartyMember instances.
    """
    return [
        PartyMember(
            name=f"Fighter{i}",
            level=level,
            character_class="Fighter",
            max_hp=40 + level * 5,
            armor_class=16,
        )
        for i in range(count)
    ]


# ---------------------------------------------------------------------------
# PartyMember
# ---------------------------------------------------------------------------

def test_party_member_proficiency_bonus():
    """PartyMember.proficiency_bonus is derived from level."""
    member = PartyMember("Hero", 5, "Fighter", 50, 16)
    assert member.proficiency_bonus == 3

    member_high = PartyMember("Legend", 17, "Paladin", 120, 18)
    assert member_high.proficiency_bonus == 6


# ---------------------------------------------------------------------------
# EncounterScaler properties
# ---------------------------------------------------------------------------

def test_average_level_standard_party():
    """average_level is the mean of all member levels."""
    party = [
        PartyMember("A", 4, "Rogue", 30, 14),
        PartyMember("B", 6, "Cleric", 50, 18),
    ]
    scaler = EncounterScaler(party)
    assert scaler.average_level == 5.0


def test_average_level_empty_party():
    """average_level returns 1.0 for an empty party."""
    scaler = EncounterScaler([])
    assert scaler.average_level == 1.0


def test_party_size():
    """party_size returns the count of members."""
    party = _make_party(4)
    scaler = EncounterScaler(party)
    assert scaler.party_size == 4


# ---------------------------------------------------------------------------
# XP threshold calculation
# ---------------------------------------------------------------------------

def test_party_xp_threshold_standard_party():
    """XP threshold is positive and size-adjusted for a standard party."""
    party = _make_party(4, level=5)
    scaler = EncounterScaler(party)
    threshold = scaler.get_party_xp_threshold(EncounterDifficulty.MEDIUM)
    # 4 members * 500 XP each * 1.0 size mult = 2000
    assert threshold == 2000


def test_party_xp_threshold_scales_with_size():
    """Smaller parties have a lower effective threshold (0.75 mult for duo)."""
    small_party = _make_party(2, level=5)
    large_party = _make_party(5, level=5)

    small_threshold = EncounterScaler(small_party).get_party_xp_threshold(
        EncounterDifficulty.MEDIUM
    )
    large_threshold = EncounterScaler(large_party).get_party_xp_threshold(
        EncounterDifficulty.MEDIUM
    )
    assert small_threshold < large_threshold


# ---------------------------------------------------------------------------
# Encounter assessment
# ---------------------------------------------------------------------------

def test_assess_encounter_trivial():
    """Very low XP produces a TRIVIAL assessment."""
    party = _make_party(4, level=5)
    scaler = EncounterScaler(party)
    metrics = scaler.assess_encounter(enemy_xp_total=10, enemy_count=1)
    assert metrics.difficulty == EncounterDifficulty.TRIVIAL


def test_assess_encounter_deadly():
    """Extremely high XP produces a DEADLY assessment."""
    party = _make_party(4, level=5)
    scaler = EncounterScaler(party)
    metrics = scaler.assess_encounter(enemy_xp_total=50000, enemy_count=1)
    assert metrics.difficulty == EncounterDifficulty.DEADLY


def test_assess_encounter_metrics_fields():
    """EncounterMetrics contains all expected fields with correct types."""
    party = _make_party(4, level=5)
    scaler = EncounterScaler(party)
    metrics = scaler.assess_encounter(enemy_xp_total=500, enemy_count=1)

    assert isinstance(metrics.average_party_level, float)
    assert isinstance(metrics.effective_party_size, float)
    assert isinstance(metrics.suggested_dc_range, tuple)
    assert len(metrics.suggested_dc_range) == 2
    easy_dc, hard_dc = metrics.suggested_dc_range
    assert easy_dc < hard_dc
    assert isinstance(metrics.threat_level, str)
    assert isinstance(metrics.resource_drain_estimate, str)


def test_assess_encounter_dc_range_scales_with_level():
    """Suggested DC range is higher for a higher-level party."""
    low_party = _make_party(4, level=1)
    high_party = _make_party(4, level=20)

    low_metrics = EncounterScaler(low_party).assess_encounter(100)
    high_metrics = EncounterScaler(high_party).assess_encounter(100)

    assert high_metrics.suggested_dc_range[1] > low_metrics.suggested_dc_range[1]


def test_assess_encounter_many_enemies_raises_difficulty():
    """More enemies increase adjusted XP and can raise the difficulty rating."""
    party = _make_party(4, level=5)
    scaler = EncounterScaler(party)

    single = scaler.assess_encounter(enemy_xp_total=500, enemy_count=1)
    many = scaler.assess_encounter(enemy_xp_total=500, enemy_count=15)

    difficulty_order = [
        EncounterDifficulty.TRIVIAL,
        EncounterDifficulty.EASY,
        EncounterDifficulty.MEDIUM,
        EncounterDifficulty.HARD,
        EncounterDifficulty.DEADLY,
    ]
    assert difficulty_order.index(many.difficulty) >= difficulty_order.index(
        single.difficulty
    )


# ---------------------------------------------------------------------------
# DC suggestion
# ---------------------------------------------------------------------------

def test_suggest_encounter_dc_medium():
    """Suggest DC for medium difficulty matches level-scaled value."""
    party = _make_party(4, level=5)
    scaler = EncounterScaler(party)
    dc = scaler.suggest_encounter_dc("skill", DifficultyTier.MEDIUM)
    # Level 5 tiered medium = 15
    assert dc == 15


def test_suggest_encounter_dc_hard():
    """Suggest DC for hard difficulty is greater than medium."""
    party = _make_party(4, level=10)
    scaler = EncounterScaler(party)
    medium_dc = scaler.suggest_encounter_dc("skill", DifficultyTier.MEDIUM)
    hard_dc = scaler.suggest_encounter_dc("skill", DifficultyTier.HARD)
    assert hard_dc > medium_dc


# ---------------------------------------------------------------------------
# build_party_from_characters helper
# ---------------------------------------------------------------------------

def test_build_party_from_characters():
    """build_party_from_characters converts dicts to PartyMember instances."""
    chars = [
        {"name": "Aragorn", "level": 10, "class": "Ranger", "max_hp": 90, "armor_class": 16},
        {"name": "Gandalf", "level": 20, "class": "Wizard", "max_hp": 120, "armor_class": 12},
    ]
    party = build_party_from_characters(chars)
    assert len(party) == 2
    assert party[0].name == "Aragorn"
    assert party[0].level == 10
    assert party[1].character_class == "Wizard"


def test_build_party_missing_fields_uses_defaults():
    """Missing fields in character dicts use sensible defaults."""
    party = build_party_from_characters([{}])
    assert len(party) == 1
    assert party[0].name == "Unknown"
    assert party[0].level == 1
    assert party[0].max_hp == 10
    assert party[0].armor_class == 10


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all_tests():
    """Run all encounter scaler tests."""
    print("=" * 70)
    print("ENCOUNTER SCALER TESTS")
    print("=" * 70)

    test_party_member_proficiency_bonus()
    test_average_level_standard_party()
    test_average_level_empty_party()
    test_party_size()
    test_party_xp_threshold_standard_party()
    test_party_xp_threshold_scales_with_size()
    test_assess_encounter_trivial()
    test_assess_encounter_deadly()
    test_assess_encounter_metrics_fields()
    test_assess_encounter_dc_range_scales_with_level()
    test_assess_encounter_many_enemies_raises_difficulty()
    test_suggest_encounter_dc_medium()
    test_suggest_encounter_dc_hard()
    test_build_party_from_characters()
    test_build_party_missing_fields_uses_defaults()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL ENCOUNTER SCALER TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
