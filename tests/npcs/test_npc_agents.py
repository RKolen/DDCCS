"""
NPC Agents Tests

Tests for the NPCAgent class and NPC loading functionality.
"""

import os
import tempfile
from pathlib import Path

# Use test_helpers to set up environment and import required names
from tests import test_helpers
NPCAgent, load_npc_from_json, create_npc_agents = test_helpers.safe_from_import(
    "src.npcs.npc_agents", "NPCAgent", "load_npc_from_json", "create_npc_agents"
)
NPCProfile = test_helpers.safe_from_import("src.characters.character_sheet", "NPCProfile")


def test_npc_agent_initialization():
    """Test NPCAgent initialization with a profile."""
    print("\n[TEST] NPCAgent Initialization")

    profile = NPCProfile.create(
        name="Garrett",
        role="Innkeeper",
        species="Human",
        personality="Friendly and chatty",
    )

    agent = NPCAgent(profile)

    assert agent.profile == profile, "Profile not stored correctly"
    assert agent.ai_client is None, "AI client should be None by default"
    assert agent.memory == [], "Memory should be empty initially"
    print("  [OK] NPCAgent initialized correctly")
    print("[PASS] NPCAgent Initialization")


def test_npc_agent_get_status():
    """Test NPCAgent get_status method."""
    print("\n[TEST] NPCAgent Get Status")

    profile = NPCProfile.create(
        name="Marcus",
        nickname="The Smith",
        role="Blacksmith",
        species="Dwarf",
        lineage="Hill Dwarf",
        personality="Gruff but skilled",
        relationships={"Theron": "Regular customer"},
        key_traits=["Master craftsman", "Short-tempered"],
        abilities=["Metalworking", "Appraisal"],
        recurring=True,
        notes="Knows about the ancient forge",
    )

    agent = NPCAgent(profile)
    status = agent.get_status()

    assert status["name"] == "Marcus", "Name incorrect"
    assert status["role"] == "Blacksmith", "Role incorrect"
    assert status["species"] == "Dwarf", "Species incorrect"
    assert status["lineage"] == "Hill Dwarf", "Lineage incorrect"
    assert status["personality"] == "Gruff but skilled", "Personality incorrect"
    assert "Theron" in status["relationships"], "Relationships incorrect"
    assert len(status["key_traits"]) == 2, "Key traits incorrect"
    assert len(status["abilities"]) == 2, "Abilities incorrect"
    assert status["recurring"] is True, "Recurring flag incorrect"
    assert "ancient forge" in status["notes"], "Notes incorrect"
    print("  [OK] All status fields correct")
    print("[PASS] NPCAgent Get Status")


def test_npc_agent_memory():
    """Test NPCAgent memory logging."""
    print("\n[TEST] NPCAgent Memory")

    profile = NPCProfile.create(name="Sarah", role="Merchant")
    agent = NPCAgent(profile)

    # Add single event
    agent.add_to_memory("Party purchased healing potions")
    assert len(agent.memory) == 1, "Memory count incorrect"
    assert agent.memory[0] == "Party purchased healing potions"
    print("  [OK] Single event added")

    # Add multiple events (55 more events = 56 total, keep last 50)
    for i in range(55):
        agent.add_to_memory(f"Event {i}")

    assert len(agent.memory) == 50, "Memory should cap at 50 events"
    # First 6 removed: "Party purchased..." and "Event 0" through "Event 4"
    # So memory[0] should be "Event 5"
    assert agent.memory[0] == "Event 5", "Oldest events should be removed"
    assert agent.memory[-1] == "Event 54", "Newest event should be last"
    print("  [OK] Memory cap enforced (max 50 events)")
    print("[PASS] NPCAgent Memory")


def test_load_npc_from_json_basic():
    """Test loading NPC from JSON file (basic)."""
    print("\n[TEST] Load NPC from JSON - Basic")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        f.write("""{
            "name": "Thomas",
            "role": "Guard Captain",
            "species": "Human",
            "personality": "Dutiful and stern"
        }""")
        temp_path = f.name

    try:
        profile = load_npc_from_json(Path(temp_path))

        assert profile.name == "Thomas", "Name not loaded"
        assert profile.role == "Guard Captain", "Role not loaded"
        assert profile.species == "Human", "Species not loaded"
        assert profile.personality == "Dutiful and stern"
        print("  [OK] Basic NPC loaded from JSON")
    finally:
        os.unlink(temp_path)

    print("[PASS] Load NPC from JSON - Basic")


