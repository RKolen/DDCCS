"""
Character Template Creation Wizard

Interactive prompts for gathering character options when creating a new
character from a class template. Separated from CharacterCLIManager to
keep module line counts manageable.
"""

from typing import Dict, List, Optional, Any

from src.characters.character_template import TemplateOptions


def prompt_template_selection(templates: List[str]) -> Optional[str]:
    """Display template list and return the selected class name.

    Args:
        templates: Sorted list of available template names.

    Returns:
        Selected class name or None if cancelled.
    """
    print("\nAvailable class templates:")
    for idx, name in enumerate(templates, 1):
        print(f"  {idx}. {name.capitalize()}")
    print("  0. Cancel")

    choice = input("\nSelect class (number): ").strip()
    if choice == "0":
        return None
    try:
        index = int(choice) - 1
        if 0 <= index < len(templates):
            return templates[index]
    except ValueError:
        pass
    print(f"[ERROR] Choose a number between 1 and {len(templates)}.")
    return None


def prompt_character_name() -> Optional[str]:
    """Prompt for character name.

    Returns:
        Entered name or None if empty/cancelled.
    """
    name = input("\nCharacter name: ").strip()
    if not name:
        print("[INFO] No name entered. Cancelling.")
        return None
    return name


def prompt_race(template: Dict[str, Any]) -> str:
    """Prompt for character species/race.

    Args:
        template: Loaded class template.

    Returns:
        Selected or entered species name.
    """
    recommended = template.get("recommended_races", [])
    if recommended:
        print("\nRecommended species for this class:")
        for idx, species in enumerate(recommended, 1):
            print(f"  {idx}. {species}")
        print(f"  {len(recommended) + 1}. Enter custom species")

        choice = input("Select species (number): ").strip()
        try:
            index = int(choice) - 1
            if 0 <= index < len(recommended):
                return recommended[index]
        except ValueError:
            pass

    custom = input("Enter species: ").strip()
    return custom if custom else "Human"


def prompt_level() -> int:
    """Prompt for character level.

    Returns:
        Level between 1 and 20.
    """
    while True:
        raw = input("\nCharacter level (1-20) [1]: ").strip()
        if not raw:
            return 1
        try:
            level = int(raw)
            if 1 <= level <= 20:
                return level
            print("[ERROR] Level must be between 1 and 20.")
        except ValueError:
            print("[ERROR] Enter a valid number.")


def prompt_background(template: Dict[str, Any]) -> str:
    """Prompt for character background.

    Args:
        template: Loaded class template.

    Returns:
        Selected or entered background name.
    """
    recommended = template.get("recommended_backgrounds", [])
    if recommended:
        print("\nRecommended backgrounds for this class:")
        for idx, bg in enumerate(recommended, 1):
            print(f"  {idx}. {bg}")
        print(f"  {len(recommended) + 1}. Enter custom background")

        choice = input("Select background (number): ").strip()
        try:
            index = int(choice) - 1
            if 0 <= index < len(recommended):
                return recommended[index]
        except ValueError:
            pass

    custom = input("Enter background: ").strip()
    return custom if custom else ""


def prompt_subclass(template: Dict[str, Any], level: int) -> Optional[str]:
    """Prompt for subclass if the character level qualifies.

    Args:
        template: Loaded class template.
        level: Character level.

    Returns:
        Selected subclass name or None.
    """
    subclass_info = template.get("subclass_options", {})
    subclass_level = subclass_info.get("level", 3)
    if level < subclass_level:
        return None

    options = subclass_info.get("options", [])
    if not options:
        return None

    print(f"\nSubclass options (available at level {subclass_level}):")
    for idx, option in enumerate(options, 1):
        print(f"  {idx}. {option}")
    print(f"  {len(options) + 1}. Enter custom subclass")
    print("  0. Skip (choose later)")

    choice = input("Select subclass (number): ").strip()
    if choice == "0":
        return None
    try:
        index = int(choice) - 1
        if 0 <= index < len(options):
            return options[index]
    except ValueError:
        pass

    custom = input("Enter subclass name: ").strip()
    return custom if custom else None


