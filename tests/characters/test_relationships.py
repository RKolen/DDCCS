"""
Test Relationship Mapping System

Tests the relationship types, schema, manager, and visualizer modules.

What we test:
- RelationshipType enum and inverse mappings
- Relationship/RelationshipEvent dataclasses (create, serialize, legacy migration)
- RelationshipGraph (node/edge queries)
- RelationshipManager (graph building, consistency validation, bidirectional sync)
- RelationshipVisualizer (DOT and Mermaid output)

Why we test this:
- Relationship data drives narrative consistency checks
- Legacy string format must still work after structured format is added
- Bidirectional sync ensures no orphaned relationships in data files
- Visualization output must be valid syntax for downstream tools
"""

import json
import tempfile
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock

from src.characters.relationship_types import (
    RelationshipType,
    get_inverse,
    RELATIONSHIP_INVERSES,
)
from src.characters.relationship import Relationship, RelationshipEvent, RelationshipStatus
from src.characters.relationship_manager import RelationshipManager, RelationshipGraph
from src.characters.relationship_visualizer import RelationshipVisualizer


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_graph(edges=None):
    """Build a minimal RelationshipGraph for visualizer tests."""
    if edges is None:
        rel = Relationship(
            target_name="Arwen",
            relationship_type=RelationshipType.ROMANTIC_PARTNER,
            strength=9,
        )
        edges = [("Aragorn", "Arwen", rel)]
    nodes = {s for s, _, _ in edges} | {t for _, t, _ in edges}
    return RelationshipGraph(nodes=nodes, edges=edges)


def _make_visualizer(graph=None):
    """Build a RelationshipVisualizer backed by a mock manager."""
    if graph is None:
        graph = _make_graph()
    manager = MagicMock()
    manager.build_relationship_graph.return_value = graph
    return RelationshipVisualizer(manager=manager)


def _write_json(path, data):
    """Write data as JSON to path."""
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _read_json(path):
    """Read and return JSON from path."""
    return json.loads(path.read_text(encoding="utf-8"))


def _make_manager(
    char_data: dict,
    npc_data: Optional[dict] = None,
    *,
    tmp_path: Path,
) -> RelationshipManager:
    """Create a RelationshipManager with mock file data in a temp dir."""
    chars_dir = tmp_path / "characters"
    npcs_dir = tmp_path / "npcs"
    chars_dir.mkdir()
    npcs_dir.mkdir()

    for filename, data in char_data.items():
        _write_json(chars_dir / filename, data)

    if npc_data:
        for filename, data in npc_data.items():
            _write_json(npcs_dir / filename, data)

    return RelationshipManager(
        characters_dir=str(chars_dir),
        npcs_dir=str(npcs_dir),
    )


# ─────────────────────────────────────────────────────────────────────────────
# RelationshipType tests
# ─────────────────────────────────────────────────────────────────────────────

def test_all_types_have_string_values():
    """All RelationshipType enum members have non-empty string values."""
    print("\n[TEST] RelationshipType - All types have non-empty string values")
    for rel_type in RelationshipType:
        assert isinstance(rel_type.value, str) and rel_type.value, (
            f"{rel_type} has empty value"
        )
    print("  [OK] All types valid")
    print("[PASS] RelationshipType - All types have non-empty string values")


def test_asymmetric_inverses():
    """Asymmetric relationship types return the correct opposing type."""
    print("\n[TEST] RelationshipType - Asymmetric inverses")
    assert get_inverse(RelationshipType.MENTOR) == RelationshipType.STUDENT
    assert get_inverse(RelationshipType.STUDENT) == RelationshipType.MENTOR
    assert get_inverse(RelationshipType.LORD) == RelationshipType.VASSAL
    assert get_inverse(RelationshipType.VASSAL) == RelationshipType.LORD
    assert get_inverse(RelationshipType.EMPLOYER) == RelationshipType.EMPLOYEE
    assert get_inverse(RelationshipType.EMPLOYEE) == RelationshipType.EMPLOYER
    assert get_inverse(RelationshipType.DEBTOR) == RelationshipType.CREDITOR
    assert get_inverse(RelationshipType.CREDITOR) == RelationshipType.DEBTOR
    print("  [OK] All asymmetric inverses correct")
    print("[PASS] RelationshipType - Asymmetric inverses")


