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
from typing import Any, Dict, List, Optional, Tuple, TypedDict, cast

from src.ai.rag_system import RAGSystem, get_rag_system
from src.integration.drupal_graphql import query_drupal

from src.ai.wiki_scraping import (
    SCRAPING_AVAILABLE as _SCRAPING_AVAILABLE,
    fetch_first as _fetch_first,
    fetch_html as _fetch_html,
    page_content,
)

if _SCRAPING_AVAILABLE:
    from bs4.element import Tag

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
    tool_choices: List[Dict[str, Any]]
    gold: int
    equipment: List[str]


# Labels that segment the background data on the rules wiki. Individual pages
# slip between the singular and plural form of the ability and tool labels, so
# both spellings are recognised and merged after the split.
_BG_LABELS = (
    "Ability Scores", "Ability Score", "Feat", "Skill Proficiencies",
    "Tool Proficiencies", "Tool Proficiency", "Equipment",
)

# Stray space some pages leave before a label's colon ("Skill Proficiencies :").
_LOOSE_LABEL_COLON = re.compile(r"\s+:")

# Page-slug forms to try per source type, most canonical first. Only the Player's
# Handbook entries have a bare redirect page (``/human``); sourcebook entries
# exist solely under their category prefix (``/species:warforged``), and class
# pages live at ``<class>:main`` with only the core classes redirecting from the
# bare slug.
_SLUG_FORMS: Dict[str, Tuple[str, ...]] = {
    "species": ("species:{slug}", "{slug}"),
    "subspecies": ("species:{slug}", "{slug}"),
    "class": ("{slug}:main", "{slug}"),
    "background": ("background:{slug}",),
}

# Labels that follow "Tool Proficiencies" in a class page's proficiency block.
_CLASS_PROF_NEXT = (
    "Weapon Proficiencies", "Weapon Proficiency", "Armor Training",
    "Saving Throw", "Starting Equipment",
)

_WORD_TO_INT = {"one": 1, "two": 2, "three": 3}

# Phrases in a "Choose N <category>" tool proficiency mapped to the
# tool_profiencies field_tool_category they scope the choice to.
_TOOL_CATEGORY_LABELS = (
    ("musical instrument", "musical_instrument"),
    ("gaming set", "gaming_set"),
    ("artisan", "artisan"),
)


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


def get_subclass_plan(
    class_name: str, subclass_name: str, level: int, *, rag: Optional[RAGSystem] = None
) -> List[Ability]:
    """Resolve a subclass's per-level features from the rules wiki.

    Subclass pages live at ``<class-slug>:<subclass-slug>`` (e.g.
    ``bard:college-of-lore``) and use the same ``Level N: Feature`` headings as
    class pages.

    Args:
        class_name: The parent class name (e.g. "Bard").
        subclass_name: The subclass name (e.g. "College of Lore").
        level: Highest character level to include.
        rag: Optional RAG system; resolved from config when omitted.

    Returns:
        Ordered, de-duplicated subclass features at or below the level. Empty
        when RAG is unavailable or the page cannot be resolved.
    """
    rag_system = rag if rag is not None else _safe_rag_system()
    if rag_system is None or not getattr(rag_system, "enabled", False):
        return []
    client = getattr(rag_system, "rules_client", None)
    if client is None or not _SCRAPING_AVAILABLE or getattr(client, "session", None) is None:
        return []

    class_slug = class_name.strip().lower().replace(" ", "-")
    if class_slug == "":
        return []
    for sub_slug in _subclass_slugs(subclass_name):
        html = _fetch_html(client, f"{client.base_url}/{class_slug}:{sub_slug}")
        if html is None:
            continue
        abilities = [a for a in _parse_abilities(html, "subclass") if a["level"] <= level]
        if abilities:
            return abilities
    return []


# Prefixes the rules wiki sometimes drops from a subclass page slug. The full
# slug is tried first; these yield fallback slugs (e.g. "The Archfey" -> archfey,
# "Circle of Stars" -> stars).
_SUBCLASS_PREFIXES = (
    "the ", "circle of ", "oath of ", "path of ", "way of ", "school of ", "college of ",
)


