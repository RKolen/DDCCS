"""
Test AI Client Interface

Tests the AIClient class for basic initialization, message creation,
and configuration management. Does NOT test actual API calls (those require
a live connection and are tested separately).

What we test:
- Client initialization with various configurations
- Environment variable loading
- Message helper methods
- CharacterAIConfig dataclass operations
- Configuration serialization/deserialization

Why we test this:
- Ensures AI client can be configured correctly
- Validates environment variable fallbacks work
- Confirms message creation helpers produce correct format
- Verifies character-specific AI config can be saved/loaded
"""

import os
import sys
from pathlib import Path
import test_helpers
# Add tests directory to path for test_helpers
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import and configure test environment
project_root = test_helpers.setup_test_environment()

# Import AI client components
try:
    from src.ai.ai_client import (
        AIClient,
        CharacterAIConfig,
        AIRequestParams,
        load_ai_config_from_env
    )
except ImportError as e:
    print(f"Error importing AI client: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


def test_ai_client_initialization():
    """Test that AIClient can be initialized with various configurations."""
    print("\n[TEST] AI Client Initialization")

    # Test 1: Default initialization (uses env vars)
    client1 = AIClient()
    assert client1.api_key is not None, "Default client should have API key from env"
    assert client1.model is not None, "Default client should have model"
    print("  [OK] Default initialization works")

    # Test 2: Custom initialization (using generic test values)
    client2 = AIClient(
        api_key="generic_test_key",
        base_url="https://api.example.com/v1",
        model="test-model"
    )
    assert client2.api_key == "generic_test_key", "Custom API key not set"
    assert client2.base_url == "https://api.example.com/v1", "Custom base URL not set"
    assert client2.model == "test-model", "Custom model not set"
    print("  [OK] Custom initialization works")

    # Test 3: Partial custom (mix of custom and env vars)
    client3 = AIClient(model="custom-model")
    assert client3.model == "custom-model", "Custom model override not set"
    assert client3.api_key is not None, "Should still use env var for API key"
    print("  [OK] Partial custom initialization works")

    # Test 4: Config parameters
    client4 = AIClient(
        default_temperature=0.9,
        default_max_tokens=2000
    )
    assert client4.default_temperature == 0.9, "Temperature config not set"
    assert client4.default_max_tokens == 2000, "Max tokens config not set"
    print("  [OK] Config parameters work")

    print("[PASS] AI Client Initialization")


def test_message_helpers():
    """Test message creation helper methods."""
    print("\n[TEST] Message Helper Methods")

    client = AIClient()

    # Test system message
    sys_msg = client.create_system_message("You are a helpful assistant")
    assert sys_msg["role"] == "system", "System message role incorrect"
    assert "helpful" in sys_msg["content"], "System message content incorrect"
    print("  [OK] System message creation works")

    # Test user message
    user_msg = client.create_user_message("Hello, AI!")
    assert user_msg["role"] == "user", "User message role incorrect"
    assert user_msg["content"] == "Hello, AI!", "User message content incorrect"
    print("  [OK] User message creation works")

    # Test assistant message
    asst_msg = client.create_assistant_message("Hello, human!")
    assert asst_msg["role"] == "assistant", "Assistant message role incorrect"
    assert asst_msg["content"] == "Hello, human!", "Assistant message content incorrect"
    print("  [OK] Assistant message creation works")

    print("[PASS] Message Helper Methods")


def test_load_ai_config_from_env():
    """Test loading AI configuration from environment variables."""
    print("\n[TEST] Load AI Config from Environment")

    config = load_ai_config_from_env()

    # Should always return a dict with required keys
    assert "api_key" in config, "Config missing api_key"
    assert "base_url" in config, "Config missing base_url"
    assert "model" in config, "Config missing model"
    assert "temperature" in config, "Config missing temperature"
    assert "max_tokens" in config, "Config missing max_tokens"
    print("  [OK] Config dict has all required keys")

    # Check types
    assert isinstance(config["temperature"], float), "Temperature not float"
    assert isinstance(config["max_tokens"], int), "Max tokens not int"
    print("  [OK] Config values have correct types")

    # Check defaults
    if not os.getenv("OPENAI_MODEL"):
        assert config["model"] == "gpt-3.5-turbo", "Default model incorrect"
        print("  [OK] Default model value correct")

    print("[PASS] Load AI Config from Environment")


def test_ai_request_params():
    """Test AIRequestParams dataclass."""
    print("\n[TEST] AIRequestParams Dataclass")

    # Test default values
    params1 = AIRequestParams()
    assert params1.temperature == 0.7, "Default temperature incorrect"
    assert params1.max_tokens == 1000, "Default max_tokens incorrect"
    assert params1.custom_parameters == {}, "Default custom_parameters not empty dict"
    print("  [OK] Default values work")

    # Test custom values
    params2 = AIRequestParams(
        temperature=0.5,
        max_tokens=500,
        custom_parameters={"top_p": 0.9}
    )
    assert params2.temperature == 0.5, "Custom temperature not set"
    assert params2.max_tokens == 500, "Custom max_tokens not set"
    assert params2.custom_parameters["top_p"] == 0.9, "Custom parameter not set"
    print("  [OK] Custom values work")

    print("[PASS] AIRequestParams Dataclass")


def test_character_ai_config():
    """Test CharacterAIConfig dataclass operations."""
    print("\n[TEST] CharacterAIConfig Dataclass")

    # Test default values
    config1 = CharacterAIConfig()
    assert config1.enabled is False, "Default enabled should be False"
    assert config1.model is None, "Default model should be None"
    assert config1.base_url is None, "Default base_url should be None"
    assert config1.api_key is None, "Default api_key should be None"
    assert config1.system_prompt is None, "Default system_prompt should be None"
    print("  [OK] Default values work")

    # Test custom values
    config2 = CharacterAIConfig(
        enabled=True,
        model="test-model",
        base_url="https://api.example.com/v1",
        api_key="test_key",
        system_prompt="You are a brave fighter",
        request_params=AIRequestParams(temperature=0.8, max_tokens=1500)
    )
    assert config2.enabled is True, "Enabled not set"
    assert config2.model == "test-model", "Model not set"
    assert config2.request_params.temperature == 0.8, "Temperature not set"
    print("  [OK] Custom values work")

    print("[PASS] CharacterAIConfig Dataclass")


def test_character_ai_config_serialization():
    """Test CharacterAIConfig to_dict and from_dict methods."""
    print("\n[TEST] CharacterAIConfig Serialization")

    # Create config
    original = CharacterAIConfig(
        enabled=True,
        model="test-model",
        base_url="https://api.example.com/v1",
        system_prompt="Test prompt",
        request_params=AIRequestParams(
            temperature=0.8,
            max_tokens=1500,
            custom_parameters={"top_p": 0.95}
        )
    )

    # Convert to dict
    config_dict = original.to_dict()
    assert isinstance(config_dict, dict), "to_dict() should return dict"
    assert config_dict["enabled"] is True, "Dict missing enabled"
    assert config_dict["model"] == "test-model", "Dict missing model"
    assert config_dict["temperature"] == 0.8, "Dict missing temperature"
    assert config_dict["max_tokens"] == 1500, "Dict missing max_tokens"
    assert config_dict["system_prompt"] == "Test prompt", "Dict missing system_prompt"
    assert config_dict["custom_parameters"]["top_p"] == 0.95, "Dict missing custom params"
    print("  [OK] to_dict() works correctly")

    # Convert back from dict
    restored = CharacterAIConfig.from_dict(config_dict)
    assert restored.enabled == original.enabled, "from_dict() enabled mismatch"
    assert restored.model == original.model, "from_dict() model mismatch"
    assert restored.base_url == original.base_url, "from_dict() base_url mismatch"
    assert restored.system_prompt == original.system_prompt, "from_dict() prompt mismatch"
    assert (
        restored.request_params.temperature == original.request_params.temperature
    ), "from_dict() temperature mismatch"
    assert (
        restored.request_params.max_tokens == original.request_params.max_tokens
    ), "from_dict() max_tokens mismatch"
    assert (
        restored.request_params.custom_parameters["top_p"]
        == original.request_params.custom_parameters["top_p"]
    ), "from_dict() custom params mismatch"
    print("  [OK] from_dict() works correctly")

    # Test roundtrip
    roundtrip_dict = restored.to_dict()
    assert roundtrip_dict == config_dict, "Roundtrip serialization not identical"
    print("  [OK] Roundtrip serialization works")

    print("[PASS] CharacterAIConfig Serialization")


def test_character_ai_config_create_client():
    """Test CharacterAIConfig.create_client() method."""
    print("\n[TEST] CharacterAIConfig create_client()")

    # Test 1: Disabled config with default client
    config1 = CharacterAIConfig(enabled=False)
    default_client = AIClient()
    client1 = config1.create_client(default_client=default_client)
    assert client1 is default_client, "Should return default client when disabled"
    print("  [OK] Returns default client when disabled")

    # Test 2: Enabled config with no custom settings (uses env defaults)
    config2 = CharacterAIConfig(enabled=True)
    client2 = config2.create_client()
    assert client2 is not None, "Should create client from env vars"
    assert client2.model is not None, "Client should have model from env"
    print("  [OK] Creates client from env vars when enabled with no custom settings")

    # Test 3: Enabled config with custom model only
    config3 = CharacterAIConfig(
        enabled=True,
        model="custom-model",
        request_params=AIRequestParams(temperature=0.9, max_tokens=2000)
    )
    client3 = config3.create_client()
    assert client3.model == "custom-model", "Custom model not used"
    assert client3.default_temperature == 0.9, "Custom temperature not used"
    assert client3.default_max_tokens == 2000, "Custom max_tokens not used"
    print("  [OK] Uses custom settings when provided")

    # Test 4: Disabled config without default client (should raise error)
    config4 = CharacterAIConfig(enabled=False)
    try:
        config4.create_client()
        assert False, "Should raise error when disabled and no default client"
    except RuntimeError as e:
        assert "not enabled" in str(e).lower(), "Error message should mention 'not enabled'"
        print("  [OK] Raises error when disabled and no default client")

    print("[PASS] CharacterAIConfig create_client()")


def run_all_tests():
    """Run all AI client tests."""
    print("=" * 70)
    print("AI CLIENT TESTS")
    print("=" * 70)

    test_ai_client_initialization()
    test_message_helpers()
    test_load_ai_config_from_env()
    test_ai_request_params()
    test_character_ai_config()
    test_character_ai_config_serialization()
    test_character_ai_config_create_client()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL AI CLIENT TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
