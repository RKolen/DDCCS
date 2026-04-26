# D&D Character Consultant System - Source Code Structure

This directory contains all source code organized into logical packages.

## Package Organization

```text
src/
|-- characters/          # Character management
|   |-- consultants/     # Per-character consultant classes
|   |-- character_sheet.py           # Character and NPC data models
|   |-- character_consistency.py     # Character consistency checking
|   `-- npc_constants.py             # NPC ability score constants
|
|-- npcs/               # NPC management
|   |-- npc_agents.py           # NPC AI agents
|   `-- npc_auto_detection.py   # Automatic NPC detection from stories
|
|-- stories/            # Story management
|   |-- story_manager.py                 # Core story management
|   |-- enhanced_story_manager.py        # Advanced story features
|   |-- story_analyzer.py / story_analysis.py  # Story analysis
|   |-- story_file_manager.py            # Story file operations
|   |-- story_ai_generator.py            # AI story generation
|   |-- story_amender.py                 # Story amendment workflow
|   |-- story_updater.py                 # Story file updates
|   |-- story_workflow_orchestrator.py   # Orchestrates story workflows
|   |-- story_consistency_analyzer.py    # Consistency analysis
|   |-- session_results_manager.py       # Session results tracking
|   |-- hooks_and_analysis.py            # Story hooks generation
|   |-- party_manager.py                 # Party state management
|   |-- character_manager.py             # Character management in stories
|   |-- character_loader.py              # Character loading
|   |-- character_load_helper.py         # Character loading helpers
|   |-- character_loading_base.py        # Base character loading
|   |-- character_action_analyzer.py     # Character action analysis
|   |-- character_fit_analyzer.py        # Character fit analysis
|   |-- series_analyzer.py               # Story series analysis
|   |-- equipment_checker.py             # Equipment consistency checks
|   |-- spotlight_types.py               # Spotlight data types (SpotlightEntry, SpotlightReport)
|   |-- spotlight_signals.py             # Spotlight signal collectors (recency, threads, DC, tension)
|   `-- spotlight_engine.py              # Spotlight scoring engine and prompt injection
|
|-- combat/             # Combat system
|   |-- combat_narrator.py      # Combat narration
|   |-- narrator_ai.py          # AI-driven narration
|   |-- narrator_consistency.py # Narrator consistency checking
|   `-- narrator_descriptions.py # Narrator description helpers
|
|-- items/              # Items and inventory
|   `-- item_registry.py        # Custom items registry
|
|-- dm/                 # Dungeon Master tools
|   |-- dungeon_master.py       # DM consultant
|   `-- history_check_helper.py # History check helper
|
|-- validation/         # Data validation
|   |-- character_validator.py  # Character JSON validation
|   |-- npc_validator.py        # NPC JSON validation
|   |-- items_validator.py      # Items JSON validation
|   |-- party_validator.py      # Party config validation
|   `-- validate_all.py         # Unified validator
|
|-- ai/                 # AI integration
|   |-- ai_client.py           # AI client interface (includes embed() for vectors)
|   |-- rag_system.py          # RAG (Retrieval Augmented Generation)
|   |-- availability.py        # AI availability detection
|   |-- lazy_imports.py        # Lazy import helpers
|   |-- milvus_client.py       # Milvus vector DB wrapper (connect/insert/search)
|   |-- milvus_collections.py  # Collection schema definitions (characters/npcs/stories/wiki)
|   |-- embedding_pipeline.py  # Chunking + embedding for all D&D data types
|   |-- semantic_retriever.py  # Semantic RAG via Milvus with keyword fallback
|   `-- index_sync.py          # Incremental sync called after JSON file saves
|
|-- config/             # Centralized configuration
|   |-- config_types.py        # AIConfig, RAGConfig, DisplayConfig, PathConfig, DrupalConfig
|   `-- config_loader.py       # Config loading from file/env
|
|-- integration/        # External service integration
|   `-- drupal_sync.py         # Push characters/stories to Drupal, trigger Gatsby builds
|
|-- utils/              # Shared utilities (check AGENTS.md catalog first)
|   |-- file_io.py                  # JSON and file I/O
|   |-- path_utils.py               # Game data path construction
|   |-- string_utils.py             # String processing
|   |-- validation_helpers.py       # Common validation patterns
|   |-- cli_utils.py                # CLI selection menus
|   |-- terminal_display.py         # Rich terminal output
|   |-- character_profile_utils.py  # Character loading helpers
|   |-- dnd_rules.py                # D&D 5e rules constants
|   |-- spell_highlighter.py        # Spell detection/highlighting
|   |-- npc_lookup_helper.py        # NPC lookup helpers
|   |-- story_file_helpers.py       # Story file utilities
|   |-- markdown_utils.py           # Markdown section updates
|   |-- tts_narrator.py             # TTS narration
|   |-- cache_utils.py              # In-memory cache management
|   |-- behaviour_generation.py     # Behavior from personality
|   |-- errors.py                   # Custom exceptions + error handling
|   |-- error_templates.py          # Standardized error messages
|   |-- ascii_art.py                # ASCII art character portraits
|   |-- audio_player.py             # Cross-platform audio playback
|   |-- piper_tts_client.py         # Piper neural TTS client
|   |-- dialogue_detector.py        # Dialogue segmentation for TTS
|   |-- text_formatting_utils.py    # Text wrapping utilities
|   |-- story_formatting_utils.py   # Story section formatting
|   |-- story_parsing_utils.py      # Story content parsing
|   |-- spell_lookup_helper.py      # Spell/ability RAG lookup
|   |-- npc_migration.py            # NPC profile migration
|   |-- optional_imports.py         # Optional dependency helpers
|   `-- display_file.py             # Standalone file viewer
|
`-- cli/                # Command-line interface
    |-- dnd_consultant.py                  # Main interactive CLI
    |-- dnd_cli_helpers.py                 # CLI helper functions
    |-- drupal_commands.py                 # --sync-drupal handler
    |-- milvus_commands.py                 # --reindex and --milvus-status handlers
    |-- cli_story_manager.py               # Story management CLI
    |-- cli_character_manager.py           # Character management CLI
    |-- cli_character_development_manager.py  # Character development CLI
    |-- cli_consultations.py               # Consultation handlers
    |-- cli_session_manager.py             # Session management CLI
    |-- cli_story_analysis.py              # Story analysis CLI
    |-- cli_story_helpers.py               # Story CLI helpers
    |-- cli_story_config_helper.py         # Story config helpers
    |-- cli_story_reader.py                # Story reader CLI
    |-- cli_series_analysis.py             # Series analysis CLI
    |-- cli_config.py                      # CLI configuration
    |-- base_story_interaction_manager.py  # Base story interaction
    |-- story_amender_cli_handler.py       # Story amender CLI
    |-- party_config_manager.py            # Party configuration
    `-- setup.py                           # Workspace initialization
```

## Running the System

### Main CLI

```bash
python -m src.cli.dnd_consultant
```

### Validation

```bash
# Validate all game data
python -m src.validation.validate_all

# Validate specific types
python -m src.validation.character_validator
python -m src.validation.npc_validator
python -m src.validation.items_validator
python -m src.validation.party_validator
```

### Setup Workspace

```bash
python -m src.cli.setup
```

## Import Conventions

All imports use absolute paths from the `src` package:

```python
from src.characters.consultants.character_consultants import CharacterProfile
from src.stories.story_manager import StoryManager
from src.validation.validate_all import validate_all_game_data
from src.utils.text_formatting_utils import wrap_narrative_text
```