def test_symmetric_inverses():
    """Symmetric relationship types return themselves as their inverse."""
    print("\n[TEST] RelationshipType - Symmetric inverses return same type")
    symmetric = [
        RelationshipType.FRIEND_CLOSE,
        RelationshipType.FRIEND,
        RelationshipType.ALLY,
        RelationshipType.RIVAL,
        RelationshipType.ENEMY,
        RelationshipType.NEMESIS,
        RelationshipType.ROMANTIC_PARTNER,
    ]
    for rel_type in symmetric:
        assert get_inverse(rel_type) == rel_type, f"{rel_type} should be symmetric"
    print("  [OK] All symmetric inverses correct")
    print("[PASS] RelationshipType - Symmetric inverses return same type")


def test_unmapped_type_returns_unknown():
    """Types not in the inverses map return UNKNOWN."""
    print("\n[TEST] RelationshipType - Unmapped types return UNKNOWN")
    for rel_type in RelationshipType:
        if rel_type not in RELATIONSHIP_INVERSES:
            result = get_inverse(rel_type)
            assert result == RelationshipType.UNKNOWN, (
                f"{rel_type} not in inverses map, expected UNKNOWN got {result}"
            )
    print("  [OK] Unmapped types return UNKNOWN")
    print("[PASS] RelationshipType - Unmapped types return UNKNOWN")


# ─────────────────────────────────────────────────────────────────────────────
# RelationshipEvent tests
# ─────────────────────────────────────────────────────────────────────────────

def test_relationship_event_round_trip():
    """RelationshipEvent survives a to_dict/from_dict round trip."""
    print("\n[TEST] RelationshipEvent - to_dict/from_dict round trip")
    event = RelationshipEvent(date="2024-01-01", description="First meeting", impact=2)
    restored = RelationshipEvent.from_dict(event.to_dict())
    assert restored.date == event.date
    assert restored.description == event.description
    assert restored.impact == event.impact
    print("  [OK] Round trip preserves all fields")
    print("[PASS] RelationshipEvent - to_dict/from_dict round trip")


def test_relationship_event_defaults():
    """RelationshipEvent.from_dict applies correct defaults for missing keys."""
    print("\n[TEST] RelationshipEvent - from_dict defaults")
    event = RelationshipEvent.from_dict({})
    assert event.description == ""
    assert event.impact == 0
    assert event.date is None
    print("  [OK] Defaults correct")
    print("[PASS] RelationshipEvent - from_dict defaults")


# ─────────────────────────────────────────────────────────────────────────────
# Relationship tests
# ─────────────────────────────────────────────────────────────────────────────

def test_relationship_create_basic():
    """Relationship can be created with required fields and defaults applied."""
    print("\n[TEST] Relationship - Basic creation")
    rel = Relationship(target_name="Gandalf", relationship_type=RelationshipType.MENTOR)
    assert rel.target_name == "Gandalf"
    assert rel.strength == 5
    assert rel.status == RelationshipStatus.CURRENT
    assert rel.timestamps.created is not None
    print("  [OK] Basic creation correct")
    print("[PASS] Relationship - Basic creation")


def test_relationship_strength_validation():
    """Relationship raises ValueError for out-of-range strength values."""
    print("\n[TEST] Relationship - Strength validation")
    try:
        Relationship(target_name="X", relationship_type=RelationshipType.FRIEND, strength=0)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    try:
        Relationship(target_name="X", relationship_type=RelationshipType.FRIEND, strength=11)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    print("  [OK] Out-of-range strength raises ValueError")
    print("[PASS] Relationship - Strength validation")


