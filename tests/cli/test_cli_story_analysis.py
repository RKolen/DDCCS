"""Tests for `StoryAnalysisCLI` flows: analyze_story and convert_combat.

These tests use small fakes and monkeypatching to avoid interactive I/O and
heavy dependencies (AI, real CombatNarrator).
"""

import shutil
from tests.test_helpers import setup_test_environment, import_module

project_root = setup_test_environment()

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

    def get_story_files_in_series(self, series_name):
        """Return story files for a specific series."""
        _ = series_name
        return []


class _FakeManagerWithSeriesStories:
    """StoryManager fake that returns stories within a series."""

    def __init__(self):
        self.consultants = {}
        self.stories_path = "/root"
        self.series_stories = {"Example_Campaign": ["001_start.md", "002_continue.md"]}

    def get_story_files(self):
        """Return root-level story files."""
        return []

    def get_story_files_in_series(self, series_name):
        """Return stories in specified series."""
        return self.series_stories.get(series_name, [])

    def analyze_story_file(self, filepath):
        """Return a fake analysis for any story file."""
        return {
            "story_file": filepath,
            "overall_consistency": {"rating": "GOOD", "score": 0.85, "summary": "Test"},
            "consultant_analyses": {},
        }


def test_analyze_story_no_files():
    """When no story files exist, analyze_story should return early without error."""
    fake_manager = _FakeManagerNoFiles()
    cli = StoryAnalysisCLI(fake_manager, workspace_path=None)

    # Should run without raising and return None
    assert cli.analyze_story() is None


def test_analyze_story_with_series_context(monkeypatch, tmp_path):
    """analyze_story with series_name should use get_story_files_in_series."""
    fake_manager = _FakeManagerWithSeriesStories()
    cli = StoryAnalysisCLI(fake_manager, str(tmp_path))

    # Track calls to ensure series-specific method is used
    calls = {"get_story_files_in_series": 0}

    original_method = fake_manager.get_story_files_in_series

    def tracked_get_story_files_in_series(series_name):
        calls["get_story_files_in_series"] += 1
        return original_method(series_name)

    monkeypatch.setattr(
        fake_manager, "get_story_files_in_series", tracked_get_story_files_in_series
    )

    # Mock input to exit early without selecting a file
    monkeypatch.setattr("builtins.input", lambda prompt: "invalid")

    cli.analyze_story(series_name="Example_Campaign")

    # Verify series-specific method was called
    assert calls["get_story_files_in_series"] == 1


def test_analyze_story_without_series_context(monkeypatch):
    """analyze_story without series_name should use get_story_files."""
    fake_manager = _FakeManagerWithConsultants()
    cli = StoryAnalysisCLI(fake_manager, workspace_path=None)

    # Track calls
    calls = {"get_story_files": 0}

    original_method = fake_manager.get_story_files

    def tracked_get_story_files():
        calls["get_story_files"] += 1
        return original_method()

    monkeypatch.setattr(fake_manager, "get_story_files", tracked_get_story_files)

    cli.analyze_story()

    # Verify root-level method was called
    assert calls["get_story_files"] == 1


def test_analyze_story_series_context_uses_campaign_path(monkeypatch, tmp_path):
    """analyze_story with series should construct path using get_campaign_path."""
    fake_manager = _FakeManagerWithSeriesStories()
    cli = StoryAnalysisCLI(fake_manager, str(tmp_path))

    # Mock to track the filepath passed to analyze_story_file
    analyzed_paths = []

    def fake_analyze(filepath):
        analyzed_paths.append(filepath)
        return {
            "story_file": filepath,
            "overall_consistency": {"rating": "OK", "score": 0.5, "summary": "Test"},
            "consultant_analyses": {},
        }

    monkeypatch.setattr(fake_manager, "analyze_story_file", fake_analyze)
    monkeypatch.setattr("builtins.input", lambda prompt: "1")
    monkeypatch.setattr("builtins.print", lambda *args, **kwargs: None)

    cli.analyze_story(series_name="Example_Campaign")

    # Verify path includes game_data/campaigns structure (from get_campaign_path)
    assert len(analyzed_paths) == 1
    assert "game_data" in analyzed_paths[0] or "campaigns" in analyzed_paths[0]


def test_save_analysis_to_session_results_creates_file(tmp_path):
    """save_analysis_to_session_results should create session results file."""
    fake_manager = _FakeManagerWithSeriesStories()
    cli = StoryAnalysisCLI(fake_manager, str(tmp_path))

    # Create a test series directory
    series_path = tmp_path / "game_data" / "campaigns" / "TestSeries"
    series_path.mkdir(parents=True, exist_ok=True)

    analysis = {
        "story_file": "test.md",
        "overall_consistency": {"rating": "GOOD", "score": 0.8, "summary": "Test analysis"},
        "consultant_analyses": {"Aragorn": {"overall_rating": "GOOD", "consistency_score": 0.8}},
        "dc_suggestions": {},
    }

    cli.save_analysis_to_session_results(analysis, str(series_path), "001_test.md")

    # Verify session results file was created
    session_files = list(series_path.glob("session_results_*.md"))
    assert len(session_files) > 0, "Session results file should be created"
    assert any("test" in f.name.lower() for f in session_files), \
        "Session file should include story name"


