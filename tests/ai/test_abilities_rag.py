"""
Test the abilities RAG resolver.

Tests src.ai.abilities_rag using crafted Wikidot-style HTML and a faked RAG
system, so no live wiki or internet connection is required.

What we test:
- Class pages parse "Level N: Feature" headings into leveled abilities
- Species pages parse bold-lead trait paragraphs (level 1)
- Stat lines (bold lead ending in ':') are excluded from traits
- get_abilities filters by level and tags the source type
- A disabled RAG system yields no abilities
- Duplicate ability names are de-duplicated

Why we test this:
- Locks the two-layout parsing contract against the 2024 ruleset structure
- Ensures the resolver degrades safely and never blocks character creation
"""

from types import SimpleNamespace

from tests import test_helpers

(
    get_abilities,
    _parse_abilities,
    _dedupe,
) = test_helpers.safe_from_import(
    "src.ai.abilities_rag",
    "get_abilities",
    "_parse_abilities",
    "_dedupe",
)

_CLASS_HTML = """
<html><body><div id="page-content">
  <h3>Fighter Class Features</h3>
  <h3>Level 1: Fighting Style</h3><p>You gain a Fighting Style feat.</p>
  <h3>Level 1: Second Wind</h3><p>You have a well of stamina.</p>
  <h3>Level 5: Extra Attack</h3><p>You can attack twice.</p>
</div></body></html>
"""

_SPECIES_HTML = """
<html><body><div id="page-content">
  <h3>Human Traits</h3>
  <p><strong>Creature Type:</strong> Humanoid. Size: Medium.</p>
  <p><strong>Resourceful.</strong> You gain Heroic Inspiration after a Long Rest.</p>
  <p><strong>Skillful.</strong> You gain proficiency in one skill.</p>
</div></body></html>
"""


def _fake_rag(html, enabled=True):
    """Build a RAG stand-in whose rules client returns canned HTML.

    Args:
        html: HTML body returned by the fake session.
        enabled: RAG enabled flag.

    Returns:
        A SimpleNamespace exposing enabled + rules_client.
    """
    response = SimpleNamespace(text=html, raise_for_status=lambda: None)
    session = SimpleNamespace(get=lambda url, timeout=10: response)
    cache = SimpleNamespace(get=lambda key: None, set=lambda key, content: None)
    client = SimpleNamespace(base_url="http://rules.example", session=session, cache=cache)
    return SimpleNamespace(enabled=enabled, rules_client=client)


def test_parse_class_features():
    """Class pages parse Level headings into leveled abilities."""
    print("\n[TEST] Abilities - class feature parsing")
    abilities = _parse_abilities(_CLASS_HTML, "class")
    names = {a["name"]: a["level"] for a in abilities}
    assert names.get("Fighting Style") == 1, names
    assert names.get("Second Wind") == 1, names
    assert names.get("Extra Attack") == 5, names
    assert "Fighter Class Features" not in names, names
    assert all(a["source_type"] == "class" for a in abilities), abilities
    print("  [PASS] Class features parsed with levels")


def test_parse_species_traits():
    """Species pages parse bold-lead traits as level-1 abilities."""
    print("\n[TEST] Abilities - species trait parsing")
    abilities = _parse_abilities(_SPECIES_HTML, "species")
    names = [a["name"] for a in abilities]
    assert "Resourceful" in names, names
    assert "Skillful" in names, names
    # Stat lines ending with ':' are not traits.
    assert "Creature Type" not in names, names
    assert all(a["level"] == 1 for a in abilities), abilities
    assert all(a["source_type"] == "species" for a in abilities), abilities
    print("  [PASS] Species traits parsed, stat lines excluded")


def test_get_abilities_filters_by_level():
    """get_abilities returns only abilities at or below the target level."""
    print("\n[TEST] Abilities - level filter")
    level_one = get_abilities("class", "Fighter", 1, rag=_fake_rag(_CLASS_HTML))
    names = [a["name"] for a in level_one]
    assert "Fighting Style" in names, names
    assert "Extra Attack" not in names, names
    print("  [PASS] Higher-level features filtered out")


def test_disabled_rag_returns_empty():
    """A disabled RAG system yields no abilities."""
    print("\n[TEST] Abilities - disabled RAG")
    abilities = get_abilities("class", "Fighter", 5, rag=_fake_rag(_CLASS_HTML, enabled=False))
    assert abilities == [], abilities
    print("  [PASS] Disabled RAG returns empty")


def test_dedupe_by_name():
    """Duplicate ability names are dropped, keeping first-seen order."""
    print("\n[TEST] Abilities - de-duplication")
    items = [
        {"name": "Second Wind", "description": "a", "level": 1, "source_type": "class"},
        {"name": "second wind", "description": "b", "level": 2, "source_type": "class"},
        {"name": "Action Surge", "description": "c", "level": 2, "source_type": "class"},
    ]
    deduped = _dedupe(items)
    assert [a["name"] for a in deduped] == ["Second Wind", "Action Surge"], deduped
    print("  [PASS] Duplicate names removed")


def run_all_tests():
    """Run all abilities RAG resolver tests."""
    print("=" * 70)
    print("ABILITIES RAG RESOLVER TESTS")
    print("=" * 70)

    test_parse_class_features()
    test_parse_species_traits()
    test_get_abilities_filters_by_level()
    test_disabled_rag_returns_empty()
    test_dedupe_by_name()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL ABILITIES RAG RESOLVER TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
