"""
Incremental embedding sync triggered on JSON writes.

Call sync_on_save() after saving a character or NPC JSON file to keep
Milvus embeddings current without modifying the low-level file_io utilities.
"""

from pathlib import Path
from typing import Any, Dict

from src.ai.embedding_pipeline import EmbeddingPipeline
from src.ai.milvus_client import MilvusClient
from src.ai.milvus_collections import COLLECTIONS
from src.config.config_loader import load_config
from src.utils.terminal_display import print_info


def sync_on_save(file_path: str, data: Dict[str, Any]) -> None:
    """Re-index a JSON file in Milvus after it is saved.

    Determines the data type from the parent directory name ("characters"
    or "npcs") and replaces the existing embeddings for that file before
    inserting fresh ones. Silently returns when Milvus is disabled or
    unreachable.

    Args:
        file_path: Path to the file that was just written.
        data: The data dict that was saved (will have _source_file added).
    """
    cfg = load_config().milvus
    if not cfg.enabled:
        return

    client = MilvusClient()
    if not client.connect():
        return

    pipeline = EmbeddingPipeline()
    path = Path(file_path)
    parent = path.parent.name

    data["_source_file"] = str(path)

    if parent == "characters":
        client.ensure_collection("characters", COLLECTIONS["characters"])
        client.delete_by_source("characters", "source_file", str(path))
        rows = pipeline.embed_character(data)
        inserted = client.insert("characters", rows)
        print_info(f"[Milvus] Re-indexed {path.name}: {inserted} chunks")

    elif parent == "npcs":
        client.ensure_collection("npcs", COLLECTIONS["npcs"])
        client.delete_by_source("npcs", "source_file", str(path))
        rows = pipeline.embed_npc(data)
        inserted = client.insert("npcs", rows)
        print_info(f"[Milvus] Re-indexed {path.name}: {inserted} chunks")

    client.disconnect()
