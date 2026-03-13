"""
Task Router - routes AI tasks to the appropriate model profile.

Provides session-level model switching and per-task profile resolution.
The active profile switch lives only in memory and is never written back
to config files.
"""

from typing import Any, Dict, Optional

from src.config.config_types import ModelProfile, ModelRegistryConfig


# Maps task types to their preferred model profile name.
TASK_PROFILE_MAP: Dict[str, str] = {
    "story_generation": "creative",
    "story_analysis": "fast",
    "combat_narration": "creative",
    "dc_evaluation": "fast",
    "character_consultation": "default",
    "npc_dialogue": "default",
    "spotlight_analysis": "fast",
    "embedding": "embedding",
}


class TaskRouter:
    """Returns the correct ModelProfile for a given task type.

    Resolves profiles using the following priority:
    1. Explicit character-level override (model_profile field in character JSON)
    2. Task-type mapping from TASK_PROFILE_MAP
    3. "default" profile fallback
    """

    def __init__(self, registry: Optional[ModelRegistryConfig] = None) -> None:
        """Initialize with an optional ModelRegistryConfig.

        Args:
            registry: The registry to resolve profiles from.
        """
        self._registry = registry

    def get_profile_name_for_task(self, task_type: str) -> str:
        """Return the profile name to use for a task type.

        Args:
            task_type: One of the keys in TASK_PROFILE_MAP.

        Returns:
            Profile name string, defaulting to "default" for unknown tasks.
        """
        return TASK_PROFILE_MAP.get(task_type, "default")

    def get_profile_for_task(
        self,
        task_type: str,
        character_override: Optional[str] = None,
    ) -> Optional[ModelProfile]:
        """Return the ModelProfile for a task, respecting character overrides.

        Args:
            task_type: Task type key used to look up a profile.
            character_override: Optional profile name from per-character config.

        Returns:
            Resolved ModelProfile, or None if the registry is not set or the
            profile name is not found.
        """
        if self._registry is None:
            return None
        profile_name = character_override or self.get_profile_name_for_task(task_type)
        profile = self._registry.get_profile(profile_name)
        # Fall back to "default" if the mapped profile does not exist
        if profile is None and profile_name != "default":
            profile = self._registry.get_profile("default")
        return profile

    def get_client_kwargs(
        self,
        task_type: str,
        character_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return AIClient init kwargs for a given task type.

        Only non-empty/non-default values are included so that the caller's
        own defaults remain intact when a profile field is not configured.

        Args:
            task_type: Task type key.
            character_override: Optional per-character profile name.

        Returns:
            Dict suitable for passing as **kwargs to AIClient().
        """
        profile = self.get_profile_for_task(task_type, character_override)
        if profile is None:
            return {}
        kwargs: Dict[str, Any] = {}
        if profile.model:
            kwargs["model"] = profile.model
        if profile.base_url:
            kwargs["base_url"] = profile.base_url
        kwargs["default_temperature"] = profile.temperature
        kwargs["default_max_tokens"] = profile.max_tokens
        return kwargs


class ModelRegistry:
    """Session-level model registry.

    Holds the active profile name in memory for the duration of the process.
    Switching via switch_profile() is never persisted to disk.
    """

    _active_profile: str = "default"
    _config: Optional[ModelRegistryConfig] = None

    @classmethod
    def initialize(cls, config: ModelRegistryConfig) -> None:
        """Load a ModelRegistryConfig and set the initial active profile.

        Args:
            config: Registry config loaded from disk.
        """
        cls._config = config
        cls._active_profile = config.active_profile

    @classmethod
    def switch_profile(cls, profile_name: str) -> bool:
        """Switch the active profile for this session.

        Args:
            profile_name: Name of the profile to activate.

        Returns:
            True if the profile exists and was switched, False otherwise.
        """
        if cls._config and profile_name in cls._config.profiles:
            cls._active_profile = profile_name
            return True
        return False

    @classmethod
    def get_active_profile(cls) -> Optional[ModelProfile]:
        """Return the currently active ModelProfile.

        Returns:
            ModelProfile or None if registry has not been initialized.
        """
        if cls._config is None:
            return None
        return cls._config.profiles.get(cls._active_profile)

    @classmethod
    def get_active_profile_name(cls) -> str:
        """Return the name of the currently active profile.

        Returns:
            Active profile name string.
        """
        return cls._active_profile

    @classmethod
    def get_router(cls) -> TaskRouter:
        """Return a TaskRouter backed by the current registry config.

        Returns:
            TaskRouter instance.
        """
        return TaskRouter(cls._config)

    @classmethod
    def reset(cls) -> None:
        """Reset the registry (used in tests).

        Restores the class to its uninitialized state.
        """
        cls._active_profile = "default"
        cls._config = None

    @classmethod
    def list_profiles(cls) -> Dict[str, ModelProfile]:
        """Return all registered profiles.

        Returns:
            Dict mapping profile name to ModelProfile, or empty dict if the
            registry has not been initialized.
        """
        if cls._config is None:
            return {}
        return dict(cls._config.profiles)
