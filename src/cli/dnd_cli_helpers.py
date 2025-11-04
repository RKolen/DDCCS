"""
Helper functions for DND Consultant CLI

Extracts complex UI interaction logic to reduce complexity in main CLI file.
"""

import os
from typing import List, Tuple, Optional, Dict, Any
from src.characters.consultants.character_profile import (
    CharacterProfile,
    CharacterBehavior,
)


def edit_character_profile_interactive(profile: CharacterProfile) -> CharacterProfile:
    """
    Interactive editor for character profiles.

    Args:
        profile: Character profile to edit

    Returns:
        Modified profile (or original if no changes)
    """
    print(f"\n EDITING: {profile.name}")
    print("-" * 30)

    while True:
        _display_profile_summary(profile)
        _display_edit_menu()

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            profile = _edit_personality_summary(profile)
        elif choice == "2":
            profile = _edit_background_story(profile)
        elif choice == "3":
            profile = _edit_list_field(profile, "motivations", "Motivations")
        elif choice == "4":
            profile = _edit_list_field(profile, "goals", "Goals")
        elif choice == "5":
            profile = _edit_list_field(profile, "fears_weaknesses", "Fears/Weaknesses")
        elif choice == "6":
            profile = _edit_speech_patterns(profile)
        elif choice == "7":
            profile = _edit_decision_making(profile)
        elif choice == "8":
            print("\n[SUCCESS] Profile saved!")
            return profile
        elif choice == "0":
            print("\n[ERROR] Changes discarded.")
            return profile
        else:
            print("Invalid choice. Please try again.")


def _display_profile_summary(profile: CharacterProfile):
    """Display current profile information."""
    print("\nCurrent Profile:")
    print(f"Name: {profile.name}")
    print(f"Class: {profile.character_class.value}")
    print(f"Level: {profile.level}")
    print(f"Personality: {profile.personality_summary}")
    print(f"Background: {profile.background_story}")
    print(f"Motivations: {', '.join(profile.motivations)}")
    print(f"Goals: {', '.join(profile.goals)}")
    print(f"Fears/Weaknesses: {', '.join(profile.fears_weaknesses)}")


def _display_edit_menu():
    """Display the character profile editing menu."""
    print("\nWhat would you like to edit?")
    print("1. Personality Summary")
    print("2. Background Story")
    print("3. Motivations")
    print("4. Goals")
    print("5. Fears/Weaknesses")
    print("6. Speech Patterns")
    print("7. Decision Making Style")
    print("8. Save and Exit")
    print("0. Exit without Saving")


def _edit_personality_summary(profile: CharacterProfile) -> CharacterProfile:
    """Edit personality summary field."""
    new_value = input("Enter new personality summary: ").strip()
    if new_value:
        profile.personality_summary = new_value
    return profile


def _edit_background_story(profile: CharacterProfile) -> CharacterProfile:
    """Edit background story field (multi-line input)."""
    print("Enter new background story (end with empty line):")
    lines = []
    while True:
        line = input()
        if not line:
            break
        lines.append(line)
    if lines:
        profile.background_story = "\n".join(lines)
    return profile


def _edit_list_field(
    profile: CharacterProfile, field_name: str, display_name: str
) -> CharacterProfile:
    """Edit a list field (motivations, goals, fears)."""
    print(f"\nCurrent {display_name}: {', '.join(getattr(profile, field_name))}")
    print(f"Enter new {display_name} (comma-separated):")
    new_values = input().strip()
    if new_values:
        setattr(profile, field_name, [v.strip() for v in new_values.split(",")])
    return profile


def _edit_speech_patterns(profile: CharacterProfile) -> CharacterProfile:
    """Edit speech patterns field."""
    new_value = input("Enter new speech patterns: ").strip()
    if new_value:
        # Accept comma-separated patterns and store them on the nested behavior dataclass
        patterns = [v.strip() for v in new_value.split(",") if v.strip()]
        if not getattr(profile, "behavior", None):
            profile.behavior = CharacterBehavior()
        profile.behavior.speech_patterns = patterns
    return profile


