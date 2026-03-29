"""
CLI Interface for Story Suggestions

Provides an interactive menu-driven workflow for DMs to generate, review,
and manage AI-powered story suggestions within a campaign.
"""

import os
from typing import Any, Dict, List, Optional

from src.stories.suggestion_engine import SuggestionConfig, SuggestionEngine
from src.stories.suggestion_storage import (
    clear_old_suggestions,
    get_pending_suggestions,
    load_suggestions,
    save_suggestions,
    update_suggestion_status,
)
from src.stories.suggestion_types import StorySuggestion, SuggestionType
from src.utils.file_io import read_text_file
from src.utils.path_utils import get_campaign_path
from src.utils.story_file_helpers import list_story_files
from src.utils.terminal_display import print_info, print_success, print_warning

# Human-readable labels for each suggestion type
_TYPE_LABELS: Dict[SuggestionType, str] = {
    SuggestionType.PLOT_HOOK: "Plot Hooks",
    SuggestionType.CHARACTER_MOMENT: "Character Moments",
    SuggestionType.PLOT_TWIST: "Plot Twists",
    SuggestionType.NARRATIVE_IMPROVEMENT: "Narrative Improvements",
    SuggestionType.NPC_INTERACTION: "NPC Interactions",
    SuggestionType.FORESHADOWING: "Foreshadowing",
}

_DESCRIPTION_PREVIEW_LEN = 100
_RATIONALE_PREVIEW_LEN = 80


def suggestions_menu(
    campaign_name: str,
    workspace_path: str,
    ai_client: Optional[Any] = None,
    party_profiles: Optional[Dict[str, Any]] = None,
    npc_data: Optional[List[Dict[str, Any]]] = None,
) -> None:
    """Interactive AI story suggestions menu for a campaign.

    Args:
        campaign_name: Name of the campaign to manage suggestions for.
        workspace_path: Workspace root directory path.
        ai_client: Optional initialised AIClient instance.
        party_profiles: Optional mapping of character name to profile dict.
        npc_data: Optional list of NPC profile dicts.
    """
    runner = SuggestionMenuRunner(campaign_name, workspace_path)
    runner.run(ai_client, party_profiles or {}, npc_data or [])


# ---------------------------------------------------------------------------
# Internal implementation class (not exported)
# ---------------------------------------------------------------------------


