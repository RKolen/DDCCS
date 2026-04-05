"""Custom spell registry for homebrew and custom spells.

Manages a JSON-backed registry of custom/homebrew D&D spells with
indexing by school, level, class, and tag for fast lookup.
"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from src.utils.file_io import load_json_file, save_json_file
from src.utils.path_utils import get_game_data_path


@dataclass
class SpellComponents:
    """Spell components required for casting."""

    verbal: bool = False
    somatic: bool = False
    material: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of components.
        """
        return {
            "verbal": self.verbal,
            "somatic": self.somatic,
            "material": self.material,
        }

    @classmethod
    def from_dict(cls, data: object) -> "SpellComponents":
        """Create from a raw value (dict or anything from JSON).

        Args:
            data: Raw value from JSON; must be a dict to extract fields.

        Returns:
            SpellComponents instance.
        """
        if isinstance(data, dict):
            return cls(
                verbal=bool(data.get("verbal", False)),
                somatic=bool(data.get("somatic", False)),
                material=str(data.get("material", "")),
            )
        return cls()


@dataclass
class SpellCasting:
    """Casting mechanics for a spell.

    Groups casting_time, range, duration, and components so that
    CustomSpell stays within the instance-attribute limit.
    """

    casting_time: str = "1 action"
    range: str = "touch"
    duration: str = "instantaneous"
    components: SpellComponents = field(default_factory=SpellComponents)


@dataclass
class SpellMeta:
    """Provenance and display metadata for a spell.

    Groups source, tags, aliases, and priority so that CustomSpell
    stays within the instance-attribute limit.
    """

    source: str = "homebrew"
    source_reference: str = ""
    tags: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)
    highlight_priority: int = 1