def _edit_decision_making(profile: CharacterProfile) -> CharacterProfile:
    """Edit decision making style field."""
    new_value = input("Enter new decision making style: ").strip()
    if new_value:
        # Store decision making style on nested behavior dataclass
        if not getattr(profile, "behavior", None):
            profile.behavior = CharacterBehavior()
        profile.behavior.decision_making_style = new_value
    return profile


def get_continuation_scene_type() -> Optional[bool]:
    """Prompt user to select continuation scene type.

    Returns:
        True for combat, False for exploration/social, None if user cancels
    """
    print("\nWhat type of scene is this?")
    print("1. Combat/Action scene")
    print("2. Exploration/Social/Roleplay scene")

    scene_type = input("\nChoice (1-2): ").strip()
    if scene_type == "1":
        return True
    if scene_type == "2":
        return False

    print("Invalid choice. Canceling.")
    return None


def get_continuation_prompt(is_combat: bool) -> str:
    """Prompt user for continuation narrative.

    Args:
        is_combat: True for combat prompt, False for exploration

    Returns:
        User's continuation prompt or empty string if user cancels
    """
    if is_combat:
        print("\nDescribe the tactical combat situation.")
        print("Example: 'Goblins ambush the party on the forest road'")
    else:
        print("\nDescribe what happens next in the story.")
        print("Example: 'A mysterious stranger enters the tavern'")

    story_prompt = input("\nContinuation prompt: ").strip()
    if not story_prompt:
        print("No prompt provided. Canceling.")
        return ""

    return story_prompt


def get_combat_narrative_style() -> str:
    """
    Prompt user for combat narrative style.

    Returns:
        Style string (cinematic, gritty, heroic, tactical)
    """
    print("\n Choose narrative style:")
    print("1. Cinematic (epic, movie-like)")
    print("2. Gritty (realistic, visceral)")
    print("3. Heroic (valorous, inspirational)")
    print("4. Tactical (clear, precise)")

    style_choice = input("Enter choice (1-4, or press Enter for Cinematic): ").strip()

    style_map = {
        "1": "cinematic",
        "2": "gritty",
        "3": "heroic",
        "4": "tactical",
        "": "cinematic",
    }
    return style_map.get(style_choice, "cinematic")


def get_multi_line_input(prompt: str, end_marker: str = "###") -> str:
    """
    Get multi-line input from user.

    Args:
        prompt: Message to display before input
        end_marker: String that marks end of input

    Returns:
        Combined input string
    """
    print(prompt)
    lines = []
    while True:
        line = input()
        if line.strip() == end_marker:
            break
        lines.append(line)
    return "\n".join(lines).strip()


def select_story_from_series(
    story_series: List[str], series_path_callback
) -> Tuple[Optional[str], Optional[str]]:
    """
    Interactive story selection from series.

    Args:
        story_series: List of available story series
        series_path_callback: Function to get story files for a series

    Returns:
        Tuple of (story_path, story_context) or (None, None)
    """
    if not story_series:
        return None, None

    # Select series
    series_name = _prompt_series_selection(story_series)
    if not series_name:
        return None, None

    # Get and select story file
    story_files = series_path_callback(series_name)
    story_file = _prompt_story_selection(story_files, series_name)

    if not story_file:
        return None, None

    return story_file, series_name


def _prompt_series_selection(story_series: List[str]) -> Optional[str]:
    """Prompt user to select a series."""
    print("\nStory Series:")
    for i, series in enumerate(story_series, 1):
        print(f"{i}. {series}")

    series_choice = input("\nSelect series number (or press Enter to skip): ").strip()

    if series_choice.isdigit():
        idx = int(series_choice) - 1
        if 0 <= idx < len(story_series):
            return story_series[idx]
    return None


