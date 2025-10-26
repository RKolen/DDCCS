"""Unit tests for src.utils.story_parsing_utils."""

from test_helpers import setup_test_environment, import_module


setup_test_environment()

sp = import_module("src.utils.story_parsing_utils")
extract_character_actions = sp.extract_character_actions
extract_dc_requests = sp.extract_dc_requests


def test_extract_character_actions_from_action_log() -> None:
    """Extract actions from explicit CHARACTER/ACTION blocks."""
    content = (
        "CHARACTER: Frodo\n"
        "ACTION: Open the chest\n"
        "REASONING: Curious\n\n"
        "CHARACTER: Sam\n"
        "ACTION: Stand guard\n"
    )
    # Call the extractor; type ignored to keep the line length within limits
    result = extract_character_actions(content, ["Frodo", "Sam"])  # type: ignore
    assert "Frodo" in result
    assert any("Open the chest" in a for a in result["Frodo"])
    assert "Sam" in result


def test_extract_character_actions_from_narrative_mentions() -> None:
    """If no explicit block exists, narrative mentions provide sentence snippets.

    This verifies that sentences mentioning a character are returned when no
    explicit action block exists.
    """
    content = (
        "A loud crash echoed as Gandalf strode through the hall. "
        "He shouted and charged forward."
    )
    result = extract_character_actions(content, ["Gandalf"])  # type: ignore
    assert "Gandalf" in result
    assert any("Gandalf" in s for s in result["Gandalf"])


def test_extract_dc_requests_found_and_cleaned() -> None:
    """DC suggestions section lines are extracted and markdown formatting removed."""
    content = (
        "## DC Suggestions Needed\n"
        "- *Pick a lock*\n"
        "Find the secret door\n"
        "\n"
    )
    reqs = extract_dc_requests(content)
    assert isinstance(reqs, list)
    assert "Pick a lock" in reqs[0]
    assert "Find the secret door" in reqs[1]


def test_extract_dc_requests_not_present() -> None:
    """When the DC section is missing, return an empty list."""
    assert extract_dc_requests("No dc here") == []
