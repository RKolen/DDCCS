"""Aggregator for all timeline tests."""

import sys
from tests import test_helpers

from tests.timeline.test_event_schema import (
    test_event_type_values,
    test_event_priority_values,
    test_timeline_event_defaults,
    test_generate_id_is_stable,
    test_generate_id_differs_for_different_events,
    test_to_dict_contains_all_fields,
    test_serialization_roundtrip,
    test_event_links_defaults,
)
from tests.timeline.test_event_extractor import (
    test_extract_combat_event,
    test_extract_no_events_from_neutral_text,
    test_extract_from_text_sets_campaign_and_story,
    test_split_sections_on_headers,
    test_extract_character_names,
    test_extract_location,
    test_extract_from_file_missing_returns_empty,
    test_ai_extractor_parse_valid_json,
    test_ai_extractor_parse_invalid_json,
)
from tests.timeline.test_timeline_store import (
    test_store_add_and_get_event,
    test_store_get_event_missing_returns_none,
    test_store_get_campaign_timeline,
    test_store_get_character_timeline,
    test_store_get_character_timeline_case_insensitive,
    test_store_query_by_campaign,
    test_store_query_by_event_type,
    test_store_query_by_priority,
    test_store_link_events,
    test_store_link_events_missing_returns_false,
    test_store_persistence_to_disk,
    test_store_reload_from_disk,
    test_store_get_campaign_names,
)

ALL_TESTS = [
    # Schema tests
    test_event_type_values,
    test_event_priority_values,
    test_timeline_event_defaults,
    test_generate_id_is_stable,
    test_generate_id_differs_for_different_events,
    test_to_dict_contains_all_fields,
    test_serialization_roundtrip,
    test_event_links_defaults,
    # Extractor tests
    test_extract_combat_event,
    test_extract_no_events_from_neutral_text,
    test_extract_from_text_sets_campaign_and_story,
    test_split_sections_on_headers,
    test_extract_character_names,
    test_extract_location,
    test_extract_from_file_missing_returns_empty,
    test_ai_extractor_parse_valid_json,
    test_ai_extractor_parse_invalid_json,
    # Store tests
    test_store_add_and_get_event,
    test_store_get_event_missing_returns_none,
    test_store_get_campaign_timeline,
    test_store_get_character_timeline,
    test_store_get_character_timeline_case_insensitive,
    test_store_query_by_campaign,
    test_store_query_by_event_type,
    test_store_query_by_priority,
    test_store_link_events,
    test_store_link_events_missing_returns_false,
    test_store_persistence_to_disk,
    test_store_reload_from_disk,
    test_store_get_campaign_names,
]


def run_all_timeline_tests():
    """Run all timeline tests and exit with appropriate code."""
    sys.exit(test_helpers.run_test_suite("Timeline Tests", ALL_TESTS))


if __name__ == "__main__":
    run_all_timeline_tests()
