"""Command history management for the CLI."""

import json
import operator
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

_HISTORY_CACHE: Dict[str, Any] = {}


@dataclass
class HistoryEntry:
    """A single command history entry."""

    command: str
    timestamp: str
    session_id: str = ""
    working_dir: str = ""
    success: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a dictionary.

        Returns:
            Dictionary representation of this entry.
        """
        return {
            "command": self.command,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "working_dir": self.working_dir,
            "success": self.success,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HistoryEntry":
        """Deserialize from a dictionary.

        Args:
            data: Dictionary with entry fields.

        Returns:
            HistoryEntry instance.
        """
        return cls(
            command=data["command"],
            timestamp=data["timestamp"],
            session_id=data.get("session_id", ""),
            working_dir=data.get("working_dir", ""),
            success=data.get("success", True),
        )


class CommandHistory:
    """Manages persistent command history across CLI sessions.

    History is stored as JSON in ~/.dnd_consultant/command_history.json and
    is trimmed to MAX_HISTORY entries automatically.
    """

    HISTORY_FILE = "command_history.json"
    MAX_HISTORY = 1000

    def __init__(self, history_dir: Optional[str] = None) -> None:
        """Initialize command history.

        Args:
            history_dir: Directory to store the history file. Defaults to
                ~/.dnd_consultant.
        """
        self.history_dir: Path = (
            Path(history_dir) if history_dir else Path.home() / ".dnd_consultant"
        )
        self.history_path: Path = self.history_dir / self.HISTORY_FILE
        self._history: List[HistoryEntry] = []
        self._session_id: str = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._session_index: int = 0
        self._load_history()

    def _load_history(self) -> None:
        """Load history entries from disk, silently ignoring missing/corrupt files."""
        if not self.history_path.exists():
            return
        try:
            with open(self.history_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            self._history = [
                HistoryEntry.from_dict(entry) for entry in data.get("entries", [])
            ]
        except (OSError, json.JSONDecodeError):
            self._history = []
        self._session_index = len(self._history)

    def _save_history(self) -> None:
        """Persist history entries to disk."""
        self.history_dir.mkdir(parents=True, exist_ok=True)
        data: Dict[str, Any] = {
            "version": 1,
            "last_updated": datetime.now().isoformat(),
            "entries": [e.to_dict() for e in self._history],
        }
        with open(self.history_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2)

    def add_command(self, command: str, success: bool = True) -> None:
        """Record a command in history.

        Consecutive duplicate commands are silently ignored.

        Args:
            command: Command string to record.
            success: Whether the command completed successfully.
        """
        if self._history and self._history[-1].command == command:
            return
        entry = HistoryEntry(
            command=command,
            timestamp=datetime.now().isoformat(),
            session_id=self._session_id,
            working_dir=os.getcwd(),
            success=success,
        )
        self._history.append(entry)
        self._session_index = len(self._history)
        if len(self._history) > self.MAX_HISTORY:
            self._history = self._history[-self.MAX_HISTORY :]
        self._save_history()

    def get_previous(self) -> Optional[str]:
        """Return the previous history entry relative to the current index.

        Returns:
            Command string, or None if already at the beginning.
        """
        if self._session_index > 0:
            self._session_index -= 1
            return self._history[self._session_index].command
        return None

    def get_next(self) -> Optional[str]:
        """Return the next history entry relative to the current index.

        Returns:
            Command string, or None if already at the end.
        """
        if self._session_index < len(self._history) - 1:
            self._session_index += 1
            return self._history[self._session_index].command
        self._session_index = len(self._history)
        return None

    def search(self, query: str) -> List[HistoryEntry]:
        """Return entries whose command contains the query substring.

        Args:
            query: Case-insensitive substring to search for.

        Returns:
            Matching history entries in chronological order.
        """
        query_lower = query.lower()
        return [e for e in self._history if query_lower in e.command.lower()]

    def get_session_commands(self) -> List[HistoryEntry]:
        """Return entries recorded in the current session.

        Returns:
            Entries belonging to the current session.
        """
        return [e for e in self._history if e.session_id == self._session_id]

    def get_recent(self, limit: int = 10) -> List[HistoryEntry]:
        """Return the most recent entries.

        Args:
            limit: Maximum number of entries to return.

        Returns:
            Up to limit entries, most recent last.
        """
        return self._history[-limit:]

    def clear(self) -> None:
        """Remove all history entries and persist the empty state."""
        self._history = []
        self._session_index = 0
        self._save_history()

    def get_stats(self) -> Dict[str, Any]:
        """Return usage statistics.

        Returns:
            Dictionary with keys: total_commands, sessions, most_common
            (list of (command, count) tuples), oldest, newest.
        """
        if not self._history:
            return {
                "total_commands": 0,
                "sessions": 0,
                "most_common": [],
                "oldest": None,
                "newest": None,
            }

        command_counts: Dict[str, int] = {}
        for entry in self._history:
            base = entry.command.split()[0] if entry.command else ""
            command_counts[base] = command_counts.get(base, 0) + 1

        sessions = {e.session_id for e in self._history}
        most_common = sorted(
            command_counts.items(),
            key=operator.itemgetter(1),
            reverse=True,
        )[:5]

        return {
            "total_commands": len(self._history),
            "sessions": len(sessions),
            "most_common": most_common,
            "oldest": self._history[0].timestamp,
            "newest": self._history[-1].timestamp,
        }


def get_command_history() -> CommandHistory:
    """Return the module-level CommandHistory singleton.

    Returns:
        Shared CommandHistory instance, created on first call.
    """
    if "instance" not in _HISTORY_CACHE:
        _HISTORY_CACHE["instance"] = CommandHistory()
    return _HISTORY_CACHE["instance"]
