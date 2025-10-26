"""Unit tests for `src.items.item_registry.ItemRegistry`.

These tests verify that the registry loads both the committed
`custom_items_registry.json` and the repository `custom_items.json`
fallback and exposes items via the public API.
"""

from tests import test_helpers

# Import ItemRegistry using centralized safe import
ItemRegistry = test_helpers.safe_from_import("src.items.item_registry", "ItemRegistry")


def test_registry_loads_registry_and_fallback():
    """ItemRegistry should load items from registry and fallback custom_items.json."""
    registry = ItemRegistry(registry_path="game_data/items/custom_items_registry.json")

    # Item present in explicit registry
    assert registry.is_custom("Test Mystic Amulet")
    item = registry.get_item("Test Mystic Amulet")
    assert item is not None
    assert item.item_type == "magic_item"

    # Item present only in the repo's custom_items.json fallback
    assert registry.is_custom("Ring of Barahir")
    ring = registry.get_item("Ring of Barahir")
    assert ring is not None
    assert ring.is_magic
