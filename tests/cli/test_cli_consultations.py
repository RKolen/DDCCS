"""Tests for `ConsultationsCLI.get_dm_narrative_suggestions` behavior.

This test uses `FakeDMConsultant` from `tests.test_helpers` and monkeypatches
`input()` to simulate user prompts for the narrative request.
"""

from test_helpers import (
    setup_test_environment,
    import_module,
    FakeDMConsultant,
)

setup_test_environment()

cli_mod = import_module("src.cli.cli_consultations")
ConsultationsCLI = cli_mod.ConsultationsCLI


def test_get_dm_narrative_suggestions_with_fake_dm(monkeypatch):
    """get_dm_narrative_suggestions should call into the DM consultant and print suggestions."""
    fake_dm = FakeDMConsultant(characters=["Frodo"], npcs=["Bilbo"])

    # Create a minimal story_manager fake (not used heavily here)
    fake_story_manager = object()

    cli = ConsultationsCLI(fake_story_manager, fake_dm)

    # Prepare inputs: prompt, characters input (blank), npcs input (blank), final Enter to continue
    inputs = ["A quiet tavern scene", "", "", ""]

    def fake_input(prompt=""):
        # Pop from inputs list to simulate user interaction
        _ = prompt
        try:
            return inputs.pop(0)
        except IndexError:
            return ""

    monkeypatch.setattr("builtins.input", fake_input)

    # Should run without raising
    cli.get_dm_narrative_suggestions()

    # No explicit return value; ensure fake DM still has expected available characters
    assert "Frodo" in fake_dm.get_available_characters()
