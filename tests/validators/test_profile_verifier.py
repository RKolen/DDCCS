"""
Tests for profile_verifier.py and verification_rules.py.

Covers unit-level tests for individual rules, the ProfileVerifier orchestration,
VerificationReport helpers, auto-fix logic, and CLI utilities.
"""

from tests import test_helpers
from src.validation.verification_rules import (
    VerificationIssue,
    VerificationRule,
    _auto_fix_proficiency_bonus,
    _auto_fix_skill_modifiers,
    _check_ability_scores_range,
    _check_ai_config,
    _check_backstory,
    _check_backstory_length,
    _check_background_field,
    _check_bonds,
    _check_feats,
    _check_flaws,
    _check_hp_consistency,
    _check_ideals,
    _check_level_range,
    _check_personality_depth,
    _check_personality_traits,
    _check_primary_ability,
    _check_proficiency_bonus,
    _check_relationship_descriptions,
    _check_relationships,
    _check_skill_modifiers,
    _check_spell_level_vs_character,
    _check_spell_slots,
    _check_subclass,
    _check_typical_ability_scores,
    _check_valid_class,
    build_rules,
)
from src.validation.profile_verifier import (
    ProfileVerifier,
    VerificationReport,
)

test_helpers.setup_test_environment()


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

def _make_char(**kwargs):
    """Return a minimal valid character dict, optionally overriding fields."""
    base = test_helpers.sample_character_data(
        name="Test Hero",
        dnd_class="fighter",
        level=5,
        ability_scores={
            "strength": 16,
            "dexterity": 14,
            "constitution": 14,
            "intelligence": 10,
            "wisdom": 12,
            "charisma": 8,
        },
        overrides={
            "backstory": "A veteran warrior who served the crown for fifteen years.",
            "personality_traits": ["Brave", "Loyal", "Stubborn", "Honourable"],
            "ideals": ["Protect the innocent"],
            "bonds": ["My shield bears my family's crest"],
            "flaws": ["Stubborn to a fault"],
            "feats": ["Alert"],
            "proficiency_bonus": 3,
            "background": "Soldier",
            "skills": {
                # STR 16 = +3, prof +3 -> proficient +6, non-proficient +3
                "Athletics": 5,
                # WIS 12 = +1, prof +3 -> +4 (proficient) correct
                "Perception": 4,
            },
        },
    )
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# Completeness checks
# ---------------------------------------------------------------------------

def test_check_backstory_missing():
    """Missing backstory returns a field string."""
    data = _make_char(backstory="")
    result = _check_backstory(data)
    assert result == "backstory"
    print("[OK] backstory missing detected")


def test_check_backstory_present():
    """Present backstory returns None (no issue)."""
    data = _make_char(backstory="A long story about the hero.")
    result = _check_backstory(data)
    assert result is None
    print("[OK] backstory present - no issue")


def test_check_personality_traits_too_few():
    """Fewer than 2 personality traits triggers the check."""
    data = _make_char(personality_traits=["Brave"])
    result = _check_personality_traits(data)
    assert result == "personality_traits"
    print("[OK] few personality_traits detected")


def test_check_personality_traits_sufficient():
    """Two or more traits returns None."""
    data = _make_char(personality_traits=["Brave", "Loyal"])
    result = _check_personality_traits(data)
    assert result is None
    print("[OK] personality_traits sufficient - no issue")


def test_check_subclass_missing_level3_plus():
    """Level 3+ character without subclass triggers warning."""
    data = _make_char(level=3)
    data.pop("subclass", None)
    result = _check_subclass(data)
    assert result == "subclass"
    print("[OK] missing subclass at level 3 detected")


def test_check_subclass_not_required_below_level3():
    """Level 2 character with no subclass is fine."""
    data = _make_char(level=2)
    data.pop("subclass", None)
    result = _check_subclass(data)
    assert result is None
    print("[OK] subclass not required below level 3 - no issue")


def test_check_subclass_present():
    """Level 5 with subclass is fine."""
    data = _make_char(level=5, subclass="Champion")
    result = _check_subclass(data)
    assert result is None
    print("[OK] subclass present at level 5 - no issue")


