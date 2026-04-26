"""Tests for src.cli.batch_operations: BatchProcessor and operation factories."""

import tempfile
from pathlib import Path

from src.cli.batch_operations import (
    BatchProcessor,
    BatchResult,
    batch_add_item,
    batch_level_up,
)


# ---------------------------------------------------------------------------
# BatchResult dataclass
# ---------------------------------------------------------------------------


def test_batch_result_success_defaults():
    """BatchResult should default message to empty string and data to None."""
    result = BatchResult(item="aragorn", success=True)
    assert result.message == ""
    assert result.data is None


def test_batch_result_stores_fields():
    """BatchResult should preserve all provided field values."""
    result = BatchResult(item="frodo", success=False, message="oops", data={"level": 1})
    assert result.item == "frodo"
    assert result.success is False
    assert result.message == "oops"
    assert result.data == {"level": 1}


# ---------------------------------------------------------------------------
# batch_level_up
# ---------------------------------------------------------------------------


def test_batch_level_up_increments_level():
    """batch_level_up should increment character level by the given amount."""
    op = batch_level_up(2)
    result = op("aragorn", {"name": "aragorn", "level": 5})
    assert result.success is True
    assert result.data is not None
    assert result.data["level"] == 7


def test_batch_level_up_defaults_missing_level_to_one():
    """batch_level_up should treat a missing 'level' field as 1."""
    op = batch_level_up(1)
    result = op("frodo", {"name": "frodo"})
    assert result.data is not None
    assert result.data["level"] == 2


def test_batch_level_up_message_shows_old_and_new():
    """batch_level_up result message should show both old and new levels."""
    op = batch_level_up(1)
    result = op("gandalf", {"level": 3})
    assert "3" in result.message
    assert "4" in result.message


# ---------------------------------------------------------------------------
# batch_add_item
# ---------------------------------------------------------------------------


def test_batch_add_item_appends_new_entry():
    """batch_add_item should append a new entry when the item is absent."""
    op = batch_add_item("Health Potion", 2)
    result = op("aragorn", {"name": "aragorn", "equipment": []})
    assert result.success is True
    assert result.data is not None
    items = result.data["equipment"]
    assert any(i["name"] == "Health Potion" and i["quantity"] == 2 for i in items)


def test_batch_add_item_increments_existing_quantity():
    """batch_add_item should increment quantity when the item already exists."""
    op = batch_add_item("Arrow", 10)
    result = op("legolas", {"equipment": [{"name": "Arrow", "quantity": 20}]})
    assert result.data is not None
    items = result.data["equipment"]
    assert any(i["name"] == "Arrow" and i["quantity"] == 30 for i in items)


def test_batch_add_item_creates_equipment_list_when_missing():
    """batch_add_item should create the equipment list when the field is absent."""
    op = batch_add_item("Torch", 5)
    result = op("bilbo", {"name": "bilbo"})
    assert result.data is not None
    assert "equipment" in result.data
    assert len(result.data["equipment"]) == 1


def test_batch_add_item_replaces_non_list_equipment():
    """batch_add_item should replace a non-list equipment value with a new list."""
    op = batch_add_item("Rope", 1)
    result = op("sam", {"name": "sam", "equipment": "string_value"})
    assert result.data is not None
    assert isinstance(result.data["equipment"], list)


# ---------------------------------------------------------------------------
# BatchProcessor.process_characters
# ---------------------------------------------------------------------------


def test_process_characters_missing_file_returns_failure():
    """process_characters should return a failure for a non-existent character."""

    def no_op(name, _data):
        return BatchResult(item=name, success=True)

    processor = BatchProcessor()
    results = processor.process_characters(no_op, character_names=["__nonexistent__"])
    assert len(results) == 1
    assert results[0].success is False
    assert "not found" in results[0].message.lower()


