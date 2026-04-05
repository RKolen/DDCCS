"""Unit tests for src.spells.spell_registry.

Tests cover:
- SpellComponents, SpellCasting, SpellMeta, CustomSpell dataclasses
- SpellRegistry CRUD operations and index lookups
- get_spell_registry / reset_spell_registry singleton
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from tests.test_helpers import make_test_spell, registry_in_temp, run_test_functions
from src.spells.spell_registry import (
    CustomSpell,
    SpellCasting,
    SpellComponents,
    SpellMeta,
    SpellRegistry,
    get_spell_registry,
    reset_spell_registry,
)


# ---------------------------------------------------------------------------
# SpellComponents
# ---------------------------------------------------------------------------

def test_spell_components_defaults():
    """SpellComponents should default to False/empty."""
    comp = SpellComponents()
    assert comp.verbal is False
    assert comp.somatic is False
    assert comp.material == ""


def test_spell_components_from_dict():
    """SpellComponents.from_dict should parse all fields."""
    comp = SpellComponents.from_dict({"verbal": True, "somatic": True, "material": "obsidian"})
    assert comp.verbal is True
    assert comp.somatic is True
    assert comp.material == "obsidian"


def test_spell_components_from_dict_non_dict():
    """SpellComponents.from_dict with a non-dict returns defaults."""
    comp = SpellComponents.from_dict("invalid")
    assert comp.verbal is False


def test_spell_components_to_dict():
    """SpellComponents.to_dict should include all three keys."""
    comp = SpellComponents(verbal=True, material="scale")
    result = comp.to_dict()
    assert result["verbal"] is True
    assert result["material"] == "scale"
    assert "somatic" in result


# ---------------------------------------------------------------------------
# CustomSpell
# ---------------------------------------------------------------------------

def test_custom_spell_to_dict_roundtrip():
    """CustomSpell should round-trip through to_dict / from_dict."""
    original = CustomSpell(
        name="Void Bolt", level=3, school="necromancy",
        description="A bolt of void energy.",
        classes=["sorcerer", "warlock"],
        casting=SpellCasting(casting_time="1 action", range="120 feet"),
        meta=SpellMeta(aliases=["vb", "void-bolt"]),
    )
    restored = CustomSpell.from_dict(original.to_dict())
    assert restored.name == original.name
    assert restored.level == original.level
    assert restored.school == original.school
    assert restored.meta.aliases == original.meta.aliases
    assert restored.classes == original.classes


def test_custom_spell_get_all_names():
    """get_all_names should include canonical name, lowercase, and aliases."""
    spell = CustomSpell(
        name="Void Bolt", level=3, school="necromancy", description="desc",
        casting=SpellCasting(), meta=SpellMeta(aliases=["VB"]),
    )
    names = spell.get_all_names()
    assert "Void Bolt" in names
    assert "void bolt" in names
    assert "VB" in names
    assert "vb" in names


# ---------------------------------------------------------------------------
# SpellRegistry – basic CRUD
# ---------------------------------------------------------------------------

def test_registry_add_and_has_spell():
    """add_spell / has_spell should register and detect spells."""
    reg = registry_in_temp(tempfile.mkdtemp())
    reg.add_spell(make_test_spell("Void Bolt", 3, "necromancy"))
    assert reg.has_spell("Void Bolt")
    assert reg.has_spell("void bolt")


def test_registry_get_spell_by_canonical():
    """get_spell should return spell by canonical name."""
    reg = registry_in_temp(tempfile.mkdtemp())
    reg.add_spell(make_test_spell("Fire Ball", 3, "evocation"))
    result = reg.get_spell("Fire Ball")
    assert result is not None
    assert result.name == "Fire Ball"


def test_registry_get_spell_by_alias():
    """get_spell should resolve aliases to the canonical spell."""
    reg = registry_in_temp(tempfile.mkdtemp())
    reg.add_spell(CustomSpell(
        name="Void Bolt", level=3, school="necromancy", description="desc",
        casting=SpellCasting(), meta=SpellMeta(aliases=["vb"]),
    ))
    result = reg.get_spell("vb")
    assert result is not None
    assert result.name == "Void Bolt"


def test_registry_get_spell_missing():
    """get_spell should return None for unknown names."""
    assert registry_in_temp(tempfile.mkdtemp()).get_spell("NonExistent") is None


def test_registry_remove_spell():
    """remove_spell should delete the spell and all its aliases."""
    reg = registry_in_temp(tempfile.mkdtemp())
    reg.add_spell(CustomSpell(
        name="Void Bolt", level=3, school="necromancy", description="desc",
        casting=SpellCasting(), meta=SpellMeta(aliases=["vb"]),
    ))
    assert reg.remove_spell("Void Bolt") is True
    assert not reg.has_spell("Void Bolt")
    assert not reg.has_spell("vb")


def test_registry_remove_nonexistent():
    """remove_spell should return False when spell does not exist."""
    assert registry_in_temp(tempfile.mkdtemp()).remove_spell("Ghost") is False


def test_registry_count():
    """count property should reflect the number of registered spells."""
    reg = registry_in_temp(tempfile.mkdtemp())
    assert reg.count == 0
    reg.add_spell(make_test_spell("A"))
    assert reg.count == 1
    reg.add_spell(make_test_spell("B", school="illusion"))
    assert reg.count == 2


def test_registry_get_all_spells():
    """get_all_spells should return all registered spells."""
    reg = registry_in_temp(tempfile.mkdtemp())
    reg.add_spell(make_test_spell("Spell A"))
    reg.add_spell(make_test_spell("Spell B"))
    names = {s.name for s in reg.get_all_spells()}
    assert "Spell A" in names
    assert "Spell B" in names


# ---------------------------------------------------------------------------
# SpellRegistry – index lookups
# ---------------------------------------------------------------------------

def test_registry_get_spells_by_school():
    """get_spells_by_school should return only matching spells."""
    reg = registry_in_temp(tempfile.mkdtemp())
    reg.add_spell(make_test_spell("Shadow Ray", school="illusion"))
    reg.add_spell(make_test_spell("Fire Bolt", school="evocation"))
    results = reg.get_spells_by_school("illusion")
    assert len(results) == 1
    assert results[0].name == "Shadow Ray"


def test_registry_get_spells_by_level():
    """get_spells_by_level should filter by level."""
    reg = registry_in_temp(tempfile.mkdtemp())
    reg.add_spell(make_test_spell("Cantrip A", level=0))
    reg.add_spell(make_test_spell("Level3 A", level=3))
    cantrips = reg.get_spells_by_level(0)
    assert any(s.name == "Cantrip A" for s in cantrips)
    assert not any(s.name == "Level3 A" for s in cantrips)


def test_registry_get_spells_by_class():
    """get_spells_by_class should return spells available to that class."""
    reg = registry_in_temp(tempfile.mkdtemp())
    reg.add_spell(CustomSpell(
        name="Warlock Only", level=1, school="evocation", description="desc",
        classes=["warlock"], casting=SpellCasting(), meta=SpellMeta(),
    ))
    reg.add_spell(CustomSpell(
        name="Wizard Only", level=1, school="evocation", description="desc",
        classes=["wizard"], casting=SpellCasting(), meta=SpellMeta(),
    ))
    names = {s.name for s in reg.get_spells_by_class("warlock")}
    assert "Warlock Only" in names
    assert "Wizard Only" not in names


def test_registry_get_spells_by_tag():
    """get_spells_by_tag should return spells matching the tag."""
    reg = registry_in_temp(tempfile.mkdtemp())
    reg.add_spell(CustomSpell(
        name="Dmg Spell", level=1, school="evocation", description="d",
        casting=SpellCasting(), meta=SpellMeta(tags=["damage"]),
    ))
    reg.add_spell(CustomSpell(
        name="Buff Spell", level=1, school="transmutation", description="b",
        casting=SpellCasting(), meta=SpellMeta(tags=["buff"]),
    ))
    damage_spells = reg.get_spells_by_tag("damage")
    assert any(s.name == "Dmg Spell" for s in damage_spells)
    assert not any(s.name == "Buff Spell" for s in damage_spells)


# ---------------------------------------------------------------------------
# SpellRegistry – search
# ---------------------------------------------------------------------------

def test_registry_search_by_name():
    """search_spells should match partial spell names."""
    reg = registry_in_temp(tempfile.mkdtemp())
    reg.add_spell(make_test_spell("Void Bolt"))
    reg.add_spell(make_test_spell("Void Shield", school="abjuration"))
    names = {s.name for s in reg.search_spells("Void")}
    assert "Void Bolt" in names
    assert "Void Shield" in names


def test_registry_search_by_description():
    """search_spells should match text in the description."""
    reg = registry_in_temp(tempfile.mkdtemp())
    reg.add_spell(CustomSpell(
        name="Radiant Ray", level=2, school="evocation",
        description="Fires a beam of radiant light.",
        casting=SpellCasting(), meta=SpellMeta(),
    ))
    assert len(reg.search_spells("radiant")) == 1


def test_registry_search_no_match():
    """search_spells should return an empty list when nothing matches."""
    reg = registry_in_temp(tempfile.mkdtemp())
    reg.add_spell(make_test_spell())
    assert not reg.search_spells("xyznomatch")


# ---------------------------------------------------------------------------
# SpellRegistry – persistence
# ---------------------------------------------------------------------------

def test_registry_persists_to_disk():
    """add_spell should write to disk; a fresh registry should load it."""
    tmp = tempfile.mkdtemp()
    with patch("src.spells.spell_registry.get_game_data_path", return_value=tmp):
        reg = SpellRegistry()
        reg.add_spell(make_test_spell("Persist Spell"))
        reg2 = SpellRegistry()
    assert reg2.has_spell("Persist Spell")


def test_registry_creates_default_file():
    """SpellRegistry should create custom_spells.json when none exists."""
    tmp = tempfile.mkdtemp()
    expected = Path(tmp) / "spells" / "custom_spells.json"
    with patch("src.spells.spell_registry.get_game_data_path", return_value=tmp):
        SpellRegistry()
    assert expected.exists()
    data = json.loads(expected.read_text(encoding="utf-8"))
    assert data["spells"] == []


def test_registry_loads_existing_file():
    """SpellRegistry should parse spells from an existing registry file."""
    tmp = tempfile.mkdtemp()
    spells_dir = Path(tmp) / "spells"
    spells_dir.mkdir()
    registry_file = spells_dir / "custom_spells.json"
    spell_data = {
        "registry_version": "1.0", "last_updated": "", "source": "homebrew",
        "spells": [make_test_spell("File Spell").to_dict()],
        "spell_groups": [],
    }
    registry_file.write_text(json.dumps(spell_data), encoding="utf-8")
    with patch("src.spells.spell_registry.get_game_data_path", return_value=tmp):
        reg = SpellRegistry()
    assert reg.has_spell("File Spell")


# ---------------------------------------------------------------------------
# Singleton helpers
# ---------------------------------------------------------------------------

def test_get_spell_registry_returns_same_instance():
    """get_spell_registry should return the same object on repeated calls."""
    reset_spell_registry()
    assert get_spell_registry() is get_spell_registry()


def test_reset_spell_registry_creates_fresh_instance():
    """reset_spell_registry should cause get_spell_registry to build a new one."""
    reset_spell_registry()
    reg1 = get_spell_registry()
    reset_spell_registry()
    reg2 = get_spell_registry()
    assert reg1 is not reg2


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_test_functions([
        test_spell_components_defaults,
        test_spell_components_from_dict,
        test_spell_components_from_dict_non_dict,
        test_spell_components_to_dict,
        test_custom_spell_to_dict_roundtrip,
        test_custom_spell_get_all_names,
        test_registry_add_and_has_spell,
        test_registry_get_spell_by_canonical,
        test_registry_get_spell_by_alias,
        test_registry_get_spell_missing,
        test_registry_remove_spell,
        test_registry_remove_nonexistent,
        test_registry_count,
        test_registry_get_all_spells,
        test_registry_get_spells_by_school,
        test_registry_get_spells_by_level,
        test_registry_get_spells_by_class,
        test_registry_get_spells_by_tag,
        test_registry_search_by_name,
        test_registry_search_by_description,
        test_registry_search_no_match,
        test_registry_persists_to_disk,
        test_registry_creates_default_file,
        test_registry_loads_existing_file,
        test_get_spell_registry_returns_same_instance,
        test_reset_spell_registry_creates_fresh_instance,
    ], cleanup=reset_spell_registry)