def test_check_background_field_missing():
    """Background field missing triggers warning."""
    data = _make_char()
    data.pop("background", None)
    result = _check_background_field(data)
    assert result == "background"
    print("[OK] background field missing detected")


def test_check_ideals_missing():
    """No ideals triggers check."""
    data = _make_char(ideals=[])
    result = _check_ideals(data)
    assert result == "ideals"
    print("[OK] missing ideals detected")


def test_check_bonds_missing():
    """No bonds triggers check."""
    data = _make_char(bonds=[])
    result = _check_bonds(data)
    assert result == "bonds"
    print("[OK] missing bonds detected")


def test_check_flaws_missing():
    """No flaws triggers check."""
    data = _make_char(flaws=[])
    result = _check_flaws(data)
    assert result == "flaws"
    print("[OK] missing flaws detected")


def test_check_feats_missing():
    """No feats triggers suggestion."""
    data = _make_char(feats=[])
    result = _check_feats(data)
    assert result == "feats"
    print("[OK] missing feats detected")


def test_check_relationships_missing():
    """Empty relationships triggers suggestion."""
    data = _make_char(relationships={})
    result = _check_relationships(data)
    assert result == "relationships"
    print("[OK] missing relationships detected")


def test_check_ai_config_missing():
    """No ai_config triggers suggestion."""
    data = _make_char()
    data.pop("ai_config", None)
    result = _check_ai_config(data)
    assert result == "ai_config"
    print("[OK] missing ai_config detected")


# ---------------------------------------------------------------------------
# Consistency checks
# ---------------------------------------------------------------------------

def test_check_proficiency_bonus_correct_level1():
    """Level 1 with +2 proficiency passes."""
    data = _make_char(level=1, proficiency_bonus=2)
    result = _check_proficiency_bonus(data)
    assert result is None
    print("[OK] level 1 proficiency +2 correct")


def test_check_proficiency_bonus_correct_level5():
    """Level 5 with +3 proficiency passes."""
    data = _make_char(level=5, proficiency_bonus=3)
    result = _check_proficiency_bonus(data)
    assert result is None
    print("[OK] level 5 proficiency +3 correct")


def test_check_proficiency_bonus_wrong():
    """Level 5 with +2 proficiency fails."""
    data = _make_char(level=5, proficiency_bonus=2)
    result = _check_proficiency_bonus(data)
    assert isinstance(result, str)
    assert "+2" in result
    print("[OK] wrong proficiency bonus detected")


def test_check_skill_modifiers_consistent():
    """Correctly calculated skill modifiers pass (proficient, non-proficient, or expertise)."""
    # WIS 12 -> modifier +1; proficiency +3
    # Perception proficient:  +1 + 3 = +4
    # Perception expertise:   +1 + 6 = +7
    # Athletics non-proficient (STR 16 = +3): +3
    data = _make_char(
        level=5,
        proficiency_bonus=3,
        ability_scores={
            "strength": 16,
            "dexterity": 14,
            "constitution": 14,
            "intelligence": 10,
            "wisdom": 12,
            "charisma": 8,
        },
        skills={"Perception": 4, "Athletics": 3, "Survival": 7},
    )
    result = _check_skill_modifiers(data)
    assert result is None
    print("[OK] correct skill modifiers pass")


def test_check_skill_modifiers_inconsistent():
    """Skill modifier that cannot result from any formula is flagged."""
    data = _make_char(
        level=5,
        proficiency_bonus=3,
        ability_scores={
            "strength": 16,
            "dexterity": 14,
            "constitution": 14,
            "intelligence": 10,
            "wisdom": 12,
            "charisma": 8,
        },
        skills={"Perception": 99},  # obviously wrong
    )
    result = _check_skill_modifiers(data)
    assert isinstance(result, str)
    assert "Perception" in result
    print("[OK] inconsistent skill modifier detected")


