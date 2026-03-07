# Error Handling Phase 4 - Remaining Files

## Status Summary

### Steps 2 & 3 - COMPLETE

- **Step 2 (Error Handler Utility)**: Implemented in `src/utils/errors.py` with:
  - `handle_errors` decorator
  - `wrap_exception` function
  - `display_error` function

- **Step 3 (Error Message Templates)**: Implemented in `src/utils/error_templates.py`

### Step 4 (Module Integration) - NOT COMPLETE

The following files still use old-style error handling (`print("[ERROR]...")` or `print("[WARNING]...")`):

---

## Files Needing Updates

### CLI Files

| File | Issues |
|------|--------|
| `src/cli/cli_story_reader.py` | Uses `print_error()` - already uses terminal_display |
| `src/cli/cli_story_manager.py` | 5+ `print("[WARNING]...")` statements |
| `src/cli/cli_series_analysis.py` | 4+ `print("[WARNING]...")` statements |
| `src/cli/cli_story_analysis.py` | 2+ `print("[WARNING]...")` statements |
| `src/cli/cli_story_helpers.py` | 2+ `print("[WARNING]...")` statements |
| `src/cli/dnd_consultant.py` | 2+ `print("[WARNING]...")` statements |
| `src/cli/party_config_manager.py` | `print("[WARNING]...")` statements |
| `src/cli/cli_consultations.py` | `print("[WARNING]...")` statements |

### Story/NPC Files

| File | Issues |
|------|--------|
| `src/stories/story_analyzer.py` | `print("[WARNING]...")` for validation |
| `src/stories/story_updater.py` | 2+ `print("[WARNING]...")` statements |
| `src/stories/party_manager.py` | `print("[WARNING]...")` statements |
| `src/stories/enhanced_story_manager.py` | `print("[WARNING]...")` statements |
| `src/stories/hooks_and_analysis.py` | `print("[WARNING]...")` statements |
| `src/npcs/npc_auto_detection.py` | `print("[WARNING]...")` for AI generation |

### Other Files

| File | Issues |
|------|--------|
| `src/dm/dungeon_master.py` | `print("[WARNING]...")` for AI narration |
| `src/combat/narrator_ai.py` | 2+ `print("[WARNING]...")` statements |
| `src/items/item_registry.py` | 3+ `print("[WARNING]...")` statements |
| `src/utils/tts_narrator.py` | 10+ `print("[ERROR]...")` and `print("[WARNING]...")` statements |
| `src/utils/npc_migration.py` | `print("[WARNING]...")` statements |

---

## Files Already Updated (Using Centralized Error Handling)

- `src/cli/cli_character_manager.py` - uses `UserInputError`, `FileSystemError`
- `src/cli/cli_config.py` - uses `UserInputError`, `FileSystemError`
- `src/cli/cli_session_manager.py` - uses `FileSystemError`
- `src/cli/story_amender_cli_handler.py` - uses `DnDError`
- `src/stories/story_ai_generator.py` - uses `display_error`, `wrap_exception`
- `src/stories/series_analyzer.py` - uses `display_error`, `wrap_exception`
- `src/items/item_registry.py` - uses `FileSystemError`
- `src/ai/rag_system.py` - uses `DnDError`

---

## Total: ~20+ files still need updating to fully complete Phase 4
