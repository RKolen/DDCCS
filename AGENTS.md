# AGENTS.md

## Project Overview

This is a D&D Character Consultant System - a Python application for managing
Dungeons & Dragons characters, NPCs, stories, and campaign sessions. The system
provides AI-powered consultation, story analysis, combat narration, and
character development tracking.

Key features:

- Character profile management with class-specific knowledge
- NPC auto-detection and management
- Story continuation and analysis with RAG integration
- Combat narration system
- Custom items registry
- JSON validation for all data types

## Critical Rules (Non-Negotiable)

### 1. NO Emojis - NEVER

Never use emojis in `.py` or `.md` files. This causes Windows cp1252 codec
failures that break the entire system. This is a hard requirement.

### 2. Pylint Score: 10.00/10 Required

All code must achieve a perfect 10.00/10 Pylint score. Never use:

- `# pylint: disable=...`
- `# noqa`
- `# pragma` comments

Instead, fix the underlying issue. If Pylint complains, there is usually a
legitimate code quality issue to address.

- never edit `pyproject.toml`

### 3. Full Pylint Output for Big Changes

For significant changes, always run the full Pylint checks:

```bash
python -m pylint src/ tests/
```

Never use flags or pipes.
No issue is acceptable even if score is 10/10.

### 4. No Hardcoded Configuration Values

Never hardcode values that should be configurable. This includes:

- API keys, base URLs, or model names for AI services
- Wiki URLs for RAG system
- Default themes or display settings
- Any value that users should be able to configure

Instead, use the centralized configuration system in `src/config/`:

```python
# Wrong - hardcoded value
model: str = "gpt-3.5-turbo"

# Correct - use empty string, configure via config file or env
model: str = ""
```

The configuration system supports defaults through config files or environment
variables. See `src/config/config_types.py` for the configuration schema.

## Before Writing Code - MANDATORY CHECK

**STOP!** Before writing ANY new utility code, check the utils catalog below.
This project has extensive shared utilities. Duplicating existing code is a
violation of project standards.

### Reusable Utils Catalog

| Category | Module | Key Functions |
| -------- | ------ | ------------- |
| File I/O | `src/utils/file_io.py` | `load_json_file`, `save_json_file`, |
| | | `read_text_file`, `write_text_file`, |
| | | `file_exists`, `ensure_directory` |
| Paths | `src/utils/path_utils.py` | `get_characters_dir`, `get_campaign_path`, |
| | | `get_story_file_path`, `get_game_data_path`, |
| | | `get_npcs_dir` |
| Strings | `src/utils/string_utils.py` | `sanitize_filename`, `normalize_name`, |
| | | `slugify`, `truncate_text`, `get_session_date`, |
| | | `get_timestamp` |
| Validation | `src/utils/validation_helpers.py` | `validate_required_fields`, |
| | | `validate_field_type`, `validate_list_field`, |
| | | `format_validation_errors` |
| CLI | `src/utils/cli_utils.py` | `display_selection_menu`, `confirm_action`, |
| | | `select_from_list`, `print_section_header` |
| Display | `src/utils/terminal_display.py` | `display_markdown_file`, `display_story_file`, |
| | | `print_error`, `print_success`, `print_info`, |
| | | `print_warning`, `display_panel` |
| Characters | `src/utils/character_profile_utils.py` | `load_character_profile`, |
| | | `load_character_traits`, `find_character_file`, |
| | | `list_character_names` |
| D&D Rules | `src/utils/dnd_rules.py` | `get_dc_for_difficulty`, |
| | | `calculate_modifier`, `get_proficiency_bonus`, |
| | | `DC_EASY`, `DC_MEDIUM`, `DC_HARD` constants |
| Spells | `src/utils/spell_highlighter.py` | `highlight_spells_in_text`, |
| | | `extract_spells_from_prompt`, |
| | | `extract_known_spells_from_characters` |
| NPCs | `src/utils/npc_lookup_helper.py` | `load_relevant_npcs_for_prompt`, |
| | | `match_npc_to_location`, `extract_location_keywords` |
| Stories | `src/utils/story_file_helpers.py` | `list_story_files`, |
| | | `next_filename_for_dir`, |
| | | `has_numbered_story_files` |
| Markdown | `src/utils/markdown_utils.py` | `update_markdown_section`, |
| | | `extract_markdown_section` |
| TTS | `src/utils/tts_narrator.py` | `narrate_file`, `narrate_text`, |
| | | `clean_text_for_narration` |
| Cache | `src/utils/cache_utils.py` | `clear_character_from_cache`, |
| | | `reload_character_from_disk` |
| Behavior | `src/utils/behaviour_generation.py` | `generate_behavior_from_personality` |