def test_check_hp_consistency_near_average():
    """HP near the expected average passes."""
    # Fighter lvl 5, CON 14 (+2). HP = 10+2 + 4*(6+2) = 12+32 = 44
    data = _make_char(
        dnd_class="fighter",
        level=5,
        ability_scores={
            "strength": 16,
            "dexterity": 14,
            "constitution": 14,
            "intelligence": 10,
            "wisdom": 12,
            "charisma": 8,
        },
        max_hit_points=44,
    )
    result = _check_hp_consistency(data)
    assert result is None
    print("[OK] HP near average passes")


def test_check_spell_slots_within_limits():
    """Spell slots within class/level limit pass."""
    # Ranger level 5 half-caster: {"1": 4, "2": 2}
    data = _make_char(dnd_class="ranger", level=5, spell_slots={"1": 4, "2": 2})
    result = _check_spell_slots(data)
    assert result is None
    print("[OK] valid spell slots pass")


def test_check_spell_slots_exceeds_limit():
    """Spell slots exceeding class/level maximum are flagged."""
    # Ranger level 5 can have at most 4 first-level slots
    data = _make_char(dnd_class="ranger", level=5, spell_slots={"1": 9, "2": 2})
    result = _check_spell_slots(data)
    assert isinstance(result, str)
    assert "level-1" in result
    print("[OK] excess spell slots detected")


# ---------------------------------------------------------------------------
# Rules compliance checks
# ---------------------------------------------------------------------------

def test_check_ability_scores_range_valid():
    """Scores 1-30 pass."""
    data = _make_char(ability_scores={
        "strength": 1, "dexterity": 30, "constitution": 15,
        "intelligence": 10, "wisdom": 10, "charisma": 10
    })
    result = _check_ability_scores_range(data)
    assert result is None
    print("[OK] valid ability score range passes")


def test_check_ability_scores_range_out_of_range():
    """Score of 31 is flagged."""
    data = _make_char(ability_scores={
        "strength": 31, "dexterity": 14, "constitution": 14,
        "intelligence": 10, "wisdom": 12, "charisma": 8
    })
    result = _check_ability_scores_range(data) or ""
    assert result, "Expected check to flag strength=31"
    assert "strength=31" in result
    print("[OK] out-of-range ability score detected")


def test_check_level_range_valid():
    """Levels 1-20 pass."""
    data = _make_char(level=20)
    result = _check_level_range(data)
    assert result is None
    print("[OK] level 20 passes")


def test_check_level_range_too_high():
    """Level 21 is flagged."""
    data = _make_char(level=21)
    result = _check_level_range(data)
    assert result is not None
    print("[OK] level 21 is flagged")


def test_check_valid_class_standard():
    """Standard class names pass."""
    for cls in ("wizard", "Wizard", "Fighter", "ranger"):
        data = _make_char(dnd_class=cls)
        result = _check_valid_class(data)
        assert result is None, f"Expected {cls} to pass, got: {result}"
    print("[OK] standard class names pass")


def test_check_valid_class_unknown():
    """Unknown class name is flagged."""
    data = _make_char(dnd_class="space-marine")
    result = _check_valid_class(data)
    assert result is not None
    print("[OK] unknown class flagged")


def test_check_typical_ability_scores_within_range():
    """Scores 3-20 are considered typical."""
    data = _make_char(ability_scores={
        "strength": 3, "dexterity": 20, "constitution": 14,
        "intelligence": 10, "wisdom": 12, "charisma": 8,
    })
    result = _check_typical_ability_scores(data)
    assert result is None
    print("[OK] typical ability score range passes")


def test_check_spell_level_vs_character_valid():
    """Spell slots within allowed levels pass."""
    # Full caster wizard level 5: can have up to level-3 slots
    data = _make_char(
        dnd_class="wizard", level=5,
        spell_slots={"1": 4, "2": 3, "3": 2}
    )
    result = _check_spell_level_vs_character(data)
    assert result is None
    print("[OK] spell level vs character level passes")


def test_check_spell_level_vs_character_too_high():
    """Spell level exceeding max is flagged."""
    # Wizard level 5 cannot have level-9 slots
    data = _make_char(
        dnd_class="wizard", level=5,
        spell_slots={"1": 4, "2": 3, "3": 2, "9": 1}
    )
    result = _check_spell_level_vs_character(data) or ""
    assert result, "Expected check to flag level-9 slot"
    assert "level-9" in result
    print("[OK] spell level too high detected")


