"""Tests for arc criteria and metrics definitions."""

from tests import test_helpers
from tests.character_arc.arc_test_helpers import ArcDimension, ArcDirection, ArcStage

ArcMetric = test_helpers.safe_from_import(
    "src.character_arc.arc_criteria",
    "ArcMetric",
)
ArcCriteria = test_helpers.safe_from_import(
    "src.character_arc.arc_criteria",
    "ArcCriteria",
)
STANDARD_METRICS = test_helpers.safe_from_import(
    "src.character_arc.arc_criteria",
    "STANDARD_METRICS",
)


def test_arc_dimension_values():
    """Test that ArcDimension enum has expected values."""
    print("\n[TEST] ArcDimension enum values")

    assert ArcDimension.PERSONALITY.value == "personality"
    assert ArcDimension.RELATIONSHIPS.value == "relationships"
    assert ArcDimension.ABILITIES.value == "abilities"
    assert ArcDimension.GOALS.value == "goals"
    assert ArcDimension.BELIEFS.value == "beliefs"
    assert ArcDimension.REPUTATION.value == "reputation"
    assert ArcDimension.TRAUMA.value == "trauma"
    assert ArcDimension.GROWTH.value == "growth"
    print("  [OK] All dimension values correct")
    print("[PASS] ArcDimension enum values")


def test_arc_direction_values():
    """Test that ArcDirection enum has expected values."""
    print("\n[TEST] ArcDirection enum values")

    assert ArcDirection.GROWTH.value == "growth"
    assert ArcDirection.DECLINE.value == "decline"
    assert ArcDirection.STASIS.value == "stasis"
    assert ArcDirection.FLUCTUATION.value == "fluctuation"
    assert ArcDirection.TRANSFORMATION.value == "transformation"
    print("  [OK] All direction values correct")
    print("[PASS] ArcDirection enum values")


def test_arc_stage_values():
    """Test that ArcStage enum has expected values."""
    print("\n[TEST] ArcStage enum values")

    assert ArcStage.INTRODUCTION.value == "introduction"
    assert ArcStage.ESTABLISHMENT.value == "establishment"
    assert ArcStage.CHALLENGE.value == "challenge"
    assert ArcStage.DEVELOPMENT.value == "development"
    assert ArcStage.CLIMAX.value == "climax"
    assert ArcStage.RESOLUTION.value == "resolution"
    assert ArcStage.AFTERMATH.value == "aftermath"
    print("  [OK] All stage values correct")
    print("[PASS] ArcStage enum values")


def test_standard_metrics_not_empty():
    """Test that STANDARD_METRICS contains metrics."""
    print("\n[TEST] STANDARD_METRICS not empty")

    assert STANDARD_METRICS, "STANDARD_METRICS must not be empty"
    print(f"  [OK] {len(STANDARD_METRICS)} standard metrics defined")
    print("[PASS] STANDARD_METRICS not empty")


def test_standard_metrics_have_required_fields():
    """Test that each standard metric has required fields."""
    print("\n[TEST] Standard metrics have required fields")

    for metric in STANDARD_METRICS:
        assert metric.metric_id, f"metric_id missing on {metric}"
        assert metric.name, f"name missing on {metric}"
        assert isinstance(metric.dimension, ArcDimension), (
            f"dimension must be ArcDimension on {metric}"
        )
        assert metric.measurement_type in ("numeric", "categorical", "text"), (
            f"invalid measurement_type on {metric}"
        )
    print(f"  [OK] All {len(STANDARD_METRICS)} metrics pass field checks")
    print("[PASS] Standard metrics have required fields")


def test_arc_criteria_defaults():
    """Test that ArcCriteria initializes with sensible defaults."""
    print("\n[TEST] ArcCriteria defaults")

    criteria = ArcCriteria()
    assert criteria.dimensions, "dimensions must not be empty"
    assert criteria.metrics, "metrics must not be empty"
    assert criteria.min_stories_for_analysis == 2
    assert 0 < criteria.significance_threshold < 1
    print("  [OK] Defaults are sane")
    print("[PASS] ArcCriteria defaults")


def test_arc_criteria_get_metrics_for_dimension():
    """Test filtering metrics by dimension."""
    print("\n[TEST] ArcCriteria.get_metrics_for_dimension")

    criteria = ArcCriteria()
    relationship_metrics = criteria.get_metrics_for_dimension(ArcDimension.RELATIONSHIPS)
    assert relationship_metrics, "Expected at least one RELATIONSHIPS metric"

    for metric in relationship_metrics:
        assert metric.dimension == ArcDimension.RELATIONSHIPS

    none_metrics = criteria.get_metrics_for_dimension(ArcDimension.POSSESSIONS)
    assert isinstance(none_metrics, list)
    print("  [OK] Filtering by dimension works correctly")
    print("[PASS] ArcCriteria.get_metrics_for_dimension")


def test_arc_criteria_custom_metrics():
    """Test that custom metrics can be provided to ArcCriteria."""
    print("\n[TEST] ArcCriteria custom metrics")

    custom_metric = ArcMetric(
        metric_id="custom_test",
        name="Custom Test Metric",
        dimension=ArcDimension.GROWTH,
        description="A test metric",
        measurement_type="numeric",
        scale_range=(0, 5),
    )
    criteria = ArcCriteria(metrics=[custom_metric])
    assert len(criteria.metrics) == 1
    assert criteria.metrics[0].metric_id == "custom_test"
    print("  [OK] Custom metrics accepted")
    print("[PASS] ArcCriteria custom metrics")


if __name__ == "__main__":
    test_arc_dimension_values()
    test_arc_direction_values()
    test_arc_stage_values()
    test_standard_metrics_not_empty()
    test_standard_metrics_have_required_fields()
    test_arc_criteria_defaults()
    test_arc_criteria_get_metrics_for_dimension()
    test_arc_criteria_custom_metrics()
    print("\n[ALL TESTS PASSED]")
