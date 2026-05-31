"""AI Client Module - Flexible OpenAI-compatible client for LLM integration."""

import functools
import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Any,
    Dict,
    Generator,
    List,
    NamedTuple,
    Optional,
    Tuple,
    Union,
    overload,
)

import tenacity
from openai import OpenAI

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

logger = logging.getLogger(__name__)

_RETRYABLE_ERROR_TYPES: frozenset = frozenset({
    "RateLimitError",
    "APIConnectionError",
    "APITimeoutError",
})


class _TransientAIError(RuntimeError):
    """Wraps transient API errors that should be retried by tenacity."""


class _RetryConfig(NamedTuple):
    """Groups retry, timeout, and per-request defaults for AIClient."""

    timeout: float = 30.0
    max_retries: int = 3
    backoff_strategy: str = "exponential"
    model_chain: Tuple[str, ...] = ()
    log_path: Optional[Path] = None
    default_temperature: float = 0.7
    default_max_tokens: int = 1000


def _build_openai_client(
    api_key: Optional[str],
    base_url: Optional[str],
    timeout: float,
) -> Any:
    """Construct the underlying OpenAI client from credentials."""
    client_kwargs: Dict[str, Any] = {}
    if api_key and isinstance(api_key, str) and api_key.strip():
        client_kwargs["api_key"] = api_key
    if base_url and isinstance(base_url, str) and base_url.strip():
        client_kwargs["base_url"] = base_url
    allowed_keys = {"api_key", "base_url"}
    filtered = {k: v for k, v in client_kwargs.items() if k in allowed_keys and v}
    return OpenAI(timeout=timeout, **filtered)


