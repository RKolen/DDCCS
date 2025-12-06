"""
Test Helper Functions

Common utilities and setup for all test files to reduce boilerplate code.

This module configures the test environment when imported. Test files should
import this module FIRST before any other project imports.

Usage in test files:
    # Standard imports
    import sys
    from pathlib import Path

    # Add tests directory to path (required to find test_helpers)
    sys.path.insert(0, str(Path(__file__).parent.parent))

    # Import test helpers and configure environment
    import test_helpers
    project_root = test_helpers.setup_test_environment()

    # Now import project modules
    from src.validation.character_validator import validate_character_json

"""

import json
import sys
import types
from pathlib import Path
import importlib


# Configuration for behaviour generation module handling
class _BehaviourConfig:
    """Configuration state for behaviour generation handling."""

    should_disable = True

    @classmethod
    def disable(cls):
        """Set flag to disable behaviour generation."""
        cls.should_disable = True

    @classmethod
    def enable(cls):
        """Set flag to enable behaviour generation."""
        cls.should_disable = False


def disable_behaviour_generation():
    """Disable behaviour generation to prevent AI hangs during tests."""

    dummy_mod = types.ModuleType("src.utils.behaviour_generation")
    sys.modules["src.utils.behaviour_generation"] = dummy_mod


def enable_behaviour_generation():
    """Re-enable behaviour generation for tests that specifically test it.

    Clears the dummy module placeholder from sys.modules to allow fresh import.
    Must be called BEFORE trying to import behaviour_generation module.
    """
    # Remove the dummy module placeholder to allow actual import
    if "src.utils.behaviour_generation" in sys.modules:
        del sys.modules["src.utils.behaviour_generation"]

    # Signal to setup_test_environment to NOT re-disable it
    _BehaviourConfig.enable()

    # Invalidate importlib caches to force fresh load
    importlib.invalidate_caches()


def setup_test_environment():
    """
    Configure test environment for proper execution.

    - Adds project root to Python path for imports
    - Disables behavior generation to prevent AI hangs in tests
    - Returns project root path for test use

    Returns:
        pathlib.Path: Project root directory

    """
    # Add project root to path for imports (tests/ parent directory)
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Disable behavior generation to prevent AI client hangs during testing,
    # unless explicitly enabled for tests that need to test behaviour_generation itself.
    # This prevents __post_init__ from trying to call the AI when loading
    # character profiles that don't have behavior fields pre-populated.
    if _BehaviourConfig.should_disable:
        disable_behaviour_generation()

    return project_root


def import_module(module_name: str):
    """Import a module by name after ensuring the test environment is configured.

    This centralizes imports for tests and prevents duplicated try/except
    import blocks across many test files (reduces lint duplication warnings).
    """
    # Ensure project root is on sys.path before importing
    setup_test_environment()
    # Delegate to importlib and allow ImportError to propagate to the caller.
    return importlib.import_module(module_name)


def _build_possessions(possessions_cls, kw):
    """Module-level helper to build CharacterPossessions from kwargs."""
    equipment = {
        "weapons": kw.get("weapons") or [],
        "armor": kw.get("armor") or [],
        "items": kw.get("items_list") or [],
    }
    magic_items_local = kw.get("magic_items") or []
    return possessions_cls(equipment=equipment, magic_items=magic_items_local)


def _build_behavior(behavior_cls, kw):
    """Module-level helper to build CharacterBehavior from kwargs."""
    return behavior_cls(speech_patterns=kw.get("speech_patterns") or [])


def _build_personality(personality_cls, kw):
    """Module-level helper to build CharacterPersonality from kwargs."""
    return personality_cls(relationships=kw.get("relationships") or {})


def _build_story(story_cls, kw):
    """Module-level helper to build CharacterStory from kwargs."""
    return story_cls(
        story_hooks=kw.get("story_hooks") or [],
        character_arcs=kw.get("character_arcs") or [],
        major_plot_actions=kw.get("major_plot_actions") or [],
    )


