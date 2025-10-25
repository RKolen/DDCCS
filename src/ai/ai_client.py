"""
AI Client Module - Flexible OpenAI-compatible client for LLM integration
Supports OpenAI, Ollama, OpenRouter, and other OpenAI-compatible providers
"""

import os
import json
import re
import ast
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from openai import OpenAI

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # dotenv not available, will use system environment variables only

class AIClient:
    """
    Flexible AI client that works with any OpenAI-compatible API.

    Configuration can be provided via:
    1. Environment variables (OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL)
    2. Direct parameters when initializing
    3. Per-request overrides

    Examples:
        # OpenAI (default)
        client = AIClient()

        # Ollama (local)
        client = AIClient(
            base_url="http://localhost:11434/v1",
            api_key="ollama",  # Ollama doesn't need a real key
            model="llama3.2"
        )

        # OpenRouter
        client = AIClient(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            model="meta-llama/llama-3.1-8b-instruct"
        )
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        **config
    ):
        """
        Initialize AI client with configuration.

        Args:
            api_key: API key for the provider (defaults to OPENAI_API_KEY env var)
            base_url: Base URL for the API (defaults to OpenAI, or OPENAI_BASE_URL env var)
            model: Model to use (defaults to OPENAI_MODEL env var or gpt-3.5-turbo)
            **config: Additional config:
                - default_temperature (float): Default temperature (default: 0.7)
                - default_max_tokens (int): Default max tokens (default: 1000)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.default_temperature = config.get("default_temperature", 0.7)
        self.default_max_tokens = config.get("default_max_tokens", 1000)

        # Initialize OpenAI client
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        self.client = OpenAI(**client_kwargs)

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
            messages: List of message dicts with 'role' and 'content'
            model: Override default model for this request
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            **kwargs: Additional parameters to pass to the API

        Returns:
            The assistant's response content as a string
        """
        try:
            response = self.client.chat.completions.create(
                model=model or self.model,
                messages=messages,
                temperature=(
                    temperature if temperature is not None else self.default_temperature
                ),
                max_tokens=max_tokens or self.default_max_tokens,
                **kwargs,
            )
            return response.choices[0].message.content
        except Exception as e:
            # Provide helpful error message
            error_msg = f"AI completion failed: {str(e)}"
            if "api_key" in str(e).lower():
                error_msg += "\n  Hint: Check your API key configuration"
            elif "connection" in str(e).lower():
                error_msg += (
                    f"\n  Hint: Check that {self.base_url or 'OpenAI'} is accessible"
                )
            raise RuntimeError(error_msg) from e

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
            custom_parameters=data.get("custom_parameters", {})
        )
        return cls(
            enabled=data.get("enabled", False),
            model=data.get("model"),
            base_url=data.get("base_url"),
            api_key=data.get("api_key"),
            system_prompt=data.get("system_prompt"),
            request_params=request_params
        )

    def create_client(self, default_client: Optional[AIClient] = None) -> AIClient:
        """
        Create an AI client for this character.

        Uses centralized .env configuration by default. Character-specific overrides
        (model, base_url, api_key) are only used if explicitly set in character JSON.

        Args:
            default_client: Default client to use if character doesn't have custom config

        Returns:
            AIClient configured for this character with .env defaults + character overrides
        """
        if not self.enabled:
            if default_client:
                return default_client
            raise RuntimeError(
                "AI is not enabled for this character and no default client provided"
            )

        # If no custom configuration at all, use default client or create from .env
        if not any([self.model, self.base_url, self.api_key]):
            return default_client if default_client else AIClient()

        # Load .env defaults, then apply character-specific overrides
        # This allows characters to override just one field (e.g., model)
        # while using .env for the rest
        env_config = load_ai_config_from_env()

        return AIClient(
            api_key=self.api_key or env_config["api_key"],
            base_url=self.base_url or env_config["base_url"],
            model=self.model or env_config["model"],
            default_temperature=self.request_params.temperature,
            default_max_tokens=self.request_params.max_tokens,
        )


def load_ai_config_from_env() -> Dict[str, str]:
    """
    Load AI configuration from environment variables.

    Returns:
        Dictionary with configuration values
    """
    return {
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "base_url": os.getenv("OPENAI_BASE_URL", ""),
        "model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        "temperature": float(os.getenv("AI_TEMPERATURE", "0.7")),
        "max_tokens": int(os.getenv("AI_MAX_TOKENS", "1000")),
    }

# Create a default AI client using .env or environment variables
_default_ai_client = AIClient()

def call_ai_for_behavior_block(prompt: str) -> dict:
    """
    Calls the LLM to generate a CharacterBehavior block from a prompt.
    Returns a dict with keys: preferred_strategies, typical_reactions, "
    "speech_patterns, decision_making_style.
    """
    # Compose messages for chat completion
    messages = [
        _default_ai_client.create_system_message(
            "You are a D&D character consultant AI."
            "Respond ONLY with a JSON object for the CharacterBehavior dataclass."),
        _default_ai_client.create_user_message(prompt)
    ]
    response = _default_ai_client.chat_completion(messages)
    # Try to extract JSON from the response (handles code block formatting)
    match = re.search(r'```json\n(.*?)```', response, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        # Fallback: try to parse the whole response
        json_str = response

    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, ValueError):
        # Fallback: attempt a safe Python literal evaluation (safer than eval)
        try:
            return ast.literal_eval(json_str)
        except (ValueError, SyntaxError) as e:
            # Provide a clear error including the raw response for debugging
            raise RuntimeError(
                "Failed to parse AI response as JSON or Python literal. "
                f"Original error: {e}. Response content: {response!r}"
            ) from e