def test_relationship_is_positive_negative():
    """is_positive and is_negative return correct polarity for known types."""
    print("\n[TEST] Relationship - is_positive / is_negative")
    rel_friend = Relationship(
        target_name="X", relationship_type=RelationshipType.FRIEND_CLOSE
    )
    rel_ally = Relationship(target_name="X", relationship_type=RelationshipType.ALLY)
    rel_enemy = Relationship(target_name="X", relationship_type=RelationshipType.ENEMY)
    rel_nemesis = Relationship(
        target_name="X", relationship_type=RelationshipType.NEMESIS
    )
    assert rel_friend.is_positive
    assert rel_ally.is_positive
    assert rel_enemy.is_negative
    assert rel_nemesis.is_negative
    print("  [OK] Polarity detection correct")
    print("[PASS] Relationship - is_positive / is_negative")


def test_relationship_add_event():
    """add_event adjusts and clamps strength correctly."""
    print("\n[TEST] Relationship - add_event adjusts strength")
    rel = Relationship(target_name="X", relationship_type=RelationshipType.FRIEND, strength=5)
    rel.add_event("Saved each other", impact=3)
    assert rel.strength == 8
    assert len(rel.history) == 1
    # Clamp high
    rel.add_event("Epic moment", impact=5)
    assert rel.strength == 10
    # Clamp low
    rel2 = Relationship(
        target_name="Y", relationship_type=RelationshipType.FRIEND, strength=2
    )
    rel2.add_event("Betrayal", impact=-5)
    assert rel2.strength == 1
    print("  [OK] Strength adjusted and clamped correctly")
    print("[PASS] Relationship - add_event adjusts strength")


def test_relationship_round_trip():
    """Relationship survives a to_dict/from_dict round trip."""
    print("\n[TEST] Relationship - to_dict/from_dict round trip")
    rel = Relationship(
        target_name="Arwen",
        relationship_type=RelationshipType.ROMANTIC_PARTNER,
        strength=9,
        notes="Beloved",
    )
    restored = Relationship.from_dict(rel.to_dict())
    assert restored.target_name == rel.target_name
    assert restored.relationship_type == rel.relationship_type
    assert restored.strength == rel.strength
    assert restored.notes == rel.notes
    print("  [OK] Round trip preserves all fields")
    print("[PASS] Relationship - to_dict/from_dict round trip")


def test_relationship_from_dict_with_history():
    """from_dict correctly loads relationship history events."""
    print("\n[TEST] Relationship - from_dict with history")
    data = {
        "target_name": "Legolas",
        "type": "friend_close",
        "strength": 8,
        "status": "current",
        "notes": "Fellowship brother",
        "history": [
            {"date": "2024-01-01", "description": "Met at Rivendell", "impact": 1}
        ],
    }
    rel = Relationship.from_dict(data)
    assert rel.target_name == "Legolas"
    assert rel.relationship_type == RelationshipType.FRIEND_CLOSE
    assert len(rel.history) == 1
    assert rel.history[0].description == "Met at Rivendell"
    print("  [OK] History loaded correctly")
    print("[PASS] Relationship - from_dict with history")


def test_relationship_from_legacy():
    """from_legacy correctly infers relationship type from plain-text descriptions."""
    print("\n[TEST] Relationship - from_legacy inference")
    cases = [
        ("Arwen", "Beloved", RelationshipType.ROMANTIC_PARTNER),
        ("Samwise", "Trusted companion", RelationshipType.FRIEND_CLOSE),
        ("Gandalf", "Mentor and guide", RelationshipType.MENTOR),
        ("Sauron", "Ancient enemy", RelationshipType.ENEMY),
        ("Theoden", "Ally in battle", RelationshipType.ALLY),
        ("Stranger", "Someone met once", RelationshipType.UNKNOWN),
    ]
    for target, desc, expected in cases:
        rel = Relationship.from_legacy(target, desc)
        assert rel.relationship_type == expected, (
            f"'{desc}' expected {expected}, got {rel.relationship_type}"
        )
        assert rel.notes == desc
    print("  [OK] Legacy inference correct for all cases")
    print("[PASS] Relationship - from_legacy inference")


