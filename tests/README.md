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

Tests are ran from root and can be run complete or as a suite(s):

`Bash
python tests/run_all_tests.py
python tests/run_all_tests.py validation
python tests/run_all_tests.py ai characters
`
It is not possible to run a single test with a command due to pathing
of the test_helpers. A workaround is to go into the test_all_[categoryname].py
and uncomment all tests you dont want to run. Example in test_all_characters.py:
`
    # Define all tests to run
    tests = [
      #  ("test_character_profile", "Character Profile Tests"),
      #  ("test_class_knowledge", "Class Knowledge Tests"),
      #  ("test_character_sheet", "Character Sheet Tests"),
      #  ("test_character_consistency", "Character Consistency Tests"),
        ("test_consultant_core", "Consultant Core Tests"),
      #  ("test_consultant_dc", "DC Calculator Tests"),
      #  ("test_consultant_story", "Story Analyzer Tests"),
      #  ("test_consultant_ai", "AI Consultant Tests"),
    ]
`
If you then run python tests/run_all_tests.py characters
it will only run the test_consultant_core.py test.

Especially the character and story tests are very long (they are almost 1,5 min
each). If you run (all) the tests be patient they are not stuck it just takes
a long time.

## Related Documentation

- JSON Validation docs: ../docs/JSON_Validation.md
- Validator Integration: ../docs/Validator_Integration.md
- Copilot Instructions: ../.github/copilot-instructions.md
- TODO: ../TODO.md

---

**Last Updated:** October 19, 2025
**Status:** Characters 5/9, all tests 10.00/10 pylint
