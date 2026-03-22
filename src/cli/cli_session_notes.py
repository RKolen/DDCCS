"""CLI interface for session notes management.

Provides an interactive menu-driven workflow for DMs to view, add, and
export session notes within a campaign.
"""

import os
from typing import Optional

from src.sessions.session_notes import NotePriority, PlotStatus
from src.sessions.session_notes_manager import SessionNotesManager
from src.utils.string_utils import get_session_date


def session_notes_menu(campaign_name: str, workspace_path: Optional[str] = None) -> None:
    """Interactive session notes management menu for a campaign.

    Args:
        campaign_name: Name of the campaign to manage notes for.
        workspace_path: Optional workspace root path.
    """
    manager = SessionNotesManager(campaign_name, workspace_path)

    while True:
        print(f"\n=== Session Notes: {campaign_name} ===")
        print("1. View recent session notes")
        print("2. View campaign timeline")
        print("3. View active plot threads")
        print("4. Add notes to a session")
        print("5. Export timeline to markdown")
        print("0. Back")

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            _view_recent_notes(manager)
        elif choice == "2":
            _view_timeline(manager)
        elif choice == "3":
            _view_plot_threads(manager)
        elif choice == "4":
            _add_session_notes(manager)
        elif choice == "5":
            _export_timeline(manager)
        elif choice == "0":
            break
        else:
            print("Invalid choice.")


def _view_recent_notes(manager: SessionNotesManager) -> None:
    """Display the five most recent session notes.

    Args:
        manager: SessionNotesManager instance for the campaign.
    """
    recent = manager.get_recent_notes(5)

    if not recent:
        print("\n[INFO] No session notes found.")
        return

    for notes in recent:
        print(f"\n--- Session: {notes.session_id} ({notes.session_date}) ---")
        print(f"Summary: {notes.summary or 'No summary'}")

        if notes.events:
            print("\nEvents:")
            for event in notes.events[:5]:
                desc = event.description
                preview = (desc[:50] + "...") if len(desc) > 50 else desc
                print(f"  - {event.title}: {preview}")

        if notes.plot_threads:
            print("\nPlot threads:")
            for thread in notes.plot_threads[:3]:
                print(f"  - [{thread.status.value}] {thread.name}")

        if notes.npc_introductions:
            print("\nNPCs met:")
            for npc in notes.npc_introductions[:3]:
                print(f"  - {npc.name} ({npc.role})")


def _view_timeline(manager: SessionNotesManager) -> None:
    """Display the last ten events in the campaign timeline.

    Args:
        manager: SessionNotesManager instance for the campaign.
    """
    timeline = manager.get_campaign_timeline()

    if not timeline:
        print("\n[INFO] No events recorded yet.")
        return

    print(f"\n=== Campaign Timeline ({len(timeline)} events) ===")
    print("[Showing last 10 events]")

    for event in timeline[-10:]:
        print(f"\n[{event['date']}] [Session {event['session_id']}] {event['title']}")
        print(f"  {event['description']}")
        if event["location"]:
            print(f"  Location: {event['location']}")


def _view_plot_threads(manager: SessionNotesManager) -> None:
    """Display all active (unresolved) plot threads.

    Args:
        manager: SessionNotesManager instance for the campaign.
    """
    threads = manager.get_active_plot_threads()

    if not threads:
        print("\n[INFO] No active plot threads.")
        return

    print(f"\n=== Active Plot Threads ({len(threads)}) ===")

    for thread in threads:
        print(f"\n** {thread['name']} **")
        print(f"  {thread['description']}")
        if thread["notes"]:
            recent_notes = thread["notes"][-3:]
            print(f"  Recent notes: {', '.join(recent_notes)}")


def _collect_event(notes) -> None:
    """Prompt the user to enter an event and add it to the notes.

    Args:
        notes: SessionNotes instance to update.
    """
    title = input("Event title: ").strip()
    if not title:
        print("[ERROR] Title cannot be empty.")
        return
    description = input("Event description: ").strip()
    characters_raw = input("Characters involved (comma-separated, or blank): ").strip()
    characters = [c.strip() for c in characters_raw.split(",")] if characters_raw else []

    print("Priority: 1=critical, 2=important, 3=minor, 4=flavor [default: 2]")
    prio_input = input("Priority: ").strip()
    priority_map = {
        "1": NotePriority.CRITICAL,
        "2": NotePriority.IMPORTANT,
        "3": NotePriority.MINOR,
        "4": NotePriority.FLAVOR,
    }
    priority = priority_map.get(prio_input, NotePriority.IMPORTANT)

    notes.add_event(title=title, description=description, characters=characters, priority=priority)
    print("[OK] Event recorded.")