@dataclass
class CustomSpell:
    """Represents a custom or homebrew spell.

    Attributes:
        name: Canonical spell name.
        level: Spell level (0 = cantrip).
        school: Magic school (e.g. 'necromancy').
        description: Spell description text.
        classes: Character classes that can use this spell.
        casting: Casting mechanics (time, range, duration, components).
        meta: Provenance and display metadata.
    """

    name: str
    level: int
    school: str
    description: str
    classes: List[str] = field(default_factory=list)
    casting: SpellCasting = field(default_factory=SpellCasting)
    meta: SpellMeta = field(default_factory=SpellMeta)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Flat dictionary matching the custom_spells.json schema.
        """
        return {
            "name": self.name,
            "level": self.level,
            "school": self.school,
            "description": self.description,
            "casting_time": self.casting.casting_time,
            "range": self.casting.range,
            "components": self.casting.components.to_dict(),
            "duration": self.casting.duration,
            "classes": self.classes,
            "source": self.meta.source,
            "source_reference": self.meta.source_reference,
            "tags": self.meta.tags,
            "highlight_priority": self.meta.highlight_priority,
            "aliases": self.meta.aliases,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CustomSpell":
        """Create from a flat registry dictionary.

        Args:
            data: Dictionary with spell fields from JSON.

        Returns:
            CustomSpell instance.
        """
        components = SpellComponents.from_dict(data.get("components", {}))
        casting = SpellCasting(
            casting_time=str(data.get("casting_time", "1 action")),
            range=str(data.get("range", "touch")),
            duration=str(data.get("duration", "instantaneous")),
            components=components,
        )
        meta = SpellMeta(
            source=str(data.get("source", "homebrew")),
            source_reference=str(data.get("source_reference", "")),
            tags=list(data.get("tags", [])),
            aliases=list(data.get("aliases", [])),
            highlight_priority=int(data.get("highlight_priority", 1)),
        )
        return cls(
            name=data["name"],
            level=int(data["level"]),
            school=str(data["school"]),
            description=str(data.get("description", "")),
            classes=list(data.get("classes", [])),
            casting=casting,
            meta=meta,
        )

    def get_all_names(self) -> Set[str]:
        """Get all names this spell might be known by.

        Returns:
            Set of all name variants (canonical + aliases).
        """
        names: Set[str] = {self.name, self.name.lower()}
        for alias in self.meta.aliases:
            names.add(alias)
            names.add(alias.lower())
        return names


class SpellRegistry:
    """Manages custom spell definitions backed by a JSON registry file."""

    def __init__(self) -> None:
        """Initialize the spell registry and load from disk."""
        self._spells: Dict[str, CustomSpell] = {}
        self._aliases: Dict[str, str] = {}
        self._by_school: Dict[str, List[str]] = {}
        self._by_level: Dict[int, List[str]] = {}
        self._by_class: Dict[str, List[str]] = {}
        self._by_tag: Dict[str, List[str]] = {}
        self._load_registry()

    @property
    def registry_path(self) -> Path:
        """Path to the custom_spells.json registry file.

        Returns:
            Absolute path to the registry file.
        """
        return Path(get_game_data_path()) / "spells" / "custom_spells.json"

    def _load_registry(self) -> None:
        """Load the custom spells registry from disk."""
        if not self.registry_path.exists():
            self._create_default_registry()
            return
        raw = load_json_file(str(self.registry_path))
        if raw is None:
            return
        try:
            self._parse_registry(raw)
        except (KeyError, ValueError, OSError):
            self._spells = {}

    def _create_default_registry(self) -> None:
        """Create a default empty registry file on disk."""
        default_data: Dict[str, Any] = {
            "registry_version": "1.0",
            "last_updated": "",
            "source": "homebrew",
            "spells": [],
            "spell_groups": [],
        }
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        save_json_file(str(self.registry_path), default_data)

    def _parse_registry(self, data: Dict[str, Any]) -> None:
        """Parse registry data into internal indexes.

        Args:
            data: Raw registry dictionary from JSON.
        """
        for spell_data in data.get("spells", []):
            try:
                spell = CustomSpell.from_dict(spell_data)
                self._add_spell_to_indexes(spell)
            except (KeyError, TypeError, ValueError):
                continue

    def _add_spell_to_indexes(self, spell: CustomSpell) -> None:
        """Add a spell to all internal lookup indexes.

        Args:
            spell: The spell to index.
        """
        self._spells[spell.name.lower()] = spell

        for alias in spell.get_all_names():
            self._aliases[alias.lower()] = spell.name

        self._by_school.setdefault(spell.school.lower(), []).append(spell.name)
        self._by_level.setdefault(spell.level, []).append(spell.name)

        for char_class in spell.classes:
            self._by_class.setdefault(char_class.lower(), []).append(spell.name)

        for tag in spell.meta.tags:
            self._by_tag.setdefault(tag.lower(), []).append(spell.name)

    def save_registry(self) -> None:
        """Persist the current registry state to disk."""
        data: Dict[str, Any] = {
            "registry_version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "source": "homebrew",
            "spells": [s.to_dict() for s in self._spells.values()],
            "spell_groups": [],
        }
        save_json_file(str(self.registry_path), data)

    def add_spell(self, spell: CustomSpell) -> None:
        """Add a new spell to the registry and persist to disk.

        Args:
            spell: The spell to add.
        """
        self._add_spell_to_indexes(spell)
        self.save_registry()

    def remove_spell(self, name: str) -> bool:
        """Remove a spell from the registry by name.

        Args:
            name: The spell name to remove.

        Returns:
            True if removed, False if not found.
        """
        name_lower = name.lower()
        if name_lower not in self._spells:
            return False

        spell = self._spells.pop(name_lower)

        for alias in spell.get_all_names():
            self._aliases.pop(alias.lower(), None)

        school_list = self._by_school.get(spell.school.lower(), [])
        if spell.name in school_list:
            school_list.remove(spell.name)

        level_list = self._by_level.get(spell.level, [])
        if spell.name in level_list:
            level_list.remove(spell.name)

        for char_class in spell.classes:
            class_list = self._by_class.get(char_class.lower(), [])
            if spell.name in class_list:
                class_list.remove(spell.name)

        for tag in spell.meta.tags:
            tag_list = self._by_tag.get(tag.lower(), [])
            if spell.name in tag_list:
                tag_list.remove(spell.name)

        self.save_registry()
        return True

    def get_spell(self, name: str) -> Optional[CustomSpell]:
        """Get a spell by name or alias.

        Args:
            name: Spell name or alias to look up.

        Returns:
            The matching CustomSpell, or None if not found.
        """
        name_lower = name.lower()
        if name_lower in self._spells:
            return self._spells[name_lower]
        canonical = self._aliases.get(name_lower)
        if canonical:
            return self._spells.get(canonical.lower())
        return None

    def has_spell(self, name: str) -> bool:
        """Check if a spell exists in the registry.

        Args:
            name: Spell name or alias to check.

        Returns:
            True if found.
        """
        return name.lower() in self._aliases

    def get_all_spell_names(self) -> Set[str]:
        """Get all spell names and aliases registered.

        Returns:
            Set of all known name variants.
        """
        return set(self._aliases.keys())

    def get_all_spells(self) -> List[CustomSpell]:
        """Get all spells in the registry.

        Returns:
            List of all CustomSpell instances.
        """
        return list(self._spells.values())

    def get_spells_by_school(self, school: str) -> List[CustomSpell]:
        """Get all spells of a specific school.

        Args:
            school: Magic school name (e.g. 'necromancy').

        Returns:
            List of matching spells.
        """
        names = self._by_school.get(school.lower(), [])
        return [self._spells[n.lower()] for n in names if n.lower() in self._spells]

    def get_spells_by_level(self, level: int) -> List[CustomSpell]:
        """Get all spells of a specific level.

        Args:
            level: Spell level (0 = cantrip).

        Returns:
            List of matching spells.
        """
        names = self._by_level.get(level, [])
        return [self._spells[n.lower()] for n in names if n.lower() in self._spells]

    def get_spells_by_class(self, char_class: str) -> List[CustomSpell]:
        """Get all spells available to a character class.

        Args:
            char_class: Character class name (e.g. 'wizard').

        Returns:
            List of matching spells.
        """
        names = self._by_class.get(char_class.lower(), [])
        return [self._spells[n.lower()] for n in names if n.lower() in self._spells]

    def get_spells_by_tag(self, tag: str) -> List[CustomSpell]:
        """Get all spells with a specific tag.

        Args:
            tag: Tag to filter by (e.g. 'damage').

        Returns:
            List of matching spells.
        """
        names = self._by_tag.get(tag.lower(), [])
        return [self._spells[n.lower()] for n in names if n.lower() in self._spells]

    def search_spells(self, query: str) -> List[CustomSpell]:
        """Search spells by name, description, or tags.

        Args:
            query: Search string.

        Returns:
            List of spells matching the query.
        """
        query_lower = query.lower()
        results = []
        for spell in self._spells.values():
            if query_lower in spell.name.lower():
                results.append(spell)
                continue
            if query_lower in spell.description.lower():
                results.append(spell)
                continue
            if any(query_lower in tag.lower() for tag in spell.meta.tags):
                results.append(spell)
        return results

    @property
    def count(self) -> int:
        """Number of spells in the registry.

        Returns:
            Spell count.
        """
        return len(self._spells)


# Module-level mutable container used as a singleton holder.
# A list avoids both `global-statement` warnings and the
# `too-few-public-methods` issue that a private holder class would trigger.
_registry_holder: List[SpellRegistry] = []


def get_spell_registry() -> SpellRegistry:
    """Get the singleton SpellRegistry instance.

    Returns:
        The global SpellRegistry.
    """
    if not _registry_holder:
        _registry_holder.append(SpellRegistry())
    return _registry_holder[0]


def reset_spell_registry() -> None:
    """Reset the singleton registry (used in tests)."""
    _registry_holder.clear()
