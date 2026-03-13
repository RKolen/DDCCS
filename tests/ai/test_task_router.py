"""
Test Task Router

Tests for the TaskRouter, ModelRegistry, and get_client_for_task integration.

What we test:
- TaskRouter profile resolution per task type
- TaskRouter character override handling
- TaskRouter fallback to "default" for unknown profiles
- ModelRegistry initialize, switch_profile, get_active_profile
- ModelRegistry.get_router() returns a correctly wired TaskRouter
- get_client_for_task returns AIClient with correct kwargs
- ModelRegistryConfig.get_profile and list_profile_names

Why we test this:
- Ensures task routing produces the expected model profiles
- Validates session switching is in-memory only
- Confirms graceful fallback when registry is uninitialized
"""

from typing import Any

from tests.test_helpers import safe_from_import

(ModelProfile, ModelRegistryConfig) = safe_from_import(
    "src.config.config_types", "ModelProfile", "ModelRegistryConfig"
)
(TaskRouter, ModelRegistry, TASK_PROFILE_MAP) = safe_from_import(
    "src.ai.task_router", "TaskRouter", "ModelRegistry", "TASK_PROFILE_MAP"
)
(get_client_for_task, AIClient) = safe_from_import(
    "src.ai.ai_client", "get_client_for_task", "AIClient"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_registry() -> Any:
    """Build a minimal ModelRegistryConfig for use in tests."""
    profiles = {
        "default": ModelProfile(
            name="default",
            provider="openai",
            base_url="http://test-host/v1",
            model="test-default-model",
            temperature=0.7,
            max_tokens=1000,
            description="Default test profile",
        ),
        "fast": ModelProfile(
            name="fast",
            provider="openai",
            base_url="http://test-host/v1",
            model="test-fast-model",
            temperature=0.3,
            max_tokens=500,
            description="Fast test profile",
        ),
        "creative": ModelProfile(
            name="creative",
            provider="openai",
            base_url="http://test-host/v1",
            model="test-creative-model",
            temperature=0.9,
            max_tokens=2000,
            description="Creative test profile",
        ),
    }
    return ModelRegistryConfig(active_profile="default", profiles=profiles)


# ---------------------------------------------------------------------------
# ModelProfile tests
# ---------------------------------------------------------------------------

def test_model_profile_defaults():
    """ModelProfile has correct default field values."""
    print("\n[TEST] ModelProfile defaults")
    profile = ModelProfile()
    assert profile.name == "", "Default name should be empty"
    assert profile.provider == "openai", "Default provider should be openai"
    assert profile.base_url == "", "Default base_url should be empty"
    assert profile.model == "", "Default model should be empty"
    assert profile.temperature == 0.7, "Default temperature should be 0.7"
    assert profile.max_tokens == 1000, "Default max_tokens should be 1000"
    print("  [OK] All defaults correct")


# ---------------------------------------------------------------------------
# ModelRegistryConfig tests
# ---------------------------------------------------------------------------

def test_model_registry_config_get_profile_by_name():
    """ModelRegistryConfig.get_profile returns the correct profile."""
    print("\n[TEST] ModelRegistryConfig.get_profile by name")
    registry = _make_registry()
    profile = registry.get_profile("fast")
    assert profile is not None, "get_profile should return a profile for 'fast'"
    assert profile.model == "test-fast-model"
    print("  [OK] Correct profile returned")


def test_model_registry_config_get_profile_empty_name_returns_active():
    """ModelRegistryConfig.get_profile with empty name returns active profile."""
    print("\n[TEST] ModelRegistryConfig.get_profile empty -> active")
    registry = _make_registry()
    profile = registry.get_profile("")
    assert profile is not None, "Should return active profile for empty name"
    assert profile.model == "test-default-model", "Active (default) profile model mismatch"
    print("  [OK] Active profile returned for empty name")


def test_model_registry_config_get_active_profile():
    """ModelRegistryConfig.get_active_profile returns the active profile."""
    print("\n[TEST] ModelRegistryConfig.get_active_profile")
    registry = _make_registry()
    active = registry.get_active_profile()
    assert active is not None
    assert active.name == "default"
    print("  [OK] Correct active profile")


def test_model_registry_config_list_profile_names():
    """ModelRegistryConfig.list_profile_names returns sorted names."""
    print("\n[TEST] ModelRegistryConfig.list_profile_names")
    registry = _make_registry()
    names = registry.list_profile_names()
    assert names == ["creative", "default", "fast"], f"Unexpected names: {names}"
    print("  [OK] Sorted profile names returned")


def test_model_registry_config_missing_profile_returns_none():
    """ModelRegistryConfig.get_profile returns None for unknown names."""
    print("\n[TEST] ModelRegistryConfig missing profile -> None")
    registry = _make_registry()
    assert registry.get_profile("nonexistent") is None
    print("  [OK] None returned for missing profile")


# ---------------------------------------------------------------------------
# TaskRouter tests
# ---------------------------------------------------------------------------

def test_task_router_known_task_types():
    """TaskRouter.get_profile_name_for_task returns expected profile names."""
    print("\n[TEST] TaskRouter known task types")
    router = TaskRouter()
    for task, expected_profile in TASK_PROFILE_MAP.items():
        result = router.get_profile_name_for_task(task)
        assert result == expected_profile, (
            f"Task '{task}': expected '{expected_profile}', got '{result}'"
        )
    print(f"  [OK] All {len(TASK_PROFILE_MAP)} task types map correctly")


def test_task_router_unknown_task_falls_back_to_default():
    """TaskRouter falls back to 'default' for unknown task types."""
    print("\n[TEST] TaskRouter unknown task fallback")
    router = TaskRouter()
    assert router.get_profile_name_for_task("unknown_task_xyz") == "default"
    print("  [OK] Unknown task returns 'default'")


def test_task_router_get_profile_for_task_resolves_profile():
    """TaskRouter.get_profile_for_task resolves to the correct ModelProfile."""
    print("\n[TEST] TaskRouter.get_profile_for_task resolution")
    registry = _make_registry()
    router = TaskRouter(registry)
    profile = router.get_profile_for_task("story_analysis")
    assert profile is not None
    assert profile.model == "test-fast-model", "story_analysis should use 'fast'"
    print("  [OK] Correct profile resolved for story_analysis")


def test_task_router_character_override_takes_priority():
    """TaskRouter respects character-level profile override."""
    print("\n[TEST] TaskRouter character override")
    registry = _make_registry()
    router = TaskRouter(registry)
    profile = router.get_profile_for_task("story_analysis", character_override="creative")
    assert profile is not None
    assert profile.name == "creative"
    print("  [OK] Character override respected")


def test_task_router_missing_profile_falls_back_to_default():
    """TaskRouter falls back to 'default' when a mapped profile does not exist."""
    print("\n[TEST] TaskRouter missing profile fallback")
    registry = _make_registry()
    router = TaskRouter(registry)
    # 'embedding' profile is not in our test registry
    profile = router.get_profile_for_task("embedding")
    assert profile is not None
    assert profile.name == "default", "Should fall back to 'default'"
    print("  [OK] Falls back to 'default' for missing profile")


def test_task_router_no_registry_returns_none():
    """TaskRouter without a registry returns None for get_profile_for_task."""
    print("\n[TEST] TaskRouter no registry")
    router = TaskRouter(None)
    assert router.get_profile_for_task("story_generation") is None
    print("  [OK] None returned without registry")


def test_task_router_get_client_kwargs_contents():
    """TaskRouter.get_client_kwargs returns expected keys."""
    print("\n[TEST] TaskRouter.get_client_kwargs")
    registry = _make_registry()
    router = TaskRouter(registry)
    kwargs = router.get_client_kwargs("combat_narration")
    assert "model" in kwargs, "model should be in kwargs"
    assert "base_url" in kwargs, "base_url should be in kwargs"
    assert kwargs["model"] == "test-creative-model", "combat_narration uses creative profile"
    print("  [OK] Client kwargs contain correct values")


def test_task_router_get_client_kwargs_empty_without_registry():
    """TaskRouter.get_client_kwargs returns empty dict without a registry."""
    print("\n[TEST] TaskRouter.get_client_kwargs no registry")
    router = TaskRouter(None)
    assert not router.get_client_kwargs("story_generation")
    print("  [OK] Empty dict without registry")


# ---------------------------------------------------------------------------
# ModelRegistry (session-level) tests
# ---------------------------------------------------------------------------

def test_model_registry_initialize_and_get_active():
    """ModelRegistry.initialize sets the active profile correctly."""
    print("\n[TEST] ModelRegistry.initialize")
    ModelRegistry.reset()
    registry = _make_registry()
    ModelRegistry.initialize(registry)
    active = ModelRegistry.get_active_profile()
    assert active is not None
    assert active.name == "default"
    ModelRegistry.reset()
    print("  [OK] Active profile set after initialize")


def test_model_registry_switch_profile_valid():
    """ModelRegistry.switch_profile switches to a valid profile."""
    print("\n[TEST] ModelRegistry.switch_profile valid")
    ModelRegistry.reset()
    ModelRegistry.initialize(_make_registry())
    switched = ModelRegistry.switch_profile("fast")
    assert switched is True
    assert ModelRegistry.get_active_profile_name() == "fast"
    active = ModelRegistry.get_active_profile()
    assert active is not None
    assert active.model == "test-fast-model"
    ModelRegistry.reset()
    print("  [OK] Profile switched successfully")


def test_model_registry_switch_profile_invalid_returns_false():
    """ModelRegistry.switch_profile returns False for unknown profile names."""
    print("\n[TEST] ModelRegistry.switch_profile invalid")
    ModelRegistry.reset()
    ModelRegistry.initialize(_make_registry())
    switched = ModelRegistry.switch_profile("does_not_exist")
    assert switched is False
    assert ModelRegistry.get_active_profile_name() == "default"
    ModelRegistry.reset()
    print("  [OK] Returns False for unknown profile, active unchanged")


def test_model_registry_uninitialized_returns_none():
    """ModelRegistry.get_active_profile returns None before initialization."""
    print("\n[TEST] ModelRegistry uninitialized -> None")
    ModelRegistry.reset()
    assert ModelRegistry.get_active_profile() is None
    print("  [OK] None returned before initialization")


def test_model_registry_get_router_wired():
    """ModelRegistry.get_router returns a TaskRouter backed by the registry."""
    print("\n[TEST] ModelRegistry.get_router")
    ModelRegistry.reset()
    ModelRegistry.initialize(_make_registry())
    router = ModelRegistry.get_router()
    profile = router.get_profile_for_task("dc_evaluation")
    assert profile is not None
    assert profile.model == "test-fast-model", "dc_evaluation uses 'fast'"
    ModelRegistry.reset()
    print("  [OK] Router correctly wired to registry")


# ---------------------------------------------------------------------------
# get_client_for_task integration tests
# ---------------------------------------------------------------------------

def test_get_client_for_task_returns_ai_client():
    """get_client_for_task returns an AIClient instance."""
    print("\n[TEST] get_client_for_task returns AIClient")
    ModelRegistry.reset()
    ModelRegistry.initialize(_make_registry())
    client = get_client_for_task("story_generation")
    assert isinstance(client, AIClient), "Should return an AIClient instance"
    ModelRegistry.reset()
    print("  [OK] AIClient returned")


def test_get_client_for_task_applies_profile_model():
    """get_client_for_task applies the profile model to the returned client."""
    print("\n[TEST] get_client_for_task applies profile model")
    ModelRegistry.reset()
    ModelRegistry.initialize(_make_registry())
    client = get_client_for_task("story_generation")
    # creative profile maps to test-creative-model
    assert client.model == "test-creative-model", f"Unexpected model: {client.model}"
    ModelRegistry.reset()
    print("  [OK] Correct model applied from profile")


def test_get_client_for_task_without_registry_returns_default():
    """get_client_for_task without registry returns a usable AIClient."""
    print("\n[TEST] get_client_for_task without registry")
    ModelRegistry.reset()
    client = get_client_for_task("combat_narration")
    assert isinstance(client, AIClient)
    print("  [OK] Returns default client without registry")


def test_get_client_for_task_character_override():
    """get_client_for_task respects per-character profile override."""
    print("\n[TEST] get_client_for_task character override")
    ModelRegistry.reset()
    ModelRegistry.initialize(_make_registry())
    # Force character to use 'fast' regardless of task
    client = get_client_for_task("story_generation", character_override="fast")
    assert client.model == "test-fast-model", f"Unexpected model: {client.model}"
    ModelRegistry.reset()
    print("  [OK] Character override respected by get_client_for_task")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_all_tests() -> None:
    """Run all task router tests."""
    test_model_profile_defaults()
    test_model_registry_config_get_profile_by_name()
    test_model_registry_config_get_profile_empty_name_returns_active()
    test_model_registry_config_get_active_profile()
    test_model_registry_config_list_profile_names()
    test_model_registry_config_missing_profile_returns_none()
    test_task_router_known_task_types()
    test_task_router_unknown_task_falls_back_to_default()
    test_task_router_get_profile_for_task_resolves_profile()
    test_task_router_character_override_takes_priority()
    test_task_router_missing_profile_falls_back_to_default()
    test_task_router_no_registry_returns_none()
    test_task_router_get_client_kwargs_contents()
    test_task_router_get_client_kwargs_empty_without_registry()
    test_model_registry_initialize_and_get_active()
    test_model_registry_switch_profile_valid()
    test_model_registry_switch_profile_invalid_returns_false()
    test_model_registry_uninitialized_returns_none()
    test_model_registry_get_router_wired()
    test_get_client_for_task_returns_ai_client()
    test_get_client_for_task_applies_profile_model()
    test_get_client_for_task_without_registry_returns_default()
    test_get_client_for_task_character_override()

    print("\n" + "=" * 70)
    print("[SUCCESS] ALL TASK ROUTER TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
