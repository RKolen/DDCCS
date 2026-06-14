"""
Test the reusable class-feature RAG service.

Tests src.ai.class_features_rag using the real Bard class template and a
lightweight fake RAG system, so no live wiki or internet connection is
required.

What we test:
- Template baseline features are returned for a known class and level
- Unknown classes return an empty baseline
- A disabled RAG system contributes nothing (baseline only)
- An enabled RAG system merges extra feature names from the rules page
- RAG fetch failures degrade gracefully to the baseline
- Merge de-duplicates case-insensitively while preserving order

Why we test this:
- Confirms the deterministic template path always works
- Ensures the RAG enrichment never breaks the core derivation
- Locks the reusable contract other features will depend on
"""

from types import SimpleNamespace

from tests import test_helpers

(
    get_class_features,
    _merge_unique,
) = test_helpers.safe_from_import(
    "src.ai.class_features_rag",
    "get_class_features",
    "_merge_unique",
)


def _fake_rules_client(sections=None, raises=False):
    """Build a rules wiki client stand-in returning canned sections or raising.

    Args:
        sections: Section dicts to return from fetch_page.
        raises: When True, fetch_page raises to simulate a fetch failure.

    Returns:
        An object exposing a fetch_page(page_title) method.
    """
    def fetch_page(page_title):
        if raises:
            raise OSError("simulated fetch failure")
        return {"title": page_title, "sections": sections or []}

    return SimpleNamespace(fetch_page=fetch_page)


def _fake_rag(enabled=False, rules_client=None):
    """Build a RAG system stand-in exposing only the attributes the service reads.

    Args:
        enabled: RAG enabled flag.
        rules_client: Rules wiki client stand-in, or None.

    Returns:
        An object with enabled and rules_client attributes.
    """
    return SimpleNamespace(enabled=enabled, rules_client=rules_client)


def test_template_baseline_features():
    """A known class returns its template features up to the target level."""
    print("\n[TEST] Class features - template baseline")
    features = get_class_features("Bard", 3, rag=_fake_rag(enabled=False))
    assert "Bardic Inspiration" in features, features
    assert "Spellcasting" in features, features
    assert "Bard Subclass" in features, features
    # Level 4+ features must not appear at level 3.
    assert "Font of Inspiration" not in features, features
    print("  [PASS] Baseline features collected up to level")


def test_unknown_class_returns_empty():
    """An unknown class yields an empty baseline when RAG adds nothing."""
    print("\n[TEST] Class features - unknown class")
    features = get_class_features("Nonexistent", 5, rag=_fake_rag(enabled=False))
    assert features == [], features
    print("  [PASS] Unknown class returns empty list")


def test_disabled_rag_returns_baseline_only():
    """A disabled RAG system contributes no extra features."""
    print("\n[TEST] Class features - disabled RAG")
    rules = _fake_rules_client(sections=[{"title": "Extra Feature", "content": "x"}])
    features = get_class_features("Bard", 1, rag=_fake_rag(enabled=False, rules_client=rules))
    assert "Extra Feature" not in features, features
    print("  [PASS] Disabled RAG adds nothing")


def test_enabled_rag_merges_extra_features():
    """An enabled RAG system merges non-generic section titles as features."""
    print("\n[TEST] Class features - enabled RAG merge")
    rules = _fake_rules_client(
        sections=[
            {"title": "Introduction", "content": "ignored"},
            {"title": "Class Features", "content": "ignored"},
            {"title": "Cutting Words", "content": "a feature"},
        ]
    )
    features = get_class_features("Bard", 1, rag=_fake_rag(enabled=True, rules_client=rules))
    assert "Cutting Words" in features, features
    # Generic sections are excluded.
    assert "Introduction" not in features, features
    assert "Class Features" not in features, features
    print("  [PASS] RAG section titles merged, generics excluded")


def test_rag_fetch_failure_degrades_to_baseline():
    """A RAG fetch failure falls back to the template baseline."""
    print("\n[TEST] Class features - RAG failure degrades")
    rules = _fake_rules_client(raises=True)
    features = get_class_features("Bard", 2, rag=_fake_rag(enabled=True, rules_client=rules))
    assert "Bardic Inspiration" in features, features
    print("  [PASS] Fetch failure degraded to baseline")


def test_merge_unique_dedupes_case_insensitive():
    """Merging de-duplicates case-insensitively and keeps first-seen casing."""
    print("\n[TEST] Class features - merge de-duplication")
    merged = _merge_unique(["Rage", "Spellcasting"], ["rage", "Reckless Attack"])
    assert merged == ["Rage", "Spellcasting", "Reckless Attack"], merged
    print("  [PASS] Merge de-duplicates case-insensitively")


def run_all_tests():
    """Run all class-feature RAG service tests."""
    print("=" * 70)
    print("CLASS FEATURES RAG SERVICE TESTS")
    print("=" * 70)

    test_template_baseline_features()
    test_unknown_class_returns_empty()
    test_disabled_rag_returns_baseline_only()
    test_enabled_rag_merges_extra_features()
    test_rag_fetch_failure_degrades_to_baseline()
    test_merge_unique_dedupes_case_insensitive()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL CLASS FEATURES RAG SERVICE TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
