# Story System Tests

This folder contains tests for the story management and analysis subsystem.

## Overview

The story system handles sequence management, file operations, story parsing,
spell highlighting, DC suggestion extraction, and integration with character
consultants for consistency analysis.

## Test Files

Below is a short description of the key test modules in this directory.

- **test_story_file_manager.py**
  - Tests story series and story file creation (numbering, sequencing)
  - Verifies pure (custom) story file creation and content writing
  - Uses TemporaryDirectory to avoid modifying repository data

- **test_story_manager.py**
  - High-level StoryManager tests (initialization, create story, series)
  - Exercises character loading and analyzer wiring via StoryManager

- **test_story_analyzer.py**
  - Tests `StoryAnalyzer.analyze_story_file` behavior (missing file, simple story, empty file)
  - Uses real character JSON profiles in `game_data/characters` to validate detection

- **test_character_consistency_integration.py**
  - Integration tests validating that the story -> analyzer -> consultant
    pipeline detects in-character vs out-of-character actions (uses Frodo profile)

- **test_hooks_and_analysis.py**
  - Tests story hooks generation and analysis helpers

- **test_story_updater.py**
  - Tests appending analysis to story files and update formatting

- **test_session_results_manager.py**
  - Tests session results recording and markdown generation

- **test_story_character_loader.py**
  - Tests character loading for the story manager (reads `game_data/characters`)

- **test_enhanced_story_manager.py**
  - Advanced integration tests for the enhanced story manager features (campaign-aware)

- **test_all_stories.py**
  - Runner that executes the story-related tests in sequence and summarizes results

## Why We Test This

The story subsystem is central to user workflows (writing narrative, auto-detecting
NPCs, suggesting DCs, tracking character development). Tests validate:

1. File operations produce stable, predictable filenames and templates.
2. Story parsing reliably extracts character actions and DC requests.
3. Integration with character consultants yields sensible consistency analysis.
4. Story update operations append analysis without corrupting content.

## Running Tests

Run the entire stories test suite with the repository test runner:

```powershell
python tests/run_all_tests.py stories
```

> Note: tests use `test_helpers.setup_test_environment()` to ensure `src` imports
> resolve correctly. Run from the project root to avoid import errors.

## Test Coverage

The stories suite focuses on:
- File I/O and naming conventions
- Story parsing utilities (character action extraction, DC extraction)
- Integration with character consultants (consistency analysis)
- Story update and session result generation

## What's Not Tested

- Live AI responses and external web requests (RAG lookups) — those belong to the
  AI tests and are mocked or skipped by design.
- Performance under extremely large story files (future enhancement)

## Quality Standards

All tests in this folder follow the project's test standards:
- Use `tempfile.TemporaryDirectory()` for filesystem tests
- No writes to the repository `game_data` folder (except reading example profiles)
- Clear docstrings and descriptive assertions
- Keep tests deterministic and idempotent

## Troubleshooting

- Import errors: ensure you're running from the project root and `test_helpers`
  has been imported at the top of the test file.
- Missing character profiles: ensure `game_data/characters` contains example
  profiles (Aragorn, Frodo, Gandalf) used by analyzer tests.

## Maintenance

When adding or changing tests here:
1. Add a short description to this README under "Test Files".
2. Keep tests small and focused (happy path + 1-2 edge cases).
3. Use existing helpers in `tests/test_helpers.py` for import wiring.
