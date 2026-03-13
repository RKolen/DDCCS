# D&D Character Consultant System - Test Suite

This directory contains tests for the D&D Character Consultant
System. Tests mirror the modular src/ directory structure.

## Purpose

Store testing scripts created during development to:

- Verify feature functionality
- Test integration between components
- Validate end-to-end workflows
- Quick validation during development

## Test Directory Structure

```
tests/
|-- ai/              # Tests for src/ai/
|-- characters/      # Tests for src/characters/ (consultants, sheets, consistency)
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
`-- test_runner_common.py  # Common runner infrastructure
```

## Test Quality Standards

- All test files: 10.00/10 pylint
- Test runner: 10.00/10 pylint
- UTF-8 encoding configured for Windows console
- Comprehensive error detection tests

## Running Tests

Tests are run from the workspace root:

```bash
# Run all tests
python3 tests/run_all_tests.py

# Run specific category or categories
python3 tests/run_all_tests.py validation
python3 tests/run_all_tests.py ai characters
python3 tests/run_all_tests.py stories
```

It is not possible to run a single test with a command due to pathing
of the test_helpers. A workaround is to go into the test_all_[categoryname].py
and comment out all tests you do not want to run.

## Related Documentation

- JSON Validation docs: ../docs/JSON_Validation.md
- AI Integration: ../docs/AI_INTEGRATION.md
- RAG Integration: ../docs/RAG_INTEGRATION.md
- Copilot Instructions: ../.github/copilot-instructions.md
- TODO: ../TODO.md
