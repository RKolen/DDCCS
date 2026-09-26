"""Every third-party import must be declared in the requirements files.

A package installed on a developer's machine but missing from
`requirements.txt` is invisible to every other gate, because every other gate
runs in the environment that already has it. Pylint resolves the import,
mypy and pyright resolve it, the tests pass, and the first machine to install
only what is declared - a CI runner, or somebody's fresh clone - gets an
`E0401` or a service that will not start.

That is not hypothetical. `rembg` went undeclared while
`src/story_images/composite.py` imported it at module scope, and the sidecar
app imports that chain at startup, so a clean install produced a sidecar that
could not boot at all. Local gates were green the whole time.

Import names and distribution names differ often enough that a hand-written
table would rot, so the mapping comes from installed metadata rather than
from a list here. An import nothing provides is left alone: nothing installs
it, so pylint's import-error already covers that case, and reporting it twice
would only make this gate wrong about optional extras.
"""

import ast
import sys
from importlib import metadata
from pathlib import Path
from typing import Dict, List, NamedTuple, Set

from src.validation.gate import run_check

REQUIREMENTS = ("requirements.txt", "requirements-dev.txt")
SOURCE_DIRS = ("src", "tests")

# Package directories that are this project, not a dependency.
FIRST_PARTY = {"src", "tests"}


class Finding(NamedTuple):
    """One import that no requirements file declares."""

    module: str
    distribution: str
    path: str
    line: int


def normalise(name: str) -> str:
    """Fold a distribution name to its comparable form.

    PEP 503 treats runs of `-`, `_` and `.` as equivalent and ignores case,
    so `python-dotenv`, `python_dotenv` and `Python.Dotenv` are one package.

    Args:
        name: A distribution name as written anywhere.

    Returns:
        The normalised form.
    """
    folded = name.strip().lower()
    for char in "_.":
        folded = folded.replace(char, "-")
    while "--" in folded:
        folded = folded.replace("--", "-")
    return folded


def declared(root: Path) -> Set[str]:
    """Read the distribution names the requirements files declare.

    Args:
        root: The repository root.

    Returns:
        Normalised distribution names.

    Raises:
        FileNotFoundError: If a requirements file is missing.
    """
    names: Set[str] = set()
    for filename in REQUIREMENTS:
        text = (root / filename).read_text(encoding="utf-8")
        for raw in text.splitlines():
            line = raw.split("#")[0].strip()
            if not line or line.startswith("-"):
                continue
            # Strip extras and any version specifier: "uvicorn[standard]>=0.22".
            name = line.split("[")[0]
            for marker in (">=", "<=", "==", "!=", "~=", ">", "<", ";"):
                name = name.split(marker)[0]
            if name.strip():
                names.add(normalise(name))
    return names


def imports_in(path: Path) -> Dict[str, int]:
    """Collect the top-level module names one file imports.

    Args:
        path: A Python source file.

    Returns:
        Module name -> the first line that imports it.

    Raises:
        SyntaxError: If the file does not parse.
    """
    # utf-8-sig, because at least one module carries a byte-order mark and
    # plain utf-8 reads it as an invalid character before parsing starts.
    tree = ast.parse(path.read_text(encoding="utf-8-sig"), str(path))
    found: Dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.setdefault(alias.name.split(".")[0], node.lineno)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.setdefault(node.module.split(".")[0], node.lineno)
    return found


def scan(root: Path) -> List[Finding]:
    """Find every installed third-party import no requirements file declares.

    Args:
        root: The repository root.

    Returns:
        The undeclared imports, in path order.
    """
    known = declared(root)
    stdlib = set(sys.stdlib_module_names)
    providers = metadata.packages_distributions()
    found: List[Finding] = []
    for source_dir in SOURCE_DIRS:
        for path in sorted((root / source_dir).rglob("*.py")):
            for module, line in sorted(imports_in(path).items()):
                if module in stdlib or module in FIRST_PARTY:
                    continue
                distributions = providers.get(module)
                if not distributions:
                    continue
                if any(normalise(dist) in known for dist in distributions):
                    continue
                found.append(Finding(
                    module=module,
                    distribution=distributions[0],
                    path=str(path.relative_to(root)),
                    line=line,
                ))
    return found


def format_report(found: List[Finding]) -> str:
    """Render the findings as a readable report.

    Args:
        found: The problems found.

    Returns:
        The report text.
    """
    if not found:
        return "Every third-party import is declared in the requirements."
    lines = [
        "Imported but not declared in requirements.txt or "
        "requirements-dev.txt.",
        "These resolve here only because the package is installed locally; a "
        "clean install gets an import error:",
        "",
    ]
    lines.extend(
        f"  {f.path}:{f.line}  imports {f.module} (provided by {f.distribution})"
        for f in found
    )
    return "\n".join(lines)


if __name__ == "__main__":
    sys.exit(run_check(scan, format_report))
