# D&D Character Consultant System - Test Suite

This directory contains tests for the D&D Character Consultant
System. Tests mirror the modular src/ directory structure.

## Important Notes

- **Tests are NOT committed to git** - They remain local only
- Tests stay git-ignored until formal test framework is added
- This prevents accidental commits of development tests

## Purpose

Store testing scripts created during development to:
- Verify feature functionality
- Test integration between components
- Validate end-to-end workflows
- Quick validation during development

## Test Directory Structure (41 tests across 11 files)

All tests achieve 10.00/10 pylint score.

## Test Quality Standards

- All test files: 10.00/10 pylint
- Test runner: 10.00/10 pylint
- UTF-8 encoding configured for Windows console
- Comprehensive error detection tests

## Running Tests

`Bash
python tests/run_all_tests.py
python tests/run_all_tests.py validation
python tests/run_all_tests.py ai characters
python tests/validation/test_character_validator.py
`

## Related Documentation

- JSON Validation docs: ../docs/JSON_Validation.md
- Validator Integration: ../docs/Validator_Integration.md
- Copilot Instructions: ../.github/copilot-instructions.md
- TODO: ../TODO.md

---

**Last Updated:** October 19, 2025
**Status:** Characters 5/9, all tests 10.00/10 pylint
