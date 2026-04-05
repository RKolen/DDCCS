"""Tests for EventExtractor (pattern-based, no AI required)."""

from tests import test_helpers
from tests.timeline.timeline_test_helpers import EventType

EventExtractor = test_helpers.safe_from_import(
    "src.timeline.event_extractor",
    "EventExtractor",
)
AIEventExtractor = test_helpers.safe_from_import(
    "src.timeline.event_extractor",
    "AIEventExtractor",
)


def test_extract_combat_event():
    """Test that combat keywords trigger combat event extraction."""
    print("\n[TEST] EventExtractor - combat pattern")

    extractor = EventExtractor()
    text = "Elara attacks the goblin with her sword. The battle is fierce."
    events = extractor.extract_from_text(
        text, campaign_name="Test_Campaign", story_file="story_001.md"
    )

    types = {e.event_type for e in events}
    assert EventType.COMBAT in types, "Expected COMBAT event from combat keywords"
    print(f"  [OK] Detected {len(events)} event(s) including COMBAT")
    print("[PASS] EventExtractor - combat pattern")


def test_extract_no_events_from_neutral_text():
    """Test that neutral text without event keywords returns no events."""
    print("\n[TEST] EventExtractor - neutral text")

    extractor = EventExtractor()
    text = "The sun rose slowly over the quiet village."
    events = extractor.extract_from_text(text)

    assert events == [], f"Expected no events, got {len(events)}"
    print("  [OK] Neutral text returns empty list")
    print("[PASS] EventExtractor - neutral text")


def test_extract_from_text_sets_campaign_and_story():
    """Test that extracted events carry campaign and story_file."""
    print("\n[TEST] EventExtractor - source fields populated")

    extractor = EventExtractor()
    text = "The party fights the trolls in the dungeon."
    events = extractor.extract_from_text(
        text, campaign_name="CampaignX", story_file="ep_01.md"
    )

    assert events, "Expected at least one event from combat text"
    for event in events:
        assert event.source.campaign_name == "CampaignX"
        assert event.source.story_file == "ep_01.md"
    print("  [OK] Source fields set correctly on all events")
    print("[PASS] EventExtractor - source fields populated")


def test_split_sections_on_headers():
    """Test that split_sections divides text at markdown headers."""
    print("\n[TEST] EventExtractor.split_sections")

    extractor = EventExtractor()
    text = "# Act One\nFirst paragraph.\n\n# Act Two\nSecond paragraph."
    sections = extractor.split_sections(text)

    titles = [title for title, _ in sections]
    assert "Act One" in titles
    assert "Act Two" in titles
    print(f"  [OK] Sections found: {titles}")
    print("[PASS] EventExtractor.split_sections")


def test_extract_character_names():
    """Test that capitalized names are extracted from text."""
    print("\n[TEST] EventExtractor.extract_character_names")

    extractor = EventExtractor()
    text = "Elara and Theron fought bravely against the Shadow."
    names = extractor.extract_character_names(text)

    assert "Elara" in names
    assert "Theron" in names
    print(f"  [OK] Names found: {names}")
    print("[PASS] EventExtractor.extract_character_names")


def test_extract_location():
    """Test that location phrases are extracted from text."""
    print("\n[TEST] EventExtractor.extract_location")

    extractor = EventExtractor()
    text = "The party arrives at Stormwatch Keep."
    location = extractor.extract_location(text)
    assert location, "Expected a location to be extracted"
    print(f"  [OK] Location found: '{location}'")
    print("[PASS] EventExtractor.extract_location")


def test_extract_from_file_missing_returns_empty():
    """Test that extracting from a missing file returns an empty list."""
    print("\n[TEST] EventExtractor.extract_from_file - missing file")

    extractor = EventExtractor()
    events = extractor.extract_from_file("/nonexistent/path/story.md")
    assert events == []
    print("  [OK] Missing file returns empty list")
    print("[PASS] EventExtractor.extract_from_file - missing file")


def test_ai_extractor_parse_valid_json():
    """Test that parse_ai_response parses valid JSON arrays."""
    print("\n[TEST] AIEventExtractor.parse_ai_response - valid JSON")

    class _FakeAI:
        def create_system_message(self, msg):
            """Return a system message dict."""
            return {"role": "system", "content": msg}

        def create_user_message(self, msg):
            """Return a user message dict."""
            return {"role": "user", "content": msg}

        def chat_completion(self, messages):
            """Return messages unchanged."""
            return messages

    ai_extractor = AIEventExtractor(_FakeAI())
    json_str = (
        '[{"event_type":"combat","title":"Fight","description":"Battle.",'
        '"characters_involved":["Elara"],"location":"Cave","priority":"important"}]'
    )
    result = ai_extractor.parse_ai_response(json_str)

    assert len(result) == 1
    assert result[0]["event_type"] == "combat"
    assert result[0]["title"] == "Fight"
    print("  [OK] Valid JSON parsed correctly")
    print("[PASS] AIEventExtractor.parse_ai_response - valid JSON")


def test_ai_extractor_parse_invalid_json():
    """Test that parse_ai_response returns empty list for invalid JSON."""
    print("\n[TEST] AIEventExtractor.parse_ai_response - invalid JSON")

    ai_extractor = AIEventExtractor(None)
    result = ai_extractor.parse_ai_response("not valid json at all")
    assert result == []
    print("  [OK] Invalid JSON returns empty list")
    print("[PASS] AIEventExtractor.parse_ai_response - invalid JSON")


if __name__ == "__main__":
    test_extract_combat_event()
    test_extract_no_events_from_neutral_text()
    test_extract_from_text_sets_campaign_and_story()
    test_split_sections_on_headers()
    test_extract_character_names()
    test_extract_location()
    test_extract_from_file_missing_returns_empty()
    test_ai_extractor_parse_valid_json()
    test_ai_extractor_parse_invalid_json()
    print("\n[ALL TESTS PASSED]")
