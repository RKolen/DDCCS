"""
D&D 5e Character Profile Verification Rules.

Defines all verification rules for checking character profile completeness,
consistency, and rules compliance. Verification is distinct from validation -
validation ensures data integrity while verification ensures data quality.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from src.utils.dnd_rules import calculate_modifier, get_proficiency_bonus

# ---------------------------------------------------------------------------
# Spell slot tables - PHB 5e
# ---------------------------------------------------------------------------

# Full casters: Bard, Cleric, Druid, Sorcerer, Wizard
_FULL_CASTER_SLOTS: Dict[int, Dict[str, int]] = {
    1:  {"1": 2},
    2:  {"1": 3},
    3:  {"1": 4, "2": 2},
    4:  {"1": 4, "2": 3},
    5:  {"1": 4, "2": 3, "3": 2},
    6:  {"1": 4, "2": 3, "3": 3},
    7:  {"1": 4, "2": 3, "3": 3, "4": 1},
    8:  {"1": 4, "2": 3, "3": 3, "4": 2},
    9:  {"1": 4, "2": 3, "3": 3, "4": 3, "5": 1},
    10: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2},
    11: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1},
    12: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1},
    13: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1},
    14: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1},
    15: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1, "8": 1},
    16: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1, "8": 1},
    17: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2, "6": 1, "7": 1, "8": 1, "9": 1},
    18: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 3, "6": 1, "7": 1, "8": 1, "9": 1},
    19: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 3, "6": 2, "7": 1, "8": 1, "9": 1},
    20: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 3, "6": 2, "7": 2, "8": 1, "9": 1},
}

# Half casters: Paladin, Ranger (use level // 2 with full-caster table)
_HALF_CASTER_SLOTS: Dict[int, Dict[str, int]] = {
    1:  {},
    2:  {"1": 2},
    3:  {"1": 3},
    4:  {"1": 3},
    5:  {"1": 4, "2": 2},
    6:  {"1": 4, "2": 2},
    7:  {"1": 4, "2": 3},
    8:  {"1": 4, "2": 3},
    9:  {"1": 4, "2": 3, "3": 2},
    10: {"1": 4, "2": 3, "3": 2},
    11: {"1": 4, "2": 3, "3": 3},
    12: {"1": 4, "2": 3, "3": 3},
    13: {"1": 4, "2": 3, "3": 3, "4": 1},
    14: {"1": 4, "2": 3, "3": 3, "4": 1},
    15: {"1": 4, "2": 3, "3": 3, "4": 2},
    16: {"1": 4, "2": 3, "3": 3, "4": 2},
    17: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 1},
    18: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 1},
    19: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2},
    20: {"1": 4, "2": 3, "3": 3, "4": 3, "5": 2},
}

# Warlock pact magic slots: (slot_level, number_of_slots)
_WARLOCK_SLOTS: Dict[int, tuple] = {
    1:  (1, 1),
    2:  (1, 2),
    3:  (2, 2),
    4:  (2, 2),
    5:  (3, 2),
    6:  (3, 2),
    7:  (4, 2),
    8:  (4, 2),
    9:  (5, 2),
    10: (5, 2),
    11: (5, 3),
    12: (5, 3),
    13: (5, 3),
    14: (5, 3),
    15: (5, 3),
    16: (5, 3),
    17: (5, 4),
    18: (5, 4),
    19: (5, 4),
    20: (5, 4),
}

# Class type mapping
FULL_CASTERS = {"bard", "cleric", "druid", "sorcerer", "wizard"}
HALF_CASTERS = {"paladin", "ranger"}
WARLOCKS = {"warlock"}
NON_CASTERS = {"barbarian", "fighter", "monk", "rogue"}

# Class primary abilities (used in best-practices suggestion)
CLASS_PRIMARY_ABILITIES: Dict[str, str] = {
    "barbarian": "strength",
    "bard": "charisma",
    "cleric": "wisdom",
    "druid": "wisdom",
    "fighter": "strength",
    "monk": "dexterity",
    "paladin": "charisma",
    "ranger": "dexterity",
    "rogue": "dexterity",
    "sorcerer": "charisma",
    "warlock": "charisma",
    "wizard": "intelligence",
}

# Skills and their governing ability
SKILL_ABILITIES: Dict[str, str] = {
    "Athletics": "strength",
    "Acrobatics": "dexterity",
    "Sleight of Hand": "dexterity",
    "Stealth": "dexterity",
    "Arcana": "intelligence",
    "History": "intelligence",
    "Investigation": "intelligence",
    "Nature": "intelligence",
    "Religion": "intelligence",
    "Animal Handling": "wisdom",
    "Insight": "wisdom",
    "Medicine": "wisdom",
    "Perception": "wisdom",
    "Survival": "wisdom",
    "Deception": "charisma",
    "Intimidation": "charisma",
    "Performance": "charisma",
    "Persuasion": "charisma",
}

# Hit die average by class
CLASS_HIT_DIE_AVERAGE: Dict[str, int] = {
    "barbarian": 7,
    "fighter": 6,
    "paladin": 6,
    "ranger": 6,
    "bard": 5,
    "cleric": 5,
    "druid": 5,
    "monk": 5,
    "rogue": 5,
    "warlock": 5,
    "sorcerer": 4,
    "wizard": 4,
}

# Hit die first-level max by class
CLASS_HIT_DIE_MAX: Dict[str, int] = {
    "barbarian": 12,
    "fighter": 10,
    "paladin": 10,
    "ranger": 10,
    "bard": 8,
    "cleric": 8,
    "druid": 8,
    "monk": 8,
    "rogue": 8,
    "warlock": 8,
    "sorcerer": 6,
    "wizard": 6,
}


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class VerificationIssue:
    """Represents a single verification finding."""

    rule_id: str
    category: str
    severity: str  # "error", "warning", "suggestion"
    message: str
    field: str
    suggestion: str = ""
    auto_fixable: bool = False


@dataclass
class VerificationRule:
    """A single verification rule with check and optional auto-fix logic."""

    rule_id: str
    category: str
    severity: str
    message: str
    check_func: Callable[[Dict[str, Any]], Optional[str]]
    suggestion: str = ""
    auto_fix_func: Optional[Callable[[Dict[str, Any]], bool]] = field(
        default=None, repr=False
    )

    @property
    def auto_fixable(self) -> bool:
        """True when an auto-fix function is registered for this rule."""
        return self.auto_fix_func is not None

    def check(self, data: Dict[str, Any]) -> Optional[VerificationIssue]:
        """Run the check function.

        Args:
            data: Character data dictionary.

        Returns:
            A VerificationIssue if the check failed, otherwise None.
        """
        detail = self.check_func(data)
        if detail is None:
            return None
        return VerificationIssue(
            rule_id=self.rule_id,
            category=self.category,
            severity=self.severity,
            message=self.message if not detail else f"{self.message}: {detail}",
            field=detail,
            suggestion=self.suggestion,
            auto_fixable=self.auto_fixable,
        )


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _get_background(data: Dict[str, Any]) -> str:
    """Return backstory text regardless of which key holds it."""
    for key in ("backstory", "background_story"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _get_class_lower(data: Dict[str, Any]) -> str:
    """Return the character's class as a lowercase string."""
    return str(data.get("dnd_class", "")).lower()


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------

