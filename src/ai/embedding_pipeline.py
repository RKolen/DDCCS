"""
Embedding generation and management for D&D data types.

This module handles the creation of vector embeddings for characters, NPCs,
story content, and wiki pages using the configured AI provider.
"""

import re
import time
from pathlib import Path
from typing import Any, Dict, List

from src.ai.ai_client import AIClient
from src.config.config_loader import load_config
from src.utils.file_io import read_text_file
from src.utils.string_utils import truncate_text

# Character fields that carry the most semantic signal, ordered by priority.
_CHARACTER_CHUNK_FIELDS = [
    ("background", "background"),
    ("personality_traits", "personality"),
    ("ideals", "ideals"),
    ("bonds", "bonds"),
    ("flaws", "flaws"),
    ("backstory", "backstory"),
    ("notes", "notes"),
    ("class_features", "class_features"),
]

# Maximum characters per chunk before truncation.
_MAX_CHUNK_CHARS = 1500
# Target paragraph size for story chunking (characters).
_STORY_CHUNK_TARGET = 800
# Minimum paragraph length before merging with the next paragraph.
_MIN_PARAGRAPH_CHARS = 80


class EmbeddingPipeline:
    """Generates embeddings using the configured AI provider.

    Delegates to AIClient.embed() for the actual API call so that embeddings
    share the same base_url and api_key as chat completions.
    """

    def __init__(self) -> None:
        cfg = load_config()
        self._client: AIClient = AIClient()
        self._model: str = cfg.milvus.embedding_model

    # ------------------------------------------------------------------
    # Core embedding call
    # ------------------------------------------------------------------

    def embed_text(self, text: str) -> List[float]:
        """Generate an embedding vector for a single text string.

        Args:
            text: Plain text to embed.

        Returns:
            List of floats representing the embedding, or [] on failure.
        """
        clean = text.strip()
        if not clean:
            return []
        try:
            return self._client.embed(clean, model=self._model)
        except RuntimeError:
            return []

    # ------------------------------------------------------------------
    # Per-type chunkers
    # ------------------------------------------------------------------

    def embed_character(self, character_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Produce one embedding chunk per semantic field of a character.

        The character name is prepended to every chunk so queries that
        mention the character name surface all their chunks.

        Args:
            character_data: Parsed character JSON dict.

        Returns:
            List of row dicts ready for MilvusClient.insert("characters").
        """
        name = character_data.get("name", "unknown")
        source = character_data.get("_source_file", "")
        rows: List[Dict[str, Any]] = []

        # One chunk for the core stat block (class / level / race)
        stat_parts = [
            f"Name: {name}",
            f"Class: {character_data.get('class', '')}",
            f"Race: {character_data.get('race', '')}",
            f"Level: {character_data.get('level', '')}",
        ]
        stat_text = " | ".join(p for p in stat_parts if p.split(": ", 1)[1])
        if stat_text:
            vec = self.embed_text(stat_text)
            if vec:
                rows.append({
                    "character_name": name,
                    "source_file": source,
                    "chunk_text": stat_text,
                    "chunk_type": "stat_block",
                    "embedding": vec,
                })

        # One chunk per narrative field
        for field_key, chunk_type in _CHARACTER_CHUNK_FIELDS:
            raw = character_data.get(field_key)
            if not raw:
                continue
            if isinstance(raw, list):
                text = "; ".join(str(item) for item in raw)
            else:
                text = str(raw)
            text = truncate_text(f"{name} - {text}", _MAX_CHUNK_CHARS)
            vec = self.embed_text(text)
            if vec:
                rows.append({
                    "character_name": name,
                    "source_file": source,
                    "chunk_text": text,
                    "chunk_type": chunk_type,
                    "embedding": vec,
                })

        return rows

    def embed_npc(self, npc_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Produce embedding chunks for an NPC profile.

        Args:
            npc_data: Parsed NPC JSON dict.

        Returns:
            List of row dicts ready for MilvusClient.insert("npcs").
        """
        name = npc_data.get("name", "unknown")
        location = npc_data.get("location", "")
        source = npc_data.get("_source_file", "")
        rows: List[Dict[str, Any]] = []

        # Core identity chunk
        parts = [
            f"NPC: {name}",
            f"Race: {npc_data.get('race', '')}",
            f"Role: {npc_data.get('role', npc_data.get('occupation', ''))}",
            f"Location: {location}",
        ]
        identity = " | ".join(p for p in parts if p.split(": ", 1)[1])
        if identity:
            vec = self.embed_text(identity)
            if vec:
                rows.append({
                    "npc_name": name,
                    "location": location,
                    "chunk_text": identity,
                    "embedding": vec,
                    "source_file": source,
                })

        # Personality / description chunks
        for field in ("description", "personality", "background", "notes"):
            text = npc_data.get(field, "")
            if not text:
                continue
            combined = truncate_text(f"{name}: {text}", _MAX_CHUNK_CHARS)
            vec = self.embed_text(combined)
            if vec:
                rows.append({
                    "npc_name": name,
                    "location": location,
                    "chunk_text": combined,
                    "embedding": vec,
                    "source_file": source,
                })

        return rows

    def embed_story_file(self, story_path: str) -> List[Dict[str, Any]]:
        """Split a story Markdown file into paragraphs and embed each.

        Paragraphs shorter than _MIN_PARAGRAPH_CHARS are merged with the
        next to avoid very small, low-signal chunks.

        Args:
            story_path: Path to a .md story file.

        Returns:
            List of row dicts ready for MilvusClient.insert("story_chunks").
        """
        path = Path(story_path)
        campaign_name = path.parent.name
        story_file = path.name

        raw = read_text_file(story_path)
        if not raw:
            return []

        # Split on blank lines, merge very short fragments
        paragraphs: List[str] = []
        buffer = ""
        for para in re.split(r"\n{2,}", raw.strip()):
            para = para.strip()
            if not para:
                continue
            buffer = (buffer + " " + para).strip() if buffer else para
            if len(buffer) >= _MIN_PARAGRAPH_CHARS:
                paragraphs.append(buffer)
                buffer = ""
        if buffer:
            paragraphs.append(buffer)

        rows: List[Dict[str, Any]] = []
        for idx, para in enumerate(paragraphs):
            text = truncate_text(para, _MAX_CHUNK_CHARS)
            vec = self.embed_text(text)
            if vec:
                rows.append({
                    "campaign_name": campaign_name,
                    "story_file": story_file,
                    "chunk_index": idx,
                    "chunk_text": text,
                    "embedding": vec,
                })

        return rows

    def embed_wiki_page(self, page_text: str, url: str) -> List[Dict[str, Any]]:
        """Split a wiki page into sentence-level chunks and embed.

        Uses _STORY_CHUNK_TARGET characters as the soft merge target so each
        chunk carries enough context to be semantically useful.

        Args:
            page_text: Plain text content of a wiki page.
            url: Source URL used as a unique identifier in the collection.

        Returns:
            List of row dicts ready for MilvusClient.insert("wiki_pages").
        """
        title_match = re.search(r"^#+ (.+)$", page_text, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else url

        sentences = re.split(r"(?<=[.!?])\s+", page_text.strip())
        chunks: List[str] = []
        buffer = ""
        for sentence in sentences:
            candidate = (buffer + " " + sentence).strip() if buffer else sentence
            if len(candidate) >= _STORY_CHUNK_TARGET:
                if buffer:
                    chunks.append(buffer)
                buffer = sentence
            else:
                buffer = candidate
        if buffer:
            chunks.append(buffer)

        now = int(time.time())
        rows: List[Dict[str, Any]] = []
        for chunk in chunks:
            text = truncate_text(chunk, _MAX_CHUNK_CHARS)
            vec = self.embed_text(text)
            if vec:
                rows.append({
                    "page_url": url,
                    "page_title": title,
                    "chunk_text": text,
                    "cached_at": now,
                    "embedding": vec,
                })

        return rows
