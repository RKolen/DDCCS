# Quick Start: Terminal Display Features

The D&D Consultant System now supports beautiful terminal display for viewing stories, characters, and documentation with colors and formatting.

## Installation

Already included in `requirements.txt`. Just ensure you have it installed:

```bash
pip install -r requirements.txt
```

This installs the `rich` library (v13.0+) for terminal formatting.

## Quick Usage

### View Any File

```bash
# View a story file
python display_story.py game_data/campaigns/Example_Campaign/001_opening.md

# View a character profile
python display_story.py game_data/characters/aragorn.json

# View documentation
python display_story.py README.md
python display_story.py docs/AI_INTEGRATION.md
```

### View Story by Campaign + Number

```bash
# View story 1 from Example_Campaign
python display_story.py Example_Campaign 1

# View story 3
python display_story.py Your_Campaign 3

# System supports:
# - Example_Campaign/001_story.md
# - Example_Campaign_Quest/01_story.md  
# - etc.
```

### Interactive CLI

When viewing stories through the main menu:

```
Choose: 2 (Manage Stories)
Choose: 2 (Work with Story Series)
Select your campaign
Choose: 2 (View Story Details)
Select a story
View with rich formatting? (y/n): y  ← Press 'y' for colors!
```

## Features

* **Markdown Rendering** - Proper formatting for headers, bold, italics, lists, code blocks  
* **JSON Syntax Highlighting** - Color-coded JSON with dracula theme  
* **Code Highlighting** - Python, Bash, YAML support  
* **Colored Output** - Error (red), Success (green), Info (cyan), Warning (yellow)  
* **Graceful Fallback** - Works even if rich library is unavailable

## Examples

### Viewing a Story

```bash
$ python display_story.py Example_Campaign 1

───────────────────────── 001_opening.md ──────────────────────────
# The Tavern Meeting

The adventurers gather in the Prancing Pony...
(full story displays with markdown formatting)
```

### Viewing a Character

```bash
$ python display_story.py game_data/characters/aragorn.json

────────────────────────── aragorn.json ────────────────────────────
{
  "name": "Aragorn",
  "dnd_class": "Ranger",
  "level": 10,
  ...
}
(JSON displays with syntax highlighting)
```

## Integration in Code

Use in your own Python scripts:

```python
from src.utils.terminal_display import display_story_file, print_info

print_info("Loading your story...")
display_story_file("game_data/campaigns/Example_Campaign/001_opening.md")

# Or display any file
from src.utils.terminal_display import display_any_file
display_any_file("game_data/characters/aragorn.json")
```

## Editor Configuration

The `.editorconfig` file optimizes editors for your project:

- **Markdown files**: 88-character lines (optimal for terminal)
- **Python files**: 100-character lines, 4-space indentation
- **JSON files**: 2-space indentation

**For VS Code:** Install [EditorConfig extension](https://marketplace.visualstudio.com/items?itemName=EditorConfig.EditorConfig)

## Colors and Styling

Available in your own code:

```python
from src.utils.terminal_display import (
    print_error,      # Red text
    print_success,    # Green text
    print_info,       # Cyan text
    print_warning,    # Yellow text
    display_panel,    # Styled box
)

print_success("Campaign created successfully!")
print_error("File not found!")
print_warning("This action cannot be undone")
print_info("Processing... please wait")

display_panel("Important Information", "Be Careful!", style="red")
```

## Troubleshooting

**Colors not showing?**
- Windows PowerShell: Use Windows Terminal (recommended)
- Or run: `chcp 65001` before starting Python

**Rich module not found?**
```bash
pip install rich
```

**Need plain text display?**
- Files display as plain text if rich is unavailable
- No errors, just less pretty

## Related Documentation

- **Full Features**: [docs/TERMINAL_DISPLAY.md](../TERMINAL_DISPLAY.md)
- **Implementation Details**: [docs/docs_personal/TERMINAL_DISPLAY_IMPLEMENTATION.md](TERMINAL_DISPLAY_IMPLEMENTATION.md)
- **API Reference**: [src/utils/terminal_display.py](../../src/utils/terminal_display.py)

## Pro Tips

1. **Create an alias** (PowerShell):
   ```powershell
   function Read-Story { python display_story.py $args }
   ```
   Then: `Read-Story Example_Campaign 1`

2. **View recent changes**:
   ```bash
   python display_story.py docs/TODO.md
   ```

3. **Quick character lookup**:
   ```bash
   python display_story.py game_data/characters/aragorn.json
   ```

4. **Read documentation**:
   ```bash
   python display_story.py README.md
   python display_story.py docs/AI_INTEGRATION.md
   ```

## What's Next?

- Explore the [full terminal display documentation](../TERMINAL_DISPLAY.md)
- Read the [implementation details](TERMINAL_DISPLAY_IMPLEMENTATION.md)
- Check out [display_file.py](../../src/utils/display_file.py) for more options

Happy storytelling!