# -- Completeness --

def _check_backstory(data: Dict[str, Any]) -> Optional[str]:
    if not _get_background(data):
        return "backstory"
    return None


def _check_personality_traits(data: Dict[str, Any]) -> Optional[str]:
    traits = data.get("personality_traits", [])
    if not isinstance(traits, list) or len(traits) < 2:
        return "personality_traits"
    return None


def _check_subclass(data: Dict[str, Any]) -> Optional[str]:
    level = data.get("level", 1)
    if isinstance(level, int) and level >= 3 and not data.get("subclass"):
        return "subclass"
    return None


def _check_background_field(data: Dict[str, Any]) -> Optional[str]:
    bg = data.get("background")
    if not bg or not str(bg).strip():
        return "background"
    return None


def _check_ideals(data: Dict[str, Any]) -> Optional[str]:
    ideals = data.get("ideals", [])
    if not isinstance(ideals, list) or not ideals:
        return "ideals"
    return None


def _check_bonds(data: Dict[str, Any]) -> Optional[str]:
    bonds = data.get("bonds", [])
    if not isinstance(bonds, list) or not bonds:
        return "bonds"
    return None


def _check_flaws(data: Dict[str, Any]) -> Optional[str]:
    flaws = data.get("flaws", [])
    if not isinstance(flaws, list) or not flaws:
        return "flaws"
    return None


