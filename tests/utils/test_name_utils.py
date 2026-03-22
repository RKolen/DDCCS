"""Unit tests for src.utils.name_utils."""

from tests.test_helpers import setup_test_environment, import_module


setup_test_environment()

nu = import_module("src.utils.name_utils")
CharacterName = nu.CharacterName
build_name_fields = nu.build_name_fields
format_character_list = nu.format_character_list
get_formal_introduction = nu.get_formal_introduction
get_name_for_dialogue = nu.get_name_for_dialogue
validate_name_fields = nu.validate_name_fields


# ---------------------------------------------------------------------------
# Name parsing (tested via the public API)
# ---------------------------------------------------------------------------

def test_parse_single_word_name() -> None:
    """Single-word names yield only a first name component."""
    cn = CharacterName.from_dict({"name": "Aragorn"})
    assert cn.first_name == "Aragorn"
    assert cn.last_name is None
    assert cn.epithet is None


def test_parse_two_word_name() -> None:
    """Two-word names split into first and last components."""
    cn = CharacterName.from_dict({"name": "Frodo Baggins"})
    assert cn.first_name == "Frodo"
    assert cn.last_name == "Baggins"
    assert cn.epithet is None


def test_parse_name_with_epithet() -> None:
    """Names containing 'the' yield an extracted epithet."""
    cn = CharacterName.from_dict({"name": "Gandalf the Grey"})
    assert cn.first_name == "Gandalf"
    assert cn.last_name is None
    assert cn.epithet == "the Grey"


def test_parse_epithet_case_insensitive() -> None:
    """Epithet extraction is case-insensitive."""
    cn = CharacterName.from_dict({"name": "Aragorn The Dunedain"})
    assert cn.first_name == "Aragorn"
    assert cn.epithet == "the Dunedain"
    assert cn.last_name is None


# ---------------------------------------------------------------------------
# CharacterName.from_dict
# ---------------------------------------------------------------------------

def test_character_name_from_dict_legacy() -> None:
    """Legacy name-only dict is parsed into components."""
    cn = CharacterName.from_dict({"name": "Frodo Baggins", "nickname": "Ring-bearer"})
    assert cn.first_name == "Frodo"
    assert cn.last_name == "Baggins"
    assert cn.nickname == "Ring-bearer"
    assert cn.epithet is None


def test_character_name_from_dict_structured() -> None:
    """Structured fields are used as-is when present."""
    cn = CharacterName.from_dict({
        "name": "Aragorn",
        "first_name": "Aragorn",
        "last_name": None,
        "nickname": "Strider",
        "title": "King of Gondor",
    })
    assert cn.first_name == "Aragorn"
    assert cn.last_name is None
    assert cn.nickname == "Strider"
    assert cn.title == "King of Gondor"


def test_character_name_from_dict_epithet() -> None:
    """Epithet parsed from legacy name is preserved."""
    cn = CharacterName.from_dict({"name": "Gandalf the Grey"})
    assert cn.first_name == "Gandalf"
    assert cn.epithet == "the Grey"


# ---------------------------------------------------------------------------
# CharacterName properties
# ---------------------------------------------------------------------------

def test_formal_name_with_title() -> None:
    """Formal name with a title uses 'Title FirstName' format."""
    cn = CharacterName(
        full_name="Aragorn",
        first_name="Aragorn",
        title="King of Gondor",
    )
    assert cn.formal_name == "King of Gondor Aragorn"


def test_formal_name_first_last() -> None:
    """Formal name without title is 'FirstName LastName'."""
    cn = CharacterName(full_name="Frodo Baggins", first_name="Frodo", last_name="Baggins")
    assert cn.formal_name == "Frodo Baggins"


def test_formal_name_fallback() -> None:
    """Formal name falls back to full_name when no structured fields."""
    cn = CharacterName(full_name="Gandalf the Grey")
    assert cn.formal_name == "Gandalf the Grey"


def test_casual_name_prefers_nickname() -> None:
    """Casual name returns nickname when available."""
    cn = CharacterName(full_name="Aragorn", first_name="Aragorn", nickname="Strider")
    assert cn.casual_name == "Strider"


def test_casual_name_falls_back_to_first() -> None:
    """Casual name falls back to first_name when no nickname."""
    cn = CharacterName(full_name="Frodo Baggins", first_name="Frodo")
    assert cn.casual_name == "Frodo"


def test_sort_key_last_first() -> None:
    """Sort key is 'LastName, FirstName' when both are set."""
    cn = CharacterName(full_name="Frodo Baggins", first_name="Frodo", last_name="Baggins")
    assert cn.sort_key == "Baggins, Frodo"


def test_sort_key_first_only() -> None:
    """Sort key is first_name when no last name."""
    cn = CharacterName(full_name="Aragorn", first_name="Aragorn")
    assert cn.sort_key == "Aragorn"


def test_get_name_for_context() -> None:
    """get_name_for_context returns the right name per context."""
    cn = CharacterName(
        full_name="Frodo Baggins",
        first_name="Frodo",
        last_name="Baggins",
        nickname="Ring-bearer",
        title=None,
    )
    assert cn.get_name_for_context("formal") == "Frodo Baggins"
    assert cn.get_name_for_context("casual") == "Ring-bearer"
    assert cn.get_name_for_context("dialogue") == "Ring-bearer"
    assert cn.get_name_for_context("narrative") == "Frodo Baggins"
    assert cn.get_name_for_context("sort") == "Baggins, Frodo"
    assert cn.get_name_for_context("unknown") == "Frodo Baggins"


