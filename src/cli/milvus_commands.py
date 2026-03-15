"""
CLI commands for Milvus index management.

Provides run_reindex() and run_milvus_status() which are invoked by the
--reindex and --milvus-status flags in dnd_consultant.py.
"""

from pathlib import Path
from typing import Any, Dict

from src.ai.embedding_pipeline import EmbeddingPipeline
from src.ai.milvus_client import MilvusClient
from src.ai.milvus_collections import COLLECTIONS
from src.config.config_loader import load_config
from src.utils.file_io import load_json_file
from src.utils.path_utils import get_characters_dir, get_npcs_dir
from src.utils.terminal_display import print_error, print_info, print_warning


def run_reindex() -> None:
    """Rebuild all Milvus collections from game_data files on disk.

    Reads every character JSON, NPC JSON, and story Markdown file and
    replaces their existing embeddings with freshly generated ones.
    Exits early with a warning when Milvus is disabled or unreachable.
    """
    cfg = load_config().milvus
    if not cfg.enabled:
        print_warning("Milvus is disabled (MILVUS_ENABLED=false). Nothing to index.")
        return

    client = MilvusClient()
    if not client.connect():
        print_error("Could not connect to Milvus. Check MILVUS_HOST / MILVUS_PORT.")
        return

    pipeline = EmbeddingPipeline()

    # Ensure all collections exist
    for name, schema in COLLECTIONS.items():
        client.ensure_collection(name, schema)

    total = 0

    # Index characters
    for json_file in Path(get_characters_dir()).glob("*.json"):
        data: Dict[str, Any] = load_json_file(str(json_file)) or {}
        data["_source_file"] = str(json_file)
        client.delete_by_source("characters", "source_file", str(json_file))
        total += client.insert("characters", pipeline.embed_character(data))

    # Index NPCs
    for json_file in Path(get_npcs_dir()).glob("*.json"):
        data = load_json_file(str(json_file)) or {}
        data["_source_file"] = str(json_file)
        client.delete_by_source("npcs", "source_file", str(json_file))
        total += client.insert("npcs", pipeline.embed_npc(data))

    # Index story files
    for story_file in Path("game_data/campaigns").glob("**/*.md"):
        rows = pipeline.embed_story_file(str(story_file))
        total += client.insert("story_chunks", rows)

    client.disconnect()
    print_info(f"[Milvus] Reindex complete. {total} total chunks inserted.")


def run_milvus_status() -> None:
    """Print Milvus connection health and per-collection entity counts."""
    cfg = load_config().milvus
    client = MilvusClient()
    if not client.connect() or not client.is_healthy():
        print_warning("Milvus is not reachable.")
        return

    print_info(f"Milvus connected at {cfg.host}:{cfg.port}")
    for base in COLLECTIONS:
        col = client.get_collection(base)
        count = col.num_entities if col is not None else 0
        print_info(f"  {client.collection_name(base)}: {count} entities")

    client.disconnect()
