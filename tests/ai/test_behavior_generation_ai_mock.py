"""AI-mocking test for behavior generation coercion.

This test monkeypatches the optional AI call in
`src.utils.behaviour_generation` to return malformed output (strings/lists
in the wrong types) and asserts that `generate_behavior_from_personality`
coerces values into the expected types for `CharacterBehavior`.

The test is written so it can be run with pytest or executed directly.
"""

from tests import test_helpers

# Enable behaviour_generation BEFORE importing it
test_helpers.enable_behaviour_generation()

# Import module and types via test_helpers helpers
bg = test_helpers.import_module("src.utils.behaviour_generation")
CharacterBehavior = test_helpers.safe_from_import(
    "src.characters.consultants.character_profile", "CharacterBehavior"
)

def test_ai_malformed_output_coercion():
    """When AI returns malformed types, generator coerces them correctly."""
    # Backup
    orig_ai_flag = getattr(bg, "AI_AVAILABLE", False)
    orig_call = getattr(bg, "call_ai_for_behavior_block", None)

    try:
        # Enable AI path and provide malformed output
        bg.AI_AVAILABLE = True

        def fake_ai(*_args, **_kwargs):
            # Malformed: preferred as string, reactions as list, speech as string,
            # decision as None
            return {
                "preferred_strategies": "single bold move",
                "typical_reactions": ["fear", "fight"],
                "speech_patterns": "loud and abrupt",
                "decision_making_style": None,
            }

        bg.call_ai_for_behavior_block = fake_ai

        behavior = bg.generate_behavior_from_personality(
            personality_traits=["brave"],
            ideals=["protect"],
            bonds=["family"],
            flaws=["pride"],
            backstory="A simple backstory",
        )

        # Backwards-compatible: generator may return a dict (refactor)
        if isinstance(behavior, dict):
            behavior = CharacterBehavior(
                preferred_strategies=list(behavior.get("preferred_strategies", [])),
                typical_reactions=dict(behavior.get("typical_reactions", {})),
                speech_patterns=list(behavior.get("speech_patterns", [])),
                decision_making_style=str(behavior.get("decision_making_style", "")),
            )

        # Type assertions
        assert isinstance(behavior, CharacterBehavior)
        assert isinstance(behavior.preferred_strategies, list)
        assert behavior.preferred_strategies == ["single bold move"]
        assert isinstance(behavior.typical_reactions, dict)
        # When a list was returned for reactions, coercion creates a default str
        assert "default" in behavior.typical_reactions
        assert isinstance(behavior.speech_patterns, list)
        assert behavior.speech_patterns == ["loud and abrupt"]
        assert isinstance(behavior.decision_making_style, str)
        # None is treated as empty string by the generator's coercion
        assert behavior.decision_making_style == ""

    finally:
        # Restore
        bg.AI_AVAILABLE = orig_ai_flag
        bg.call_ai_for_behavior_block = orig_call


def run():
    """
    Run a simple AI-mocking behaviour generation test.

    This function coordinates a small test sequence by:
    - Printing a start message to stdout.
    - Invoking test_ai_malformed_output_coercion(), which performs the actual test logic.
    - Printing a pass message to stdout if the invoked test completes without raising.

    Side effects:
    - Writes progress and result messages to standard output.
    - Depends on the presence of test_ai_malformed_output_coercion() in the same module or scope; 
      any exception raised by that function will propagate.

    Returns:
    - None
    """
    print("Running AI-mocking behaviour generation test...")
    test_ai_malformed_output_coercion()
    print("[PASS] AI-mocking behaviour generation test")


if __name__ == "__main__":
    run()
