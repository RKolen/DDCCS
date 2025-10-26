"""Unit tests for src.utils.story_formatting_utils."""

from typing import Dict, Any

from tests.test_helpers import setup_test_environment, import_module


setup_test_environment()

sf = import_module("src.utils.story_formatting_utils")
generate_consultant_notes = sf.generate_consultant_notes
generate_consistency_section = sf.generate_consistency_section


def test_generate_consultant_notes_empty() -> None:
    """Empty analysis should return the no-notes placeholder."""
    out = generate_consultant_notes({})
    assert "No consultant notes generated" in out


def test_generate_consultant_notes_with_dc_and_consultant() -> None:
    """Ensure DC suggestions and consultant analyses are rendered."""
    analysis: Dict[str, Any] = {
        "dc_suggestions": {
            "Open Door": {
                "Frodo": {
                    "suggested_dc": 12,
                    "reasoning": "Simple lockpick",
                    "alternative_approaches": ["Kick door", "Find key"],
                }
            }
        },
        "consultant_analyses": {
            "Frodo": {"suggestions": ["Be cautious"]}
        },
    }

    out = generate_consultant_notes(analysis)
    assert "DC Suggestions" in out
    assert "Open Door" in out
    assert "Frodo" in out
    assert "Be cautious" in out


def test_generate_consistency_section_basic() -> None:
    """Basic consistency section formatting contains overall summary and character entries."""
    analysis: Dict[str, Any] = {
        "overall_consistency": {"rating": "Good", "score": 0.9, "summary": "Mostly consistent"},
        "consultant_analyses": {
            "Gandalf": {
                "overall_rating": "OK",
                "consistency_score": 0.8,
                "positive_notes": ["Steadfast"],
                "issues": ["Occasional verbosity"],
            }
        },
    }

    out = generate_consistency_section(analysis)
    assert "Overall Consistency" in out
    assert "Gandalf" in out
    assert "Positive aspects" in out or "Positive aspects" in out