def test_load_npc_from_json_full():
    """Test loading NPC from JSON file (full profile)."""
    print("\n[TEST] Load NPC from JSON - Full Profile")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        f.write("""{
            "name": "Elena",
            "nickname": "The Wise",
            "role": "Sage",
            "species": "Elf",
            "lineage": "High Elf",
            "personality": "Patient teacher with vast knowledge",
            "relationships": {
                "Aldric": "Former student",
                "Council": "Trusted advisor"
            },
            "key_traits": ["Scholarly", "Perceptive", "Mysterious"],
            "abilities": ["Arcana", "History", "Divination"],
            "recurring": true,
            "notes": "Knows prophecy about the party"
        }""")
        temp_path = f.name

    try:
        profile = load_npc_from_json(Path(temp_path))

        assert profile.name == "Elena", "Name incorrect"
        assert profile.nickname == "The Wise", "Nickname incorrect"
        assert profile.species == "Elf", "Species incorrect"
        assert profile.lineage == "High Elf", "Lineage incorrect"
        assert len(profile.relationships) == 2, "Relationships incorrect"
        assert len(profile.key_traits) == 3, "Key traits incorrect"
        assert len(profile.abilities) == 3, "Abilities incorrect"
        assert profile.recurring is True, "Recurring flag incorrect"
        assert "prophecy" in profile.notes, "Notes incorrect"
        print("  [OK] Full NPC profile loaded correctly")
    finally:
        os.unlink(temp_path)

    print("[PASS] Load NPC from JSON - Full Profile")


def test_load_npc_from_json_defaults():
    """Test loading NPC with missing optional fields."""
    print("\n[TEST] Load NPC from JSON - Defaults")

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        f.write("""{
            "name": "Bob"
        }""")
        temp_path = f.name

    try:
        profile = load_npc_from_json(Path(temp_path))

        assert profile.name == "Bob", "Name incorrect"
        assert profile.nickname is None, "Nickname should be None"
        assert profile.role == "NPC", "Default role incorrect"
        assert profile.species == "Human", "Default species incorrect"
        assert profile.lineage == "", "Default lineage incorrect"
        assert profile.personality == "", "Default personality incorrect"
        assert profile.relationships == {}, "Default relationships incorrect"
        assert profile.key_traits == [], "Default key_traits incorrect"
        assert profile.abilities == [], "Default abilities incorrect"
        assert profile.recurring is False, "Default recurring incorrect"
        assert profile.notes == "", "Default notes incorrect"
        print("  [OK] Default values applied correctly")
    finally:
        os.unlink(temp_path)

    print("[PASS] Load NPC from JSON - Defaults")


def test_create_npc_agents():
    """Test creating multiple NPC agents from directory."""
    print("\n[TEST] Create NPC Agents")

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test NPC files
        npc1_path = Path(temp_dir) / "npc_garrett.json"
        npc1_path.write_text("""{
            "name": "Garrett",
            "role": "Innkeeper"
        }""", encoding="utf-8")

        npc2_path = Path(temp_dir) / "npc_marcus.json"
        npc2_path.write_text("""{
            "name": "Marcus",
            "role": "Blacksmith"
        }""", encoding="utf-8")

        # Create example file (should be skipped)
        example_path = Path(temp_dir) / "npc.example.json"
        example_path.write_text("""{
            "name": "Example",
            "role": "Example"
        }""", encoding="utf-8")

        agents = create_npc_agents(Path(temp_dir))

        assert len(agents) == 2, "Should create 2 agents (skip example)"
        names = [agent.profile.name for agent in agents]
        assert "Garrett" in names, "Garrett agent not created"
        assert "Marcus" in names, "Marcus agent not created"
        assert "Example" not in names, "Example should be skipped"
        print("  [OK] Created 2 agents, skipped example file")

    print("[PASS] Create NPC Agents")


def test_create_npc_agents_empty_directory():
    """Test creating agents from empty directory."""
    print("\n[TEST] Create NPC Agents - Empty Directory")

    with tempfile.TemporaryDirectory() as temp_dir:
        agents = create_npc_agents(Path(temp_dir))
        assert not agents, "Empty directory should return empty list"
        print("  [OK] Empty directory handled correctly")

    print("[PASS] Create NPC Agents - Empty Directory")


def run_all_tests():
    """Run all NPC agent tests."""
    print("=" * 70)
    print("NPC AGENTS TESTS")
    print("=" * 70)

    test_npc_agent_initialization()
    test_npc_agent_get_status()
    test_npc_agent_memory()
    test_load_npc_from_json_basic()
    test_load_npc_from_json_full()
    test_load_npc_from_json_defaults()
    test_create_npc_agents()
    test_create_npc_agents_empty_directory()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL NPC AGENTS TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
