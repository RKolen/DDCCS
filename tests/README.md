# D&D Character Consultant System - Test Suite# D&D Character Consultant System - Test Suite# Development Tests



This directory contains the comprehensive test suite for the D&D Character Consultant System. The test structure mirrors the modular `src/` directory for clarity and maintainability.



## 📁 Test Directory StructureThis directory contains the comprehensive test suite for the D&D Character Consultant System. The test structure mirrors the modular `src/` directory for clarity and maintainability.This folder contains development tests for the D&D Character Consultant System.



```

tests/

├── validation/          # JSON validation tests (5 tests - ALL PASSING ✅)## 📁 Test Directory Structure## Important Notes

│   ├── test_character_validator.py

│   ├── test_npc_validator.py

│   ├── test_items_validator.py

│   ├── test_party_validator.py```- **Tests are NOT committed to git** - They remain local only

│   └── test_all_validators.py

├── ai/                  # AI integration tests (1 test - PASSING ✅)tests/- Tests will stay git-ignored until a formal test framework is implemented (see TODO.md)

│   └── test_ai_env_config.py

├── characters/          # Character system tests (TODO)├── validation/          # JSON validation tests- This prevents accidental commits of development tests to the repository

├── npcs/                # NPC system tests (TODO)

├── stories/             # Story management tests (TODO)│   ├── test_character_validator.py

├── combat/              # Combat system tests (TODO)

├── items/               # Items system tests (TODO)│   ├── test_npc_validator.py## Purpose

├── dm/                  # DM tools tests (TODO)

├── utils/               # Utility function tests (TODO)│   ├── test_items_validator.py

├── cli/                 # CLI interface tests (TODO)

├── integration/         # End-to-end workflow tests (TODO)│   ├── test_party_validator.pyStore testing scripts created during development to:

├── test_helpers.py      # Shared test utilities (UTF-8 encoding, path setup)

├── run_all_tests.py     # Unified test runner (10.00/10 pylint)│   └── test_all_validators.py- Verify feature functionality

├── .pylintrc            # Test-specific pylint configuration

└── README.md            # This file├── ai/                  # AI integration tests- Test integration between components

```

│   └── test_ai_env_config.py- Validate end-to-end workflows

## 🎯 Current Test Status

├── characters/          # Character system tests- Quick validation during development

**Implemented Tests (6/6 passing):**

- ✅ Character JSON validation (12 character files validated)├── npcs/                # NPC system tests

- ✅ NPC JSON validation (1 NPC file validated)

- ✅ Items registry validation├── stories/             # Story management tests## Test Guidelines

- ✅ Party configuration validation

- ✅ Cross-reference validation (party members vs character files)├── combat/              # Combat system tests

- ✅ AI environment configuration test

├── items/               # Items system tests**Naming Convention:**

**Test Quality:**

- All test files: 10.00/10 pylint (when run from tests directory)├── dm/                  # DM tools tests- Use descriptive names: `test_<feature>_<scenario>.py`

- Test runner: 10.00/10 pylint

- UTF-8 encoding properly configured for Windows console├── utils/               # Utility function tests- Example: `test_spell_highlighting_integration.py`

- Comprehensive error detection tests

├── cli/                 # CLI interface tests- Example: `test_story_creation_workflow.py`

## 🚀 Running Tests

├── integration/         # End-to-end workflow tests

### Run All Tests

```powershell├── test_setup.py        # Test setup utilities**Test Structure:**

python tests/run_all_tests.py

```└── run_all_tests.py     # Unified test runner- Include clear test purpose in docstring or comments



### Run Specific Test Category```- Document expected outcomes

```powershell

python tests/run_all_tests.py validation- Clean up test data after runs (campaigns, temporary files)

python tests/run_all_tests.py ai

```## 🚀 Running Tests- Include verification of actual behavior, not just programmatic checks



### Run Individual Test File

```powershell

python tests/validation/test_character_validator.py### Run All Tests**Test Types:**

python tests/ai/test_ai_env_config.py

``````bash



### Run Pylint on Testspython tests/run_all_tests.py1. **Integration Tests**: Verify multiple components work together

```powershell

cd tests```   - Example: Test spell highlighter with enhanced story manager

python -m pylint validation/*.py ai/*.py test_helpers.py run_all_tests.py --score=y

```   - Verify data flows correctly between modules



## 📝 Writing New Tests### Run Specific Category



### Test File Template```bash2. **Workflow Tests**: Verify end-to-end user workflows



```pythonpython tests/run_all_tests.py validation   - Example: Create campaign story, verify file creation, check git patterns

"""

Test <feature description>python tests/run_all_tests.py ai   - Test actual user scenarios from start to finish

Verifies that <module> correctly <behavior>.

"""python tests/run_all_tests.py stories



import os```3. **Manual Tests**: Quick validation scripts

import sys

from pathlib import Path   - Example: Check specific function outputs



# Add tests directory to path so we can import test_helpers### Run Multiple Categories   - Verify path configurations

