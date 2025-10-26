"""Unit tests for markdown utilities in src.utils.markdown_utils."""

from tests.test_helpers import setup_test_environment, import_module


setup_test_environment()

md_utils = import_module("src.utils.markdown_utils")
update_markdown_section = md_utils.update_markdown_section
extract_markdown_section = md_utils.extract_markdown_section


def test_update_existing_section() -> None:
    """Updating an existing section should replace its contents."""
    original = "# Title\n\n## Notes\nOld content\n\n"
    updated = update_markdown_section(original, "Notes", "New content")

    # Extract should return the new content
    extracted = extract_markdown_section(updated, "Notes")
    assert "New content" in extracted


def test_add_new_section() -> None:
    """Adding a section that doesn't exist should append it to the document."""
    original = "# Title\n\nSome intro text.\n"
    result = update_markdown_section(original, "Scene", "Scene details")

    assert "## Scene" in result
    assert "Scene details" in result


def test_extract_missing_section_returns_empty() -> None:
    """Extracting a missing section should return an empty string."""
    content = "# Only Title\n\nNo sections here.\n"
    assert extract_markdown_section(content, "Nonexistent") == ""
