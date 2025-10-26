# Combat Subsystem Tests

This folder contains unit and integration tests for the combat-to-narrative
pipeline: AI-enhanced narration, action description formatting, and
consistency checks that ensure character actions match profiles.

## Tests included
- `test_narrator_descriptions.py` — unit tests for `CombatDescriptor` (damage
  buckets, attack/spell/healing/status phrasing).
- `test_narrator_ai.py` — integration tests for `AIEnhancedNarrator` using the
  shared `FakeAIClient` and real character fixtures (aragorn, frodo, gandalf).
- `test_narrator_consistency.py` — tests for `ConsistencyChecker` (uses
  `FakeConsultant` from `tests/test_helpers.py`).
- `test_combat_conversion.py` — simulates parsed combat actions and verifies
  conversion to readable narrative fragments.
- `test_combat_narrator.py` — higher-level tests for `CombatNarrator` and
  fallback/title extraction behavior.

## How to run
From the project root run the combat aggregator which runs the group:

```powershell
python -m tests.combat.test_all_combat
python tests\run_all_tests.py combat
```

Or run an individual test module:

```powershell
python -m tests.combat.test_narrator_descriptions
```

## Conventions and patterns
- Tests use `tests/test_helpers.py` for shared test doubles: `FakeAIClient`,
  `FakeConsultant`, and `setup_test_environment()`.
- Use real character JSON fixtures in `game_data/characters/` for realistic
  behavior without stubbing profiles.
- Maintain a `10.00/10` pylint score for test files; do not add `# pylint: disable`.
- Keep tests small and focused: unit tests for `CombatDescriptor`, lightweight
  integration tests for AI path using the fake client, and conversion tests
  that exercise parsed-action -> narrative flow.

## Source modules under test
- `src/combat/narrator_descriptions.py` — action-to-text logic
- `src/combat/narrator_ai.py` — AI prompt building, RAG lookup, post-processing
- `src/combat/narrator_consistency.py` — consistency checking and notes
- `src/combat/combat_narrator.py` — high-level orchestration of components

## Notes
- Prefer using `FakeAIClient` to exercise AI flows deterministically. The
  fake client echoes a short preview of `messages` it receives which tests
  can assert against to verify prompt contents.
- Keep narrative outputs trimmed to 80 characters per line when asserting
  on formatted output in tests.
