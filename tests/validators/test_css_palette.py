"""Unit tests for src.validation.css_palette."""

from pathlib import Path

from tests.test_helpers import setup_test_environment, import_module


setup_test_environment()

cp = import_module("src.validation.css_palette")

load_tokens = cp.load_tokens
hex_index = cp.hex_index
universal_name = cp.universal_name
scan = cp.scan
format_report = cp.format_report
STYLES_DIR = cp.STYLES_DIR

TOKENS = """:root {
  --color-gold-mid: #c9a96e;
  --color-text-primary: #e8d5b0;
  --color-partial: #c9a96e;
}
"""


def _styles(root: Path) -> Path:
    """Create the stylesheet directory with a palette in it.

    Args:
        root: The temporary repository root.

    Returns:
        The stylesheet directory.
    """
    styles = root / STYLES_DIR
    styles.mkdir(parents=True)
    (styles / "tokens.css").write_text(TOKENS, encoding="utf-8")
    return styles


def test_tokens_are_read_from_the_palette(tmp_path: Path) -> None:
    """Every definition in tokens.css is loaded, not just the first."""
    styles = _styles(tmp_path)
    assert load_tokens(styles) == {
        "color-gold-mid": "#c9a96e",
        "color-text-primary": "#e8d5b0",
        "color-partial": "#c9a96e",
    }


def test_hex_index_groups_shared_values(tmp_path: Path) -> None:
    """Two tokens holding one value are both indexed under it."""
    index = hex_index(load_tokens(_styles(tmp_path)))
    assert index["#c9a96e"] == ["color-gold-mid", "color-partial"]


def test_universal_name_prefers_the_first_declared() -> None:
    """The palette is ordered palette-first, so the earlier name is generic."""
    assert universal_name(["color-gold-mid", "color-partial"]) == "color-gold-mid"


def test_raw_hex_that_has_a_token_is_reported(tmp_path: Path) -> None:
    """A colour the palette already holds must use the token."""
    styles = _styles(tmp_path)
    (styles / "screen.css").write_text(".a { color: #c9a96e; }\n", encoding="utf-8")
    found = scan(tmp_path)
    assert len(found) == 1
    assert "var(--color-gold-mid)" in found[0].message


def test_redefining_a_palette_token_is_reported(tmp_path: Path) -> None:
    """A second copy silently wins over the palette, so it is a defect."""
    styles = _styles(tmp_path)
    (styles / "screen.css").write_text(
        ":root {\n  --color-gold-mid: #123456;\n}\n", encoding="utf-8"
    )
    found = scan(tmp_path)
    assert len(found) == 1
    assert "already defined" in found[0].message


def test_self_referential_definition_is_reported(tmp_path: Path) -> None:
    """`--x: var(--x)` is invalid and drops the colour wherever it is used."""
    styles = _styles(tmp_path)
    (styles / "screen.css").write_text(":root {\n  --thing: var(--thing);\n}\n", encoding="utf-8")
    found = scan(tmp_path)
    assert len(found) == 1
    assert "defined as itself" in found[0].message


def test_a_colour_with_no_token_is_left_alone(tmp_path: Path) -> None:
    """One-off colours the palette does not hold are not the check's business."""
    styles = _styles(tmp_path)
    (styles / "screen.css").write_text(".a { color: #010203; }\n", encoding="utf-8")
    assert scan(tmp_path) == []


def test_the_palette_itself_is_not_scanned(tmp_path: Path) -> None:
    """tokens.css is where colours are declared; it cannot violate itself."""
    _styles(tmp_path)
    assert scan(tmp_path) == []


def test_unreadable_palette_fails_rather_than_passing(tmp_path: Path) -> None:
    """A check that cannot read the palette must not report success."""
    (tmp_path / STYLES_DIR).mkdir(parents=True)
    found = scan(tmp_path)
    assert len(found) == 1
    assert "cannot run" in found[0].message


def test_report_is_quiet_when_clean() -> None:
    """A clean palette says so rather than printing an empty list."""
    assert "Palette is clean" in format_report([])