# ─────────────────────────────────────────────────────────────────────────────
# RelationshipGraph tests
# ─────────────────────────────────────────────────────────────────────────────

def test_relationship_graph_get_relationships_for():
    """get_relationships_for returns all edges that include the named node."""
    print("\n[TEST] RelationshipGraph - get_relationships_for")
    r1 = Relationship(target_name="Arwen", relationship_type=RelationshipType.ROMANTIC_PARTNER)
    r2 = Relationship(target_name="Gandalf", relationship_type=RelationshipType.ALLY)
    graph = RelationshipGraph(
        nodes={"Aragorn", "Arwen", "Gandalf"},
        edges=[("Aragorn", "Arwen", r1), ("Aragorn", "Gandalf", r2)]
    )
    assert len(graph.get_relationships_for("Aragorn")) == 2
    assert len(graph.get_relationships_for("Arwen")) == 1
    assert len(graph.get_relationships_for("Gandalf")) == 1
    print("  [OK] Relationship lookup correct")
    print("[PASS] RelationshipGraph - get_relationships_for")


def test_relationship_graph_connection_strength():
    """get_connection_strength returns the correct value for both directions."""
    print("\n[TEST] RelationshipGraph - get_connection_strength")
    r = Relationship(
        target_name="Arwen",
        relationship_type=RelationshipType.ROMANTIC_PARTNER,
        strength=9,
    )
    graph = RelationshipGraph(
        nodes={"Aragorn", "Arwen"},
        edges=[("Aragorn", "Arwen", r)]
    )
    assert graph.get_connection_strength("Aragorn", "Arwen") == 9
    assert graph.get_connection_strength("Arwen", "Aragorn") == 9  # bidirectional lookup
    assert graph.get_connection_strength("Arwen", "Gandalf") is None
    print("  [OK] Strength lookup correct")
    print("[PASS] RelationshipGraph - get_connection_strength")


# ─────────────────────────────────────────────────────────────────────────────
# RelationshipManager tests
# ─────────────────────────────────────────────────────────────────────────────

def test_manager_build_graph_legacy():
    """build_relationship_graph correctly parses legacy string relationship format."""
    print("\n[TEST] RelationshipManager - build_relationship_graph (legacy format)")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        manager = _make_manager(
            {"aragorn.json": {"name": "Aragorn", "relationships": {"Arwen": "Beloved"}}},
            tmp_path=tmp_path,
        )
        graph = manager.build_relationship_graph()
        assert "Aragorn" in graph.nodes
        assert "Arwen" in graph.nodes
        assert len(graph.edges) == 1
    print("  [OK] Legacy format parsed correctly")
    print("[PASS] RelationshipManager - build_relationship_graph (legacy format)")


def test_manager_build_graph_structured():
    """build_relationship_graph correctly parses structured dict relationship format."""
    print("\n[TEST] RelationshipManager - build_relationship_graph (structured format)")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        manager = _make_manager(
            {
                "aragorn.json": {
                    "name": "Aragorn",
                    "relationships": {
                        "Gandalf": {"type": "ally", "strength": 8, "status": "current"}
                    }
                }
            },
            tmp_path=tmp_path,
        )
        graph = manager.build_relationship_graph()
        assert len(graph.edges) == 1
        _, _, rel = graph.edges[0]
        assert rel.relationship_type == RelationshipType.ALLY
        assert rel.strength == 8
    print("  [OK] Structured format parsed correctly")
    print("[PASS] RelationshipManager - build_relationship_graph (structured format)")


