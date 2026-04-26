"""Name and path completion helpers for the CLI.

Provides functions that return sorted lists of available character, NPC,
campaign, and story file names. These lists can be used wherever the CLI
needs to display selectable options or validate user input.
"""

from pathlib import Path
from typing import List

from src.utils.path_utils import get_characters_dir, get_game_data_path, get_npcs_dir


def get_character_names(prefix: str = "") -> List[str]:
    """Return character names, optionally filtered by a prefix.

    Args:
        prefix: Case-insensitive prefix filter. Returns all names when empty.

    Returns:
        Sorted list of matching character names (JSON file stems).
    """
    characters_dir = Path(get_characters_dir())
    names: List[str] = []
    if characters_dir.exists():
        for char_file in characters_dir.glob("*.json"):
            if not char_file.name.startswith("."):
                name = char_file.stem
                if not prefix or name.lower().startswith(prefix.lower()):
                    names.append(name)
    return sorted(names)


def get_npc_names(prefix: str = "") -> List[str]:
    """Return NPC names, optionally filtered by a prefix.

    Args:
        prefix: Case-insensitive prefix filter. Returns all names when empty.

    Returns:
        Sorted list of matching NPC names (JSON file stems).
    """
    npcs_dir = Path(get_npcs_dir())
    names: List[str] = []
    if npcs_dir.exists():
        for npc_file in npcs_dir.glob("*.json"):
            if not npc_file.name.startswith("."):
                name = npc_file.stem
                if not prefix or name.lower().startswith(prefix.lower()):
                    names.append(name)
    return sorted(names)


def get_campaign_names(prefix: str = "") -> List[str]:
    """Return campaign folder names, optionally filtered by a prefix.

    Args:
        prefix: Case-insensitive prefix filter. Returns all names when empty.

    Returns:
        Sorted list of matching campaign directory names.
    """
    campaigns_dir = Path(get_game_data_path()) / "campaigns"
    names: List[str] = []
    if campaigns_dir.exists():
        for campaign_dir in campaigns_dir.iterdir():
            if campaign_dir.is_dir():
                name = campaign_dir.name
                if not prefix or name.lower().startswith(prefix.lower()):
                    names.append(name)
    return sorted(names)


def get_story_files(campaign_name: str, prefix: str = "") -> List[str]:
    """Return story file names within a campaign, optionally filtered by prefix.

    Args:
        campaign_name: Campaign folder name.
        prefix: Case-insensitive prefix filter. Returns all files when empty.

    Returns:
        Sorted list of matching story file names (with .md extension).
    """
    campaign_dir: Path = Path(get_game_data_path()) / "campaigns" / campaign_name
    files: List[str] = []
    if campaign_dir.exists():
        for story_file in campaign_dir.glob("*.md"):
            name = story_file.name
            if not prefix or name.lower().startswith(prefix.lower()):
                files.append(name)
    return sorted(files)


def print_completion_instructions() -> None:
    """Print instructions for enabling shell tab completion."""
    print(
        "\nShell Completion Setup"
        "\n======================"
        "\n"
        "\nTo enable tab completion for the CLI entry point add one of the"
        "\nfollowing to your shell configuration file and then restart your shell:"
        "\n"
        "\nBash (~/.bashrc):"
        '\n    eval "$(_DND_CONSULTANT_COMPLETE=bash_source dnd-consultant)"'
        "\n"
        "\nZsh (~/.zshrc):"
        '\n    eval "$(_DND_CONSULTANT_COMPLETE=zsh_source dnd-consultant)"'
        "\n"
        "\nFish (~/.config/fish/config.fish):"
        "\n    _DND_CONSULTANT_COMPLETE=fish_source dnd-consultant | source"
        "\n"
    )
