# D&D Character Consultant System - Source Code Structure

This directory contains all source code organized into logical packages.

## Package Organization

```
src/
├── characters/          # Character management
│   ├── consultants/     # Character consultant system (will be split in Phase 1)
│   ├── character_sheet.py       # Character and NPC data models
│   └── character_consistency.py # Character consistency checking
│
├── npcs/               # NPC management
│   ├── npc_agents.py           # NPC AI agents
│   └── npc_auto_detection.py   # Automatic NPC detection from stories
│
├── stories/            # Story management
│   ├── story_manager.py            # Core story management
│   ├── enhanced_story_manager.py   # Advanced story features
│   ├── story_analyzer.py           # Story analysis
│   ├── story_file_manager.py       # Story file operations
│   ├── session_results_manager.py  # Session results tracking
│   └── hooks_and_analysis.py       # Story hooks generation
│
├── combat/             # Combat system
│   └── combat_narrator.py      # Fantasy Grounds combat converter
│
├── items/              # Items and inventory
│   └── item_registry.py        # Custom items registry
│
├── dm/                 # Dungeon Master tools
│   ├── dungeon_master.py       # DM consultant
│   └── history_check_helper.py # History check helper
│
├── validation/         # Data validation
│   ├── character_validator.py  # Character JSON validation
│   ├── npc_validator.py        # NPC JSON validation
│   ├── items_validator.py      # Items JSON validation
│   ├── party_validator.py      # Party config validation
│   └── validate_all.py         # Unified validator
│
├── ai/                 # AI integration
│   ├── ai_client.py           # AI client interface
│   └── rag_system.py          # RAG (Retrieval Augmented Generation)
│
├── utils/              # Shared utilities
│   ├── file_io.py                # JSON and file I/O operations
│   ├── path_utils.py             # Game data path construction
│   ├── string_utils.py           # String processing and normalization
│   ├── validation_helpers.py     # Common validation patterns
│   ├── text_formatting_utils.py  # Text formatting and wrapping
│   └── spell_highlighter.py      # Spell detection and highlighting
│
└── cli/                # Command-line interface
    ├── dnd_consultant.py       # Main interactive CLI
    ├── dnd_cli_helpers.py      # CLI helper functions
    ├── party_config_manager.py # Party configuration
    └── setup.py                # Workspace initialization
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
