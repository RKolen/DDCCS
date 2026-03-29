"""NPC Management CLI Module

Handles major NPC management menu: listing, viewing details, and validating
major NPC profiles (BBEGs, recurring antagonists, key allies).
"""

from pathlib import Path
from src.utils.path_utils import get_major_npc_files
from src.npcs.npc_agents import load_npc_from_json
from src.validation.npc_validator import validate_npc_file
from src.utils.cli_utils import display_selection_menu


def _cr_label(challenge_rating) -> str:
    """Format a challenge rating value for display."""
    if challenge_rating is None:
        return "?"
    return str(challenge_rating)


def _print_section(title: str, items) -> None:
    """Print a labelled list section, skipping it when items is empty/None."""
    if not items:
        return
    print(f"\n  {title}:")
    if isinstance(items, list):
        for item in items:
            print(f"    - {item}")
    elif isinstance(items, dict):
        for key, value in items.items():
            print(f"    {key}: {value}")
    else:
        print(f"    {items}")


def _display_boss_mechanics(major) -> None:
    """Print legendary actions, lair actions, and regional effects."""
    if major.legendary_actions:
        avail = major.legendary_actions.get("available", "?")
        actions = major.legendary_actions.get("actions", [])
        print(f"\n  Legendary Actions ({avail}/turn):")
        for action in actions:
            cost = action.get("cost", 1)
            name = action.get("name", "?")
            print(f"    [{cost}] {name}")

    if major.lair_actions and major.lair_actions.get("enabled"):
        loc = major.lair_actions.get("lair_location", "unknown")
        actions = major.lair_actions.get("actions", [])
        print(f"\n  Lair Actions (at {loc}):")
        for action in actions:
            print(f"    - {action.get('name', '?')}")

    if major.regional_effects and major.regional_effects.get("enabled"):
        radius = major.regional_effects.get("radius_miles", "?")
        effects = major.regional_effects.get("effects", [])
        print(f"\n  Regional Effects ({radius} mi radius):")
        for effect in effects:
            print(f"    - {effect.get('name', '?')}")


def _display_major_npc_details(profile) -> None:
    """Print a formatted summary of a major NPC profile."""
    stats = profile.combat_stats
    major = profile.major_stats

    print(f"\n{'=' * 50}")
    print(f"  {profile.name.upper()}")
    if profile.nickname:
        print(f"  \"{profile.nickname}\"")
    print(f"  {profile.role}")
    print(f"{'=' * 50}")

    # Identity
    print(f"\n  Species : {profile.species}" +
          (f" ({profile.lineage})" if profile.lineage else ""))
    if stats:
        print(f"  Class   : {stats.dnd_class}" +
              (f" ({stats.subclass})" if stats.subclass else ""))
        print(f"  Level   : {stats.level}")
        cr_raw = getattr(profile.basic, "challenge_rating", None)
        if cr_raw is not None:
            print(f"  CR      : {_cr_label(cr_raw)}")
        print(f"  HP      : {stats.combat.max_hit_points}  "
              f"AC: {stats.combat.armor_class}  "
              f"Speed: {stats.combat.movement_speed} ft")
    print(f"  Faction : {profile.faction}")

    # Personality
    if profile.personality:
        print(f"\n  Personality: {profile.personality}")

    # Relationships
    if profile.relationships:
        _print_section("Relationships", profile.relationships)

    # Major-only fields
    if major:
        _print_section("Encounter Tactics", major.encounter_tactics)
        _print_section("Plot Hooks", major.plot_hooks)
        _print_section("Defeat Conditions", major.defeat_conditions)
        _display_boss_mechanics(major)

    # Notes
    if profile.notes:
        print(f"\n  Notes: {profile.notes}")

    print()


class NpcCLIManager:
    """Manages NPC-related CLI operations."""

    def __init__(self, workspace_path: str):
        """Initialize NPC CLI manager.

        Args:
            workspace_path: Workspace root directory path.
        """
        self.workspace_path = workspace_path

    def manage_npcs(self) -> None:
        """Major NPC management submenu."""
        while True:
            print("\n NPC MANAGEMENT")
            print("-" * 30)
            print("1. List Major NPCs")
            print("2. View Major NPC Details")
            print("3. Validate Major NPC Files")
            print("0. Back to Main Menu")

            choice = input("Enter your choice: ").strip()

            if choice == "1":
                self.list_major_npcs()
            elif choice == "2":
                self.view_major_npc()
            elif choice == "3":
                self.validate_major_npcs()
            elif choice == "0":
                break
            else:
                print("Invalid choice. Please try again.")

    def _get_major_npc_files(self):
        """Return sorted list of major NPC file paths."""
        return get_major_npc_files(self.workspace_path)

    def list_major_npcs(self) -> None:
        """Display a table of all major NPCs."""
        files = self._get_major_npc_files()
        if not files:
            print("\nNo major NPC files found in game_data/npcs/.")
            return

        print(f"\n{'=' * 60}")
        print("  MAJOR NPCs")
        print(f"{'=' * 60}")
        print(f"  {'Name':<28} {'Role':<20} {'Faction'}")
        print(f"  {'-' * 27} {'-' * 19} {'-' * 10}")

        for filepath in files:
            profile = load_npc_from_json(Path(filepath))
            name_display = profile.name[:27]
            role_display = profile.role[:19] if profile.role else "-"
            print(f"  {name_display:<28} {role_display:<20} {profile.faction}")

        print(f"\n  Total: {len(files)} major NPC(s)")

    def view_major_npc(self) -> None:
        """Select and display details for a major NPC."""
        files = self._get_major_npc_files()
        if not files:
            print("\nNo major NPC files found.")
            return

        profiles = [load_npc_from_json(Path(f)) for f in files]
        labels = [
            f"{p.name}  ({p.role})" for p in profiles
        ]

        idx = display_selection_menu(
            labels,
            title="[SELECT] Choose Major NPC",
            prompt="Select NPC",
            allow_zero_back=True,
        )
        if idx is None:
            return

        _display_major_npc_details(profiles[idx])

    def validate_major_npcs(self) -> None:
        """Validate all major NPC JSON files and report results."""
        files = self._get_major_npc_files()
        if not files:
            print("\nNo major NPC files to validate.")
            return

        print(f"\nValidating {len(files)} major NPC file(s)...\n")
        all_valid = True

        for filepath in files:
            is_valid, errors = validate_npc_file(filepath)
            filename = Path(filepath).name
            if is_valid:
                print(f"  [OK]     {filename}")
            else:
                all_valid = False
                print(f"  [FAIL]   {filename}")
                for error in errors:
                    print(f"             - {error}")

        print()
        if all_valid:
            print("[OK] All major NPC files are valid.")
        else:
            print("[WARN] Some major NPC files have validation errors.")
