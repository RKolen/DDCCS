"""
Story AI Generator Tests

Tests for the story_ai_generator module which handles AI-powered narrative
generation, story descriptions, and narrative enhancement features.
"""

from unittest.mock import Mock

from tests import test_helpers

# Import functions using safe import helper
generate_story_from_prompt = test_helpers.safe_from_import(
    "src.stories.story_ai_generator", "generate_story_from_prompt"
)
generate_story_description = test_helpers.safe_from_import(
    "src.stories.story_ai_generator", "generate_story_description"
)
enhance_story_narrative = test_helpers.safe_from_import(
    "src.stories.story_ai_generator", "enhance_story_narrative"
)


def test_generate_story_from_prompt_without_ai():
    """Verify generate_story_from_prompt returns None gracefully when AI unavailable."""
    print("\n[TEST] Generate Story From Prompt (No AI)")

    # Call with no AI client
    result = generate_story_from_prompt(
        ai_client=None,
        story_prompt="A wizard enters a tavern",
        party_characters={"Gandalf": {}, "Frodo": {}},
        campaign_context=None,
    )

    # Should return None when AI is unavailable
    assert result is None, "Should return None when AI client is None"

    print("[PASS] Generate Story From Prompt (No AI)")


def test_generate_story_from_prompt_with_mock_ai():
    """Test generate_story_from_prompt with mocked AI client."""
    print("\n[TEST] Generate Story From Prompt (With Mock AI)")

    # Mock AI client
    mock_ai = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "A wizard named Gandalf entered the tavern..."
    mock_ai.client.chat.completions.create.return_value = mock_response
    mock_ai.model = "gpt-4"

    result = generate_story_from_prompt(
        ai_client=mock_ai,
        story_prompt="A wizard enters a tavern",
        party_characters={"Gandalf": {}, "Frodo": {}},
    )

    # With mock AI, should return the mocked narrative
    assert isinstance(result, str), "Should return string when AI available"
    assert len(result) > 0, "Generated narrative should not be empty"
    assert mock_ai.client.chat.completions.create.called, "AI client should have been called"

    print("[PASS] Generate Story From Prompt (With Mock AI)")


def test_generate_story_description_without_ai():
    """Verify generate_story_description returns None gracefully when AI unavailable."""
    print("\n[TEST] Generate Story Description (No AI)")

    result = generate_story_description(
        ai_client=None,
        story_title="The Dragon's Lair",
    )

    # Should return None when AI is unavailable
    assert result is None, "Should return None when AI client is None"

    print("[PASS] Generate Story Description (No AI)")


def test_generate_story_description_with_mock_ai():
    """Test generate_story_description with mocked AI client."""
    print("\n[TEST] Generate Story Description (With Mock AI)")

    # Mock AI client
    mock_ai = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "A tale of adventure and danger."
    mock_ai.client.chat.completions.create.return_value = mock_response
    mock_ai.model = "gpt-4"

    result = generate_story_description(
        ai_client=mock_ai,
        story_title="The Dragon's Lair",
    )

    # With mock AI, should return the mocked description
    assert isinstance(result, str), "Should return string when AI available"
    assert len(result) > 0, "Generated description should not be empty"
    assert mock_ai.client.chat.completions.create.called, "AI client should have been called"

    print("[PASS] Generate Story Description (With Mock AI)")


def test_enhance_story_narrative_without_ai():
    """Verify enhance_story_narrative returns None gracefully when AI unavailable."""
    print("\n[TEST] Enhance Story Narrative (No AI)")

    narrative = "The party enters the forest."
    result = enhance_story_narrative(
        ai_client=None,
        narrative_text=narrative,
        enhancement_type="expand",
    )

    # Should return None when AI is unavailable
    assert result is None, "Should return None when AI client is None"

    print("[PASS] Enhance Story Narrative (No AI)")


