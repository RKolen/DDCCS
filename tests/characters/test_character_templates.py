"""
Tests for the character template system (D&D 2024).

What we test:
- Loading individual class templates
- Listing available templates
- Level-scaling calculations (HP, proficiency bonus, spell slots, features)
- Building character data from a template (TemplateOptions API)
- validate_character_template() validator

Why we test this:
- Templates are the foundation of the character creation wizard.
- Level scaling must match D&D 2024 rules exactly.
- Validation prevents malformed templates from reaching production.
"""

from pathlib import Path
from typing import Dict, Any

from src.characters.character_template import (
    PROFICIENCY_BONUS_BY_LEVEL,
    ASI_LEVELS,
    TemplateOptions,
    calculate_modifier,
    calculate_hit_points,
    get_proficiency_bonus,
    get_class_features_up_to_level,
    get_spell_slots_for_level,
    load_template,
    list_available_templates,
    build_character_data_from_template,
)
from src.validation.character_validator import validate_character_template
from src.utils.path_utils import get_character_templates_dir


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TEMPLATES_DIR = Path(get_character_templates_dir())

ALL_CLASSES = [
    "barbarian", "bard", "cleric", "druid", "fighter",
    "monk", "paladin", "ranger", "rogue", "sorcerer",
    "warlock", "wizard",
]


def _load(class_name: str) -> Dict[str, Any]:
    """Load a template and assert it is not None."""
    template = load_template(class_name)
    assert template is not None, f"Template '{class_name}' failed to load"
    return template


def _build(class_name: str, options: TemplateOptions) -> Dict[str, Any]:
    """Build character data from a class template using the given options."""
    template = _load(class_name)
    return build_character_data_from_template(template=template, options=options)


def _default_options(
    name: str = "TestChar",
    race: str = "Human",
    level: int = 1,
    background: str = "Soldier",
    subclass: str = "",
) -> TemplateOptions:
    """Return a TemplateOptions with sensible defaults for testing."""
    return TemplateOptions(name=name, race=race, level=level,
                           background=background, subclass=subclass or None)


# ---------------------------------------------------------------------------
# Template loading
# ---------------------------------------------------------------------------

def test_load_template_fighter():
    """Fighter template loads and contains required keys."""
    print("\n[TEST] Load fighter template")
    template = _load("fighter")
    assert template["class"] == "Fighter"
    assert template["hit_die"] == 10
    assert "Strength" in template["primary_abilities"]


def test_load_template_wizard():
    """Wizard template loads with spellcasting block."""
    print("\n[TEST] Load wizard template")
    template = _load("wizard")
    assert template["class"] == "Wizard"
    assert template["hit_die"] == 6
    assert "spellcasting" in template
    assert template["spellcasting"]["ability"] == "Intelligence"


def test_load_template_rogue():
    """Rogue template loads with correct hit die."""
    print("\n[TEST] Load rogue template")
    template = _load("rogue")
    assert template["class"] == "Rogue"
    assert template["hit_die"] == 8


def test_load_template_all_classes():
    """Every core class template loads successfully."""
    print("\n[TEST] Load all class templates")
    for class_name in ALL_CLASSES:
        template = load_template(class_name)
        assert template is not None, f"Template missing: {class_name}"
        assert "class" in template
        assert "hit_die" in template


def test_load_template_nonexistent():
    """Loading a template for an unknown class returns None."""
    print("\n[TEST] Load nonexistent template")
    result = load_template("artificer_2099")
    assert result is None


def test_list_available_templates():
    """list_available_templates returns all 12 core classes."""
    print("\n[TEST] List available templates")
    templates = list_available_templates()
    assert len(templates) >= 12
    names_lower = [t.lower() for t in templates]
    for cls in ALL_CLASSES:
        assert cls in names_lower, f"Template missing from list: {cls}"


def test_all_subclasses_at_level_3():
    """Every class template specifies subclass at level 3 (2024 rules)."""
    print("\n[TEST] All subclasses at level 3")
    for class_name in ALL_CLASSES:
        template = _load(class_name)
        subclass_info = template.get("subclass_options", {})
        level = subclass_info.get("level")
        assert level == 3, (
            f"{class_name}: expected subclass_options.level=3, got {level}"
        )


