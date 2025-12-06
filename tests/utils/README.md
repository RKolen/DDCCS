## tests/utils — Utility module tests

This folder contains unit tests covering the small, commonly used helper
modules under `src/utils/`.

Purpose
- Verify deterministic behavior of pure utility functions used across the
  project (string normalization, file I/O helpers, markdown helpers, spell
  highlighting, validation helpers, and text formatting).
- Keep tests small, fast, and isolated from network or AI services by using
  fakes and `tmp_path` where filesystem access is required.

Files in this folder
- `test_all_utils.py` — aggregator that runs the utils tests as a group.
- `test_behaviour_generation.py` — heuristics for behavior generation.
- `test_cli_utils.py` — CLI helper functions (selection, input helpers).
- `test_dnd_rules.py` — DCs, modifiers, and proficiency logic.
- `test_file_io.py` — JSON and text read/write helpers and directory helpers.
- `test_markdown_utils.py` — update/extract markdown section helpers.
- `test_spell_highlighter.py` — spell detection/highlighting helpers.
- `test_story_formatting_utils.py` — formatting analysis results to markdown.
- `test_story_parsing_utils.py` — story parsing helpers (character actions, DC requests).
- `test_string_utils.py` — string utilities and normalization helpers.
- `test_text_formatting_utils.py` — text wrapping and optional spell highlighting.
- `test_validation_helpers.py` — validation helper functions and formatting.
- `test_story_file_helpers.py` - file helper for story functionality.

Running the tests
Use the repository test runner to execute the utils tests only (PowerShell):

```powershell
python .\tests\run_all_tests.py utils
```

Linting and style
- All test files must meet the project's lint standard (pylint score 10.00/10).
  The repository enforces this for test files and the CI expects no pylint
  disables in test modules.

Notes
- Tests use `tests/test_helpers.py` for shared setup and fakes. Import
  `test_helpers` and call `setup_test_environment()` before importing
  project modules in tests (this is already done in the test files here).
- Keep tests small and deterministic: monkeypatch `input()` where needed and
  avoid external network calls (use fakes/mocks instead).

If you want me to, I can:
- Run the utils aggregator now and paste the runtime output, or
- Add a short `tests/utils/README.md` section showing a quick example for
  adding new utils tests or templates for common patterns.
