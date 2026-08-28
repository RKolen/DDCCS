"""Unit tests for src.story_images.events."""

import json

from tests.ai_fixtures import ScriptedAIClient
from tests.test_helpers import setup_test_environment, import_module

setup_test_environment()

ev = import_module("src.story_images.events")

story_to_text = ev.story_to_text
chunk_story = ev.chunk_story
build_events_prompt = ev.build_events_prompt
parse_events = ev.parse_events
merge_events = ev.merge_events
extract_events = ev.extract_events
StoryEvent = import_module("src.story_images.types").StoryEvent


def test_story_to_text_strips_html() -> None:
    """Drupal processed HTML becomes plain prose."""
    print("\n[TEST] story_to_text - strips tags")
    text = story_to_text("<p>Aragorn <em>drew</em> his sword.</p>")
    assert "Aragorn drew his sword." == text
    print("  [OK] Tags removed, words kept")


def test_chunk_story_splits_on_sentences() -> None:
    """A long body is split under the character budget."""
    print("\n[TEST] chunk_story - splits on sentences")
    sentence = "Aragorn walked on. "
    body = sentence * 80
    chunks = chunk_story(body, limit=200)
    assert len(chunks) > 1
    assert all(len(chunk) <= 200 for chunk in chunks)
    print(f"  [OK] {len(chunks)} chunks, each within budget")


def test_chunk_story_keeps_a_short_body_whole() -> None:
    """A short story is a single chunk."""
    print("\n[TEST] chunk_story - short body")
    chunks = chunk_story("Aragorn reached Bree.")
    assert chunks == ["Aragorn reached Bree."]
    print("  [OK] One chunk")


def test_prompt_asks_for_json_events() -> None:
    """The per-chunk prompt carries the passage and the JSON shape."""
    print("\n[TEST] build_events_prompt - JSON contract")
    prompt = build_events_prompt("Aragorn reached the Prancing Pony.", "Arrival")
    assert "Arrival" in prompt
    assert "Prancing Pony" in prompt
    assert '"events"' in prompt
    print("  [OK] Title, passage, and JSON envelope present")


def test_parse_events_attaches_excerpt_from_the_chunk() -> None:
    """A hint copied from the passage selects the excerpt window."""
    print("\n[TEST] parse_events - excerpt from hint")
    chunk = (
        "The road was long. Aragorn reached the Prancing Pony and asked "
        "Barliman Butterbur for a room."
    )
    raw = json.dumps(
        {
            "events": [
                {
                    "title": "At the Pony",
                    "one_line": "Aragorn asks for a room.",
                    "excerpt_hint": "Prancing Pony",
                }
            ]
        }
    )
    events = parse_events(raw, chunk)
    assert len(events) == 1
    assert events[0].title == "At the Pony"
    assert "Prancing Pony" in events[0].excerpt
    print("  [OK] Excerpt includes the hinted phrase")


def test_parse_events_skips_blank_titles() -> None:
    """An entry without a title is dropped."""
    print("\n[TEST] parse_events - blank title dropped")
    raw = json.dumps({"events": [{"title": "", "one_line": "Nothing"}]})
    assert parse_events(raw, "Aragorn waited.") == []
    print("  [OK] Empty list")


def test_merge_events_dedupes_by_title() -> None:
    """The same title from two chunks is kept once."""
    print("\n[TEST] merge_events - title dedupe")
    first = StoryEvent("At the Pony", "Arrival", "excerpt one")
    second = StoryEvent("At the Pony", "Duplicate", "excerpt two")
    third = StoryEvent("The chase", "Flight", "excerpt three")
    merged = merge_events([[first], [second, third]])
    assert [event.title for event in merged] == ["At the Pony", "The chase"]
    print("  [OK] Duplicate title dropped")


def test_extract_events_map_reduces_chunks() -> None:
    """Each chunk is asked separately and the answers are merged."""
    print("\n[TEST] extract_events - map-reduce")
    payload = json.dumps(
        {
            "events": [
                {
                    "title": "Arrival",
                    "one_line": "They reach Bree.",
                    "excerpt_hint": "Bree",
                }
            ]
        }
    )
    client = ScriptedAIClient(payload)
    events = extract_events(client, "Aragorn reached Bree.", "The Arrival")
    assert len(events) == 1
    assert events[0].title == "Arrival"
    assert client.calls
    print("  [OK] One event from one chunk")


def test_extract_events_without_ai_returns_empty() -> None:
    """No client means no events, not an error."""
    print("\n[TEST] extract_events - no client")
    assert extract_events(None, "Aragorn reached Bree.", "The Arrival") == []
    print("  [OK] Empty list")


def run_all_tests() -> None:
    """Run all event-extraction tests."""
    test_story_to_text_strips_html()
    test_chunk_story_splits_on_sentences()
    test_chunk_story_keeps_a_short_body_whole()
    test_prompt_asks_for_json_events()
    test_parse_events_attaches_excerpt_from_the_chunk()
    test_parse_events_skips_blank_titles()
    test_merge_events_dedupes_by_title()
    test_extract_events_map_reduces_chunks()
    test_extract_events_without_ai_returns_empty()
    print("\n[PASS] All story-image event tests passed.")


if __name__ == "__main__":
    run_all_tests()
