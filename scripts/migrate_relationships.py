"""Migrate relationships to structured format."""

import json
from pathlib import Path

from src.characters.relationship import Relationship


def migrate_character_relationships(characters_dir: str = "game_data/characters"):
    """Convert legacy string relationships to structured format."""
    char_path = Path(characters_dir)

    for char_file in char_path.glob("*.json"):
        if ".example" in char_file.name:
            continue

        with open(char_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if "relationships" not in data:
            continue

        old_rels = data["relationships"]
        new_rels = {}
        changed = False

        for target, value in old_rels.items():
            if isinstance(value, str):
                rel = Relationship.from_legacy(target, value)
                new_rels[target] = rel.to_dict()
                changed = True
            else:
                new_rels[target] = value

        if changed:
            data["relationships"] = new_rels

            with open(char_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"Migrated: {char_file.name}")
        else:
            print(f"Already structured: {char_file.name}")


def migrate_npc_relationships(npcs_dir: str = "game_data/npcs"):
    """Convert legacy string relationships in NPC files to structured format."""
    npc_path = Path(npcs_dir)

    for npc_file in npc_path.glob("*.json"):
        if ".example" in npc_file.name:
            continue

        with open(npc_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if "relationships" not in data:
            continue

        old_rels = data["relationships"]
        new_rels = {}
        changed = False

        for target, value in old_rels.items():
            if isinstance(value, str):
                rel = Relationship.from_legacy(target, value)
                new_rels[target] = rel.to_dict()
                changed = True
            else:
                new_rels[target] = value

        if changed:
            data["relationships"] = new_rels

            with open(npc_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"Migrated: {npc_file.name}")
        else:
            print(f"Already structured: {npc_file.name}")


if __name__ == "__main__":
    import sys

    dirs_to_migrate = {
        "characters": "game_data/characters",
        "npcs": "game_data/npcs",
    }

    if len(sys.argv) > 1:
        target = sys.argv[1]
        if target == "characters":
            migrate_character_relationships()
        elif target == "npcs":
            migrate_npc_relationships()
        else:
            print(f"Unknown target: {target}. Use 'characters' or 'npcs'.")
            sys.exit(1)
    else:
        print("Migrating characters...")
        migrate_character_relationships()
        print("\nMigrating NPCs...")
        migrate_npc_relationships()
        print("\nDone.")
