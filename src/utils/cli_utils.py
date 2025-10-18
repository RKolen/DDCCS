"""
Generic CLI Utilities

Reusable functions for command-line interface operations.
"""

from typing import List, Optional, Tuple


def print_section_header(title: str, width: int = 50):
    """
    Print a formatted section header.

    Args:
        title: Section title
        width: Total width of the header
    """
    print(f"\n{title}")
    print("=" * width)


def print_menu_header(title: str, width: int = 30):
    """
    Print a formatted menu header.

    Args:
        title: Menu title
        width: Width of the separator line
    """
    print(f"\n{title}")
    print("-" * width)


def print_list_with_numbers(items: List[str], prefix: str = ""):
    """
    Print a numbered list of items.

    Args:
        items: List of items to print
        prefix: Optional prefix for each line
    """
    for i, item in enumerate(items, 1):
        print(f"{prefix}{i}. {item}")


def select_from_list(items: List[str], prompt: str = "Enter selection") -> Optional[int]:
    """
    Let user select an item from a list by number.

    Args:
        items: List of items to select from
        prompt: Prompt message

    Returns:
        Selected index (0-based), or None if cancelled/invalid
    """
    if not items:
        return None

    try:
        choice = int(input(f"{prompt}: ")) - 1
        if 0 <= choice < len(items):
            return choice
        print("Invalid selection.")
        return None
    except ValueError:
        print("Invalid input. Please enter a number.")
        return None


def select_character_from_list(
    characters: List[str], prompt: str = "Enter character number"
) -> Optional[Tuple[int, str]]:
    """
    Let user select a character from a list.

    Args:
        characters: List of character names
        prompt: Prompt message

    Returns:
        Tuple of (index, character_name), or None if invalid
    """
    if not characters:
        return None

    print_list_with_numbers(characters)

    choice_idx = select_from_list(characters, prompt)
    if choice_idx is not None:
        return choice_idx, characters[choice_idx]
    return None


def confirm_action(prompt: str, default: bool = False) -> bool:
    """
    Ask user to confirm an action with yes/no.

    Args:
        prompt: Confirmation prompt
        default: Default value if user just presses Enter

    Returns:
        True if confirmed, False otherwise
    """
    default_str = "Y/n" if default else "y/N"
    response = input(f"{prompt} ({default_str}): ").strip().lower()

    if not response:
        return default
    return response in ("y", "yes")


def get_non_empty_input(prompt: str) -> Optional[str]:
    """
    Get non-empty input from user.

    Args:
        prompt: Input prompt

    Returns:
        User input string, or None if empty
    """
    user_input = input(prompt).strip()
    if not user_input:
        print("Input cannot be empty.")
        return None
    return user_input
