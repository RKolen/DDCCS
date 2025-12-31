"""
ASCII Art Character Display Module

Provides ASCII art rendering for D&D characters using rich library.
Supports custom ASCII art from character JSON or generates default frames.
Can optionally generate AI-based ASCII art from character backstory.
"""

from typing import Optional, Dict, Any

from src.utils.optional_imports import (
    RICH_AVAILABLE,
    get_rich_console,
    get_rich_component,
)

# Get rich components
Panel = get_rich_component("Panel")
Align = get_rich_component("Align")
Text = get_rich_component("Text")
Columns = get_rich_component("Columns")

# Lazy import for AI to avoid circular dependencies
try:
    from src.ai.availability import AI_AVAILABLE
    from src.ai.ai_client import AIClient
except ImportError:
    AI_AVAILABLE = False
    AIClient = None

console = get_rich_console()


def get_class_icon(dnd_class: str) -> str:
    """Get ASCII icon for D&D class.

    Args:
        dnd_class: Character class name

    Returns:
        ASCII representation of class icon
    """
    icons = {
        "barbarian": "[X]",
        "bard": "[~]",
        "cleric": "[+]",
        "druid": "[*]",
        "fighter": "[#]",
        "monk": "[@]",
        "paladin": "[^]",
        "ranger": "[>]",
        "rogue": "[/]",
        "sorcerer": "[%]",
        "warlock": "[&]",
        "wizard": "[?]",
    }
    return icons.get(dnd_class.lower(), "[?]")


def create_character_portrait(
    character_name: str,
    dnd_class: str,
    level: int,
    *,
    custom_art: Optional[str] = None,
    backstory: Optional[str] = None,
    **options,
) -> str:
    """Create ASCII portrait for character.

    Args:
        character_name: Name of the character
        dnd_class: Character class
        level: Character level
        custom_art: Optional custom ASCII art string (takes priority)
        backstory: Character backstory for AI generation
        **options: Additional options (generate_from_backstory: bool)

    Returns:
        Formatted ASCII art portrait
    """
    generate_from_backstory = options.get("generate_from_backstory", False)

    if custom_art:
        return custom_art

    # Try to generate from backstory if requested and available
    if generate_from_backstory and backstory and AI_AVAILABLE:
        ai_art = _generate_ascii_from_backstory(character_name, dnd_class, backstory)
        if ai_art:
            return ai_art

    # Default portrait with class icon
    icon = get_class_icon(dnd_class)
    lines = [
        "     _____ ",
        f"    {icon:^5} ",
        "    |   | ",
        "   _|   |_ ",
        "  |       |",
        "  |_______|",
        "",
        f" {character_name[:11]:^11}",
        f" {dnd_class[:11]:^11}",
        f"  Level {level:>2}",
    ]
    return "\n".join(lines)


def _generate_ascii_from_backstory(
    character_name: str, dnd_class: str, backstory: str
) -> Optional[str]:
    """Generate ASCII art from character backstory using AI.

    Args:
        character_name: Character name
        dnd_class: Character class
        backstory: Character backstory

    Returns:
        Generated ASCII art or None if generation fails
    """
    if not AI_AVAILABLE or not AIClient:
        return None

    try:
        client = AIClient()
        prompt = f"""Generate a simple ASCII art portrait (max 10 lines, max 40 chars wide)
representing this D&D character. Focus on a key visual element from their backstory.
Use only basic ASCII characters. Keep it simple and recognizable.

Character: {character_name}
Class: {dnd_class}
Backstory: {backstory[:300]}...

Generate ONLY the ASCII art, no explanation or markdown formatting."""

        messages = [
            client.create_system_message(
                "You are an ASCII art generator. Create simple, clean ASCII art."
            ),
            client.create_user_message(prompt),
        ]

        response = client.chat_completion(messages, temperature=0.8, max_tokens=500)

        if response and len(response.strip().split("\n")) <= 15:
            return response.strip()
        return None
    except (RuntimeError, AttributeError):
        return None


def display_character_portrait(
    character_name: str,
    dnd_class: str,
    level: int,
    *,
    custom_art: Optional[str] = None,
    **options,
) -> None:
    """Display character portrait in terminal.

    Args:
        character_name: Name of the character
        dnd_class: Character class
        level: Character level
        custom_art: Optional custom ASCII art
        **options: Additional options (backstory, generate_from_backstory, style)
    """
    style = options.get("style", "cyan")
    backstory = options.get("backstory")
    generate_from_backstory = options.get("generate_from_backstory", False)

    if not RICH_AVAILABLE:
        # Fallback: plain text display
        art = create_character_portrait(
            character_name,
            dnd_class,
            level,
            custom_art=custom_art,
            backstory=backstory,
            generate_from_backstory=generate_from_backstory,
        )
        print("\n" + "=" * 40)
        print(art)
        print("=" * 40 + "\n")
        return

    art = create_character_portrait(
        character_name,
        dnd_class,
        level,
        custom_art=custom_art,
        backstory=backstory,
        generate_from_backstory=generate_from_backstory,
    )
    panel = Panel(
        Align.center(Text(art, style=style)),
        title=f"[bold {style}]Character Portrait[/bold {style}]",
        border_style=style,
        padding=(1, 2),
    )
    console.print(panel)


def display_party_portraits(characters: list[Dict[str, Any]]) -> None:
    """Display multiple character portraits in a grid.

    Args:
        characters: List of character dicts with name, dnd_class, level fields
    """
    if not RICH_AVAILABLE or not Columns:
        # Fallback: display one by one
        for char in characters:
            art = create_character_portrait(
                char.get("name", "Unknown"),
                char.get("dnd_class", "unknown"),
                char.get("level", 1),
                custom_art=char.get("ascii_art"),
            )
            print("\n" + art + "\n")
        return

    panels = []
    for char in characters:
        art = create_character_portrait(
            char.get("name", "Unknown"),
            char.get("dnd_class", "unknown"),
            char.get("level", 1),
            custom_art=char.get("ascii_art"),
        )
        panel = Panel(
            Align.center(Text(art, style="cyan")),
            title=char.get("name", "Unknown"),
            border_style="cyan",
        )
        panels.append(panel)

    console.print(Columns(panels, equal=True, expand=True))


def get_default_ascii_templates() -> Dict[str, str]:
    """Get default ASCII art templates for each class.

    Returns:
        Dictionary mapping class names to default ASCII art
    """
    templates = {
        "barbarian": """
     _____
    [X]
    |   |
   _|   |_
  | \\_/ |
  |_____|
""",
        "wizard": """
     _____
    [?]
    |   |
   _| ^ |_
  | /_\\ |
  |_____|
""",
        "fighter": """
     _____
    [#]
    |   |
   _|   |_
  | |_| |
  |_____|
""",
        "cleric": """
     _____
    [+]
    |   |
   _|   |_
  |  +  |
  |_____|
""",
    }
    return templates


def display_ascii_banner(text: str, style: str = "bold green") -> None:
    """Display ASCII banner with text.

    Args:
        text: Text to display in banner
        style: Rich style for the text
    """
    if not RICH_AVAILABLE:
        print("\n" + "=" * 60)
        print(f"  {text}")
        print("=" * 60 + "\n")
        return

    banner_panel = Panel(
        Align.center(Text(text, style=style)), border_style="green", padding=(0, 2)
    )
    console.print(banner_panel)
