# Terminal Display and File Viewing Features

This document describes the terminal display enhancements for viewing story files, markdown, and JSON files with rich formatting in the D&D Character Consultant System.

## Overview

The system now supports beautiful, formatted terminal output for viewing various file types:

- **Markdown files** - Story files, documentation with syntax highlighting and formatting
- **JSON files** - Character profiles, configurations with syntax highlighting
- **Text files** - Any text file with optional code syntax highlighting
- **Rich formatting** - Colors, panels, tables, and other visual enhancements

## Features

### 1. EditorConfig

An `.editorconfig` file has been added to the project root to ensure consistent code formatting across different editors and IDEs, particularly optimizing Markdown readability:

- **Markdown files** are configured for 88-character line length (Black's default) for balanced readability
- **Python files** are configured for 100-character line length with 4-space indentation
- **JSON/YAML** files use 2-space indentation for readability

VS Code users should install the [EditorConfig extension](https://marketplace.visualstudio.com/items?itemName=EditorConfig.EditorConfig) to support these settings.

### 2. Rich Library Integration

The `rich` library has been added to `requirements.txt` for beautiful terminal output. Install it with:

```bash
pip install -r requirements.txt
```

### 3. Terminal Display Module

A new utility module `src/utils/terminal_display.py` provides functions for rendering files with rich formatting.

#### Available Functions

##### Display Markdown Files
```python
from src.utils.terminal_display import display_markdown_file

# Display a story or markdown file
display_markdown_file("game_data/campaigns/Example_Campaign/1_opening.md")

# With optional title
display_markdown_file("path/to/file.md", title="My Story")
```

Features:
- Renders markdown formatting (headers, bold, italics, lists, code blocks)
- Colored title with cyan styling
- Automatic fallback to plain text if `rich` is unavailable

##### Display Story Files
```python
from src.utils.terminal_display import display_story_file

# Display a story with story-specific formatting
display_story_file("game_data/campaigns/Example_Campaign/1_opening.md")

# With optional story name
display_story_file("path/to/story.md", story_name="The Beginning")
```

Features:
- Same as markdown display, with green styling for story titles
- Better visual separation for narrative content

##### Display JSON Files
```python
from src.utils.terminal_display import display_json_file

# Display a character profile with syntax highlighting
display_json_file("game_data/characters/aragorn.json")

# With optional title
display_json_file("path/to/file.json", title="Character Profile")
```

Features:
- JSON syntax highlighting with "dracula" theme
- Blue styling for titles
- Automatic indentation and formatting

##### Display Text Files
```python
from src.utils.terminal_display import display_text_file

# Plain text file
display_text_file("path/to/file.txt")

# With syntax highlighting (python, bash, yaml, etc.)
display_text_file("path/to/script.py", syntax_highlight="python")

# With title
display_text_file("path/to/file.sh", title="Setup Script", 
                  syntax_highlight="bash")
```

Features:
- Optional syntax highlighting for code files
- Line numbers for code display
- Yellow styling for titles

##### Display Panels
```python
from src.utils.terminal_display import display_panel

# Display important information in a styled panel
display_panel("This is important information", 
              title="Important Notice", 
              style="cyan")
```

Supports colors: `cyan`, `green`, `blue`, `red`, `yellow`, `magenta`

##### Helper Functions
```python
from src.utils.terminal_display import (
    print_error,
    print_success,
    print_info,
    print_warning
)

print_error("Something went wrong!")
print_success("Operation completed!")
print_info("Processing...")
print_warning("Be careful!")
```

## Usage Examples

### Command-Line Script

Use the provided `display_story.py` script to view files from the terminal:

```bash
# View a story file with rich formatting
python display_story.py game_data/campaigns/Example_Campaign/1_opening.md

# View a character profile
python display_story.py game_data/characters/aragorn.json

# View any markdown file
python display_story.py docs/docs_personal/COPILOT_CONTEXT.md
```

### Interactive CLI

When viewing stories through the CLI menu (`"2. View Story Details"`), you'll be prompted:

```
View with rich formatting? (y/n):
```

Select `y` to display the story with rich formatting and colors.

### Integration in Custom Scripts

```python
from src.utils.terminal_display import display_markdown_file, print_info

print_info("Loading story analysis...")
display_markdown_file("game_data/campaigns/Example_Campaign/analysis.md")
```

## Graceful Fallback

All functions gracefully fall back to plain text display if the `rich` library is unavailable. This ensures the system works even without the optional dependency, though with reduced visual appeal.

## Configuration

### Theme
The syntax highlighting theme is set to "dracula" for pleasant colors and readability. To change it, modify `src/utils/terminal_display.py`:

```python
syntax = Syntax(content, "json", theme="monokai", line_numbers=False)
```

Available themes: `dracula`, `monokai`, `native`, `vim`, `emacs`, etc.

### Line Length
Markdown files are configured for 88-character lines in `.editorconfig`. Adjust in the `.editorconfig` file if needed:

```ini
[*.md]
max_line_length = 88
```

## Technical Details

### No External Dependencies Beyond Rich
- The `rich` library is the only new external dependency added
- All other functionality uses Python standard library
- Graceful degradation if `rich` is not installed

### Pylint Compliance
All new code maintains 10.00/10 Pylint score:
- No disable comments or pragmas
- Proper error handling with try/except blocks
- Well-documented docstrings

### File Support
- **Markdown** (.md) - Full support with markdown rendering
- **JSON** (.json) - Syntax highlighted display
- **Python** (.py) - Syntax highlighted with line numbers
- **Shell** (.sh) - Syntax highlighted with line numbers
- **Text** (.txt) - Plain text or with syntax highlighting

## Future Enhancements

Potential improvements for consideration:

1. **Pagination** - Add pagination for very long files
2. **Search** - Add search/filter capability for large files
3. **Side-by-side comparison** - Compare two files side-by-side
4. **Table rendering** - Enhanced markdown table display
5. **Interactive navigation** - Jump to specific sections
6. **Export** - Export formatted output to HTML/PDF

## Related Documentation

- [Project README](../../README.md)
- [D&D Consultant Instructions](../../.github/copilot-instructions.md)
- [Story Creation Flow](./STORY_CONTINUATION.md)
