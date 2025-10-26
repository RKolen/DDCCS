"""Unit tests for file I/O utilities in src.utils.file_io.

These tests exercise JSON and text read/write helpers and directory
helpers in an isolated temporary directory.
"""
from typing import Dict
from pathlib import Path

from test_helpers import setup_test_environment, import_module


setup_test_environment()

file_io = import_module("src.utils.file_io")


# Local helpers resolved from the imported module to keep tests readable
load_json_file = file_io.load_json_file
save_json_file = file_io.save_json_file
read_text_file = file_io.read_text_file
write_text_file = file_io.write_text_file
read_text_file_lines = file_io.read_text_file_lines
file_exists = file_io.file_exists
directory_exists = file_io.directory_exists
ensure_directory = file_io.ensure_directory
get_json_files_in_directory = file_io.get_json_files_in_directory


def test_save_and_load_json(tmp_path: Path) -> None:
    """Saving then loading a JSON file should preserve the data."""
    target_dir = tmp_path / "data" / "sub"
    target_file = target_dir / "test.json"
    data: Dict[str, int] = {"value": 42}

    save_json_file(str(target_file), data)

    assert file_exists(str(target_file))

    loaded = load_json_file(str(target_file))
    assert isinstance(loaded, dict)
    assert loaded.get("value") == 42


def test_text_read_write_and_lines(tmp_path: Path) -> None:
    """Text helpers should write and read content and lines correctly."""
    txt_file = tmp_path / "notes" / "note.txt"
    content = "Line1\nLine2\n"

    write_text_file(str(txt_file), content)

    read_back = read_text_file(str(txt_file))
    assert read_back == content

    lines = read_text_file_lines(str(txt_file))
    assert isinstance(lines, list)
    # readlines keeps newline characters
    assert lines[0].strip() == "Line1"
    assert lines[1].strip() == "Line2"


def test_directory_helpers_and_json_listing(tmp_path: Path) -> None:
    """Ensure directories are created and json listing honors exclude patterns."""
    d = tmp_path / "jsons"
    ensure_directory(str(d))
    assert directory_exists(str(d))

    file_a = d / "data.json"
    file_b = d / "example.json"

    save_json_file(str(file_a), {"a": 1})
    save_json_file(str(file_b), {"b": 2})

    files = get_json_files_in_directory(str(d), exclude_patterns=["example"])
    # Only data.json should remain after excluding pattern
    names = [p.name for p in files]
    assert "data.json" in names
    assert "example.json" not in names
