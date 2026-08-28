"""Keep live-campaign characters out of the shared codebase.

Only the Example Campaign world may be named in code, tests, and
documentation. A live campaign's cast belongs in ``game_data/`` and
``docs/docs_personal/`` and nowhere else.

The rule is not about tidiness. A test fixture written with a live NPC puts
someone's real campaign into the shared repository, and worse, anything the
console later shows a model - an arc roster, a relationship candidate list -
will keep proposing those names because they are the ones on record. That is
how a bbeg from one campaign ended up attached to an Example Campaign test arc.

Every name in ``game_data`` that is not in ``game_data/example_world.json`` is
treated as live. Run from ``check.sh``; exits non-zero on any hit.
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Where a live name is allowed to appear. Everything else is scanned.
EXEMPT_DIRS = (
    "game_data",
    "docs/docs_personal",
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "public",
    ".cache",
    "vendor",
)

SCANNED_SUFFIXES = (
    ".py",
    ".pyi",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".md",
    ".php",
    ".yml",
    ".yaml",
    ".json",
    ".css",
    ".graphqls",
)

# A name needs at least this many characters before it is worth matching, so a
# short handle cannot collide with ordinary prose.
MIN_NAME_CHARS = 4


def repo_root() -> Path:
    """Return the repository root.

    Returns:
        The directory two levels above this module.
    """
    return Path(__file__).resolve().parents[2]


def _names_in(path: Path) -> Set[str]:
    """Read every character or NPC name out of one game_data file.

    Args:
        path: A JSON file under game_data.

    Returns:
        The names it declares, empty when it declares none.
    """
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    if not isinstance(data, dict):
        return set()
    found: Set[str] = set()
    name = data.get("name")
    if isinstance(name, str) and name.strip():
        found.add(name.strip())
    members = data.get("party_members")
    if isinstance(members, list):
        found.update(str(m).strip() for m in members if str(m).strip())
    return found


def load_allowed(root: Path) -> Set[str]:
    """Read the Example Campaign allowlist.

    Args:
        root: The repository root.

    Returns:
        The names that may appear anywhere in the repository.
    """
    path = root / "game_data" / "example_world.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return set()
    allowed = data.get("allowed", []) if isinstance(data, dict) else []
    return {str(name).strip() for name in allowed if str(name).strip()}


def load_live_names(root: Path) -> Set[str]:
    """Collect every game_data name that is not on the allowlist.

    Example-file templates are skipped: they carry placeholder names that are
    meant to be quoted in documentation.

    Args:
        root: The repository root.

    Returns:
        The live-campaign names to keep out of the codebase.
    """
    allowed = load_allowed(root)
    live: Set[str] = set()
    for path in (root / "game_data").rglob("*.json"):
        if ".example." in path.name or path.name == "example_world.json":
            continue
        live.update(_names_in(path))
    return {
        name for name in live
        if name not in allowed and len(name) >= MIN_NAME_CHARS
    }


def _is_exempt(path: Path, root: Path) -> bool:
    """Report whether a path is somewhere live names are allowed.

    Args:
        path: The file being considered.
        root: The repository root.

    Returns:
        True when the file must not be scanned.
    """
    relative = path.relative_to(root).as_posix()
    return any(
        relative == part or relative.startswith(f"{part}/") or f"/{part}/" in f"/{relative}"
        for part in EXEMPT_DIRS
    )


def scan(root: Path, names: Set[str]) -> List[Tuple[str, int, str]]:
    """Find live-campaign names anywhere they are not allowed.

    Args:
        root: The repository root.
        names: The live names to look for.

    Returns:
        One (path, line number, name) per hit, in path order.
    """
    if not names:
        return []
    pattern = re.compile(
        "|".join(re.escape(name) for name in sorted(names, key=len, reverse=True))
    )
    hits: List[Tuple[str, int, str]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in SCANNED_SUFFIXES:
            continue
        if _is_exempt(path, root):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            match = pattern.search(line)
            if match:
                hits.append((path.relative_to(root).as_posix(), number, match.group(0)))
    return hits


def format_report(hits: List[Tuple[str, int, str]]) -> str:
    """Render the hits as a readable report.

    Args:
        hits: The scan results.

    Returns:
        The report text.
    """
    if not hits:
        return "No live-campaign names outside game_data/ and docs/docs_personal/."
    by_name: Dict[str, List[str]] = {}
    for path, number, name in hits:
        by_name.setdefault(name, []).append(f"{path}:{number}")
    lines = [
        "Live-campaign names found outside game_data/ and docs/docs_personal/.",
        "Only the Example Campaign world may be named in code, tests, and docs.",
        "",
    ]
    for name in sorted(by_name):
        lines.append(f"  {name}")
        lines.extend(f"    {place}" for place in by_name[name])
    lines.extend(
        [
            "",
            "Use an Example Campaign character instead, or add the name to",
            "game_data/example_world.json if it genuinely belongs to that world.",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    """Run the check.

    Returns:
        0 when nothing was found, 1 otherwise.
    """
    root = repo_root()
    hits = scan(root, load_live_names(root))
    print(format_report(hits))
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