def _collect_plot_thread(notes) -> None:
    """Prompt the user to enter a plot thread and add it to the notes.

    Args:
        notes: SessionNotes instance to update.
    """
    name = input("Plot thread name: ").strip()
    if not name:
        print("[ERROR] Name cannot be empty.")
        return
    description = input("Description: ").strip()
    print("Status: 1=introduced, 2=active, 3=resolved, 4=abandoned [default: 1]")
    status_input = input("Status: ").strip()
    status_map = {
        "1": PlotStatus.INTRODUCED,
        "2": PlotStatus.ACTIVE,
        "3": PlotStatus.RESOLVED,
        "4": PlotStatus.ABANDONED,
    }
    status = status_map.get(status_input, PlotStatus.INTRODUCED)
    notes.add_plot_thread(name, description, status)
    print("[OK] Plot thread recorded.")


def _collect_npc(notes) -> None:
    """Prompt the user to enter an NPC introduction and add it to the notes.

    Args:
        notes: SessionNotes instance to update.
    """
    name = input("NPC name: ").strip()
    if not name:
        print("[ERROR] Name cannot be empty.")
        return
    role = input("NPC role (e.g. innkeeper, guard): ").strip()
    location = input("Location where met: ").strip()
    impression = input("First impression: ").strip()
    relationship = input("Relationship to party [Neutral]: ").strip() or "Neutral"
    npc = notes.add_npc_introduction(name, role, location, impression)
    npc.relationship_to_party = relationship
    print("[OK] NPC introduction recorded.")


def _collect_decision(notes) -> None:
    """Prompt the user to enter a player decision and add it to the notes.

    Args:
        notes: SessionNotes instance to update.
    """
    decision = input("Decision made: ").strip()
    if not decision:
        print("[ERROR] Decision cannot be empty.")
        return
    made_by = input("Made by (character name): ").strip()
    consequences = input("Known consequences (or blank): ").strip() or None
    notes.add_player_decision(decision, made_by, consequences=consequences)
    print("[OK] Decision recorded.")


def _add_session_notes(manager: SessionNotesManager) -> None:
    """Interactively add notes to an existing or new session.

    Args:
        manager: SessionNotesManager instance for the campaign.
    """
    session_id = input("\nEnter session ID (existing) or 'new' for a new session: ").strip()

    if session_id.lower() == "new":
        session_id = input("Enter new session ID (e.g. 001): ").strip()
        if not session_id:
            print("[ERROR] Session ID cannot be empty.")
            return
        notes = manager.create_session_notes(session_id)
        print(f"[INFO] New session notes created for session {session_id} ({get_session_date()})")
    else:
        notes = manager.load_session_notes(session_id)
        if notes is None:
            print(f"[ERROR] Session '{session_id}' not found. Use 'new' to create it.")
            return
        print(f"[INFO] Loaded session {session_id} ({notes.session_date})")

    add_handlers = {
        "1": _collect_event,
        "2": _collect_plot_thread,
        "3": _collect_npc,
        "4": _collect_decision,
    }

    while True:
        print("\nWhat would you like to add?")
        print("1. Event")
        print("2. Plot thread")
        print("3. NPC introduction")
        print("4. Player decision")
        print("5. Update summary")
        print("0. Save and exit")

        choice = input("Select: ").strip()

        if choice == "0":
            break
        if choice == "5":
            notes.summary = input("Session summary: ").strip()
            print("[OK] Summary updated.")
        elif choice in add_handlers:
            add_handlers[choice](notes)
        else:
            print("Invalid choice.")

    manager.save_session_notes(notes)
    print(f"\n[SUCCESS] Notes saved for session {session_id}")


def _export_timeline(manager: SessionNotesManager) -> None:
    """Export the campaign timeline to a markdown file.

    Writes to ``<campaign_dir>/campaign_timeline.md``.

    Args:
        manager: SessionNotesManager instance for the campaign.
    """
    markdown = manager.export_timeline_markdown()
    output_path = os.path.join(manager.campaign_dir, "campaign_timeline.md")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"\n[SUCCESS] Timeline exported to: {output_path}")
