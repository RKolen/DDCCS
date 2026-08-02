"""
Test the character-creation catalogue resolver.

Tests src.ai.catalog_rag using crafted Wikidot-style HTML and a faked RAG
system, so no live wiki or internet connection is required.

What we test:
- An index page's entry links become catalogue entries, sorted by name
- Each entry carries the sourcebook from its own page's "Source:" line
- Entry names come from the page title with minor words lowercased
- Classes resolve through the "<class>:main" slug form, species through
  "species:<slug>"
- Sourcebook filtering keeps only owned books and is case-insensitive
- An empty sourcebook list means no restriction
- An unknown kind and a disabled RAG system both yield an empty catalogue

Why we test this:
- Locks the index-page contract the taxonomy seeder depends on
- Ensures a group is only ever offered content from books it owns
- Ensures the resolver degrades safely and never blocks character creation
"""

from tests import test_helpers
from tests.ai import rag_fixtures

(
    list_catalog,
    get_sourcebook,
    filter_by_sourcebooks,
    _display_name,
    _index_slugs,
    _parse_sourcebook,
    _entry_title,
) = test_helpers.safe_from_import(
    "src.ai.catalog_rag",
    "list_catalog",
    "get_sourcebook",
    "filter_by_sourcebooks",
    "_display_name",
    "_index_slugs",
    "_parse_sourcebook",
    "_entry_title",
)

_BACKGROUND_INDEX = """
<html><body><div id="page-content">
  <table>
    <tr><th>Name</th></tr>
    <tr><td><a href="/background:acolyte">Acolyte</a></td></tr>
    <tr><td><a href="/background:harper">Harper</a></td></tr>
    <tr><td><a href="/background:knight-of-the-gauntlet">Knight Of The Gauntlet</a></td></tr>
  </table>
  <p><a href="/background:all">All backgrounds</a></p>
</div></body></html>
"""

_CLASS_INDEX = """
<html><body><div id="page-content">
  <table>
    <tr><th>Name</th></tr>
    <tr><td><a href="/fighter:main">Fighter</a></td></tr>
    <tr><td><a href="/artificer:main">Artificer</a></td></tr>
  </table>
</div></body></html>
"""

_SPECIES_INDEX = """
<html><body><div id="page-content">
  <table><tr><th>Name</th></tr>
    <tr><td><a href="/species:warforged">Warforged</a></td></tr>
  </table>
</div></body></html>
"""


def _entry_page(title: str, source: str) -> str:
    """Build a canned entry page carrying a title and a source line.

    Args:
        title: The page's own title, before the site-name suffix.
        source: The sourcebook named on the page's first paragraph.

    Returns:
        Wikidot-style page HTML.
    """
    return (
        f"<html><head><title>{title} - D&amp;D 5e (2024)</title></head><body>"
        f'<div id="page-content"><p>Source: {source}</p>'
        "<p>Flavour text about this option.</p></div></body></html>"
    )


# Sourcebook each canned entry page reports, keyed by its page slug.
_PAGE_SOURCES = {
    "background:acolyte": ("Acolyte", "Player's Handbook"),
    "background:harper": ("Harper", "Forgotten Realms - Heroes of Faerun"),
    "background:knight-of-the-gauntlet": (
        "Knight Of The Gauntlet", "Forgotten Realms - Heroes of Faerun",
    ),
    "fighter:main": ("Fighter", "Player's Handbook"),
    "artificer:main": ("Artificer", "Eberron - Forge of the Artificer"),
    "species:warforged": ("Warforged", "Eberron - Forge of the Artificer"),
}

_INDEX_PAGES = {
    "background:all": _BACKGROUND_INDEX,
    "class:all": _CLASS_INDEX,
    "species:all": _SPECIES_INDEX,
}


def _page_for(url: str):
    """Serve the canned index or entry page for a requested URL.

    Args:
        url: The requested page URL.

    Returns:
        The page HTML, or None when the fake wiki has no such page.
    """
    slug = url.rsplit("/", 1)[-1]
    if slug in _INDEX_PAGES:
        return _INDEX_PAGES[slug]
    if slug in _PAGE_SOURCES:
        return _entry_page(*_PAGE_SOURCES[slug])
    return None


def _fake_rag(enabled: bool = True):
    """Build a RAG stand-in serving the canned index and entry pages.

    Args:
        enabled: RAG enabled flag.

    Returns:
        A SimpleNamespace exposing enabled + rules_client.
    """
    return rag_fixtures.make_fake_rules_rag(_page_for, enabled=enabled)


def test_index_slugs_extracted():
    """An index page's entry links yield slugs, excluding the index itself."""
    print("\n[TEST] Catalogue - index slug extraction")
    slugs = _index_slugs(_BACKGROUND_INDEX, "background")
    assert slugs == ["acolyte", "harper", "knight-of-the-gauntlet"], slugs
    assert _index_slugs(_CLASS_INDEX, "class") == ["fighter", "artificer"]
    print("  [PASS] Entry slugs extracted and the index link skipped")