sys.path.insert(0, str(Path(__file__).parent.parent))

```bash   - Validate data formats

# Import and configure test environment (UTF-8, project paths)

import test_helperspython tests/run_all_tests.py validation ai characters

project_root = test_helpers.setup_test_environment()

```## Running Tests

# Import the module to test

from src.module.to_test import function_to_test



### Verbose OutputTests should be run manually using Python:

def test_feature():

    """Test that feature works correctly."""```bash

    # Test implementation

    result = function_to_test()python tests/run_all_tests.py --verbose```powershell

    assert result == expected, f"Expected {expected}, got {result}"

    print("✓ Test passed")python tests/run_all_tests.py validation --verbosepython tests/test_<name>.py



``````

if __name__ == "__main__":

    print("Running <feature> tests...\n")

    

    try:### Run Individual Test FileAlways clean up test data after running:

        test_feature()

        print("\n✓ All tests passed!")```bash- Remove test campaigns from `game_data/campaigns/`

    except AssertionError as e:

        print(f"\n✗ Test failed: {e}")python tests/validation/test_character_validator.py- Delete temporary files

        sys.exit(1)

    except Exception as e:python tests/ai/test_ai_env_config.py- Verify git status shows no test artifacts

        print(f"\n✗ Unexpected error: {e}")

        import traceback```

        traceback.print_exc()

        sys.exit(1)## Test Data Locations

```

## 📋 Test Categories

### Test Guidelines

Common test data locations:

**Naming Convention:**

- Use descriptive names: `test_<module>_<feature>.py`### Validation Tests (`tests/validation/`)- Campaign tests: `game_data/campaigns/Test_*` folders

- Examples: `test_story_manager_creation.py`, `test_combat_narrator_descriptions.py`

- Character JSON validation- Character tests: Use existing example profiles when possible

**Test Structure:**

1. Import test_helpers first (handles UTF-8 encoding and paths)- NPC JSON validation- NPC tests: Create temporary NPC profiles, clean up after

2. Import modules to test

3. Write test functions with clear assertions- Items registry validation

4. Include comprehensive error handling

5. Print success/failure messages with ✓/✗ symbols- Party configuration validation## Examples



**Best Practices:**- Cross-reference consistency checking

- Use `assert` statements for validation

- Print descriptive messages for test progress**Good Test:**

- Clean up test data after runs (if creating files)

- Test both success and failure cases### AI Integration Tests (`tests/ai/`)```python

- Include edge cases and boundary conditions

- AI client configuration# test_story_creation_workflow.py

## 🛠️ Test Infrastructure

- Environment variable handling"""

### test_helpers.py

Provides common test utilities:- AI-enhanced featuresVerify story creation workflow:

- **UTF-8 encoding configuration** for Windows console (fixes ✓/✗ display)

- **Project path setup** for imports- Fallback behavior1. Create test campaign

- **Returns project_root** for path calculations

2. Generate story file

Usage:

```python### Character System Tests (`tests/characters/`)3. Verify git ignores story files

import test_helpers

project_root = test_helpers.setup_test_environment()- Character profile management4. Clean up test data

```

- Character consultant functionality"""

### run_all_tests.py

Unified test runner with:- DC calculations

- Test discovery by category

- Subprocess execution for isolation- Class-specific features# Test implementation with cleanup

- Formatted output with pass/fail indicators

- Error reporting with stdout/stderr capturetry:

- Summary statistics

### NPC System Tests (`tests/npcs/`)    # ... test code ...

Features:

- Run all tests: `python tests/run_all_tests.py`- NPC profile management    print("SUCCESS: All tests passed")

- Run specific category: `python tests/run_all_tests.py validation`

- Returns exit code 0 (success) or 1 (failure)- NPC auto-detectionfinally:



### .pylintrc- NPC agents    # Clean up test campaign folder

Test-specific pylint configuration that disables:

- `wrong-import-position` - Necessary pattern for test path setup    if os.path.exists(test_path):

- `wrong-import-order` - Acceptable in test files

- `duplicate-code` - Expected test boilerplate similarity### Story Management Tests (`tests/stories/`)        shutil.rmtree(test_path)