def prompt_ability_scores(template: Dict[str, Any]) -> Dict[str, int]:
    """Prompt for ability score method and return the final scores.

    Args:
        template: Loaded class template.

    Returns:
        Ability scores dictionary.
    """
    base_scores = template.get("base_ability_scores", {})
    print("\nAbility scores:")
    print("  1. Use recommended scores (standard array, class-optimised)")
    print("  2. Enter custom scores")

    choice = input("Select option [1]: ").strip() or "1"
    if choice == "2":
        return _enter_custom_ability_scores()
    return dict(base_scores)


def _enter_custom_ability_scores() -> Dict[str, int]:
    """Prompt user to enter each ability score manually.

    Returns:
        Ability scores dictionary with user-provided values.
    """
    abilities = [
        "strength", "dexterity", "constitution",
        "intelligence", "wisdom", "charisma",
    ]
    scores: Dict[str, int] = {}
    print("\nEnter each ability score (press Enter for default 10):")
    for ability in abilities:
        while True:
            raw = input(f"  {ability.capitalize()} [10]: ").strip() or "10"
            try:
                value = int(raw)
                if 1 <= value <= 30:
                    scores[ability] = value
                    break
                print("[ERROR] Score must be between 1 and 30.")
            except ValueError:
                print("[ERROR] Enter a valid number.")
    return scores


def prompt_skills(template: Dict[str, Any]) -> List[str]:
    """Prompt for skill proficiency selection.

    Args:
        template: Loaded class template.

    Returns:
        List of selected skill names.
    """
    skill_options = template.get("skill_options", {})
    available = skill_options.get("from", [])
    choose_count = skill_options.get("choose", 2)

    if not available:
        return []

    print(f"\nChoose {choose_count} skill proficiencies:")
    for idx, skill in enumerate(available, 1):
        print(f"  {idx}. {skill}")

    selected: List[str] = []
    while len(selected) < choose_count:
        remaining = choose_count - len(selected)
        raw = input(
            f"Select skill {len(selected) + 1}/{choose_count} "
            f"(number, {remaining} remaining): "
        ).strip()
        try:
            index = int(raw) - 1
            if 0 <= index < len(available):
                skill = available[index]
                if skill not in selected:
                    selected.append(skill)
                else:
                    print("[ERROR] Skill already selected.")
            else:
                print(f"[ERROR] Choose a number between 1 and {len(available)}.")
        except ValueError:
            print("[ERROR] Enter a valid number.")

    return selected


def build_options_from_prompts(template: Dict[str, Any]) -> Optional[TemplateOptions]:
    """Run all wizard prompts and return a TemplateOptions instance.

    Returns None if the user cancels at any step.

    Args:
        template: Loaded class template.

    Returns:
        Populated TemplateOptions or None if cancelled.
    """
    char_name = prompt_character_name()
    if not char_name:
        return None

    race = prompt_race(template)
    level = prompt_level()
    background = prompt_background(template)
    subclass = prompt_subclass(template, level)
    ability_scores = prompt_ability_scores(template)
    skills = prompt_skills(template)

    return TemplateOptions(
        name=char_name,
        race=race,
        level=level,
        background=background,
        subclass=subclass,
        ability_scores=ability_scores,
        skills=skills,
    )


def print_character_summary(template: Dict[str, Any], options: TemplateOptions) -> None:
    """Display a formatted summary of the character to be created.

    Args:
        template: Loaded class template.
        options: The options gathered from the wizard prompts.
    """
    print("\n" + "=" * 50)
    print("CHARACTER SUMMARY")
    print("=" * 50)
    print(f"Name:       {options.name}")
    print(f"Class:      {template.get('class', '')}")
    print(f"Species:    {options.race}")
    print(f"Level:      {options.level}")
    print(f"Background: {options.background or '(none)'}")
    if options.subclass:
        print(f"Subclass:   {options.subclass}")
    print(f"Skills:     {', '.join(options.skills) if options.skills else '(none)'}")
    scores = options.ability_scores or template.get("base_ability_scores", {})
    print("Ability Scores:")
    for ability, score in scores.items():
        print(f"  {ability.capitalize():14}: {score}")
    print("=" * 50)
