"""Spell Registry CLI Manager.

Provides an interactive menu for managing the custom spell registry:
adding, removing, searching, listing, and importing/exporting spells.
"""

from typing import List, Optional

from src.spells.spell_import_export import SpellExporter, SpellImporter
from src.spells.spell_registry import (
    CustomSpell,
    SpellCasting,
    SpellMeta,
    get_spell_registry,
)
from src.utils.terminal_display import print_error, print_info, print_success


def spell_registry_menu() -> None:
    """Display the interactive spell registry management menu."""
    while True:
        registry = get_spell_registry()
        print("\n SPELL REGISTRY")
        print("-" * 30)
        print(f" Custom Spells: {registry.count}")
        print()
        print("1. List Spells")
        print("2. Add Spell")
        print("3. Remove Spell")
        print("4. Search Spells")
        print("5. Import Spells (JSON/CSV)")
        print("6. Export Spells (JSON/CSV/Markdown)")
        print("0. Back")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            _list_spells()
        elif choice == "2":
            _add_spell()
        elif choice == "3":
            _remove_spell()
        elif choice == "4":
            _search_spells()
        elif choice == "5":
            _import_spells()
        elif choice == "6":
            _export_spells()
        elif choice == "0":
            break
        else:
            print_error("Invalid choice.")


def _list_spells() -> None:
    """Display all spells in the registry, grouped by school."""
    registry = get_spell_registry()
    spells = registry.get_all_spells()

    if not spells:
        print_info("No custom spells registered yet.")
        print_info("Use 'Add Spell' to register a homebrew spell.")
        return

    # Group by school for display
    by_school: dict = {}
    for spell in sorted(spells, key=lambda s: (s.school.lower(), s.name.lower())):
        by_school.setdefault(spell.school.title(), []).append(spell)

    print(f"\n Custom Spells ({len(spells)} total)")
    print("-" * 40)
    for school, school_spells in sorted(by_school.items()):
        print(f"\n  {school}")
        for spell in school_spells:
            level_str = "Cantrip" if spell.level == 0 else f"Level {spell.level}"
            classes_str = ", ".join(spell.classes) if spell.classes else "Any"
            print(f"    {spell.name} ({level_str}) - {classes_str}")
            if spell.meta.aliases:
                print(f"      Aliases: {', '.join(spell.meta.aliases)}")

    input("\nPress Enter to continue...")


