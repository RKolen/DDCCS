"""
Helper functions for DND Consultant CLI

Extracts complex UI interaction logic to reduce complexity in main CLI file.
"""

from typing import List, Tuple, Optional
from src.characters.consultants.character_consultants import CharacterProfile


def edit_character_profile_interactive(profile: CharacterProfile) -> CharacterProfile:
    """
    Interactive editor for character profiles.
    
    Args:
        profile: Character profile to edit
        
    Returns:
        Modified profile (or original if no changes)
    """
    print(f"\n📝 EDITING: {profile.name}")
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
            print("\n✅ Profile saved!")
            return profile
        elif choice == "0":
            print("\n❌ Changes discarded.")
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
        profile.speech_patterns = new_value
    return profile


def _edit_decision_making(profile: CharacterProfile) -> CharacterProfile:
    """Edit decision making style field."""
    new_value = input("Enter new decision making style: ").strip()
    if new_value:
        profile.decision_making = new_value
    return profile


def get_combat_narrative_style() -> str:
    """
    Prompt user for combat narrative style.
    
    Returns:
        Style string (cinematic, gritty, heroic, tactical)
    """
    print("\n🎨 Choose narrative style:")
    print("1. Cinematic (epic, movie-like)")
    print("2. Gritty (realistic, visceral)")
    print("3. Heroic (valorous, inspirational)")
    print("4. Tactical (clear, precise)")

    style_choice = input(
        "Enter choice (1-4, or press Enter for Cinematic): "
    ).strip()

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
    story_series: List[str],
    series_path_callback
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

    print("\nStory Series:")
    for i, series in enumerate(story_series, 1):
        print(f"{i}. {series}")

    series_choice = input(
        "\nSelect series number (or press Enter to skip): "
    ).strip()

    if not series_choice.isdigit():
        return None, None

    idx = int(series_choice) - 1
    if not 0 <= idx < len(story_series):
        return None, None

    series_name = story_series[idx]
    story_files = series_path_callback(series_name)

    if not story_files:
        print(f"No stories found in {series_name}")
        return None, None

    print(f"\nStories in {series_name}:")
    for i, story_file in enumerate(story_files, 1):
        print(f"{i}. {story_file}")

    story_choice = input("\nSelect story number: ").strip()
    if not story_choice.isdigit():
        return None, None

    story_idx = int(story_choice) - 1
    if not 0 <= story_idx < len(story_files):
        return None, None

    return story_files[story_idx], series_name