These are legitimate test-specific exceptions properly documented.- Story creation and series management```



## 📊 Test Categories- Story analysis



### Validation Tests (Complete)- Character consistency checking**Test Checklist:**

- Character JSON schema validation

- NPC JSON schema validation  - Story file operations- [ ] Clear test purpose documented

- Items registry validation

- Party configuration validation- [ ] Expected outcomes defined

- Cross-reference consistency checks

- Error detection verification### Combat System Tests (`tests/combat/`)- [ ] Cleanup code included



### AI Tests (Complete)- Combat narration- [ ] Actual behavior verified (not just programmatic)

- Environment configuration validation

- Ollama connection testing- FGU combat log conversion- [ ] Test data removed after run

- Model availability verification

- Narrative styles

### Pending Test Categories (TODO)

- **Characters**: CharacterProfile, CharacterConsultant, class knowledge- Combat-to-story appending## Future Plans

- **NPCs**: NPC agents, auto-detection, profile management

- **Stories**: Story manager, file operations, hooks generation

- **Combat**: Combat narrator, FGU conversion, action descriptions

- **Items**: Item registry, custom item validation### Items System Tests (`tests/items/`)When test framework is formalized (see TODO.md):

- **DM**: DM consultant, history check helper

- **Utils**: Spell highlighting, text formatting, path utilities- Custom items registry- Tests will be migrated to proper test structure

- **CLI**: Interactive CLI, command workflows

- **Integration**: End-to-end user workflows, multi-system tests- Item validation- Framework will be chosen (pytest, unittest, etc.)



## 🎨 Test Output- Tests will be committed to repository



Tests use UTF-8 symbols for clear visual feedback:### DM Tools Tests (`tests/dm/`)- CI/CD integration may be added

- ✅ PASSED - Test succeeded

- ❌ FAILED - Test failed- DM consultant features

- ✓ - Individual assertion passed

- ✗ - Individual assertion failed- History check helpersUntil then, keep tests local and git-ignored.

- ⚠ - Warning or optional check



All tests properly handle Windows console encoding issues.### Utils Tests (`tests/utils/`)

- Text formatting

## 📈 Adding New Test Categories- Spell highlighting

- Markdown utilities

When creating tests for a new module:- File I/O utilities



1. Create test file in appropriate category folder### CLI Tests (`tests/cli/`)

2. Follow the test template structure- CLI interface functionality

3. Import test_helpers for environment setup- Menu navigation

4. Write descriptive test functions- User interactions

5. Include comprehensive assertions

6. Add error handling and cleanup### Integration Tests (`tests/integration/`)

7. Test file should be executable directly- End-to-end workflows

8. Verify 10.00/10 pylint score- Cross-module interactions

- Complete user scenarios

Example:

```powershell## ✅ Test Status

# Create new test

cd tests/stories### Currently Available Tests:

# Write test_story_creation.py- ✅ Validation tests (5 files)

- ✅ AI configuration test (1 file)

# Run test directly

python tests/stories/test_story_creation.py### To Be Created:

- ⏳ Character system tests

# Run through test runner- ⏳ Story management tests

python tests/run_all_tests.py stories- ⏳ Combat system tests

- ⏳ Integration tests

# Check pylint- ⏳ And more...

cd tests

python -m pylint stories/test_story_creation.py## 📝 Test Guidelines

```

1. **Naming Convention**: All test files must start with `test_`

## 🔍 Troubleshooting2. **Structure**: Mirror the `src/` directory structure

3. **Independence**: Tests should be independent and not rely on execution order

**Unicode encoding errors:**4. **Cleanup**: Tests should clean up any temporary files/data they create

- Make sure test imports test_helpers5. **Documentation**: Include docstrings explaining what each test validates

- Verify test_helpers.setup_test_environment() is called

- Check that UTF-8 configuration is working## 🛠️ Creating New Tests



**Import errors:**### Template for New Test File:

- Verify sys.path.insert() before importing test_helpers```python

- Check that project root is correctly calculated"""

- Ensure src modules use proper import pathsTests for [Feature Name].



**Test runner issues:**This module tests [brief description of what's being tested].

- Run from project root: `python tests/run_all_tests.py`"""

- Check that test files are executable

- Verify __init__.py files exist in test categoriesimport unittest

import sys

**Pylint issues:**from pathlib import Path

- Run pylint from tests directory: `cd tests; python -m pylint file.py`

- Check .pylintrc is being loaded# Add project root to path

- Verify no inline pylint disable comments (use configuration instead)project_root = Path(__file__).parent.parent.parent

sys.path.insert(0, str(project_root))

## 📚 Related Documentation

from src.module import FeatureClass

- [JSON Validation](../docs/JSON_Validation.md) - Validator schemas and usage

- [Validator Integration](../docs/Validator_Integration.md) - Integration guide

- [Copilot Instructions](../.github/copilot-instructions.md) - Project overviewclass TestFeature(unittest.TestCase):

- [TODO](../TODO.md) - Testing roadmap and priorities    """Test cases for [Feature Name]."""


    def setUp(self):
        """Set up test fixtures."""
        pass

    def tearDown(self):
        """Clean up after tests."""
        pass

    def test_basic_functionality(self):
        """Test basic feature functionality."""
        # Arrange
        # Act
        # Assert
        pass


if __name__ == "__main__":
    unittest.main()
```

## 📊 Test Results

Test results are documented in `test_results.md` after each test run.

## 🔍 CI/CD Integration

The `run_all_tests.py` script is designed for easy CI/CD integration:
- Returns exit code 0 on success, 1 on failure
- Provides clear summary output
- Supports selective test execution

---

**Last Updated:** October 18, 2025  
**Status:** Test structure reorganization complete, ready for Phase 3 testing
