"""Relationship management and synchronization."""

from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from dataclasses import dataclass

from src.characters.relationship import Relationship
from src.characters.relationship_types import get_inverse
from src.utils.file_io import load_json_file, save_json_file
from src.utils.path_utils import get_characters_dir, get_npcs_dir


@dataclass
class RelationshipGraph:
    """Graph representation of all relationships."""
    nodes: Set[str]  # All character/NPC names
    edges: List[Tuple[str, str, Relationship]]  # (source, target, relationship)

    def get_relationships_for(self, name: str) -> List[Relationship]:
        """Get all relationships for a specific character."""
        return [r for s, t, r in self.edges if name in (s, t)]

    def get_connection_strength(self, name1: str, name2: str) -> Optional[int]:
        """Get the strength of connection between two characters."""
        for source, target, rel in self.edges:
            if (source == name1 and target == name2) or \
               (source == name2 and target == name1):
                return rel.strength
        return None


class RelationshipManager:
    """Manages relationships across all characters and NPCs."""

    def __init__(
        self,
        characters_dir: Optional[str] = None,
        npcs_dir: Optional[str] = None
    ):
        self.characters_dir = Path(characters_dir or get_characters_dir())
        self.npcs_dir = Path(npcs_dir or get_npcs_dir())

    def build_relationship_graph(self) -> RelationshipGraph:
        """Build a complete relationship graph from all sources."""
        nodes: Set[str] = set()
        edges: List[Tuple[str, str, Relationship]] = []

        # Load character relationships
        for char_file in self.characters_dir.glob("*.json"):
            if ".example" in char_file.name:
                continue

            data = load_json_file(str(char_file))
            if not data:
                continue
            char_name = data.get("name")
            if not char_name:
                continue

            nodes.add(char_name)

            for rel in self._parse_relationships(data):
                edges.append((char_name, rel.target_name, rel))
                nodes.add(rel.target_name)

        # Load NPC relationships
        for npc_file in self.npcs_dir.glob("*.json"):
            if ".example" in npc_file.name:
                continue

            data = load_json_file(str(npc_file))
            if not data:
                continue
            npc_name = data.get("name")
            if not npc_name:
                continue

            nodes.add(npc_name)

            for rel in self._parse_relationships(data):
                edges.append((npc_name, rel.target_name, rel))
                nodes.add(rel.target_name)

        return RelationshipGraph(nodes=nodes, edges=edges)

    def _parse_relationships(self, data: Dict) -> List[Relationship]:
        """Parse relationships from character/NPC data."""
        relationships = []
        rel_data = data.get("relationships", {})

        if not isinstance(rel_data, dict):
            return relationships

        for target_name, rel_value in rel_data.items():
            if isinstance(rel_value, dict):
                try:
                    relationships.append(Relationship.from_dict(
                        {"target_name": target_name, **rel_value}
                    ))
                except (KeyError, ValueError):
                    pass
            elif isinstance(rel_value, str):
                relationships.append(
                    Relationship.from_legacy(target_name, rel_value)
                )

        return relationships

    def validate_consistency(self) -> List[str]:
        """Check for relationship inconsistencies.

        Returns:
            List of warning messages about inconsistent relationships
        """
        warnings = []
        graph = self.build_relationship_graph()

        # Check for missing inverse relationships
        for source, target, rel in graph.edges:
            target_rels = [r for s, t, r in graph.edges if s == target and t == source]

            if not target_rels:
                expected_type = get_inverse(rel.relationship_type)
                warnings.append(
                    f"{source} -> {target}: {rel.relationship_type.value}, "
                    f"but {target} has no relationship to {source} "
                    f"(expected: {expected_type.value})"
                )

        return warnings

    def sync_bidirectional(self, character_name: str) -> int:
        """Ensure all relationships for a character are bidirectional.

        Creates inverse relationships where missing.

        Returns:
            Number of relationships created
        """
        char_file = self._find_character_file(character_name)
        if not char_file:
            return 0

        data = load_json_file(str(char_file))
        if not data:
            return 0
        relationships = data.get("relationships", {})
        created = 0

        for target_name, rel_value in relationships.items():
            target_file = self._find_character_file(target_name)
            if not target_file:
                continue

            target_data = load_json_file(str(target_file))
            if not target_data:
                continue
            target_rels = target_data.get("relationships", {})

            if character_name not in target_rels:
                if isinstance(rel_value, dict):
                    rel = Relationship.from_dict(
                        {"target_name": target_name, **rel_value}
                    )
                else:
                    rel = Relationship.from_legacy(target_name, str(rel_value))

                inverse_type = get_inverse(rel.relationship_type)
                target_rels[character_name] = {
                    "type": inverse_type.value,
                    "strength": rel.strength,
                    "status": rel.status.value,
                    "notes": f"Auto-synced from {character_name}"
                }
                target_data["relationships"] = target_rels
                save_json_file(str(target_file), target_data)
                created += 1

        return created

    def _find_character_file(self, name: str) -> Optional[Path]:
        """Find a character or NPC file by name."""
        for char_file in self.characters_dir.glob("*.json"):
            if ".example" in char_file.name:
                continue
            data = load_json_file(str(char_file))
            if data and data.get("name") == name:
                return char_file

        for npc_file in self.npcs_dir.glob("*.json"):
            if ".example" in npc_file.name:
                continue
            data = load_json_file(str(npc_file))
            if data and data.get("name") == name:
                return npc_file

        return None
