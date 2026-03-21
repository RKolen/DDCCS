"""Unit tests for src.utils.pronoun_utils."""

from tests.test_helpers import setup_test_environment, import_module


setup_test_environment()

pu = import_module("src.utils.pronoun_utils")
parse_pronouns = pu.parse_pronouns
get_pronoun_display = pu.get_pronoun_display
validate_pronouns = pu.validate_pronouns
PRONOUN_SETS = pu.PRONOUN_SETS
DEFAULT_PRONOUNS = pu.DEFAULT_PRONOUNS


# ---------------------------------------------------------------------------
# parse_pronouns
# ---------------------------------------------------------------------------

def test_parse_he_him():
    """Test parsing he/him pronouns."""
    print("\n[TEST] parse he/him")
    assert parse_pronouns("he/him") == PRONOUN_SETS["he/him"]
    print("[PASS] parse he/him")


def test_parse_she_her():
    """Test parsing she/her pronouns."""
    print("\n[TEST] parse she/her")
    assert parse_pronouns("she/her") == PRONOUN_SETS["she/her"]
    print("[PASS] parse she/her")


def test_parse_they_them():
    """Test parsing they/them pronouns."""
    print("\n[TEST] parse they/them")
    assert parse_pronouns("they/them") == PRONOUN_SETS["they/them"]
    print("[PASS] parse they/them")


def test_parse_none_returns_default():
    """Test that None returns the default (they/them) pronoun set."""
    print("\n[TEST] parse None returns default")
    assert parse_pronouns(None) == PRONOUN_SETS[DEFAULT_PRONOUNS]
    print("[PASS] parse None returns default")


def test_parse_case_insensitive():
    """Test case-insensitive parsing."""
    print("\n[TEST] parse case insensitive")
    assert parse_pronouns("HE/HIM") == PRONOUN_SETS["he/him"]
    print("[PASS] parse case insensitive")


def test_parse_custom_format():
    """Test parsing custom pronoun format xe/xem."""
    print("\n[TEST] parse custom xe/xem")
    result = parse_pronouns("xe/xem")
    assert result["subject"] == "xe"
    assert result["object"] == "xem"
    print("[PASS] parse custom xe/xem")


def test_parse_unknown_single_word_returns_default():
    """Unknown non-slash format falls back to default."""
    print("\n[TEST] parse unknown single word returns default")
    assert parse_pronouns("unknown") == PRONOUN_SETS[DEFAULT_PRONOUNS]
    print("[PASS] parse unknown single word returns default")


def test_pronoun_sets_have_required_keys():
    """All standard pronoun sets include the five required keys."""
    print("\n[TEST] pronoun sets have required keys")
    required_keys = {
        "subject",
        "object",
        "possessive_determiner",
        "possessive_pronoun",
        "reflexive",
    }
    for pronoun_key, pronoun_set in PRONOUN_SETS.items():
        assert required_keys == set(pronoun_set.keys()), (
            f"Pronoun set '{pronoun_key}' missing keys"
        )
    print("[PASS] pronoun sets have required keys")


# ---------------------------------------------------------------------------
# get_pronoun_display
# ---------------------------------------------------------------------------

def test_display_standard():
    """Display of standard pronouns returns exact input."""
    print("\n[TEST] display standard pronouns")
    assert get_pronoun_display("he/him") == "he/him"
    print("[PASS] display standard pronouns")


def test_display_none_returns_empty():
    """Display of None pronouns returns empty string."""
    print("\n[TEST] display None returns empty")
    assert get_pronoun_display(None) == ""
    print("[PASS] display None returns empty")


def test_display_strips_whitespace():
    """Display trims surrounding whitespace."""
    print("\n[TEST] display strips whitespace")
    assert get_pronoun_display("  she/her  ") == "she/her"
    print("[PASS] display strips whitespace")


def test_display_preserves_original_case():
    """Display preserves the original casing."""
    print("\n[TEST] display preserves original case")
    assert get_pronoun_display("He/Him") == "He/Him"
    print("[PASS] display preserves original case")


# ---------------------------------------------------------------------------
# validate_pronouns
# ---------------------------------------------------------------------------

def test_validate_standard_he_him():
    """Standard he/him passes validation."""
    print("\n[TEST] validate he/him")
    is_valid, error = validate_pronouns("he/him")
    assert is_valid
    assert error == ""
    print("[PASS] validate he/him")


def test_validate_standard_she_her():
    """Standard she/her passes validation."""
    print("\n[TEST] validate she/her")
    is_valid, error = validate_pronouns("she/her")
    assert is_valid
    assert error == ""
    print("[PASS] validate she/her")


def test_validate_custom_pronouns():
    """Custom neopronouns pass validation."""
    print("\n[TEST] validate custom xe/xem")
    is_valid, error = validate_pronouns("xe/xem")
    assert is_valid
    assert error == ""
    print("[PASS] validate custom xe/xem")


def test_validate_none_is_valid():
    """None is a valid (unset) pronouns value."""
    print("\n[TEST] validate None is valid")
    is_valid, error = validate_pronouns(None)
    assert is_valid
    assert error == ""
    print("[PASS] validate None is valid")


def test_validate_empty_string_is_invalid():
    """Empty string fails validation."""
    print("\n[TEST] validate empty string is invalid")
    is_valid, error = validate_pronouns("")
    assert not is_valid
    assert "empty" in error.lower()
    print("[PASS] validate empty string is invalid")


def test_validate_whitespace_only_is_invalid():
    """Whitespace-only string fails validation."""
    print("\n[TEST] validate whitespace-only is invalid")
    is_valid, error = validate_pronouns("   ")
    assert not is_valid
    assert "empty" in error.lower()
    print("[PASS] validate whitespace-only is invalid")


def test_validate_non_string_is_invalid():
    """Non-string (e.g. integer) fails validation."""
    print("\n[TEST] validate non-string is invalid")
    is_valid, error = validate_pronouns(42)  # type: ignore[arg-type]
    assert not is_valid
    assert "string" in error.lower()
    print("[PASS] validate non-string is invalid")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all_tests():
    """Run all pronoun utils tests."""
    print("=" * 70)
    print("PRONOUN UTILS TESTS")
    print("=" * 70)

    test_parse_he_him()
    test_parse_she_her()
    test_parse_they_them()
    test_parse_none_returns_default()
    test_parse_case_insensitive()
    test_parse_custom_format()
    test_parse_unknown_single_word_returns_default()
    test_pronoun_sets_have_required_keys()
    test_display_standard()
    test_display_none_returns_empty()
    test_display_strips_whitespace()
    test_display_preserves_original_case()
    test_validate_standard_he_him()
    test_validate_standard_she_her()
    test_validate_custom_pronouns()
    test_validate_none_is_valid()
    test_validate_empty_string_is_invalid()
    test_validate_whitespace_only_is_invalid()
    test_validate_non_string_is_invalid()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL PRONOUN UTILS TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
