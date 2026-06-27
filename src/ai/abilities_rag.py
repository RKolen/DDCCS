"""Resolve D&D abilities and features from the 2024 ruleset.

Given a source (class, species, subspecies, ...) and a character level, this
fetches the relevant page from the rules wiki configured via
``RAG_RULES_BASE_URL`` and extracts the abilities granted up to that level,
with their rules text.

Two page layouts are supported:
  * Class pages use ``Level N: Feature`` headings followed by description text.
  * Species/subspecies pages list traits as bold-lead paragraphs
    (``<strong>Resourceful.</strong> ...``); higher-level lineage traits using
    ``Level N:`` headings are also captured.

The resolver degrades gracefully to an empty list whenever RAG is disabled,
scraping dependencies are missing, or a page cannot be fetched or parsed. It is
intentionally generic so other features can resolve rules content the same way.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, TypedDict, cast

from src.ai.rag_system import RAGSystem, get_rag_system

try:
    from bs4 import BeautifulSoup
    from bs4.element import Tag
    _SCRAPING_AVAILABLE = True
except ImportError:
    _SCRAPING_AVAILABLE = False

logger = logging.getLogger(__name__)

# Heading form used for leveled features, e.g. "Level 1: Second Wind".
_LEVEL_HEADING = re.compile(r"^Level\s+(\d+):\s*(.+)$", re.IGNORECASE)

# Source categories that use the species-style trait layout.
_TRAIT_SOURCES = frozenset({"species", "subspecies"})

# Cache key suffix so ability parses do not collide with WikiClient section
# caches stored under the same page URL.
_CACHE_SUFFIX = "#abilities"

# Cap a single feature description to keep payloads and storage reasonable.
_MAX_DESCRIPTION = 2000


class Ability(TypedDict):
    """A resolved ability/feature granted by a source at a given level."""

    name: str
    description: str
    level: int
    source_type: str


class BackgroundData(TypedDict):
    """Structured data a 2024 background grants."""

    ability_options: List[str]
    feat: str
    feat_description: str
    skills: List[str]
    tools: List[str]
    gold: int
    equipment: List[str]


# Labels that segment the single background data paragraph on the rules wiki.
_BG_LABELS = ("Ability Scores", "Feat", "Skill Proficiencies", "Tool Proficiency", "Equipment")

# Labels that follow "Tool Proficiencies" in a class page's proficiency block.
_CLASS_PROF_NEXT = (
    "Weapon Proficiencies", "Weapon Proficiency", "Armor Training",
    "Saving Throw", "Starting Equipment",
)

# Standard musical instruments (matching the tool_profiencies vocabulary), used
# to scope a "Choose N Musical Instruments" class tool proficiency.
MUSICAL_INSTRUMENTS = ["Bagpipes", "Concertina", "Horn", "Lute", "Lyre", "Pan Flute", "Viol"]

_WORD_TO_INT = {"one": 1, "two": 2, "three": 3}


def get_abilities(
    source_type: str,
    source_name: str,
    level: int,
    *,
    rag: Optional[RAGSystem] = None,
) -> List[Ability]:
    """Resolve abilities a source grants up to a character level.

    Args:
        source_type: Source category ("class", "species", "subspecies", ...).
        source_name: Source name used to locate the wiki page (e.g. "Fighter").
        level: Highest character level to include (features above are dropped).
        rag: Optional RAG system to use; when omitted a shared instance is
            resolved. Pass an explicit instance to control or bypass RAG, which
            aids testing.

    Returns:
        Ordered, de-duplicated abilities at or below the requested level. Empty
        when RAG is unavailable or the page cannot be resolved.
    """
    rag_system = rag if rag is not None else _safe_rag_system()
    if rag_system is None or not getattr(rag_system, "enabled", False):
        return []

    all_abilities = _resolve_page(rag_system, source_type, source_name)
    return [ability for ability in all_abilities if ability["level"] <= level]


def get_background(name: str, *, rag: Optional[RAGSystem] = None) -> Optional[BackgroundData]:
    """Resolve a 2024 background's granted data from the rules wiki.

    Args:
        name: Background name (e.g. "Charlatan").
        rag: Optional RAG system to use; resolved from config when omitted.

    Returns:
        Structured background data, or None when RAG is unavailable or the
        page cannot be fetched/parsed.
    """
    rag_system = rag if rag is not None else _safe_rag_system()
    if rag_system is None or not getattr(rag_system, "enabled", False):
        return None
    client = getattr(rag_system, "rules_client", None)
    if client is None or not _SCRAPING_AVAILABLE or getattr(client, "session", None) is None:
        return None

    slug = "background:" + name.strip().lower().replace(" ", "-")
    if slug == "background:":
        return None
    html = _fetch_html(client, f"{client.base_url}/{slug}")
    if html is None:
        return None
    data = _parse_background(html)
    if data is not None and data["feat"]:
        data["feat_description"] = get_feat(data["feat"], rag=rag_system) or ""
    return data


def get_feat(name: str, *, rag: Optional[RAGSystem] = None) -> Optional[str]:
    """Resolve a feat's rules description from the rules wiki.

    Args:
        name: Feat name (e.g. "Skilled" or "Magic Initiate (Cleric)").
        rag: Optional RAG system; resolved from config when omitted.

    Returns:
        The feat's description text, or None when it cannot be resolved.
    """
    rag_system = rag if rag is not None else _safe_rag_system()
    if rag_system is None or not getattr(rag_system, "enabled", False):
        return None
    client = getattr(rag_system, "rules_client", None)
    if client is None or not _SCRAPING_AVAILABLE or getattr(client, "session", None) is None:
        return None

    # Feat pages key on the base feat name (drop any parenthetical specialisation).
    base = re.sub(r"\s*\(.*?\)\s*", "", name).strip().lower().replace(" ", "-")
    if base == "":
        return None
    html = _fetch_html(client, f"{client.base_url}/feat:{base}")
    if html is None:
        return None
    return _parse_feat_description(html)


def _safe_rag_system() -> Optional[RAGSystem]:
    """Resolve the shared RAG system, returning None when unavailable.

    Returns:
        A RAG system instance when one can be built, otherwise None.
    """
    try:
        return get_rag_system()
    except (ImportError, OSError, ValueError) as exc:
        logger.debug("RAG system unavailable for abilities: %s", exc)
        return None


def _resolve_page(rag: RAGSystem, source_type: str, source_name: str) -> List[Ability]:
    """Fetch and parse all abilities for a source page, with caching.

    Args:
        rag: RAG system providing the rules wiki client.
        source_type: Source category.
        source_name: Source name to locate the page.

    Returns:
        All abilities parsed from the page (unfiltered by level).
    """
    client = getattr(rag, "rules_client", None)
    if client is None or not _SCRAPING_AVAILABLE or getattr(client, "session", None) is None:
        return []

    slug = source_name.strip().lower().replace(" ", "-")
    if slug == "":
        return []
    url = f"{client.base_url}/{slug}"

    cached = client.cache.get(url + _CACHE_SUFFIX)
    if cached is not None and isinstance(cached.get("abilities"), list):
        return [_coerce_ability(item) for item in cached["abilities"] if isinstance(item, dict)]

    html = _fetch_html(client, url)
    if html is None:
        return []

    abilities = _parse_abilities(html, source_type)
    client.cache.set(url + _CACHE_SUFFIX, {"abilities": [dict(a) for a in abilities]})
    return abilities


def _fetch_html(client: object, url: str) -> Optional[str]:
    """Fetch the page-content HTML for a URL, returning None on any failure.

    Args:
        client: The rules WikiClient (provides a requests session).
        url: Absolute page URL.

    Returns:
        The raw HTML body, or None when the request fails.
    """
    session = getattr(client, "session", None)
    if session is None:
        return None
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
    except OSError as exc:
        logger.debug("Ability page fetch failed for %s: %s", url, exc)
        return None
    return str(response.text)


def _parse_abilities(html: str, source_type: str) -> List[Ability]:
    """Parse abilities from page HTML for the given source type.

    Args:
        html: Raw page HTML.
        source_type: Source category determining the layout to expect.

    Returns:
        De-duplicated abilities parsed from the page.
    """
    if not _SCRAPING_AVAILABLE:
        return []
    found = BeautifulSoup(html, "html.parser").find("div", id="page-content")
    if not isinstance(found, Tag):
        return []
    content = cast("Tag", found)

    leveled = _parse_level_headings(content, source_type)
    if source_type not in _TRAIT_SOURCES:
        return _dedupe(leveled)
    return _dedupe(_parse_bold_traits(content, source_type) + leveled)


def _parse_level_headings(content: "Tag", source_type: str) -> List[Ability]:
    """Parse "Level N: Feature" headings into abilities.

    Args:
        content: The page-content BeautifulSoup element.
        source_type: Source category to stamp on each ability.

    Returns:
        Abilities derived from leveled headings.
    """
    abilities: List[Ability] = []
    for heading in content.find_all(["h1", "h2", "h3", "h4"]):
        match = _LEVEL_HEADING.match(heading.get_text(strip=True))
        if match is None:
            continue
        abilities.append(
            Ability(
                name=match.group(2).strip(),
                description=_collect_description(heading),
                level=int(match.group(1)),
                source_type=source_type,
            )
        )
    return abilities


def _parse_bold_traits(content: "Tag", source_type: str) -> List[Ability]:
    """Parse bold-lead trait paragraphs (e.g. species traits) into abilities.

    Args:
        content: The page-content BeautifulSoup element.
        source_type: Source category to stamp on each ability.

    Returns:
        Level-1 abilities derived from bold-lead paragraphs.
    """
    abilities: List[Ability] = []
    for paragraph in content.find_all("p"):
        lead = paragraph.find(["strong", "b"])
        if lead is None:
            continue
        lead_text = lead.get_text(strip=True)
        # A trailing period marks a trait name; stat lines end with a colon.
        if not lead_text.endswith("."):
            continue
        name = lead_text.rstrip(".").strip()
        if name == "":
            continue
        full = paragraph.get_text(" ", strip=True)
        description = full[len(lead_text):].strip() if full.startswith(lead_text) else full
        abilities.append(
            Ability(
                name=name,
                description=_clean(description),
                level=1,
                source_type=source_type,
            )
        )
    return abilities


def _collect_description(heading: "Tag") -> str:
    """Collect description text following a heading until the next heading.

    Args:
        heading: A heading BeautifulSoup element.

    Returns:
        Cleaned, joined description text capped at a sensible length.
    """
    parts: List[str] = []
    for sibling in heading.find_next_siblings():
        if sibling.name in ("h1", "h2", "h3", "h4"):
            break
        if sibling.name in ("p", "ul"):
            text = _clean(sibling.get_text(" ", strip=True))
            if text:
                parts.append(text)
    return "\n\n".join(parts)[:_MAX_DESCRIPTION]


def _clean(text: str) -> str:
    """Strip citation/edit markers and collapse whitespace.

    Args:
        text: Raw text.

    Returns:
        Cleaned text.
    """
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"\[edit\]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _coerce_ability(item: dict) -> Ability:
    """Coerce a cached dict into an Ability with safe defaults.

    Args:
        item: Cached ability dict.

    Returns:
        A well-formed Ability.
    """
    return Ability(
        name=str(item.get("name", "")),
        description=str(item.get("description", "")),
        level=int(item.get("level", 1)),
        source_type=str(item.get("source_type", "")),
    )


def _dedupe(abilities: List[Ability]) -> List[Ability]:
    """Drop abilities with duplicate names, keeping first-seen order.

    Args:
        abilities: Abilities to de-duplicate.

    Returns:
        De-duplicated abilities.
    """
    seen = set()
    unique: List[Ability] = []
    for ability in abilities:
        key = ability["name"].lower()
        if key in seen or key == "":
            continue
        seen.add(key)
        unique.append(ability)
    return unique


def _parse_background(html: str) -> Optional[BackgroundData]:
    """Parse the labeled background data paragraph from page HTML.

    Args:
        html: Raw background page HTML.

    Returns:
        Structured background data, or None when the data paragraph is absent.
    """
    if not _SCRAPING_AVAILABLE:
        return None
    found = BeautifulSoup(html, "html.parser").find("div", id="page-content")
    if not isinstance(found, Tag):
        return None
    content = cast("Tag", found)

    data_text = ""
    for paragraph in content.find_all("p"):
        text = paragraph.get_text(" ", strip=True)
        if "Ability Scores" in text and "Skill Proficiencies" in text:
            data_text = _clean(text)
            break
    if data_text == "":
        return None

    segments = _split_labeled(data_text, _BG_LABELS)
    equipment_text = segments.get("Equipment", "")
    return BackgroundData(
        ability_options=_split_names(segments.get("Ability Scores", "")),
        feat=segments.get("Feat", "").strip(),
        feat_description="",
        skills=_split_names(segments.get("Skill Proficiencies", "")),
        tools=_split_names(segments.get("Tool Proficiency", "")),
        gold=_parse_gold(equipment_text),
        equipment=_parse_equipment(equipment_text),
    )


def get_class_tools(class_name: str, *, rag: Optional[RAGSystem] = None) -> Dict[str, Any]:
    """Resolve a class's tool proficiencies from the rules wiki.

    Args:
        class_name: Class name (e.g. "Bard").
        rag: Optional RAG system; resolved from config when omitted.

    Returns:
        A dict ``{"granted": [tool names], "choice": {...} | None}``. ``granted``
        holds fixed tool grants (e.g. Rogue's Thieves' Tools); ``choice`` is a
        choice group (e.g. Bard's three Musical Instruments) or None.
    """
    result: Dict[str, Any] = {"granted": [], "choice": None}
    rag_system = rag if rag is not None else _safe_rag_system()
    if rag_system is None or not getattr(rag_system, "enabled", False):
        return result
    client = getattr(rag_system, "rules_client", None)
    if client is None or not _SCRAPING_AVAILABLE or getattr(client, "session", None) is None:
        return result

    slug = class_name.strip().lower().replace(" ", "-")
    if slug == "":
        return result
    html = _fetch_html(client, f"{client.base_url}/{slug}")
    if html is None:
        return result

    segment = _class_tool_segment(html)
    if segment == "" or segment.lower() == "none":
        return result

    match = re.match(r"choose\s+(\d+|one|two|three)\s+(.+)", segment, re.IGNORECASE)
    if match is not None:
        raw_count = match.group(1).lower()
        count = int(raw_count) if raw_count.isdigit() else _WORD_TO_INT.get(raw_count, 1)
        category = match.group(2).strip()
        options = MUSICAL_INSTRUMENTS if "musical instrument" in category.lower() else []
        result["choice"] = {
            "id": "class-tools", "label": f"Tool: {category}",
            "count": count, "from": options, "kind": "tool",
        }
    else:
        result["granted"] = _split_names(segment)
    return result


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
    for slug, item_type in _EQUIPMENT_PAGES.items():
        html = _fetch_html(client, f"{getattr(client, 'base_url', '')}/equipment:{slug}")
        if html is not None:
            _parse_equipment_page(html, item_type, catalog)
    if cache is not None:
        cache.set(cache_key, {"items": {key: dict(value) for key, value in catalog.items()}})
    return catalog


def _parse_equipment_page(
    html: str, item_type: str, catalog: Dict[str, EquipmentInfo]
) -> None:
    """Parse one equipment page's tables into the catalogue, in place.

    Args:
        html: Raw equipment page HTML.
        item_type: The item type all rows on this page receive.
        catalog: Catalogue to populate (mutated in place).
    """
    if not _SCRAPING_AVAILABLE:
        return
    found = BeautifulSoup(html, "html.parser").find("div", id="page-content")
    if not isinstance(found, Tag):
        return
    content = cast("Tag", found)
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


def _class_tool_segment(html: str) -> str:
    """Extract the "Tool Proficiencies" value from a class page.

    Args:
        html: Raw class page HTML.

    Returns:
        The text following "Tool Proficiencies" up to the next proficiency
        label, or the empty string when absent.
    """
    if not _SCRAPING_AVAILABLE:
        return ""
    found = BeautifulSoup(html, "html.parser").find("div", id="page-content")
    if not isinstance(found, Tag):
        return ""
    text = _clean(cast("Tag", found).get_text(" ", strip=True))
    index = text.find("Tool Proficiencies")
    if index == -1:
        return ""
    segment = text[index + len("Tool Proficiencies"):]
    for label in _CLASS_PROF_NEXT:
        cut = segment.find(label)
        if cut != -1:
            segment = segment[:cut]
    return segment.strip()


def _parse_feat_description(html: str) -> Optional[str]:
    """Parse a feat page's description, skipping metadata lines.

    Args:
        html: Raw feat page HTML.

    Returns:
        The joined description paragraphs, or None when none are found.
    """
    if not _SCRAPING_AVAILABLE:
        return None
    found = BeautifulSoup(html, "html.parser").find("div", id="page-content")
    if not isinstance(found, Tag):
        return None
    content = cast("Tag", found)

    parts: List[str] = []
    for paragraph in content.find_all("p"):
        text = _clean(paragraph.get_text(" ", strip=True))
        lower = text.lower()
        if text == "" or lower.startswith(("source:", "prerequisite:", "repeatable")):
            continue
        parts.append(text)
        if len(" ".join(parts)) >= _MAX_DESCRIPTION:
            break
    joined = " ".join(parts)[:_MAX_DESCRIPTION]
    return joined if joined != "" else None


def _split_labeled(text: str, labels: tuple) -> dict:
    """Split a string into a label->value map by known inline labels.

    Args:
        text: The full labeled string.
        labels: Label names (without the trailing colon).

    Returns:
        Mapping of label to the text following it up to the next label.
    """
    positions = []
    for label in labels:
        index = text.find(label + ":")
        if index != -1:
            positions.append((index, label))
    positions.sort()

    out: dict = {}
    for ordinal, (start, label) in enumerate(positions):
        value_start = start + len(label) + 1
        value_end = positions[ordinal + 1][0] if ordinal + 1 < len(positions) else len(text)
        out[label] = text[value_start:value_end].strip()
    return out


def _split_names(value: str) -> List[str]:
    """Split a comma/and-separated list of names into a clean list.

    Args:
        value: e.g. "Dexterity, Constitution, Charisma" or "Deception and Sleight of Hand".

    Returns:
        Ordered list of trimmed names.
    """
    return [part.strip() for part in value.replace(" and ", ",").split(",") if part.strip()]


def _parse_gold(equipment_text: str) -> int:
    """Extract the gold alternative (option B) from an equipment string.

    Args:
        equipment_text: e.g. "Choose A or B: (A) ..., 15 GP; or (B) 50 GP".

    Returns:
        The gold amount, or 0 when none is found.
    """
    option_b = re.search(r"\(B\)\s*([\d,]+)\s*GP", equipment_text)
    if option_b is not None:
        return int(option_b.group(1).replace(",", ""))
    amounts = re.findall(r"([\d,]+)\s*GP", equipment_text)
    return int(amounts[-1].replace(",", "")) if amounts else 0


def _parse_equipment(equipment_text: str) -> List[str]:
    """Extract the equipment package (option A items) from an equipment string.

    Args:
        equipment_text: e.g. "Choose A or B: (A) Forgery Kit, Costume, 15 GP; or (B) 50 GP".

    Returns:
        Item names from option A, excluding any gold entries.
    """
    package = re.search(r"\(A\)\s*(.*?)(?:;|\bor\b\s*\(B\))", equipment_text)
    part = package.group(1) if package is not None else ""
    items = [item.strip() for item in part.split(",")]
    return [item for item in items if item and not re.search(r"\d+\s*GP", item)]
