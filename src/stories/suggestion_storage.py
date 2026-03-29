"""
Suggestion Storage System

Persists and retrieves AI story suggestions for a campaign.
Suggestions are stored as a single JSON file per campaign inside the
campaign directory.
"""

import json
import os
from datetime import datetime
from typing import List, Optional

from src.utils.file_io import ensure_directory
from src.utils.path_utils import get_campaign_path
from src.stories.suggestion_types import StorySuggestion, SuggestionSet, SuggestionType

_SUGGESTIONS_FILENAME = "suggestions.json"


def get_suggestions_path(campaign_name: str, workspace_path: Optional[str] = None) -> str:
    """Return the path to a campaign's suggestions JSON file.

    Args:
        campaign_name: Name of the campaign.
        workspace_path: Optional workspace root path.

    Returns:
        Absolute path string to the suggestions file.
    """
    campaign_path = get_campaign_path(campaign_name, workspace_path)
    return os.path.join(campaign_path, _SUGGESTIONS_FILENAME)


def save_suggestions(
    suggestion_set: SuggestionSet,
    workspace_path: Optional[str] = None,
) -> bool:
    """Append new suggestions to the campaign's suggestions file.

    Existing suggestions are preserved. New suggestions from suggestion_set
    are appended to them before writing.

    Args:
        suggestion_set: SuggestionSet containing new suggestions to persist.
        workspace_path: Optional workspace root path.

    Returns:
        True if the save succeeded, False on error.
    """
    try:
        suggestions_path = get_suggestions_path(
            suggestion_set.campaign_name, workspace_path
        )
        ensure_directory(os.path.dirname(suggestions_path))

        existing = load_suggestions(suggestion_set.campaign_name, workspace_path)

        for new_suggestion in suggestion_set.suggestions:
            existing.suggestions.append(new_suggestion)

        with open(suggestions_path, "w", encoding="utf-8") as file_handle:
            json.dump(existing.to_dict(), file_handle, indent=2)

        return True

    except (OSError, ValueError) as exc:
        print(f"[ERROR] Failed to save suggestions: {exc}")
        return False


def load_suggestions(
    campaign_name: str,
    workspace_path: Optional[str] = None,
) -> SuggestionSet:
    """Load all suggestions for a campaign.

    Args:
        campaign_name: Name of the campaign.
        workspace_path: Optional workspace root path.

    Returns:
        SuggestionSet with stored suggestions, or an empty set on failure.
    """
    suggestions_path = get_suggestions_path(campaign_name, workspace_path)

    if not os.path.exists(suggestions_path):
        return SuggestionSet(campaign_name=campaign_name, story_file=None)

    try:
        with open(suggestions_path, "r", encoding="utf-8") as file_handle:
            data = json.load(file_handle)
        return SuggestionSet.from_dict(data)

    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"[WARNING] Could not load suggestions: {exc}")
        return SuggestionSet(campaign_name=campaign_name, story_file=None)


def update_suggestion_status(
    campaign_name: str,
    suggestion_index: int,
    accepted: Optional[bool],
    user_notes: Optional[str] = None,
    workspace_path: Optional[str] = None,
) -> bool:
    """Update the accepted status and optional notes for a single suggestion.

    Args:
        campaign_name: Name of the campaign.
        suggestion_index: Zero-based index into the full suggestions list.
        accepted: True to accept, False to reject, None to keep existing status.
        user_notes: Optional freetext DM notes for this suggestion.
        workspace_path: Optional workspace root path.

    Returns:
        True if the update succeeded, False otherwise.
    """
    suggestion_set = load_suggestions(campaign_name, workspace_path)

    if suggestion_index < 0 or suggestion_index >= len(suggestion_set.suggestions):
        return False

    suggestion = suggestion_set.suggestions[suggestion_index]
    if accepted is not None:
        suggestion.review.accepted = accepted
    suggestion.review.user_notes = user_notes

    try:
        suggestions_path = get_suggestions_path(campaign_name, workspace_path)
        with open(suggestions_path, "w", encoding="utf-8") as file_handle:
            json.dump(suggestion_set.to_dict(), file_handle, indent=2)
        return True
    except OSError as exc:
        print(f"[ERROR] Failed to update suggestion: {exc}")
        return False


def get_pending_suggestions(
    campaign_name: str,
    workspace_path: Optional[str] = None,
) -> List[StorySuggestion]:
    """Return all unreviewed suggestions for a campaign.

    Args:
        campaign_name: Name of the campaign.
        workspace_path: Optional workspace root path.

    Returns:
        List of pending StorySuggestion objects.
    """
    return load_suggestions(campaign_name, workspace_path).get_pending()


def get_suggestions_by_type(
    campaign_name: str,
    suggestion_type: SuggestionType,
    workspace_path: Optional[str] = None,
) -> List[StorySuggestion]:
    """Return all suggestions of a specific type for a campaign.

    Args:
        campaign_name: Name of the campaign.
        suggestion_type: The SuggestionType to filter for.
        workspace_path: Optional workspace root path.

    Returns:
        List of matching StorySuggestion objects.
    """
    return load_suggestions(campaign_name, workspace_path).get_by_type(suggestion_type)


def clear_old_suggestions(
    campaign_name: str,
    days_old: int = 30,
    workspace_path: Optional[str] = None,
) -> int:
    """Remove suggestions older than the specified number of days.

    Accepted or rejected suggestions are never removed.  Only pending
    suggestions that have aged past the threshold are cleared.

    Args:
        campaign_name: Name of the campaign.
        days_old: Age threshold in days (default 30).
        workspace_path: Optional workspace root path.

    Returns:
        Number of suggestions removed.
    """
    suggestion_set = load_suggestions(campaign_name, workspace_path)
    cutoff = datetime.now().timestamp() - (days_old * 24 * 60 * 60)

    original_count = len(suggestion_set.suggestions)
    suggestion_set.suggestions = [
        s for s in suggestion_set.suggestions
        if s.review.accepted is not None or s.context.created_at.timestamp() > cutoff
    ]

    removed = original_count - len(suggestion_set.suggestions)

    if removed > 0:
        updated_set = SuggestionSet(
            campaign_name=campaign_name,
            story_file=suggestion_set.story_file,
            suggestions=suggestion_set.suggestions,
        )
        save_suggestions(updated_set, workspace_path)

    return removed
