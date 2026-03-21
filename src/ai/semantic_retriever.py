"""
Semantic retrieval layer backed by Milvus with JSON fallback.

This module provides semantic search capabilities for retrieving contextually
relevant data for AI prompt construction. When Milvus is unavailable the class
falls back to keyword search using existing helpers.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.ai.embedding_pipeline import EmbeddingPipeline
from src.ai.milvus_client import MilvusClient
from src.config.config_loader import load_config
from src.utils.character_profile_utils import load_character_profile
from src.utils.npc_lookup_helper import load_relevant_npcs_for_prompt
from src.utils.path_utils import get_characters_dir


class SemanticRetriever:
    """Retrieves contextually relevant data for AI prompt construction.

    Falls back to keyword-based retrieval when Milvus is unavailable.
    """

    def __init__(self) -> None:
        cfg = load_config().milvus
        self._top_k = cfg.top_k
        self._threshold = cfg.similarity_threshold
        self._client = MilvusClient()
        self._pipeline = EmbeddingPipeline()
        if cfg.enabled:
            self._client.connect()

    @property
    def _available(self) -> bool:
        """True when Milvus is reachable."""
        return self._client.is_healthy()

    def is_available(self) -> bool:
        """Return True when Milvus is connected and reachable."""
        return self._available

    # ------------------------------------------------------------------
    # Public retrieval API
    # ------------------------------------------------------------------

    def get_relevant_characters(
        self, query: str, top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Return most semantically relevant character profile chunks.

        Args:
            query: Natural language description of the needed context.
            top_k: Override default result count.

        Returns:
            List of result dicts with keys: character_name, chunk_text,
            chunk_type, source_file, score.
        """
        if not self._available:
            return self._fallback_characters(query)
        vec = self._pipeline.embed_text(query)
        if not vec:
            return []
        hits = self._client.search(
            "characters",
            vec,
            top_k=top_k or self._top_k,
        )
        return self._filter_by_threshold(hits)

    def get_relevant_npcs(
        self,
        query: str,
        location: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Return NPCs relevant to the current scene.

        When a location is supplied it is appended to the query before
        embedding so nearby location embeddings are boosted naturally.

        Args:
            query: Scene description or prompt excerpt.
            location: Optional current scene location name.
            top_k: Override default result count.

        Returns:
            List of result dicts with keys: npc_name, location,
            chunk_text, source_file, score.
        """
        if not self._available:
            return self._fallback_npcs(query, location)
        combined = f"{query} location: {location}" if location else query
        vec = self._pipeline.embed_text(combined)
        if not vec:
            return []
        expr = f'location == "{location}"' if location else ""
        hits = self._client.search(
            "npcs",
            vec,
            top_k=top_k or self._top_k,
            expr=expr,
        )
        return self._filter_by_threshold(hits)

    def get_relevant_story_context(
        self,
        query: str,
        campaign_name: str,
        top_k: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Return story chunks relevant to a prompt.

        Results are scoped to the given campaign to prevent cross-campaign
        contamination.

        Args:
            query: Current story prompt or continuation seed.
            campaign_name: Name of the active campaign folder.
            top_k: Override default result count.

        Returns:
            List of result dicts with keys: campaign_name, story_file,
            chunk_index, chunk_text, score.
        """
        if not self._available:
            return []
        vec = self._pipeline.embed_text(query)
        if not vec:
            return []
        hits = self._client.search(
            "story_chunks",
            vec,
            top_k=top_k or self._top_k,
            expr=f'campaign_name == "{campaign_name}"',
        )
        return self._filter_by_threshold(hits)

    def get_relevant_lore(
        self, query: str, top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Return relevant wiki / lore content chunks.

        Args:
            query: Topic or phrase to search for in cached wiki content.
            top_k: Override default result count.

        Returns:
            List of result dicts with keys: page_url, page_title,
            chunk_text, cached_at, score.
        """
        if not self._available:
            return []
        vec = self._pipeline.embed_text(query)
        if not vec:
            return []
        hits = self._client.search(
            "wiki_pages",
            vec,
            top_k=top_k or self._top_k,
        )
        return self._filter_by_threshold(hits)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _filter_by_threshold(
        self, hits: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Drop results below the configured similarity threshold.

        Args:
            hits: Raw search results from MilvusClient.search().

        Returns:
            Filtered list containing only results meeting the threshold.
        """
        return [h for h in hits if h.get("score", 0) >= self._threshold]

    def _fallback_characters(self, query: str) -> List[Dict[str, Any]]:
        """Keyword fallback: score all character files by word overlap.

        Args:
            query: Search query.

        Returns:
            Top-k character dicts scored by keyword overlap.
        """
        results: List[Dict[str, Any]] = []
        chars_dir = Path(get_characters_dir())
        query_words = set(query.lower().split())
        for json_file in chars_dir.glob("*.json"):
            try:
                profile = load_character_profile(json_file.stem)
                if not profile:
                    continue
                text = json.dumps(profile).lower()
                score = sum(1 for w in query_words if w in text) / max(len(query_words), 1)
                if score > 0:
                    results.append({
                        "character_name": profile.get("name", json_file.stem),
                        "chunk_text": profile.get("background", ""),
                        "chunk_type": "fallback",
                        "source_file": str(json_file),
                        "score": score,
                    })
            except (OSError, ValueError):
                continue
        results.sort(key=lambda r: r["score"], reverse=True)
        return results[: self._top_k]

    def _fallback_npcs(
        self, query: str, location: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Delegate to existing npc_lookup_helper keyword matching.

        Args:
            query: Scene description or prompt excerpt.
            location: Optional location filter appended to the query.

        Returns:
            Matched NPC dicts wrapped in the standard result schema.
        """
        effective_query = f"{query} location:{location}" if location else query
        loaded = load_relevant_npcs_for_prompt(effective_query, os.getcwd())
        return [
            {
                "npc_name": n.get("name", ""),
                "location": n.get("location", ""),
                "chunk_text": n.get("description", ""),
                "source_file": "",
                "score": 0.5,
            }
            for n in loaded
        ]
