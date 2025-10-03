"""
AI Client Module - Flexible OpenAI-compatible client for LLM integration
Supports OpenAI, Ollama, OpenRouter, and other OpenAI-compatible providers
"""

import os
from typing import Dict, List, Any, Optional
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
        default_temperature: float = 0.7,
        default_max_tokens: int = 1000
    ):
        """
        Initialize AI client with configuration.
        
        Args:
            api_key: API key for the provider (defaults to OPENAI_API_KEY env var)
            base_url: Base URL for the API (defaults to OpenAI, or OPENAI_BASE_URL env var)
            model: Default model to use (defaults to gpt-3.5-turbo, or OPENAI_MODEL env var)
            default_temperature: Default temperature for requests (0.0-2.0)
            default_max_tokens: Default maximum tokens for responses
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.default_temperature = default_temperature
        self.default_max_tokens = default_max_tokens
        
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
        **kwargs
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
                temperature=temperature if temperature is not None else self.default_temperature,
                max_tokens=max_tokens or self.default_max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            # Provide helpful error message
            error_msg = f"AI completion failed: {str(e)}"
            if "api_key" in str(e).lower():
                error_msg += "\n  Hint: Check your API key configuration"
            elif "connection" in str(e).lower():
                error_msg += f"\n  Hint: Check that {self.base_url or 'OpenAI'} is accessible"
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


class CharacterAIConfig:
    """
    AI configuration specific to a character.
    Allows each character to have unique AI behavior, model selection, etc.
    """
    
    def __init__(
        self,
        enabled: bool = False,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_prompt: Optional[str] = None,
        custom_parameters: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize character-specific AI configuration.
        
        Args:
            enabled: Whether AI is enabled for this character
            model: Model to use for this character (None = use default)
            base_url: Base URL for this character (None = use default)
            api_key: API key for this character (None = use default)
            temperature: Temperature for this character's responses
            max_tokens: Max tokens for this character's responses
            system_prompt: Custom system prompt for character roleplay
            custom_parameters: Additional provider-specific parameters
        """
        self.enabled = enabled
        self.model = model
        self.base_url = base_url
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.custom_parameters = custom_parameters or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "enabled": self.enabled,
            "model": self.model,
            "base_url": self.base_url,
            "api_key": self.api_key,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "system_prompt": self.system_prompt,
            "custom_parameters": self.custom_parameters
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CharacterAIConfig':
        """Create from dictionary."""
        return cls(
            enabled=data.get("enabled", False),
            model=data.get("model"),
            base_url=data.get("base_url"),
            api_key=data.get("api_key"),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 1000),
            system_prompt=data.get("system_prompt"),
            custom_parameters=data.get("custom_parameters", {})
        )
    
    def create_client(self, default_client: Optional[AIClient] = None) -> AIClient:
        """
        Create an AI client for this character.
        
        Args:
            default_client: Default client to use if character doesn't have custom config
            
        Returns:
            AIClient configured for this character
        """
        if not self.enabled:
            if default_client:
                return default_client
            raise RuntimeError("AI is not enabled for this character and no default client provided")
        
        # If no custom configuration, use defaults
        if not any([self.model, self.base_url, self.api_key]):
            return default_client if default_client else AIClient()
        
        # Create custom client for this character
        return AIClient(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            default_temperature=self.temperature,
            default_max_tokens=self.max_tokens
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
        "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
        "max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
    }
