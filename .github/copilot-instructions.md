# D&D Character Consultant System - Copilot Instructions

##  IMPORTANT: Read This First

**BEFORE starting ANY task:**
1. **ALWAYS read this entire file** to understand the current project state
2. **If asked to "verify the entire project" or "check everything":**
   - Read EVERY file mentioned in the project structure below
   - NO shortcuts, NO assumptions, NO partial reads
   - Verify actual code matches documentation
   - Check imports, dependencies, and file relationships
   - Confirm examples and workflows are accurate

**When making plans:**
- First verify you understand the current system by reading relevant files
- Plans should reflect ACTUAL code structure, not assumptions
- If uncertain about ANY detail, read the source file completely

This workspace contains a Python-based D&D character consultant system designed to help with campaign management and story development.

## Project Overview

This is a **D&D 5e (2024) Character Consultant System** that provides:
- 12 AI character consultants (one per D&D class)
- Story sequence management with markdown files in campaign folders
- Character background customization
- DC suggestion engine
- Fantasy Grounds Unity combat conversion
- Character consistency analysis
- Automatic NPC detection and profile generation
- Spell highlighting in story narratives
- RAG system integration with D&D wikis (lore + rules)
- Custom items registry for homebrew content
- VSCode workspace integration

## Key Files & Structure

```
D&D Campaign Workspace/
├── game_data/               # All user campaign data (git-ignored except examples)
│   ├── characters/          # Character profile JSON files
│   │   ├── barbarian.json   # Customizable character backgrounds
│   │   ├── bard.json       # User writes custom personalities
│   │   └── ...             # All 12 D&D classes
│   ├── npcs/               # NPC profile JSON files
│   ├── items/              # Custom items registry
│   ├── current_party/      # Party configuration
│   └── campaigns/          # User campaign folders
│       └── Your_Campaign/  # Campaign stories and analysis
│           ├── 001_*.md    # Story sequence files
│           └── session_results_*.md
├── src/                    # All source code (Phase 0 complete!)
│   ├── characters/         # Character management
│   │   ├── consultants/    # Character consultant system (Phase 1 complete!)
│   │   │   ├── consultant_core.py         # Main CharacterConsultant class
│   │   │   ├── consultant_dc.py           # DC calculation component
│   │   │   ├── consultant_story.py        # Story analysis component
│   │   │   ├── consultant_ai.py           # AI integration component
│   │   │   ├── character_profile.py       # CharacterProfile dataclass
│   │   │   └── class_knowledge.py         # D&D class data (12 classes)
│   │   ├── character_sheet.py       # Character and NPC data models
│   │   └── character_consistency.py # Character consistency checking
│   ├── npcs/              # NPC management
│   │   ├── npc_agents.py           # NPC AI agents
│   │   └── npc_auto_detection.py   # Automatic NPC detection
│   ├── stories/           # Story management
│   │   ├── story_manager.py            # Core story management
│   │   ├── enhanced_story_manager.py   # Advanced story features
│   │   ├── story_analyzer.py           # Story analysis
│   │   ├── story_file_manager.py       # Story file operations
│   │   ├── session_results_manager.py  # Session results tracking
│   │   └── hooks_and_analysis.py       # Story hooks generation
│   ├── combat/            # Combat system (Phase 2 complete!)
│   │   ├── combat_narrator.py          # Main combat narrator (92 lines)
│   │   ├── narrator_ai.py              # AI-enhanced narration component
│   │   ├── narrator_descriptions.py    # Combat action descriptions
│   │   └── narrator_consistency.py     # Character consistency checking
│   ├── items/             # Items and inventory
│   │   └── item_registry.py        # Custom items registry
│   ├── dm/                # Dungeon Master tools
│   │   ├── dungeon_master.py       # DM consultant
│   │   └── history_check_helper.py # History check helper
│   ├── validation/        # Data validation
│   │   ├── character_validator.py  # Character JSON validation
│   │   ├── npc_validator.py        # NPC JSON validation
│   │   ├── items_validator.py      # Items JSON validation
│   │   ├── party_validator.py      # Party config validation
│   │   └── validate_all.py         # Unified validator
│   ├── ai/                # AI integration
│   │   ├── ai_client.py           # AI client interface
│   │   └── rag_system.py          # RAG system
│   ├── utils/             # Shared utilities
│   │   ├── dnd_rules.py            # D&D 5e game rules (DCs, modifiers)
│   │   ├── file_io.py              # File operations
│   │   ├── path_utils.py           # Path utilities
│   │   ├── string_utils.py         # String utilities
│   │   ├── validation_helpers.py   # Validation helpers
│   │   ├── text_formatting_utils.py  # Text formatting
│   │   └── spell_highlighter.py      # Spell detection
│   └── cli/               # Command-line interface (Phase 2 complete!)
│       ├── dnd_consultant.py       # Main interactive CLI (110 lines)
│       ├── cli_character_manager.py # Character management operations
│       ├── cli_story_manager.py     # Story and series management
│       ├── cli_consultations.py     # Character consultations and DCs
│       ├── cli_story_analysis.py    # Story analysis and combat conversion
│       ├── dnd_cli_helpers.py      # CLI helper functions
│       ├── party_config_manager.py # Party configuration
│       └── setup.py                # Workspace initialization
├── tests/                 # Test suite (git-ignored)
│   ├── test_character_validator.py
│   ├── test_npc_validator.py
│   ├── test_items_validator.py
│   ├── test_party_validator.py
│   └── test_all_validators.py
├── docs/                  # Documentation
│   ├── JSON_Validation.md
│   └── Validator_Integration.md
└── .vscode/
    ├── tasks.json         # Quick access to consultants
    └── settings.json      # Markdown preferences
```

