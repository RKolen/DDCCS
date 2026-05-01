# Calendar Tests

Tests for `src/calendar/` - in-world date tracking and calendar engine.

## What is tested

- `CalendarEngine` - calendar definition loading, season/holiday/weekday
  detection, date arithmetic, formatting, and round-trip ordinal conversion
- `DateTracker` - per-campaign current date persistence, advance/retreat,
  AI prompt context generation, and preservation of existing timeline events

## Test files

| File | Purpose |
|------|---------|
| `test_calendar_engine.py` | CalendarEngine unit tests (generic + Forgotten Realms) |
| `test_date_tracker.py` | DateTracker unit tests with isolated temp workspaces |
| `test_all_calendar.py` | Aggregator that runs both modules |

## Running

```bash
# Run all calendar tests
python3 tests/run_all_tests.py calendar

# Run a single file
python3 -m tests.calendar.test_calendar_engine
```

## Test data

Tests use actual calendar definitions from `game_data/calendars/`.
`test_date_tracker.py` copies those files into an isolated `tempfile` workspace
per test so no campaign data is written to the real `game_data/` directory.
