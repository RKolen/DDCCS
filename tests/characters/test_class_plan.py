"""
Test the class plan resolver.

Tests src.characters.class_plan: shaping raw class_grant paragraphs into a
ClassPlan (the taxonomy path) and building a plan from a JSON template (the
fallback). No live Drupal or wiki access is required - grant dicts are crafted
to mirror the GraphQL shape, and the template fallback uses a real class
template from templates/characters/.

What we test:
- Grant paragraphs become skill/tool/equipment choice groups + features
- Grants above the character level are dropped
- The template fallback yields a plan with the class skill choice and equipment

Why we test this:
- Locks the taxonomy-to-plan contract the wizard's skills step depends on
- Ensures the resolver degrades to the template without Drupal
"""

from tests import test_helpers

(
    _plan_from_grants,
    _plan_from_template,
) = test_helpers.safe_from_import(
    "src.characters.class_plan",
    "_plan_from_grants",
    "_plan_from_template",
)

_GRANTS = [
    {
        "level": 1, "grantKind": "skill_choice", "chooseCount": 3,
        "skills": [{"name": "Deception"}, {"name": "Persuasion"}, {"name": "Stealth"}],
    },
    {
        "level": 1, "grantKind": "tool_choice", "chooseCount": 3,
        "text": [{"value": "Tool: Musical Instruments"}],
        "tools": [{"name": "Lute"}, {"name": "Lyre"}],
    },
    {
        "level": 1, "grantKind": "equipment_choice", "gold": 10,
        "equipmentItems": [
            {"title": "Rapier", "itemType": "weapon"},
            {"title": "Lute", "itemType": "item"},
        ],
    },
    {"level": 3, "grantKind": "subclass_choice"},
    {"level": 1, "grantKind": "feature", "text": [{"value": "Bardic Inspiration"}]},
    {"level": 5, "grantKind": "feature", "text": [{"value": "Font of Inspiration"}]},
]


def test_plan_from_grants_shapes_choices():
    """Grant paragraphs become choice groups + features, filtered by level."""
    print("\n[TEST] Class plan - grants to choices")
    plan = _plan_from_grants(_GRANTS, 3)
    assert plan["source"] == "taxonomy", plan
    assert plan["skill_choices"][0]["count"] == 3, plan["skill_choices"]
    assert plan["tool_choices"][0]["label"] == "Tool: Musical Instruments", plan["tool_choices"]
    assert plan["equipment_choices"][0]["gold"] == 10, plan["equipment_choices"]
    assert plan["equipment_choices"][0]["items"][0] == {"name": "Rapier", "item_type": "weapon"}
    assert plan["subclass"] == {"level": 3, "options": []}, plan["subclass"]
    feature_names = [f["name"] for f in plan["features"]]
    assert "Bardic Inspiration" in feature_names, feature_names
    # Font of Inspiration is a level-5 feature, dropped for a level-3 character.
    assert "Font of Inspiration" not in feature_names, feature_names
    print("  [PASS] Grants shaped into choices and level-filtered")


def test_plan_from_template_fallback():
    """The template fallback yields the class skill choice and equipment."""
    print("\n[TEST] Class plan - template fallback")
    plan = _plan_from_template("Bard", 1)
    assert plan["source"] == "template", plan
    assert any(c["id"] == "class" for c in plan["skill_choices"]), plan["skill_choices"]
    assert len(plan["equipment_choices"]) == 1, plan["equipment_choices"]
    print("  [PASS] Template fallback produced a plan")


def run_all_tests():
    """Run all class plan resolver tests."""
    print("=" * 70)
    print("CLASS PLAN RESOLVER TESTS")
    print("=" * 70)

    test_plan_from_grants_shapes_choices()
    test_plan_from_template_fallback()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL CLASS PLAN RESOLVER TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
