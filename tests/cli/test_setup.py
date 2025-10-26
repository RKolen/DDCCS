"""Tests for the CLI setup utilities in `src.cli.setup`.

Verifies that `create_vscode_configuration` writes `tasks.json` and
`settings.json` into a `.vscode` directory within the current working
directory. The test runs inside a temporary directory to avoid modifying
the repository workspace.
"""

import json
import os
from pathlib import Path
import tempfile

from tests.test_helpers import setup_test_environment, import_module

setup_test_environment()

setup_mod = import_module("src.cli.setup")


def test_create_vscode_configuration_writes_files():
    """create_vscode_configuration should produce .vscode/tasks.json and settings.json."""
    cwd = os.getcwd()
    with tempfile.TemporaryDirectory() as td:
        try:
            os.chdir(td)
            ok = setup_mod.create_vscode_configuration()
            assert ok is True

            vscode_dir = Path(td) / ".vscode"
            assert vscode_dir.exists() and vscode_dir.is_dir()

            tasks_path = vscode_dir / "tasks.json"
            settings_path = vscode_dir / "settings.json"

            assert tasks_path.exists()
            assert settings_path.exists()

            # Basic sanity check on JSON contents
            tasks = json.loads(tasks_path.read_text(encoding="utf-8"))
            settings = json.loads(settings_path.read_text(encoding="utf-8"))

            assert "tasks" in tasks
            assert "files.associations" in settings
        finally:
            os.chdir(cwd)
