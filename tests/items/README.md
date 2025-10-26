````markdown
# Items Subsystem Tests

This folder contains unit tests for the items registry and item-related APIs.
The items subsystem is responsible for tracking homebrew/custom items that
should not be looked up on external wikis and for exposing those items to the
rest of the system.

## Tests included
- `test_item_registry.py` — verifies that the committed `custom_items_registry.json`
  and repository `custom_items.json` fallback are loaded and exposed via the API.
- `test_item_registry_precedence.py` — ensures entries in the explicit registry
  file take precedence over conflicting entries in the fallback `custom_items.json`.
- `test_item_registry_fallback_only.py` — ensures fallback-only items are loaded
  when no explicit registry file exists.
- `test_item_registry_api.py` — tests public API surface (`get_item`, `is_custom`,
  `get_all_custom_items`) for registered and non-registered items.

## How to run
From the project root run the items aggregator which runs the group:

```powershell
python tests\run_all_tests.py items
```

## Conventions and patterns
- Tests use `tests/test_helpers.py` for shared test doubles and environment
  setup: `setup_test_environment()`, `FakeAIClient`, `FakeConsultant` (where needed).
- Tests create temporary directories for file-based fixtures using
  `tempfile.TemporaryDirectory()` so they do not modify repository data.
- Maintain a `10.00/10` pylint score for test files; do not add `# pylint: disable`.
- Keep tests small and focused: file-loading, precedence, API behavior, and
  resilience to missing/malformed files.

## Source modules under test
- `src/items/item_registry.py` — registry loading, fallback handling, API helpers
  (`is_custom`, `get_item`, `get_all_custom_items`, `save_registry`).

## Notes
- The repository includes a `game_data/items/custom_items.json` file used as a
  convenient fallback in tests and examples. The `ItemRegistry` treats entries
  in `custom_items_registry.json` as authoritative and uses `custom_items.json`
  only as a non-authoritative fallback.
- Tests intentionally avoid writing to the repository `custom_items_registry.json`.
  Use temporary directories and pass a `registry_path` pointing at the temp dir.

````