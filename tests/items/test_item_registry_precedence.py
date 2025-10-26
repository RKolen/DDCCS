"""Tests for precedence: explicit registry entries should override fallback custom_items.json.

This test creates a temporary directory with both a registry file and a
fallback `custom_items.json` file containing an item with the same name but
different properties. The `ItemRegistry` should prefer the explicit registry
file's entry.
"""

import json
import os
import tempfile

from tests import test_helpers

# Import ItemRegistry using centralized safe import
ItemRegistry = test_helpers.safe_from_import("src.items.item_registry", "ItemRegistry")


def test_load_precedence_registry_over_fallback():
    """Explicit registry entry must take precedence over the fallback file.

    Steps:
    - Create a temp directory
    - Write `custom_items_registry.json` with item X (registry version)
    - Write `custom_items.json` fallback with item X (fallback version)
    - Initialize ItemRegistry pointing at the temp registry file
    - Assert the loaded item matches the registry version, not the fallback
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Prepare file paths
        registry_path = os.path.join(tmpdir, "custom_items_registry.json")
        fallback_path = os.path.join(tmpdir, "custom_items.json")

        # Item name used for the precedence test
        item_name = "Fallback Sword"

        # Registry (authoritative) version of the item
        registry_item = {
            item_name: {
                "name": item_name,
                "item_type": "weapon",
                "is_magic": False,
                "description": "Registry version - mundane sword",
                "properties": {"damage": "1d8"},
                "notes": "From registry",
            }
        }

        # Fallback version of the same item (conflicting)
        fallback_item = {
            item_name: {
                "name": item_name,
                "item_type": "weapon",
                "is_magic": True,
                "description": "Fallback version - enchanted sword",
                "properties": {"damage": "1d8+1"},
                "notes": "From fallback",
            }
        }

        # Write both JSON files
        with open(registry_path, "w", encoding="utf-8") as fh:
            json.dump(registry_item, fh)
        with open(fallback_path, "w", encoding="utf-8") as fh:
            json.dump(fallback_item, fh)

        # Initialize ItemRegistry pointing at the temp registry file
        registry = ItemRegistry(registry_path=registry_path)

        # Ensure the item is present
        assert registry.is_custom(item_name)
        loaded = registry.get_item(item_name)
        assert loaded is not None

        # The loaded item should match the registry version (is_magic False)
        assert loaded.is_magic is False
        assert "Registry version" in loaded.description

        # Also verify that the fallback would have been different
        assert loaded.description != fallback_item[item_name]["description"]
