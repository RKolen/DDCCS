"""Verify that when only the fallback `custom_items.json` is present,
ItemRegistry loads those items correctly.
"""

import json
import os
import tempfile

from tests import test_helpers

# Configure test environment for imports
test_helpers.setup_test_environment()

try:
    from src.items.item_registry import ItemRegistry
except ImportError as exc:
    print(f"[ERROR] Import failed: {exc}")
    raise


def test_load_fallback_only_items_present():
    """When no explicit registry exists, fallback file items should be loaded."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Prepare fallback path only (no registry file)
        fallback_path = os.path.join(tmpdir, "custom_items.json")

        # Item present only in fallback
        item_name = "Fallback-only Amulet"
        fallback_item = {
            item_name: {
                "name": item_name,
                "item_type": "magic_item",
                "is_magic": True,
                "description": "Only in fallback file",
                "properties": {"bonus": "+1"},
                "notes": "Fallback-only",
            }
        }

        # Write fallback JSON file
        with open(fallback_path, "w", encoding="utf-8") as fh:
            json.dump(fallback_item, fh)

        # Initialize ItemRegistry pointing to a non-existent registry path in the tmp dir
        registry_path = os.path.join(tmpdir, "custom_items_registry.json")
        registry = ItemRegistry(registry_path=registry_path)

        # The fallback item should be present via the registry's fallback loader
        assert registry.is_custom(item_name)
        loaded = registry.get_item(item_name)
        assert loaded is not None
        assert loaded.is_magic is True
        assert "Only in fallback" in loaded.description
