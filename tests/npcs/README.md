# NPC System Tests

This directory contains comprehensive tests for the NPC management
system, including NPC agents and automatic NPC detection.

## Overview

The NPC system manages non-player characters in the campaign,
including automatic detection of NPCs in story content, profile
generation, and NPC agent management for recurring characters.

## Test Files

### NPC Management

**test_npc_agents.py** (8 tests)
- Tests NPCAgent class initialization and functionality
- Validates get_status() method with complete NPC profiles
- Tests memory logging with 50-event cap enforcement
- Tests load_npc_from_json() with basic and full profiles
- Validates default value handling for missing fields
- Tests create_npc_agents() for multiple NPC loading
- Validates example file filtering (npc.example.json skipped)
- Tests empty directory handling

**test_npc_auto_detection.py** (14 tests)
- Tests detect_npc_suggestions() with multiple patterns:
  - "innkeeper named X" pattern
  - "X, the innkeeper" pattern
  - "merchant named X" pattern
  - "guard captain X" pattern
  - "blacksmith X" patterns (both variants)
- Tests multiple NPC detection in single story
- Validates party member exclusion from detection
- Tests false positive filtering (common words, articles)
- Validates existing profile skip behavior
- Tests context excerpt extraction
- Tests generate_npc_from_story() without AI (fallback)
- Tests _create_fallback_profile() error handling
- Tests save_npc_profile() with validation warnings
- Validates fail-soft save behavior

### Test Runner

**test_all_npcs.py**
- Executes all 2 NPC test files (22 total tests)
- Provides formatted output with test summaries
- Returns proper exit codes (0 success, 1 failure)
- Shows comprehensive results across entire subsystem

## Usage

Run individual test files:
```bash
python .\tests\run_all_tests.py npcs
```

## Source Code Tested

Tests cover these source modules:
- `src/npcs/npc_agents.py` - NPCAgent class and NPC loading
- `src/npcs/npc_auto_detection.py` - Automatic NPC detection and
  profile generation

## Test Standards

All tests follow strict quality standards:
- **10.00/10 pylint score** (no exceptions, no disable comments)
- **80-character line limits** in all markdown
- **Import pattern**: try-except blocks for src imports
- **Temporary files**: tempfile module for isolated testing
- **Comprehensive coverage**: All major code paths tested

## Key Testing Patterns

**NPC Agent Creation:**
```python
profile = NPCProfile.create(
    name="Garrett",
    role="Innkeeper",
    species="Human",
    personality="Friendly and chatty"
)
agent = NPCAgent(profile)
status = agent.get_status()
```

**NPC Detection Testing:**
```python
story = "The innkeeper named Garrett greeted them warmly."
suggestions = detect_npc_suggestions(story, party_names, workspace)
assert suggestions[0]["name"] == "Garrett"
assert suggestions[0]["role"] == "Innkeeper"
```

**Temporary File Testing:**
```python
with tempfile.NamedTemporaryFile(
    mode="w", suffix=".json", delete=False
) as f:
    f.write('{"name": "TestNPC", "role": "Merchant"}')
    temp_path = f.name
try:
    profile = load_npc_from_json(Path(temp_path))
    assert profile.name == "TestNPC"
finally:
    os.unlink(temp_path)
```

**Directory Testing:**
```python
with tempfile.TemporaryDirectory() as temp_dir:
    # Create test files
    agents = create_npc_agents(Path(temp_dir))
    assert len(agents) == 2
```

## Test Coverage

The NPC test suite provides comprehensive coverage:
- **NPC Agents**: Initialization, status, memory, loading, batch
  creation
- **Auto-Detection**: Pattern matching (5 NPC types), multiple
  patterns per type
- **False Positives**: Article filtering, common word filtering,
  party exclusion
- **Profile Generation**: AI fallback, error handling, validation
- **File Operations**: JSON save/load, sanitized filenames, fail-soft
  validation
- **Edge Cases**: Empty directories, missing fields, existing
  profiles

Total: **22 tests** across **2 test files**, all achieving
**10.00/10 pylint**.
