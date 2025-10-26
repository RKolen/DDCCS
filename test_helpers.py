"""Top-level shim removed.

This project formerly shipped a small top-level `test_helpers.py` shim to
help tests import helpers when run from the repository root. We no longer
use a root-level helper; please import the canonical module at
`tests.test_helpers` instead.

Any attempt to import this module will raise so the developer notices and
fixes imports to use the package-local helper.
"""
raise ImportError(
    "Top-level `test_helpers` shim removed; import `tests.test_helpers` instead."
)