def test_all_backgrounds_are_2024_valid():
    """All recommended backgrounds exist in the 2024 PHB list."""
    print("\n[TEST] Recommended backgrounds are 2024-valid")
    valid_backgrounds = {
        "Acolyte", "Artisan", "Charlatan", "Criminal", "Entertainer",
        "Farmer", "Guard", "Hermit", "Noble", "Sage", "Sailor",
        "Soldier", "Wayfarer", "Scribe",
    }
    for class_name in ALL_CLASSES:
        template = _load(class_name)
        for bg in template.get("recommended_backgrounds", []):
            assert bg in valid_backgrounds, (
                f"{class_name}: background '{bg}' is not a 2024 PHB background"
            )


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

def test_template_schema_validation_all():
    """All class templates pass validate_character_template."""
    print("\n[TEST] Template schema validation")
    for class_name in ALL_CLASSES:
        template = _load(class_name)
        valid, errors = validate_character_template(template, class_name)
        assert valid, f"{class_name} failed validation: {errors}"


def test_template_schema_validation_missing_required_field():
    """Template missing 'hit_die' fails validation with a clear error."""
    print("\n[TEST] Validation catches missing hit_die")
    bad_template = {"name": "Test", "class": "Fighter", "primary_abilities": []}
    valid, errors = validate_character_template(bad_template)
    assert not valid
    assert any("hit_die" in e for e in errors)


def test_template_schema_validation_invalid_hit_die():
    """Template with hit_die=7 fails validation."""
    print("\n[TEST] Validation catches invalid hit_die")
    bad_template = {
        "name": "Test", "class": "Fighter", "hit_die": 7,
        "primary_abilities": ["Strength"],
    }
    valid, errors = validate_character_template(bad_template)
    assert not valid
    assert any("hit_die" in e for e in errors)


# ---------------------------------------------------------------------------
# Level scaling - proficiency bonus
# ---------------------------------------------------------------------------

def test_proficiency_bonus_level_1():
    """Proficiency bonus at level 1 is 2."""
    print("\n[TEST] Proficiency bonus level 1")
    assert get_proficiency_bonus(1) == 2


def test_proficiency_bonus_level_5():
    """Proficiency bonus at level 5 is 3."""
    print("\n[TEST] Proficiency bonus level 5")
    assert get_proficiency_bonus(5) == 3


def test_proficiency_bonus_level_17():
    """Proficiency bonus at level 17 is 6."""
    print("\n[TEST] Proficiency bonus level 17")
    assert get_proficiency_bonus(17) == 6


def test_proficiency_bonus_all_levels():
    """Proficiency bonus table covers all 20 levels and only increases."""
    print("\n[TEST] Proficiency bonus table completeness")
    assert len(PROFICIENCY_BONUS_BY_LEVEL) == 20
    previous = 0
    for lvl in range(1, 21):
        pb = PROFICIENCY_BONUS_BY_LEVEL[lvl]
        assert pb >= previous
        previous = pb


def test_proficiency_bonus_invalid_level():
    """get_proficiency_bonus raises ValueError for level 0 and 21."""
    print("\n[TEST] Proficiency bonus invalid level")
    try:
        get_proficiency_bonus(0)
        assert False, "Expected ValueError for level 0"
    except ValueError:
        pass
    try:
        get_proficiency_bonus(21)
        assert False, "Expected ValueError for level 21"
    except ValueError:
        pass


# ---------------------------------------------------------------------------
# Level scaling - hit points
# ---------------------------------------------------------------------------

def test_calculate_modifier():
    """Ability modifier calculations match expected values."""
    print("\n[TEST] calculate_modifier")
    assert calculate_modifier(10) == 0
    assert calculate_modifier(8) == -1
    assert calculate_modifier(16) == 3
    assert calculate_modifier(20) == 5


