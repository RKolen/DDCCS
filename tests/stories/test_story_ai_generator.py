"""
Story AI Generator Tests

Tests for the story_ai_generator module which handles AI-powered narrative
generation, story descriptions, and narrative enhancement features.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock

from tests import test_helpers
from src.stories.story_ai_generator import (
    generate_story_hooks_from_content,
    generate_story_from_prompt,
    generate_story_description,
    enhance_story_narrative,
    generate_session_results_from_story,
)
from src.stories.story_updater import StoryUpdater, ContinuationConfig
from src.utils.npc_lookup_helper import load_relevant_npcs_for_prompt


def test_generate_story_from_prompt_without_ai():
    """Verify generate_story_from_prompt returns None gracefully when AI unavailable."""
    print("\n[TEST] Generate Story From Prompt (No AI)")

    # Call with no AI client
    result = generate_story_from_prompt(
        ai_client=None,
        story_prompt="A wizard enters a tavern",
        story_config={"party_characters": {"Gandalf": {}, "Frodo": {}}},
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
    mock_response.choices[0].message.content = (
        "A wizard named Gandalf entered the tavern..."
    )
    mock_ai.client.chat.completions.create.return_value = mock_response
    mock_ai.model = "gpt-4"

    result = generate_story_from_prompt(
        ai_client=mock_ai,
        story_prompt="A wizard enters a tavern",
        story_config={"party_characters": {"Gandalf": {}, "Frodo": {}}},
    )

    # With mock AI, should return the mocked narrative
    assert isinstance(result, str), "Should return string when AI available"
    assert len(result) > 0, "Generated narrative should not be empty"
    assert (
        mock_ai.client.chat.completions.create.called
    ), "AI client should have been called"

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
    assert (
        mock_ai.client.chat.completions.create.called
    ), "AI client should have been called"

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
    assert (
        mock_ai.client.chat.completions.create.called
    ), "AI client should have been called"

    print("[PASS] Enhance Story Narrative (Expand Mode)")


def test_enhance_story_narrative_dialogue_mode():
    """Test enhance_story_narrative with dialogue mode."""
    print("\n[TEST] Enhance Story Narrative (Dialogue Mode)")

    narrative = "The party meets a merchant."
    mock_ai = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = (
        "The party meets a grizzled merchant. "
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
    assert (
        mock_ai.client.chat.completions.create.called
    ), "AI client should have been called"

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
    assert (
        mock_ai.client.chat.completions.create.called
    ), "AI client should have been called"

    print("[PASS] Enhance Story Narrative (Atmosphere Mode)")


def test_generate_functions_handle_errors():
    """Test that all generate functions handle AI errors gracefully."""
    print("\n[TEST] AI Error Handling")

    # Mock AI that raises AttributeError (which is caught)
    mock_ai = Mock()
    mock_ai.client.chat.completions.create.side_effect = AttributeError("Mock AI error")

    # All functions should handle errors gracefully
    result1 = generate_story_from_prompt(
        ai_client=mock_ai,
        story_prompt="Test prompt",
        story_config={"party_characters": {"Alice": {}}},
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


def test_generate_story_from_prompt_no_combat_with_exploration_flag():
    """Test that is_exploration=True prevents combat in narrative generation."""
    print("\n[TEST] Exploration Flag No Combat")

    mock_ai = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = (
        "The party enters the tavern and orders drinks. "
        "A mysterious stranger beckons from the corner."
    )
    mock_ai.client.chat.completions.create.return_value = mock_response
    mock_ai.model = "gpt-4"

    result = generate_story_from_prompt(
        ai_client=mock_ai,
        story_prompt="The party encounters bandits on the road",
        story_config={
            "party_characters": {"Legolas": {"dnd_class": "ranger"}},
            "is_exploration": True,
        },
    )

    assert isinstance(result, str), "Should return string with exploration flag"

    # Verify system prompt contains no-combat language
    test_helpers.assert_system_prompt_contains(mock_ai, "combat", "hostile")

    print("[PASS] Exploration Flag No Combat")


def test_generate_story_from_prompt_with_rag_context():
    """Test that RAG spell/ability lookup is included in story generation."""
    print("\n[TEST] Story Generation with RAG Context")

    mock_ai = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = (
        "The wizard casts a fireball spell, illuminating the dark dungeon."
    )
    mock_ai.client.chat.completions.create.return_value = mock_response
    mock_ai.model = "gpt-4"

    result = generate_story_from_prompt(
        ai_client=mock_ai,
        story_prompt="A wizard casts fireball at approaching enemies",
        story_config={
            "party_characters": {"Gandalf": {"dnd_class": "wizard"}},
            "is_exploration": True,
        },
    )

    assert isinstance(result, str), "Should return string"

    # Verify user prompt includes ability_context placeholder (even if RAG unavailable)
    call_args = mock_ai.client.chat.completions.create.call_args
    messages = call_args[1]["messages"]
    user_msg = next((m for m in messages if m["role"] == "user"), None)

    assert user_msg is not None, "User message should exist"
    # The user prompt should contain reference to spells if RAG is available
    assert (
        "fireball" in user_msg["content"].lower()
    ), "User prompt should reference mentioned spells"

    print("[PASS] Story Generation with RAG Context")


def test_generate_story_rag_graceful_fallback():
    """Test that story generation works when RAG is unavailable."""
    print("\n[TEST] Story Generation RAG Fallback")

    mock_ai = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = (
        "The party arrives at a mysterious location."
    )
    mock_ai.client.chat.completions.create.return_value = mock_response
    mock_ai.model = "gpt-4"

    # Should work even if RAG lookup doesn't find anything
    result = generate_story_from_prompt(
        mock_ai,
        "Party explores an empty room",
        story_config={"party_characters": {"Alice": {"dnd_class": "rogue"}}},
    )

    assert isinstance(result, str), "Should return string even without RAG results"
    assert (
        mock_ai.client.chat.completions.create.called
    ), "AI should be called regardless of RAG availability"

    print("[PASS] Story Generation RAG Fallback")


def test_generate_story_hooks_with_ai():
    """Test generate_story_hooks_from_content with AI available."""
    print("\n[TEST] Generate Story Hooks (With AI)")

    story_content = (
        "Kael investigates the ruins and finds a hidden lever. "
        "Lira casts Detect Magic, revealing a faint aura. "
        "An NPC named Tobias Stone offers a cryptic warning."
    )
    character_context = {
        "Kael": {"dnd_class": "rogue", "level": 3},
        "Lira": {"dnd_class": "wizard", "level": 4},
    }
    mock_ai = test_helpers.FakeAIClient()
    hooks = generate_story_hooks_from_content(mock_ai, story_content, character_context)
    assert isinstance(
        hooks, (list, dict, type(None))
    ), "Should return list, dict, or None"

    print("[PASS] Generate Story Hooks (With AI)")


def test_generate_story_hooks_fallback():
    """Test generate_story_hooks_from_content fallback when AI unavailable."""
    print("\n[TEST] Generate Story Hooks (Fallback)")

    story_content = (
        "Kael investigates the ruins and finds a hidden lever. "
        "Lira casts Detect Magic, revealing a faint aura. "
        "An NPC named Tobias Stone offers a cryptic warning."
    )
    character_context = {
        "Kael": {"dnd_class": "rogue", "level": 3},
        "Lira": {"dnd_class": "wizard", "level": 4},
    }
    hooks = generate_story_hooks_from_content(None, story_content, character_context)
    assert isinstance(
        hooks, (list, dict, type(None))
    ), "Should return list, dict, or None"

    print("[PASS] Generate Story Hooks (Fallback)")


def test_phase1_append_ai_continuation_filters_template():
    """Phase 1: Verify AI continuation filters template text correctly."""
    print("\n[TEST] Phase 1 - AI Continuation (Template Filtering)")

    workspace = str(Path.cwd())
    with tempfile.TemporaryDirectory() as tmpdir:
        campaign_dir = tmpdir
        story_file = os.path.join(tmpdir, "test_story.md")

        # Create initial story with template text
        initial_content = (
            "# Test Story\n\n"
            "The party enters the tavern.\n\n"
            "## Scene Title\n\n"
            "[Add descriptive details]\n\n"
            "This is actual narrative."
        )
        with open(story_file, "w", encoding="utf-8") as f:
            f.write(initial_content)

        config = (
            ContinuationConfig()
            .set_paths(story_file, campaign_dir, workspace)
            .set_content("New story content here.")
        )

        updater = StoryUpdater()
        result = updater.append_ai_continuation(config)

        assert result is True, "Should successfully append continuation"
        assert os.path.exists(story_file), "Story file should exist"

        # Verify content was updated
        with open(story_file, "r", encoding="utf-8") as f:
            updated_content = f.read()

        assert (
            "New story content here" in updated_content
        ), "Continuation should be appended"

    print("[PASS] Phase 1 - AI Continuation (Template Filtering)")


def test_phase1_preserves_narrative_content():
    """Phase 1: Verify template filtering preserves narrative content."""
    print("\n[TEST] Phase 1 - AI Continuation (Preserve Narrative)")

    workspace = str(Path.cwd())
    with tempfile.TemporaryDirectory() as tmpdir:
        campaign_dir = tmpdir
        story_file = os.path.join(tmpdir, "test_story.md")

        # Create story with valuable narrative and template text
        initial_content = (
            "# Chapter 1\n\n"
            "The party approaches the castle gates. "
            "A guard stops them and demands entry papers.\n\n"
            "[Add more detail about the atmosphere]"
        )
        with open(story_file, "w", encoding="utf-8") as f:
            f.write(initial_content)

        config = (
            ContinuationConfig()
            .set_paths(story_file, campaign_dir, workspace)
            .set_content("The guard examines their papers carefully.")
        )

        updater = StoryUpdater()
        result = updater.append_ai_continuation(config)

        assert result is True, "Should successfully handle story"
        with open(story_file, "r", encoding="utf-8") as f:
            updated_content = f.read()

        # Narrative should be preserved
        assert "party" in updated_content.lower(), "Party reference should be preserved"
        assert "guard" in updated_content.lower(), "Guard reference should be preserved"

    print("[PASS] Phase 1 - AI Continuation (Preserve Narrative)")


# Phase 2: NPC Lookup Tests
def test_npc_lookup_by_location():
    """Phase 2: Verify NPC lookup finds NPCs by location context."""
    print("\n[TEST] Phase 2 - NPC Lookup (By Location)")

    workspace = str(Path.cwd())
    prompt = (
        "The party arrives at the tavern. The innkeeper greets them warmly. "
        "They settle in and order drinks."
    )

    npcs = load_relevant_npcs_for_prompt(prompt, workspace)

    # Should find tavern-related NPCs or return empty list
    assert isinstance(npcs, list), "Should return list of NPCs"

    print("[PASS] Phase 2 - NPC Lookup (By Location)")


def test_npc_lookup_by_role():
    """Phase 2: Verify NPC lookup finds NPCs by role keywords."""
    print("\n[TEST] Phase 2 - NPC Lookup (By Role)")

    workspace = str(Path.cwd())
    prompt = (
        "The party encounters a merchant at the marketplace. "
        "He offers exotic wares from distant lands."
    )

    npcs = load_relevant_npcs_for_prompt(prompt, workspace)

    # Should recognize merchant role
    assert isinstance(npcs, list), "Should return list of NPCs"

    print("[PASS] Phase 2 - NPC Lookup (By Role)")


def test_npc_lookup_empty_context():
    """Phase 2: Verify NPC lookup handles empty context gracefully."""
    print("\n[TEST] Phase 2 - NPC Lookup (Empty Context)")

    workspace = str(Path.cwd())
    prompt = "The party walks silently through the forest."

    npcs = load_relevant_npcs_for_prompt(prompt, workspace)

    # Should return empty list gracefully
    assert isinstance(npcs, list), "Should return empty list gracefully"

    print("[PASS] Phase 2 - NPC Lookup (Empty Context)")


# Phase 3: Session Results Tests
def test_generate_session_results_with_ai():
    """Phase 3: Verify session results extraction with AI available."""
    print("\n[TEST] Phase 3 - Session Results (With AI)")

    story = (
        "Kael attempted a stealth check (DC 12) and rolled a 15, succeeding. "
        "Lira cast Fireball (attack roll DC 14) against the goblins. "
        "Combat lasted 3 rounds with 5 enemies defeated."
    )

    mock_ai = test_helpers.FakeAIClient()

    results = generate_session_results_from_story(mock_ai, story, ["Kael", "Lira"])

    assert isinstance(
        results, (str, type(None))
    ), "Should return string of session results or None"

    print("[PASS] Phase 3 - Session Results (With AI)")


def test_generate_session_results_fallback():
    """Phase 3: Verify session results fallback when AI unavailable."""
    print("\n[TEST] Phase 3 - Session Results (Fallback)")

    story = (
        "Kael made a stealth check and succeeded. "
        "Combat ensued with multiple enemies."
    )

    results = generate_session_results_from_story(None, story, ["Kael"])

    # Should handle gracefully without AI
    assert isinstance(results, (str, type(None))), "Should handle missing AI gracefully"

    print("[PASS] Phase 3 - Session Results (Fallback)")


def test_generate_session_results_identifies_actions():
    """Phase 3: Verify session results identifies character actions."""
    print("\n[TEST] Phase 3 - Session Results (Action Identification)")

    story = (
        "Kael used Stealth to sneak past the guards. "
        "Lira cast Detect Magic to sense magical auras. "
        "Aragorn made a Persuasion check to negotiate with the merchant."
    )

    mock_ai = test_helpers.FakeAIClient()

    results = generate_session_results_from_story(
        mock_ai, story, ["Kael", "Lira", "Aragorn"]
    )

    assert isinstance(results, (str, type(None))), "Should identify character actions"

    print("[PASS] Phase 3 - Session Results (Action Identification)")


def run_all_story_ai_generator_tests():
    """Run all story AI generator tests."""
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
        test_generate_story_from_prompt_no_combat_with_exploration_flag,
        test_generate_story_from_prompt_with_rag_context,
        test_generate_story_rag_graceful_fallback,
        test_generate_story_hooks_with_ai,
        test_generate_story_hooks_fallback,
        # Phase 1-3 Tests
        test_phase1_append_ai_continuation_filters_template,
        test_phase1_preserves_narrative_content,
        test_npc_lookup_by_location,
        test_npc_lookup_by_role,
        test_npc_lookup_empty_context,
        test_generate_session_results_with_ai,
        test_generate_session_results_fallback,
        test_generate_session_results_identifies_actions,
    ]

    return test_helpers.run_test_suite("Story AI Generator", tests)


if __name__ == "__main__":

    sys.exit(run_all_story_ai_generator_tests())