def _build_mechanics(mechanics_cls, stats_cls, abilities_cls, kw):
    """Module-level helper to build CharacterMechanics from kwargs."""
    stats = stats_cls(
        ability_scores=kw.get("ability_scores") or {},
        skills=kw.get("skills") or {},
        max_hit_points=kw.get("max_hit_points") or 0,
        armor_class=kw.get("armor_class") or 10,
        movement_speed=kw.get("movement_speed") or 30,
        proficiency_bonus=kw.get("proficiency_bonus") or 2,
        background=kw.get("background") or "",
    )
    abilities = abilities_cls(
        feats=kw.get("feats") or [],
        class_abilities=kw.get("class_abilities") or [],
        specialized_abilities=kw.get("specialized_abilities") or [],
        spell_slots=kw.get("spell_slots") or {},
        known_spells=kw.get("known_spells") or [],
    )
    return mechanics_cls(stats=stats, abilities=abilities)


def load_consultant_fixture(name: str):
    """Load a CharacterProfile from game_data and wrap it in a CharacterConsultant.

    This centralizes the common `_load_fixture` helper used across many tests.
    """
    setup_test_environment()
    cp_mod = import_module("src.characters.consultants.character_profile")
    core_mod = import_module("src.characters.consultants.consultant_core")

    character_profile_cls = getattr(cp_mod, "CharacterProfile")
    character_consultant_cls = getattr(core_mod, "CharacterConsultant")

    base = Path(__file__).parent.parent
    fp = base / "game_data" / "characters" / f"{name}.json"
    profile = character_profile_cls.load_from_file(str(fp))
    return character_consultant_cls(profile)


def sample_character_data(
    name: str = "Test Character",
    dnd_class: str = "fighter",
    level: int = 5,
    ability_scores: dict | None = None,
    overrides: dict | None = None,
):
    """Return a canonical character dict for use in tests.

    Tests should use this helper instead of inlining large dict literals.
    """
    if ability_scores is None:
        ability_scores = {
            "strength": 16,
            "dexterity": 14,
            "constitution": 15,
            "intelligence": 10,
            "wisdom": 12,
            "charisma": 8,
        }

    base = {
        "name": name,
        "species": "Human",
        "dnd_class": dnd_class,
        "level": level,
        "ability_scores": ability_scores,
        "equipment": {
            "weapons": ["Longsword", "Shield"],
            "armor": ["Plate Armor"],
            "items": ["Backpack", "Rope"],
        },
        "known_spells": [],
        "background": "Soldier",
        "backstory": "A veteran warrior.",
        "relationships": {},
    }

    if overrides:
        base.update(overrides)

    return base


def write_character_file(
    workspace_path: str, character_name: str, data: dict | None = None
):
    """Write a character JSON file under the provided workspace path and return the filepath.

    Creates the `game_data/characters` directory if required. If `data` is None,
    uses `sample_character_data(character_name)`.
    """

    characters_dir = Path(workspace_path) / "game_data" / "characters"
    characters_dir.mkdir(parents=True, exist_ok=True)

    if data is None:
        data = sample_character_data(character_name)

    filepath = characters_dir / f"{character_name.lower()}.json"
    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)

    return str(filepath)


def sample_npc_data(
    name: str = "Test NPC",
    role: str = "Merchant",
    species: str = "Human",
    overrides: dict | None = None,
):
    """Return a canonical NPC dict for tests.

    Use this instead of inlining NPC dictionaries in multiple tests.
    """
    base = {
        "name": name,
        "nickname": None,
        "role": role,
        "species": species,
        "lineage": "",
        "personality": "Friendly",
        "relationships": {},
        "key_traits": ["Honest"],
        "abilities": ["Appraisal"],
        "recurring": False,
        "notes": "Test NPC",
        "ai_config": {
            "enabled": False,
            "temperature": 0.7,
            "max_tokens": 1000,
            "system_prompt": "",
        },
    }

    if overrides:
        base.update(overrides)

    return base


def make_fake_input(inputs: list):
    """Return a callable that can be used to monkeypatch builtins.input.

    The returned function will pop values from the provided list and return
    an empty string when the list is exhausted. This centralizes the small
    fake-input implementations used across CLI tests.
    """

    def _fake_input(prompt=""):
        _ = prompt
        try:
            return inputs.pop(0)
        except IndexError:
            return ""

    return _fake_input


