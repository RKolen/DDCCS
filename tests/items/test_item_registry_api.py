"""Tests for ItemRegistry public API: get_item and is_custom.

Verifies that items written to an explicit registry file are exposed via
`is_custom`, `get_item`, and `get_all_custom_items`. Also checks that
non-registered items return False/None as expected.
"""

import json
import os
import tempfile
import test_helpers

# Configure test environment for imports
test_helpers.setup_test_environment()

try:
    from src.items.item_registry import ItemRegistry
except ImportError as exc:
    print(f"[ERROR] Import failed: {exc}")
    raise


def test_get_item_and_is_custom_api():
    """Ensure get_item and is_custom behave correctly for registered and unregistered items."""
    with tempfile.TemporaryDirectory() as tmpdir:
        registry_path = os.path.join(tmpdir, "custom_items_registry.json")

        # Prepare registry JSON with two items
        registry_data = {
            "Registry Shield": {
                "name": "Registry Shield",
                "item_type": "armor",
                "is_magic": False,
                "description": "A sturdy shield from the test registry",
                "properties": {"ac": "+2"},
                "notes": "Test registry shield",
            },
            "Registry Ring": {
                "name": "Registry Ring",
                "item_type": "magic_item",
                "is_magic": True,
                "description": "A ring present in registry",
                "properties": {"bonus": "+1"},
                "notes": "Test registry ring",
            },
        }

        with open(registry_path, "w", encoding="utf-8") as fh:
            json.dump(registry_data, fh)

        registry = ItemRegistry(registry_path=registry_path)

        # Registered items
        assert registry.is_custom("Registry Shield")
        shield = registry.get_item("Registry Shield")
        assert shield is not None
        assert shield.item_type == "armor"
        assert shield.is_magic is False

        assert registry.is_custom("Registry Ring")
        ring = registry.get_item("Registry Ring")
        assert ring is not None
        assert ring.is_magic is True

        # Non-registered item
        assert not registry.is_custom("Nonexistent Blade")
        assert registry.get_item("Nonexistent Blade") is None

        # get_all_custom_items contains both
        all_names = {itm.name for itm in registry.get_all_custom_items()}
        assert "Registry Shield" in all_names and "Registry Ring" in all_names