def _check_feats(data: Dict[str, Any]) -> Optional[str]:
    feats = data.get("feats", [])
    if not isinstance(feats, list) or not feats:
        return "feats"
    return None


def _check_relationships(data: Dict[str, Any]) -> Optional[str]:
    rels = data.get("relationships", {})
    if not isinstance(rels, dict) or not rels:
        return "relationships"
    return None


def _check_ai_config(data: Dict[str, Any]) -> Optional[str]:
    if not data.get("ai_config"):
        return "ai_config"
    return None


# -- Consistency --

def _check_proficiency_bonus(data: Dict[str, Any]) -> Optional[str]:
    level = data.get("level")
    current = data.get("proficiency_bonus")
    if not isinstance(level, int) or current is None:
        return None
    expected = get_proficiency_bonus(level)
    if current != expected:
        return f"proficiency_bonus (expected +{expected}, found +{current})"
    return None


def _check_skill_modifiers(data: Dict[str, Any]) -> Optional[str]:
    """Check that each skill modifier is defensible given ability scores.

    Accepts non-proficient, proficient, and expertise (double proficiency)
    values, as all three are standard D&D 5e options.
    """
    skills = data.get("skills", {})
    ability_scores = data.get("ability_scores", {})
    proficiency = data.get("proficiency_bonus", 2)

    if not isinstance(skills, dict) or not isinstance(ability_scores, dict):
        return None

    bad_skills: List[str] = []
    for skill, modifier in skills.items():
        ability = SKILL_ABILITIES.get(skill)
        if ability is None or ability not in ability_scores:
            continue
        ability_mod = calculate_modifier(ability_scores[ability])
        # Valid values:
        #   ability_mod              - not proficient
        #   ability_mod + proficiency - proficient
        #   ability_mod + 2*proficiency - expertise
        valid_values = {
            ability_mod,
            ability_mod + proficiency,
            ability_mod + 2 * proficiency,
        }
        if not isinstance(modifier, int) or modifier not in valid_values:
            bad_skills.append(
                f"{skill} (got {modifier:+d}, "
                f"expected {ability_mod:+d}, "
                f"{ability_mod + proficiency:+d}, "
                f"or {ability_mod + 2 * proficiency:+d})"
            )

    if bad_skills:
        return "; ".join(bad_skills)
    return None


def _check_hp_consistency(data: Dict[str, Any]) -> Optional[str]:
    """Check HP is within a reasonable range for class/level/constitution."""
    level = data.get("level")
    hp = data.get("max_hit_points")
    dnd_class = _get_class_lower(data)
    ability_scores = data.get("ability_scores", {})

    if not isinstance(level, int) or not isinstance(hp, int):
        return None
    if dnd_class not in CLASS_HIT_DIE_AVERAGE:
        return None

    con_score = ability_scores.get("constitution", 10)
    con_mod = calculate_modifier(con_score) if isinstance(con_score, int) else 0
    first_level_hp = CLASS_HIT_DIE_MAX.get(dnd_class, 8) + con_mod
    avg_hp = first_level_hp + (level - 1) * (CLASS_HIT_DIE_AVERAGE[dnd_class] + con_mod)
    # Allow a broad tolerance: +/- (level * 2) for rolled HP or manual entry
    tolerance = level * 2
    if abs(hp - avg_hp) > tolerance:
        return (
            f"max_hit_points (rough average for {dnd_class} lvl {level} "
            f"is ~{avg_hp}, found {hp})"
        )
    return None


def _check_spell_slots(data: Dict[str, Any]) -> Optional[str]:
    """Check spell slots do not exceed the class/level maximum."""
    level = data.get("level")
    dnd_class = _get_class_lower(data)
    spell_slots = data.get("spell_slots", {})

    if not isinstance(level, int) or not isinstance(spell_slots, dict):
        return None
    if not spell_slots:
        return None  # No slots present - handled elsewhere

    if dnd_class in FULL_CASTERS:
        allowed = _FULL_CASTER_SLOTS.get(level, {})
    elif dnd_class in HALF_CASTERS:
        allowed = _HALF_CASTER_SLOTS.get(level, {})
    elif dnd_class in WARLOCKS:
        slot_level, num_slots = _WARLOCK_SLOTS.get(level, (1, 1))
        allowed = {str(slot_level): num_slots}
    else:
        return None  # Non-caster; no slots expected

    violations: List[str] = []
    for slot_lvl, count in spell_slots.items():
        max_count = allowed.get(str(slot_lvl), 0)
        if isinstance(count, int) and count > max_count:
            violations.append(
                f"level-{slot_lvl} slots (max {max_count}, found {count})"
            )

    if violations:
        return "; ".join(violations)
    return None


