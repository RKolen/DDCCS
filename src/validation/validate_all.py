"""
Unified Game Data Validation Module

Validates all JSON data files in the D&D Campaign System:
- Character profiles
- NPC profiles
- Custom items registry
- Party configuration

Usage:
    # Validate all game data
    python validate_all.py

    # Validate specific types
    python validate_all.py --characters
    python validate_all.py --npcs
    python validate_all.py --items
    python validate_all.py --party

    # Validate with verbose output
    python validate_all.py --verbose
"""

import sys
import argparse
from typing import Dict, Tuple
from ..utils.file_io import get_json_files_in_directory, file_exists
from ..utils.path_utils import (
    get_characters_dir,
    get_npcs_dir,
    get_items_registry_path,
    get_party_config_path,
)

# Import all validators
try:
    from src.validation.character_validator import validate_character_file

    CHAR_AVAILABLE = True
except ImportError:
    CHAR_AVAILABLE = False

try:
    from src.validation.npc_validator import validate_npc_file

    NPC_AVAILABLE = True
except ImportError:
    NPC_AVAILABLE = False

try:
    from src.validation.items_validator import validate_items_file

    ITEMS_AVAILABLE = True
except ImportError:
    ITEMS_AVAILABLE = False

try:
    from src.validation.party_validator import validate_party_file

    PARTY_AVAILABLE = True
except ImportError:
    PARTY_AVAILABLE = False


def validate_characters(verbose: bool = False) -> Tuple[bool, int, int]:
    """Validate all character files."""
    if not CHAR_AVAILABLE:
        print("[WARNING] Character validator not available")
        return (True, 0, 0)

    print("\n=== Validating Characters ===")
    characters_dir = get_characters_dir()

    if not file_exists(characters_dir):
        print(f"[WARNING] Characters directory not found: {characters_dir}")
        return (True, 0, 0)

    all_valid = True
    valid_count = 0
    invalid_count = 0

    for filepath in sorted(get_json_files_in_directory(characters_dir)):
        if filepath.name.endswith(".example.json"):
            continue

        is_valid, errors = validate_character_file(str(filepath))
        filename = filepath.name  # Get just the filename for display

        if is_valid:
            valid_count += 1
            if verbose:
                print(f"  [OK] {filename}")
        else:
            invalid_count += 1
            all_valid = False
            print(f"  [FAILED] {filename}: INVALID")
            for error in errors:
                print(f"    - {error}")

    if not verbose and valid_count > 0:
        print(f"  [OK] {valid_count} character(s) validated successfully")

    if invalid_count > 0:
        print(f"  [FAILED] {invalid_count} character(s) failed validation")

    return (all_valid, valid_count, invalid_count)


def validate_npcs(verbose: bool = False) -> Tuple[bool, int, int]:
    """Validate all NPC files."""
    if not NPC_AVAILABLE:
        print("[WARNING] NPC validator not available")
        return (True, 0, 0)

    print("\n=== Validating NPCs ===")
    npcs_dir = get_npcs_dir()

    if not file_exists(npcs_dir):
        print(f"[WARNING] NPCs directory not found: {npcs_dir}")
        return (True, 0, 0)

    all_valid = True
    valid_count = 0
    invalid_count = 0

    for filepath in sorted(get_json_files_in_directory(npcs_dir)):
        if filepath.name.endswith(".example.json"):
            continue

        is_valid, errors = validate_npc_file(str(filepath))
        filename = filepath.name  # Get just the filename for display

        if is_valid:
            valid_count += 1
            if verbose:
                print(f"  [OK] {filename}")
        else:
            invalid_count += 1
            all_valid = False
            print(f"  [FAILED] {filename}: INVALID")
            for error in errors:
                print(f"    - {error}")

    if not verbose and valid_count > 0:
        print(f"  [OK] {valid_count} NPC(s) validated successfully")

    if invalid_count > 0:
        print(f"  [FAILED] {invalid_count} NPC(s) failed validation")

    return (all_valid, valid_count, invalid_count)


def validate_items() -> Tuple[bool, int, int]:
    """Validate items registry file."""
    if not ITEMS_AVAILABLE:
        print("[WARNING] Items validator not available")
        return (True, 0, 0)

    print("\n=== Validating Items Registry ===")
    items_file = get_items_registry_path()

    if not file_exists(items_file):
        print(f"[WARNING] Items registry not found: {items_file}")
        return (True, 0, 0)

    is_valid, errors = validate_items_file(items_file)

    if is_valid:
        print("  [OK] Items registry validated successfully")
        return (True, 1, 0)
    print("  [FAILED] Items registry: INVALID")
    for error in errors:
        print(f"    - {error}")
    return (False, 0, 1)


def validate_party() -> Tuple[bool, int, int]:
    """Validate party configuration file."""
    if not PARTY_AVAILABLE:
        print("[WARNING] Party validator not available")
        return (True, 0, 0)

    print("\n=== Validating Party Configuration ===")
    party_file = get_party_config_path()

    if not file_exists(party_file):
        print(f"[WARNING] Party configuration not found: {party_file}")
        return (True, 0, 0)

    # Get characters directory for cross-reference
    characters_dir = get_characters_dir()
    if not file_exists(characters_dir):
        characters_dir = None

    is_valid, errors = validate_party_file(party_file, characters_dir)

    if is_valid:
        print("  [OK] Party configuration validated successfully")
        return (True, 1, 0)
    print("  [FAILED] Party configuration: INVALID")
    for error in errors:
        print(f"    - {error}")
    return (False, 0, 1)


def print_summary(results: Dict[str, Tuple[bool, int, int]]):
    """Print validation summary."""
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)

    total_valid = 0
    total_invalid = 0
    all_passed = True

    for data_type, (passed, valid, invalid) in results.items():
        status = "[OK] PASS" if passed else "[FAILED] FAIL"
        print(f"{data_type:20} {status:10} ({valid} valid, {invalid} invalid)")
        total_valid += valid
        total_invalid += invalid
        if not passed:
            all_passed = False

    print("=" * 50)
    print(f"Total: {total_valid} valid, {total_invalid} invalid")

    if all_passed:
        print("\n[OK] All game data validated successfully!")
    else:
        print("\n[FAILED] Some game data failed validation")

    return all_passed


def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(
        description="Validate all JSON data files in the D&D Campaign System"
    )
    parser.add_argument(
        "--characters", action="store_true", help="Validate only character files"
    )
    parser.add_argument("--npcs", action="store_true", help="Validate only NPC files")
    parser.add_argument(
        "--items", action="store_true", help="Validate only items registry"
    )
    parser.add_argument(
        "--party", action="store_true", help="Validate only party configuration"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show validation for each file"
    )

    args = parser.parse_args()

    # If no specific type selected, validate all
    validate_all = not (args.characters or args.npcs or args.items or args.party)

    print("D&D Campaign System - Game Data Validation")
    print("=" * 50)

    results = {}

    if validate_all or args.characters:
        results["Characters"] = validate_characters(args.verbose)

    if validate_all or args.npcs:
        results["NPCs"] = validate_npcs(args.verbose)

    if validate_all or args.items:
        results["Items Registry"] = validate_items()

    if validate_all or args.party:
        results["Party Config"] = validate_party()

    all_passed = print_summary(results)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