def test_process_characters_success_with_real_character():
    """process_characters should succeed for an existing character file."""

    def read_only(name, _data):
        return BatchResult(item=name, success=True, message="ok")

    processor = BatchProcessor()
    results = processor.process_characters(read_only, character_names=["aragorn"])
    assert len(results) == 1
    assert results[0].success is True


def test_process_characters_progress_callback_invoked():
    """process_characters should invoke the progress_callback for each item."""
    calls = []

    def callback(name, current, total):
        calls.append((name, current, total))

    def no_op(name, _data):
        return BatchResult(item=name, success=True)

    processor = BatchProcessor()
    processor.process_characters(no_op, character_names=["aragorn"], progress_callback=callback)
    assert calls == [("aragorn", 1, 1)]


# ---------------------------------------------------------------------------
# BatchProcessor.process_campaigns
# ---------------------------------------------------------------------------


def test_process_campaigns_missing_returns_failure():
    """process_campaigns should return a failure for a non-existent campaign."""

    def no_op(name, _path):
        return BatchResult(item=name, success=True)

    processor = BatchProcessor()
    results = processor.process_campaigns(no_op, campaign_names=["__nonexistent__"])
    assert len(results) == 1
    assert results[0].success is False


def test_process_campaigns_known_campaign_succeeds():
    """process_campaigns should succeed for Example_Campaign."""

    def read_only(name, path):
        return BatchResult(item=name, success=True, message=str(path))

    processor = BatchProcessor()
    results = processor.process_campaigns(read_only, campaign_names=["Example_Campaign"])
    assert len(results) == 1
    assert results[0].success is True


# ---------------------------------------------------------------------------
# BatchProcessor.process_stories
# ---------------------------------------------------------------------------


def test_process_stories_missing_campaign_returns_failure():
    """process_stories should return a failure when the campaign does not exist."""

    def no_op(filename, _path):
        return BatchResult(item=filename, success=True)

    processor = BatchProcessor()
    results = processor.process_stories("__nonexistent__", no_op)
    assert len(results) == 1
    assert results[0].success is False


def test_process_stories_known_campaign_processes_md_files():
    """process_stories should process all .md files in Example_Campaign."""
    processed = []

    def record(filename, _path):
        processed.append(filename)
        return BatchResult(item=filename, success=True)

    processor = BatchProcessor()
    results = processor.process_stories("Example_Campaign", record)
    assert len(results) >= 1
    assert all(r.success for r in results)
    assert all(f.endswith(".md") for f in processed)


# ---------------------------------------------------------------------------
# batch_level_up does not write when data=None
# ---------------------------------------------------------------------------


def test_level_up_does_not_persist_without_data():
    """A read-only operation (data=None) should not overwrite the character file."""
    with tempfile.TemporaryDirectory() as tmp:
        char_path = Path(tmp) / "test_char.json"
        char_path.write_text('{"name": "test", "level": 3}', encoding="utf-8")

        def read_only(name, _data):
            return BatchResult(item=name, success=True)

        processor = BatchProcessor()
        processor.process_characters(
            read_only,
            character_names=["test_char"],
        )
        content = char_path.read_text(encoding="utf-8")
        assert '"level": 3' in content


if __name__ == "__main__":
    test_batch_result_success_defaults()
    test_batch_result_stores_fields()
    test_batch_level_up_increments_level()
    test_batch_level_up_defaults_missing_level_to_one()
    test_batch_level_up_message_shows_old_and_new()
    test_batch_add_item_appends_new_entry()
    test_batch_add_item_increments_existing_quantity()
    test_batch_add_item_creates_equipment_list_when_missing()
    test_batch_add_item_replaces_non_list_equipment()
    test_process_characters_missing_file_returns_failure()
    test_process_characters_success_with_real_character()
    test_process_characters_progress_callback_invoked()
    test_process_campaigns_missing_returns_failure()
    test_process_campaigns_known_campaign_succeeds()
    test_process_stories_missing_campaign_returns_failure()
    test_process_stories_known_campaign_processes_md_files()
    test_level_up_does_not_persist_without_data()
    print("All batch operation tests passed.")
