"""
Rich Terminal Formatting Utilities

Provides rich text formatting for markdown and story files
displayed in the terminal, making them more readable with
colors, formatting, and structured layout.
"""

import os
from typing import Optional

from src.utils.optional_imports import (
    RICH_AVAILABLE,
    get_rich_console,
    get_rich_component,
)

# Get rich components
Markdown = get_rich_component("Markdown")
Panel = get_rich_component("Panel")
Syntax = get_rich_component("Syntax")

# Import TTS separately (not a Rich component)
try:
    from src.utils.tts_narrator import narrate_file, is_tts_available
except ImportError:
    narrate_file = None
    is_tts_available = None

# Initialize console for terminal output
console = get_rich_console()


def display_markdown_file(filepath: str, title: Optional[str] = None) -> None:
    """Display a markdown file with rich formatting in the terminal.

    Args:
        filepath: Path to the markdown file to display
        title: Optional title to display above the content
    """
    if not os.path.exists(filepath):
        if RICH_AVAILABLE:
            console.print(f"[red]Error: File not found: {filepath}[/red]")
        else:
            print(f"Error: File not found: {filepath}")
        return

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        if not RICH_AVAILABLE:
            # Fallback: plain text display
            filename = os.path.basename(filepath)
            display_title = title or filename
            print(f"\n{'='*60}")
            print(f"{display_title}")
            print(f"{'='*60}\n")
            print(content)
            return

        # Display with optional title
        if title:
            console.rule(f"[bold cyan]{title}[/bold cyan]", style="cyan")
        else:
            # Use filename as title if not provided
            filename = os.path.basename(filepath)
            console.rule(f"[bold cyan]{filename}[/bold cyan]", style="cyan")

        markdown = Markdown(content)
        console.print(markdown)

    except (OSError, UnicodeDecodeError) as e:
        if RICH_AVAILABLE:
            console.print(f"[red]Error reading file: {e}[/red]")
        else:
            print(f"Error reading file: {e}")


def _display_story_content(
    filepath: str, content: str, story_name: Optional[str]
) -> None:
    """Display story content with appropriate formatting.

    Args:
        filepath: Path to the story file
        content: Story content to display
        story_name: Optional custom name for the story
    """
    if not RICH_AVAILABLE:
        # Fallback: plain text display
        filename = os.path.basename(filepath)
        display_title = story_name or filename
        print(f"\n{'='*60}")
        print(f"{display_title}")
        print(f"{'='*60}\n")
        print(content)
    else:
        # Display with optional title
        if story_name:
            console.rule(f"[bold green]{story_name}[/bold green]", style="green")
        else:
            filename = os.path.basename(filepath)
            console.rule(f"[bold green]{filename}[/bold green]", style="green")

        # Display as markdown (story files are typically markdown)
        markdown = Markdown(content)
        console.print(markdown)


def _handle_narration(filepath: str) -> None:
    """Handle TTS narration of a file.

    Args:
        filepath: Path to file to narrate
    """
    if narrate_file and is_tts_available and is_tts_available():
        print("\n[INFO] Starting narration...")
        narrate_file(filepath)
    else:
        print_warning("TTS not available. Install pyttsx3 for narration support.")


def display_story_file(
    filepath: str, story_name: Optional[str] = None, narrate: bool = False
) -> None:
    """Display a story file with rich formatting.

    Stories are displayed with syntax highlighting for better
    readability in terminal.

    Args:
        filepath: Path to the story file to display
        story_name: Optional custom name for the story
        narrate: If True, narrate the story using TTS after displaying
    """
    if not os.path.exists(filepath):
        if RICH_AVAILABLE:
            console.print(f"[red]Error: File not found: {filepath}[/red]")
        else:
            print(f"Error: File not found: {filepath}")
        return

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        _display_story_content(filepath, content, story_name)

        # Narrate if requested
        if narrate:
            _handle_narration(filepath)

    except (OSError, UnicodeDecodeError) as e:
        if RICH_AVAILABLE:
            console.print(f"[red]Error reading file: {e}[/red]")
        else:
            print(f"Error reading file: {e}")


def display_json_file(filepath: str, title: Optional[str] = None) -> None:
    """Display a JSON file with syntax highlighting.

    Args:
        filepath: Path to the JSON file to display
        title: Optional title to display above the content
    """
    if not os.path.exists(filepath):
        if RICH_AVAILABLE:
            console.print(f"[red]Error: File not found: {filepath}[/red]")
        else:
            print(f"Error: File not found: {filepath}")
        return

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        if not RICH_AVAILABLE:
            # Fallback: plain text display
            filename = os.path.basename(filepath)
            display_title = title or filename
            print(f"\n{'='*60}")
            print(f"{display_title}")
            print(f"{'='*60}\n")
            print(content)
            return

        # Display with optional title
        if title:
            console.rule(f"[bold blue]{title}[/bold blue]", style="blue")
        else:
            filename = os.path.basename(filepath)
            console.rule(f"[bold blue]{filename}[/bold blue]", style="blue")

        syntax = Syntax(content, "json", theme="dracula", line_numbers=False)
        console.print(syntax)

    except (OSError, UnicodeDecodeError) as e:
        if RICH_AVAILABLE:
            console.print(f"[red]Error reading file: {e}[/red]")
        else:
            print(f"Error reading file: {e}")


