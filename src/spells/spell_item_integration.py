"""Integration between custom spells and the magic item registry.

Provides SpellItemLink to record which items cast or rely on spells,
and SpellItemIntegration to manage those relationships.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from src.items.item_registry import ItemRegistry
from src.spells.spell_registry import CustomSpell, SpellCasting, SpellMeta, get_spell_registry


@dataclass
class SpellItemLinkDetails:
    """Optional details for a spell-item relationship.

    Groups the optional fields of SpellItemLink so the parent
    dataclass stays within the instance-attribute limit.

    Attributes:
        link_type: Relationship kind: 'casts', 'contains', 'enhances', 'requires'.
        charges: Charges consumed per cast (0 if not applicable).
        description: Free-text description of the relationship.
    """

    link_type: str = "casts"
    charges: int = 0
    description: str = ""


@dataclass
class SpellItemLink:
    """Records a relationship between a magic item and a spell.

    Attributes:
        item_name: Name of the magic item.
        spell_name: Name of the spell.
        details: Optional relationship details (type, charges, description).
    """

    item_name: str
    spell_name: str
    details: SpellItemLinkDetails


class SpellItemIntegration:
    """Manages relationships between spells and magic items."""

    def __init__(self) -> None:
        """Initialize with the singleton spell registry and a fresh item registry."""
        self.spell_registry = get_spell_registry()
        self.item_registry = ItemRegistry()
        self._links: Dict[str, List[SpellItemLink]] = {}

    def link_spell_to_item(
        self,
        item_name: str,
        spell_name: str,
        details: Optional[SpellItemLinkDetails] = None,
    ) -> SpellItemLink:
        """Create a link between a spell and an item.

        If the spell does not exist in the registry a minimal entry is
        created automatically so that it can be highlighted.

        Args:
            item_name: Name of the magic item.
            spell_name: Name of the spell.
            details: Optional relationship details (type, charges, description).
                Defaults to a 'casts' link with no charges.

        Returns:
            The created SpellItemLink.
        """
        link = SpellItemLink(
            item_name=item_name,
            spell_name=spell_name,
            details=details or SpellItemLinkDetails(),
        )
        self._links.setdefault(item_name, []).append(link)

        if not self.spell_registry.has_spell(spell_name):
            spell = CustomSpell(
                name=spell_name,
                level=0,
                school="unknown",
                description=f"Spell cast by {item_name}",
                casting=SpellCasting(),
                meta=SpellMeta(source="item"),
            )
            self.spell_registry.add_spell(spell)

        return link

    def get_spells_for_item(self, item_name: str) -> List[CustomSpell]:
        """Get all spells associated with an item.

        Args:
            item_name: Name of the item.

        Returns:
            List of CustomSpell instances linked to the item.
        """
        spells = []
        for link in self._links.get(item_name, []):
            spell = self.spell_registry.get_spell(link.spell_name)
            if spell:
                spells.append(spell)
        return spells

    def get_items_for_spell(self, spell_name: str) -> List[str]:
        """Get all item names that use a specific spell.

        Args:
            spell_name: Name of the spell.

        Returns:
            List of item names that reference this spell.
        """
        spell_lower = spell_name.lower()
        return [
            item_name
            for item_name, links in self._links.items()
            if any(lnk.spell_name.lower() == spell_lower for lnk in links)
        ]

    def import_from_items(self) -> int:
        """Scan the item registry for spell references and auto-register them.

        Looks for item properties named 'spell', 'spells', 'casts',
        'contains_spell', 'spell_effect', or 'grants_spell'.

        Returns:
            Number of new spells imported.
        """
        imported = 0
        spell_props = {
            "spell", "spells", "casts",
            "contains_spell", "spell_effect", "grants_spell",
        }

        for item in self.item_registry.get_all_custom_items():
            item_dict = item.to_dict()
            item_name = item_dict.get("name", "")
            properties: Dict = item_dict.get("properties", {})

            for prop in spell_props:
                if prop not in properties:
                    continue
                for spell_name in _extract_spell_names(properties[prop]):
                    if not self.spell_registry.has_spell(spell_name):
                        spell = CustomSpell(
                            name=spell_name,
                            level=0,
                            school="unknown",
                            description=f"Spell from {item_name}",
                            casting=SpellCasting(),
                            meta=SpellMeta(source="item"),
                        )
                        self.spell_registry.add_spell(spell)
                        imported += 1
                    self.link_spell_to_item(
                        item_name=item_name,
                        spell_name=spell_name,
                    )
        return imported


def _extract_spell_names(value: object) -> List[str]:
    """Extract a list of spell name strings from an item property value.

    Args:
        value: String, list, or other JSON value.

    Returns:
        List of non-empty spell name strings.
    """
    if isinstance(value, str):
        return [s.strip() for s in value.split(",") if s.strip()]
    if isinstance(value, list):
        return [str(s).strip() for s in value if s]
    return []


# Module-level mutable list used as a singleton holder (avoids global-statement
# warnings and the too-few-public-methods issue of a private holder class).
_integration_holder: List[SpellItemIntegration] = []


def get_spell_item_integration() -> SpellItemIntegration:
    """Return the singleton SpellItemIntegration instance.

    Returns:
        The global SpellItemIntegration.
    """
    if not _integration_holder:
        _integration_holder.append(SpellItemIntegration())
    return _integration_holder[0]


def reset_spell_item_integration() -> None:
    """Reset the singleton (used in tests)."""
    _integration_holder.clear()
