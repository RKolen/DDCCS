"""Tests for session notes data structures and manager."""

import os
import tempfile

from tests import test_helpers

SessionNotes = test_helpers.safe_from_import(
    "src.sessions.session_notes",
    "SessionNotes",
)
NotePriority = test_helpers.safe_from_import(
    "src.sessions.session_notes",
    "NotePriority",
)
PlotStatus = test_helpers.safe_from_import(
    "src.sessions.session_notes",
    "PlotStatus",
)
PlotThread = test_helpers.safe_from_import(
    "src.sessions.session_notes",
    "PlotThread",
)
SessionEvent = test_helpers.safe_from_import(
    "src.sessions.session_notes",
    "SessionEvent",
)
NPCIntroduction = test_helpers.safe_from_import(
    "src.sessions.session_notes",
    "NPCIntroduction",
)
PlayerDecision = test_helpers.safe_from_import(
    "src.sessions.session_notes",
    "PlayerDecision",
)
SessionNotesManager = test_helpers.safe_from_import(
    "src.sessions.session_notes_manager",
    "SessionNotesManager",
)
build_story_prompt_with_session_context = test_helpers.safe_from_import(
    "src.stories.story_ai_generator",
    "build_story_prompt_with_session_context",
)


# ---------------------------------------------------------------------------
# SessionNotes data structure tests
# ---------------------------------------------------------------------------


def test_session_notes_initialization():
    """Test that SessionNotes initialises with correct defaults."""
    print("\n[TEST] SessionNotes Initialization")

    notes = SessionNotes(
        session_id="001",
        session_date="2026-03-22",
        campaign_name="Example_Campaign",
    )

    assert notes.session_id == "001"
    assert notes.session_date == "2026-03-22"
    assert notes.campaign_name == "Example_Campaign"
    assert notes.story_file is None
    assert notes.summary == ""
    assert not notes.events
    assert not notes.plot_threads
    assert not notes.npc_introductions
    assert not notes.player_decisions
    assert not notes.roll_results
    assert notes.created_date is not None
    assert notes.last_updated is not None
    print("  [OK] All defaults correct")
    print("[PASS] SessionNotes Initialization")


def test_session_notes_add_event():
    """Test adding an event to session notes."""
    print("\n[TEST] SessionNotes.add_event")

    notes = SessionNotes("002", "2026-03-22", "Example_Campaign")
    event = notes.add_event(
        title="Goblin ambush",
        description="The party was ambushed by goblins on the road.",
        characters=["Aragorn", "Frodo"],
    )
    event.npcs_involved = ["Goblin Chief"]
    event.location = "Darkwood Road"

    assert len(notes.events) == 1
    recorded = notes.events[0]
    assert recorded.title == "Goblin ambush"
    assert "goblins" in recorded.description
    assert "Aragorn" in recorded.characters_involved
    assert "Frodo" in recorded.characters_involved
    assert recorded.location == "Darkwood Road"
    assert recorded.priority == NotePriority.IMPORTANT
    print("  [OK] Event added with correct fields")
    print("[PASS] SessionNotes.add_event")


def test_session_notes_add_event_priority():
    """Test that custom priority is stored on events."""
    print("\n[TEST] SessionNotes.add_event priority")

    notes = SessionNotes("003", "2026-03-22", "Example_Campaign")
    notes.add_event(
        title="Critical moment",
        description="The king revealed his true identity.",
        priority=NotePriority.CRITICAL,
    )

    assert notes.events[0].priority == NotePriority.CRITICAL
    print("  [OK] Priority stored correctly")
    print("[PASS] SessionNotes.add_event priority")


def test_session_notes_add_plot_thread_new():
    """Test adding a new plot thread."""
    print("\n[TEST] SessionNotes.add_plot_thread - new thread")

    notes = SessionNotes("004", "2026-03-22", "Example_Campaign")
    notes.add_plot_thread(
        "The Missing Heir",
        "The throne is empty and the real prince is missing.",
        PlotStatus.INTRODUCED,
    )

    assert len(notes.plot_threads) == 1
    thread = notes.plot_threads[0]
    assert thread.name == "The Missing Heir"
    assert thread.status == PlotStatus.INTRODUCED
    assert thread.introduced_session == "004"
    print("  [OK] New plot thread created")
    print("[PASS] SessionNotes.add_plot_thread - new thread")


