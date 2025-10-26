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

import sys
from pathlib import Path
import importlib


def setup_test_environment():
    """
    Configure test environment for proper execution.

    - Adds project root to Python path for imports
    - Returns project root path for test use

    Returns:
        pathlib.Path: Project root directory

    """
    # Add project root to path for imports (tests/ parent directory)
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

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


def make_profile(name: str = "TestChar", dnd_class=None, level: int = 1, **kwargs):
    """Create a minimal CharacterProfile instance for tests.

    This helper constructs the nested dataclasses (Identity, Possessions,
    Behavior, Personality) used by production `CharacterProfile` so tests
    can avoid boilerplate fixture construction.
    """
    cp_mod = import_module("src.characters.consultants.character_profile")
    character_profile_cls = getattr(cp_mod, "CharacterProfile")
    character_possessions_cls = getattr(cp_mod, "CharacterPossessions")
    character_behavior_cls = getattr(cp_mod, "CharacterBehavior")
    character_personality_cls = getattr(cp_mod, "CharacterPersonality")

    identity = make_identity(name=name, dnd_class=dnd_class, level=level)

    equipment = {
        "weapons": kwargs.get("weapons") or [],
        "armor": kwargs.get("armor") or [],
        "items": kwargs.get("items_list") or [],
    }

    magic_items = kwargs.get("magic_items") or []
    speech_patterns = kwargs.get("speech_patterns") or []
    relationships = kwargs.get("relationships") or {}

    possessions = character_possessions_cls(equipment=equipment, magic_items=magic_items)

    behavior = character_behavior_cls(speech_patterns=speech_patterns)
    personality = character_personality_cls(relationships=relationships)

    return (
        character_profile_cls(
            identity=identity,
            possessions=possessions,
            behavior=behavior,
            personality=personality,
        )
    )


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


class FakeAIClient:
    """Reusable fake AI client for tests.

    Provides a minimal `chat_completion` and `ping` interface compatible with
    the production ai_client. `chat_completion` accepts arbitrary positional
    and keyword arguments (e.g., `messages=`, `temperature=`) and returns a
    canned narrative with an optional preview suffix derived from the
    provided arguments.
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

    def ping(self) -> bool:
        """Simple health-check returning True to indicate availability."""
        return True


class FakeConsultant:
    """Reusable fake character consultant for tests.

    Provides a minimal `suggest_reaction(prompt=None)` and `ping()` API
    compatible with production `CharacterConsultant` used by consistency
    checks. Initialize with a preset reaction dict that will be returned by
    `suggest_reaction`.
    """

    def __init__(self, reaction: dict):
        """Create the fake with a preset reaction dict."""
        self._reaction = reaction

    def suggest_reaction(self, prompt=None):
        """Return the preset reaction dict; accepts an optional prompt."""
        _ = prompt
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