def _subclass_slugs(subclass_name: str) -> List[str]:
    """Build candidate page slugs for a subclass, full form first.

    Args:
        subclass_name: The subclass display name.

    Returns:
        Ordered, de-duplicated slug candidates.
    """
    base = subclass_name.strip().lower()
    if base == "":
        return []
    candidates = [base]
    for prefix in _SUBCLASS_PREFIXES:
        if base.startswith(prefix):
            candidates.append(base[len(prefix):])
    seen: Dict[str, bool] = {}
    slugs = []
    for candidate in candidates:
        slug = candidate.strip().replace(" ", "-")
        if slug and slug not in seen:
            seen[slug] = True
            slugs.append(slug)
    return slugs


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

    html = _fetch_first(client, page_urls(client.base_url, "background", name))
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

    urls = page_urls(client.base_url, source_type, source_name)
    if not urls:
        return []

    cached = client.cache.get(urls[0] + _CACHE_SUFFIX)
    if cached is not None and isinstance(cached.get("abilities"), list):
        return [_coerce_ability(item) for item in cached["abilities"] if isinstance(item, dict)]

    for url in urls:
        html = _fetch_html(client, url)
        if html is None:
            continue
        abilities = _parse_abilities(html, source_type)
        if abilities:
            client.cache.set(urls[0] + _CACHE_SUFFIX, {"abilities": [dict(a) for a in abilities]})
            return abilities
    return []


def page_urls(base_url: str, source_type: str, source_name: str) -> List[str]:
    """Build the candidate rules-wiki page URLs for a source, best guess first.

    Args:
        base_url: The rules wiki base URL.
        source_type: Source category ("class", "species", "background", ...).
        source_name: Source name (e.g. "Warforged").

    Returns:
        Ordered candidate URLs, or an empty list when the name is blank.
    """
    slug = source_name.strip().lower().replace(" ", "-")
    if slug == "":
        return []
    forms = _SLUG_FORMS.get(source_type, ("{slug}",))
    return [f"{base_url}/{form.format(slug=slug)}" for form in forms]


def _parse_abilities(html: str, source_type: str) -> List[Ability]:
    """Parse abilities from page HTML for the given source type.

    Args:
        html: Raw page HTML.
        source_type: Source category determining the layout to expect.

    Returns:
        De-duplicated abilities parsed from the page.
    """
    content = page_content(html)
    if content is None:
        return []

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
    """Parse the labeled background data from page HTML.

    Args:
        html: Raw background page HTML.

    Returns:
        Structured background data, or None when the data block is absent.
    """
    content = page_content(html)
    if content is None:
        return None

    data_text = _background_data_text(cast("Tag", content))
    if data_text == "":
        return None

    segments = _split_labeled(data_text, _BG_LABELS)
    equipment_text = segments.get("Equipment", "")
    tool_text = segments.get("Tool Proficiencies", "") or segments.get("Tool Proficiency", "")
    ability_text = segments.get("Ability Scores", "") or segments.get("Ability Score", "")
    fixed_tools, tool_choices = _split_background_tools(tool_text)
    return BackgroundData(
        ability_options=_split_names(ability_text),
        feat=_clean_feat(segments.get("Feat", "")),
        feat_description="",
        skills=_split_names(segments.get("Skill Proficiencies", "")),
        tools=fixed_tools,
        tool_choices=tool_choices,
        gold=_parse_gold(equipment_text),
        equipment=_parse_equipment(equipment_text),
    )


def _background_data_text(content: "Tag") -> str:
    """Collect a background's labeled data into one text block.

    The rules wiki uses two layouts: Player's Handbook pages put every label in
    a single paragraph, while the sourcebook pages give each label its own
    paragraph. Joining every label-bearing paragraph handles both.

    Args:
        content: The page-content BeautifulSoup element.

    Returns:
        The joined data text, or an empty string when no labels are present.
    """
    parts: List[str] = []
    for paragraph in content.find_all("p"):
        text = _LOOSE_LABEL_COLON.sub(":", _clean(paragraph.get_text(" ", strip=True)))
        if any(f"{label}:" in text for label in _BG_LABELS):
            parts.append(text)
    joined = " ".join(parts)
    if "Skill Proficiencies:" not in joined:
        return ""
    if "Ability Scores:" not in joined and "Ability Score:" not in joined:
        return ""
    return joined