def test_manager_skips_example_files():
    """build_relationship_graph skips files whose name contains '.example'."""
    print("\n[TEST] RelationshipManager - skips .example files")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        manager = _make_manager(
            {
                "aragorn.json": {"name": "Aragorn", "relationships": {"Arwen": "Beloved"}},
                "npc.example.json": {"name": "Example", "relationships": {}},
            },
            tmp_path=tmp_path,
        )
        graph = manager.build_relationship_graph()
        assert "Example" not in graph.nodes
    print("  [OK] Example files skipped")
    print("[PASS] RelationshipManager - skips .example files")


def test_manager_validate_consistency_finds_missing_inverse():
    """validate_consistency reports a warning when inverse relationship is absent."""
    print("\n[TEST] RelationshipManager - validate_consistency (missing inverse)")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        manager = _make_manager(
            {"aragorn.json": {"name": "Aragorn", "relationships": {"Arwen": "Beloved"}}},
            tmp_path=tmp_path,
        )
        warnings = manager.validate_consistency()
        assert any("Arwen" in w for w in warnings), f"Expected Arwen warning, got: {warnings}"
    print("  [OK] Missing inverse detected")
    print("[PASS] RelationshipManager - validate_consistency (missing inverse)")


def test_manager_validate_consistency_no_warnings_bidirectional():
    """validate_consistency produces no warnings when both sides exist."""
    print("\n[TEST] RelationshipManager - validate_consistency (bidirectional, no warnings)")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        aragorn_rel = {"type": "friend_close", "strength": 7, "status": "current"}
        legolas_rel = {"type": "friend_close", "strength": 7, "status": "current"}
        manager = _make_manager(
            {
                "aragorn.json": {
                    "name": "Aragorn",
                    "relationships": {"Legolas": aragorn_rel},
                },
                "legolas.json": {
                    "name": "Legolas",
                    "relationships": {"Aragorn": legolas_rel},
                },
            },
            tmp_path=tmp_path,
        )
        warnings = manager.validate_consistency()
        assert not warnings, f"Expected no warnings, got: {warnings}"
    print("  [OK] No warnings for bidirectional relationships")
    print("[PASS] RelationshipManager - validate_consistency (bidirectional, no warnings)")


def test_manager_sync_bidirectional_creates_inverse():
    """sync_bidirectional creates a missing inverse relationship in the target file."""
    print("\n[TEST] RelationshipManager - sync_bidirectional creates inverse")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        chars_dir = tmp_path / "characters"
        npcs_dir = tmp_path / "npcs"
        chars_dir.mkdir()
        npcs_dir.mkdir()

        _write_json(chars_dir / "aragorn.json", {
            "name": "Aragorn",
            "relationships": {"Legolas": "Fellow ranger"}
        })
        _write_json(chars_dir / "legolas.json", {
            "name": "Legolas",
            "relationships": {}
        })

        manager = RelationshipManager(
            characters_dir=str(chars_dir),
            npcs_dir=str(npcs_dir),
        )
        created = manager.sync_bidirectional("Aragorn")
        assert created == 1

        legolas_data = _read_json(chars_dir / "legolas.json")
        assert "Aragorn" in legolas_data["relationships"], (
            f"Expected 'Aragorn' in Legolas relationships, got: {legolas_data['relationships']}"
        )
    print("  [OK] Inverse relationship created")
    print("[PASS] RelationshipManager - sync_bidirectional creates inverse")


def test_manager_sync_skips_missing_targets():
    """sync_bidirectional returns 0 when the target character file does not exist."""
    print("\n[TEST] RelationshipManager - sync_bidirectional skips missing targets")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        manager = _make_manager(
            {"aragorn.json": {"name": "Aragorn", "relationships": {"NonExistent": "Someone"}}},
            tmp_path=tmp_path,
        )
        created = manager.sync_bidirectional("Aragorn")
        assert created == 0
    print("  [OK] Missing target skipped gracefully")
    print("[PASS] RelationshipManager - sync_bidirectional skips missing targets")