## User Workflow

The user creates story files in format `001_<storyname>.md` and:
1. Writes pure narrative in story files (dialogue, descriptions, events)
2. System auto-detects NPCs and suggests profiles in story_hooks_*.md files
3. Spell names are automatically highlighted when mentioned (e.g., casts **Fireball**)
4. Character development tracked in separate character_development_*.md files
5. DC suggestions calculated in separate story_dc_suggestions.md file
6. Session results (rolls, DCs, outcomes) saved in session_results_*.md files
7. Fantasy Grounds Unity combat converted to narrative and appended to story

## Character Consultant System

**Architecture (Phase 1 complete!):** Uses composition pattern with specialized components:

- **consultant_core.py** - Main `CharacterConsultant` class that orchestrates components
  - Handles character loading, core reactions, item management
  - Delegates to specialized components via composition
  
- **consultant_dc.py** - `DCCalculator` component
  - DC calculations based on action difficulty + character strengths
  - Alternative approach suggestions
  - Character advantage detection
  
- **consultant_story.py** - `StoryAnalyzer` component
  - Story consistency checking against character profile
  - Relationship update suggestions
  - Character development tracking
  - Plot action logging
  
- **consultant_ai.py** - `AIConsultant` component (optional)
  - AI-enhanced reaction suggestions
  - AI-powered DC calculations
  - Integration with AI client
  
- **character_profile.py** - `CharacterProfile` dataclass
  - 30+ fields (name, class, level, personality, equipment, etc.)
  - JSON save/load methods
  
- **class_knowledge.py** - Static D&D class data
  - All 12 D&D classes with abilities, reactions, roleplay notes

Each consultant provides:
- **Class expertise** (spell lists, abilities, tactics)
- **DC suggestions** based on character strengths
- **Personality guidance** from custom backgrounds
- **Consistency checking** against established character traits
- **Alternative approaches** that fit the character class

## Coding Guidelines

### CRITICAL: No Emojis in Any Code

**NEVER use emojis in any Python files (.py) or Markdown files (.md)**
- Emojis cause encoding errors on Windows (cp1252 codec)
- Break code execution even with UTF-8 configuration
- Use ASCII alternatives instead
- **Rationale:** Windows console uses cp1252 encoding by default, emojis break execution
- **Applies to:** All .py files, all .md files, all documentation

### CRITICAL: No Pylint Disable Comments

**NEVER use `# pylint: disable=...` comments**
**NEVER!**
**Never create a .pylintrc file to cheat this rule**
**NEVER!**