def display_text_file(
    filepath: str, title: Optional[str] = None, syntax_highlight: Optional[str] = None
) -> None:
    """Display a text file with optional syntax highlighting.

    Args:
        filepath: Path to the text file to display
        title: Optional title to display above the content
        syntax_highlight: Optional language for syntax highlighting
                         (e.g., 'python', 'bash', 'yaml')
    """
    if not os.path.exists(filepath):
        if RICH_AVAILABLE:
            console.print(f"[red]Error: File not found: {filepath}[/red]")
        else:
            print(f"Error: File not found: {filepath}")
        return

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        if not RICH_AVAILABLE:
            # Fallback: plain text display
            filename = os.path.basename(filepath)
            display_title = title or filename
            print(f"\n{'='*60}")
            print(f"{display_title}")
            print(f"{'='*60}\n")
            print(content)
            return

        # Display with optional title
        if title:
            console.rule(f"[bold yellow]{title}[/bold yellow]", style="yellow")
        else:
            filename = os.path.basename(filepath)
            console.rule(f"[bold yellow]{filename}[/bold yellow]", style="yellow")

        if syntax_highlight:
            syntax = Syntax(
                content, syntax_highlight, theme="dracula", line_numbers=True
            )
            console.print(syntax)
        else:
            console.print(content)

    except (OSError, UnicodeDecodeError) as e:
        if RICH_AVAILABLE:
            console.print(f"[red]Error reading file: {e}[/red]")
        else:
            print(f"Error reading file: {e}")


def display_panel(content: str, title: str, style: str = "cyan") -> None:
    """Display content in a styled panel.

    Useful for displaying important information or status messages.

    Args:
        content: Text content to display
        title: Title for the panel
        style: Color/style for the panel border (cyan, green, blue, red, etc.)
    """
    if not RICH_AVAILABLE:
        # Fallback: simple text display
        print(f"\n{'*'*60}")
        print(f"{title}")
        print(f"{'*'*60}")
        print(content)
        print(f"{'*'*60}\n")
        return

    panel = Panel(content, title=title, style=style)
    console.print(panel)


def display_table_from_file(filepath: str, title: Optional[str] = None) -> None:
    """Display a markdown table from file with rich formatting.

    Args:
        filepath: Path to file containing markdown table
        title: Optional title for the display
    """
    if not os.path.exists(filepath):
        if RICH_AVAILABLE:
            console.print(f"[red]Error: File not found: {filepath}[/red]")
        else:
            print(f"Error: File not found: {filepath}")
        return

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        if not RICH_AVAILABLE:
            # Fallback: plain text display
            if title:
                print(f"\n{'='*60}")
                print(f"{title}")
                print(f"{'='*60}\n")
            print(content)
            return

        if title:
            console.rule(f"[bold magenta]{title}[/bold magenta]", style="magenta")

        markdown = Markdown(content)
        console.print(markdown)

    except (OSError, UnicodeDecodeError) as e:
        if RICH_AVAILABLE:
            console.print(f"[red]Error reading file: {e}[/red]")
        else:
            print(f"Error reading file: {e}")


def display_any_file(filepath: str) -> None:
    """Display any file based on its type with appropriate formatting.

    Automatically detects file type and applies suitable rendering:
    - JSON files: Syntax highlighted
    - Markdown files: Rendered markdown
    - Text files: Plain text display

    Args:
        filepath: Path to file to display
    """
    if not os.path.exists(filepath):
        if RICH_AVAILABLE:
            console.print(f"[red]Error: File not found: {filepath}[/red]")
        else:
            print(f"Error: File not found: {filepath}")
        return

    # Determine file type and display accordingly
    if filepath.endswith(".json"):
        display_json_file(filepath)
    elif filepath.endswith(".md"):
        # Auto-detect story vs markdown based on path
        if "campaign" in filepath.lower() or "story" in filepath.lower():
            display_story_file(filepath)
        else:
            display_markdown_file(filepath)
    else:
        # Default to plain text display
        display_text_file(filepath)


def print_error(message: str) -> None:
    """Print an error message with red styling."""
    if RICH_AVAILABLE:
        console.print(f"[red]{message}[/red]")
    else:
        print(f"ERROR: {message}")


def print_success(message: str) -> None:
    """Print a success message with green styling."""
    if RICH_AVAILABLE:
        console.print(f"[green]{message}[/green]")
    else:
        print(f"SUCCESS: {message}")


def print_info(message: str) -> None:
    """Print an info message with cyan styling."""
    if RICH_AVAILABLE:
        console.print(f"[cyan]{message}[/cyan]")
    else:
        print(f"INFO: {message}")


def print_warning(message: str) -> None:
    """Print a warning message with yellow styling."""
    if RICH_AVAILABLE:
        console.print(f"[yellow]{message}[/yellow]")
    else:
        print(f"WARNING: {message}")