def run_tests_safely(tests: list, success_message: str = "[OK] All tests passed!"):
    """Run a list of test callables, printing failures and exiting on unexpected errors.

    Each item in `tests` should be a callable (no-arg). This reproduces the
    repeated `if __name__ == '__main__'` pattern present in many test files.
    """
    try:
        for t in tests:
            t()

        print("\n" + success_message)
    except AssertionError as e:
        print(f"\n[FAILED] Test failed: {e}")
        sys.exit(1)
    except (ImportError, ValueError, KeyError, OSError) as e:
        print(f"\n[FAILED] Unexpected error: {e}")
        sys.exit(1)


def safe_from_import(module_name: str, *names):
    """Safely import attributes from a module for tests.

    This helper ensures the test environment is configured, imports the
    requested module, and returns the requested attributes. On failure it
    prints a helpful error and exits the test process (matching the
    existing per-test-file behavior).

    Usage:
        StoryManager = test_helpers.safe_from_import("src.stories.story_manager", "StoryManager")
        get_campaigns_dir = test_helpers.safe_from_import("src.utils.path_utils",
            "get_campaigns_dir")

    Returns:
        Single object when one name is requested, or a tuple when multiple
        names are requested.
    """
    setup_test_environment()
    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        print(f"[ERROR] Failed to import required module '{module_name}': {exc}")
        print("[ERROR] Make sure you're running from the tests directory")
        sys.exit(1)

    results = []
    for name in names:
        try:
            results.append(getattr(module, name))
        except AttributeError as exc:
            print(f"[ERROR] Failed to import '{name}' from '{module_name}': {exc}")
            print("[ERROR] Make sure you're running from the tests directory")
            sys.exit(1)

    if len(results) == 1:
        return results[0]
    return tuple(results)


def make_identity(name: str = "TestChar", dnd_class=None, level: int = 1):
    """Create a CharacterIdentity instance for tests.

    dnd_class may be either a `src.characters.character_sheet.DnDClass`
    enum member or a string name (case-insensitive). This function imports
    the required class at runtime to avoid top-level import errors in
    partial test environments.
    """
    # Import CharacterIdentity and DnDClass at runtime
    cp_mod = import_module("src.characters.consultants.character_profile")
    sheet_mod = import_module("src.characters.character_sheet")

    character_identity_cls = getattr(cp_mod, "CharacterIdentity")
    dnd_class_enum = getattr(sheet_mod, "DnDClass")

    # Resolve string class names to enum members
    if isinstance(dnd_class, str):
        key = dnd_class.strip().upper()
        try:
            dnd_enum = dnd_class_enum[key]
        except KeyError:
            # Fallback: try matching by value (case-insensitive)
            dnd_enum = None
            for member in dnd_class_enum:
                if member.value.lower() == dnd_class.strip().lower():
                    dnd_enum = member
                    break
            if dnd_enum is None:
                # Default to Fighter to keep tests predictable
                dnd_enum = dnd_class_enum.FIGHTER
    elif dnd_class is None:
        dnd_enum = dnd_class_enum.FIGHTER
    else:
        dnd_enum = dnd_class

    return character_identity_cls(name=name, character_class=dnd_enum, level=level)


def _get_character_classes():
    """Get all character profile-related classes from the character_profile module."""
    cp_mod = import_module("src.characters.consultants.character_profile")
    return {
        "profile": getattr(cp_mod, "CharacterProfile"),
        "personality": getattr(cp_mod, "CharacterPersonality"),
        "behavior": getattr(cp_mod, "CharacterBehavior"),
        "story": getattr(cp_mod, "CharacterStory"),
        "mechanics": getattr(cp_mod, "CharacterMechanics"),
        "stats": getattr(cp_mod, "CharacterStats"),
        "abilities": getattr(cp_mod, "CharacterAbilities"),
        "possessions": getattr(cp_mod, "CharacterPossessions"),
    }