# ---------------------------------------------------------------------------
# Best practices checks
# ---------------------------------------------------------------------------

def test_check_backstory_length_short():
    """Backstory under 100 chars triggers suggestion."""
    data = _make_char(backstory="Short.")
    result = _check_backstory_length(data)
    assert result is not None
    print("[OK] short backstory detected")


def test_check_backstory_length_sufficient():
    """Backstory of 100+ chars is fine."""
    data = _make_char(backstory="A" * 100)
    result = _check_backstory_length(data)
    assert result is None
    print("[OK] sufficient backstory length - no issue")


def test_check_personality_depth_few():
    """Fewer than 4 traits triggers suggestion."""
    data = _make_char(personality_traits=["Brave", "Loyal"])
    result = _check_personality_depth(data)
    assert result is not None
    print("[OK] few personality traits depth flagged")


def test_check_relationship_descriptions_empty():
    """Relationship without description is flagged."""
    data = _make_char(relationships={"Gandalf": "", "Frodo": "Best friend"})
    result = _check_relationship_descriptions(data)
    assert isinstance(result, str)
    assert "Gandalf" in result
    print("[OK] empty relationship description detected")


def test_check_primary_ability_appropriate():
    """Wizard with high intelligence does not trigger suggestion."""
    data = _make_char(
        dnd_class="wizard",
        ability_scores={
            "strength": 8, "dexterity": 14, "constitution": 12,
            "intelligence": 18, "wisdom": 12, "charisma": 10,
        }
    )
    result = _check_primary_ability(data)
    assert result is None
    print("[OK] primary ability check passes for wizard with high INT")


# ---------------------------------------------------------------------------
# Auto-fix tests
# ---------------------------------------------------------------------------

def test_auto_fix_proficiency_bonus_level5():
    """Auto-fix sets proficiency to +3 for level 5."""
    data = {"level": 5, "proficiency_bonus": 2}
    fixed = _auto_fix_proficiency_bonus(data)
    assert fixed is True
    assert data["proficiency_bonus"] == 3
    print("[OK] auto-fix proficiency bonus level 5")


def test_auto_fix_proficiency_bonus_level10():
    """Auto-fix sets proficiency to +4 for level 10."""
    data = {"level": 10, "proficiency_bonus": 2}
    fixed = _auto_fix_proficiency_bonus(data)
    assert fixed is True
    assert data["proficiency_bonus"] == 4
    print("[OK] auto-fix proficiency bonus level 10")


def test_auto_fix_proficiency_bonus_already_correct():
    """Auto-fix returns False when already correct."""
    data = {"level": 1, "proficiency_bonus": 2}
    fixed = _auto_fix_proficiency_bonus(data)
    assert fixed is False
    print("[OK] auto-fix no-ops when proficiency already correct")


def test_auto_fix_skill_modifiers_corrects_value():
    """Auto-fix rounds a clearly wrong modifier to the nearest valid value."""
    # WIS 12 -> +1; proficiency 3
    # Valid values: +1 (no prof), +4 (proficient), +7 (expertise)
    # We set it to 99 which is > proficient_val so it should become +7 (expertise)
    data = {
        "ability_scores": {"wisdom": 12},
        "proficiency_bonus": 3,
        "skills": {"Perception": 99},
    }
    fixed = _auto_fix_skill_modifiers(data)
    assert fixed is True
    # 99 > proficient_val (+4), so expertise: +1 + 2*3 = +7
    assert data["skills"]["Perception"] == 7
    print("[OK] auto-fix skill modifier corrects value")


def test_auto_fix_skill_modifiers_noop_when_correct():
    """Auto-fix returns False when all modifiers are already correct."""
    data = {
        "ability_scores": {"wisdom": 12},
        "proficiency_bonus": 3,
        "skills": {"Perception": 4},  # +1 + 3 = +4 correct
    }
    fixed = _auto_fix_skill_modifiers(data)
    assert fixed is False
    print("[OK] auto-fix skill modifier no-ops when correct")


# ---------------------------------------------------------------------------
# ProfileVerifier tests
# ---------------------------------------------------------------------------

