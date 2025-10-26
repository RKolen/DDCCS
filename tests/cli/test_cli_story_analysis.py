"""Tests for `StoryAnalysisCLI` flows: analyze_story and convert_combat.

These tests use small fakes and monkeypatching to avoid interactive I/O and
heavy dependencies (AI, real CombatNarrator).
"""

from tests.test_helpers import setup_test_environment, import_module

setup_test_environment()

cli_mod = import_module("src.cli.cli_story_analysis")
StoryAnalysisCLI = cli_mod.StoryAnalysisCLI


class _FakeManagerNoFiles:
    """StoryManager fake that reports no story files."""

    def get_story_files(self):
        """Return an empty list to simulate no stories present."""
        return []

    def get_story_series(self):
        """Return an empty list of story series for callers that expect it."""
        return []


class _FakeManagerWithConsultants:
    """Minimal fake story manager exposing consultants mapping required by the CLI."""

    def __init__(self):
        self.consultants = {}
        self.stories_path = ""

    def get_story_files(self):
        """Return an empty list of story files for consumers."""
        return []

    def get_story_series(self):
        """Return an empty list of series for callers that expect it."""
        return []


def test_analyze_story_no_files():
    """When no story files exist, analyze_story should return early without error."""
    fake_manager = _FakeManagerNoFiles()
    cli = StoryAnalysisCLI(fake_manager, workspace_path=None)

    # Should run without raising and return None
    assert cli.analyze_story() is None


def test_convert_combat_uses_combat_narrator(monkeypatch, tmp_path):
    """convert_combat should initialize the combat narrator and call its methods."""
    fake_manager = _FakeManagerWithConsultants()

    # Provide deterministic helpers to avoid interactive prompts and file IO
    monkeypatch.setattr(cli_mod, "get_multi_line_combat_input", lambda: "A quick skirmish")
    monkeypatch.setattr(cli_mod, "select_narrative_style", lambda: "cinematic")
    monkeypatch.setattr(cli_mod, "select_target_story_for_combat", lambda wp, sm: (None, ""))
    monkeypatch.setattr(cli_mod, "save_combat_narrative", lambda *args, **kwargs: None)

    # Fake CombatNarrator to observe that its methods are invoked
    class FakeCombatNarrator:
        """Simple fake that records calls made by StoryAnalysisCLI."""

        def __init__(self, consultants, ai_client=None):
            self.consultants = consultants
            self.ai_client = ai_client
            self.title_generated = False
            self.narrated = False

        def generate_combat_title(self, combat_prompt, story_context):
            """Generate a short title for the supplied combat prompt and context."""
            _ = (combat_prompt, story_context)
            self.title_generated = True
            return "Generated Title"

        def narrate_combat_from_prompt(self, combat_prompt, story_context, style):
            """Return a short generated narrative for the combat prompt."""
            _ = (combat_prompt, story_context, style)
            self.narrated = True
            return "Generated Narrative"

        def reset(self):
            """Reset internal state for reuse in multiple test runs."""
            self.title_generated = False
            self.narrated = False

    monkeypatch.setattr(cli_mod, "CombatNarrator", FakeCombatNarrator)

    cli = StoryAnalysisCLI(fake_manager, str(tmp_path))
    cli.convert_combat()

    # After convert_combat, the CLI's combat_narrator should be our fake and
    # both methods should have been invoked during the flow.
    assert isinstance(cli.combat_narrator, FakeCombatNarrator)
    assert cli.combat_narrator.title_generated is True
    assert cli.combat_narrator.narrated is True