def test_calculate_hit_points_level_1_fighter():
    """Fighter (d10) at level 1 with CON 15 (mod +2) has 12 HP."""
    print("\n[TEST] HP level 1 fighter CON 15")
    hp = calculate_hit_points(hit_die=10, constitution_score=15, level=1)
    assert hp == 12  # 10 + 2


def test_calculate_hit_points_level_10_fighter():
    """Fighter (d10) at level 10 with CON 14 (mod +2) has correct HP."""
    print("\n[TEST] HP level 10 fighter")
    # Level 1: 10 + 2 = 12; levels 2-10 (9 levels): (6 + 2) * 9 = 72; total = 84
    hp = calculate_hit_points(hit_die=10, constitution_score=14, level=10)
    assert hp == 84


def test_calculate_hit_points_level_1_wizard():
    """Wizard (d6) at level 1 with CON 14 (mod +2) has 8 HP."""
    print("\n[TEST] HP level 1 wizard")
    hp = calculate_hit_points(hit_die=6, constitution_score=14, level=1)
    assert hp == 8  # 6 + 2


def test_calculate_hit_points_minimum():
    """HP is always at least 1 per level even with severe CON penalty."""
    print("\n[TEST] HP minimum 1 per level")
    hp = calculate_hit_points(hit_die=6, constitution_score=1, level=5)
    assert hp >= 5


# ---------------------------------------------------------------------------
# Level scaling - class features
# ---------------------------------------------------------------------------

def test_get_class_features_up_to_level():
    """Returns all features gained at or below the target level."""
    print("\n[TEST] Class features up to level")
    features = {"1": ["Feature A"], "3": ["Feature B"], "5": ["Feature C"]}
    result = get_class_features_up_to_level(features, 3)
    assert "Feature A" in result
    assert "Feature B" in result
    assert "Feature C" not in result


def test_class_features_fighter_level_5():
    """Fighter at level 5 has Second Wind and Extra Attack."""
    print("\n[TEST] Fighter features at level 5")
    template = _load("fighter")
    features = get_class_features_up_to_level(template["class_features"], 5)
    assert "Second Wind" in features
    assert "Extra Attack" in features


# ---------------------------------------------------------------------------
# Level scaling - spell slots
# ---------------------------------------------------------------------------

def test_spell_slots_wizard_level_1():
    """Wizard at level 1 has 2 first-level spell slots."""
    print("\n[TEST] Wizard spell slots level 1")
    template = _load("wizard")
    slots = get_spell_slots_for_level(template.get("spellcasting"), 1)
    assert slots.get("1") == 2


def test_spell_slots_wizard_level_9():
    """Wizard at level 9 has 4/3/3/3/1 spell slots."""
    print("\n[TEST] Wizard spell slots level 9")
    template = _load("wizard")
    slots = get_spell_slots_for_level(template.get("spellcasting"), 9)
    assert slots.get("1") == 4
    assert slots.get("5") == 1


def test_spell_slots_cleric_level_5():
    """Cleric (full caster) at level 5 has 3rd-level slots."""
    print("\n[TEST] Cleric spell slots level 5")
    template = _load("cleric")
    slots = get_spell_slots_for_level(template.get("spellcasting"), 5)
    assert slots.get("3") == 2


def test_spell_slots_ranger_half_caster():
    """Ranger (half caster) has no slots at level 1, gains them at level 2."""
    print("\n[TEST] Ranger half-caster spell slots")
    template = _load("ranger")
    slots_1 = get_spell_slots_for_level(template.get("spellcasting"), 1)
    assert not slots_1
    slots_2 = get_spell_slots_for_level(template.get("spellcasting"), 2)
    assert slots_2.get("1") == 2


def test_spell_slots_warlock_pact_magic():
    """Warlock pact magic uses a single slot level at a time."""
    print("\n[TEST] Warlock pact magic slots")
    template = _load("warlock")
    slots_1 = get_spell_slots_for_level(template.get("spellcasting"), 1)
    assert slots_1.get("1") == 1
    slots_5 = get_spell_slots_for_level(template.get("spellcasting"), 5)
    assert slots_5.get("3") == 2


