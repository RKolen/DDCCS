"""Resolve a class's build plan from the Drupal taxonomy, with a fallback.

The ``class`` taxonomy is the source of truth: each class term carries
``class_grant`` paragraphs describing, per level, the skills/tools/equipment it
grants or lets the player choose, the subclass choice, and its features. This
module reads those grants over GraphQL and shapes them into a plan the
character-creation wizard renders.

When a class term has no grants (or Drupal is unreachable), it falls back to the
JSON class template plus the rules-wiki tool resolver, so the wizard always has a
plan.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, TypedDict

from src.ai.abilities_rag import get_class_tools
from src.ai.rag_system import RAGSystem
from src.characters.character_template import load_template
from src.integration.drupal_graphql import query_drupal

logger = logging.getLogger(__name__)


class ClassPlan(TypedDict):
    """A class's resolved build plan, filtered to a character level."""

    granted_skills: List[str]
    granted_tools: List[str]
    skill_choices: List[Dict[str, Any]]
    tool_choices: List[Dict[str, Any]]
    equipment_choices: List[Dict[str, Any]]
    subclass: Optional[Dict[str, Any]]
    features: List[Dict[str, Any]]
    source: str


_CLASS_GRANTS_QUERY = """
{
  termClasses(first: 50) {
    nodes {
      name
      classGrants {
        ... on ParagraphClassGrant {
          level
          grantKind
          chooseCount
          text { value }
          skills { ... on TermSkill { name } }
          tools { ... on TermToolProfiency { name } }
          gold
          equipmentItems { ... on NodeItem { title itemType } }
        }
      }
    }
  }
}
"""

_SUBCLASS_QUERY = """
{
  termSubclasses(first: 100) {
    nodes { name class { ... on TermClass { name } } }
  }
}
"""


def get_class_plan(
    class_name: str, level: int, *, rag: Optional[RAGSystem] = None
) -> ClassPlan:
    """Resolve a class's build plan up to a character level.

    Args:
        class_name: The class name (e.g. "Bard").
        level: Highest character level to include (higher grants are dropped).
        rag: Optional RAG system used by the template fallback's tool lookup.

    Returns:
        A ClassPlan. ``source`` is "taxonomy" when grants were found, else
        "template".
    """
    grants = _fetch_grants(class_name)
    if grants:
        plan = _plan_from_grants(grants, level)
        plan["subclass"] = _merge_subclass_options(plan["subclass"], class_name)
        return plan
    return _plan_from_template(class_name, level, rag=rag)


def _fetch_grants(class_name: str) -> List[Dict[str, Any]]:
    """Fetch a class term's grant paragraphs from Drupal, or [] when absent."""
    data = query_drupal(_CLASS_GRANTS_QUERY)
    nodes = data.get("termClasses", {}).get("nodes", []) if data else []
    target = class_name.strip().lower()
    for node in nodes:
        if str(node.get("name", "")).strip().lower() == target:
            return [g for g in node.get("classGrants", []) if isinstance(g, dict)]
    return []


def _empty_plan(source: str) -> ClassPlan:
    """Return an empty plan stamped with its source."""
    return ClassPlan(
        granted_skills=[], granted_tools=[], skill_choices=[], tool_choices=[],
        equipment_choices=[], subclass=None, features=[], source=source,
    )


def _ref_names(refs: Any) -> List[str]:
    """Extract the ``name`` field from a list of term reference dicts."""
    if not isinstance(refs, list):
        return []
    return [str(r["name"]) for r in refs if isinstance(r, dict) and r.get("name")]


def _plan_from_grants(grants: List[Dict[str, Any]], level: int) -> ClassPlan:
    """Shape raw grant paragraphs into a ClassPlan, filtered by level."""
    plan = _empty_plan("taxonomy")
    for grant in grants:
        grant_level = int(grant.get("level") or 1)
        if grant_level > level:
            continue
        _apply_grant(grant, grant_level, plan)
    return plan