def _prompt_story_selection(
    story_files: List[str], series_name: str
) -> Optional[str]:
    """Prompt user to select a story file."""
    if not story_files:
        print(f"No stories found in {series_name}")
        return None

    print(f"\nStories in {series_name}:")
    for i, story_file in enumerate(story_files, 1):
        print(f"{i}. {story_file}")

    story_choice = input("\nSelect story number: ").strip()
    if story_choice.isdigit():
        story_idx = int(story_choice) - 1
        if 0 <= story_idx < len(story_files):
            return story_files[story_idx]
    return None


# ============================================================================
# Combat Conversion Helper Functions
# ============================================================================


def get_multi_line_combat_input() -> str:
    """
    Get multi-line combat description from user.

    Returns:
        Combat description text, or empty string if cancelled.
    """
    print("Enter your combat description (end with '###' on a new line):")
    lines = []
    while True:
        line = input()
        if line.strip() == "###":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def select_narrative_style() -> str:
    """
    Prompt user to select narrative style for combat.

    Returns:
        Selected style: 'cinematic', 'gritty', 'heroic', or 'tactical'
    """
    print("\n Choose narrative style:")
    print("1. Cinematic (epic, movie-like)")
    print("2. Gritty (realistic, visceral)")
    print("3. Heroic (valorous, inspirational)")
    print("4. Tactical (clear, precise)")

    style_choice = input("Enter choice (1-4, or press Enter for Cinematic): ").strip()
    style_map = {
        "1": "cinematic",
        "2": "gritty",
        "3": "heroic",
        "4": "tactical",
        "": "cinematic",
    }
    return style_map.get(style_choice, "cinematic")


def select_target_story_for_combat(
    workspace_path: str, story_manager
) -> Tuple[Optional[str], str]:
    """
    Interactive story selection for combat narrative appending.

    Args:
        workspace_path: Root workspace path
        story_manager: Story manager instance

    Returns:
        Tuple of (story_file_path, story_context_text)
        Returns (None, "") if no story selected
    """
    print("\n Which story should this combat be added to?")
    story_series = story_manager.get_story_series()

    if not story_series:
        return None, ""

    # Select series
    series_name = _select_story_series(story_series)
    if not series_name:
        return None, ""

    # Get stories in series
    story_files = story_manager.get_story_files_in_series(series_name)
    if not story_files:
        return None, ""

    # Select story file
    story_file = _select_story_file(story_files, series_name)
    if not story_file:
        return None, ""

    # Build path and read context
    target_path = os.path.join(workspace_path, series_name, story_file)
    context = _read_story_context(target_path)

    return target_path, context


def _select_story_series(story_series: List[str]) -> Optional[str]:
    """Select a story series from list."""
    print("\nStory Series:")
    for i, series in enumerate(story_series, 1):
        print(f"{i}. {series}")

    series_choice = input("\nSelect series number (or press Enter to skip): ").strip()

    if not series_choice.isdigit():
        return None

    series_idx = int(series_choice) - 1
    if 0 <= series_idx < len(story_series):
        return story_series[series_idx]
    return None


def _select_story_file(story_files: List[str], series_name: str) -> Optional[str]:
    """Select a story file from list."""
    print(f"\nStories in {series_name}:")
    for i, story_file in enumerate(story_files, 1):
        print(f"{i}. {story_file}")

    story_choice = input("\nSelect story number: ").strip()
    if not story_choice.isdigit():
        return None

    story_idx = int(story_choice) - 1
    if 0 <= story_idx < len(story_files):
        return story_files[story_idx]
    return None


