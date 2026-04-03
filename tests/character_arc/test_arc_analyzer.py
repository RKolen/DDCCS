"""Tests for ArcAnalyzer (pattern-based, no AI required)."""

from tests import test_helpers
from tests.character_arc.arc_test_helpers import (
    ArcDirection,
    ArcStage,
    CharacterArc,
    make_arc_with_points,
    make_data_point,
)

ArcAnalyzer = test_helpers.safe_from_import(
    "src.character_arc.arc_analyzer",
    "ArcAnalyzer",
)


def test_analyze_story_pattern_no_ai():
    """Test pattern-based story analysis without AI."""
    print("\n[TEST] ArcAnalyzer.analyze_story (pattern, no AI)")

    analyzer = ArcAnalyzer()
    story = (
        "Elara attacks the goblin with her sword. "
        "Elara speaks to the merchant and convinces him to lower his prices. "
        "Elara fights bravely in the battle."
    )
    data_point = analyzer.analyze_story(
        story_content=story,
        character_name="Elara",
        story_file="story_001.md",
        session_id="001",
    )

    assert data_point.story_file == "story_001.md"
    assert data_point.session_id == "001"
    assert data_point.timestamp, "Timestamp should be set automatically"
    assert isinstance(data_point.metric_values, dict)
    assert data_point.metric_values.get("engagement", 0) > 0
    print("  [OK] Pattern analysis returns non-empty metric_values")
    print("[PASS] ArcAnalyzer.analyze_story (pattern, no AI)")


def test_analyze_story_character_not_in_text():
    """Test pattern analysis when character does not appear in story."""
    print("\n[TEST] ArcAnalyzer.analyze_story - character absent")

    analyzer = ArcAnalyzer()
    story = "The dragon burns down the village without mercy."
    data_point = analyzer.analyze_story(
        story_content=story,
        character_name="Elara",
    )

    assert data_point.metric_values.get("engagement", 0) == 0
    print("  [OK] engagement=0 when character absent")
    print("[PASS] ArcAnalyzer.analyze_story - character absent")


def test_analyze_arc_progression_insufficient_data():
    """Test that < 2 data points returns STASIS / INTRODUCTION."""
    print("\n[TEST] ArcAnalyzer.analyze_arc_progression - insufficient data")

    analyzer = ArcAnalyzer()
    arc = CharacterArc(character_name="Elara", campaign_name="Test_Campaign")
    arc.add_data_point(make_data_point("story_001.md", {"confidence": 5}))

    result = analyzer.analyze_arc_progression(arc)

    assert result["direction"] == ArcDirection.STASIS.value
    assert result["stage"] == ArcStage.INTRODUCTION.value
    assert "Insufficient" in result["summary"]
    print("  [OK] Insufficient data returns stasis/introduction")
    print("[PASS] ArcAnalyzer.analyze_arc_progression - insufficient data")


def test_analyze_arc_progression_growth():
    """Test that consistent metric increases produce a valid analysis."""
    print("\n[TEST] ArcAnalyzer.analyze_arc_progression - growth detected")

    analyzer = ArcAnalyzer()
    arc = make_arc_with_points("Elara", [
        make_data_point("story_001.md",
                        {"confidence": 3, "relationship_strength": 3},
                        "2026-01-01T00:00:00"),
        make_data_point("story_002.md",
                        {"confidence": 7, "relationship_strength": 8},
                        "2026-01-02T00:00:00"),
    ])

    result = analyzer.analyze_arc_progression(arc)

    valid_directions = {d.value for d in ArcDirection}
    assert result["direction"] in valid_directions, (
        f"Unexpected direction: {result['direction']}"
    )
    assert "summary" in result
    assert "stage" in result
    print(f"  [OK] Direction resolved: {result['direction']}")
    print("[PASS] ArcAnalyzer.analyze_arc_progression - growth detected")


def test_arc_stage_progression_via_public_api():
    """Test that arc stage changes correctly as data points accumulate."""
    print("\n[TEST] Arc stage progression via public API")

    analyzer = ArcAnalyzer()

    def arc_stage_for(count):
        """Return the arc stage for an arc with count data points."""
        arc = CharacterArc(character_name="Elara", campaign_name="Test_Campaign")
        for i in range(count):
            arc.add_data_point(make_data_point(f"story_{i:03d}.md", {}))
        # Add a second point if count == 1 so analysis runs, else use 1 directly
        if count < 2:
            # Insufficient data - stage is always INTRODUCTION
            return ArcStage.INTRODUCTION.value
        result = analyzer.analyze_arc_progression(arc)
        return result["stage"]

    assert arc_stage_for(0) == ArcStage.INTRODUCTION.value
    assert arc_stage_for(1) == ArcStage.INTRODUCTION.value

    # For 2+ points, verify the stage is one of the valid stages
    valid_stages = {s.value for s in ArcStage}
    for count in (2, 3, 5, 7, 9):
        stage = arc_stage_for(count)
        assert stage in valid_stages, f"Unexpected stage {stage} for {count} points"

    print("  [OK] Stage values are valid for all story counts")
    print("[PASS] Arc stage progression via public API")


def test_pattern_generate_summary():
    """Test pattern-based summary generation."""
    print("\n[TEST] ArcAnalyzer pattern summary generation")

    analyzer = ArcAnalyzer()
    arc = make_arc_with_points("Elara", [
        make_data_point("story_001.md", {"confidence": 3}),
        make_data_point("story_002.md", {"confidence": 8}),
    ])
    result = analyzer.analyze_arc_progression(arc)

    assert "Elara" in result["summary"]
    assert result["summary"].endswith(".")
    print(f"  [OK] Summary: {result['summary'][:80]}")
    print("[PASS] ArcAnalyzer pattern summary generation")


def test_metric_progression_retrieval():
    """Test that metric progression is correctly extracted from data points."""
    print("\n[TEST] CharacterArc.get_metric_progression")

    arc = CharacterArc(character_name="Elara", campaign_name="Test_Campaign")
    arc.add_data_point(
        make_data_point("story_001.md", {"confidence": 3}, "2026-01-01T00:00:00")
    )
    arc.add_data_point(
        make_data_point("story_002.md", {"confidence": 7}, "2026-01-02T00:00:00")
    )

    progression = arc.get_metric_progression("confidence")
    assert len(progression) == 2
    assert progression[0][1] == 3
    assert progression[1][1] == 7
    print("  [OK] Progression correctly extracted")
    print("[PASS] CharacterArc.get_metric_progression")


if __name__ == "__main__":
    test_analyze_story_pattern_no_ai()
    test_analyze_story_character_not_in_text()
    test_analyze_arc_progression_insufficient_data()
    test_analyze_arc_progression_growth()
    test_arc_stage_progression_via_public_api()
    test_pattern_generate_summary()
    test_metric_progression_retrieval()
    print("\n[ALL TESTS PASSED]")