def test_session_notes_add_plot_thread_existing():
    """Test that an existing plot thread gets a note appended."""
    print("\n[TEST] SessionNotes.add_plot_thread - existing thread")

    notes = SessionNotes("005", "2026-03-22", "Example_Campaign")
    notes.add_plot_thread("Corruption", "Something is rotten in the city.")
    notes.add_plot_thread("Corruption", "New evidence points to the guild.", PlotStatus.ACTIVE)

    assert len(notes.plot_threads) == 1
    thread = notes.plot_threads[0]
    assert thread.status == PlotStatus.ACTIVE
    assert "New evidence" in thread.notes[0]
    print("  [OK] Existing thread updated with note")
    print("[PASS] SessionNotes.add_plot_thread - existing thread")


def test_session_notes_resolve_plot_thread():
    """Test resolving a plot thread."""
    print("\n[TEST] SessionNotes.resolve_plot_thread")

    notes = SessionNotes("006", "2026-03-22", "Example_Campaign")
    notes.add_plot_thread("Dragon Threat", "A dragon terrorises the valley.")
    notes.resolve_plot_thread("Dragon Threat", "Dragon defeated by the party.")

    thread = notes.plot_threads[0]
    assert thread.status == PlotStatus.RESOLVED
    assert thread.resolved_session == "006"
    assert any("Dragon defeated" in n for n in thread.notes)
    print("  [OK] Thread resolved correctly")
    print("[PASS] SessionNotes.resolve_plot_thread")


def test_session_notes_add_npc_introduction():
    """Test adding an NPC introduction."""
    print("\n[TEST] SessionNotes.add_npc_introduction")

    notes = SessionNotes("007", "2026-03-22", "Example_Campaign")
    npc = notes.add_npc_introduction(
        name="Elara",
        role="Blacksmith",
        location="Rivendell",
        impression="Gruff but fair",
    )
    npc.relationship_to_party = "Friendly"

    assert len(notes.npc_introductions) == 1
    recorded = notes.npc_introductions[0]
    assert recorded.name == "Elara"
    assert recorded.role == "Blacksmith"
    assert recorded.location == "Rivendell"
    assert recorded.relationship_to_party == "Friendly"
    print("  [OK] NPC introduction recorded")
    print("[PASS] SessionNotes.add_npc_introduction")


def test_session_notes_add_player_decision():
    """Test adding a player decision."""
    print("\n[TEST] SessionNotes.add_player_decision")

    notes = SessionNotes("008", "2026-03-22", "Example_Campaign")
    notes.add_player_decision(
        decision="Side with the rebels",
        made_by="Aragorn",
        alternatives=["Stay neutral", "Side with the king"],
        consequences="The rebels owe a favour",
    )

    assert len(notes.player_decisions) == 1
    dec = notes.player_decisions[0]
    assert dec.decision == "Side with the rebels"
    assert dec.made_by == "Aragorn"
    assert len(dec.alternatives_considered) == 2
    assert dec.consequences == "The rebels owe a favour"
    print("  [OK] Decision recorded")
    print("[PASS] SessionNotes.add_player_decision")


def test_session_notes_serialization_roundtrip():
    """Test to_dict/from_dict roundtrip for full notes."""
    print("\n[TEST] SessionNotes serialization roundtrip")

    notes = SessionNotes("009", "2026-03-22", "Example_Campaign")
    notes.summary = "A session full of adventure."
    notes.add_event("Test event", "Something happened.", characters=["Frodo"])
    notes.add_plot_thread("Ring Bearer", "Frodo carries the Ring.")
    sauron = notes.add_npc_introduction("Sauron", "Villain", "Mordor", "Terrifying")
    sauron.relationship_to_party = "Hostile"
    notes.add_player_decision("Destroy the Ring", "Frodo")

    data = notes.to_dict()

    assert data["session_id"] == "009"
    assert data["summary"] == "A session full of adventure."
    assert len(data["events"]) == 1
    assert len(data["plot_threads"]) == 1
    assert len(data["npc_introductions"]) == 1
    assert len(data["player_decisions"]) == 1

    restored = SessionNotes.from_dict(data)

    assert restored.session_id == "009"
    assert restored.summary == "A session full of adventure."
    assert len(restored.events) == 1
    assert restored.events[0].title == "Test event"
    assert restored.events[0].characters_involved == ["Frodo"]
    assert len(restored.plot_threads) == 1
    assert restored.plot_threads[0].name == "Ring Bearer"
    assert len(restored.npc_introductions) == 1
    assert restored.npc_introductions[0].name == "Sauron"
    assert len(restored.player_decisions) == 1
    assert restored.player_decisions[0].made_by == "Frodo"
    print("  [OK] Roundtrip successful")
    print("[PASS] SessionNotes serialization roundtrip")