def _read_story_context(story_path: str) -> str:
    """Read story context from file."""
    if os.path.exists(story_path):
        with open(story_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def save_combat_narrative(
    narrative: str,
    combat_title: str,
    target_story_path: Optional[str],
    workspace_path: str,
) -> None:
    """
    Save or append combat narrative to file.

    Args:
        narrative: Generated combat narrative text
        combat_title: Title for the combat section
        target_story_path: Path to story file (if appending), or None
        workspace_path: Root workspace path for new files
    """
    if target_story_path:
        append = (
            input(f"\nAppend to {os.path.basename(target_story_path)}? (y/n): ")
            .strip()
            .lower()
        )
        if append == "y":
            with open(target_story_path, "a", encoding="utf-8") as f:
                f.write(f"\n\n### {combat_title}\n\n")
                f.write(narrative)
            print(f"[SUCCESS] Appended to: {target_story_path}")
    else:
        save = input("\nSave to separate file? (y/n): ").strip().lower()
        if save == "y":
            filename = input("Enter filename (without extension): ").strip()
            if filename:
                filepath = os.path.join(workspace_path, f"{filename}.md")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"# {combat_title}\n\n")
                    f.write(narrative)
                print(f"[SUCCESS] Saved to: {filepath}")


def _prompt_for_series_selection(
    series_list: List[str],
) -> Optional[str]:
    """Prompt user to select a series from list.

    Args:
        series_list: List of available series

    Returns:
        Selected series name or None
    """
    print("\nAvailable story series:")
    for i, series in enumerate(series_list, 1):
        print(f"{i}. {series}")

    try:
        series_choice = int(input("Select series (0 to cancel): "))
        if series_choice == 0:
            return None
        if 1 <= series_choice <= len(series_list):
            return series_list[series_choice - 1]
        print("Invalid choice.")
    except ValueError:
        print("Invalid input.")
    return None


def _prompt_for_story_selection(
    story_files: List[str], series_name: str
) -> Optional[str]:
    """Prompt user to select a story from list.

    Args:
        story_files: List of available story files
        series_name: Name of the series (for display)

    Returns:
        Selected story filename or None
    """
    print(f"\nStories in {series_name}:")
    for i, story in enumerate(story_files, 1):
        print(f"{i}. {story}")

    try:
        story_choice = int(input("Select story (0 to cancel): "))
        if story_choice == 0:
            return None
        if 1 <= story_choice <= len(story_files):
            return story_files[story_choice - 1]
        print("Invalid choice.")
    except ValueError:
        print("Invalid input.")
    return None


def get_series_and_story_from_manager(
    story_manager
) -> Optional[Tuple[str, str]]:
    """Prompt user to select a series and story from story manager.

    Args:
        story_manager: StoryManager instance with get_story_series and
                      get_story_files_in_series methods

    Returns:
        Tuple of (series_name, story_filename) or None if cancelled
    """
    series_list = story_manager.get_story_series()
    if not series_list:
        print("No story series found.")
        return None

    series_name = _prompt_for_series_selection(series_list)
    if series_name is None:
        return None

    story_files = story_manager.get_story_files_in_series(series_name)
    if not story_files:
        print(f"No stories in series '{series_name}'.")
        return None

    story_filename = _prompt_for_story_selection(story_files, series_name)
    if story_filename is None:
        return None

    return (series_name, story_filename)


def collect_generic_input(
    fields: List[Tuple[str, str, Optional[str]]]
) -> Optional[Dict[str, Any]]:
    """Collect generic input from user for multiple fields.

    Args:
        fields: List of (field_name, prompt_text, default_value) tuples
               If default_value is provided, it's used when input is empty
               If default_value is None, empty input causes error/retry

    Returns:
        Dictionary with field_name: value pairs, or None if user cancels
    """
    result = {}

    for field_name, prompt_text, default_value in fields:
        user_input = input(prompt_text).strip()

        # Check for cancel command
        if user_input.lower() == 'done':
            return None

        # Handle empty input
        if not user_input:
            if default_value is not None:
                result[field_name] = default_value
            else:
                print(f"{field_name.replace('_', ' ').title()} cannot be empty.")
                return None
        else:
            result[field_name] = user_input

    return result