## Project Structure

### Source Code Organization

src/
|-- characters/      # Character management + consultants subsystem
|-- npcs/            # NPC management and auto-detection
|-- stories/         # Story management and analysis
|-- combat/          # Combat narration system
|-- items/           # Custom items registry
|-- dm/              # Dungeon Master tools
|-- validation/      # JSON validation for all data types
|-- ai/              # AI client and RAG system
|-- utils/           # Shared utilities (CHECK FIRST)
|-- cli/             # Command-line interface

### Data Directories

game_data/
|-- characters/      # Character JSON files (aragorn.json, frodo.json, etc.)
|-- campaigns/       # Campaign folders with story files
|-- npcs/            # NPC JSON files
|-- items/           # Custom items registry

### Test Structure

Tests mirror the `src/` directory structure:

tests/
|-- ai/              # Tests for src/ai/
|-- characters/      # Tests for src/characters/
|-- cli/             # Tests for src/cli/
|-- stories/         # Tests for src/stories/
|-- utils/           # Tests for src/utils/
|-- validation/      # Tests for src/validation/
|-- run_all_tests.py # Main test runner

### Drupal CMS

The project includes a Drupal CMS recipe system in `drupal-cms/`. This is a
separate component that requires Docker and DDEV for local development.

**Important:** Any changes to the Drupal CMS components require DDEV to be
running. Before making changes to files in `drupal-cms/`, ensure the DDEV
environment is started:

```bash
# Start DDEV
ddev start

# After making changes, you may need to rebuild
ddev rebuild
```

The Drupal CMS uses its own testing and validation - do not apply the
standard Python/Pylint rules to the Drupal PHP code.

### Drupal Contrib Patch Policy

If changes are needed in `drupal-cms/web/modules/contrib/`, do not leave
direct edits as the only implementation.

Required process:

1. Create a patch file in `drupal-cms/patches/`.
2. Register the patch in `drupal-cms/composer.json` under `extra.patches`.
3. Enable and use Composer patch tooling so the fix reapplies after updates.

This keeps contrib upgrades reproducible and prevents local hotfixes from
being lost on reinstall/update.

## Coding Standards

### Import Conventions

Always use absolute imports from the `src` package:

```python
# Correct - absolute imports
from src.characters.consultants.character_profile import CharacterProfile
from src.stories.story_manager import StoryManager
from src.utils.file_io import load_json_file
from src.utils.path_utils import get_characters_dir

# Incorrect - relative imports
from .character_profile import CharacterProfile
from ..utils.file_io import load_json_file
```

### Code Style (from .editorconfig)

**Python files:**

- 4-space indentation
- 100 maximum line length
- UTF-8 encoding
- LF line endings

**Markdown files:**

- 2-space indentation
- 80 maximum line length (terminal readability)
- Trim trailing whitespace

**JSON files:**

- 2-space indentation

### Docstrings

Use Google-style docstrings:

```python
def load_character_profile(character_name: str) -> dict:
    """Load a character profile from the game_data directory.

    Args:
        character_name: The name of the character to load.

    Returns:
        A dictionary containing the character profile data.

    Raises:
        FileNotFoundError: If the character file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
```

