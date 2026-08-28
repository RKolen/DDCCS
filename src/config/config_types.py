"""
Configuration Type Definitions

Dataclasses for type-safe configuration management.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
from pathlib import Path


@dataclass
class ModelProfile:
    """A named AI model configuration profile."""

    name: str = ""
    provider: str = "openai"  # "openai", "ollama", "openrouter"
    base_url: str = ""
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 1000
    description: str = ""


@dataclass
class ModelRegistryConfig:
    """Registry of available model profiles."""

    active_profile: str = "default"
    profiles: Dict[str, ModelProfile] = field(default_factory=dict)

    def get_profile(self, name: str) -> Optional[ModelProfile]:
        """Return a profile by name, falling back to the active profile.

        Args:
            name: Profile name to look up.

        Returns:
            The matching ModelProfile, or None if not found.
        """
        return self.profiles.get(name if name else self.active_profile)

    def get_active_profile(self) -> Optional[ModelProfile]:
        """Return the currently active ModelProfile.

        Returns:
            The active ModelProfile, or None if the registry is empty.
        """
        return self.profiles.get(self.active_profile)

    def list_profile_names(self) -> List[str]:
        """Return a sorted list of available profile names.

        Returns:
            Sorted list of profile name strings.
        """
        return sorted(self.profiles.keys())


@dataclass
class AIConfig:
    """AI service configuration."""

    api_key: str = ""
    base_url: Optional[str] = None
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 1000
    enabled: bool = True

    # Per-character overrides stored separately
    character_overrides: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def get_client_config(self) -> Dict[str, Any]:
        """Get configuration dict for AIClient initialization."""
        return {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

    def is_configured(self) -> bool:
        """Check if AI is properly configured."""
        return bool(self.api_key and self.api_key != "your-openai-api-key-here")

    def get_character_config(self, character_name: str) -> Dict[str, Any]:
        """Get AI config for a specific character, with overrides."""
        base_config = self.get_client_config()

        if character_name in self.character_overrides:
            base_config.update(self.character_overrides[character_name])

        return base_config


@dataclass
class RAGConfig:
    """RAG (Retrieval-Augmented Generation) configuration."""

    enabled: bool = False
    wiki_base_url: str = ""
    rules_base_url: str = ""
    cache_ttl: int = 604800  # 7 days in seconds
    max_cache_size: int = 100
    search_depth: int = 3
    min_relevance: float = 0.5

    def is_configured(self) -> bool:
        """Check if RAG is properly configured."""
        return self.enabled and bool(self.wiki_base_url)


@dataclass
class RulesetConfig:
    """Which published rules content this group may use.

    Separate from RAGConfig, which says *how* rules pages are retrieved: this
    says *which* of them count. Character creation only offers the backgrounds,
    species, and classes introduced by the books listed here.
    """

    sourcebooks: List[str] = field(default_factory=list)

    def owns(self, sourcebook: str) -> bool:
        """Check whether a rules page's sourcebook line is one we own.

        Args:
            sourcebook: The "Source:" line from a rules page.

        Returns:
            True when no restriction is configured, or when any configured
            book name appears in the line (case-insensitive).
        """
        if not self.sourcebooks:
            return True
        haystack = sourcebook.lower()
        return any(book.strip().lower() in haystack for book in self.sourcebooks if book.strip())


@dataclass
class DisplayConfig:
    """Terminal display configuration."""

    use_rich: bool = True
    theme: str = ""
    max_line_width: int = 80
    enable_tts: bool = False
    tts_voice: Optional[str] = None
    tts_speed: int = 150
    # Piper-specific config stored as dict
    piper_config: Dict[str, Any] = field(default_factory=dict)

    def get_tts_config(self) -> Dict[str, Any]:
        """Get TTS configuration dict."""
        config = {
            "enabled": self.enable_tts,
            "voice": self.tts_voice,
            "speed": self.tts_speed,
        }
        config.update(self.piper_config)
        return config


@dataclass
class MilvusEmbeddingConfig:
    """Embedding model settings for Milvus semantic retrieval."""

    model: str = ""
    dim: int = 1536


@dataclass
class MilvusConfig:
    """Milvus vector database configuration.

    Host and port carry no defaults, for the same reason as SidecarConfig:
    MILVUS_HOST / MILVUS_PORT are authoritative, and guessing an address hides a
    misconfiguration behind a connection error to the wrong place.
    """

    enabled: bool = False
    host: str = ""
    port: int = 0
    collection_prefix: str = "dnd"
    embedding: MilvusEmbeddingConfig = field(default_factory=MilvusEmbeddingConfig)
    top_k: int = 5
    similarity_threshold: float = 0.7


@dataclass
class PathConfig:
    """File path configuration."""

    game_data_dir: Path = field(default_factory=lambda: Path("game_data"))
    cache_dir: Path = field(default_factory=lambda: Path(".rag_cache"))
    milvus_data_dir: Path = field(
        default_factory=lambda: Path("game_data") / "milvus"
    )

    @property
    def milvus_dir(self) -> Path:
        """Get milvus directory path."""
        return self.milvus_data_dir

    @property
    def characters_dir(self) -> Path:
        """Get characters directory path."""
        return self.game_data_dir / "characters"

    @property
    def campaigns_dir(self) -> Path:
        """Get campaigns directory path."""
        return self.game_data_dir / "campaigns"

    @property
    def npcs_dir(self) -> Path:
        """Get NPCs directory path."""
        return self.game_data_dir / "npcs"

    @property
    def items_dir(self) -> Path:
        """Get items directory path."""
        return self.game_data_dir / "items"

    def validate_paths(self) -> list:
        """Validate that required paths exist."""
        errors = []

        if not self.game_data_dir.exists():
            errors.append(f"Game data directory not found: {self.game_data_dir}")

        if not self.characters_dir.exists():
            errors.append(f"Characters directory not found: {self.characters_dir}")

        return errors


@dataclass
class SpotlightConfig:
    """Spotlight system configuration.

    Controls signal weights and the number of entries injected into AI prompts.
    Weights determine how much each signal type contributes to the 0-100 score.
    """

    enabled: bool = True
    recency_weight: float = 20.0
    thread_weight: float = 25.0
    dc_weight: float = 20.0
    tension_weight: float = 15.0
    max_characters_in_prompt: int = 3
    max_npcs_in_prompt: int = 3


@dataclass
class DrupalConfig:
    """Drupal CMS integration configuration."""

    base_url: str = ""
    user: str = ""
    password: str = ""
    gatsby_webhook_url: str = ""
    # Bearer token for authenticated GraphQL reads (same token Gatsby uses).
    # Needed to resolve reference fields that are not exposed anonymously.
    graphql_token: str = ""
    # Optional CA bundle path for verifying Drupal's TLS certificate. Set to the
    # mkcert root CA for local ddev; empty uses the default trust store. TLS is
    # always verified.
    ca_bundle: str = ""


@dataclass
class SidecarConfig:
    """Query-parser sidecar configuration.

    Host and port carry no defaults: they are authoritative configuration
    (SIDECAR_HOST / SIDECAR_PORT), and a guessed address is worse than a loud
    failure - it silently targets the wrong service.
    """

    host: str = ""
    port: int = 0
    timeout: float = 5.0
    min_confidence: float = 0.6
    log_level: str = "info"
    secret: str = ""
    reload: bool = False


@dataclass
class ComfyUIReactor:
    """Optional ReActor face-swap files for staggered story-scene likeness.

    Empty ``swap_model`` means those swaps are skipped rather than failing the
    render. Detection and node class have working defaults.
    """

    swap_model: str = ""
    face_detection: str = "retinaface_resnet50"
    node: str = "ReActorFaceSwap"

    def available(self) -> bool:
        """True when a swap model filename is configured."""
        return bool(self.swap_model)


@dataclass
class ComfyUIAssets:
    """The model files ComfyUI generation and image->prompt need.

    ``image_to_prompt_model`` is the Ollama vision model that describes an
    existing portrait into a prompt (image->prompt); ``checkpoint`` is the
    Stable Diffusion model file name inside ComfyUI's ``models/checkpoints/``.

    ``ipadapter_model`` and ``clip_vision`` are the identity-conditioning pair
    (in ``models/ipadapter/`` and ``models/clip_vision/``), used to keep a
    regenerated portrait recognisably the same character. They are configured
    rather than derived because the right pair depends on the checkpoint family
    - an SD 1.5 IPAdapter silently produces nothing useful on an SDXL
    checkpoint. Both empty means identity conditioning is simply unavailable and
    generation falls back to text-to-image.

    ``reactor`` is the InsightFace swapper used after the two IPAdapter leads
    on a story scene. ``scene_timeout`` is the longer ComfyUI wait for that
    path (base render plus staggered swaps).
    """

    image_to_prompt_model: str = ""
    checkpoint: str = ""
    ipadapter_model: str = ""
    clip_vision: str = ""
    reactor: ComfyUIReactor = field(default_factory=ComfyUIReactor)
    scene_timeout: float = 1800.0

    def supports_identity(self) -> bool:
        """Check whether IPAdapter identity conditioning can be used.

        Returns:
            True when both the IPAdapter model and its CLIP-vision encoder are
            configured. One without the other cannot build a valid graph.
        """
        return bool(self.ipadapter_model and self.clip_vision)

    def supports_reactor(self) -> bool:
        """Check whether staggered ReActor face swaps can be used.

        Returns:
            True when a swap model filename is configured. Detection and node
            class have defaults; the swap file is what a deployment must install.
        """
        return self.reactor.available()


@dataclass
class ComfyUIConfig:
    """Local ComfyUI (Stable Diffusion) portrait-generation service.

    ComfyUI runs on the host (like Ollama), never in DDEV. The sidecar reaches it
    over its HTTP workflow API. ``base_url`` is derived from host/port when empty.
    Disabled by default; opt in via ``COMFYUI_ENABLED``.

    ``ollama_url`` is the local Ollama server's native API base (not the ``/v1``
    OpenAI-compatible path), composed from OLLAMA_HOST/OLLAMA_PORT. The portrait
    flow uses it to unload resident Ollama models before Stable Diffusion loads
    its checkpoint - on a CPU-only box, two large models resident at once is the
    top OOM risk.
    """

    enabled: bool = False
    host: str = ""
    port: int = 0
    base_url: str = ""
    timeout: float = 900.0  # CPU generation is slow (minutes/image)
    assets: ComfyUIAssets = field(default_factory=ComfyUIAssets)
    ollama_url: str = ""

    def get_base_url(self) -> str:
        """Return the configured base URL, or one built from host/port.

        Returns:
            The base URL without a trailing slash, or an empty string when
            neither COMFYUI_BASE_URL nor a full COMFYUI_HOST/COMFYUI_PORT pair
            is configured - which ``is_configured()`` reports as "not set up"
            rather than guessing an address.
        """
        if self.base_url:
            return self.base_url.rstrip("/")
        if self.host and self.port:
            return f"http://{self.host}:{self.port}"
        return ""

    def is_configured(self) -> bool:
        """Check if ComfyUI is enabled and has a reachable base URL."""
        return self.enabled and bool(self.get_base_url())

    @property
    def scene_timeout(self) -> float:
        """Seconds to wait for a story-scene render, including staggered swaps."""
        return self.assets.scene_timeout

    @scene_timeout.setter
    def scene_timeout(self, value: float) -> None:
        """Store the scene timeout on the assets bundle.

        Args:
            value: Seconds. Must stay under the Drupal job lease.
        """
        self.assets.scene_timeout = value


@dataclass
class ServiceConfig:
    """Grouped service configuration (model registry, vector database, spotlighting)."""

    model_registry: ModelRegistryConfig = field(default_factory=ModelRegistryConfig)
    milvus: MilvusConfig = field(default_factory=MilvusConfig)
    spotlight: SpotlightConfig = field(default_factory=SpotlightConfig)
    drupal: DrupalConfig = field(default_factory=DrupalConfig)
    sidecar: SidecarConfig = field(default_factory=SidecarConfig)
    comfyui: ComfyUIConfig = field(default_factory=ComfyUIConfig)
    ruleset: RulesetConfig = field(default_factory=RulesetConfig)


@dataclass
class DnDConfig:
    """Root configuration container."""

    ai: AIConfig = field(default_factory=AIConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    services: ServiceConfig = field(default_factory=ServiceConfig)

    # Metadata
    config_file_path: Optional[Path] = None
    _dirty: bool = field(default=False, repr=False)

    # ------------------------------------------------------------------
    # Convenience properties for frequently accessed service sub-configs
    # ------------------------------------------------------------------

    @property
    def model_registry(self) -> ModelRegistryConfig:
        """Return the model registry config."""
        return self.services.model_registry

    @model_registry.setter
    def model_registry(self, value: ModelRegistryConfig) -> None:
        """Replace the model registry config."""
        self.services.model_registry = value

    @property
    def milvus(self) -> MilvusConfig:
        """Return the Milvus config."""
        return self.services.milvus

    @milvus.setter
    def milvus(self, value: MilvusConfig) -> None:
        """Replace the Milvus config."""
        self.services.milvus = value

    @property
    def ruleset(self) -> RulesetConfig:
        """Return the ruleset content config."""
        return self.services.ruleset

    @ruleset.setter
    def ruleset(self, value: RulesetConfig) -> None:
        """Replace the ruleset content config."""
        self.services.ruleset = value

    @property
    def spotlight(self) -> "SpotlightConfig":
        """Return the spotlight config."""
        return self.services.spotlight

    @spotlight.setter
    def spotlight(self, value: "SpotlightConfig") -> None:
        """Replace the spotlight config."""
        self.services.spotlight = value

    @property
    def drupal(self) -> "DrupalConfig":
        """Return the Drupal integration config."""
        return self.services.drupal

    @drupal.setter
    def drupal(self, value: "DrupalConfig") -> None:
        """Replace the Drupal integration config."""
        self.services.drupal = value

    @property
    def sidecar(self) -> "SidecarConfig":
        """Return the query-parser sidecar config."""
        return self.services.sidecar

    @sidecar.setter
    def sidecar(self, value: "SidecarConfig") -> None:
        """Replace the query-parser sidecar config."""
        self.services.sidecar = value

    @property
    def comfyui(self) -> "ComfyUIConfig":
        """Return the ComfyUI portrait service config."""
        return self.services.comfyui

    @comfyui.setter
    def comfyui(self, value: "ComfyUIConfig") -> None:
        """Replace the ComfyUI portrait service config."""
        self.services.comfyui = value

    def is_dirty(self) -> bool:
        """Check if configuration has unsaved changes."""
        return self._dirty

    def mark_dirty(self) -> None:
        """Mark configuration as having unsaved changes."""
        self._dirty = True

    def mark_clean(self) -> None:
        """Mark configuration as saved."""
        self._dirty = False

    def validate(self) -> list:
        """Validate configuration and return list of errors.

        Returns:
            List of validation error messages (empty if valid).
        """
        errors = []

        # Validate AI config
        if self.ai.enabled and not self.ai.api_key:
            errors.append("AI is enabled but api_key is not set")
        if self.ai.api_key and self.ai.api_key == "your-openai-api-key-here":
            errors.append("AI api_key appears to be a placeholder")

        # Validate RAG config
        if self.rag.enabled and not self.rag.wiki_base_url:
            errors.append("RAG is enabled but wiki_base_url is not set")

        # Validate paths
        errors.extend(self.paths.validate_paths())

        return errors

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.

        Args:
            key: Configuration key (e.g., 'ai.model', 'rag.enabled')
            default: Default value if key not found

        Returns:
            Configuration value or default.
        """
        # Handle nested keys like 'ai.model'
        parts = key.split(".")
        if not parts:
            return default

        # Navigate to the correct config section
        section = parts[0]
        obj: Optional[Union[AIConfig, RAGConfig, DisplayConfig, PathConfig]] = None
        if section == "ai":
            obj = self.ai
        elif section == "rag":
            obj = self.rag
        elif section == "display":
            obj = self.display
        elif section == "paths":
            obj = self.paths
        else:
            return default

        # Get the attribute value
        if len(parts) == 1:
            return obj

        # Handle nested attributes
        attr = parts[1]
        if hasattr(obj, attr):
            return getattr(obj, attr)
        return default

    def set(self, key: str, value: Any) -> None:
        """Set configuration value by key.

        Args:
            key: Configuration key (e.g., 'ai.model', 'rag.enabled')
            value: Value to set
        """
        # Handle nested keys like 'ai.model'
        parts = key.split(".")
        if not parts:
            return

        # Navigate to the correct config section
        section = parts[0]
        obj2: Optional[Union[AIConfig, RAGConfig, DisplayConfig, PathConfig]] = None
        if section == "ai":
            obj2 = self.ai
        elif section == "rag":
            obj2 = self.rag
        elif section == "display":
            obj2 = self.display
        elif section == "paths":
            obj2 = self.paths
        else:
            return

        # Set the attribute value
        if len(parts) == 1:
            return

        attr = parts[1]
        if hasattr(obj2, attr):
            setattr(obj2, attr, value)
            self.mark_dirty()


# Convenience exports
__all__ = [
    "AIConfig",
    "ModelProfile",
    "ModelRegistryConfig",
    "RAGConfig",
    "DisplayConfig",
    "PathConfig",
    "DrupalConfig",
    "SidecarConfig",
    "ComfyUIConfig",
    "DnDConfig",
]
