# Sessions Tests

Tests for the `src/sessions/` package, which provides structured session
notes management for D&D campaigns.

## What Is Tested

| File | Module | Coverage |
|------|--------|----------|
| `test_session_notes.py` | `src/sessions/session_notes.py` | Data structures, serialization |
| `test_session_notes.py` | `src/sessions/session_notes_manager.py` | CRUD, timeline, context |
| `test_session_notes.py` | `src/stories/story_ai_generator.py` | `build_story_prompt_with_session_context` |

## Running Tests

```bash
# All sessions tests
python3 tests/run_all_tests.py sessions

# Single file
python3 -m tests.sessions.test_session_notes
```

## Test Standards

All tests reach 10.00/10 Pylint score with no disable comments.
