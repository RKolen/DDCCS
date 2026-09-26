"""Unit tests for src.validation.dependency_declarations."""

from pathlib import Path
import tempfile

from tests.test_helpers import setup_test_environment, import_module


setup_test_environment()

dd = import_module("src.validation.dependency_declarations")

normalise = dd.normalise
declared = dd.declared
imports_in = dd.imports_in
scan = dd.scan
format_report = dd.format_report


def _repo(root: Path, requirements: str, source: str) -> None:
    """Lay out a miniature repository for the scanner.

    Args:
        root: The temporary repository root.
        requirements: Contents of requirements.txt.
        source: Contents of the one source file.
    """
    (root / "src").mkdir()
    (root / "tests").mkdir()
    (root / "requirements.txt").write_text(requirements, encoding="utf-8")
    (root / "requirements-dev.txt").write_text("pylint==4.0.5\n", encoding="utf-8")
    (root / "src" / "module.py").write_text(source, encoding="utf-8")


def test_normalise_folds_separators_and_case() -> None:
    """PEP 503 treats runs of -, _ and . as one separator."""
    print("\n[TEST] normalise")
    assert normalise("python-dotenv") == "python-dotenv"
    assert normalise("Python_Dotenv") == "python-dotenv"
    assert normalise("zope.interface") == "zope-interface"
    assert normalise("  Pillow  ") == "pillow"
    print("  [OK] Case and separators folded")


def test_declared_strips_extras_and_specifiers() -> None:
    """A requirement line carries far more than the name."""
    print("\n[TEST] declared - one name per line")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "requirements.txt").write_text(
            "uvicorn[standard]>=0.22.0  # comment\n"
            "openai>=1.0.0\n"
            "\n"
            "# a comment line\n"
            "Pillow>=10.0.0\n",
            encoding="utf-8",
        )
        (root / "requirements-dev.txt").write_text(
            "pylint==4.0.5    # gate\n", encoding="utf-8")
        names = declared(root)
    assert names == {"uvicorn", "openai", "pillow", "pylint"}, names
    print("  [OK] Extras, specifiers and comments stripped")


def test_imports_in_reads_both_forms_and_a_byte_order_mark() -> None:
    """`import x`, `from x import y`, and a file that opens with a BOM.

    At least one module in this repository carries a byte-order mark, and
    reading it as plain utf-8 fails to parse before the scan can start.
    """
    print("\n[TEST] imports_in")
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "module.py"
        path.write_text(
            '﻿"""Doc."""\n'
            "import os\n"
            "import openai.types\n"
            "from rembg import remove\n"
            "from . import sibling\n",
            encoding="utf-8",
        )
        found = imports_in(path)
    assert set(found) == {"os", "openai", "rembg"}, found
    assert found["rembg"] == 4
    print("  [OK] Both forms read, relative imports ignored, BOM survived")


def test_an_installed_but_undeclared_import_is_reported() -> None:
    """The failure this gate exists for.

    `rembg` was imported at module scope and never declared. Every local
    gate passed, because the package was installed locally - and the first
    clean install produced a sidecar that could not start.
    """
    print("\n[TEST] scan - installed but undeclared")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # pylint is installed and deliberately left out of requirements.txt;
        # requirements-dev.txt declares it, so it must NOT be reported. pip
        # is installed in every virtualenv and is declared nowhere, which is
        # the shape of the bug: present locally, absent from the contract.
        _repo(root, "openai>=1.0.0\n",
              '"""Doc."""\nimport pylint\nimport pip\n')
        found = scan(root)
    reported = {f.module for f in found}
    assert "pylint" not in reported, reported
    assert "pip" in reported, reported
    assert format_report(list(found)).count("pip") >= 1
    print("  [OK] Undeclared reported; the dev requirements count as declared")


def test_stdlib_and_first_party_are_never_reported() -> None:
    """Only third-party packages belong in requirements."""
    print("\n[TEST] scan - stdlib and first party")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _repo(root, "openai>=1.0.0\n",
              '"""Doc."""\nimport json\nimport pathlib\nimport src\nimport tests\n')
        assert scan(root) == []
    print("  [OK] Nothing reported for stdlib or this project")


def test_an_uninstalled_import_is_left_to_pylint() -> None:
    """Nothing provides it, so pylint's import-error already covers it.

    Reporting it here as well would make this gate wrong about an optional
    extra that is genuinely meant to be absent.
    """
    print("\n[TEST] scan - uninstalled imports")
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _repo(root, "openai>=1.0.0\n",
              '"""Doc."""\nimport not_installed_anywhere_at_all\n')
        assert scan(root) == []
    print("  [OK] Left alone, because pylint reports it as an import error")


def test_the_real_repository_declares_everything_it_imports() -> None:
    """The gate itself, run against this repository."""
    print("\n[TEST] scan - this repository")
    gate = import_module("src.validation.gate")
    found = scan(gate.repo_root())
    assert found == [], format_report(found)
    print("  [OK] Every third-party import is declared")


def run_all_tests() -> None:
    """Run every dependency-declaration test."""
    test_normalise_folds_separators_and_case()
    test_declared_strips_extras_and_specifiers()
    test_imports_in_reads_both_forms_and_a_byte_order_mark()
    test_an_installed_but_undeclared_import_is_reported()
    test_stdlib_and_first_party_are_never_reported()
    test_an_uninstalled_import_is_left_to_pylint()
    test_the_real_repository_declares_everything_it_imports()
    print("\n[PASS] All dependency-declaration tests passed.")


if __name__ == "__main__":
    run_all_tests()