# ---------------------------------------------------------------------------
# build_name_fields
# ---------------------------------------------------------------------------

def test_build_name_fields_first_last() -> None:
    """build_name_fields produces first_name and last_name for a two-word name."""
    result = build_name_fields("Barliman Butterbur")
    assert result["first_name"] == "Barliman"
    assert result["last_name"] == "Butterbur"
    assert "epithet" not in result


def test_build_name_fields_epithet() -> None:
    """build_name_fields extracts epithet from names with 'the'."""
    result = build_name_fields("Gandalf the Grey")
    assert result["first_name"] == "Gandalf"
    assert "last_name" not in result
    assert result["epithet"] == "the Grey"


def test_build_name_fields_with_nickname() -> None:
    """Nickname is included when supplied."""
    result = build_name_fields("Aragorn", nickname="Strider")
    assert result["first_name"] == "Aragorn"
    assert result["nickname"] == "Strider"


# ---------------------------------------------------------------------------
# format_character_list
# ---------------------------------------------------------------------------

def test_format_character_list_full() -> None:
    """Full format joins names with comma-space."""
    chars = [{"name": "Aragorn"}, {"name": "Frodo"}, {"name": "Gandalf"}]
    assert format_character_list(chars) == "Aragorn, Frodo, Gandalf"


def test_format_character_list_short() -> None:
    """Short format prefers nickname, then first_name, then name."""
    chars = [
        {"name": "Aragorn", "nickname": "Strider"},
        {"name": "Frodo Baggins", "first_name": "Frodo"},
        {"name": "Gandalf the Grey"},
    ]
    result = format_character_list(chars, format_type="short")
    assert result == "Strider, Frodo, Gandalf the Grey"


def test_format_character_list_sorted() -> None:
    """Sorted format orders by last name then first name."""
    chars = [
        {"name": "Frodo Baggins", "first_name": "Frodo", "last_name": "Baggins"},
        {"name": "Aragorn", "first_name": "Aragorn"},
        {"name": "Barliman Butterbur", "first_name": "Barliman", "last_name": "Butterbur"},
    ]
    result = format_character_list(chars, format_type="sorted")
    # Baggins < Butterbur; Aragorn has no last name -> sorts by first name only
    names = [n.strip() for n in result.split(",")]
    assert names.index("Aragorn") > names.index("Frodo Baggins")
    assert names.index("Frodo Baggins") < names.index("Barliman Butterbur")


# ---------------------------------------------------------------------------
# get_name_for_dialogue / get_formal_introduction
# ---------------------------------------------------------------------------

def test_get_name_for_dialogue_nickname() -> None:
    """Dialogue name returns nickname when set."""
    assert get_name_for_dialogue({"name": "Aragorn", "nickname": "Strider"}) == "Strider"


def test_get_name_for_dialogue_first_name() -> None:
    """Dialogue name returns first_name when no nickname."""
    assert get_name_for_dialogue({"name": "Frodo Baggins", "first_name": "Frodo"}) == "Frodo"


def test_get_name_for_dialogue_fallback() -> None:
    """Dialogue name falls back to full name."""
    assert get_name_for_dialogue({"name": "Gandalf the Grey"}) == "Gandalf the Grey"


def test_get_formal_introduction_with_title_and_epithet() -> None:
    """Formal introduction includes title, name, and epithet in order."""
    char = {"name": "Aragorn", "title": "King of Gondor", "epithet": "the Dunedain"}
    result = get_formal_introduction(char)
    assert result == "King of Gondor Aragorn the Dunedain"


def test_get_formal_introduction_name_only() -> None:
    """Formal introduction is just the name when no title or epithet."""
    assert get_formal_introduction({"name": "Frodo Baggins"}) == "Frodo Baggins"


# ---------------------------------------------------------------------------
# validate_name_fields
# ---------------------------------------------------------------------------

def test_validate_name_fields_valid_structured() -> None:
    """Structured name fields with correct types produce no errors."""
    data = {
        "name": "Frodo Baggins",
        "first_name": "Frodo",
        "last_name": "Baggins",
        "nickname": None,
    }
    errors = validate_name_fields(data)
    assert errors == []


def test_validate_name_fields_wrong_type() -> None:
    """A non-string first_name produces a validation error."""
    data = {"name": "Frodo Baggins", "first_name": 42}
    errors = validate_name_fields(data)
    assert any("first_name" in e for e in errors)


def test_validate_name_fields_inconsistent_first_name() -> None:
    """first_name that does not match the start of name is flagged."""
    data = {"name": "Frodo Baggins", "first_name": "Bilbo"}
    errors = validate_name_fields(data)
    assert any("first_name" in e for e in errors)


def test_validate_name_fields_missing_name_is_skipped() -> None:
    """Missing or non-string name skips sub-field validation gracefully."""
    assert validate_name_fields({}) == []
    assert validate_name_fields({"name": 123}) == []


def test_validate_name_fields_legacy_name_no_errors() -> None:
    """A plain legacy name dict produces no errors."""
    assert validate_name_fields({"name": "Aragorn", "nickname": "Strider"}) == []