# ---------------------------------------------------------------------------
# SessionNotesManager tests
# ---------------------------------------------------------------------------


def _create_manager_with_tmpdir():
    """Helper: create a SessionNotesManager backed by a temp directory."""
    tmpdir = tempfile.mkdtemp()
    # Fake game_data layout inside tmpdir
    game_data = os.path.join(tmpdir, "game_data")
    os.makedirs(game_data)
    manager = SessionNotesManager("Test_Campaign", workspace_path=tmpdir)
    return manager, tmpdir


def test_manager_save_and_load():
    """Test saving and loading session notes via the manager."""
    print("\n[TEST] SessionNotesManager save and load")

    manager, _tmp = _create_manager_with_tmpdir()

    notes = manager.create_session_notes("001")
    notes.summary = "First session."
    notes.add_event("Arrived in town", "The party arrived in Bree.")

    manager.save_session_notes(notes)

    loaded = manager.load_session_notes("001")
    assert loaded is not None
    assert loaded.session_id == "001"
    assert loaded.summary == "First session."
    assert len(loaded.events) == 1
    assert loaded.events[0].title == "Arrived in town"
    print("  [OK] Save and load successful")
    print("[PASS] SessionNotesManager save and load")


def test_manager_load_missing_returns_none():
    """Test that loading a non-existent session ID returns None."""
    print("\n[TEST] SessionNotesManager load missing returns None")

    manager, _tmp = _create_manager_with_tmpdir()
    result = manager.load_session_notes("nonexistent")
    assert result is None
    print("  [OK] None returned for missing session")
    print("[PASS] SessionNotesManager load missing returns None")


def test_manager_get_all_session_notes_empty():
    """Test get_all_session_notes on a campaign with no notes."""
    print("\n[TEST] SessionNotesManager get_all_session_notes empty")

    manager, _tmp = _create_manager_with_tmpdir()
    result = manager.get_all_session_notes()
    assert result == []
    print("  [OK] Empty list returned")
    print("[PASS] SessionNotesManager get_all_session_notes empty")


def test_manager_get_all_session_notes_sorted():
    """Test that get_all_session_notes returns notes in date order."""
    print("\n[TEST] SessionNotesManager get_all_session_notes sorted")

    manager, _tmp = _create_manager_with_tmpdir()

    n1 = SessionNotes("002", "2026-03-23", "Test_Campaign")
    n2 = SessionNotes("001", "2026-03-22", "Test_Campaign")
    manager.save_session_notes(n1)
    manager.save_session_notes(n2)

    all_notes = manager.get_all_session_notes()
    assert len(all_notes) == 2
    assert all_notes[0].session_date == "2026-03-22"
    assert all_notes[1].session_date == "2026-03-23"
    print("  [OK] Notes sorted by date")
    print("[PASS] SessionNotesManager get_all_session_notes sorted")


def test_manager_get_recent_notes():
    """Test that get_recent_notes returns only the most recent entries."""
    print("\n[TEST] SessionNotesManager get_recent_notes")

    manager, _tmp = _create_manager_with_tmpdir()

    for i in range(5):
        n = SessionNotes(str(i).zfill(3), f"2026-03-{10 + i:02d}", "Test_Campaign")
        manager.save_session_notes(n)

    recent = manager.get_recent_notes(3)
    assert len(recent) == 3
    assert recent[-1].session_id == "004"
    print("  [OK] Correct number of recent notes")
    print("[PASS] SessionNotesManager get_recent_notes")


