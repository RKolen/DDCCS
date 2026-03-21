"""
Milvus client and collection management.

Wraps pymilvus with connection lifecycle, health checks, and collection
bootstrap. All callers should check is_healthy() before using
insert/search/delete operations.
"""

from typing import Any, Dict, List, Optional

from src.ai.milvus_collections import COLLECTIONS
from src.config.config_loader import load_config
from src.utils.terminal_display import print_info, print_warning

try:
    from pymilvus import (
        Collection,
        CollectionSchema,
        DataType,
        FieldSchema,
        connections,
        utility,
    )

    PYMILVUS_AVAILABLE = True
except ImportError:
    print_warning("pymilvus not installed. Milvus integration disabled.")
    print("  Install with: pip install pymilvus")
    PYMILVUS_AVAILABLE = False

# Default output fields per collection used in search results.
_OUTPUT_FIELDS: Dict[str, List[str]] = {
    "characters": ["character_name", "chunk_text", "chunk_type", "source_file"],
    "npcs": ["npc_name", "location", "chunk_text", "source_file"],
    "story_chunks": ["campaign_name", "story_file", "chunk_index", "chunk_text"],
    "wiki_pages": ["page_url", "page_title", "chunk_text", "cached_at"],
}


class MilvusClient:
    """Manages connection to Milvus and ensures collections exist.

    Attributes:
        connected: True once the connection is confirmed healthy.
    """

    def __init__(self) -> None:
        cfg = load_config().milvus
        self._host = cfg.host
        self._port = cfg.port
        self._prefix = cfg.collection_prefix
        self._dim = cfg.embedding.dim
        self.connected: bool = False

    def connect(self) -> bool:
        """Open a connection to Milvus.

        Returns:
            True on success, False when unavailable or pymilvus not installed.
        """
        if not PYMILVUS_AVAILABLE:
            return False
        try:
            connections.connect(
                alias="default",
                host=self._host,
                port=str(self._port),
            )
            self.connected = True
            return True
        except (OSError, RuntimeError):
            self.connected = False
            return False

    def disconnect(self) -> None:
        """Close connection if open."""
        if not PYMILVUS_AVAILABLE or not self.connected:
            return
        try:
            connections.disconnect("default")
        except (OSError, RuntimeError):
            pass
        self.connected = False

    def is_available(self) -> bool:
        """Check whether Milvus is reachable.

        Returns:
            True if connected and healthy, False otherwise.
        """
        return self.is_healthy()

    def is_healthy(self) -> bool:
        """Ping Milvus and return True when reachable.

        Returns:
            True if the server responds, False otherwise.
        """
        if not PYMILVUS_AVAILABLE or not self.connected:
            return False
        try:
            return bool(utility.get_server_version())
        except (OSError, RuntimeError):
            self.connected = False
            return False

    def collection_name(self, base: str) -> str:
        """Return a fully qualified collection name.

        Args:
            base: Unqualified name such as "characters".

        Returns:
            Prefixed name such as "dnd_characters".
        """
        return f"{self._prefix}_{base}"

    def ensure_collection(
        self, base: str, schema_def: Dict[str, Any]
    ) -> Optional[Any]:
        """Create a collection from a schema dict if it does not yet exist.

        Args:
            base: Unqualified collection name (e.g. "characters").
            schema_def: Entry from COLLECTIONS in milvus_collections.py.

        Returns:
            pymilvus Collection object, or None when unavailable.
        """
        if not self.connected:
            return None
        name = self.collection_name(base)
        if utility.has_collection(name):
            col = Collection(name)
            col.load()
            return col
        fields = []
        for fld in schema_def["fields"]:
            dtype = getattr(DataType, fld["dtype"])
            kwargs: Dict[str, Any] = {}
            if fld["dtype"] == "VARCHAR":
                kwargs["max_length"] = fld["max_length"]
            if fld["dtype"] == "FLOAT_VECTOR":
                kwargs["dim"] = self._dim
            fields.append(
                FieldSchema(
                    name=fld["name"],
                    dtype=dtype,
                    is_primary=fld.get("is_primary", False),
                    auto_id=fld.get("auto_id", False),
                    **kwargs,
                )
            )
        schema = CollectionSchema(
            fields=fields, description=schema_def["description"]
        )
        collection = Collection(name=name, schema=schema)
        idx = schema_def.get("index", {})
        collection.create_index(
            field_name="embedding",
            index_params={
                "metric_type": idx.get("metric_type", "COSINE"),
                "index_type": idx.get("index_type", "IVF_FLAT"),
                "params": {"nlist": idx.get("nlist", 128)},
            },
        )
        collection.load()
        print_info(f"[Milvus] Created collection: {name}")
        return collection

    def create_collections(self) -> None:
        """Create all standard D&D collections.

        Delegates to ensure_collection for each entry in COLLECTIONS.
        """
        for base, schema_def in COLLECTIONS.items():
            self.ensure_collection(base, schema_def)

    def delete_collections(self) -> None:
        """Drop all standard D&D collections.

        Used for full re-index or test teardown.
        """
        if not self.connected:
            return
        for base in COLLECTIONS:
            name = self.collection_name(base)
            if utility.has_collection(name):
                utility.drop_collection(name)
                print_info(f"[Milvus] Dropped collection: {name}")

    def get_collection(self, base: str) -> Optional[Any]:
        """Return a loaded Collection or None when unavailable.

        Args:
            base: Unqualified collection name.

        Returns:
            Loaded pymilvus Collection or None.
        """
        if not self.connected:
            return None
        name = self.collection_name(base)
        if not utility.has_collection(name):
            return None
        col = Collection(name)
        col.load()
        return col

    def insert(self, base: str, rows: List[Dict[str, Any]]) -> int:
        """Bulk-insert rows into a collection.

        The list of dicts is transposed into the column-oriented format
        required by pymilvus.

        Args:
            base: Unqualified collection name.
            rows: List of dicts whose keys match the collection schema.

        Returns:
            Number of rows inserted, 0 on failure.
        """
        col = self.get_collection(base)
        if col is None or not rows:
            return 0
        columns: Dict[str, List[Any]] = {k: [] for k in rows[0]}
        for row in rows:
            for key, value in row.items():
                columns[key].append(value)
        col.insert(list(columns.values()))
        col.flush()
        return len(rows)

    def search(
        self,
        base: str,
        query_vector: List[float],
        top_k: int = 5,
        expr: str = "",
    ) -> List[Dict[str, Any]]:
        """Perform a cosine-similarity vector search.

        Output fields are determined automatically from the collection name.
        Use _OUTPUT_FIELDS to see the per-collection field sets.

        Args:
            base: Unqualified collection name.
            query_vector: Embedding of the query text.
            top_k: Maximum number of results to return.
            expr: Optional Milvus boolean expression filter.

        Returns:
            List of result dicts each including a "score" key.
        """
        col = self.get_collection(base)
        if col is None:
            return []
        output_fields = _OUTPUT_FIELDS.get(base, [])
        params = {"metric_type": "COSINE", "params": {"nprobe": 16}}
        results = col.search(
            data=[query_vector],
            anns_field="embedding",
            param=params,
            limit=top_k,
            expr=expr or None,
            output_fields=output_fields,
        )
        hits: List[Dict[str, Any]] = []
        for hit in results[0]:
            record: Dict[str, Any] = {
                field: hit.entity.get(field) for field in output_fields
            }
            record["score"] = hit.score
            hits.append(record)
        return hits

    def delete_by_source(
        self, base: str, source_field: str, source_value: str
    ) -> None:
        """Remove all rows matching a source field value.

        Used to purge stale embeddings before re-indexing a file.

        Args:
            base: Unqualified collection name.
            source_field: Field name to filter on (e.g. "source_file").
            source_value: Value to match.
        """
        col = self.get_collection(base)
        if col is None:
            return
        col.delete(f'{source_field} == "{source_value}"')
        col.flush()