def test_profile_verifier_no_issues_on_complete_character():
    """A well-formed character should produce no errors or warnings."""
    # Load the real aragorn.json which is a complete, rules-compliant character.
    # Skills: Survival 10 (WIS 15 +2, expertise +8), Perception 6 (proficient), etc.
    data = test_helpers.load_game_character("aragorn")
    verifier = ProfileVerifier()
    report = verifier.verify(data)

    assert not report.errors, f"Unexpected errors: {[i.message for i in report.errors]}"
    print("[OK] complete character has no errors")


def test_profile_verifier_detects_errors():
    """Verifier reports errors for a character with obvious rule violations."""
    data = _make_char(
        level=25,   # out of range
        ability_scores={
            "strength": 50,  # out of range
            "dexterity": 14,
            "constitution": 14,
            "intelligence": 10,
            "wisdom": 12,
            "charisma": 8,
        },
    )
    verifier = ProfileVerifier()
    report = verifier.verify(data)
    assert report.errors, "Expected errors for invalid level and ability score"
    print("[OK] verifier detects rule errors")


def test_verification_report_summary():
    """VerificationReport summary counts match issues list."""
    issue_e = VerificationIssue("R001", "rules", "error", "Error msg", "field")
    issue_w = VerificationIssue("R002", "completeness", "warning", "Warn msg", "field")
    issue_s = VerificationIssue("R003", "best_practices", "suggestion", "Sug msg", "field")

    report = VerificationReport(
        character_name="Test",
        issues=[issue_e, issue_w, issue_s],
        total_checks=10,
    )

    assert len(report.errors) == 1
    assert len(report.warnings) == 1
    assert len(report.suggestions) == 1
    assert report.passed == 7
    print("[OK] VerificationReport summary counts correct")


def test_verification_report_filter_errors_only():
    """Filtering to 'error' returns only errors."""
    issue_e = VerificationIssue("R001", "rules", "error", "Error", "f")
    issue_w = VerificationIssue("R002", "completeness", "warning", "Warn", "f")

    report = VerificationReport(
        character_name="Test",
        issues=[issue_e, issue_w],
        total_checks=5,
    )

    filtered = report.filter_by_severity("error")
    assert len(filtered.issues) == 1
    assert filtered.issues[0].severity == "error"
    print("[OK] filter_by_severity('error') returns only errors")


def test_verification_report_to_dict():
    """to_dict returns well-structured dictionary."""
    issue = VerificationIssue("R001", "rules", "error", "Error msg", "level")
    report = VerificationReport(
        character_name="Gandalf",
        issues=[issue],
        total_checks=5,
    )
    data = report.to_dict()
    assert data["character"] == "Gandalf"
    assert data["summary"]["errors"] == 1
    assert data["summary"]["total_checks"] == 5
    assert len(data["issues"]) == 1
    assert data["issues"][0]["rule_id"] == "R001"
    print("[OK] to_dict returns correct structure")


def test_verification_report_to_terminal():
    """to_terminal returns a non-empty string with expected sections."""
    issue = VerificationIssue(
        "CONS001", "consistency", "error", "Proficiency mismatch", "proficiency_bonus"
    )
    report = VerificationReport(
        character_name="Frodo",
        issues=[issue],
        total_checks=10,
    )
    output = report.to_terminal()
    assert "Frodo" in output
    assert "CONSISTENCY" in output
    assert "[ERROR]" in output
    assert "Summary" in output
    print("[OK] to_terminal produces expected output")


def test_build_rules_returns_populated_list():
    """build_rules returns a non-empty list of VerificationRule instances."""
    rules = build_rules()
    assert len(rules) > 0
    rule_ids = {r.rule_id for r in rules}
    # Check a sample of expected rule IDs
    assert "COMP001" in rule_ids
    assert "CONS001" in rule_ids
    assert "RULE001" in rule_ids
    assert "BEST001" in rule_ids
    print(f"[OK] build_rules returns {len(rules)} rules")