def test_manager_get_active_plot_threads():
    """Test tracking active vs resolved plot threads across sessions."""
    print("\n[TEST] SessionNotesManager get_active_plot_threads")

    manager, _tmp = _create_manager_with_tmpdir()

    n1 = SessionNotes("001", "2026-03-22", "Test_Campaign")
    n1.add_plot_thread("Dark Prophecy", "An ancient prophecy looms.", PlotStatus.ACTIVE)
    n1.add_plot_thread("Lost Sword", "A legendary sword is missing.", PlotStatus.ACTIVE)
    manager.save_session_notes(n1)

    n2 = SessionNotes("002", "2026-03-23", "Test_Campaign")
    n2.add_plot_thread("Lost Sword", "Sword found in the dungeon.", PlotStatus.RESOLVED)
    manager.save_session_notes(n2)

    threads = manager.get_active_plot_threads()
    names = [t["name"] for t in threads]
    assert "Dark Prophecy" in names
    assert "Lost Sword" not in names
    print("  [OK] Resolved thread excluded from active list")
    print("[PASS] SessionNotesManager get_active_plot_threads")


def test_manager_get_npc_introductions():
    """Test that NPC introductions are de-duplicated across sessions."""
    print("\n[TEST] SessionNotesManager get_npc_introductions")

    manager, _tmp = _create_manager_with_tmpdir()

    n1 = SessionNotes("001", "2026-03-22", "Test_Campaign")
    n1.add_npc_introduction("Gandalf", "Wizard", "Shire", "Old and wise")
    manager.save_session_notes(n1)

    n2 = SessionNotes("002", "2026-03-23", "Test_Campaign")
    n2.add_npc_introduction("Gandalf", "Wizard", "Shire", "Old and wise")
    n2.add_npc_introduction("Saruman", "Wizard", "Isengard", "Proud and cold")
    manager.save_session_notes(n2)

    npcs = manager.get_npc_introductions()
    names = [n["name"] for n in npcs]
    assert names.count("Gandalf") == 1
    assert "Saruman" in names
    print("  [OK] NPCs de-duplicated correctly")
    print("[PASS] SessionNotesManager get_npc_introductions")


def test_manager_get_campaign_timeline():
    """Test that get_campaign_timeline returns events in order."""
    print("\n[TEST] SessionNotesManager get_campaign_timeline")

    manager, _tmp = _create_manager_with_tmpdir()

    n1 = SessionNotes("001", "2026-03-22", "Test_Campaign")
    n1.add_event("Event A", "First event")
    manager.save_session_notes(n1)

    n2 = SessionNotes("002", "2026-03-23", "Test_Campaign")
    n2.add_event("Event B", "Second event")
    manager.save_session_notes(n2)

    timeline = manager.get_campaign_timeline()
    assert len(timeline) == 2
    assert timeline[0]["title"] == "Event A"
    assert timeline[1]["title"] == "Event B"
    print("  [OK] Timeline ordered correctly")
    print("[PASS] SessionNotesManager get_campaign_timeline")


def test_manager_get_context_for_story_generation():
    """Test that story generation context has expected keys and data."""
    print("\n[TEST] SessionNotesManager get_context_for_story_generation")

    manager, _tmp = _create_manager_with_tmpdir()

    n = SessionNotes("001", "2026-03-22", "Test_Campaign")
    n.add_event(
        "Big fight", "The party fought trolls.", priority=NotePriority.IMPORTANT
    )
    n.add_plot_thread("Troll Menace", "Trolls roam the hills.", PlotStatus.ACTIVE)
    n.add_npc_introduction("Bilbo", "Hobbit", "Shire", "Cheerful")
    n.add_player_decision("Avoid the mountain pass", "Frodo")
    manager.save_session_notes(n)

    context = manager.get_context_for_story_generation()

    assert "recent_events" in context
    assert "active_plots" in context
    assert "recent_npcs" in context
    assert "pending_decisions" in context

    assert len(context["recent_events"]) >= 1
    assert len(context["active_plots"]) >= 1
    assert len(context["recent_npcs"]) >= 1
    assert len(context["pending_decisions"]) >= 1
    print("  [OK] Context contains expected keys and data")
    print("[PASS] SessionNotesManager get_context_for_story_generation")


