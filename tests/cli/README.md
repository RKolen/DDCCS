# CLI Subsystem Tests

This folder contains unit tests for the command-line interface (CLI) layer of
the D&D Character Consultant System. The CLI layer wires together story
management, character management, consultations, and DM/story analysis
features into an interactive and a non-interactive API.

## Tests included
- `test_dnd_consultant.py` — tests for `DDConsultantCLI` non-interactive commands.
- `test_setup.py` — tests for CLI setup utilities (VSCode tasks/settings creation).
- `test_cli_character_manager.py` — tests for `CharacterCLIManager` display/listing behavior.
- `test_cli_story_manager.py` — tests for story manager helpers and display logic.
- `test_cli_consultations.py` — tests for consultations flows (DM narrative prompts).
- `test_cli_story_analysis.py` — tests for story analysis and combat conversion flows.

## How to run
From the project root run the CLI aggregator which runs the group:

```powershell
python tests\run_all_tests.py cli
```

Or run a single test module directly (PowerShell):

```powershell
python -m cli.test_cli_consultations
```

## Conventions and patterns
- Tests use `tests/test_helpers.py` for shared fakes and environment setup.
- Avoid calling external services (AI/RAG) — use fakes or monkeypatching for deterministic behavior.
- Avoid interactive blocking in tests: monkeypatch `builtins.input` when needed.
- Use `tempfile` or `tmp_path` fixtures for filesystem operations so repository data is not modified.
- Keep tests small and focused and maintain a `10.00/10` pylint score for test files.

## Source modules under test
- `src/cli/dnd_consultant.py` — main CLI entrypoint and interactive loop.
- `src/cli/cli_character_manager.py` — character management menus and display helpers.
- `src/cli/cli_story_manager.py` — story management menus and file operations.
- `src/cli/cli_consultations.py` — consultation flows (character/DC/DM suggestions).
- `src/cli/cli_story_analysis.py` — story analysis and combat conversion helpers.

## Notes
- Tests provide coverage for CLI logic, not for deep StoryManager or DM logic — those are covered in subsystem tests. CLI tests focus on wiring, input parsing, and display behavior.
- If you'd like, I can add a short example showing how to run an individual CLI test module and interpret output.
