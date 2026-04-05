"""Unit tests for src.spells.spell_import_export.

Tests cover SpellImporter (JSON, CSV) and SpellExporter (JSON, CSV, Markdown).
"""

import csv
import json
import os
import tempfile
from pathlib import Path

from tests.test_helpers import make_test_spell, registry_in_temp, run_test_functions
from src.spells.spell_import_export import SpellExporter, SpellImporter
from src.spells.spell_registry import reset_spell_registry


# ---------------------------------------------------------------------------
# SpellImporter – JSON
# ---------------------------------------------------------------------------

def test_importer_json_imports_spells():
    """import_from_json should add spells from a valid JSON file."""
    tmp = tempfile.mkdtemp()
    registry = registry_in_temp(tmp)

    json_path = os.path.join(tmp, "import.json")
    data = {"spells": [make_test_spell("Imported Spell").to_dict()]}
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh)

    stats = SpellImporter(registry=registry).import_from_json(json_path)
    assert stats["imported"] == 1
    assert stats["errors"] == 0
    assert registry.has_spell("Imported Spell")


def test_importer_json_skips_duplicates():
    """import_from_json should skip spells already in the registry."""
    tmp = tempfile.mkdtemp()
    registry = registry_in_temp(tmp)
    registry.add_spell(make_test_spell("Duplicate Spell"))

    json_path = os.path.join(tmp, "import.json")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump({"spells": [make_test_spell("Duplicate Spell").to_dict()]}, fh)

    stats = SpellImporter(registry=registry).import_from_json(json_path)
    assert stats["imported"] == 0
    assert stats["skipped"] == 1


def test_importer_json_missing_file():
    """import_from_json should count an error for a missing file."""
    tmp = tempfile.mkdtemp()
    stats = SpellImporter(registry=registry_in_temp(tmp)).import_from_json(
        "/nonexistent/path/import.json"
    )
    assert stats["errors"] >= 1


# ---------------------------------------------------------------------------
# SpellImporter – CSV
# ---------------------------------------------------------------------------

def test_importer_csv_imports_spells():
    """import_from_csv should parse and add spells from a CSV file."""
    tmp = tempfile.mkdtemp()
    registry = registry_in_temp(tmp)

    csv_path = os.path.join(tmp, "spells.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["name", "level", "school", "description", "classes"],
        )
        writer.writeheader()
        writer.writerow({
            "name": "CSV Spell", "level": "2", "school": "divination",
            "description": "A divination spell.", "classes": "wizard,cleric",
        })

    stats = SpellImporter(registry=registry).import_from_csv(csv_path)
    assert stats["imported"] == 1
    assert registry.has_spell("CSV Spell")


def test_importer_csv_missing_name_counts_error():
    """import_from_csv should count a row with no name as an error."""
    tmp = tempfile.mkdtemp()
    csv_path = os.path.join(tmp, "bad.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["name", "level", "school"])
        writer.writeheader()
        writer.writerow({"name": "", "level": "1", "school": "evocation"})

    stats = SpellImporter(registry=registry_in_temp(tmp)).import_from_csv(csv_path)
    assert stats["errors"] >= 1


# ---------------------------------------------------------------------------
# SpellExporter – JSON
# ---------------------------------------------------------------------------

def test_exporter_json_writes_file():
    """export_to_json should write a valid JSON file."""
    tmp = tempfile.mkdtemp()
    registry = registry_in_temp(tmp)
    registry.add_spell(make_test_spell("Export Spell"))

    out_path = os.path.join(tmp, "out.json")
    SpellExporter(registry=registry).export_to_json(out_path)

    assert Path(out_path).exists()
    with open(out_path, encoding="utf-8") as fh:
        data = json.load(fh)
    assert any(s["name"] == "Export Spell" for s in data["spells"])


def test_exporter_json_includes_metadata():
    """export_to_json with include_metadata=True should add timestamp and count."""
    tmp = tempfile.mkdtemp()
    registry = registry_in_temp(tmp)
    registry.add_spell(make_test_spell())

    out_path = os.path.join(tmp, "meta.json")
    SpellExporter(registry=registry).export_to_json(out_path, include_metadata=True)

    with open(out_path, encoding="utf-8") as fh:
        data = json.load(fh)
    assert "exported_at" in data
    assert data["spell_count"] == 1


# ---------------------------------------------------------------------------
# SpellExporter – CSV
# ---------------------------------------------------------------------------

def test_exporter_csv_writes_file():
    """export_to_csv should write a CSV with the expected header."""
    tmp = tempfile.mkdtemp()
    registry = registry_in_temp(tmp)
    registry.add_spell(make_test_spell("CSV Export Spell"))

    out_path = os.path.join(tmp, "out.csv")
    SpellExporter(registry=registry).export_to_csv(out_path)

    assert Path(out_path).exists()
    with open(out_path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 1
    assert rows[0]["name"] == "CSV Export Spell"


# ---------------------------------------------------------------------------
# SpellExporter – Markdown
# ---------------------------------------------------------------------------

def test_exporter_markdown_writes_file():
    """export_to_markdown should write a Markdown file with spell headings."""
    tmp = tempfile.mkdtemp()
    registry = registry_in_temp(tmp)
    registry.add_spell(make_test_spell("Markdown Spell", level=1))

    out_path = os.path.join(tmp, "spells.md")
    SpellExporter(registry=registry).export_to_markdown(out_path, title="Test Spells")

    content = Path(out_path).read_text(encoding="utf-8")
    assert "# Test Spells" in content
    assert "### Markdown Spell" in content


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    run_test_functions([
        test_importer_json_imports_spells,
        test_importer_json_skips_duplicates,
        test_importer_json_missing_file,
        test_importer_csv_imports_spells,
        test_importer_csv_missing_name_counts_error,
        test_exporter_json_writes_file,
        test_exporter_json_includes_metadata,
        test_exporter_csv_writes_file,
        test_exporter_markdown_writes_file,
    ], cleanup=reset_spell_registry)