def test_source_and_title_parsed():
    """An entry page yields its sourcebook and its own title."""
    print("\n[TEST] Catalogue - source line and title parsing")
    page = _entry_page("Harper", "Forgotten Realms - Heroes of Faerun")
    assert _parse_sourcebook(page) == "Forgotten Realms - Heroes of Faerun"
    assert _entry_title(page) == "Harper"
    assert _parse_sourcebook("<div id='page-content'><p>No source</p></div>") == ""
    print("  [PASS] Source line and title read from the entry page")


def test_display_name_lowercases_minor_words():
    """Wiki title casing is normalised without changing the derived slug."""
    print("\n[TEST] Catalogue - display name normalisation")
    assert _display_name("Knight Of The Gauntlet") == "Knight of the Gauntlet"
    assert _display_name("house-cannith-heir") == "House Cannith Heir"
    assert _display_name("Lords' Alliance Vassal") == "Lords' Alliance Vassal"
    normalised = _display_name("Knight Of The Gauntlet")
    assert normalised.lower().replace(" ", "-") == "knight-of-the-gauntlet"
    print("  [PASS] Minor words lowercased and the slug still round-trips")


def test_list_catalog_tags_each_entry():
    """Every catalogue entry carries its kind and sourcebook."""
    print("\n[TEST] Catalogue - listing with sourcebooks")
    rag = _fake_rag()
    entries = list_catalog("background", rag=rag)
    assert [entry["name"] for entry in entries] == [
        "Acolyte", "Harper", "Knight of the Gauntlet",
    ], entries
    assert entries[0]["source"] == "Player's Handbook", entries[0]
    assert entries[1]["source"] == "Forgotten Realms - Heroes of Faerun", entries[1]
    assert all(entry["kind"] == "background" for entry in entries)
    print("  [PASS] Entries listed in name order with their sourcebooks")


def test_class_and_species_slug_forms():
    """Classes resolve via '<class>:main' and species via 'species:<slug>'."""
    print("\n[TEST] Catalogue - per-kind page slug forms")
    rag = _fake_rag()
    classes = list_catalog("class", rag=rag)
    assert {entry["name"] for entry in classes} == {"Artificer", "Fighter"}, classes
    artificer = next(entry for entry in classes if entry["name"] == "Artificer")
    assert artificer["source"] == "Eberron - Forge of the Artificer", artificer

    species = list_catalog("species", rag=rag)
    assert species[0]["name"] == "Warforged", species
    assert species[0]["source"] == "Eberron - Forge of the Artificer", species
    print("  [PASS] Sourcebook-only pages resolve through their category prefix")


def test_get_sourcebook_for_one_entry():
    """A single entry's sourcebook resolves without listing the catalogue."""
    print("\n[TEST] Catalogue - single entry sourcebook")
    rag = _fake_rag()
    assert get_sourcebook("class", "Artificer", rag=rag) == "Eberron - Forge of the Artificer"
    assert get_sourcebook("background", "Nonexistent", rag=rag) == ""
    print("  [PASS] Sourcebook resolved per entry and missing pages degrade")


def test_filter_by_sourcebooks():
    """Filtering keeps only entries from the named books."""
    print("\n[TEST] Catalogue - sourcebook filtering")
    entries = list_catalog("background", rag=_fake_rag())
    owned = filter_by_sourcebooks(entries, ["forgotten realms"])
    assert [entry["name"] for entry in owned] == ["Harper", "Knight of the Gauntlet"], owned
    assert len(filter_by_sourcebooks(entries, [])) == len(entries)
    assert filter_by_sourcebooks(entries, ["Lorwyn"]) == []
    print("  [PASS] Only owned books kept; an empty list means no restriction")


def test_unknown_kind_and_disabled_rag():
    """An unknown kind or disabled RAG yields an empty catalogue."""
    print("\n[TEST] Catalogue - safe degradation")
    assert list_catalog("weapon", rag=_fake_rag()) == []
    assert list_catalog("background", rag=_fake_rag(enabled=False)) == []
    assert get_sourcebook("class", "Fighter", rag=_fake_rag(enabled=False)) == ""
    print("  [PASS] Unknown kinds and disabled RAG degrade to empty")


def run_all_tests():
    """Run all catalogue resolver tests."""
    print("=" * 70)
    print("CATALOGUE RAG RESOLVER TESTS")
    print("=" * 70)

    test_index_slugs_extracted()
    test_source_and_title_parsed()
    test_display_name_lowercases_minor_words()
    test_list_catalog_tags_each_entry()
    test_class_and_species_slug_forms()
    test_get_sourcebook_for_one_entry()
    test_filter_by_sourcebooks()
    test_unknown_kind_and_disabled_rag()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL CATALOGUE RAG RESOLVER TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