# -- Rules compliance --

def _check_ability_scores_range(data: Dict[str, Any]) -> Optional[str]:
    ability_scores = data.get("ability_scores", {})
    if not isinstance(ability_scores, dict):
        return None
    bad: List[str] = []
    for stat, val in ability_scores.items():
        if isinstance(val, int) and not 1 <= val <= 30:
            bad.append(f"{stat}={val}")
    return ", ".join(bad) if bad else None


def _check_typical_ability_scores(data: Dict[str, Any]) -> Optional[str]:
    ability_scores = data.get("ability_scores", {})
    if not isinstance(ability_scores, dict):
        return None
    unusual: List[str] = []
    for stat, val in ability_scores.items():
        if isinstance(val, int) and not 3 <= val <= 20:
            unusual.append(f"{stat}={val}")
    return ", ".join(unusual) if unusual else None


def _check_level_range(data: Dict[str, Any]) -> Optional[str]:
    level = data.get("level")
    if isinstance(level, int) and not 1 <= level <= 20:
        return f"level={level}"
    return None


def _check_valid_class(data: Dict[str, Any]) -> Optional[str]:
    dnd_class = _get_class_lower(data)
    valid_classes = (
        FULL_CASTERS | HALF_CASTERS | WARLOCKS | NON_CASTERS
        | {"artificer", "blood hunter"}
    )
    if dnd_class and dnd_class not in valid_classes:
        return f"dnd_class='{data.get('dnd_class')}'"
    return None


def _check_spell_level_vs_character(data: Dict[str, Any]) -> Optional[str]:
    """Ensure no known spell slot level exceeds what the class/level allows."""
    level = data.get("level")
    dnd_class = _get_class_lower(data)
    spell_slots = data.get("spell_slots", {})

    if not isinstance(level, int) or not isinstance(spell_slots, dict):
        return None
    if dnd_class in FULL_CASTERS:
        allowed = _FULL_CASTER_SLOTS.get(level, {})
    elif dnd_class in HALF_CASTERS:
        allowed = _HALF_CASTER_SLOTS.get(level, {})
    elif dnd_class in WARLOCKS:
        slot_level, _ = _WARLOCK_SLOTS.get(level, (1, 0))
        allowed = {str(i): 1 for i in range(1, slot_level + 1)}
    else:
        return None

    max_allowed_level = max((int(k) for k in allowed if allowed[k] > 0), default=0)
    bad: List[str] = []
    for slot_lvl_str in spell_slots:
        try:
            slot_lvl = int(slot_lvl_str)
        except ValueError:
            continue
        if slot_lvl > max_allowed_level:
            bad.append(f"level-{slot_lvl} slot")
    return ", ".join(bad) if bad else None


# -- Best practices --

def _check_backstory_length(data: Dict[str, Any]) -> Optional[str]:
    text = _get_background(data)
    if text and len(text) < 100:
        return f"backstory length={len(text)} chars (recommended: 100+)"
    return None


def _check_personality_depth(data: Dict[str, Any]) -> Optional[str]:
    traits = data.get("personality_traits", [])
    if isinstance(traits, list) and 0 < len(traits) < 4:
        return f"personality_traits count={len(traits)} (recommended: 4+)"
    return None


def _check_relationship_descriptions(data: Dict[str, Any]) -> Optional[str]:
    rels = data.get("relationships", {})
    if not isinstance(rels, dict) or not rels:
        return None
    missing = [name for name, desc in rels.items() if not desc]
    if missing:
        return f"relationships without descriptions: {', '.join(missing)}"
    return None


def _check_primary_ability(data: Dict[str, Any]) -> Optional[str]:
    """Suggest that the class primary ability should be among the highest scores."""
    dnd_class = _get_class_lower(data)
    ability_scores = data.get("ability_scores", {})
    if not isinstance(ability_scores, dict) or dnd_class not in CLASS_PRIMARY_ABILITIES:
        return None
    primary = CLASS_PRIMARY_ABILITIES[dnd_class]
    primary_score = ability_scores.get(primary)
    if not isinstance(primary_score, int):
        return None
    max_score = max((v for v in ability_scores.values() if isinstance(v, int)), default=0)
    if primary_score < max_score - 4:
        return (
            f"Primary ability for {dnd_class} is {primary} "
            f"(score {primary_score}), but highest score is {max_score}"
        )
    return None


