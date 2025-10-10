"""
Equipment and Item Management System with RAG Integration
Handles distinction between official D&D items and homebrew content
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import json
import os


@dataclass
class Item:
    """
    Represents a custom/homebrew item.
    
    NOTE: Items in custom_items_registry.json are ALWAYS custom/homebrew.
    Being in this registry means: do NOT lookup on wikidot.
    Official D&D items should NOT be added to this registry.
    """
    name: str
    item_type: str  # weapon, armor, gear, magic_item, consumable, tool, etc.
    is_magic: bool = False  # Whether this is a magic item
    description: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "item_type": self.item_type,
            "is_magic": self.is_magic,
            "description": self.description,
            "properties": self.properties,
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Item':
        """Create Item from dictionary"""
        return cls(
            name=data.get("name", ""),
            item_type=data.get("item_type", "gear"),
            is_magic=data.get("is_magic", False),
            description=data.get("description", ""),
            properties=data.get("properties", {}),
            notes=data.get("notes", "")
        )


class ItemRegistry:
    """
    Registry for tracking custom/homebrew items.
    
    IMPORTANT: This registry ONLY contains custom/homebrew items.
    All items in this registry will NOT be looked up on wikidot.
    Official D&D items are not registered here - they're looked up directly.
    """
    
    def __init__(self, registry_path: str = "game_data/items/custom_items_registry.json"):
        self.registry_path = registry_path
        self.items: Dict[str, Item] = {}
        self._load_registry()
    
    def _load_registry(self):
        """Load item registry from file"""
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item_name, item_data in data.items():
                        self.items[item_name] = Item.from_dict(item_data)
            except Exception as e:
                print(f"Warning: Could not load item registry: {e}")
    
    def save_registry(self):
        """Save item registry to file"""
        try:
            data = {name: item.to_dict() for name, item in self.items.items()}
            with open(self.registry_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving item registry: {e}")
    
    def register_item(self, item: Item):
        """Register an item in the registry"""
        self.items[item.name] = item
        self.save_registry()
    
    def is_custom(self, item_name: str) -> bool:
        """
        Check if an item is in the custom registry.
        
        Returns:
            True if item is in the custom registry (do NOT lookup on wikidot)
            False if item is not in registry (assume official, CAN lookup)
        """
        return item_name in self.items
    
    def can_lookup_on_wiki(self, item_name: str) -> bool:
        """
        Determine if this item should be looked up on wikidot.
        
        Returns:
            False if item is in custom registry (homebrew - do NOT lookup)
            True if item is NOT in registry (official - CAN lookup)
        """
        # If item is in the custom registry, it's homebrew - don't lookup
        return item_name not in self.items
    
    def get_item(self, item_name: str) -> Optional[Item]:
        """Get item information from custom registry (returns None if not custom/homebrew)"""
        return self.items.get(item_name)
    
    def add_custom_item(self, item: Item):
        """
        Add a custom/homebrew item to the registry.
        
        Items in this registry will NOT be looked up on wikidot.
        """
        self.items[item.name] = item
        self.save_registry()
    
    def remove_item(self, item_name: str):
        """Remove an item from the custom registry"""
        if item_name in self.items:
            del self.items[item_name]
            self.save_registry()
    
    def get_all_custom_items(self) -> List[Item]:
        """Get all custom/homebrew items in the registry"""
        return list(self.items.values())
    
    def get_magic_items(self) -> List[Item]:
        """Get all custom magic items"""
        return [item for item in self.items.values() if item.is_magic]
    
    def get_non_magic_items(self) -> List[Item]:
        """Get all custom non-magic items (equipment, tools, etc.)"""
        return [item for item in self.items.values() if not item.is_magic]





# Example usage and setup
if __name__ == "__main__":
    print("=== Custom Item Registry System ===\n")
    print("This registry ONLY tracks custom/homebrew items.")
    print("Official D&D items are NOT registered - they're looked up directly on wikidot.\n")
    
    # Create registry
    registry = ItemRegistry()
    
    # Example: Add a custom magic item
    custom_magic = Item(
        name="Example Mystic Amulet",
        item_type="magic_item",
        is_magic=True,
        description="A magical amulet with ancient runes",
        properties={"rarity": "rare", "attunement": True},
        notes="Provides +1 to AC while attuned"
    )
    registry.add_custom_item(custom_magic)
    print(f"✅ Added custom magic item: {custom_magic.name}")
    
    # Example: Add custom non-magic equipment
    custom_gear = Item(
        name="Example Reinforced Backpack",
        item_type="gear",
        is_magic=False,
        description="A specially reinforced backpack with extra storage",
        properties={"capacity": "40 lbs", "weight": "3 lbs"},
        notes="Can hold 10 lbs more than standard backpack"
    )
    registry.add_custom_item(custom_gear)
    print(f"✅ Added custom gear: {custom_gear.name}")
    
    # Check if items can be looked up on wikidot
    print("\n" + "="*60)
    print("LOOKUP TESTS:")
    print("="*60)
    print(f"Can lookup 'Greataxe' (official): {registry.can_lookup_on_wiki('Greataxe')}")
    print(f"Can lookup '{custom_magic.name}' (custom): {registry.can_lookup_on_wiki(custom_magic.name)}")
    print(f"Can lookup 'Longsword' (official): {registry.can_lookup_on_wiki('Longsword')}")
    
    print("\n" + "="*60)
    print("REGISTRY CONTENTS:")
    print("="*60)
    print(f"\nTotal custom items: {len(registry.get_all_custom_items())}")
    
    print("\nCustom magic items:")
    for item in registry.get_magic_items():
        print(f"  - {item.name}: {item.description}")
    
    print("\nCustom non-magic items:")
    for item in registry.get_non_magic_items():
        print(f"  - {item.name}: {item.description}")
