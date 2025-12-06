# Game Data JSON Validation

This document describes the comprehensive JSON validation system for all game data files in the D&D Campaign System, including character profiles, NPC profiles, custom items registry, and party configuration.

## Overview

The validation system ensures data integrity for:
- **Character profiles** (`game_data/characters/*.json`)
- **NPC profiles** (`game_data/npcs/*.json`)
- **Custom items registry** (`game_data/items/custom_items_registry.json`)
- **Party configuration** (`game_data/current_party/current_party.json`)

## Validation Modules

- `character_validator.py` - Validates character profiles
- `npc_validator.py` - Validates NPC profiles
- `items_validator.py` - Validates custom items registry
- `party_validator.py` - Validates party configuration (with character cross-reference)
- `validate_all.py` - Unified validator for all game data

## Usage

```bash
# Validate specific data type
python character_validator.py
python npc_validator.py
python items_validator.py
python party_validator.py

# Validate all game data
python validate_all.py

# Validate specific types with verbose output
python validate_all.py --characters --verbose
python validate_all.py --npcs
python validate_all.py --items
python validate_all.py --party

# Run validation tests
python tests/test_character_validator.py
python tests/test_npc_validator.py
python tests/test_items_validator.py
python tests/test_party_validator.py
python tests/test_all_validators.py  # Comprehensive test including consistency checks
```

## Character Profile Validation

### Required Fields
- `name`: string
- `species`: string
- `dnd_class`: string
- `level`: integer (1-20)
- `ability_scores`: dict (strength, dexterity, constitution, intelligence, wisdom, charisma)
- `equipment`: dict (weapons, armor, items)
- `known_spells`: list of strings
- `background`: string
- `backstory`: string
- `relationships`: dict

### Validation Rules
- All required fields must be present
- Field types must match schema
- Ability scores must include all six abilities as integers
- Equipment must have weapons, armor, items as arrays
- Relationships must be a dict with string values

## NPC Profile Validation

### Required Fields
- `name`: string
- `role`: string
- `species`: string
- `lineage`: string
- `personality`: string
- `relationships`: dict
- `key_traits`: list of strings
- `abilities`: list of strings
- `recurring`: boolean
- `notes`: string
- `ai_config`: dict (enabled: bool, optional fields)

### Validation Rules
- All required fields must be present
- Field types must match schema
- ai_config must have `enabled` (bool), optional fields validated if present
- Relationships must be a dict with string values
- key_traits and abilities must be arrays of strings

## Items Registry Validation

### Required Structure
- Registry is a dict; metadata fields (starting with `_`) are ignored
- Each item entry must be a dict with:
  - `name`: string
  - `item_type`: one of [magic_item, weapon, armor, gear, tool, consumable, treasure]
  - `is_magic`: boolean
  - `description`: string
  - `properties`: dict (values must be string, number, or boolean)
  - `notes`: string

### Validation Rules
- Registry must contain at least one item entry
- All required fields must be present in each item
- item_type must be valid
- properties must be a dict with valid value types

## Party Configuration Validation

### Required Structure
- `party_members`: array of strings (no duplicates, no empty strings)
- `last_updated`: ISO 8601 timestamp string

### Validation Rules
- Both fields must be present
- party_members must be non-empty, all strings, no duplicates
- last_updated must be a valid ISO timestamp
- Optionally cross-references party_members with character files

### Example Configuration
The system includes example characters: Aragorn, Frodo, and Gandalf

**Valid configuration:**
```json
{
  "party_members": [
    "Aragorn",
    "Frodo Baggins",
    "Gandalf the Grey"
  ],
  "last_updated": "2025-11-14T10:30:00.000000"
}
```

**Character files referenced:**
- `game_data/characters/aragorn.json` → "Aragorn"
- `game_data/characters/frodo.json` → "Frodo Baggins"
- `game_data/characters/gandalf.json` → "Gandalf the Grey"

### Running Party Validation
```bash
# Validate party configuration
python -m src.validation.party_validator

# Output
 game_data/current_party/current_party.json: Valid
 All 3 party members have valid character profiles
```

## Output Format

All validators use consistent output formatting:

### Valid File
```
 game_data/characters/aragorn.json: Valid
```

### Invalid File
```
 game_data/npcs/invalid_npc.json: INVALID
  - Missing required field: role
  - Field 'recurring' must be of type bool, got str
  - ai_config.enabled must be a boolean
```

## Features
- Early error detection before runtime issues
- Clear, specific error messages with field names
- Type checking for all required fields
- Cross-reference validation (party members vs character files)
- Data consistency checking across all game files
- Comprehensive test suites with edge case coverage

## Integration
- Character validation automatically integrated into `enhanced_story_manager.py` and `story_manager.py`
- Other validators available for standalone or programmatic use
- See this document for details