# ---------------------------------------------------------------------------
# Auto-fix functions
# ---------------------------------------------------------------------------

def _auto_fix_proficiency_bonus(data: Dict[str, Any]) -> bool:
    """Correct proficiency bonus based on level."""
    level = data.get("level")
    if not isinstance(level, int):
        return False
    correct = get_proficiency_bonus(level)
    if data.get("proficiency_bonus") != correct:
        data["proficiency_bonus"] = correct
        return True
    return False


def _auto_fix_skill_modifiers(data: Dict[str, Any]) -> bool:
    """Recalculate skill modifiers from ability scores.

    Heuristic: if the current modifier exceeds ability_mod + proficiency, it is
    assumed to be an expertise value and is left at ability_mod + 2*proficiency.
    Otherwise, if it exceeds ability_mod, it is treated as proficient.
    """
    skills = data.get("skills", {})
    ability_scores = data.get("ability_scores", {})
    proficiency = data.get("proficiency_bonus", 2)

    if not isinstance(skills, dict) or not isinstance(ability_scores, dict):
        return False

    fixed = False
    for skill, modifier in list(skills.items()):
        ability = SKILL_ABILITIES.get(skill)
        if ability is None or ability not in ability_scores:
            continue
        ability_mod = calculate_modifier(ability_scores[ability])
        proficient_val = ability_mod + proficiency
        expertise_val = ability_mod + 2 * proficiency
        valid_values = {ability_mod, proficient_val, expertise_val}
        if not isinstance(modifier, int) or modifier in valid_values:
            continue
        # Pick best approximation
        if modifier > proficient_val:
            expected = expertise_val
        elif modifier > ability_mod:
            expected = proficient_val
        else:
            expected = ability_mod
        skills[skill] = expected
        fixed = True
    return fixed


# ---------------------------------------------------------------------------
# Rule definitions
# ---------------------------------------------------------------------------

