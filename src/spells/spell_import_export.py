"""Import and export functionality for custom spells.

Supports JSON and CSV formats for sharing spell definitions between
campaigns or with other DMs.
"""

import csv
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.spells.spell_registry import CustomSpell, SpellRegistry, get_spell_registry
from src.utils.file_io import load_json_file, save_json_file


class SpellImporter:
    """Import spells from various file formats into the registry."""

    def __init__(self, registry: Optional[SpellRegistry] = None) -> None:
        """Initialize importer.

        Args:
            registry: Spell registry to import into; uses singleton if None.
        """
        self.registry = registry or get_spell_registry()

    def import_from_json(self, file_path: str, merge: bool = True) -> Dict[str, int]:
        """Import spells from a JSON file.

        Args:
            file_path: Path to JSON file with a 'spells' list.
            merge: If True, skip existing spells; if False, overwrite.

        Returns:
            Dict with 'imported', 'skipped', and 'errors' counts.
        """
        stats: Dict[str, int] = {"imported": 0, "skipped": 0, "errors": 0}
        data = load_json_file(file_path)
        if data is None:
            stats["errors"] += 1
            return stats

        for spell_data in data.get("spells", []):
            try:
                spell = CustomSpell.from_dict(spell_data)
                if merge and self.registry.has_spell(spell.name):
                    stats["skipped"] += 1
                    continue
                self.registry.add_spell(spell)
                stats["imported"] += 1
            except (KeyError, TypeError, ValueError):
                stats["errors"] += 1

        return stats

    def import_from_csv(
        self,
        file_path: str,
        column_mapping: Optional[Dict[str, str]] = None,
    ) -> Dict[str, int]:
        """Import spells from a CSV file.

        Expected columns: name, level, school, description, classes,
        casting_time, range, duration (all optional except name).

        Args:
            file_path: Path to CSV file.
            column_mapping: Maps CSV column names to spell field names.
                Defaults to identity mapping.

        Returns:
            Dict with 'imported', 'skipped', and 'errors' counts.
        """
        default_mapping: Dict[str, str] = {
            "name": "name",
            "level": "level",
            "school": "school",
            "description": "description",
            "classes": "classes",
            "casting_time": "casting_time",
            "range": "range",
            "duration": "duration",
        }
        mapping = column_mapping or default_mapping
        stats: Dict[str, int] = {"imported": 0, "skipped": 0, "errors": 0}

        try:
            with open(file_path, "r", encoding="utf-8") as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    spell_data: Dict[str, Any] = {}
                    for csv_col, spell_field in mapping.items():
                        if csv_col not in row:
                            continue
                        value: Any = row[csv_col]
                        if spell_field == "level":
                            value = int(value) if str(value).isdigit() else 0
                        elif spell_field == "classes":
                            value = [c.strip() for c in str(value).split(",") if c.strip()]
                        spell_data[spell_field] = value

                    if not spell_data.get("name"):
                        stats["errors"] += 1
                        continue

                    spell_data.setdefault("level", 0)
                    spell_data.setdefault("school", "unknown")
                    spell_data.setdefault("description", "")

                    try:
                        spell = CustomSpell.from_dict(spell_data)
                        if self.registry.has_spell(spell.name):
                            stats["skipped"] += 1
                            continue
                        self.registry.add_spell(spell)
                        stats["imported"] += 1
                    except (KeyError, TypeError, ValueError):
                        stats["errors"] += 1
        except (OSError, csv.Error):
            stats["errors"] += 1

        return stats


class SpellExporter:
    """Export spells from the registry to various file formats."""

    def __init__(self, registry: Optional[SpellRegistry] = None) -> None:
        """Initialize exporter.

        Args:
            registry: Spell registry to export from; uses singleton if None.
        """
        self.registry = registry or get_spell_registry()

    def export_to_json(
        self,
        file_path: str,
        spells: Optional[List[CustomSpell]] = None,
        include_metadata: bool = True,
    ) -> None:
        """Export spells to a JSON file.

        Args:
            file_path: Path to output file.
            spells: Specific spells to export; exports all if None.
            include_metadata: Include export timestamp and count.
        """
        spell_list = spells if spells is not None else self.registry.get_all_spells()
        data: Dict[str, Any] = {
            "registry_version": "1.0",
            "spells": [s.to_dict() for s in spell_list],
        }
        if include_metadata:
            data["exported_at"] = datetime.now().isoformat()
            data["spell_count"] = len(spell_list)
        save_json_file(file_path, data)

    def export_to_csv(
        self,
        file_path: str,
        spells: Optional[List[CustomSpell]] = None,
    ) -> None:
        """Export spells to a CSV file.

        Args:
            file_path: Path to output file.
            spells: Specific spells to export; exports all if None.
        """
        spell_list = spells if spells is not None else self.registry.get_all_spells()
        fieldnames = [
            "name", "level", "school", "description",
            "casting_time", "range", "duration",
            "classes", "source", "tags",
        ]
        with open(file_path, "w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()
            for spell in spell_list:
                writer.writerow({
                    "name": spell.name,
                    "level": spell.level,
                    "school": spell.school,
                    "description": spell.description,
                    "casting_time": spell.casting.casting_time,
                    "range": spell.casting.range,
                    "duration": spell.casting.duration,
                    "classes": ",".join(spell.classes),
                    "source": spell.meta.source,
                    "tags": ",".join(spell.meta.tags),
                })

    def export_to_markdown(
        self,
        file_path: str,
        spells: Optional[List[CustomSpell]] = None,
        title: str = "Custom Spells",
    ) -> None:
        """Export spells to a Markdown reference document.

        Args:
            file_path: Path to output file.
            spells: Specific spells to export; exports all if None.
            title: Document title.
        """
        spell_list = spells if spells is not None else self.registry.get_all_spells()
        lines = [f"# {title}", "", f"**Total Spells:** {len(spell_list)}", ""]

        by_level: Dict[int, List[CustomSpell]] = {}
        for spell in spell_list:
            by_level.setdefault(spell.level, []).append(spell)

        for level in sorted(by_level.keys()):
            lines.append(f"## {_level_name(level)}")
            lines.append("")
            for spell in sorted(by_level[level], key=lambda s: s.name):
                lines.append(f"### {spell.name}")
                lines.append("")
                lines.append(f"**School:** {spell.school.title()}")
                lines.append(f"**Casting Time:** {spell.casting.casting_time}")
                lines.append(f"**Range:** {spell.casting.range}")
                lines.append(f"**Duration:** {spell.casting.duration}")
                if spell.classes:
                    lines.append(f"**Classes:** {', '.join(spell.classes)}")
                lines.append("")
                lines.append(spell.description)
                lines.append("")
            lines.append("---")
            lines.append("")

        with open(file_path, "w", encoding="utf-8") as md_file:
            md_file.write("\n".join(lines))


def _level_name(level: int) -> str:
    """Return a display name for a spell level.

    Args:
        level: Spell level integer (0 = cantrip).

    Returns:
        Human-readable level string.
    """
    level_names = {0: "Cantrips (0 Level)", 1: "1st Level", 2: "2nd Level", 3: "3rd Level"}
    if level in level_names:
        return level_names[level]
    return f"{level}th Level"
