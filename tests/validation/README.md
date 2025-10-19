# Validation Tests

## What This Tests
JSON validation for all game data files (characters, NPCs, items, party configuration). Ensures data integrity and catches schema errors before they cause runtime issues.

## Why These Tests Matter
- **Early Error Detection:** Catch invalid data before it breaks the system
- **Data Integrity:** Ensure all JSON files match expected schemas
- **Cross-Reference Validation:** Verify party members exist as character files
- **Consistency Checking:** Validate relationships and references across files
- **User Feedback:** Provide clear error messages for data issues

## Test Files

### test_character_validator.py
- **What:** Validates character profile JSON files against schema
- **Why:** Characters are the core data structure, must be valid
- **Focus:** Required fields, optional fields, type checking, file I/O errors
- **Coverage:** All 12 D&D class character files validated

### test_npc_validator.py
- **What:** Validates NPC profile JSON files against schema
- **Why:** NPCs are auto-generated and need validation
- **Focus:** Required fields, optional fields, AI config validation, relationships
- **Coverage:** NPC schema structure and type validation

### test_party_validator.py
- **What:** Validates party configuration JSON and cross-references with character files
- **Why:** Party config drives NPC detection and story analysis
- **Focus:** Party members list, character existence checks, date validation
- **Coverage:** Party file structure and character cross-validation

### test_items_validator.py
- **What:** Validates custom items registry JSON against schema
- **Why:** Homebrew items need structured data for wiki lookup blocking
- **Focus:** Item entries, item types, properties validation, required fields
- **Coverage:** Items registry structure and item data validation

### test_all_validators.py
- **What:** Comprehensive test suite running all validators together
- **Why:** Ensures unified validation system works correctly
- **Focus:** 
  - All character files validation
  - All NPC files validation  
  - Items registry validation
  - Party configuration validation
  - Cross-validation (party ↔ characters)
  - Data consistency (relationships)
  - Error detection (invalid data catches)
- **Coverage:** Full game data validation + consistency checks

## Running Tests

```bash
# Run all validation tests
python tests/validation/test_all_validators.py

# Run individual validators
python tests/validation/test_character_validator.py
python tests/validation/test_npc_validator.py
python tests/validation/test_party_validator.py
python tests/validation/test_items_validator.py

# Run from root with full suite
python tests/run_all_tests.py
```

## Test Results

**Current Status:** ✅ 5/5 tests passing, 10.00/10 pylint

- ✅ test_character_validator.py - PASS (12 character files validated)
- ✅ test_npc_validator.py - PASS
- ✅ test_party_validator.py - PASS
- ✅ test_items_validator.py - PASS
- ✅ test_all_validators.py - PASS (comprehensive validation + consistency)

## Test Coverage

### What's Tested
- ✅ Character profile schema validation
- ✅ NPC profile schema validation
- ✅ Items registry schema validation
- ✅ Party configuration schema validation
- ✅ Cross-reference validation (party → characters)
- ✅ Data consistency checks (relationships)
- ✅ Error detection and reporting
- ✅ File I/O error handling
- ✅ Type checking for all fields
- ✅ Required vs optional field validation

### What's Not Tested
- ❌ Runtime validation during actual gameplay
- ❌ Performance testing with large datasets
- ❌ Concurrent file access scenarios

### Future Enhancements
- [ ] Add validation for campaign folder structures
- [ ] Add validation for story file formats
- [ ] Add validation for session results files
- [ ] Add performance benchmarks for large datasets

## Integration with Main System

**Automatic Validation:**
- Character profiles validated on save: `CharacterProfile.save_to_file()`
- NPC profiles validated on save: `EnhancedStoryManager.save_npc_profile()`
- Party config validated on save: `save_current_party()`
- Items registry validated on save: `ItemRegistry.save_registry()`

**Standalone Validators:**
```bash
# Validate all character files
python -m src.validation.character_validator

# Validate all NPC files
python -m src.validation.npc_validator

# Validate party configuration
python -m src.validation.party_validator

# Validate items registry
python -m src.validation.items_validator

# Validate all game data
python -m src.validation.validate_all
```

## Shared Helper Functions

**From `src/utils/validation_helpers.py`:**
- `get_type_name(expected_type)` - Converts type annotations to human-readable strings
- `print_validation_report(filepath, is_valid, errors)` - Standardized validation output
- Other validation utilities for common patterns

**Why Shared Helpers:**
- DRY principle - no code duplication
- Consistent validation behavior across all validators
- Easier to maintain and extend
- Achieved 10.00/10 pylint by extracting duplicate code

## Notes

- All validators achieve 10.00/10 pylint with NO disable comments
- Validators use fail-soft approach (warnings but continue) to prevent data loss
- Clear, specific error messages include field names and expected types
- Cross-reference validation ensures data consistency across files
- Comprehensive test suite includes edge cases and error scenarios