def build_rules() -> List[VerificationRule]:
    """Build and return all verification rules.

    Returns:
        List of VerificationRule instances in evaluation order.
    """
    return [
        # ---- Completeness ----
        VerificationRule(
            rule_id="COMP001",
            category="completeness",
            severity="warning",
            message="Missing backstory",
            check_func=_check_backstory,
            suggestion="Add a backstory to improve roleplay and AI consultations",
        ),
        VerificationRule(
            rule_id="COMP002",
            category="completeness",
            severity="warning",
            message="Fewer than 2 personality traits defined",
            check_func=_check_personality_traits,
            suggestion="Add at least 2 personality traits",
        ),
        VerificationRule(
            rule_id="COMP003",
            category="completeness",
            severity="warning",
            message="Subclass missing for level 3+ character",
            check_func=_check_subclass,
            suggestion="Add a subclass (characters choose subclass at level 3 or earlier)",
        ),
        VerificationRule(
            rule_id="COMP004",
            category="completeness",
            severity="warning",
            message="Missing background field",
            check_func=_check_background_field,
            suggestion="Add a PHB background (e.g. Noble, Soldier, Sage)",
        ),
        VerificationRule(
            rule_id="COMP005",
            category="completeness",
            severity="suggestion",
            message="No ideals defined",
            check_func=_check_ideals,
            suggestion="Add at least 1 ideal to enrich the character",
        ),
        VerificationRule(
            rule_id="COMP006",
            category="completeness",
            severity="suggestion",
            message="No bonds defined",
            check_func=_check_bonds,
            suggestion="Add at least 1 bond for story hooks",
        ),
        VerificationRule(
            rule_id="COMP007",
            category="completeness",
            severity="suggestion",
            message="No flaws defined",
            check_func=_check_flaws,
            suggestion="Add at least 1 flaw for roleplay depth",
        ),
        VerificationRule(
            rule_id="COMP008",
            category="completeness",
            severity="suggestion",
            message="No feats defined",
            check_func=_check_feats,
            suggestion="Add feats earned at levels 4, 8, 12 etc.",
        ),
        VerificationRule(
            rule_id="COMP009",
            category="completeness",
            severity="suggestion",
            message="No relationships defined",
            check_func=_check_relationships,
            suggestion="Add relationships to enable relationship-aware AI responses",
        ),
        VerificationRule(
            rule_id="COMP010",
            category="completeness",
            severity="suggestion",
            message="No ai_config defined",
            check_func=_check_ai_config,
            suggestion="Add an ai_config block to enable AI consultations",
        ),
        # ---- Consistency ----
        VerificationRule(
            rule_id="CONS001",
            category="consistency",
            severity="error",
            message="Proficiency bonus does not match level",
            check_func=_check_proficiency_bonus,
            suggestion="Use the proficiency bonus table: +2 lvl1-4, +3 lvl5-8, +4 lvl9-12, ...",
            auto_fix_func=_auto_fix_proficiency_bonus,
        ),
        VerificationRule(
            rule_id="CONS002",
            category="consistency",
            severity="error",
            message="Skill modifier(s) inconsistent with ability scores",
            check_func=_check_skill_modifiers,
            suggestion="Recalculate: ability modifier + (proficiency bonus if proficient)",
            auto_fix_func=_auto_fix_skill_modifiers,
        ),
        VerificationRule(
            rule_id="CONS003",
            category="consistency",
            severity="warning",
            message="Max HP appears outside expected range for class/level/CON",
            check_func=_check_hp_consistency,
            suggestion=(
                "Expected HP = max hit die at lvl 1 + avg die per level + CON modifier per level"
            ),
        ),
        VerificationRule(
            rule_id="CONS005",
            category="consistency",
            severity="warning",
            message="Spell slot counts exceed class/level maximum",
            check_func=_check_spell_slots,
            suggestion="Refer to the spell slot table in the PHB for your class and level",
        ),
        # ---- Rules compliance ----
        VerificationRule(
            rule_id="RULE001",
            category="rules",
            severity="error",
            message="Ability score(s) outside valid D&D range (1-30)",
            check_func=_check_ability_scores_range,
            suggestion="All ability scores must be between 1 and 30",
        ),
        VerificationRule(
            rule_id="RULE002",
            category="rules",
            severity="error",
            message="Character level outside valid range (1-20)",
            check_func=_check_level_range,
            suggestion="Level must be between 1 and 20",
        ),
        VerificationRule(
            rule_id="RULE003",
            category="rules",
            severity="error",
            message="Unknown D&D class",
            check_func=_check_valid_class,
            suggestion=(
                "Use a standard class: barbarian, bard, cleric, druid, fighter, "
                "monk, paladin, ranger, rogue, sorcerer, warlock, wizard"
            ),
        ),
        VerificationRule(
            rule_id="RULE004",
            category="rules",
            severity="warning",
            message="Ability score(s) outside typical PC range (3-20)",
            check_func=_check_typical_ability_scores,
            suggestion=(
                "Typical ability scores are between 3 and 20; "
                "values outside this range may be intentional for special characters"
            ),
        ),
        VerificationRule(
            rule_id="RULE005",
            category="rules",
            severity="error",
            message="Spell slot level exceeds maximum for class/level",
            check_func=_check_spell_level_vs_character,
            suggestion="Remove or downgrade spell slots that exceed your class/level maximum",
        ),
        # ---- Best practices ----
        VerificationRule(
            rule_id="BEST001",
            category="best_practices",
            severity="suggestion",
            message="Backstory is short",
            check_func=_check_backstory_length,
            suggestion="A longer backstory (100+ chars) gives better AI consultation results",
        ),
        VerificationRule(
            rule_id="BEST002",
            category="best_practices",
            severity="suggestion",
            message="Few personality traits",
            check_func=_check_personality_depth,
            suggestion="4+ personality traits give richer roleplay opportunities",
        ),
        VerificationRule(
            rule_id="BEST003",
            category="best_practices",
            severity="suggestion",
            message="Some relationships have no description",
            check_func=_check_relationship_descriptions,
            suggestion="Add a short description to every relationship entry",
        ),
        VerificationRule(
            rule_id="BEST005",
            category="best_practices",
            severity="suggestion",
            message="Primary class ability may not be the highest",
            check_func=_check_primary_ability,
            suggestion="Consider distributing ability scores so the class primary ability is high",
        ),
    ]
