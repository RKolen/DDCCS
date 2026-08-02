"""Resolve equipment and tool item data from the 2024 ruleset.

Scrapes the rules-wiki equipment and tool pages into a catalogue of item
descriptions and types, and exposes the tool-proficiency categories. Used to
enrich item nodes (and the proficiency sublists) during character creation.

Shared scraping primitives come from :mod:`src.ai.wiki_scraping`.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, TypedDict

from src.ai.abilities_rag import (
    _CACHE_SUFFIX,
    _MAX_DESCRIPTION,
    _clean,
    _safe_rag_system,
)
from src.ai.wiki_scraping import (
    SCRAPING_AVAILABLE as _SCRAPING_AVAILABLE,
    fetch_html as _fetch_html,
    page_content,
)
from src.ai.rag_system import RAGSystem


class EquipmentInfo(TypedDict):
    """Resolved catalogue data for a piece of equipment."""

    description: str
    item_type: str


# Equipment category pages on the rules wiki and the item type each grants.
# Only the gear-style pages carry a prose description column; the weapon and
# armor pages are stat tables, but still let us type their items authoritatively.
_EQUIPMENT_PAGES: Dict[str, str] = {
    "adventuring-gear": "item",
    "tool": "item",
    "trinket": "item",
    "crafting": "item",
    "poison": "item",
    "mounts-and-vehicles": "item",
    "weapon": "weapon",
    "armor": "armor",
}

# Header cell labels that mark a table's prose description column.
_DESC_HEADERS = ("function", "description", "effect")

# Cell labels identifying a table header row (rather than a data row).
_HEADER_LABELS = frozenset({
    "item", "name", "armor", "tool", "artisan tool", "other tool", "gaming set",
    "mount", "vehicle", "weight", "cost", "damage", "properties", "mastery",
    "ability", "function", "description", "effect", "strength", "stealth",
    "speed", "armor class (ac)", "carrying capacity",
})


def get_equipment_descriptions(
    names: List[str], *, rag: Optional[RAGSystem] = None
) -> Dict[str, EquipmentInfo]:
    """Resolve equipment descriptions and types from the rules wiki.

    Scrapes the 2024 equipment category pages and returns, for each requested
    name that matches a catalogued item, its prose description (where the page
    provides one, e.g. gear) and item type (weapon/armor/item) inferred from the
    page it appears on. Wiki names in "Group, Modifier" form (e.g. "Clothes,
    Fine") also match their natural form ("Fine Clothes").

    Args:
        names: Item names to resolve (display form, e.g. "Fine Clothes").
        rag: Optional RAG system; resolved from config when omitted.

    Returns:
        A map of each requested name to its resolved info. Unmatched names are
        omitted. Empty when RAG is unavailable or no page can be fetched.
    """
    wanted = [name.strip() for name in names if name and name.strip()]
    if wanted == []:
        return {}
    rag_system = rag if rag is not None else _safe_rag_system()
    if rag_system is None or not getattr(rag_system, "enabled", False):
        return {}
    client = getattr(rag_system, "rules_client", None)
    if client is None or not _SCRAPING_AVAILABLE or getattr(client, "session", None) is None:
        return {}

    catalog = _equipment_catalog(client)
    result: Dict[str, EquipmentInfo] = {}
    for name in wanted:
        info = catalog.get(_equip_key(name))
        if info is not None:
            result[name] = info
    return result


_TOOL_CATEGORY_HEADERS = {
    "artisan tool": "artisan",
    "other tool": "other",
    "gaming set": "gaming_set",
    "musical instrument": "musical_instrument",
}


def get_tool_categories(*, rag: Optional[RAGSystem] = None) -> Dict[str, List[str]]:
    """Resolve the rules-wiki tool categories and their member tools.

    Args:
        rag: Optional RAG system; resolved from config when omitted.

    Returns:
        A map of category key (``artisan``/``other``/``gaming_set``/
        ``musical_instrument``) to the tool names it contains. Empty when RAG is
        unavailable or the page cannot be fetched.
    """
    rag_system = rag if rag is not None else _safe_rag_system()
    if rag_system is None or not getattr(rag_system, "enabled", False):
        return {}
    client = getattr(rag_system, "rules_client", None)
    if client is None or not _SCRAPING_AVAILABLE or getattr(client, "session", None) is None:
        return {}
    html = _fetch_html(client, f"{getattr(client, 'base_url', '')}/equipment:tool")
    if html is None:
        return {}
    return _parse_tool_categories(html)


def _parse_tool_categories(html: str) -> Dict[str, List[str]]:
    """Parse the tool page's category tables into a category->names map.

    Args:
        html: Raw tool page HTML.

    Returns:
        Category key to member tool names.
    """
    content = page_content(html)
    if content is None:
        return {}
    result: Dict[str, List[str]] = {}
    for table in content.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        header = _clean(rows[0].get_text(" ", strip=True)).lower()
        category = next(
            (cat for label, cat in _TOOL_CATEGORY_HEADERS.items() if label in header), None
        )
        if category is None:
            continue
        names = []
        for row in rows[1:]:
            cell = row.find(["td", "th"])
            if cell is not None:
                name = _clean(cell.get_text(" ", strip=True))
                if name != "":
                    names.append(name)
        if names:
            result[category] = names
    return result


def _equip_key(name: str) -> str:
    """Normalise an item name into a catalogue lookup key.

    Args:
        name: Item name in any case/spacing.

    Returns:
        A lowercase, whitespace-collapsed, apostrophe-normalised key.
    """
    text = name.strip().lower().replace("’", "'")
    return re.sub(r"\s+", " ", text)


def _equipment_catalog(client: object) -> Dict[str, EquipmentInfo]:
    """Build (or load from cache) the full equipment catalogue.

    Args:
        client: The rules WikiClient (provides the session, cache and base URL).

    Returns:
        A map from normalised item key to its resolved info.
    """
    cache_key = f"{getattr(client, 'base_url', '')}/equipment{_CACHE_SUFFIX}"
    cache = getattr(client, "cache", None)
    cached = cache.get(cache_key) if cache is not None else None
    if isinstance(cached, dict) and isinstance(cached.get("items"), dict):
        return {
            key: _coerce_equipment(value)
            for key, value in cached["items"].items()
            if isinstance(value, dict)
        }

    catalog: Dict[str, EquipmentInfo] = {}
    tool_html = None
    for slug, item_type in _EQUIPMENT_PAGES.items():
        html = _fetch_html(client, f"{getattr(client, 'base_url', '')}/equipment:{slug}")
        if html is not None:
            _parse_equipment_page(html, item_type, catalog)
            if slug == "tool":
                tool_html = html
    if tool_html is not None:
        for name, description in _parse_tool_descriptions(tool_html).items():
            info = EquipmentInfo(description=description, item_type="item")
            _register_equipment(catalog, name, info)
    if cache is not None:
        cache.set(cache_key, {"items": {key: dict(value) for key, value in catalog.items()}})
    return catalog


def _parse_tool_descriptions(html: str) -> Dict[str, str]:
    """Parse the tool page's per-tool detail tabs into name -> description.

    Artisan and "other" tools have an individual tab; gaming sets and musical
    instruments share one "<Category> (Varies)" tab, whose description applies to
    every member of that category.

    Args:
        html: Raw tool page HTML.

    Returns:
        A map of specific tool name to its description.
    """
    content = page_content(html)
    if content is None:
        return {}
    categories = _parse_tool_categories(html)
    result: Dict[str, str] = {}
    for navset in content.select("div.yui-navset"):
        labels = [a.get_text(strip=True) for a in navset.select("ul.yui-nav li a")]
        panels = navset.select("div.yui-content > div")
        for label, panel in zip(labels, panels):
            description = _clean(panel.get_text(" ", strip=True))[:_MAX_DESCRIPTION]
            if description == "":
                continue
            for name in _expand_tool_label(label, categories):
                result[name] = description
    return result


def _expand_tool_label(label: str, categories: Dict[str, List[str]]) -> List[str]:
    """Resolve a tool tab label to the specific tool names it describes.

    Args:
        label: The tab label (e.g. "Smith's Tools" or "Gaming Set (Varies)").
        categories: Category key to member names, for "(Varies)" labels.

    Returns:
        The specific tool names the label's description applies to.
    """
    lowered = label.lower()
    if "varies" in lowered:
        for phrase, key in _TOOL_CATEGORY_HEADERS.items():
            if phrase in lowered:
                return categories.get(key, [])
    return [label]


def _parse_equipment_page(
    html: str, item_type: str, catalog: Dict[str, EquipmentInfo]
) -> None:
    """Parse one equipment page's tables into the catalogue, in place.

    Args:
        html: Raw equipment page HTML.
        item_type: The item type all rows on this page receive.
        catalog: Catalogue to populate (mutated in place).
    """
    content = page_content(html)
    if content is None:
        return
    for table in content.find_all("table"):
        desc_index: Optional[int] = None
        for row in table.find_all("tr"):
            cells = [_clean(cell.get_text(" ", strip=True)) for cell in row.find_all(["td", "th"])]
            if len(cells) < 2:
                continue
            if any(cell.lower() in _HEADER_LABELS for cell in cells):
                desc_index = _description_column(cells)
                continue
            name = cells[0]
            if name == "":
                continue
            description = ""
            if desc_index is not None and desc_index < len(cells):
                description = cells[desc_index][:_MAX_DESCRIPTION]
            _register_equipment(catalog, name, EquipmentInfo(
                description=description, item_type=item_type,
            ))


def _description_column(header_cells: List[str]) -> Optional[int]:
    """Find the index of a table's prose description column.

    Args:
        header_cells: Cleaned header row cell texts.

    Returns:
        The column index of a description header, or None when absent.
    """
    for index, cell in enumerate(header_cells):
        if cell.lower() in _DESC_HEADERS:
            return index
    return None


def _register_equipment(
    catalog: Dict[str, EquipmentInfo], name: str, info: EquipmentInfo
) -> None:
    """Register an item under its own key and its inverted ("X, Y") key.

    Args:
        catalog: Catalogue to populate.
        name: Item name as printed on the wiki (may be "Group, Modifier").
        info: Resolved info to store.
    """
    keys = [_equip_key(name)]
    if "," in name:
        group, modifier = name.split(",", 1)
        keys.append(_equip_key(f"{modifier.strip()} {group.strip()}"))
    for key in keys:
        existing = catalog.get(key)
        if existing is None:
            catalog[key] = info
        elif existing["description"] == "" and info["description"] != "":
            catalog[key] = info


def _coerce_equipment(item: dict) -> EquipmentInfo:
    """Coerce a cached dict into an EquipmentInfo with safe defaults.

    Args:
        item: Cached equipment dict.

    Returns:
        A well-formed EquipmentInfo.
    """
    return EquipmentInfo(
        description=str(item.get("description", "")),
        item_type=str(item.get("item_type", "item")),
    )