def _apply_grant(grant: Dict[str, Any], grant_level: int, plan: ClassPlan) -> None:
    """Fold one grant paragraph into the plan in place."""
    kind = grant.get("grantKind")
    if kind == "skill_choice":
        plan["skill_choices"].append({
            "id": "class", "label": "Class skills",
            "count": int(grant.get("chooseCount") or 1),
            "from": _ref_names(grant.get("skills")), "kind": "skill",
        })
    elif kind == "tool_choice":
        plan["tool_choices"].append({
            "id": "class-tools", "label": _text_value(grant) or "Tool proficiency",
            "count": int(grant.get("chooseCount") or 1),
            "from": _ref_names(grant.get("tools")), "kind": "tool",
        })
    elif kind == "fixed_skill":
        plan["granted_skills"].extend(_ref_names(grant.get("skills")))
    elif kind == "fixed_tool":
        plan["granted_tools"].extend(_ref_names(grant.get("tools")))
    elif kind == "equipment_choice":
        plan["equipment_choices"].append(_equipment_group(grant, grant_level))
    elif kind == "subclass_choice":
        plan["subclass"] = {"level": grant_level, "options": []}
    elif kind == "feature":
        name = _text_value(grant)
        if name:
            plan["features"].append({"level": grant_level, "name": name})


def _equipment_group(grant: Dict[str, Any], grant_level: int) -> Dict[str, Any]:
    """Build an equipment choice group (option A items, option B gold)."""
    items = [
        {"name": str(i["title"]), "item_type": str(i.get("itemType") or "item")}
        for i in grant.get("equipmentItems", []) or []
        if isinstance(i, dict) and i.get("title")
    ]
    return {
        "id": f"class-equipment-{grant_level}",
        "label": _text_value(grant) or "Starting equipment",
        "items": items, "gold": int(grant.get("gold") or 0),
    }


def _text_value(grant: Dict[str, Any]) -> str:
    """Read the first text field value from a grant, or empty string."""
    text = grant.get("text")
    if isinstance(text, list) and text and isinstance(text[0], dict):
        return str(text[0].get("value") or "")
    if isinstance(text, dict):
        return str(text.get("value") or "")
    return ""


def _merge_subclass_options(
    subclass: Optional[Dict[str, Any]], class_name: str
) -> Optional[Dict[str, Any]]:
    """Fill a subclass choice's options from the subclasses vocab."""
    if subclass is None:
        return None
    subclass["options"] = _subclass_options(class_name)
    return subclass


def _subclass_options(class_name: str) -> List[str]:
    """List subclass term names whose parent class matches the given class."""
    data = query_drupal(_SUBCLASS_QUERY)
    nodes = data.get("termSubclasses", {}).get("nodes", []) if data else []
    target = class_name.strip().lower()
    options = []
    for node in nodes:
        parent = node.get("class") or {}
        if str(parent.get("name", "")).strip().lower() == target:
            options.append(str(node.get("name", "")))
    return options


def _plan_from_template(
    class_name: str, level: int, *, rag: Optional[RAGSystem] = None
) -> ClassPlan:
    """Build a plan from the JSON class template + rules-wiki tools (fallback)."""
    template = load_template(class_name)
    if template is None:
        return _empty_plan("template")
    plan = _empty_plan("template")

    options = template.get("skill_options", {})
    if isinstance(options, dict) and options.get("from"):
        plan["skill_choices"].append({
            "id": "class", "label": f"{template.get('class', 'Class')} skills",
            "count": int(options.get("choose", 1)),
            "from": list(options["from"]), "kind": "skill",
        })

    tools = get_class_tools(class_name, rag=rag)
    if tools.get("choice"):
        plan["tool_choices"].append(tools["choice"])
    plan["granted_tools"].extend(tools.get("granted", []))

    plan["equipment_choices"].append(_template_equipment(template))

    subclass = template.get("subclass_options", {})
    if isinstance(subclass, dict) and subclass.get("level"):
        plan["subclass"] = {
            "level": int(subclass["level"]),
            "options": list(subclass.get("options", [])),
        }

    for feat_level, names in (template.get("class_features", {}) or {}).items():
        if int(feat_level) <= level:
            plan["features"].extend({"level": int(feat_level), "name": n} for n in names)
    return plan


def _template_equipment(template: Dict[str, Any]) -> Dict[str, Any]:
    """Build an equipment choice group from a template's starting_equipment."""
    equip = template.get("starting_equipment", {})
    names = (
        list(equip.get("weapons", []))
        + list(equip.get("armor", []))
        + list(equip.get("items", []))
    )
    return {
        "id": "class-equipment-1", "label": "Starting equipment",
        "items": [{"name": name, "item_type": "item"} for name in names],
        "gold": int(equip.get("gold", 0)),
    }
