"""
Tests for AI Integration Component

This module tests the AIConsultant component that provides AI-powered
consultation features with graceful fallback to rule-based methods.
"""

import sys
from pathlib import Path
import test_helpers

# Add tests directory to path for test_helpers
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import and configure test environment
test_helpers.setup_test_environment()

# Import character components
try:
    from src.characters.consultants.consultant_ai import (
        AIConsultant, AI_AVAILABLE
    )
    from src.characters.consultants.character_profile import (
        CharacterProfile, CharacterIdentity
    )
    from src.characters.character_sheet import DnDClass
except ImportError as e:
    print(f"Error importing AI consultant components: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


def test_ai_consultant_initialization():
    """Test AI consultant initialization."""
    print("\n[TEST] AI Consultant - Initialization")

    identity = CharacterIdentity(
        name="TestChar",
        character_class=DnDClass.FIGHTER,
        level=5
    )
    profile = CharacterProfile(identity=identity)
    class_knowledge = {"key_features": ["Action Surge"]}

    consultant = AIConsultant(profile, class_knowledge)

    assert consultant.profile == profile, "Profile not set correctly"
    assert consultant.class_knowledge == class_knowledge, "Knowledge not set"
    assert consultant.ai_client is None, "AI client should be None by default"
    print("  [OK] AI consultant initialized correctly")

    print("[PASS] AI Consultant - Initialization")


def test_ai_consultant_initialization_with_client():
    """Test AI consultant initialization with AI client."""
    print("\n[TEST] AI Consultant - Initialization with Client")

    identity = CharacterIdentity(
        name="TestChar",
        character_class=DnDClass.WIZARD,
        level=5
    )
    profile = CharacterProfile(identity=identity)

    # Create mock AI client
    mock_client = type('MockAIClient', (), {})()

    consultant = AIConsultant(profile, {}, ai_client=mock_client)

    assert consultant.ai_client == mock_client, "AI client not set correctly"
    print("  [OK] AI consultant initialized with client")

    print("[PASS] AI Consultant - Initialization with Client")


def test_get_ai_client_no_ai():
    """Test get_ai_client when AI is not available."""
    print("\n[TEST] AI Consultant - Get AI Client (No AI)")

    identity = CharacterIdentity(
        name="TestChar",
        character_class=DnDClass.FIGHTER,
        level=5
    )
    profile = CharacterProfile(identity=identity)
    consultant = AIConsultant(profile, {})

    # If AI is not available, should return None
    if not AI_AVAILABLE:
        client = consultant.get_ai_client()
        assert client is None, "Should return None when AI not available"
        print("  [OK] Returns None when AI not available")
    else:
        print("  [OK] AI is available (skipping None test)")

    print("[PASS] AI Consultant - Get AI Client (No AI)")


def test_get_ai_client_with_global():
    """Test get_ai_client with global AI client."""
    print("\n[TEST] AI Consultant - Get AI Client (Global)")

    identity = CharacterIdentity(
        name="TestChar",
        character_class=DnDClass.WIZARD,
        level=5
    )
    profile = CharacterProfile(identity=identity)

    mock_global_client = type('MockGlobalClient', (), {})()
    consultant = AIConsultant(profile, {}, ai_client=mock_global_client)

    client = consultant.get_ai_client()

    # Should return global client when no character-specific config
    if AI_AVAILABLE:
        assert client == mock_global_client, (
            "Should return global client when available"
        )
        print("  [OK] Returns global client when available")
    else:
        assert client is None, "Should return None when AI not available"
        print("  [OK] Returns None when AI not available")

    print("[PASS] AI Consultant - Get AI Client (Global)")


def test_build_character_system_prompt_basic():
    """Test building basic character system prompt."""
    print("\n[TEST] AI Consultant - Build System Prompt Basic")

    identity = CharacterIdentity(
        name="BraveKnight",
        character_class=DnDClass.FIGHTER,
        level=5
    )
    profile = CharacterProfile(identity=identity)
    consultant = AIConsultant(profile, {})

    prompt = consultant.build_character_system_prompt()

    assert "BraveKnight" in prompt, "Should include character name"
    assert "Fighter" in prompt, "Should include class"
    assert "level 5" in prompt or "Level 5" in prompt, "Should include level"
    assert isinstance(prompt, str), "Should return string"
    assert len(prompt) > 0, "Prompt should not be empty"
    print("  [OK] Basic system prompt generated correctly")

    print("[PASS] AI Consultant - Build System Prompt Basic")


def test_build_character_system_prompt_with_background():
    """Test system prompt with character background."""
    print("\n[TEST] AI Consultant - Build System Prompt with Background")

    identity = CharacterIdentity(
        name="MysteriousRogue",
        character_class=DnDClass.ROGUE,
        level=7
    )
    profile = CharacterProfile(identity=identity)
    profile.personality.background_story = (
        "Former thief turned adventurer seeking redemption"
    )
    profile.personality.personality_summary = "Cautious but loyal"

    consultant = AIConsultant(profile, {})
    prompt = consultant.build_character_system_prompt()

    assert "MysteriousRogue" in prompt, "Should include name"
    assert "Rogue" in prompt, "Should include class"
    assert "thief" in prompt or "adventurer" in prompt, (
        "Should include background"
    )
    assert "Cautious" in prompt or "loyal" in prompt, (
        "Should include personality"
    )
    print("  [OK] System prompt includes background and personality")

    print("[PASS] AI Consultant - Build System Prompt with Background")


def test_build_character_system_prompt_with_motivations():
    """Test system prompt with motivations and goals."""
    print("\n[TEST] AI Consultant - Build System Prompt with Motivations")

    identity = CharacterIdentity(
        name="NobleCleric",
        character_class=DnDClass.CLERIC,
        level=8
    )
    profile = CharacterProfile(identity=identity)
    profile.personality.motivations = ["Protect the innocent", "Serve my deity"]
    profile.personality.goals = ["Establish a temple", "Become a saint"]
    profile.personality.fears_weaknesses = ["Fear of failure"]

    consultant = AIConsultant(profile, {})
    prompt = consultant.build_character_system_prompt()

    assert "Protect the innocent" in prompt, "Should include motivations"
    assert "Establish a temple" in prompt, "Should include goals"
    assert "Fear of failure" in prompt or "failure" in prompt, (
        "Should include fears"
    )
    print("  [OK] System prompt includes motivations, goals, and fears")

    print("[PASS] AI Consultant - Build System Prompt with Motivations")


def test_build_character_system_prompt_with_class_knowledge():
    """Test system prompt with class knowledge."""
    print("\n[TEST] AI Consultant - Build System Prompt with Class Knowledge")

    identity = CharacterIdentity(
        name="WiseMage",
        character_class=DnDClass.WIZARD,
        level=10
    )
    profile = CharacterProfile(identity=identity)

    class_knowledge = {
        "decision_style": "analyze carefully before acting",
        "key_features": ["Spellcasting", "Arcane Recovery"]
    }

    consultant = AIConsultant(profile, class_knowledge)
    prompt = consultant.build_character_system_prompt()

    assert "analyze carefully" in prompt.lower(), (
        "Should include decision style"
    )
    assert "Wizard" in prompt, "Should mention class"
    print("  [OK] System prompt includes class knowledge")

    print("[PASS] AI Consultant - Build System Prompt with Class Knowledge")


def test_suggest_reaction_ai_requires_base():
    """Test that AI reaction suggestion requires base suggestion."""
    print("\n[TEST] AI Consultant - Reaction Requires Base Suggestion")

    identity = CharacterIdentity(
        name="TestChar",
        character_class=DnDClass.FIGHTER,
        level=5
    )
    profile = CharacterProfile(identity=identity)
    consultant = AIConsultant(profile, {})

    # Should raise ValueError when base_suggestion is None
    try:
        consultant.suggest_reaction_ai("danger approaches", base_suggestion=None)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "base_suggestion is required" in str(e), (
            "Error message should mention base_suggestion"
        )
        print("  [OK] Correctly requires base suggestion")

    print("[PASS] AI Consultant - Reaction Requires Base Suggestion")


def test_suggest_reaction_ai_without_ai():
    """Test AI reaction fallback when AI not available."""
    print("\n[TEST] AI Consultant - Reaction Fallback (No AI)")

    identity = CharacterIdentity(
        name="BraveFighter",
        character_class=DnDClass.FIGHTER,
        level=5
    )
    profile = CharacterProfile(identity=identity)
    consultant = AIConsultant(profile, {})

    base_suggestion = {
        "reaction": "Charge forward",
        "reasoning": "Fighters are brave"
    }

    result = consultant.suggest_reaction_ai(
        "Enemy approaches",
        base_suggestion=base_suggestion
    )

    # Should return base suggestion with ai_enhanced=False when no AI
    assert "ai_enhanced" in result, "Should have ai_enhanced field"
    assert isinstance(result, dict), "Should return dictionary"
    assert "reaction" in result, "Should preserve base suggestion"
    print("  [OK] Falls back gracefully without AI")

    print("[PASS] AI Consultant - Reaction Fallback (No AI)")


def test_suggest_dc_for_action_ai_requires_base():
    """Test that AI DC suggestion requires base suggestion."""
    print("\n[TEST] AI Consultant - DC Requires Base Suggestion")

    identity = CharacterIdentity(
        name="TestChar",
        character_class=DnDClass.ROGUE,
        level=5
    )
    profile = CharacterProfile(identity=identity)
    consultant = AIConsultant(profile, {})

    # Should raise ValueError when base_suggestion is None
    try:
        consultant.suggest_dc_for_action_ai(
            "pick a lock",
            base_suggestion=None
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "base_suggestion is required" in str(e), (
            "Error message should mention base_suggestion"
        )
        print("  [OK] Correctly requires base suggestion")

    print("[PASS] AI Consultant - DC Requires Base Suggestion")


def test_suggest_dc_for_action_ai_without_ai():
    """Test AI DC fallback when AI not available."""
    print("\n[TEST] AI Consultant - DC Fallback (No AI)")

    identity = CharacterIdentity(
        name="SneakyRogue",
        character_class=DnDClass.ROGUE,
        level=5
    )
    profile = CharacterProfile(identity=identity)
    consultant = AIConsultant(profile, {})

    base_suggestion = {
        "suggested_dc": 15,
        "reasoning": "Medium difficulty for rogue"
    }

    result = consultant.suggest_dc_for_action_ai(
        "sneak past guards",
        base_suggestion=base_suggestion
    )

    # Should return base suggestion with ai_enhanced=False when no AI
    assert "ai_enhanced" in result, "Should have ai_enhanced field"
    assert isinstance(result, dict), "Should return dictionary"
    assert "suggested_dc" in result, "Should preserve base suggestion"
    print("  [OK] Falls back gracefully without AI")

    print("[PASS] AI Consultant - DC Fallback (No AI)")


def test_ai_consultant_error_handling():
    """Test AI consultant handles errors gracefully."""
    print("\n[TEST] AI Consultant - Error Handling")

    identity = CharacterIdentity(
        name="TestChar",
        character_class=DnDClass.WIZARD,
        level=5
    )
    profile = CharacterProfile(identity=identity)

    # Create a mock client that will fail
    mock_client = type('FailingClient', (), {
        'chat_completion': lambda self, messages: (_ for _ in ()).throw(
            ConnectionError("Mock connection error")
        ),
        'create_system_message': lambda self, content: {
            "role": "system", "content": content
        },
        'create_user_message': lambda self, content: {
            "role": "user", "content": content
        }
    })()

    consultant = AIConsultant(profile, {}, ai_client=mock_client)

    base_suggestion = {"reaction": "Test"}

    result = consultant.suggest_reaction_ai(
        "test situation",
        base_suggestion=base_suggestion
    )

    # Should handle error gracefully
    assert "ai_enhanced" in result, "Should have ai_enhanced field"
    assert result["ai_enhanced"] is False, (
        "Should mark as not AI enhanced after error"
    )
    if "ai_error" in result:
        assert isinstance(result["ai_error"], str), (
            "AI error should be a string"
        )
        print("  [OK] Error captured in ai_error field")
    else:
        print("  [OK] Error handled gracefully")

    print("[PASS] AI Consultant - Error Handling")


def run_all_tests():
    """Run all AI consultant tests."""
    print("=" * 70)
    print("AI CONSULTANT TESTS")
    print("=" * 70)

    if not AI_AVAILABLE:
        print("\nNOTE: AI integration is not available")
        print("Tests will verify graceful fallback behavior\n")

    test_ai_consultant_initialization()
    test_ai_consultant_initialization_with_client()
    test_get_ai_client_no_ai()
    test_get_ai_client_with_global()
    test_build_character_system_prompt_basic()
    test_build_character_system_prompt_with_background()
    test_build_character_system_prompt_with_motivations()
    test_build_character_system_prompt_with_class_knowledge()
    test_suggest_reaction_ai_requires_base()
    test_suggest_reaction_ai_without_ai()
    test_suggest_dc_for_action_ai_requires_base()
    test_suggest_dc_for_action_ai_without_ai()
    test_ai_consultant_error_handling()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL AI CONSULTANT TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
