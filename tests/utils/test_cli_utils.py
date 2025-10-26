"""Tests for `src.utils.cli_utils` helper functions.

These tests monkeypatch `input()` to simulate user responses and verify
selection and confirmation helpers behave as expected.
"""

from test_helpers import setup_test_environment, import_module

setup_test_environment()

cli_utils = import_module("src.utils.cli_utils")


def test_select_from_list_and_select_character(monkeypatch):
    """Selecting valid and invalid choices yields expected indices or None."""
    items = ["one", "two", "three"]

    # Valid selection (1 -> index 0)
    monkeypatch.setattr("builtins.input", lambda prompt="": "1")
    idx = cli_utils.select_from_list(items, prompt="Pick")
    assert idx == 0

    # Invalid numeric selection -> None
    monkeypatch.setattr("builtins.input", lambda prompt="": "99")
    assert cli_utils.select_from_list(items) is None

    # Non-numeric input -> None
    monkeypatch.setattr("builtins.input", lambda prompt="": "abc")
    assert cli_utils.select_from_list(items) is None

    # select_character_from_list should return (index, name)
    monkeypatch.setattr("builtins.input", lambda prompt="": "2")
    res = cli_utils.select_character_from_list(["Alice", "Bob"])  # choose Bob
    assert isinstance(res, tuple) and res[0] == 1 and res[1] == "Bob"


def test_confirm_and_non_empty_input(monkeypatch):
    """confirm_action and get_non_empty_input handle default and empty values."""
    # Confirm yes
    monkeypatch.setattr("builtins.input", lambda prompt="": "y")
    assert cli_utils.confirm_action("Proceed?", default=False) is True

    # Confirm default on empty response
    monkeypatch.setattr("builtins.input", lambda prompt="": "")
    assert cli_utils.confirm_action("Proceed?", default=True) is True

    # Non-empty input
    monkeypatch.setattr("builtins.input", lambda prompt="": "hello")
    assert cli_utils.get_non_empty_input("Enter:") == "hello"

    # Empty input returns None
    monkeypatch.setattr("builtins.input", lambda prompt="": "   ")
    assert cli_utils.get_non_empty_input("Enter:") is None
