"""Tests for the character portrait prompt builder (portrait_prompt)."""

from tests import test_helpers

build_portrait_prompt = test_helpers.safe_from_import(
    "src.ai.portrait_prompt", "build_portrait_prompt"
)


def test_build_portrait_prompt_includes_descriptor() -> None:
    """Species/lineage/class descriptors appear in the positive prompt."""
    print("\n[TEST] build_portrait_prompt - descriptor included")
    profile = {
        "species": "human",
        "lineage": "Dunedain",
        "character_class": "Ranger",
    }
    positive, negative = build_portrait_prompt(profile)

    assert "Dunedain" in positive
    assert "human" in positive
    assert "Ranger" in positive
    assert negative, "Negative prompt should not be empty"
    print("  [OK] Descriptor and negative prompt present")


def test_build_portrait_prompt_bounds_flavour_text() -> None:
    """Long appearance/backstory flavour is truncated for the encoder."""
    print("\n[TEST] build_portrait_prompt - flavour bounded")
    profile = {
        "species": "elf",
        "appearance": "x" * 1000,
    }
    positive, _ = build_portrait_prompt(profile)

    assert "x" * 280 in positive
    assert "x" * 300 not in positive
    print("  [OK] Flavour text truncated to a bounded length")


def test_build_portrait_prompt_handles_missing_fields() -> None:
    """An almost-empty profile still yields a usable base-style prompt."""
    print("\n[TEST] build_portrait_prompt - missing fields tolerated")
    positive, negative = build_portrait_prompt({})

    assert "portrait" in positive.lower()
    assert negative
    print("  [OK] Base style used when profile fields are absent")


def test_build_portrait_prompt_limits_personality_traits() -> None:
    """Only the first few personality traits are folded into the prompt."""
    print("\n[TEST] build_portrait_prompt - traits limited")
    profile = {
        "species": "dwarf",
        "personality_traits": ["gruff", "loyal", "stubborn", "secretive"],
    }
    positive, _ = build_portrait_prompt(profile)

    assert "gruff" in positive
    assert "secretive" not in positive
    print("  [OK] Trait list bounded to the leading entries")


def test_build_portrait_prompt_strips_html_from_traits() -> None:
    """Rich-text HTML wrappers are stripped from traits and flavour."""
    print("\n[TEST] build_portrait_prompt - HTML stripped")
    profile = {
        "species": "human",
        "personality_traits": ["<p>Stoic</p>", "<p>Wise</p>"],
        "appearance": "<p>weathered &amp; scarred</p>",
    }
    positive, _ = build_portrait_prompt(profile)

    assert "Stoic" in positive
    assert "Wise" in positive
    assert "<p>" not in positive and "</p>" not in positive
    assert "weathered & scarred" in positive
    print("  [OK] Tags removed, entities decoded")


def run_all_tests() -> None:
    """Run all portrait prompt builder tests."""
    test_build_portrait_prompt_includes_descriptor()
    test_build_portrait_prompt_bounds_flavour_text()
    test_build_portrait_prompt_handles_missing_fields()
    test_build_portrait_prompt_limits_personality_traits()
    test_build_portrait_prompt_strips_html_from_traits()
    print("\n[PASS] All portrait prompt tests passed.")


if __name__ == "__main__":
    run_all_tests()