### Type Hints

Always include type hints for function parameters and return values:

```python
def get_campaign_path(campaign_name: str) -> Path:
    """Get the path to a campaign directory."""
    return get_game_data_path() / "campaigns" / campaign_name
```

## Testing

### Running Tests

Run all tests:

```bash
python tests/run_all_tests.py
```

Run specific test category:

```bash
python tests/run_all_tests.py validation
python tests/run_all_tests.py characters
python tests/run_all_tests.py stories
```

### Test Data Requirements

**CRITICAL:** Use existing data from `game_data/characters` and
`game_data/campaigns`. NEVER create mock data for tests.

Available test characters:

- `aragorn.json` - Ranger character
- `frodo.json` - Halfling character
- `gandalf.json` - Wizard character

Available test campaigns:

- `Example_Campaign/` - Contains story files and session results

### Test File Standards

- All tests must achieve 10.00/10 Pylint score
- Test files mirror `src/` directory structure
- Use descriptive test function names: `test_<function>_<scenario>_<expected>`
- Use the test helpers from `tests/test_helpers.py`

## Common Patterns

### File Operations

```python
from src.utils.file_io import load_json_file, save_json_file
from src.utils.path_utils import get_characters_dir

# Load a character
char_path = get_characters_dir() / "aragorn.json"
character = load_json_file(char_path)

# Save changes
save_json_file(char_path, character)
```

### Validation Pattern

```python
from src.utils.validation_helpers import (
    validate_required_fields,
    validate_field_type,
    format_validation_errors
)

errors = []
errors.extend(validate_required_fields(data, ["name", "class"], "character"))
errors.extend(validate_field_type(data, "level", int, "character"))

if errors:
    print(format_validation_errors(errors))
```

### Character Loading Pattern

```python
from src.utils.character_profile_utils import load_character_profile
from src.utils.path_utils import get_characters_dir

# Load with full profile
profile = load_character_profile("aragorn")
print(profile["name"])
print(profile["class"])
```

### Decision Tables

For complex conditional logic, use decision tables:

```python
# Decision table for DC modifiers
DC_MODIFIERS = {
    "easy": -5,
    "medium": 0,
    "hard": 5,
    "very_hard": 10,
}

modifier = DC_MODIFIERS.get(difficulty, 0)
```

## Workflow

### Before Starting Work

1. Read this AGENTS.md file completely
2. Check `TODO.md` for current tasks and priorities
3. Review existing code in the relevant module
4. Check `src/utils/` for existing utilities

### Making Changes

1. Write code following all standards above
2. Run Pylint: `python -m pylint src/`
3. Run relevant tests: `python tests/run_all_tests.py <category>`
4. Ensure 10.00/10 Pylint score
5. Update documentation if needed

### Committing Changes

1. Verify all tests pass
2. Verify Pylint score is 10.00/10
3. Write clear commit messages
4. Do not commit files with emojis

## Quick Reference

### Common Commands

```bash
# Run main application
python dnd_consultant.py

# Run all tests
python tests/run_all_tests.py

# Run Pylint on source
python -m pylint src/

# Run Pylint on tests
python -m pylint tests/

# Validate all game data
python -m src.validation.validate_all
```

### File Locations

| Purpose | Location |
| ------- | -------- |
| Characters | `game_data/characters/*.json` |
| Campaigns | `game_data/campaigns/<name>/` |
| Story files | `game_data/campaigns/<name>/*.md` |
| NPCs | `game_data/npcs/*.json` |
| Items | `game_data/items/custom_items.json` |
| Templates | `templates/` |

### Key Entry Points

| Entry Point | File |
| ----------- | ---- |
| Main CLI | `dnd_consultant.py` |
| Test runner | `tests/run_all_tests.py` |
| Validation | `src/validation/validate_all.py` |
