"""Keep the frontend colour palette in one place.

``frontend/src/styles/tokens.css`` is the palette. Every other stylesheet
consumes it and defines nothing that already lives there.

Three things go wrong without a check, and all three were found in the tree:

* A raw hex written where a token already holds that exact value, so the same
  colour exists under two spellings and only one of them moves when the palette
  is retuned.
* A stylesheet redefining a token ``tokens.css`` already defines. Because the
  feature sheets load after it, the copy silently wins and editing the palette
  file does nothing.
* A self-referential definition (``--x: var(--x)``), which is invalid at
  computed-value time and quietly drops the colour everywhere it is used.

Run from ``check.sh``; exits non-zero on any hit.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Set

STYLES_DIR = Path("frontend") / "src" / "styles"
TOKENS_FILE = "tokens.css"

_DEFINITION_RE = re.compile(r"^\s*--([a-z0-9-]+)\s*:\s*([^;]+);", re.MULTILINE)
_HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")


class Finding(NamedTuple):
    """One palette problem.

    Attributes:
        path: Stylesheet the problem is in, relative to the repository root.
        line: 1-indexed line number.
        message: What is wrong and what to do instead.
    """

    path: str
    line: int
    message: str


def repo_root() -> Path:
    """Return the repository root.

    Returns:
        The directory two levels above this module.
    """
    return Path(__file__).resolve().parents[2]


def load_tokens(styles: Path) -> Dict[str, str]:
    """Read the palette's token definitions.

    Args:
        styles: The stylesheet directory.

    Returns:
        Token name to declared value, empty when the palette is unreadable.
    """
    path = styles / TOKENS_FILE
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    tokens: Dict[str, str] = {}
    for name, value in _DEFINITION_RE.findall(text):
        tokens.setdefault(name, value.strip())
    return tokens


def hex_index(tokens: Dict[str, str]) -> Dict[str, List[str]]:
    """Index the palette by hex value.

    Args:
        tokens: Token name to declared value.

    Returns:
        Lowercased hex value to the token names holding it.
    """
    index: Dict[str, List[str]] = {}
    for name, value in tokens.items():
        match = _HEX_RE.fullmatch(value.strip())
        if match:
            index.setdefault(value.strip().lower(), []).append(name)
    return index


def universal_name(names: List[str]) -> str:
    """Pick the name to recommend when several tokens hold the same value.

    The more universal name wins. tokens.css is ordered from raw palette to
    semantic roles - Backgrounds, Gold, Text, then Semantic/Status - so the
    first name declared for a value is the one describing the colour itself,
    and the later ones describe what it happens to be used for. `#c9a96e` is
    `--color-gold-mid` before it is `--color-partial`.

    Args:
        names: Token names sharing a value, in declaration order.

    Returns:
        The name to recommend.
    """
    return names[0]


def check_file(
    path: Path,
    relative: str,
    tokens: Dict[str, str],
    by_hex: Dict[str, List[str]],
) -> List[Finding]:
    """Check one stylesheet against the palette.

    Args:
        path: The stylesheet to read.
        relative: Its path for reporting.
        tokens: The palette's token definitions.
        by_hex: The palette indexed by hex value.

    Returns:
        The problems found, in line order.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []

    found: List[Finding] = []
    for number, line in enumerate(text.splitlines(), start=1):
        definition = _DEFINITION_RE.match(line)
        if definition:
            name, value = definition.group(1), definition.group(2).strip()
            if value == f"var(--{name})":
                found.append(Finding(
                    relative, number,
                    f"--{name} is defined as itself, which drops the colour; "
                    f"delete it and let {TOKENS_FILE} provide it",
                ))
            elif name in tokens:
                found.append(Finding(
                    relative, number,
                    f"--{name} is already defined in {TOKENS_FILE}; "
                    "delete it rather than keeping a second copy",
                ))
            continue
        for hex_value in _HEX_RE.findall(line):
            names = by_hex.get(hex_value.lower())
            if names:
                found.append(Finding(
                    relative, number,
                    f"{hex_value} is already the palette's "
                    f"var(--{universal_name(names)}); use the token",
                ))
    return found


def scan(root: Path) -> List[Finding]:
    """Check every stylesheet except the palette itself.

    Args:
        root: The repository root.

    Returns:
        The problems found, in path order.
    """
    styles = root / STYLES_DIR
    tokens = load_tokens(styles)
    if not tokens:
        # Reporting "clean" because the palette could not be read is how a
        # broken check passes silently; say so and fail instead.
        return [Finding(
            str(STYLES_DIR / TOKENS_FILE), 0,
            "no token definitions could be read; the palette check cannot run",
        )]
    by_hex = hex_index(tokens)

    seen: Set[str] = set()
    found: List[Finding] = []
    for path in sorted(styles.glob("*.css")):
        if path.name == TOKENS_FILE or path.name in seen:
            continue
        seen.add(path.name)
        found.extend(check_file(path, str(STYLES_DIR / path.name), tokens, by_hex))
    return found


def format_report(found: List[Finding]) -> str:
    """Render the findings as a readable report.

    Args:
        found: The problems found.

    Returns:
        The report text.
    """
    if not found:
        return f"Palette is clean: no duplicate colours outside {TOKENS_FILE}."
    lines = [
        f"Colours defined outside {STYLES_DIR / TOKENS_FILE}, or written as raw",
        "hex when the palette already holds them:",
        "",
    ]
    lines.extend(f"  {f.path}:{f.line}  {f.message}" for f in found)
    return "\n".join(lines)


def main() -> int:
    """Run the check.

    Returns:
        0 when the palette is clean, 1 otherwise.
    """
    found = scan(repo_root())
    print(format_report(found))
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