def test_profile_verifier_auto_fix_returns_corrected_copy():
    """auto_fix returns a deep copy with corrections applied."""
    data = {"name": "Tester", "level": 10, "proficiency_bonus": 2, "skills": {}}
    verifier = ProfileVerifier()
    fixed = verifier.auto_fix(data)

    # Original not mutated
    assert data["proficiency_bonus"] == 2
    # Fixed copy is corrected
    assert fixed["proficiency_bonus"] == 4
    print("[OK] auto_fix returns corrected deep copy without mutating original")


def test_verification_rule_check_passes():
    """VerificationRule.check returns None when the check_func returns None."""
    rule = VerificationRule(
        rule_id="TEST001",
        category="test",
        severity="error",
        message="Should not trigger",
        check_func=lambda _: None,
    )
    result = rule.check({"name": "Hero"})
    assert result is None
    print("[OK] VerificationRule.check returns None on pass")


def test_verification_rule_check_fails():
    """VerificationRule.check returns VerificationIssue when check_func returns a string."""
    rule = VerificationRule(
        rule_id="TEST002",
        category="test",
        severity="warning",
        message="Field missing",
        check_func=lambda _: "some_field",
    )
    issue = rule.check({"name": "Hero"})
    assert issue is not None
    assert isinstance(issue, VerificationIssue)
    assert issue.rule_id == "TEST002"
    assert issue.severity == "warning"
    print("[OK] VerificationRule.check returns VerificationIssue on failure")


# ---------------------------------------------------------------------------
# Run all tests
# ---------------------------------------------------------------------------

def run_all_tests():
    """Run all test functions and report results."""
    tests = [
        test_check_backstory_missing,
        test_check_backstory_present,
        test_check_personality_traits_too_few,
        test_check_personality_traits_sufficient,
        test_check_subclass_missing_level3_plus,
        test_check_subclass_not_required_below_level3,
        test_check_subclass_present,
        test_check_background_field_missing,
        test_check_ideals_missing,
        test_check_bonds_missing,
        test_check_flaws_missing,
        test_check_feats_missing,
        test_check_relationships_missing,
        test_check_ai_config_missing,
        test_check_proficiency_bonus_correct_level1,
        test_check_proficiency_bonus_correct_level5,
        test_check_proficiency_bonus_wrong,
        test_check_skill_modifiers_consistent,
        test_check_skill_modifiers_inconsistent,
        test_check_hp_consistency_near_average,
        test_check_spell_slots_within_limits,
        test_check_spell_slots_exceeds_limit,
        test_check_ability_scores_range_valid,
        test_check_ability_scores_range_out_of_range,
        test_check_level_range_valid,
        test_check_level_range_too_high,
        test_check_valid_class_standard,
        test_check_valid_class_unknown,
        test_check_typical_ability_scores_within_range,
        test_check_spell_level_vs_character_valid,
        test_check_spell_level_vs_character_too_high,
        test_check_backstory_length_short,
        test_check_backstory_length_sufficient,
        test_check_personality_depth_few,
        test_check_relationship_descriptions_empty,
        test_check_primary_ability_appropriate,
        test_auto_fix_proficiency_bonus_level5,
        test_auto_fix_proficiency_bonus_level10,
        test_auto_fix_proficiency_bonus_already_correct,
        test_auto_fix_skill_modifiers_corrects_value,
        test_auto_fix_skill_modifiers_noop_when_correct,
        test_profile_verifier_no_issues_on_complete_character,
        test_profile_verifier_detects_errors,
        test_verification_report_summary,
        test_verification_report_filter_errors_only,
        test_verification_report_to_dict,
        test_verification_report_to_terminal,
        test_build_rules_returns_populated_list,
        test_profile_verifier_auto_fix_returns_corrected_copy,
        test_verification_rule_check_passes,
        test_verification_rule_check_fails,
    ]

    passed = 0
    failed = 0
    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except AssertionError as exc:
            print(f"[FAIL] {test_fn.__name__}: {exc}")
            failed += 1
        except (RuntimeError, TypeError, ValueError, KeyError, AttributeError) as exc:
            print(f"[ERROR] {test_fn.__name__}: {type(exc).__name__}: {exc}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Profile Verifier Tests: {passed} passed, {failed} failed")
    print(f"{'='*60}")
    return failed == 0
