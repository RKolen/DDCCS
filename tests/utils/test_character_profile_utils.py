"""Unit tests for src.utils.character_profile_utils."""

from tests.test_helpers import setup_test_environment, import_module, run_test_suite


setup_test_environment()

cpu = import_module("src.utils.character_profile_utils")
find_character_file = cpu.find_character_file
load_character_profile = cpu.load_character_profile
load_character_profiles = cpu.load_character_profiles
load_character_traits = cpu.load_character_traits
is_example_or_template_file = cpu.is_example_or_template_file
list_character_files = cpu.list_character_files
list_character_names = cpu.list_character_names


def test_find_character_file_exact_match() -> None:
    """Find character file returns path for existing character (Aragorn)."""
    print("\n[TEST] Find Character File - Exact Match")
    result = find_character_file("Aragorn")
    assert result is not None, "Should find aragorn.json"
    assert "aragorn.json" in result.lower(), "Path should contain aragorn.json"
    print("  [OK] Found Aragorn character file")


def test_find_character_file_full_name() -> None:
    """Find character file works with full name (Frodo Baggins)."""
    print("\n[TEST] Find Character File - Full Name")
    result = find_character_file("Frodo Baggins")
    assert result is not None, "Should find frodo.json via first name"
    assert "frodo.json" in result.lower(), "Path should contain frodo.json"
    print("  [OK] Found Frodo via full name")


def test_find_character_file_not_found() -> None:
    """Find character file returns None for non-existent character."""
    print("\n[TEST] Find Character File - Not Found")
    result = find_character_file("NonExistentCharacter")
    assert result is None, "Should return None for non-existent character"
    print("  [OK] Returns None for non-existent character")


def test_load_character_profile_success() -> None:
    """Load character profile returns dict with expected fields."""
    print("\n[TEST] Load Character Profile - Success")
    profile = load_character_profile("Aragorn")
    assert profile is not None, "Should load Aragorn profile"
    assert "name" in profile, "Profile should have name field"
    assert "dnd_class" in profile, "Profile should have dnd_class field"
    print(f"  [OK] Loaded profile for: {profile.get('name')}")


def test_load_character_profile_not_found() -> None:
    """Load character profile returns None for non-existent character."""
    print("\n[TEST] Load Character Profile - Not Found")
    profile = load_character_profile("NonExistentCharacter")
    assert profile is None, "Should return None for non-existent character"
    print("  [OK] Returns None for non-existent character")


def test_load_character_profiles_multiple() -> None:
    """Load character profiles loads multiple characters."""
    print("\n[TEST] Load Character Profiles - Multiple")
    names = ["Aragorn", "Frodo Baggins", "Gandalf the Grey"]
    profiles = load_character_profiles(names)
    assert len(profiles) >= 2, f"Should load at least 2 profiles, got {len(profiles)}"
    print(f"  [OK] Loaded {len(profiles)} profiles: {list(profiles.keys())}")


def test_load_character_profiles_empty_list() -> None:
    """Load character profiles handles empty list."""
    print("\n[TEST] Load Character Profiles - Empty List")
    profiles = load_character_profiles([])
    assert profiles == {}, "Should return empty dict for empty list"
    print("  [OK] Returns empty dict for empty list")


def test_load_character_traits() -> None:
    """Load character traits extracts personality fields."""
    print("\n[TEST] Load Character Traits")
    traits = load_character_traits(["Aragorn"])
    assert "Aragorn" in traits, "Should have Aragorn in traits"
    aragorn_traits = traits["Aragorn"]
    assert "name" in aragorn_traits, "Traits should have name"
    assert "dnd_class" in aragorn_traits, "Traits should have dnd_class"
    assert (
        "personality_summary" in aragorn_traits
    ), "Traits should have personality_summary"
    assert "motivations" in aragorn_traits, "Traits should have motivations"
    print(f"  [OK] Loaded traits with {len(aragorn_traits)} fields")


def test_is_example_or_template_file() -> None:
    """Is example or template file correctly identifies example files."""
    print("\n[TEST] Is Example or Template File")
    assert is_example_or_template_file("class.example.json") is True
    assert is_example_or_template_file("npc.example.json") is True
    assert is_example_or_template_file("story_template.md") is True
    assert is_example_or_template_file("EXAMPLE_file.json") is True
    assert is_example_or_template_file("aragorn.json") is False
    assert is_example_or_template_file("gandalf.json") is False
    print("  [OK] Correctly identifies example/template files")


def test_list_character_files_excludes_examples() -> None:
    """List character files excludes example files by default."""
    print("\n[TEST] List Character Files - Excludes Examples")
    files = list_character_files()
    assert len(files) > 0, "Should find character files"
    for filename in files:
        assert "example" not in filename.lower(), f"Should not include: {filename}"
    print(f"  [OK] Found {len(files)} character files (examples excluded)")


def test_list_character_files_includes_examples() -> None:
    """List character files can include examples when requested."""
    print("\n[TEST] List Character Files - Includes Examples")
    files_no_examples = list_character_files(include_examples=False)
    files_with_examples = list_character_files(include_examples=True)
    assert len(files_with_examples) >= len(
        files_no_examples
    ), "With examples should have at least as many files"
    print(
        f"  [OK] Without examples: {len(files_no_examples)}, "
        f"with examples: {len(files_with_examples)}"
    )


def test_list_character_names() -> None:
    """List character names returns actual character names."""
    print("\n[TEST] List Character Names")
    names = list_character_names()
    assert len(names) > 0, "Should find character names"
    # Check that names look like proper names (not filenames)
    for name in names:
        assert ".json" not in name, f"Name should not contain .json: {name}"
    print(f"  [OK] Found {len(names)} character names")


def run_all_tests() -> bool:
    """Run all character profile utils tests."""
    tests = [
        test_find_character_file_exact_match,
        test_find_character_file_full_name,
        test_find_character_file_not_found,
        test_load_character_profile_success,
        test_load_character_profile_not_found,
        test_load_character_profiles_multiple,
        test_load_character_profiles_empty_list,
        test_load_character_traits,
        test_is_example_or_template_file,
        test_list_character_files_excludes_examples,
        test_list_character_files_includes_examples,
        test_list_character_names,
    ]
    exit_code = run_test_suite("CHARACTER PROFILE UTILS TESTS", tests)
    return exit_code == 0


if __name__ == "__main__":
    import sys

    success = run_all_tests()
    sys.exit(0 if success else 1)