def test_spell_slots_fighter_no_spellcasting():
    """Fighter (non-caster) returns empty spell slots."""
    print("\n[TEST] Fighter has no spell slots")
    template = _load("fighter")
    slots = get_spell_slots_for_level(template.get("spellcasting"), 10)
    assert not slots


# ---------------------------------------------------------------------------
# build_character_data_from_template
# ---------------------------------------------------------------------------

def test_build_character_data_fighter_level_1():
    """Fighter character data at level 1 has correct structure."""
    print("\n[TEST] Build fighter character data level 1")
    data = _build("fighter", _default_options(name="Thorin", race="Dwarf", level=1))
    assert data["name"] == "Thorin"
    assert data["species"] == "Dwarf"
    assert data["dnd_class"] == "Fighter"
    assert data["level"] == 1
    assert data["max_hit_points"] > 0
    assert data["proficiency_bonus"] == 2
    assert "strength" in data["ability_scores"]


def test_build_character_data_wizard_level_5():
    """Wizard at level 5 has spell slots and spellcasting features."""
    print("\n[TEST] Build wizard character data level 5")
    data = _build("wizard", _default_options(name="Gandalf", race="Human", level=5))
    assert data["level"] == 5
    assert data["proficiency_bonus"] == 3
    assert "1" in data["spell_slots"]


def test_build_character_data_invalid_level():
    """build_character_data_from_template raises ValueError for level 0."""
    print("\n[TEST] Build character data invalid level")
    template = _load("fighter")
    try:
        build_character_data_from_template(
            template=template,
            options=TemplateOptions(name="Bad", level=0),
        )
        assert False, "Expected ValueError for level 0"
    except ValueError:
        pass


def test_build_character_data_custom_ability_scores():
    """Custom ability scores override template defaults."""
    print("\n[TEST] Build character with custom ability scores")
    template = _load("fighter")
    custom = {"strength": 18, "dexterity": 12, "constitution": 16,
               "intelligence": 8, "wisdom": 10, "charisma": 8}
    options = TemplateOptions(name="Conan", race="Human", level=1, ability_scores=custom)
    data = build_character_data_from_template(template=template, options=options)
    assert data["ability_scores"]["strength"] == 18


def test_build_character_data_subclass():
    """Subclass is stored in character data when provided."""
    print("\n[TEST] Build character with subclass")
    template = _load("fighter")
    options = TemplateOptions(name="Knight", race="Human", level=5, subclass="Champion")
    data = build_character_data_from_template(template=template, options=options)
    assert data["subclass"] == "Champion"


# ---------------------------------------------------------------------------
# Character data structure tests (formerly CharacterProfile.from_template)
# ---------------------------------------------------------------------------

def test_character_data_from_template_fighter():
    """Fighter character data at level 3 has correct fields."""
    print("\n[TEST] Character data from fighter template")
    opts = _default_options(name="Boromir", race="Human", level=3, background="Soldier")
    data = _build("fighter", opts)
    assert data["name"] == "Boromir"
    assert data["level"] == 3
    assert data["species"] == "Human"
    assert data["dnd_class"] == "Fighter"
    assert data["max_hit_points"] > 0
    assert data["proficiency_bonus"] == 2


def test_character_data_from_template_wizard():
    """Wizard character data at level 7 has spellcasting data."""
    print("\n[TEST] Character data from wizard template")
    data = _build("wizard", _default_options(name="Merlin", race="Elf", level=7))
    assert data["level"] == 7
    assert data["spell_slots"]


def test_character_data_from_template_with_subclass():
    """Subclass is stored in character data."""
    print("\n[TEST] Character data with subclass")
    template = _load("rogue")
    options = TemplateOptions(name="Bilbo", race="Halfling", level=5, subclass="Thief")
    data = build_character_data_from_template(template=template, options=options)
    assert data["subclass"] == "Thief"


def test_asi_levels_correct():
    """ASI_LEVELS matches expected D&D 2024 pattern."""
    print("\n[TEST] ASI levels")
    assert ASI_LEVELS == [4, 8, 12, 16, 19]