def test_manager_export_timeline_markdown():
    """Test that export_timeline_markdown produces valid markdown."""
    print("\n[TEST] SessionNotesManager export_timeline_markdown")

    manager, _tmp = _create_manager_with_tmpdir()

    n = SessionNotes("001", "2026-03-22", "Test_Campaign")
    n.add_event("Departure", "The party set out from Rivendell.", characters=["Frodo"])
    manager.save_session_notes(n)

    markdown = manager.export_timeline_markdown()

    assert "# Campaign Timeline: Test_Campaign" in markdown
    assert "Departure" in markdown
    assert "2026-03-22" in markdown
    print("  [OK] Markdown contains expected content")
    print("[PASS] SessionNotesManager export_timeline_markdown")


# ---------------------------------------------------------------------------
# story_ai_generator integration
# ---------------------------------------------------------------------------


def test_build_story_prompt_no_context():
    """Test that an empty context returns the prompt unchanged."""
    print("\n[TEST] build_story_prompt_with_session_context - empty context")

    prompt = "The party arrives at the tavern."
    result = build_story_prompt_with_session_context(prompt, {})
    assert result == prompt
    print("  [OK] Empty context leaves prompt unchanged")
    print("[PASS] build_story_prompt_with_session_context - empty context")


def test_build_story_prompt_with_events():
    """Test that recent events are injected into the prompt."""
    print("\n[TEST] build_story_prompt_with_session_context - with events")

    prompt = "The party continues their journey."
    context = {
        "recent_events": [
            {"session": "001", "title": "Battle at Helm's Deep", "description": "A great siege."}
        ],
        "active_plots": [],
        "recent_npcs": [],
        "pending_decisions": [],
    }

    result = build_story_prompt_with_session_context(prompt, context)

    assert "Battle at Helm's Deep" in result
    assert "Session Context" in result
    assert prompt in result
    print("  [OK] Event injected into prompt")
    print("[PASS] build_story_prompt_with_session_context - with events")


def test_build_story_prompt_with_all_context():
    """Test that all context types are injected into the prompt."""
    print("\n[TEST] build_story_prompt_with_session_context - all context types")

    prompt = "The party investigates the ruin."
    context = {
        "recent_events": [
            {
                "session": "002",
                "title": "Dark ritual",
                "description": "Cultists performed a ritual.",
            }
        ],
        "active_plots": [
            {"name": "Cult Rising", "description": "A cult seeks to awaken an ancient evil."}
        ],
        "recent_npcs": [
            {"name": "High Priest", "role": "Villain", "first_impression": "Fanatical"}
        ],
        "pending_decisions": [
            {"made_by": "Gandalf", "decision": "Seal the vault", "consequences": None}
        ],
    }

    result = build_story_prompt_with_session_context(prompt, context)

    assert "Dark ritual" in result
    assert "Cult Rising" in result
    assert "High Priest" in result
    assert "Gandalf" in result
    print("  [OK] All context sections present")
    print("[PASS] build_story_prompt_with_session_context - all context types")


if __name__ == "__main__":
    test_session_notes_initialization()
    test_session_notes_add_event()
    test_session_notes_add_event_priority()
    test_session_notes_add_plot_thread_new()
    test_session_notes_add_plot_thread_existing()
    test_session_notes_resolve_plot_thread()
    test_session_notes_add_npc_introduction()
    test_session_notes_add_player_decision()
    test_session_notes_serialization_roundtrip()
    test_manager_save_and_load()
    test_manager_load_missing_returns_none()
    test_manager_get_all_session_notes_empty()
    test_manager_get_all_session_notes_sorted()
    test_manager_get_recent_notes()
    test_manager_get_active_plot_threads()
    test_manager_get_npc_introductions()
    test_manager_get_campaign_timeline()
    test_manager_get_context_for_story_generation()
    test_manager_export_timeline_markdown()
    test_build_story_prompt_no_context()
    test_build_story_prompt_with_events()
    test_build_story_prompt_with_all_context()
    print("\n[ALL TESTS PASSED]")
