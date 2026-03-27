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

Any style warnings are considered violations and must be fixed.

- never edit `pyproject.toml`

### 3. Full Pylint Output for Big Changes

For significant changes, always run the full Pylint checks:

```bash
python3 -m pylint src/ tests/
```

Never use flags or pipes.
No issue is acceptable even if score is 10/10.

#### 3.1 Pylance also needs to be happy

VsCode Pylance must also be happy with the code.

For 3 never use the excuse these are pre existing issues, they must be fixed.

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

### 5. Documentation Must Track Code

When a code change alters any of the following, the corresponding
documentation file must be updated in the same commit:

| Change Type | Documentation to Update |
|-------------|------------------------|
| New util function | AGENTS.md utils catalog |
| New config key | `docs/AI_INTEGRATION.md` or `.env.example` |
| New CLI argument | AGENTS.md quick reference + relevant `docs/` file |
| New data field in JSON schema | `docs/JSON_Validation.md` |
| New test category | `tests/README.md` |
| New `src/` module | `src/README.md` |
| Changed AI/RAG architecture | `docs/AI_INTEGRATION.md`, `docs/RAG_INTEGRATION.md` |

### 6. Type Safety: mypy + Pylance

The Python code is enforced by three complementary tools:

- **Pylint** (existing) - style, logic, and code quality
- **Pylance** (existing) - VS Code real-time type checking
- **mypy** - static type checking at CI/pre-commit level

All three must pass with zero errors before committing.

```bash
# Run mypy on source
python3 -m mypy src/

# Run mypy on tests
python3 -m mypy tests/
```

mypy configuration is in `pyproject.toml` (do not modify). Key rules:

- Every function parameter and return value must have a type annotation.
- Use `Optional[X]` (or `X | None` for Python 3.10+) for nullable values.
- Do not use `# type: ignore` comments - fix the underlying type issue.
- For third-party libraries without stubs, add `ignore_missing_imports = true`
  in the `[mypy-<package>.*]` section of config.

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
| Errors | `src/utils/errors.py` | `DnDError`, `UserInputError`, |
| | | `AIConnectionError`, `FileSystemError`, |
| | | `handle_errors`, `display_error` |
| Error Templates | `src/utils/error_templates.py` | `get_error_template`, |
| | | `ERROR_TEMPLATES` |
| ASCII Art | `src/utils/ascii_art.py` | `display_character_portrait`, |
| | | `display_party_portraits`, |
| | | `get_class_icon` |
| Audio | `src/utils/audio_player.py` | `AudioPlayer`, |
| | | `play_wav_bytes`, |
| | | `get_audio_duration_wav` |
| Piper TTS | `src/utils/piper_tts_client.py` | `PiperTTSClient`, `VoiceInfo` |
| Dialogue | `src/utils/dialogue_detector.py` | `segment_story_for_tts`, |
| | | `get_speaker_voice_map`, |
| | | `DialogueDetector` |
| Text Format | `src/utils/text_formatting_utils.py` | `wrap_narrative_text` |
| Story Format | `src/utils/story_formatting_utils.py` | `generate_consultant_notes` |
| Story Parse | `src/utils/story_parsing_utils.py` | `extract_character_actions` |
| Spell Lookup | `src/utils/spell_lookup_helper.py` | `lookup_spells_and_abilities` |
| NPC Migration | `src/utils/npc_migration.py` | `migrate_npc_to_full_profile` |
| Optional Imports | `src/utils/optional_imports.py` | `rich_available`, |
| | | `get_rich_console`, |
| | | `get_rich_component` |
| Names | `src/utils/name_utils.py` | `CharacterName`, `build_name_fields`, |
| | | `format_character_list`, |
| | | `get_name_for_dialogue`, |
| | | `get_formal_introduction`, |
| | | `validate_name_fields` |

## Project Structure

### Source Code Organization

src/
|-- characters/      # Character management + consultants subsystem
|   |-- consultants/ # Per-character consultant classes
|   |-- character_sheet.py
|   |-- character_consistency.py
|   |-- npc_constants.py
|-- npcs/            # NPC management and auto-detection
|   |-- npc_agents.py
|   |-- npc_auto_detection.py
|-- stories/         # Story management and analysis
|   |-- story_manager.py
|   |-- enhanced_story_manager.py
|   |-- story_analyzer.py / story_analysis.py
|   |-- story_file_manager.py
|   |-- story_ai_generator.py
|   |-- story_amender.py
|   |-- story_updater.py
|   |-- story_workflow_orchestrator.py
|   |-- session_results_manager.py
|   |-- hooks_and_analysis.py
|   |-- party_manager.py / character_manager.py
|   |-- character_loader.py / character_load_helper.py
|   |-- spotlight_types.py       # Spotlight data types
|   |-- spotlight_signals.py     # Spotlight signal collectors
|   |-- spotlight_engine.py      # Spotlight scoring + prompt injection
|-- combat/          # Combat narration system
|   |-- combat_narrator.py
|   |-- narrator_ai.py / narrator_consistency.py
|-- items/           # Custom items registry
|   |-- item_registry.py
|-- dm/              # Dungeon Master tools
|   |-- dungeon_master.py
|   |-- history_check_helper.py
|-- validation/      # JSON validation for all data types
|   |-- character_validator.py / npc_validator.py
|   |-- items_validator.py / party_validator.py
|   |-- validate_all.py
|-- ai/              # AI client and RAG system
|   |-- ai_client.py
|   |-- rag_system.py
|   |-- availability.py
|-- config/          # Centralized configuration
|   |-- config_types.py  # AIConfig, RAGConfig, DisplayConfig, PathConfig
|   |-- config_loader.py
|-- utils/           # Shared utilities (CHECK FIRST)
|-- cli/             # Command-line interface
|   |-- dnd_consultant.py  # Main interactive CLI
|   |-- dnd_cli_helpers.py
|   |-- cli_story_manager.py / cli_character_manager.py
|   |-- party_config_manager.py
|   |-- setup.py

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
|-- combat/          # Tests for src/combat/
|-- config/          # Tests for src/config/
|-- dm/              # Tests for src/dm/
|-- integration/     # Cross-module integration tests
|-- items/           # Tests for src/items/
|-- npcs/            # Tests for src/npcs/
|-- stories/         # Tests for src/stories/
|-- utils/           # Tests for src/utils/
|-- validators/      # Tests for src/validation/
|-- run_all_tests.py # Main test runner
|-- test_helpers.py  # Shared test utilities

### Drupal CMS

The project includes a Drupal CMS component in `drupal-cms/`. It is a separate,
PHP-based component that requires DDEV. Python tooling (Pylint, mypy, Pylance)
does not apply there.

For all Drupal-specific rules, DDEV commands, PHP code quality standards
(PHPCS + PHPStan level 6), and the contrib patch policy, see
`drupal-cms/AGENTS.md`.

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
python3 tests/run_all_tests.py
```

Run specific test category:

```bash
python3 tests/run_all_tests.py validation
python3 tests/run_all_tests.py characters
python3 tests/run_all_tests.py stories
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
python3 dnd_consultant.py

# Run all tests
python3 tests/run_all_tests.py

# Run Pylint on source
python3 -m pylint src/

# Run Pylint on tests
python3 -m pylint tests/

# Run mypy type checking
python3 -m mypy src/
python3 -m mypy tests/

# Validate all game data
python3 -m src.validation.validate_all
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
