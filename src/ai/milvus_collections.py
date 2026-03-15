"""
Milvus collection definitions for D&D data types.

This module defines the collection schemas for storing embeddings in Milvus.
"""

from typing import Dict, Any


COLLECTIONS: Dict[str, Dict[str, Any]] = {
    "characters": {
        "description": "Character profile embeddings",
        "fields": [
            {"name": "id", "dtype": "INT64", "is_primary": True, "auto_id": True},
            {"name": "character_name", "dtype": "VARCHAR", "max_length": 100},
            {"name": "source_file", "dtype": "VARCHAR", "max_length": 512},
            {"name": "chunk_text", "dtype": "VARCHAR", "max_length": 2048},
            {"name": "chunk_type", "dtype": "VARCHAR", "max_length": 50},
            {"name": "embedding", "dtype": "FLOAT_VECTOR", "dim": 1536},
        ],
        "index": {"metric_type": "COSINE", "index_type": "IVF_FLAT", "nlist": 128},
    },
    "npcs": {
        "description": "NPC profile embeddings",
        "fields": [
            {"name": "id", "dtype": "INT64", "is_primary": True, "auto_id": True},
            {"name": "npc_name", "dtype": "VARCHAR", "max_length": 100},
            {"name": "location", "dtype": "VARCHAR", "max_length": 200},
            {"name": "chunk_text", "dtype": "VARCHAR", "max_length": 2048},
            {"name": "embedding", "dtype": "FLOAT_VECTOR", "dim": 1536},
        ],
        "index": {"metric_type": "COSINE", "index_type": "IVF_FLAT", "nlist": 128},
    },
    "story_chunks": {
        "description": "Story file paragraph-level embeddings",
        "fields": [
            {"name": "id", "dtype": "INT64", "is_primary": True, "auto_id": True},
            {"name": "campaign_name", "dtype": "VARCHAR", "max_length": 200},
            {"name": "story_file", "dtype": "VARCHAR", "max_length": 512},
            {"name": "chunk_index", "dtype": "INT64"},
            {"name": "chunk_text", "dtype": "VARCHAR", "max_length": 4096},
            {"name": "embedding", "dtype": "FLOAT_VECTOR", "dim": 1536},
        ],
        "index": {"metric_type": "COSINE", "index_type": "IVF_FLAT", "nlist": 256},
    },
    "wiki_pages": {
        "description": "Cached wiki page sentence embeddings",
        "fields": [
            {"name": "id", "dtype": "INT64", "is_primary": True, "auto_id": True},
            {"name": "page_url", "dtype": "VARCHAR", "max_length": 1024},
            {"name": "page_title", "dtype": "VARCHAR", "max_length": 512},
            {"name": "chunk_text", "dtype": "VARCHAR", "max_length": 4096},
            {"name": "cached_at", "dtype": "INT64"},
            {"name": "embedding", "dtype": "FLOAT_VECTOR", "dim": 1536},
        ],
        "index": {"metric_type": "COSINE", "index_type": "IVF_FLAT", "nlist": 256},
    },
}
