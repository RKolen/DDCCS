"""
CLI Configuration Manager

Provides interactive configuration management through the CLI.
Allows users to view, edit, and save configuration settings.
"""

from pathlib import Path
from typing import Optional

from src.config.config_loader import load_config, save_config
from src.config.config_types import DnDConfig


class ConfigCLI:
    """CLI for managing configuration settings."""

    def __init__(self, config: Optional[DnDConfig] = None):
        """Initialize config CLI.

        Args:
            config: Optional DnDConfig instance. If not provided, loads from file.
        """
        self.config = config
        self.config_path = Path("game_data/config.json")

    def ensure_config(self) -> DnDConfig:
        """Ensure config is loaded."""
        if self.config is None:
            try:
                self.config = load_config(self.config_path)
            except (OSError, ImportError):
                self.config = DnDConfig()
                self.config.config_file_path = self.config_path
        return self.config

    def show_current_config(self) -> None:
        """Display current configuration."""
        config = self.ensure_config()

        print("\n[CONFIG] Current Configuration")
        print("=" * 40)

        # AI Config
        print("\n[AI Settings]")
        print(f"  API Key: {'*' * 8 if config.ai.api_key else '(not set)'}")
        print(f"  Base URL: {config.ai.base_url or '(default)'}")
        print(f"  Model: {config.ai.model or '(not set)'}")
        print(f"  Temperature: {config.ai.temperature}")
        print(f"  Max Tokens: {config.ai.max_tokens}")
        print(f"  Enabled: {config.ai.enabled}")

        # RAG Config
        print("\n[RAG Settings]")
        print(f"  Enabled: {config.rag.enabled}")
        print(f"  Wiki Base URL: {config.rag.wiki_base_url or '(not set)'}")
        print(f"  Rules Base URL: {config.rag.rules_base_url or '(not set)'}")
        print(f"  Cache TTL: {config.rag.cache_ttl} seconds")
        print(f"  Max Cache Size: {config.rag.max_cache_size}")
        print(f"  Search Depth: {config.rag.search_depth}")
        print(f"  Min Relevance: {config.rag.min_relevance}")

        # Display Config
        print("\n[Display Settings]")
        print(f"  Use Rich: {config.display.use_rich}")
        print(f"  Theme: {config.display.theme or '(default)'}")
        print(f"  Max Line Width: {config.display.max_line_width}")
        print(f"  TTS Enabled: {config.display.enable_tts}")
        print(f"  TTS Voice: {config.display.tts_voice or '(default)'}")
        print(f"  TTS Speed: {config.display.tts_speed}")

        # Path Config
        print("\n[Path Settings]")
        print(f"  Game Data Dir: {config.paths.game_data_dir}")
        print(f"  Cache Dir: {config.paths.cache_dir}")

        print()

    def run_config_menu(self) -> None:
        """Run the configuration menu."""
        while True:
            print("\n[CONFIG] Configuration Menu")
            print("-" * 30)
            print("1. View Current Configuration")
            print("2. Configure AI Settings")
            print("3. Configure RAG Settings")
            print("4. Configure Display Settings")
            print("5. Configure Path Settings")
            print("6. Save Configuration")
            print("7. Validate Configuration")
            print("0. Back to Main Menu")
            print()

            choice = input("Enter your choice: ").strip()

            if choice == "0":
                break
            if choice == "1":
                self.show_current_config()
            elif choice == "2":
                self.configure_ai()
            elif choice == "3":
                self.configure_rag()
            elif choice == "4":
                self.configure_display()
            elif choice == "5":
                self.configure_paths()
            elif choice == "6":
                self.save_config()
            elif choice == "7":
                self.validate_config()
            else:
                print("[ERROR] Invalid choice")

    def configure_ai(self) -> None:
        """Configure AI settings."""
        config = self.ensure_config()

        print("\n[CONFIG] AI Settings")
        print("(Press Enter to keep current value)")

        # API Key
        new_key = input(f"API Key [{('*' * 8) if config.ai.api_key else '(not set)'}]: ").strip()
        if new_key:
            config.ai.api_key = new_key

        # Base URL
        new_url = input(f"Base URL [{config.ai.base_url or 'default'}]: ").strip()
        if new_url:
            config.ai.base_url = new_url

        # Model
        new_model = input(f"Model [{config.ai.model or 'not set'}]: ").strip()
        if new_model:
            config.ai.model = new_model

        # Temperature
        new_temp = input(f"Temperature [{config.ai.temperature}]: ").strip()
        if new_temp:
            try:
                config.ai.temperature = float(new_temp)
            except ValueError:
                print("[ERROR] Invalid temperature value")

        # Max Tokens
        new_tokens = input(f"Max Tokens [{config.ai.max_tokens}]: ").strip()
        if new_tokens:
            try:
                config.ai.max_tokens = int(new_tokens)
            except ValueError:
                print("[ERROR] Invalid max tokens value")

        # Enabled
        new_enabled = input(f"Enabled (yes/no) [{config.ai.enabled}]: ").strip().lower()
        if new_enabled:
            config.ai.enabled = new_enabled in ("yes", "y", "true", "1")

        print("[SUCCESS] AI settings updated")

    def configure_rag(self) -> None:
        """Configure RAG settings."""
        config = self.ensure_config()

        print("\n[CONFIG] RAG Settings")
        print("(Press Enter to keep current value)")

        # Enabled
        new_enabled = input(f"Enabled (yes/no) [{config.rag.enabled}]: ").strip().lower()
        if new_enabled:
            config.rag.enabled = new_enabled in ("yes", "y", "true", "1")

        # Wiki Base URL
        new_url = input(f"Wiki Base URL [{config.rag.wiki_base_url or 'not set'}]: ").strip()
        if new_url:
            config.rag.wiki_base_url = new_url

        # Rules Base URL
        new_rules = input(f"Rules Base URL [{config.rag.rules_base_url or 'not set'}]: ").strip()
        if new_rules:
            config.rag.rules_base_url = new_rules

        # Cache TTL
        new_ttl = input(f"Cache TTL (seconds) [{config.rag.cache_ttl}]: ").strip()
        if new_ttl:
            try:
                config.rag.cache_ttl = int(new_ttl)
            except ValueError:
                print("[ERROR] Invalid cache TTL value")

        # Search Depth
        new_depth = input(f"Search Depth [{config.rag.search_depth}]: ").strip()
        if new_depth:
            try:
                config.rag.search_depth = int(new_depth)
            except ValueError:
                print("[ERROR] Invalid search depth value")

        print("[SUCCESS] RAG settings updated")

    def configure_display(self) -> None:
        """Configure display settings."""
        config = self.ensure_config()

        print("\n[CONFIG] Display Settings")
        print("(Press Enter to keep current value)")

        # Use Rich
        new_rich = input(f"Use Rich (yes/no) [{config.display.use_rich}]: ").strip().lower()
        if new_rich:
            config.display.use_rich = new_rich in ("yes", "y", "true", "1")

        # Theme
        new_theme = input(f"Theme [{config.display.theme or 'default'}]: ").strip()
        if new_theme:
            config.display.theme = new_theme

        # Max Line Width
        new_width = input(f"Max Line Width [{config.display.max_line_width}]: ").strip()
        if new_width:
            try:
                config.display.max_line_width = int(new_width)
            except ValueError:
                print("[ERROR] Invalid width value")

        # TTS Enabled
        new_tts = input(f"TTS Enabled (yes/no) [{config.display.enable_tts}]: ").strip().lower()
        if new_tts:
            config.display.enable_tts = new_tts in ("yes", "y", "true", "1")

        # TTS Voice
        new_voice = input(f"TTS Voice [{config.display.tts_voice or 'default'}]: ").strip()
        if new_voice:
            config.display.tts_voice = new_voice

        print("[SUCCESS] Display settings updated")

    def configure_paths(self) -> None:
        """Configure path settings."""
        config = self.ensure_config()

        print("\n[CONFIG] Path Settings")
        print("(Press Enter to keep current value)")

        # Game Data Dir
        new_gamedata = input(f"Game Data Dir [{config.paths.game_data_dir}]: ").strip()
        if new_gamedata:
            config.paths.game_data_dir = Path(new_gamedata)

        # Cache Dir
        new_cache = input(f"Cache Dir [{config.paths.cache_dir}]: ").strip()
        if new_cache:
            config.paths.cache_dir = Path(new_cache)

        print("[SUCCESS] Path settings updated")

    def save_config(self) -> None:
        """Save configuration to file."""
        config = self.ensure_config()

        try:
            save_config(config, self.config_path)
            print(f"[SUCCESS] Configuration saved to {self.config_path}")
        except OSError as e:
            print(f"[ERROR] Failed to save configuration: {e}")

    def validate_config(self) -> None:
        """Validate configuration."""
        config = self.ensure_config()

        errors = config.validate()

        if errors:
            print("\n[ERROR] Configuration validation failed:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("\n[SUCCESS] Configuration is valid")


def run_config_cli() -> None:
    """Run the configuration CLI."""
    cli = ConfigCLI()
    cli.run_config_menu()
