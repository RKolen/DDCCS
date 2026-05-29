"""AI Client Module - Flexible OpenAI-compatible client for LLM integration."""

import ast
import functools
import json
import os
import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

try:
    from src.config.config_loader import load_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

from src.ai.task_router import ModelRegistry


class AIClient:
    """Flexible AI client for any OpenAI-compatible API.

    Configuration is resolved via centralized config, then env vars.
    All provider details (base_url, model, api_key) must be set via
    config or environment — no hardcoded defaults.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        **config,
    ):
        """
        Initialize AI client with configuration.

        Args:
            api_key: API key for the provider.
            base_url: Base URL for the API endpoint.
            model: Model name to use.
            **config: Additional config keys:
                - default_temperature (float)
                - default_max_tokens (int)
                - embedding_model (str)
                - ai_config: Optional AIConfig object from src.config (takes precedence)
        """
        ai_config = config.pop("ai_config", None)
        if ai_config is not None:
            self.api_key = api_key or ai_config.api_key
            self.base_url = base_url or ai_config.base_url
            self.model = model or ai_config.model
            self.default_temperature = config.get("default_temperature", ai_config.temperature)
            self.default_max_tokens = config.get("default_max_tokens", ai_config.max_tokens)
        else:
            self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
            self.base_url = base_url or os.getenv("OPENAI_BASE_URL", None)
            self.model = model or os.getenv("OPENAI_MODEL", "")
            self.default_temperature = config.get("default_temperature", 0.7)
            self.default_max_tokens = config.get("default_max_tokens", 1000)

        self.embedding_model: str = str(
            config.get("embedding_model") or os.getenv("OPENAI_EMBEDDING_MODEL", "")
        )

        self.client = None
        if OPENAI_AVAILABLE:
            client_kwargs = {}
            if self.api_key and isinstance(self.api_key, str) and self.api_key.strip():
                client_kwargs["api_key"] = self.api_key
            if self.base_url and isinstance(self.base_url, str) and self.base_url.strip():
                client_kwargs["base_url"] = self.base_url

            allowed_keys = {"api_key", "base_url"}
            filtered_kwargs = {
                k: v for k, v in client_kwargs.items() if k in allowed_keys and v
            }

            self.client = OpenAI(**filtered_kwargs)

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """
        Get a chat completion from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            model: Override default model for this request.
            temperature: Override default temperature.
            max_tokens: Override default max_tokens.
            **kwargs: Additional parameters passed to the API.

        Returns:
            The assistant's response content as a string.
        """
        if self.client is None:
            raise RuntimeError(
                "AI client not available. Install openai package: pip install openai"
            )
        try:
            response = self.client.chat.completions.create(
                model=model or self.model,
                messages=messages,
                temperature=(
                    temperature if temperature is not None else self.default_temperature
                ),
                max_tokens=max_tokens if max_tokens is not None else self.default_max_tokens,
                **kwargs,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            error_type = type(e).__name__
            if error_type == "AuthenticationError":
                raise RuntimeError("AI completion failed: Invalid API key") from e
            if error_type == "RateLimitError":
                raise RuntimeError("AI completion failed: Rate limit exceeded") from e
            if error_type == "APIConnectionError":
                raise RuntimeError(
                    f"AI completion failed: Cannot reach {self.base_url or 'provider'}"
                ) from e
            if error_type == "APITimeoutError":
                raise RuntimeError("AI completion failed: Request timed out") from e
            if error_type == "BadRequestError":
                raise RuntimeError(f"AI completion failed: Bad request: {e}") from e
            raise RuntimeError(f"AI completion failed: {e}") from e

    def embed(self, text: str, model: str = "") -> List[float]:
        """Generate an embedding vector for text.

        Args:
            text: Text to embed.
            model: Embedding model name. Falls back to OPENAI_EMBEDDING_MODEL env var.

        Returns:
            List of floats representing the embedding, or [] on failure.
        """
        effective_model = model or self.embedding_model
        if not effective_model or self.client is None:
            return []
        try:
            response = self.client.embeddings.create(
                input=text,
                model=effective_model,
            )
            return list(response.data[0].embedding)
        except Exception as exc:
            raise RuntimeError(f"Embedding failed: {exc}") from exc

    def create_system_message(self, system_prompt: str) -> Dict[str, str]:
        """Create a system message dict."""
        return {"role": "system", "content": system_prompt}

    def create_user_message(self, content: str) -> Dict[str, str]:
        """Create a user message dict."""
        return {"role": "user", "content": content}

    def create_assistant_message(self, content: str) -> Dict[str, str]:
        """Create an assistant message dict."""
        return {"role": "assistant", "content": content}


@dataclass
class AIRequestParams:
    """Parameters for AI requests."""

    temperature: float = 0.7
    max_tokens: int = 1000
    custom_parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CharacterAIConfig:
    """
    AI configuration specific to a character.
    Allows each character to have unique AI behavior, model selection, etc.
    """

    enabled: bool = False
    model: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    system_prompt: Optional[str] = None
    request_params: AIRequestParams = field(default_factory=AIRequestParams)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization (flat format for compatibility)."""
        return {
            "enabled": self.enabled,
            "model": self.model,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "temperature": self.request_params.temperature,
            "max_tokens": self.request_params.max_tokens,
            "system_prompt": self.system_prompt,
            "custom_parameters": self.request_params.custom_parameters,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CharacterAIConfig":
        """Create from dictionary (accepts flat format for compatibility)."""
        request_params = AIRequestParams(
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 1000),
            custom_parameters=data.get("custom_parameters", {}),
        )
        return cls(
            enabled=data.get("enabled", False),
            model=data.get("model"),
            base_url=data.get("base_url"),
            api_key=data.get("api_key"),
            system_prompt=data.get("system_prompt"),
            request_params=request_params,
        )

    def create_client(self, default_client: Optional[AIClient] = None) -> AIClient:
        """
        Create an AI client for this character.

        Uses centralized .env configuration by default. Character-specific overrides
        (model, base_url, api_key) are only used if explicitly set in character JSON.

        Args:
            default_client: Default client to use if character doesn't have custom config.

        Returns:
            AIClient configured for this character with .env defaults + character overrides.
        """
        if not self.enabled:
            if default_client:
                return default_client
            raise RuntimeError(
                "AI is not enabled for this character and no default client provided"
            )

        if not any([self.model, self.base_url, self.api_key]):
            return default_client if default_client else AIClient()

        env_config = load_ai_config_from_env()

        return AIClient(
            api_key=self.api_key or env_config["api_key"],
            base_url=self.base_url or env_config["base_url"],
            model=self.model or env_config["model"],
            default_temperature=self.request_params.temperature,
            default_max_tokens=self.request_params.max_tokens,
        )