def make_profile(name: str = "TestChar", dnd_class=None, level: int = 1, **kwargs):
    """Create a minimal CharacterProfile instance for tests.

    This helper constructs the nested dataclasses (Identity, Personality,
    Behavior, Story, Mechanics, Possessions) used by production `CharacterProfile`
    so tests can avoid boilerplate fixture construction.
    """
    classes = _get_character_classes()

    identity = make_identity(name=name, dnd_class=dnd_class, level=level)
    personality = _build_personality(classes["personality"], kwargs)
    behavior = _build_behavior(classes["behavior"], kwargs)
    story = _build_story(classes["story"], kwargs)
    mechanics = _build_mechanics(
        classes["mechanics"], classes["stats"], classes["abilities"], kwargs
    )
    possessions = _build_possessions(classes["possessions"], kwargs)

    profile_args = {
        "identity": identity,
        "personality": personality,
        "behavior": behavior,
        "story": story,
        "mechanics": mechanics,
        "possessions": possessions,
    }
    return classes["profile"](**profile_args)


# Pre-import commonly used DM modules to keep tests DRY and avoid
DM_HISTORY_HELPER = None
DM_DUNGEON_MASTER = None
try:
    DM_HISTORY_HELPER = import_module("src.dm.history_check_helper")
except ImportError:
    DM_HISTORY_HELPER = None

try:
    DM_DUNGEON_MASTER = import_module("src.dm.dungeon_master")
except ImportError:
    DM_DUNGEON_MASTER = None


def assert_system_prompt_contains(mock_ai, *keywords):
    """Helper to verify system prompt contains specific keywords.

    Args:
        mock_ai: Mock AI client with call history
        *keywords: Keywords that must be in system prompt

    Raises:
        AssertionError: If keywords not found in system prompt
    """
    call_args = mock_ai.client.chat.completions.create.call_args
    messages = call_args[1]["messages"]
    system_msg = next((m for m in messages if m["role"] == "system"), None)

    assert system_msg is not None, "System message should exist"
    for keyword in keywords:
        assert (
            keyword in system_msg["content"].lower()
        ), f"System prompt should contain '{keyword}'"