class AIClient:
    """Flexible AI client for any OpenAI-compatible API.

    Configuration is resolved via centralized config, then env vars.
    All provider details (base_url, model, api_key) must be set via
    config or environment -- no hardcoded defaults.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        **config,
    ):
        """Initialize AI client.

        Args:
            api_key: API key for the provider.
            base_url: Base URL for the API endpoint.
            model: Model name to use.
            **config: Additional config keys:
                - default_temperature (float)
                - default_max_tokens (int)
                - embedding_model (str)
                - timeout (float): Request timeout in seconds (default 30.0).
                - max_retries (int): Attempts on transient errors (default 3).
                - backoff_strategy (str): "exponential" or "fixed" (default "exponential").
                - model_chain (List[str]): Ordered fallback models after primary fails.
                - ai_config: Optional AIConfig object (takes precedence).
        """
        ai_config = config.pop("ai_config", None)
        if ai_config is not None:
            self.api_key = api_key or ai_config.api_key
            self.base_url = base_url or ai_config.base_url
            self.model = model or ai_config.model
            cfg_temp: float = config.get("default_temperature", ai_config.temperature)
            cfg_tokens: int = config.get("default_max_tokens", ai_config.max_tokens)
        else:
            self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
            self.base_url = base_url or os.getenv("OPENAI_BASE_URL", None)
            self.model = model or os.getenv("OPENAI_MODEL", "")
            cfg_temp = config.get("default_temperature", 0.7)
            cfg_tokens = config.get("default_max_tokens", 1000)

        self.embedding_model: str = str(
            config.get("embedding_model") or os.getenv("OPENAI_EMBEDDING_MODEL", "")
        )

        timeout = float(config.pop("timeout", 30.0))
        max_retries = int(config.pop("max_retries", 3))
        backoff_strategy = str(config.pop("backoff_strategy", "exponential"))
        model_chain = config.pop("model_chain", None)
        log_path_raw = os.getenv("AI_CALL_LOG_PATH", "")

        self._retry = _RetryConfig(
            timeout=timeout,
            max_retries=max_retries,
            backoff_strategy=backoff_strategy,
            model_chain=tuple(model_chain or []),
            log_path=Path(log_path_raw) if log_path_raw else None,
            default_temperature=float(cfg_temp),
            default_max_tokens=int(cfg_tokens),
        )

        self.client: Any = _build_openai_client(self.api_key, self.base_url, timeout)

    # -- Backward-compatible properties for retry config fields --

    @property
    def default_temperature(self) -> float:
        """Default temperature for chat completions."""
        return self._retry.default_temperature

    @property
    def default_max_tokens(self) -> int:
        """Default max_tokens for chat completions."""
        return self._retry.default_max_tokens

    @property
    def timeout(self) -> float:
        """Request timeout in seconds."""
        return self._retry.timeout

    @property
    def max_retries(self) -> int:
        """Number of retry attempts on transient errors."""
        return self._retry.max_retries

    @property
    def backoff_strategy(self) -> str:
        """Backoff strategy: 'exponential' or 'fixed'."""
        return self._retry.backoff_strategy

    @property
    def model_chain(self) -> List[str]:
        """Ordered list of fallback models."""
        return list(self._retry.model_chain)

    @property
    def _is_ollama(self) -> bool:
        """Return True when base_url targets an Ollama instance."""
        if not self.base_url:
            return False
        url = self.base_url.lower()
        return "ollama" in url or ":11434" in url

    # -- Logging hook --

    def _log_call(
        self,
        messages: List[Dict[str, str]],
        response: str,
        latency: float,
        token_count: Optional[int],
    ) -> None:
        """Append one call record to the JSONL log file."""
        log_path = self._retry.log_path
        if log_path is None:
            return
        record: Dict[str, Any] = {
            "ts": time.time(),
            "model": self.model,
            "latency": round(latency, 3),
            "tokens": token_count,
            "messages": messages,
            "response": response,
        }
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(record) + "\n")
        except OSError as exc:
            logger.debug("Call log write failed: %s", exc)

    # -- Low-level completion helpers --

    def _raw_chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        **kwargs,
    ) -> Tuple[str, Optional[int]]:
        """Single API call. Returns (content, token_count).

        Raises _TransientAIError for retryable failures, RuntimeError otherwise.
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )
            content = response.choices[0].message.content or ""
            tokens: Optional[int] = (
                response.usage.total_tokens if response.usage else None
            )
            return content, tokens
        except Exception as exc:
            error_type = type(exc).__name__
            if error_type in _RETRYABLE_ERROR_TYPES:
                raise _TransientAIError(
                    f"AI completion failed (transient): {exc}"
                ) from exc
            if error_type == "AuthenticationError":
                raise RuntimeError("AI completion failed: Invalid API key") from exc
            if error_type == "BadRequestError":
                raise RuntimeError(
                    f"AI completion failed: Bad request: {exc}"
                ) from exc
            raise RuntimeError(f"AI completion failed: {exc}") from exc

    def _attempt_model(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        **kwargs,
    ) -> Tuple[str, Optional[int]]:
        """Run completion with tenacity retry for transient errors."""
        wait: Any = (
            tenacity.wait_fixed(1.0)
            if self._retry.backoff_strategy == "fixed"
            else tenacity.wait_exponential(multiplier=1, min=1, max=10)
        )
        for attempt in tenacity.Retrying(
            stop=tenacity.stop_after_attempt(self._retry.max_retries),
            wait=wait,
            retry=tenacity.retry_if_exception_type(_TransientAIError),
            reraise=True,
        ):
            with attempt:
                return self._raw_chat(model, messages, temperature, max_tokens, **kwargs)
        raise RuntimeError("Retry loop exhausted without result")

    # -- Public API --

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """Get a chat completion from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            model: Override default model for this request.
            temperature: Override default temperature.
            max_tokens: Override default max_tokens.
            **kwargs: Additional parameters. Pass json_mode=True to request
                structured JSON output; all other kwargs are forwarded to the API.

        Returns:
            The assistant's response content as a string.
        """
        if self.client is None:
            raise RuntimeError(
                "AI client not available. Install openai package: pip install openai"
            )
        json_mode: bool = kwargs.pop("json_mode", False)
        if json_mode:
            if self._is_ollama:
                kwargs["extra_body"] = {"format": "json"}
            else:
                kwargs["response_format"] = {"type": "json_object"}

        effective_temp = (
            temperature if temperature is not None else self._retry.default_temperature
        )
        effective_tokens = (
            max_tokens if max_tokens is not None else self._retry.default_max_tokens
        )

        last_exc: RuntimeError = RuntimeError("No models attempted")
        t_start = time.monotonic()
        for attempt_model in [model or self.model] + list(self._retry.model_chain):
            try:
                result, token_count = self._attempt_model(
                    attempt_model, messages, effective_temp, effective_tokens, **kwargs
                )
                self._log_call(messages, result, time.monotonic() - t_start, token_count)
                return result
            except RuntimeError as exc:
                last_exc = exc
                if "Invalid API key" in str(exc) or "Bad request" in str(exc):
                    raise
        raise last_exc

    def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Generator[str, None, None]:
        """Stream chat completion chunks as a generator.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            model: Override default model.
            temperature: Override default temperature.
            max_tokens: Override default max_tokens.
            **kwargs: Additional parameters passed to the API.

        Yields:
            Content delta strings as they arrive from the API.
        """
        if self.client is None:
            raise RuntimeError(
                "AI client not available. Install openai package: pip install openai"
            )
        try:
            stream = self.client.chat.completions.create(
                model=model or self.model,
                messages=messages,
                temperature=(
                    temperature
                    if temperature is not None
                    else self._retry.default_temperature
                ),
                max_tokens=(
                    max_tokens
                    if max_tokens is not None
                    else self._retry.default_max_tokens
                ),
                stream=True,
                **kwargs,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as exc:
            raise RuntimeError(f"Stream completion failed: {exc}") from exc

    @overload
    def embed(self, text: str, model: str = "") -> List[float]: ...

    @overload
    def embed(self, text: List[str], model: str = "") -> List[List[float]]: ...

    def embed(
        self, text: Union[str, List[str]], model: str = ""
    ) -> Union[List[float], List[List[float]]]:
        """Generate embedding(s).

        Args:
            text: Single string or list of strings to embed.
            model: Embedding model. Falls back to OPENAI_EMBEDDING_MODEL env var.

        Returns:
            List[float] for a single string; List[List[float]] for a list.
        """
        effective_model = model or self.embedding_model
        if not effective_model or self.client is None:
            return []
        if isinstance(text, str):
            text_batch: List[str] = [text]
        else:
            text_batch = list(text)
        single = isinstance(text, str)
        try:
            response = self.client.embeddings.create(
                input=text_batch, model=effective_model
            )
            vectors = [list(item.embedding) for item in response.data]
            return vectors[0] if single else vectors
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
    """AI configuration specific to a character.

    Holds data only -- use build_client_for_character() to create an AIClient.
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


def _make_client(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None,
    default_temperature: Optional[float] = None,
    default_max_tokens: Optional[int] = None,
) -> AIClient:
    """Create an AIClient by merging centralized config with caller overrides.

    Args:
        api_key: Override the configured API key.
        base_url: Override the configured base URL.
        model: Override the configured model name.
        default_temperature: Override the configured temperature.
        default_max_tokens: Override the configured max_tokens.

    Returns:
        A fully configured AIClient instance.
    """
    env = load_ai_config_from_env()
    return AIClient(
        api_key=api_key or env.get("api_key", ""),
        base_url=base_url or env.get("base_url"),
        model=model or env.get("model", ""),
        default_temperature=(
            default_temperature
            if default_temperature is not None
            else env.get("temperature", 0.7)
        ),
        default_max_tokens=(
            default_max_tokens
            if default_max_tokens is not None
            else env.get("max_tokens", 1000)
        ),
    )


@functools.lru_cache(maxsize=1)
def _get_default_client() -> AIClient:
    """Return the cached default AIClient."""
    return _make_client()


def build_client_for_character(
    char_config: CharacterAIConfig,
    default_client: Optional[AIClient] = None,
) -> AIClient:
    """Create an AIClient for a character, applying character-level overrides.

    Args:
        char_config: Character-specific AI configuration.
        default_client: Fallback used when the character has no custom config.

    Returns:
        AIClient configured for the character.

    Raises:
        RuntimeError: If AI is disabled and no default client is provided.
    """
    if not char_config.enabled:
        if default_client:
            return default_client
        raise RuntimeError(
            "AI is not enabled for this character and no default client provided"
        )

    if not any([char_config.model, char_config.base_url, char_config.api_key]):
        return default_client if default_client else _get_default_client()

    return _make_client(
        api_key=char_config.api_key,
        base_url=char_config.base_url,
        model=char_config.model,
        default_temperature=char_config.request_params.temperature,
        default_max_tokens=char_config.request_params.max_tokens,
    )


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
        return _make_client(**kwargs)
    return _get_default_client()


def call_ai_for_behavior_block(prompt: str) -> dict:
    """Call the LLM to generate a CharacterBehavior block from a prompt.

    Args:
        prompt: The behavior generation prompt.

    Returns:
        Dict with keys: preferred_strategies, typical_reactions,
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
    response = client.chat_completion(messages, json_mode=True)
    try:
        return json.loads(response)
    except (json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(
            f"Failed to parse AI response as JSON. Response content: {response!r}"
        ) from exc