def _prompt_casting_and_meta() -> tuple:
    """Prompt the user for optional casting mechanics and metadata fields.

    Returns:
        Tuple of (SpellCasting, SpellMeta, classes list).
    """
    casting_time = input("Casting time [1 action]: ").strip() or "1 action"
    spell_range = input("Range [touch]: ").strip() or "touch"
    duration = input("Duration [instantaneous]: ").strip() or "instantaneous"

    classes_input = input("Classes (comma-separated, or blank for any): ").strip()
    classes: List[str] = (
        [c.strip() for c in classes_input.split(",") if c.strip()] if classes_input else []
    )

    source = input("Source [homebrew]: ").strip() or "homebrew"
    tags_input = input("Tags (comma-separated, or blank): ").strip()
    tags: List[str] = (
        [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else []
    )
    aliases_input = input("Aliases (comma-separated, or blank): ").strip()
    aliases: List[str] = (
        [a.strip() for a in aliases_input.split(",") if a.strip()] if aliases_input else []
    )

    casting = SpellCasting(casting_time=casting_time, range=spell_range, duration=duration)
    meta = SpellMeta(source=source, tags=tags, aliases=aliases)
    return casting, meta, classes


def _add_spell() -> None:
    """Interactively add a new spell to the registry."""
    print("\n ADD CUSTOM SPELL")
    print("-" * 30)

    name = input("Spell name: ").strip()
    if not name:
        print_error("Spell name cannot be empty.")
        return

    registry = get_spell_registry()
    if registry.has_spell(name):
        print_error(f"Spell '{name}' already exists in the registry.")
        return

    level_input = input("Level (0 = cantrip, 1-9): ").strip()
    try:
        level = int(level_input)
        if not 0 <= level <= 9:
            raise ValueError("out of range")
    except ValueError:
        print_error("Level must be an integer 0-9.")
        return

    school = input("School (e.g. necromancy, evocation): ").strip() or "unknown"
    description = input("Description: ").strip()
    casting, meta, classes = _prompt_casting_and_meta()

    spell = CustomSpell(
        name=name,
        level=level,
        school=school,
        description=description,
        classes=classes,
        casting=casting,
        meta=meta,
    )

    registry.add_spell(spell)
    print_success(f"Spell '{name}' added to the registry.")


def _remove_spell() -> None:
    """Interactively remove a spell from the registry."""
    registry = get_spell_registry()
    if not registry.count:
        print_info("No custom spells in the registry.")
        return

    print("\n REMOVE SPELL")
    print("-" * 30)
    name = input("Spell name to remove: ").strip()
    if not name:
        return

    if not registry.has_spell(name):
        print_error(f"Spell '{name}' not found.")
        return

    confirm = input(f"Remove '{name}'? (y/n): ").strip().lower()
    if confirm == "y":
        registry.remove_spell(name)
        print_success(f"Spell '{name}' removed.")
    else:
        print_info("Removal cancelled.")


def _search_spells() -> None:
    """Search the registry by name, description, or tag."""
    print("\n SEARCH SPELLS")
    print("-" * 30)
    query = input("Search query: ").strip()
    if not query:
        return

    registry = get_spell_registry()
    results = registry.search_spells(query)

    if not results:
        print_info(f"No spells found matching '{query}'.")
        return

    print(f"\n Results for '{query}' ({len(results)} found)")
    print("-" * 40)
    for spell in sorted(results, key=lambda s: s.name.lower()):
        level_str = "Cantrip" if spell.level == 0 else f"Level {spell.level}"
        print(f"  {spell.name} ({level_str}, {spell.school.title()})")
        print(f"    {spell.description[:80]}{'...' if len(spell.description) > 80 else ''}")
        print()

    input("Press Enter to continue...")


def _import_spells() -> None:
    """Import spells from a JSON or CSV file."""
    print("\n IMPORT SPELLS")
    print("-" * 30)
    print("Supported formats: JSON (.json), CSV (.csv)")
    file_path = input("File path: ").strip()
    if not file_path:
        return

    importer = SpellImporter()

    if file_path.lower().endswith(".csv"):
        stats = importer.import_from_csv(file_path)
    else:
        stats = importer.import_from_json(file_path)

    print_success(
        f"Import complete: {stats['imported']} imported, "
        f"{stats['skipped']} skipped, {stats['errors']} errors."
    )


def _export_spells() -> None:
    """Export spells to a JSON, CSV, or Markdown file."""
    registry = get_spell_registry()
    if not registry.count:
        print_info("No custom spells to export.")
        return

    print("\n EXPORT SPELLS")
    print("-" * 30)
    print("Formats: 1) JSON  2) CSV  3) Markdown")
    fmt_choice = input("Format choice [1]: ").strip() or "1"
    file_path = input("Output file path: ").strip()
    if not file_path:
        return

    exporter = SpellExporter()
    exported = _run_export(exporter, fmt_choice, file_path)
    if exported:
        print_success(f"Exported {registry.count} spells to '{file_path}'.")
    else:
        print_error("Unknown format choice. Use 1 (JSON), 2 (CSV), or 3 (Markdown).")


def _run_export(exporter: SpellExporter, fmt_choice: str, file_path: str) -> bool:
    """Dispatch the export to the correct format method.

    Args:
        exporter: SpellExporter instance.
        fmt_choice: User-selected format choice ('1', '2', or '3').
        file_path: Destination file path.

    Returns:
        True if the export was dispatched, False if the choice was invalid.
    """
    dispatch = {
        "1": exporter.export_to_json,
        "2": exporter.export_to_csv,
        "3": exporter.export_to_markdown,
    }
    handler = dispatch.get(fmt_choice)
    if handler is None:
        return False
    handler(file_path)
    return True


def get_registry_spell_names_for_highlighting() -> Optional[List[str]]:
    """Return all custom spell names for use in the spell highlighter.

    Returns None when the registry is empty (signals: use pattern fallback).

    Returns:
        List of spell name strings, or None if the registry is empty.
    """
    registry = get_spell_registry()
    if not registry.count:
        return None
    return list(registry.get_all_spell_names())
