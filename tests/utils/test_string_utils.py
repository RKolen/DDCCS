"""Unit tests for src.utils.string_utils."""

from tests.test_helpers import setup_test_environment, import_module


setup_test_environment()

su = import_module("src.utils.string_utils")
sanitize_filename = su.sanitize_filename
normalize_name = su.normalize_name
slugify = su.slugify
clean_whitespace = su.clean_whitespace
title_case_category = su.title_case_category
extract_bracketed_text = su.extract_bracketed_text
truncate_text = su.truncate_text
is_empty_or_whitespace = su.is_empty_or_whitespace
capitalize_first_letter = su.capitalize_first_letter
remove_multiple_blank_lines = su.remove_multiple_blank_lines


def test_sanitize_and_normalize() -> None:
    """Sanitize and normalize transform names predictably."""
    assert sanitize_filename("Kael Ironheart") == "kael_ironheart"
    assert normalize_name("  Kael Ironheart  ") == "kael ironheart"


def test_slugify_and_clean_whitespace() -> None:
    """Slugify produces URL-safe slugs and whitespace is normalized."""
    assert slugify("The Lost Mine of Phandelver") == "the-lost-mine-of-phandelver"
    assert clean_whitespace("Too   many   spaces") == "Too many spaces"


def test_title_case_and_extract_bracketed() -> None:
    """Title-casing and bracket extraction behave as expected."""
    assert title_case_category("unresolved_plot_threads") == "Unresolved Plot Threads"
    assert extract_bracketed_text("A [note] and [other]") == ["note", "other"]


def test_truncate_and_empty_checks() -> None:
    """Truncation adds suffix and emptiness checks work for None and whitespace."""
    assert truncate_text("Hello world", 5) == "He..."
    assert is_empty_or_whitespace(None)
    assert is_empty_or_whitespace("")
    assert is_empty_or_whitespace("   ")


def test_capitalize_and_remove_blanks() -> None:
    """Capitalization touches only the first letter and blank lines are reduced."""
    assert capitalize_first_letter("kael speaks") == "Kael speaks"
    text = "Line1\n\n\nLine2\n\n\n\nLine3"
    cleaned = remove_multiple_blank_lines(text)
    assert "\n\n\n" not in cleaned
