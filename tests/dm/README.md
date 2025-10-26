# DM Subsystem Tests

This folder contains unit tests for the Dungeon Master (DM) subsystem.
The DM subsystem provides narrative generation, consistency checking, and
integration points for AI and the RAG (retrieval-augmented generation) system.

## Tests included
- `test_dungeon_master.py` — high-level tests for `DMConsultant` interfaces.
- `test_history_check_helper.py` — tests for history/context helpers used by the DM.
- `test_suggest_narrative_with_character_insights.py` — verifies character
  consultant insight integration in narrative suggestions.
- `test_generate_narrative_with_ai_client_and_rag.py` — exercises the AI branch
  of narrative generation and ensures RAG context is included when available.
- `test_check_consistency_relationships.py` — ensures consistency notes include
  NPC-character relationship evidence.

## How to run
From the project root run the DM aggregator which runs the group:

```powershell
python tests\run_all_tests.py dm
```

## Conventions and patterns
- Tests use `tests/test_helpers.py` for shared test doubles and environment
  setup: `setup_test_environment()`, `FakeAIClient`, `FakeConsultant` and helpers.
- Tests should mock external systems (AI clients, RAG) with deterministic
  fakes so runs are repeatable and do not call external services.
- Use temporary directories for file-based fixtures to avoid mutating
  repository data.
- Maintain a `10.00/10` pylint score for test files; do not add
  `# pylint: disable` comments — fix issues explicitly.
- Follow the project's "no emojis in .py/.md files" rule to avoid encoding issues
  on Windows consoles.

## Source modules under test
- `src/dm/dungeon_master.py` — DMConsultant and narrative suggestion APIs.
- `src/dm/history_check_helper.py` — helper functions for history/context checks.

## Notes
- RAG is a cross-cutting component; the DM tests mock or stub the RAG
  interface rather than re-testing RAG internals (those are covered by
  `tests/ai/test_rag_system.py`).
- Use `FakeAIClient` from `tests/test_helpers.py` for deterministic chat
  completions; the DM tests often rely on the fake's `msg_preview` field.
- Prefer exercising public APIs (e.g., `DMConsultant.suggest_narrative`) over
  reaching into protected members when possible.

If you'd like, I can add a short example of a failing AI/RAG scenario test or
wire this README into the top-level `tests/README.md` navigation.