class SuggestionMenuRunner:
    """Drives the interactive suggestions menu for a single campaign."""

    def __init__(self, campaign_name: str, workspace_path: str) -> None:
        self._campaign_name = campaign_name
        self._workspace_path = workspace_path
        self._engine: Optional[SuggestionEngine] = None
        self._party_profiles: Dict[str, Any] = {}
        self._npc_data: List[Dict[str, Any]] = []

    def get_pending_count(self) -> int:
        """Return the number of pending (unreviewed) suggestions for the campaign.

        Returns:
            Count of suggestions awaiting DM review.
        """
        return len(get_pending_suggestions(self._campaign_name, self._workspace_path))

    def run(
        self,
        ai_client: Optional[Any],
        party_profiles: Dict[str, Any],
        npc_data: List[Dict[str, Any]],
    ) -> None:
        """Run the main suggestions menu loop.

        Args:
            ai_client: Optional initialised AIClient instance.
            party_profiles: Mapping of character name to profile dict.
            npc_data: List of NPC profile dicts.
        """
        self._engine = SuggestionEngine(ai_client)
        self._party_profiles = party_profiles
        self._npc_data = npc_data
        while True:
            print(f"\n=== AI Story Suggestions: {self._campaign_name} ===")
            print("1. Generate new suggestions")
            print("2. View pending suggestions")
            print("3. View all suggestions")
            print("4. View by type")
            print("5. Remove suggestions older than 30 days")
            print("0. Back")

            choice = input("\nSelect option: ").strip()

            if choice == "1":
                self._generate_flow()
            elif choice == "2":
                self._view_pending_flow()
            elif choice == "3":
                self._view_all_flow()
            elif choice == "4":
                self._view_by_type_flow()
            elif choice == "5":
                self._clear_old_flow()
            elif choice == "0":
                break
            else:
                print_warning("Invalid choice.")

    # ------------------------------------------------------------------
    # Menu actions
    # ------------------------------------------------------------------

    def _generate_flow(self) -> None:
        """Guide the DM through generating new suggestions."""
        if self._engine is None:
            return
        if self._engine.ai_client is None:
            print_warning("AI is not available. Configure AI first in settings.")
            return

        # Choose suggestion type(s)
        selected_types = self._select_suggestion_types()
        if selected_types is None:
            return

        print_info("Loading campaign data and generating suggestions...")

        story_content = self._get_latest_story_content()
        story_file = self._get_latest_story_filename()

        suggestion_set = self._engine.generate_comprehensive_suggestions(
            SuggestionConfig(
                campaign_name=self._campaign_name,
                story_content=story_content,
                story_file=story_file,
                party_profiles=self._party_profiles,
                npc_data=self._npc_data,
                suggestion_types=selected_types,
                count_per_type=2,
            )
        )

        if not suggestion_set.suggestions:
            print_warning("No suggestions were generated. Check your AI configuration.")
            return

        save_suggestions(suggestion_set, self._workspace_path)
        print_success(f"Generated {len(suggestion_set.suggestions)} suggestion(s).")
        _display_suggestion_list(suggestion_set.suggestions)

    def _view_pending_flow(self) -> None:
        """Display and allow action on all pending suggestions."""
        pending = get_pending_suggestions(self._campaign_name, self._workspace_path)

        if not pending:
            print_info("No pending suggestions.")
            return

        print(f"\n=== Pending Suggestions ({len(pending)}) ===")
        _display_suggestion_list(pending)
        self._action_menu(pending)

    def _view_all_flow(self) -> None:
        """Display all suggestions for the campaign."""
        suggestion_set = load_suggestions(self._campaign_name, self._workspace_path)

        if not suggestion_set.suggestions:
            print_info("No suggestions found for this campaign.")
            return

        print(f"\n=== All Suggestions ({len(suggestion_set.suggestions)}) ===")
        _display_suggestion_list(suggestion_set.suggestions)

    def _view_by_type_flow(self) -> None:
        """Display suggestions filtered by a chosen type."""
        print("\nSelect suggestion type to view:")
        type_list = list(_TYPE_LABELS.items())
        for idx, (_, label) in enumerate(type_list, 1):
            print(f"{idx}. {label}")

        selection = input("\nSelect: ").strip()
        try:
            chosen_type, _ = type_list[int(selection) - 1]
        except (ValueError, IndexError):
            print_warning("Invalid selection.")
            return

        suggestion_set = load_suggestions(self._campaign_name, self._workspace_path)
        filtered = suggestion_set.get_by_type(chosen_type)

        if not filtered:
            print_info(f"No {_TYPE_LABELS[chosen_type]} suggestions found.")
            return

        _display_suggestion_list(filtered)

    def _clear_old_flow(self) -> None:
        """Remove pending suggestions older than 30 days."""
        removed = clear_old_suggestions(
            self._campaign_name, days_old=30, workspace_path=self._workspace_path
        )
        if removed:
            print_info(f"Removed {removed} old suggestion(s).")
        else:
            print_info("No old suggestions to remove.")

    def _action_menu(self, suggestions: List[StorySuggestion]) -> None:
        """Allow the DM to accept, reject, or annotate suggestions."""
        while True:
            print("\n--- Actions ---")
            print("1. Accept a suggestion")
            print("2. Reject a suggestion")
            print("3. Add notes to a suggestion")
            print("0. Back")

            choice = input("\nSelect: ").strip()

            if choice == "1":
                self._set_suggestion_status(suggestions, accepted=True)
            elif choice == "2":
                self._set_suggestion_status(suggestions, accepted=False)
            elif choice == "3":
                self._add_notes(suggestions)
            elif choice == "0":
                break
            else:
                print_warning("Invalid choice.")

    def _set_suggestion_status(
        self, suggestions: List[StorySuggestion], accepted: bool
    ) -> None:
        """Accept or reject a suggestion by local list index.

        The local index maps directly to global index because view_pending
        presents suggestions in their original order from the stored list.

        Args:
            suggestions: Subset of suggestions currently displayed.
            accepted: True to accept, False to reject.
        """
        selection = input("Enter suggestion number: ").strip()
        try:
            idx = int(selection)
        except ValueError:
            print_warning("Invalid input.")
            return

        if idx < 0 or idx >= len(suggestions):
            print_warning("Invalid number.")
            return

        full_set = load_suggestions(self._campaign_name, self._workspace_path)
        global_idx = _find_global_index(full_set.suggestions, suggestions[idx])

        if global_idx < 0:
            print_warning("Could not locate suggestion.")
            return

        update_suggestion_status(
            self._campaign_name, global_idx, accepted=accepted,
            workspace_path=self._workspace_path,
        )
        verb = "accepted" if accepted else "rejected"
        print_success(f"Suggestion {idx} {verb}.")

    def _add_notes(self, suggestions: List[StorySuggestion]) -> None:
        """Attach DM notes to a suggestion.

        Args:
            suggestions: Subset of suggestions currently displayed.
        """
        selection = input("Enter suggestion number: ").strip()
        try:
            idx = int(selection)
        except ValueError:
            print_warning("Invalid input.")
            return

        if idx < 0 or idx >= len(suggestions):
            print_warning("Invalid number.")
            return

        notes = input("Enter notes: ").strip()
        full_set = load_suggestions(self._campaign_name, self._workspace_path)
        global_idx = _find_global_index(full_set.suggestions, suggestions[idx])

        if global_idx < 0:
            print_warning("Could not locate suggestion.")
            return

        update_suggestion_status(
            self._campaign_name, global_idx,
            accepted=None,
            user_notes=notes,
            workspace_path=self._workspace_path,
        )
        print_success("Notes saved.")

    # ------------------------------------------------------------------
    # Data helpers
    # ------------------------------------------------------------------

    def _select_suggestion_types(self) -> Optional[List[SuggestionType]]:
        """Prompt the DM to choose which suggestion types to generate.

        Returns:
            List of selected SuggestionType values, or None on invalid input.
            Returns all types when "All Types" is chosen.
        """
        print("\nSelect suggestion types to generate:")
        type_list = list(_TYPE_LABELS.items())
        for idx, (_, label) in enumerate(type_list, 1):
            print(f"{idx}. {label}")
        print(f"{len(type_list) + 1}. All Types")

        selection = input("\nSelect type (number): ").strip()
        try:
            idx = int(selection) - 1
        except ValueError:
            print_warning("Invalid input.")
            return None

        if idx == len(type_list):
            return None  # None means all types in generate_comprehensive_suggestions

        if 0 <= idx < len(type_list):
            return [type_list[idx][0]]

        print_warning("Invalid selection.")
        return None

    def _get_latest_story_content(self) -> str:
        """Return the content of the most recent story file in the campaign.

        Returns:
            Story text, or an empty string if no stories are found.
        """
        campaign_path = get_campaign_path(self._campaign_name, self._workspace_path)
        story_files = list_story_files(campaign_path)
        if not story_files:
            return ""
        latest = os.path.join(campaign_path, story_files[-1])
        return read_text_file(latest) or ""

    def _get_latest_story_filename(self) -> Optional[str]:
        """Return the filename of the most recent story in the campaign.

        Returns:
            Filename string, or None if no stories exist.
        """
        campaign_path = get_campaign_path(self._campaign_name, self._workspace_path)
        story_files = list_story_files(campaign_path)
        return story_files[-1] if story_files else None