# ─────────────────────────────────────────────────────────────────────────────
# RelationshipVisualizer tests
# ─────────────────────────────────────────────────────────────────────────────

def test_visualizer_to_dot_structure():
    """to_dot produces valid DOT syntax containing all expected identifiers."""
    print("\n[TEST] RelationshipVisualizer - to_dot produces valid structure")
    viz = _make_visualizer()
    dot = viz.to_dot()
    assert dot.startswith("digraph Relationships {"), "Must start with digraph declaration"
    assert dot.endswith("}"), "Must end with closing brace"
    assert "Aragorn" in dot
    assert "Arwen" in dot
    assert "romantic_partner" in dot
    print("  [OK] DOT structure valid")
    print("[PASS] RelationshipVisualizer - to_dot produces valid structure")


def test_visualizer_to_dot_filters_by_strength():
    """to_dot excludes edges below min_strength."""
    print("\n[TEST] RelationshipVisualizer - to_dot filters by min_strength")
    viz = _make_visualizer()
    dot = viz.to_dot(min_strength=10)  # strength=9, should be excluded
    assert "->" not in dot, "No edges should appear above min_strength"
    print("  [OK] Strength filter works")
    print("[PASS] RelationshipVisualizer - to_dot filters by min_strength")


def test_visualizer_to_dot_filters_by_type():
    """to_dot excludes edges whose type is not in include_types."""
    print("\n[TEST] RelationshipVisualizer - to_dot filters by include_types")
    viz = _make_visualizer()
    dot = viz.to_dot(include_types=[RelationshipType.ENEMY])
    assert "->" not in dot, "ROMANTIC_PARTNER edge should be excluded by type filter"
    print("  [OK] Type filter works")
    print("[PASS] RelationshipVisualizer - to_dot filters by include_types")


def test_visualizer_to_mermaid_structure():
    """to_mermaid produces valid Mermaid syntax containing all expected identifiers."""
    print("\n[TEST] RelationshipVisualizer - to_mermaid produces valid structure")
    viz = _make_visualizer()
    mermaid = viz.to_mermaid()
    assert mermaid.startswith("flowchart LR")
    assert "Aragorn" in mermaid
    assert "Arwen" in mermaid
    assert "romantic_partner" in mermaid
    print("  [OK] Mermaid structure valid")
    print("[PASS] RelationshipVisualizer - to_mermaid produces valid structure")


def test_visualizer_to_mermaid_filters_by_strength():
    """to_mermaid excludes edges below min_strength."""
    print("\n[TEST] RelationshipVisualizer - to_mermaid filters by min_strength")
    viz = _make_visualizer()
    mermaid = viz.to_mermaid(min_strength=10)
    assert "-->" not in mermaid, "No edges should appear above min_strength"
    print("  [OK] Mermaid strength filter works")
    print("[PASS] RelationshipVisualizer - to_mermaid filters by min_strength")


def test_visualizer_center_on_excludes_unconnected():
    """center_on limits the graph to nodes reachable from the named character."""
    print("\n[TEST] RelationshipVisualizer - center_on excludes unconnected nodes")
    rel = Relationship(target_name="Arwen", relationship_type=RelationshipType.ROMANTIC_PARTNER)
    graph = RelationshipGraph(
        nodes={"Aragorn", "Arwen", "Sauron"},
        edges=[("Aragorn", "Arwen", rel)]
    )
    viz = _make_visualizer(graph)
    dot = viz.to_dot(center_on="Aragorn")
    assert "Sauron" not in dot, "Sauron has no connection to Aragorn"
    assert "Aragorn" in dot
    print("  [OK] Unconnected nodes excluded when centering")
    print("[PASS] RelationshipVisualizer - center_on excludes unconnected nodes")


