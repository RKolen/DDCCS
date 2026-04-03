"""Relationship visualization and export."""

from typing import Optional, List, Set
from pathlib import Path

from src.characters.relationship_manager import RelationshipManager, RelationshipGraph
from src.characters.relationship_types import RelationshipType


class RelationshipVisualizer:
    """Generate visual representations of relationships."""

    # Color mapping for relationship types
    TYPE_COLORS = {
        RelationshipType.FAMILY_CLOSE: "#2E86AB",      # Blue
        RelationshipType.ROMANTIC_PARTNER: "#E94F37",  # Red
        RelationshipType.FRIEND_CLOSE: "#7CB518",      # Green
        RelationshipType.FRIEND: "#AACC00",            # Light green
        RelationshipType.ALLY: "#F0A500",              # Orange
        RelationshipType.MENTOR: "#9B5DE5",            # Purple
        RelationshipType.STUDENT: "#9B5DE5",           # Purple
        RelationshipType.ENEMY: "#F72585",             # Pink
        RelationshipType.NEMESIS: "#B5179E",           # Dark pink
        RelationshipType.RIVAL: "#7209B7",             # Violet
        RelationshipType.UNKNOWN: "#6C757D",           # Gray
    }

    def __init__(self, manager: Optional[RelationshipManager] = None):
        self.manager = manager or RelationshipManager()

    def to_dot(
        self,
        center_on: Optional[str] = None,
        min_strength: int = 1,
        include_types: Optional[List[RelationshipType]] = None
    ) -> str:
        """Generate Graphviz DOT format for relationship visualization.

        Args:
            center_on: Optional character name to center the graph on
            min_strength: Minimum relationship strength to include
            include_types: Only include these relationship types

        Returns:
            DOT format string for rendering with Graphviz
        """
        graph = self.manager.build_relationship_graph()

        lines = [
            'digraph Relationships {',
            '    rankdir=LR;',
            '    node [shape=box, style="rounded,filled", fillcolor=white];',
            '    edge [fontsize=10];',
            ''
        ]

        if center_on:
            nodes = self._get_connected_nodes(graph, center_on)
        else:
            nodes = graph.nodes

        for node in sorted(nodes):
            safe_name = self._safe_id(node)
            lines.append(f'    {safe_name} [label="{node}"];')

        lines.append('')

        seen_edges: Set[tuple] = set()
        for source, target, rel in graph.edges:
            if source not in nodes or target not in nodes:
                continue
            if rel.strength < min_strength:
                continue
            if include_types and rel.relationship_type not in include_types:
                continue

            edge_key = (min(source, target), max(source, target))
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)

            color = self.TYPE_COLORS.get(rel.relationship_type, "#6C757D")
            safe_source = self._safe_id(source)
            safe_target = self._safe_id(target)
            label = f"{rel.relationship_type.value}\\n({rel.strength})"

            lines.append(
                f'    {safe_source} -> {safe_target} '
                f'[label="{label}", color="{color}", fontcolor="{color}"];'
            )

        lines.append('}')
        return '\n'.join(lines)

    def to_mermaid(
        self,
        center_on: Optional[str] = None,
        min_strength: int = 1
    ) -> str:
        """Generate Mermaid diagram format.

        Args:
            center_on: Optional character name to center on
            min_strength: Minimum relationship strength to include

        Returns:
            Mermaid flowchart syntax
        """
        graph = self.manager.build_relationship_graph()

        if center_on:
            nodes = self._get_connected_nodes(graph, center_on)
        else:
            nodes = graph.nodes

        lines = ['flowchart LR']

        seen: Set[tuple] = set()
        for source, target, rel in graph.edges:
            if source not in nodes or target not in nodes:
                continue
            if rel.strength < min_strength:
                continue

            edge_key = (min(source, target), max(source, target))
            if edge_key in seen:
                continue
            seen.add(edge_key)

            safe_source = self._safe_mermaid_id(source)
            safe_target = self._safe_mermaid_id(target)

            lines.append(
                f'    {safe_source}["{source}"] '
                f'-- "{rel.relationship_type.value}" --> '
                f'{safe_target}["{target}"]'
            )

        return '\n'.join(lines)

    def export_dot_file(
        self,
        output_path: str,
        center_on: Optional[str] = None
    ) -> None:
        """Export to a .dot file for Graphviz rendering."""
        dot_content = self.to_dot(center_on=center_on)
        Path(output_path).write_text(dot_content, encoding='utf-8')

    def _get_connected_nodes(
        self,
        graph: RelationshipGraph,
        center: str,
        depth: int = 2
    ) -> Set[str]:
        """Get all nodes connected to center within depth hops."""
        connected = {center}
        frontier = {center}

        for _ in range(depth):
            new_frontier = set()
            for node in frontier:
                for source, target, _ in graph.edges:
                    if source == node and target not in connected:
                        new_frontier.add(target)
                        connected.add(target)
                    elif target == node and source not in connected:
                        new_frontier.add(source)
                        connected.add(source)
            frontier = new_frontier
            if not frontier:
                break

        return connected

    @staticmethod
    def _safe_id(name: str) -> str:
        """Convert name to safe DOT identifier."""
        return name.replace(' ', '_').replace('-', '_').replace("'", "")

    @staticmethod
    def _safe_mermaid_id(name: str) -> str:
        """Convert name to safe Mermaid identifier."""
        return name.replace(' ', '_').replace('-', '_').replace("'", "")


def render_relationship_map(
    output_format: str = "dot",
    center_on: Optional[str] = None,
    output_path: Optional[str] = None
) -> str:
    """Generate a relationship map.

    Args:
        output_format: One of 'dot', 'mermaid'
        center_on: Optional character to center the map on
        output_path: Optional file path to write output

    Returns:
        The generated map content
    """
    visualizer = RelationshipVisualizer()

    if output_format == "mermaid":
        content = visualizer.to_mermaid(center_on=center_on)
    else:
        content = visualizer.to_dot(center_on=center_on)

    if output_path:
        Path(output_path).write_text(content, encoding='utf-8')

    return content
