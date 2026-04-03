"""Shared helpers and imports for character arc tests."""

from tests import test_helpers

ArcDimension = test_helpers.safe_from_import(
    "src.character_arc.arc_criteria",
    "ArcDimension",
)
ArcDirection = test_helpers.safe_from_import(
    "src.character_arc.arc_criteria",
    "ArcDirection",
)
ArcStage = test_helpers.safe_from_import(
    "src.character_arc.arc_criteria",
    "ArcStage",
)
ArcDataPoint = test_helpers.safe_from_import(
    "src.character_arc.arc_data",
    "ArcDataPoint",
)
CharacterArc = test_helpers.safe_from_import(
    "src.character_arc.arc_data",
    "CharacterArc",
)


def make_data_point(story_file, metric_values, timestamp="2026-01-01T00:00:00"):
    """Create an ArcDataPoint with given metric values."""
    return ArcDataPoint(
        story_file=story_file,
        session_id="test",
        timestamp=timestamp,
        metric_values=metric_values,
    )


def make_arc_with_points(character_name, data_points):
    """Create a CharacterArc and attach data points."""
    arc = CharacterArc(character_name=character_name, campaign_name="Test_Campaign")
    for data_point in data_points:
        arc.add_data_point(data_point)
    return arc