def load_ai_config_from_env() -> Dict[str, Any]:
    """Load AI configuration from centralized config, then env var fallback.

    Returns:
        Dictionary with configuration values.
    """
    if CONFIG_AVAILABLE:
        try:
            config = load_config()
            return config.ai.get_client_config()
        except (OSError, ImportError, AttributeError):
            pass

    return {
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "base_url": os.getenv("OPENAI_BASE_URL", ""),
        "model": os.getenv("OPENAI_MODEL", ""),
        "temperature": float(os.getenv("AI_TEMPERATURE", "0.7")),
        "max_tokens": int(os.getenv("AI_MAX_TOKENS", "1000")),
    }


@functools.lru_cache(maxsize=1)
def _get_default_client() -> AIClient:
    """Get or create the default AI client (lazy initialization)."""
    return AIClient()


def get_client_for_task(
    task_type: str,
    character_override: Optional[str] = None,
) -> AIClient:
    """Return an AIClient configured for the given task type.

    Uses the session-level ModelRegistry to resolve the appropriate model
    profile. Falls back to the default client when no profile matches.

    Args:
        task_type: Task type key (e.g. "story_generation", "combat_narration").
        character_override: Optional per-character model profile name.

    Returns:
        AIClient instance configured for the task.
    """
    kwargs = ModelRegistry.get_router().get_client_kwargs(task_type, character_override)
    if kwargs:
        return AIClient(**kwargs)
    return _get_default_client()


def call_ai_for_behavior_block(prompt: str) -> dict:
    """
    Calls the LLM to generate a CharacterBehavior block from a prompt.
    Returns a dict with keys: preferred_strategies, typical_reactions,
    speech_patterns, decision_making_style.
    """
    client = get_client_for_task("npc_dialogue")
    messages: List[Dict[str, str]] = [
        client.create_system_message(
            "You are a D&D character consultant AI. "
            "Respond ONLY with a JSON object for the CharacterBehavior dataclass."
        ),
        client.create_user_message(prompt),
    ]
    response = client.chat_completion(messages)
    match = re.search(r"```json\n(.*?)```", response, re.DOTALL)
    json_str = match.group(1) if match else response

    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        try:
            return ast.literal_eval(json_str)
        except (ValueError, SyntaxError) as e:
            raise RuntimeError(
                "Failed to parse AI response as JSON or Python literal. "
                f"Original error: {e}. Response content: {response!r}"
            ) from e
