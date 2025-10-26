"""Centralized AI availability check.

This module exposes two public symbols used across the codebase:
- AI_AVAILABLE: bool indicating whether the AI client import succeeded
- CharacterAIConfig: the imported class when available, otherwise None

Centralizing this check avoids duplicate try/except-import blocks across
modules and makes it easier to test import availability in one place.
"""
try:
    from src.ai.ai_client import CharacterAIConfig

    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    CharacterAIConfig = None

__all__ = ["AI_AVAILABLE", "CharacterAIConfig"]
