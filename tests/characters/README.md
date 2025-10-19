# Character System Tests

This directory contains comprehensive tests for the D&D character
consultant system.

## Overview

The character system provides AI-enhanced character consultants for
all 12 D&D classes. Each consultant offers class expertise, DC
suggestions, personality guidance, and story consistency checking.

## Test Files

### Core Data Structures

**test_character_profile.py** (4 tests)
- Tests the CharacterProfile nested dataclass structure
- Validates 8 nested dataclasses (Identity, Personality, Behavior,
  Story, Stats, Abilities, Possessions, Mechanics)
- Tests JSON save/load with backward compatibility
- Verifies property access to nested structures

**test_class_knowledge.py** (7 tests)
- Tests static D&D class knowledge database
- Validates all 12 D&D classes (Barbarian through Wizard)
- Checks required fields (abilities, reactions, features, roleplay)
- Verifies primary abilities and key features for each class

**test_character_sheet.py** (9 tests)
- Tests DnDClass and Species enums
- Validates NPC dataclass structures (BasicInfo, PhysicalInfo,
  CharacterInfo, Profile)
- Tests enum value access and construction
- Verifies lineage lists (Elf, Gnome, Tiefling, Dragonborn)

### Character Development Tracking

**test_character_consistency.py** (7 tests)
- Tests character development file creation
- Validates story action logging with CHARACTER/ACTION/REASONING
- Tests recruit filtering with exclusion lists
- Verifies markdown file formatting and date handling

### Character Consultant Components

**test_consultant_core.py** (14 tests)
- Tests main CharacterConsultant class delegation pattern
- Validates component initialization (DC, Story, AI)
- Tests reaction suggestions (threat, puzzle, social, magic)
- Verifies personality modifiers and consistency checking
- Tests item management and relationship retrieval
- Validates load_consultant() factory function

**test_consultant_dc.py** (9 tests)
- Tests DC calculation component
- Validates difficulty modifiers (easy, hard, impossible)
- Tests class-specific bonuses (Rogue stealth, Bard persuasion,
  Barbarian intimidation)
- Verifies action type detection (stealth, persuasion, etc.)
- Tests minimum DC enforcement (never below 5)
- Validates alternative approach suggestions by class
- Tests character and background advantages

**test_consultant_story.py** (12 tests)
- Tests story consistency analysis component
- Validates consistency checking against personality and fears
- Tests consistency rating levels (through public API)
- Verifies relationship suggestions (new and updates)
- Tests plot action logging format
- Validates character development suggestions (courage, caution,
  leadership, fears)
- Tests story content analysis and character name extraction

**test_consultant_ai.py** (13 tests)
- Tests AI-enhanced consultation with graceful fallback
- Validates AI client initialization and retrieval
- Tests system prompt building (background, motivations, class
  knowledge)
- Verifies reaction and DC enhancement (requires base suggestions)
- Tests graceful degradation when AI unavailable
- Validates error handling with mock failing client

### Test Runner

**test_all_characters.py**
- Executes all 8 character test files (75 total tests)
- Provides formatted output with test summaries
- Returns proper exit codes (0 success, 1 failure)
- Shows comprehensive results across entire subsystem

## Usage

Run individual test files:
```bash
cd tests
python -m characters.test_character_profile
python -m characters.test_class_knowledge
python -m characters.test_character_sheet
python -m characters.test_character_consistency
python -m characters.test_consultant_core
python -m characters.test_consultant_dc
python -m characters.test_consultant_story
python -m characters.test_consultant_ai
```

Run entire character test suite:
```bash
cd tests
python -m characters.test_all_characters
```

## Source Code Tested

Tests cover these source modules:
- `src/characters/consultants/character_profile.py` - Profile data
  structure
- `src/characters/consultants/class_knowledge.py` - D&D class data
- `src/characters/character_sheet.py` - Character and NPC models
- `src/characters/character_consistency.py` - Development tracking
- `src/characters/consultants/consultant_core.py` - Main consultant
  class
- `src/characters/consultants/consultant_dc.py` - DC calculations
- `src/characters/consultants/consultant_story.py` - Story analysis
- `src/characters/consultants/consultant_ai.py` - AI integration

## Test Standards

All tests follow strict quality standards:
- **10.00/10 pylint score** (no exceptions, no disable comments)
- **80-character line limits** in all markdown
- **Import pattern**: try-except blocks for src imports
- **Protected methods**: Test through public API only
- **Mock pattern**: Factory functions using `type()`, not classes
- **Error handling**: Comprehensive coverage with edge cases

## Key Testing Patterns

**Nested Dataclass Testing:**
```python
profile = CharacterProfile(name="Test", level=5, dnd_class="fighter")
assert profile.identity.name == "Test"
assert profile.mechanics.level == 5
```

**Public API Testing (Protected Methods):**
```python
# Don't: result = analyzer._extract_character_names(text)
# Do: result = analyzer.analyze_story_content(text)
assert "Gandalf" in result["characters_mentioned"]
```

**Mock Object Factory:**
```python
def create_mock_consultant(profile):
    return type('MockConsultant', (), {'profile': profile})()
```

**Graceful Degradation Testing:**
```python
result = ai_consultant.suggest_reaction_enhanced(base_suggestion)
if ai_available:
    assert "ai_enhanced" in result
else:
    assert result == base_suggestion
```

## Test Coverage

The character test suite provides comprehensive coverage:
- **Data Structures**: All dataclasses and enums tested
- **Business Logic**: DC calculations, story analysis, consistency
  checking
- **Integration**: Component delegation and interaction
- **AI Integration**: Enhancement and graceful fallback
- **Error Handling**: Missing data, invalid inputs, AI failures
- **File I/O**: JSON save/load with validation warnings

Total: **75 tests** across **8 test files**, all achieving
**10.00/10 pylint**.