def test_enhance_story_narrative_expand_mode():
    """Test enhance_story_narrative with expand mode."""
    print("\n[TEST] Enhance Story Narrative (Expand Mode)")

    narrative = "The party enters the forest."
    mock_ai = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = (
        "The party carefully enters the dark, ancient forest. "
        "Trees tower overhead, and strange sounds echo through the woods."
    )
    mock_ai.client.chat.completions.create.return_value = mock_response
    mock_ai.model = "gpt-4"

    result = enhance_story_narrative(
        ai_client=mock_ai,
        narrative_text=narrative,
        enhancement_type="expand",
    )

    assert isinstance(result, str), "Should return string when AI available"
    assert len(result) > len(narrative), "Expanded narrative should be longer"
    assert mock_ai.client.chat.completions.create.called, "AI client should have been called"

    print("[PASS] Enhance Story Narrative (Expand Mode)")


def test_enhance_story_narrative_dialogue_mode():
    """Test enhance_story_narrative with dialogue mode."""
    print("\n[TEST] Enhance Story Narrative (Dialogue Mode)")

    narrative = "The party meets a merchant."
    mock_ai = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = (
        'The party meets a grizzled merchant. '
        '"Welcome, travelers," he says with a knowing smile.'
    )
    mock_ai.client.chat.completions.create.return_value = mock_response
    mock_ai.model = "gpt-4"

    result = enhance_story_narrative(
        ai_client=mock_ai,
        narrative_text=narrative,
        enhancement_type="dialogue",
    )

    assert isinstance(result, str), "Should return string when AI available"
    assert mock_ai.client.chat.completions.create.called, "AI client should have been called"

    print("[PASS] Enhance Story Narrative (Dialogue Mode)")


def test_enhance_story_narrative_atmosphere_mode():
    """Test enhance_story_narrative with atmosphere mode."""
    print("\n[TEST] Enhance Story Narrative (Atmosphere Mode)")

    narrative = "A storm approaches."
    mock_ai = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = (
        "Dark clouds gather on the horizon. Thunder rumbles ominously. "
        "The wind picks up, carrying the smell of rain and ozone."
    )
    mock_ai.client.chat.completions.create.return_value = mock_response
    mock_ai.model = "gpt-4"

    result = enhance_story_narrative(
        ai_client=mock_ai,
        narrative_text=narrative,
        enhancement_type="atmosphere",
    )

    assert isinstance(result, str), "Should return string when AI available"
    assert mock_ai.client.chat.completions.create.called, "AI client should have been called"

    print("[PASS] Enhance Story Narrative (Atmosphere Mode)")


def test_generate_functions_handle_errors():
    """Test that all generate functions handle AI errors gracefully."""
    print("\n[TEST] AI Error Handling")

    # Mock AI that raises AttributeError (which is caught)
    mock_ai = Mock()
    mock_ai.client.chat.completions.create.side_effect = AttributeError(
        "Mock AI error"
    )

    # All functions should handle errors gracefully
    result1 = generate_story_from_prompt(
        ai_client=mock_ai,
        story_prompt="Test prompt",
        party_characters={"Alice": {}},
    )
    assert result1 is None, "Should return None on AI error"

    result2 = generate_story_description(
        ai_client=mock_ai,
        story_title="Test Title",
    )
    assert result2 is None, "Should return None on AI error"

    result3 = enhance_story_narrative(
        ai_client=mock_ai,
        narrative_text="Test narrative",
        enhancement_type="expand",
    )
    assert result3 is None, "Should return None on AI error"

    print("[PASS] AI Error Handling")


def run_all_story_ai_generator_tests():
    """Run all story AI generator tests."""
    print("\n" + "=" * 70)
    print("STORY AI GENERATOR TESTS")
    print("=" * 70)

    tests = [
        test_generate_story_from_prompt_without_ai,
        test_generate_story_from_prompt_with_mock_ai,
        test_generate_story_description_without_ai,
        test_generate_story_description_with_mock_ai,
        test_enhance_story_narrative_without_ai,
        test_enhance_story_narrative_expand_mode,
        test_enhance_story_narrative_dialogue_mode,
        test_enhance_story_narrative_atmosphere_mode,
        test_generate_functions_handle_errors,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"[FAIL] {test_func.__name__}: {e}")
        except (ValueError, OSError, KeyError, AttributeError, TypeError) as e:
            failed += 1
            print(f"[ERROR] {test_func.__name__}: {type(e).__name__}: {e}")

    print("\n" + "=" * 70)
    print(f"Story AI Generator: {passed} passed, {failed} failed")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(run_all_story_ai_generator_tests())
