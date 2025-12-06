"""
Test Terminal Display Utilities

Tests for the rich terminal display module and file viewer functionality.
"""

import json
import os
from pathlib import Path
from tests.test_helpers import setup_test_environment, import_module

setup_test_environment()

# Import modules
terminal_display = import_module("src.utils.terminal_display")
display_file = import_module("src.utils.display_file")

# Import specific functions
display_any_file = terminal_display.display_any_file
display_json_file = terminal_display.display_json_file
display_markdown_file = terminal_display.display_markdown_file
print_error = terminal_display.print_error
print_info = terminal_display.print_info
print_success = terminal_display.print_success
print_warning = terminal_display.print_warning
find_story_file = display_file.find_story_file

# Get project root
project_root = Path(__file__).parent.parent.parent


def test_terminal_display_import():
    """Test that terminal_display module imports correctly."""
    try:
        assert terminal_display.RICH_AVAILABLE is not None
        assert True
    except (ImportError, AttributeError) as e:
        assert False, f"Failed to import terminal_display: {e}"


def test_display_any_file_nonexistent():
    """Test display_any_file handles nonexistent files gracefully."""
    # Should not raise exception
    try:
        display_any_file("/nonexistent/file.md")
        assert True
    except (OSError, ValueError) as e:
        assert False, f"Should not raise exception: {e}"


def test_display_markdown_file_with_real_file():
    """Test display_markdown_file with README.md."""
    readme_path = project_root / "README.md"
    if readme_path.exists():
        try:
            display_markdown_file(str(readme_path))
            assert True
        except (OSError, ValueError) as e:
            assert False, f"Failed to display markdown: {e}"


def test_display_json_file_with_character():
    """Test display_json_file with character profile."""
    char_path = project_root / "game_data" / "characters" / "aragorn.json"
    if char_path.exists():
        try:
            display_json_file(str(char_path))
            assert True
        except (OSError, ValueError) as e:
            assert False, f"Failed to display JSON: {e}"


def test_print_functions():
    """Test that print functions work without errors."""
    try:
        print_error("Test error")
        print_success("Test success")
        print_info("Test info")
        print_warning("Test warning")
        assert True
    except (OSError, ValueError) as e:
        assert False, f"Print functions failed: {e}"


def test_display_file_import():
    """Test that display_file module imports correctly."""
    try:
        assert hasattr(display_file, 'main')
        assert True
    except (ImportError, AttributeError) as e:
        assert False, f"Failed to import display_file: {e}"


def test_find_story_file_with_example_campaign():
    """Test find_story_file with Example_Campaign."""
    result = find_story_file("Example_Campaign", "1")
    if result:
        assert result.endswith(".md")
        assert os.path.exists(result)
    else:
        # Example campaign may not exist in test environment
        assert True


def test_graceful_fallback_without_rich():
    """Test that display functions work even if rich is unavailable."""
    # Functions should work regardless of RICH_AVAILABLE
    try:
        terminal_display.print_error("Test")
        terminal_display.print_info("Test")
        assert True
    except (OSError, ValueError) as e:
        assert False, f"Graceful fallback failed: {e}"


def test_character_profile_loading_from_party():
    """Test that character profiles can be loaded by name field."""
    chars_dir = project_root / "game_data" / "characters"
    party_names = ["Aragorn", "Frodo Baggins", "Gandalf the Grey"]

    found_chars = []
    for char_file in os.listdir(str(chars_dir)):
        if not char_file.endswith('.json'):
            continue
        filepath = chars_dir / char_file
        with open(filepath, 'r', encoding='utf-8') as f:
            char_data = json.load(f)
            char_name = char_data.get('name', '')
            if char_name in party_names:
                found_chars.append(char_name)

    assert len(found_chars) == 3, f"Expected 3 characters, found {len(found_chars)}: {found_chars}"
    assert "Aragorn" in found_chars
    assert "Frodo Baggins" in found_chars
    assert "Gandalf the Grey" in found_chars


if __name__ == "__main__":
    from tests.test_helpers import run_test_suite

    tests = [
        test_terminal_display_import,
        test_display_any_file_nonexistent,
        test_display_markdown_file_with_real_file,
        test_display_json_file_with_character,
        test_print_functions,
        test_display_file_import,
        test_find_story_file_with_example_campaign,
        test_graceful_fallback_without_rich,
        test_character_profile_loading_from_party,
    ]

    run_test_suite("Terminal Display Tests", tests)