def run_test_suite(test_suite_name, test_functions):
    """Run a suite of tests with consistent output formatting.

    Args:
        test_suite_name: Name of the test suite (e.g., "CLI Continuation")
        test_functions: List of test functions to run

    Returns:
        Exit code: 0 if all tests pass, 1 if any fail
    """
    print("\n" + "=" * 70)
    print(test_suite_name.upper())
    print("=" * 70)

    passed = 0
    failed = 0

    for test_func in test_functions:
        try:
            test_func()
            print(f"[PASS] {test_func.__name__}")
            passed += 1
        except AssertionError as exc:
            print(f"[FAIL] {test_func.__name__}: {exc}")
            failed += 1
        except (ValueError, OSError, KeyError, AttributeError, TypeError) as exc:
            print(f"[ERROR] {test_func.__name__}: {type(exc).__name__}: {exc}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"{test_suite_name}: {passed} passed, {failed} failed")
    print("=" * 70)

    return 0 if failed == 0 else 1


class FakeAIClient:
    """Reusable fake AI client for tests.

    Provides a minimal `chat_completion`, `send_prompt`, and `ping` interface
    compatible with the production ai_client. `chat_completion` accepts
    arbitrary positional and keyword arguments (e.g., `messages=`,
    `temperature=`) and returns a canned narrative with an optional preview
    suffix. `send_prompt` accepts system and user prompts and returns
    structured response for testing.
    """

    def chat_completion(self, *args, **kwargs):
        """Return a canned narrative; accepts arbitrary args/kwargs.

        When `messages` is provided in kwargs, a short preview is appended
        to the returned string to help tests assert on processed content.
        """
        # Use args/kwargs to avoid pylint unused-arg warnings and provide a
        # small preview when tests pass messages.
        parts = []
        if args:
            parts.append("args:" + ",".join(map(str, args)))

        if kwargs:
            if "messages" in kwargs:
                msgs = kwargs.get("messages")
                try:
                    first = msgs[0]
                    if isinstance(first, dict):
                        content = first.get("content") or first.get("message")
                        if content:
                            parts.append("msg_preview:" + str(content)[:40])
                    else:
                        parts.append("msg_preview:" + str(first)[:40])
                except (IndexError, TypeError, KeyError, AttributeError):
                    parts.append("messages=" + str(msgs))
            else:
                parts.append(
                    "kwargs:" + ",".join(f"{k}={v}" for k, v in kwargs.items())
                )

        suffix = " -- " + " | ".join(parts) if parts else ""
        return (
            "A generated combat narrative describing Aragorn's daring strike." + suffix
        )

    def send_prompt(self, system_prompt: str, user_prompt: str) -> str:
        """Send system and user prompts and return structured response.

        This method is used for structured AI tasks like session analysis.
        Returns a generic structured response for testing.
        """
        del system_prompt, user_prompt
        return (
            "ACTIONS:\n"
            "- Character: Performed an action\n"
            "EVENTS:\n"
            "- A narrative event occurred\n"
        )

    def ping(self) -> bool:
        """Simple health-check returning True to indicate availability."""
        return True


class FakeConsultant:
    """Reusable fake character consultant for tests.

    Provides a minimal `suggest_reaction(situation, context=None)` API
    compatible with production `CharacterConsultant` used by consistency
    checks. Initialize with a preset reaction dict that will be returned by
    `suggest_reaction`.
    """

    def __init__(self, reaction: dict):
        """Create the fake with a preset reaction dict."""
        self._reaction = reaction

    def suggest_reaction(self, situation: str, context=None):
        """Return the preset reaction dict; accepts situation and optional context."""
        _ = situation  # Acknowledge parameter
        _ = context
        return self._reaction

    def ping(self) -> bool:
        """Health-check method to satisfy interfaces expecting availability."""
        return True


class FakeStoryAnalysis:
    """Minimal fake for the StoryAnalysisCLI used in CLI tests.

    Exposes an `analyze_story` method that records it was called. Tests can
    replace the real StoryAnalysisCLI with this fake to avoid filesystem or
    complex behavior.
    """

    def __init__(self):
        self.analyzed = False
        self.last_story = None

    def analyze_story(self):
        """Mark that analyze_story was invoked."""
        self.analyzed = True

    def was_analyzed(self) -> bool:
        """Return True if analyze_story was called since construction or last reset."""
        return bool(self.analyzed)

    def reset(self) -> None:
        """Reset the analyzed state and last_story for reuse in multiple tests."""
        self.analyzed = False
        self.last_story = None


class FakeStoryManager:
    """Minimal fake story manager used by CLI tests.

    Implements the small subset of StoryManager API used by CLI modules.
    """

    def __init__(self, characters=None, existing_stories=None):
        self.consultants = {}
        self._characters = characters or []
        self._existing = existing_stories or []

    def get_character_list(self):
        """Return a list of character names."""
        return list(self._characters)

    def get_existing_stories(self):
        """Return a list of existing story filenames."""
        return list(self._existing)


class FakeDMConsultant:
    """Minimal fake DM consultant exposing the small API used by ConsultationsCLI."""

    def __init__(self, characters=None, npcs=None):
        self._characters = characters or []
        self._npcs = npcs or []

    def get_available_characters(self):
        """Return available character names."""
        return list(self._characters)

    def get_available_npcs(self):
        """Return available NPC names."""
        return list(self._npcs)

    def suggest_narrative(self, prompt, characters_present=None, npcs_present=None):
        """Return a deterministic suggestion structure for tests."""
        _ = (prompt, characters_present, npcs_present)
        return {
            "user_prompt": prompt,
            "character_insights": {},
            "npc_insights": {},
            "narrative_suggestions": ["A short generated narrative."],
            "consistency_notes": [],
        }


class NoSeriesFakeStoryManager:
    """Fake story manager with no series - reused across CLI tests."""

    def get_story_series(self):
        """Return empty list."""
        return []

    def get_story_files_in_series(self, _series_name: str):
        """Return story files (not used in this test)."""
        return []
