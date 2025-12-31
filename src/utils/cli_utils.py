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


def select_from_list(
    items: List[str], prompt: str = "Enter selection"
) -> Optional[int]:
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


def get_multiline_input() -> List[str]:
    """
    Get multi-line input from user until empty line.

    Collects lines until user enters an empty line.

    Returns:
        List of non-empty lines entered
    """
    lines = []
    while True:
        line = input()
        if not line:
            break
        lines.append(line)
    return lines


def get_multiline_text(prompt: Optional[str] = None) -> Optional[str]:
    """
    Get multi-line text input from user.

    Args:
        prompt: Optional prompt to display before input

    Returns:
        Joined text from all lines, or None if no input
    """
    if prompt:
        print(prompt)
    lines = get_multiline_input()
    if lines:
        return "\n".join(lines)
    return None


def display_selection_menu(
    items: List[str],
    title: str = "",
    prompt: str = "Select option",
    allow_zero_back: bool = False,
    prefix: str = "  ",
) -> Optional[int]:
    """
    Display a numbered menu and get user selection.

    Combines print_list_with_numbers and select_from_list patterns
    used throughout CLI modules.

    Args:
        items: List of items to display
        title: Optional title shown above the list
        prompt: Selection prompt
        allow_zero_back: If True, 0 returns None (for "back" option)
        prefix: Prefix for each numbered item

    Returns:
        Selected index (0-based), or None if cancelled/invalid
    """
    if not items:
        print("No items available.")
        return None

    if title:
        print(f"\n{title}")

    for i, item in enumerate(items, 1):
        print(f"{prefix}{i}. {item}")

    try:
        range_hint = f"0-{len(items)}" if allow_zero_back else f"1-{len(items)}"
        choice = int(input(f"\n{prompt} ({range_hint}): "))

        if allow_zero_back and choice == 0:
            return None

        if 1 <= choice <= len(items):
            return choice - 1

        print("Invalid selection.")
        return None
    except ValueError:
        print("Invalid input. Please enter a number.")
        return None