**Instead, properly fix the issue:**
- **Import outside toplevel:** Move imports to module top level
- **Too many arguments:** Use builder pattern, config dicts, or dataclasses
- **Too complex functions:** Extract helper functions or split into smaller methods
- **Unused variables:** Remove them or prefix with `_` if required by API
- **Long lines:** Split properly using parentheses and line continuations
- **Broad exceptions:** Use specific exception types
- **File too long (>1000 lines):** Split into multiple modules

If you encounter a pylint warning, propose a proper architectural solution and document it in `docs/docs_personal/future_rework.md` for review.

### When working with this codebase:

1. **Character Profiles**: All stored as JSON in `game_data/characters/` directory with user-customizable backgrounds
2. **Story Analysis**: Parse markdown files for CHARACTER/ACTION/REASONING blocks
3. **DC Calculations**: Base difficulty + character modifiers + context
4. **Narrative Style**: Character-appropriate descriptions for combat
5. **VSCode Integration**: Use tasks.json for quick access to consultant features

## Example Character Profile Structure

```json
{
  "name": "Character Name",
  "dnd_class": "fighter",
  "level": 5,
  "background_story": "User's custom background...",
  "personality_summary": "User's personality description...",
  "motivations": ["list", "of", "motivations"],
  "fears_weaknesses": ["character", "vulnerabilities"],
  "relationships": {
    "Character2": "relationship description"
  },
  "equipment": {
    "weapons": ["Longsword", "Shield"],
    "armor": "Plate Armor",
    "magic_items": ["Ring of Protection"]
  },
  "known_spells": ["Shield", "Misty Step", "Fireball"]
}
```

## Story File Format

**Primary Story Files (`001_*.md`):**
```markdown
# Chapter Title

*Note: Keep lines to max 80 characters for improved readability*

## Scene Title

Write pure narrative story content here. Focus on:
- Character actions and dialogue
- Environmental descriptions  
- Plot developments
- NPC interactions

Example narrative format:
Kael strode confidently to the bar where a portly human was cleaning 
mugs. "Good evening, friend. My companions and I seek rooms for the 
night, and perhaps a warm meal."

The innkeeper glanced around nervously before leaning closer. "Rooms 
I've got, but there's been strange happenings lately..."
```

**Character Development Analysis (separate file `character_development_*.md`):**
```markdown
# Character Development: Story Name

## Character Actions & Reasoning

### CHARACTER: [Character Name]
**ACTION:** [What they attempted]
**REASONING:** [Why they did it - for consistency]
**Consistency Check:** [Analysis results]
**Development Notes:** [Suggestions]
```

**DC Suggestions (separate file `story_dc_suggestions.md`):**
- Character-specific DC calculations
- Action difficulty assessments
- Alternative approach suggestions
- Skill check requirements

**Session Results (separate file `session_results_*.md`):**
- Roll results (dice, DCs, outcomes)
- Mechanical game data
- Recruiting pool information

**Story Hooks (separate file `story_hooks_*.md`):**
- Unresolved plot threads
- NPC profile suggestions (auto-detected)
- Future session ideas

## Main Commands

- `python -m src.cli.setup` - One-time workspace initialization (creates VSCode config, verifies folders)
- `python -m src.cli.dnd_consultant` - **Main interactive tool** for all user workflows:
  - Create and manage campaigns
  - Create and edit story files
  - Manage party configuration
  - Get character consultations and DC suggestions
  - Convert combat logs to narratives
- VS Code tasks for quick access via Ctrl+Shift+P

## JSON Validation System

The system includes comprehensive JSON validation for all game data:

**Validators:**
- `character_validator.py` - Validates character profiles (12 files validated)
- `npc_validator.py` - Validates NPC profiles
- `items_validator.py` - Validates custom items registry
- `party_validator.py` - Validates party configuration (with character cross-reference)
- `validate_all.py` - Unified validator for all game data at once

**Usage:**
```bash
# Validate specific data type
python -m src.validation.character_validator
python -m src.validation.npc_validator
python -m src.validation.items_validator
python -m src.validation.party_validator

# Validate all game data
python -m src.validation.validate_all

# Validate specific types with verbose output
python -m src.validation.validate_all --characters --verbose
python -m src.validation.validate_all --npcs
python -m src.validation.validate_all --items
python -m src.validation.validate_all --party

# Run validation tests
python tests/test_character_validator.py
python tests/test_npc_validator.py
python tests/test_items_validator.py
python tests/test_party_validator.py
python tests/test_all_validators.py  # Comprehensive test including consistency checks
```

