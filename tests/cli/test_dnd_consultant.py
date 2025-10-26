"""Tests for the top-level DDConsultantCLI behavior.

Covers non-interactive command handling (run_command) by wiring in a fake
`StoryAnalysis` implementation from `tests.test_helpers` and asserting the
analyze flow is invoked.
"""

from test_helpers import setup_test_environment, import_module, FakeStoryAnalysis


setup_test_environment()

# Import the CLI module under test
dnd_cli_mod = import_module("src.cli.dnd_consultant")
DDConsultantCLI = dnd_cli_mod.DDConsultantCLI


def test_run_command_analyze_triggers_story_analysis():
    """run_command('analyze') should call the story analysis component."""
    fake_analysis = FakeStoryAnalysis()

    cli = DDConsultantCLI(workspace_path=None, campaign_name=None)
    # Inject our fake analysis object
    cli.story_analysis = fake_analysis

    # Call non-interactive analyze command
    cli.run_command("analyze", story_file="example_story.md")

    assert fake_analysis.analyzed is True
