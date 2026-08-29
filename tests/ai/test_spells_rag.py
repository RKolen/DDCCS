"""Test the spell rules-wiki resolver.

Tests src.ai.spells_rag using crafted Wikidot-style HTML and a faked RAG
system, so no live wiki or internet connection is required.
"""

from typing import Any, Dict, Optional

from tests import test_helpers
from tests.ai import rag_fixtures

(
    lookup_spell,
    parse_spell_page,
    spell_page_urls,
) = test_helpers.safe_from_import(
    "src.ai.spells_rag",
    "lookup_spell",
    "parse_spell_page",
    "spell_page_urls",
)


_FIREBALL_HTML = """
<html>
<head><title>Fireball - D&amp;D 5th Edition</title></head>
<body><div id="page-content">
  <p><em>3rd-level evocation</em></p>
  <p><strong>Casting Time:</strong> 1 action</p>
  <p><strong>Range:</strong> 150 feet</p>
  <p><strong>Components:</strong> V, S, M (a tiny ball of bat guano and sulfur)</p>
  <p><strong>Duration:</strong> Instantaneous</p>
  <p>A bright streak flashes from your pointing finger to a point you choose
  within range and then blossoms with a low roar into an explosion of flame.</p>
</div></body></html>
"""

_DETECT_MAGIC_HTML = """
<html>
<head><title>Detect Magic - D&amp;D 5th Edition</title></head>
<body><div id="page-content">
  <p><em>1st-level divination (ritual)</em></p>
  <p><strong>Casting Time:</strong> 1 action</p>
  <p><strong>Range:</strong> Self</p>
  <p><strong>Components:</strong> V, S</p>
  <p><strong>Duration:</strong> Concentration, up to 10 minutes</p>
  <p>For the duration, you sense the presence of magic within 30 feet of you.</p>
</div></body></html>
"""

_LIGHT_HTML = """
<html>
<head><title>Light - D&amp;D 5th Edition</title></head>
<body><div id="page-content">
  <p><em>Evocation cantrip</em></p>
  <p><strong>Casting Time:</strong> 1 action</p>
  <p><strong>Range:</strong> Touch</p>
  <p><strong>Components:</strong> V, M (a firefly or phosphorescent moss)</p>
  <p><strong>Duration:</strong> 1 hour</p>
  <p>You touch one object that is no larger than 10 feet in any dimension.</p>
</div></body></html>
"""


def _fake_rag(
    pages: Optional[Dict[str, str]] = None,
    enabled: bool = True,
) -> Any:
    """Build a RAG stand-in that serves canned spell pages.

    Args:
        pages: Optional URL-to-HTML map. Defaults to Fireball at spell:fireball.
        enabled: RAG enabled flag.

    Returns:
        A fake RAG system.
    """
    canned = pages if pages is not None else {
        "http://rules.example/spell:fireball": _FIREBALL_HTML,
    }

    def _pages(url: str) -> Optional[str]:
        return canned.get(url)

    return rag_fixtures.make_fake_rules_rag(_pages, enabled=enabled)


def test_page_urls_prefer_spell_namespace():
    """Candidate URLs try spell:{slug} before a bare slug."""
    print("\n[TEST] Spell page URLs")
    urls = spell_page_urls("http://wiki.test", "Melf's Acid Arrow")
    assert urls[0] == "http://wiki.test/spell:melfs-acid-arrow"
    assert urls[1] == "http://wiki.test/spells:melfs-acid-arrow"
    assert spell_page_urls("http://wiki.test/", "Fireball")[0] == (
        "http://wiki.test/spell:fireball"
    )
    assert spell_page_urls("http://wiki.test", "   ") == []
    print("  [PASS] spell: slug is first; blank names yield no URLs")


def test_parse_leveled_evocation():
    """A 3rd-level evocation page fills every Drupal field."""
    print("\n[TEST] Parse Fireball")
    data = parse_spell_page(_FIREBALL_HTML)
    assert data is not None
    assert data["name"] == "Fireball"
    assert data["level"] == 3
    assert data["school"] == "Evocation"
    assert data["casting_time"] == "1 action"
    assert data["spell_range"] == "150 feet"
    assert data["components"].startswith("V, S, M")
    assert data["duration"] == "Instantaneous"
    assert data["concentration"] is False
    assert data["ritual"] is False
    assert "explosion of flame" in data["description"]
    print("  [PASS] Level, school, labels, and rules text parsed")


def test_parse_ritual_and_concentration():
    """Ritual lives on the heading; concentration lives on duration."""
    print("\n[TEST] Parse Detect Magic")
    data = parse_spell_page(_DETECT_MAGIC_HTML)
    assert data is not None
    assert data["level"] == 1
    assert data["school"] == "Divination"
    assert data["ritual"] is True
    assert data["concentration"] is True
    print("  [PASS] Ritual and concentration flags")


def test_parse_cantrip():
    """A cantrip heading is level 0."""
    print("\n[TEST] Parse Light cantrip")
    data = parse_spell_page(_LIGHT_HTML)
    assert data is not None
    assert data["level"] == 0
    assert data["school"] == "Evocation"
    print("  [PASS] Cantrip is level 0")


def test_lookup_hits_spell_slug():
    """lookup_spell fetches spell:{slug} through the faked client."""
    print("\n[TEST] lookup_spell")
    data = lookup_spell("Fireball", rag=_fake_rag())
    assert data is not None
    assert data["name"] == "Fireball"
    assert data["level"] == 3
    print("  [PASS] Lookup uses the spell: namespace")


def test_lookup_degrades_when_missing_or_disabled():
    """A miss or disabled RAG returns None, never raises."""
    print("\n[TEST] lookup_spell degrades")
    assert lookup_spell("Fireball", rag=_fake_rag(pages={})) is None
    assert lookup_spell("Fireball", rag=_fake_rag(enabled=False)) is None
    assert parse_spell_page("<html><body>no content</body></html>") is None
    print("  [PASS] Missing pages and disabled RAG degrade to None")


def run_all_tests():
    """Run all spell resolver tests."""
    print("=" * 70)
    print("SPELL RAG RESOLVER TESTS")
    print("=" * 70)

    test_page_urls_prefer_spell_namespace()
    test_parse_leveled_evocation()
    test_parse_ritual_and_concentration()
    test_parse_cantrip()
    test_lookup_hits_spell_slug()
    test_lookup_degrades_when_missing_or_disabled()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL SPELL RAG RESOLVER TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
