"""Interactive menu for CLI enhancement features: history and batch operations."""

from typing import List, Optional

from src.cli.batch_operations import BatchProcessor, BatchResult, batch_add_item, batch_level_up
from src.cli.completion import get_character_names
from src.cli.history import CommandHistory, get_command_history
from src.utils.cli_utils import confirm_action, display_selection_menu, print_section_header
from src.utils.terminal_display import print_error, print_info, print_success


class CLIEnhancementsMenu:
    """Interactive menu for history viewing and batch operations.

    Provides sub-menus for:
    - Viewing, searching, and clearing persistent command history
    - Batch level-up and item distribution across characters
    """

    def __init__(self) -> None:
        """Initialize with the shared history singleton."""
        self._history: CommandHistory = get_command_history()

    def run(self) -> None:
        """Run the enhancements menu until the user chooses Back."""
        while True:
            print_section_header("Tools & Batch Operations")
            print("1. View Recent History")
            print("2. Search History")
            print("3. History Statistics")
            print("4. Clear History")
            print("5. Batch Level-Up Characters")
            print("6. Batch Add Item to Characters")
            print("0. Back")
            print()

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self._show_recent_history()
            elif choice == "2":
                self._search_history()
            elif choice == "3":
                self._show_history_stats()
            elif choice == "4":
                self._clear_history()
            elif choice == "5":
                self._batch_level_up()
            elif choice == "6":
                self._batch_add_item()
            elif choice == "0":
                break
            else:
                print_error("Invalid choice. Please try again.")

    # ------------------------------------------------------------------ history

    def _show_recent_history(self) -> None:
        """Display the most recent history entries."""
        limit_input = input("How many entries to show? [10] ").strip()
        limit = int(limit_input) if limit_input.isdigit() else 10
        entries = self._history.get_recent(limit)

        if not entries:
            print_info("No command history recorded yet.")
            return

        print_section_header(f"Last {len(entries)} Commands")
        for entry in entries:
            date = entry.timestamp.split("T")[0]
            status = "[OK]" if entry.success else "[FAIL]"
            print(f"  {date} {status} {entry.command}")

    def _search_history(self) -> None:
        """Search history by keyword and display matches."""
        query = input("Search query: ").strip()
        if not query:
            return
        entries = self._history.search(query)
        if not entries:
            print_info(f"No history entries match '{query}'.")
            return
        print_section_header(f"History matches for '{query}'")
        for entry in entries:
            date = entry.timestamp.split("T")[0]
            print(f"  {date}  {entry.command}")

    def _show_history_stats(self) -> None:
        """Display usage statistics for the command history."""
        stats = self._history.get_stats()
        print_section_header("History Statistics")
        print(f"  Total commands : {stats['total_commands']}")
        print(f"  Sessions       : {stats['sessions']}")
        if stats["most_common"]:
            print("  Most used:")
            for cmd, count in stats["most_common"]:
                print(f"    {cmd}: {count}")

    def _clear_history(self) -> None:
        """Prompt for confirmation, then remove all history entries."""
        if confirm_action("Clear all command history? This cannot be undone."):
            self._history.clear()
            print_success("Command history cleared.")
        else:
            print_info("Clear cancelled.")

    # --------------------------------------------------------- batch operations

    def _batch_level_up(self) -> None:
        """Level up one or more characters by a chosen amount."""
        names = self._select_characters("Select characters to level up (0 = all)")
        if names is None:
            return

        amount_input = input("Levels to add [1]: ").strip()
        amount = (
            int(amount_input)
            if amount_input.isdigit() and int(amount_input) > 0
            else 1
        )

        processor = BatchProcessor()
        results = processor.process_characters(
            batch_level_up(amount),
            names if names else None,
            progress_callback=lambda n, i, t: print(f"  [{i}/{t}] {n}"),
        )
        self.print_batch_results(results)

    def _batch_add_item(self) -> None:
        """Add an item with a chosen quantity to one or more characters."""
        item_name = input("Item name: ").strip()
        if not item_name:
            print_error("Item name cannot be empty.")
            return

        qty_input = input("Quantity [1]: ").strip()
        quantity = (
            int(qty_input) if qty_input.isdigit() and int(qty_input) > 0 else 1
        )

        names = self._select_characters("Select characters to receive the item (0 = all)")
        if names is None:
            return

        processor = BatchProcessor()
        results = processor.process_characters(
            batch_add_item(item_name, quantity),
            names if names else None,
            progress_callback=lambda n, i, t: print(f"  [{i}/{t}] {n}"),
        )
        self.print_batch_results(results)

    # ----------------------------------------------------------------- helpers

    def _select_characters(self, prompt: str) -> Optional[List[str]]:
        """Let the user pick one character or all from the known list.

        Args:
            prompt: Description shown above the selection menu.

        Returns:
            A list with one character name, an empty list meaning "all
            characters", or None if the user cancelled.
        """
        all_names = get_character_names()
        if not all_names:
            print_error("No character files found.")
            return None

        print_info(prompt)
        choices = all_names + ["-- All characters --"]
        idx = display_selection_menu(
            choices,
            title="Characters",
            prompt="Select",
            allow_zero_back=True,
        )
        if idx is None:
            print_info("Cancelled.")
            return None
        if choices[idx] == "-- All characters --":
            return []
        return [choices[idx]]

    @staticmethod
    def print_batch_results(results: List[BatchResult]) -> None:
        """Display a summary of batch operation results.

        Args:
            results: List of BatchResult instances to display.
        """
        successes = sum(1 for r in results if r.success)
        print_section_header(f"Batch Results ({successes}/{len(results)} succeeded)")
        for result in results:
            if result.success:
                print_success(f"  {result.item}: {result.message}")
            else:
                print_error(f"  {result.item}: {result.message}")