def test_save_analysis_appends_to_existing_session_file(tmp_path):
    """save_analysis_to_session_results should append to existing file on same day."""
    fake_manager = _FakeManagerWithSeriesStories()
    cli = StoryAnalysisCLI(fake_manager, str(tmp_path))

    series_path = tmp_path / "game_data" / "campaigns" / "TestSeries"
    series_path.mkdir(parents=True, exist_ok=True)

    analysis1 = {
        "story_file": "test.md",
        "overall_consistency": {"rating": "GOOD", "score": 0.8, "summary": "First"},
        "consultant_analyses": {},
        "dc_suggestions": {},
    }

    analysis2 = {
        "story_file": "test.md",
        "overall_consistency": {"rating": "OK", "score": 0.6, "summary": "Second"},
        "consultant_analyses": {},
        "dc_suggestions": {},
    }

    # Save first analysis
    cli.save_analysis_to_session_results(analysis1, str(series_path), "001_test.md")

    # Save second analysis to same file
    cli.save_analysis_to_session_results(analysis2, str(series_path), "001_test.md")

    # Verify only one file exists
    session_files = list(series_path.glob("session_results_*.md"))
    assert len(session_files) == 1, "Should have single session results file"

    # Verify both analyses are in the file
    content = session_files[0].read_text(encoding="utf-8")
    assert "First" in content, "First analysis should be present"
    assert "Second" in content, "Second analysis should be present"


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


def test_analyze_character_development_series(monkeypatch, tmp_path):
    """analyze_character_development_series should generate a report using real data."""
    fake_manager = _FakeManagerWithSeriesStories()
    cli = StoryAnalysisCLI(fake_manager, str(tmp_path))

    # Copy real character data to tmp_path
    real_chars_dir = project_root / "game_data" / "characters"
    tmp_chars_dir = tmp_path / "game_data" / "characters"
    shutil.copytree(real_chars_dir, tmp_chars_dir)

    # Copy real campaign data to tmp_path
    real_campaign_dir = project_root / "game_data" / "campaigns" / "Example_Campaign"
    tmp_campaign_dir = tmp_path / "game_data" / "campaigns" / "Example_Campaign"
    shutil.copytree(real_campaign_dir, tmp_campaign_dir)

    # Mock dependencies
    # Use real party members from Example_Campaign
    monkeypatch.setattr(cli_mod, "load_current_party",
                        lambda **kwargs: ["Aragorn", "Frodo Baggins", "Gandalf the Grey"])
    monkeypatch.setattr(cli_mod, "get_campaign_path", lambda name, ws: str(tmp_campaign_dir))

    # Use real story content
    def real_read_text_file(path):
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    monkeypatch.setattr(cli_mod, "read_text_file", real_read_text_file)

    # Mock extract_character_actions to return some data (still mocking this as it's complex logic)
    # But we verify it receives the real profiles
    def fake_extract(_content, _party, _truncate, character_profiles=None):
        assert character_profiles is not None
        assert "Aragorn" in character_profiles
        assert "Frodo Baggins" in character_profiles
        # Verify real profile data is loaded
        assert character_profiles["Aragorn"]["dnd_class"] == "Ranger"

        return [{
            "character": "Aragorn",
            "action": "Aragorn led the way.",
            "reasoning": "Leadership.",
            "consistency": "Consistent",
            "notes": "Good."
        }]
    monkeypatch.setattr(cli_mod, "extract_character_actions", fake_extract)

    # Mock write_text_file to verify output
    written_files = {}

    def fake_write(path, content):
        written_files[path] = content
    monkeypatch.setattr(cli_mod, "write_text_file", fake_write)

    # Mock input to confirm analysis
    monkeypatch.setattr("builtins.input", lambda prompt: "y")
    monkeypatch.setattr("builtins.print", lambda *args, **kwargs: None)

    # Run analysis on real stories
    stories = ["001_start.md", "002_continue.md", "003_end.md"]
    cli.analyze_character_development_series("Example_Campaign", stories)

    # Verify report was generated
    assert len(written_files) == 1
    report_path = list(written_files.keys())[0]
    content = written_files[report_path]

    assert "Character Development Analysis" in content
    assert "Aragorn" in content
    # Verify real background data is used in the report
    assert "Heir of Isildur" in content or "Ranger of the North" in content
