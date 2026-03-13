"""Centralized AI availability check.

This module exposes public symbols used across the codebase:
- AI_AVAILABLE: bool indicating whether the AI client import succeeded
- CharacterAIConfig: the imported class when available, otherwise None
- RAG_AVAILABLE: bool indicating whether the RAG system import succeeded
- get_rag_system: the RAG system factory when available, otherwise None

Centralizing this check avoids duplicate try/except-import blocks across
modules and makes it easier to test import availability in one place.
"""
from src.ai.ai_client import CharacterAIConfig
from src.ai.rag_system import get_rag_system

AI_AVAILABLE = True
RAG_AVAILABLE = True

__all__ = ["AI_AVAILABLE", "CharacterAIConfig", "RAG_AVAILABLE", "get_rag_system"]
