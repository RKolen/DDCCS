"""Unit tests for src.validation.example_world."""

import json
from pathlib import Path
from typing import Any

from tests.test_helpers import setup_test_environment, import_module


setup_test_environment()

ew = import_module("src.validation.example_world")

load_allowed = ew.load_allowed
load_live_names = ew.load_live_names
scan = ew.scan
format_report = ew.format_report


def _build_repo(root: Path, npc_name: str, allowed: Any) -> None:
    """Lay out a miniature repository for the checker to walk.

    Args:
        root: The temporary repository root.
        npc_name: The name declared by a live NPC file.
        allowed: The allowlist contents.
    """
    game = root / "game_data"
    (game / "npcs").mkdir(parents=True)
    (game / "npcs" / "villain.json").write_text(
        json.dumps({"name": npc_name}), encoding="utf-8"
    )
    (game / "example_world.json").write_text(
        json.dumps({"allowed": allowed}), encoding="utf-8"
    )


def test_allowlist_is_read(tmp_path: Path) -> None:
    """Names in example_world.json are the sanctioned ones."""
    _build_repo(tmp_path, "Someone Else", ["Aragorn", "Frodo Baggins"])
    assert load_allowed(tmp_path) == {"Aragorn", "Frodo Baggins"}


def test_allowed_names_are_not_live(tmp_path: Path) -> None:
    """A game_data name on the allowlist is not treated as live."""
    _build_repo(tmp_path, "Aragorn", ["Aragorn"])
    assert load_live_names(tmp_path) == set()


def test_unlisted_game_data_names_are_live(tmp_path: Path) -> None:
    """Anything in game_data that is not allowlisted counts as live."""
    _build_repo(tmp_path, "Some Villain", ["Aragorn"])
    assert load_live_names(tmp_path) == {"Some Villain"}


def test_party_members_are_collected(tmp_path: Path) -> None:
    """A party roster contributes its members, not just a name field."""
    _build_repo(tmp_path, "Aragorn", ["Aragorn"])
    (tmp_path / "game_data" / "party.json").write_text(
        json.dumps({"party_members": ["Aragorn", "Some Villain"]}), encoding="utf-8"
    )
    assert load_live_names(tmp_path) == {"Some Villain"}


def test_example_template_files_are_skipped(tmp_path: Path) -> None:
    """Placeholder templates carry names meant to be quoted in docs."""
    _build_repo(tmp_path, "Aragorn", ["Aragorn"])
    (tmp_path / "game_data" / "npcs" / "npc.example.json").write_text(
        json.dumps({"name": "Character Name 1"}), encoding="utf-8"
    )
    assert load_live_names(tmp_path) == set()


def test_scan_finds_a_live_name_in_code(tmp_path: Path) -> None:
    """A live name written into source is reported with its location."""
    _build_repo(tmp_path, "Some Villain", ["Aragorn"])
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "thing.py").write_text(
        '"""Doc."""\nNAME = "Some Villain"\n', encoding="utf-8"
    )
    hits = scan(tmp_path, load_live_names(tmp_path))
    assert hits == [("src/thing.py", 2, "Some Villain")]


def test_scan_ignores_game_data_and_personal_docs(tmp_path: Path) -> None:
    """The two places a live campaign is allowed to be written down."""
    _build_repo(tmp_path, "Some Villain", ["Aragorn"])
    personal = tmp_path / "docs" / "docs_personal"
    personal.mkdir(parents=True)
    (personal / "plan.md").write_text("Some Villain schemes.\n", encoding="utf-8")
    (tmp_path / "game_data" / "notes.md").write_text("Some Villain.\n", encoding="utf-8")
    assert scan(tmp_path, load_live_names(tmp_path)) == []


def test_scan_ignores_unscanned_file_types(tmp_path: Path) -> None:
    """A binary or unlisted suffix is not read."""
    _build_repo(tmp_path, "Some Villain", ["Aragorn"])
    (tmp_path / "notes.txt").write_text("Some Villain.\n", encoding="utf-8")
    assert scan(tmp_path, load_live_names(tmp_path)) == []


def test_scan_with_no_live_names_does_nothing(tmp_path: Path) -> None:
    """An empty live set never matches, rather than matching everything."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "thing.py").write_text("x = 1\n", encoding="utf-8")
    assert scan(tmp_path, set()) == []


def test_report_names_every_location() -> None:
    """The report groups locations under the name that was found."""
    text = format_report([("src/a.py", 3, "Some Villain"), ("docs/b.md", 9, "Some Villain")])
    assert "Some Villain" in text
    assert "src/a.py:3" in text
    assert "docs/b.md:9" in text


def test_report_is_quiet_when_clean() -> None:
    """A clean run says so rather than printing an empty list."""
    assert "No live-campaign names" in format_report([])
