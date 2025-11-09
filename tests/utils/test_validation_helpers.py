"""Unit tests for src.utils.validation_helpers."""

from typing import Any, Dict
import io
from contextlib import redirect_stdout

from tests.test_helpers import setup_test_environment, import_module


setup_test_environment()

vh = import_module("src.utils.validation_helpers")
validate_required_fields = vh.validate_required_fields
validate_field_type = vh.validate_field_type
validate_list_field = vh.validate_list_field
validate_enum_value = vh.validate_enum_value
validate_dict_field = vh.validate_dict_field
format_validation_errors = vh.format_validation_errors
collect_errors = vh.collect_errors
get_type_name = vh.get_type_name
print_validation_report = vh.print_validation_report


def test_validate_required_fields_and_format() -> None:
    """Required field validation detects missing and empty values."""
    good = {"name": "Sam", "age": 30}
    ok, errs = validate_required_fields(good, ["name"])  
    assert ok and not errs

    bad = {"name": "", "age": None}
    ok2, errs2 = validate_required_fields(bad, ["name", "age", "title"])  
    assert not ok2
    formatted = format_validation_errors(errs2, data_type="character")
    assert "Validation errors for character" in formatted


def test_validate_field_type_and_enum_and_dict() -> None:
    """Field type, enum and dict validations return the expected tuples."""
    data: Dict[str, Any] = {"count": 3, "kind": "orc", "meta": {}}
    ok, e = validate_field_type(data, "count", int)
    assert ok and e is None

    ok_enum, msg_enum = validate_enum_value(data, "kind", ["elf", "human"], required=False)
    assert not ok_enum and msg_enum

    ok_dict, msg_dict = validate_dict_field(data, "meta", required=True, allow_empty=True)
    assert ok_dict and msg_dict is None


def test_validate_list_field_constraints_and_collect_errors() -> None:
    """List validation enforces item types and collect_errors flattens results."""
    data = {"tags": ["a", 2, "c"]}
    ok, errors = validate_list_field(data, "tags", item_type=str, min_length=2)
    assert not ok
    assert any("tags[1]" in e for e in errors)

    combined = collect_errors([(ok, errors), (False, "single error"), (True, None)])
    assert "single error" in combined


def test_get_type_name_representation() -> None:
    """Type-name helper returns readable type names for types and tuples."""
    assert "int" in get_type_name(int)
    assert "int or str" in get_type_name((int, str))


def test_print_validation_report_outputs() -> None:
    """print_validation_report writes OK/INVALID lines to stdout."""
    buf = io.StringIO()
    with redirect_stdout(buf):
        print_validation_report("file.json", False, ["oops"])  
    out = buf.getvalue()
    assert "[INVALID] file.json" in out