# Cross-reference asides the sourcebooks append to a feat grant, e.g.
# "A Dark Gift feat of your choice (see "Feats" ...; Mist Walker is recommended)".
# Deliberately narrow: a trailing parenthetical is usually a specialisation that
# belongs in the name ("Magic Initiate (Cleric)"), so only prose is dropped.
_FEAT_ASIDE = re.compile(r"\s*\((?=[^)]*(?:\bsee\b|recommend))[^)]*\)\s*$", re.IGNORECASE)
_FEAT_CHOICE = re.compile(r"^(?:A|An)\s+(.*?)\s+feat of your choice\b.*$", re.IGNORECASE)


def _clean_feat(segment: str) -> str:
    """Reduce a raw feat segment to the feat (or feat category) name.

    Args:
        segment: The raw "Feat" text from the page.

    Returns:
        The feat name, or the category name when the background grants a choice.
    """
    text = _FEAT_ASIDE.sub("", segment.strip()).strip()
    match = _FEAT_CHOICE.match(text)
    if match is not None:
        return match.group(1).strip()
    return text


def _split_background_tools(segment: str) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Split a background tool proficiency into fixed tools and category choices.

    A "choose one kind of Musical Instrument / Gaming Set / Artisan's Tools"
    entry becomes a choice from that category's members (like a class tool
    choice) rather than a literal tool proficiency.

    Args:
        segment: The raw "Tool Proficiency" text.

    Returns:
        A tuple of (fixed tool names, tool choice groups).
    """
    fixed: List[str] = []
    choices: List[Dict[str, Any]] = []
    for entry in _split_names(segment):
        category_key = _tool_category_key(entry)
        if category_key is None:
            fixed.append(entry)
            continue
        choices.append({
            "id": f"background-tools:{category_key}",
            "label": entry,
            "count": 1,
            "from": get_tools_in_category(category_key),
            "kind": "tool",
        })
    return fixed, choices


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

    html = _fetch_first(client, page_urls(client.base_url, "class", class_name))
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
        category_key = _tool_category_key(category)
        options = get_tools_in_category(category_key) if category_key is not None else []
        result["choice"] = {
            "id": "class-tools", "label": f"Tool: {category}",
            "count": count, "from": options, "kind": "tool",
        }
    else:
        result["granted"] = _split_names(segment)
    return result


def _tool_category_key(label: str) -> Optional[str]:
    """Map a "Choose N <category>" label to a tool_category key, or None.

    Args:
        label: The category text from a class tool proficiency.

    Returns:
        The matching tool_category key, or None when unrecognised.
    """
    lowered = label.lower()
    for phrase, key in _TOOL_CATEGORY_LABELS:
        if phrase in lowered:
            return key
    return None


def get_tools_in_category(category: str) -> List[str]:
    """List the tool names in a tool_profiencies category, read from Drupal.

    Args:
        category: A field_tool_category key (e.g. "musical_instrument").

    Returns:
        Tool names in that category; empty when Drupal is unreachable.
    """
    data = query_drupal(
        "{ termToolProfiencies(first: 100) { nodes { name toolCategory } } }"
    )
    nodes = data.get("termToolProfiencies", {}).get("nodes", []) if data else []
    return [
        str(node["name"])
        for node in nodes
        if isinstance(node, dict) and node.get("toolCategory") == category and node.get("name")
    ]


def _class_tool_segment(html: str) -> str:
    """Extract the "Tool Proficiencies" value from a class page.

    Args:
        html: Raw class page HTML.

    Returns:
        The text following "Tool Proficiencies" up to the next proficiency
        label, or the empty string when absent.
    """
    content = page_content(html)
    if content is None:
        return ""
    text = _clean(content.get_text(" ", strip=True))
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
    content = page_content(html)
    if content is None:
        return None

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