**Features:**
- Early error detection before runtime issues
- Clear, specific error messages with field names
- Type checking for all required fields
- Cross-reference validation (party members vs character files)
- Data consistency checking across all game files
- Comprehensive test suites with edge case coverage

**Integration:**
- **Automatic validation on save** - All JSON file creation/saving includes validation
  - `CharacterProfile.save_to_file()` - character validation
  - `EnhancedStoryManager.save_npc_profile()` - NPC validation
  - `StoryAnalyzer.save_npc_template()` - NPC validation
  - `save_current_party()` - party validation
  - `ItemRegistry.save_registry()` - items validation
- **Automatic validation on load** - Character loading validates in story managers
- **Standalone validators** - Can be run manually or in CI/CD
- **Fail-soft approach** - Warnings displayed but saves continue (prevents data loss)
- See `docs/JSON_Validation.md` and `docs/Validator_Integration.md` for details

## Technical Notes

- **No external dependencies** - uses only Python standard library
- **Type hints throughout** for better code clarity
- **JSON-based storage** for easy character customization
- **JSON validation** ensures data integrity across all game files
- **Markdown integration** with VSCode workflow
- **Modular design** for easy extension

## User Customization Areas

Users should customize:
1. **Character backgrounds** in JSON files
2. **Personality traits** and motivations
3. **Character relationships** with each other
4. **Story hooks** and character arcs

## Spell Highlighting System

The spell highlighter automatically detects and formats spell names in story text:

**Detection Patterns:**
- Context words: casts, channels, invokes, summons, conjures, unleashes, weaves, etc.
- Spell names: 1-3 capitalized words following context words
- Smart boundaries: Stops at prepositions, punctuation, articles
- Known spells: Extracted from character profiles' `known_spells` field

**Usage:**
```python
from spell_highlighter import highlight_spells_in_text, extract_known_spells_from_characters

# Extract known spells from all characters
characters = load_character_data()
known_spells = extract_known_spells_from_characters(characters)

# Highlight spells in text
text = "Gandalf casts Fireball at the approaching orcs."
highlighted = highlight_spells_in_text(text, known_spells)
# Result: "Gandalf casts **Fireball** at the approaching orcs."
```

**Integration:**
- `enhanced_story_manager.py` automatically applies spell highlighting to story narratives
- Uses `apply_spell_highlighting()` method for public API access
- Known spells updated when characters are loaded

## Testing Practices

**Test Directory:**
- All development tests are stored in `tests/` folder
- Tests are **git-ignored** and should not be committed
- Tests will remain local until test framework is formalized (see TODO.md)

**Creating Tests:**
- Name tests descriptively: `test_<feature>_<scenario>.py`
- Include verification of actual behavior, not just programmatic tests
- Clean up test data (campaigns, files) after test runs
- Document test purpose and expected outcomes

**Test Types:**
- Integration tests: Verify multiple components work together
- Workflow tests: Verify end-to-end user workflows (story creation, git patterns)
- Manual tests: Quick validation scripts for development

## Commit Message Standards

Follow these guidelines for all commits:

**Format:**
```
Brief summary of changes (50 chars or less)

Optional detailed explanation if needed:
- Bullet points for multiple changes
- Keep focused on what and why, not how
```

**Rules:**
- Keep summary line concise (50 characters max)
- Use imperative mood: "Add feature" not "Added feature"
- No emojis or decorative characters
- Professional tone
- Group related changes in single commit
- Reference issue numbers if applicable

**Examples:**
-  Good: "Reorganize user data into game_data folder and add spell highlighting"
-  Bad: " Added spell highlighting  and reorganized stuff "
-  Good: "Fix gitignore pattern for campaign files"
-  Bad: "Fixed the .gitignore because campaign files were showing up in git status which was annoying"

## Common Tasks

When assisting with this project:
- Help customize character profiles with rich backgrounds
- Assist with story analysis and consistency checking
- Support VSCode task configuration
- Guide DC balancing for character abilities

This system enhances user creativity rather than replacing it - the user maintains full control while getting expert character consultation.