# ---------------------------------------------------------------------------
# Module-level display helpers
# ---------------------------------------------------------------------------


def _display_suggestion_list(suggestions: List[StorySuggestion]) -> None:
    """Print a numbered list of suggestions to stdout.

    Args:
        suggestions: List of StorySuggestion objects to display.
    """
    for idx, suggestion in enumerate(suggestions):
        status = _status_label(suggestion.review.accepted)
        type_label = _TYPE_LABELS.get(suggestion.suggestion_type, "Unknown")
        print(f"\n{idx}. [{type_label}]{status} {suggestion.title}")
        desc_preview = suggestion.description[:_DESCRIPTION_PREVIEW_LEN]
        if len(suggestion.description) > _DESCRIPTION_PREVIEW_LEN:
            desc_preview += "..."
        print(f"   {desc_preview}")
        if suggestion.rationale:
            rationale_preview = suggestion.rationale[:_RATIONALE_PREVIEW_LEN]
            if len(suggestion.rationale) > _RATIONALE_PREVIEW_LEN:
                rationale_preview += "..."
            print(f"   Rationale: {rationale_preview}")
        if suggestion.context.implementation_notes:
            print(f"   Notes: {suggestion.context.implementation_notes[:80]}")
        if suggestion.review.user_notes:
            print(f"   DM Notes: {suggestion.review.user_notes}")


def _status_label(accepted: Optional[bool]) -> str:
    """Return a short status tag for display.

    Args:
        accepted: None for pending, True for accepted, False for rejected.

    Returns:
        A bracketed status string, or empty string for pending suggestions.
    """
    if accepted is True:
        return " [ACCEPTED]"
    if accepted is False:
        return " [REJECTED]"
    return ""


def _find_global_index(
    all_suggestions: List[StorySuggestion],
    target: StorySuggestion,
) -> int:
    """Return the index of target inside all_suggestions by identity.

    Falls back to matching by created_at + title if identity fails.

    Args:
        all_suggestions: Full list of stored suggestions.
        target: The suggestion to locate.

    Returns:
        Zero-based index, or -1 if not found.
    """
    for idx, suggestion in enumerate(all_suggestions):
        if suggestion is target:
            return idx

    # Fallback: match by content fingerprint
    for idx, suggestion in enumerate(all_suggestions):
        if (
            suggestion.context.created_at == target.context.created_at
            and suggestion.title == target.title
        ):
            return idx

    return -1