def test_visualizer_export_dot_file():
    """export_dot_file writes a file containing valid DOT syntax."""
    print("\n[TEST] RelationshipVisualizer - export_dot_file writes file")
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "relationships.dot"
        viz = _make_visualizer()
        viz.export_dot_file(str(output))
        assert output.exists(), "Output file should exist"
        content = output.read_text(encoding="utf-8")
        assert "digraph" in content
    print("  [OK] DOT file written correctly")
    print("[PASS] RelationshipVisualizer - export_dot_file writes file")


def test_visualizer_safe_id():
    """safe_id replaces spaces, hyphens, and apostrophes with underscores or empty string."""
    print("\n[TEST] RelationshipVisualizer - safe_id handles special chars")
    assert RelationshipVisualizer.safe_id("Frodo Baggins") == "Frodo_Baggins"
    assert RelationshipVisualizer.safe_id("Obi-Wan") == "Obi_Wan"
    assert RelationshipVisualizer.safe_id("D'Artagnan") == "DArtagnan"
    print("  [OK] Special characters replaced correctly")
    print("[PASS] RelationshipVisualizer - safe_id handles special chars")


def test_render_relationship_map_dot():
    """RelationshipVisualizer produces DOT output for an empty graph."""
    print("\n[TEST] render_relationship_map - dot format")
    graph = RelationshipGraph(nodes=set(), edges=[])
    manager = MagicMock()
    manager.build_relationship_graph.return_value = graph

    viz = RelationshipVisualizer(manager=manager)
    content = viz.to_dot()
    assert "digraph" in content
    print("  [OK] DOT output produced")
    print("[PASS] render_relationship_map - dot format")


def test_render_relationship_map_mermaid():
    """RelationshipVisualizer produces Mermaid output for an empty graph."""
    print("\n[TEST] render_relationship_map - mermaid format")
    graph = RelationshipGraph(nodes=set(), edges=[])
    manager = MagicMock()
    manager.build_relationship_graph.return_value = graph

    viz = RelationshipVisualizer(manager=manager)
    content = viz.to_mermaid()
    assert "flowchart" in content
    print("  [OK] Mermaid output produced")
    print("[PASS] render_relationship_map - mermaid format")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def run_all_tests():
    """Run all relationship mapping tests."""
    print("=" * 70)
    print("RELATIONSHIP MAPPING TESTS")
    print("=" * 70)

    # RelationshipType
    test_all_types_have_string_values()
    test_asymmetric_inverses()
    test_symmetric_inverses()
    test_unmapped_type_returns_unknown()

    # RelationshipEvent
    test_relationship_event_round_trip()
    test_relationship_event_defaults()

    # Relationship
    test_relationship_create_basic()
    test_relationship_strength_validation()
    test_relationship_is_positive_negative()
    test_relationship_add_event()
    test_relationship_round_trip()
    test_relationship_from_dict_with_history()
    test_relationship_from_legacy()

    # RelationshipGraph
    test_relationship_graph_get_relationships_for()
    test_relationship_graph_connection_strength()

    # RelationshipManager
    test_manager_build_graph_legacy()
    test_manager_build_graph_structured()
    test_manager_skips_example_files()
    test_manager_validate_consistency_finds_missing_inverse()
    test_manager_validate_consistency_no_warnings_bidirectional()
    test_manager_sync_bidirectional_creates_inverse()
    test_manager_sync_skips_missing_targets()

    # RelationshipVisualizer
    test_visualizer_to_dot_structure()
    test_visualizer_to_dot_filters_by_strength()
    test_visualizer_to_dot_filters_by_type()
    test_visualizer_to_mermaid_structure()
    test_visualizer_to_mermaid_filters_by_strength()
    test_visualizer_center_on_excludes_unconnected()
    test_visualizer_export_dot_file()
    test_visualizer_safe_id()
    test_render_relationship_map_dot()
    test_render_relationship_map_mermaid()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL RELATIONSHIP MAPPING TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
