# Milvus Integration

Semantic vector search for characters, NPCs, story files, and wiki lore.
This is an **optional** feature - the system works fully without it,
falling back to keyword-based retrieval.

## What It Does

When enabled, every character JSON, NPC JSON, story Markdown file, and
wiki page is chunked and embedded as a vector. At query time the
`SemanticRetriever` converts the user prompt to a vector and does a cosine
similarity search to pull the most relevant context into the AI prompt.

| Data type | Collection | Fallback (no Milvus) |
|-----------|-----------|----------------------|
| Characters | `dnd_characters` | Keyword scan of JSON files |
| NPCs | `dnd_npcs` | `npc_lookup_helper.load_relevant_npcs_for_prompt` |
| Story files | `dnd_story_chunks` | Not retrieved |
| Wiki lore | `dnd_wiki_pages` | Not retrieved |

---

## Setup

### 1. Start Milvus via DDEV

Milvus runs as a DDEV sidecar service alongside Drupal. No separate Docker
Compose file or manual startup is needed.

```bash
cd drupal-cms
ddev start
```

DDEV automatically starts the Milvus standalone container defined in
`.ddev/docker-compose.milvus.yaml`. The companion `.ddev/embedEtcd.yaml`
file configures the embedded etcd server that Milvus uses internally for
metadata storage. Both files must be present in `.ddev/`. Milvus will be
reachable at `localhost:19530` from the host and at `milvus:19530` from
other DDEV containers.

Milvus takes up to 90 seconds to become healthy on first start. You can
check it with:

```bash
ddev milvus-status
```

### 2. Install pymilvus

```bash
pip install pymilvus>=2.4.0
```

Or just re-run requirements:

```bash
pip install -r requirements.txt
```

### 3. Configure the connection

Add to `game_data/config.json` under the `"milvus"` key, or set environment
variables:

```json
{
  "milvus": {
    "enabled": true,
    "host": "localhost",
    "port": 19530,
    "collection_prefix": "dnd",
    "embedding_model": "text-embedding-3-small",
    "embedding_dim": 1536,
    "top_k": 5,
    "similarity_threshold": 0.7
  }
}
```

Environment variable equivalents:

```env
MILVUS_ENABLED=true
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_COLLECTION_PREFIX=dnd
MILVUS_EMBEDDING_MODEL=text-embedding-3-small
MILVUS_EMBEDDING_DIM=1536
MILVUS_TOP_K=5
MILVUS_SIMILARITY_THRESHOLD=0.7
```

`MILVUS_EMBEDDING_MODEL` must be a model your AI provider exposes through the
OpenAI-compatible embeddings endpoint (`POST /v1/embeddings`).

### 4. Build the index

```bash
python3 dnd_consultant.py --reindex
```

This walks every file in `game_data/characters/`, `game_data/npcs/`, and
`game_data/campaigns/` and upserts embeddings. Expected output:

```
[INFO] [Milvus] Reindex complete. 370 total chunks inserted.
```

---

## Verification

### Check connection and entity counts

```bash
python3 dnd_consultant.py --milvus-status
```

Expected output when healthy:

```
[INFO] Milvus connected at localhost:19530
[INFO]   dnd_characters: 42 entities
[INFO]   dnd_npcs: 18 entities
[INFO]   dnd_story_chunks: 310 entities
[INFO]   dnd_wiki_pages: 0 entities
```

If Milvus is not reachable you will see:

```
[WARNING] Milvus is not reachable.
```

The application still starts and functions normally - semantic retrieval
falls back to the keyword path automatically.

### Run the AI test suite

```bash
python3 tests/run_all_tests.py ai
```

All 9 AI tests run without a live Milvus instance (pymilvus is mocked).

---

## Visual Inspection (Attu GUI)

Attu is the official Milvus web UI. Run it alongside Milvus:

```bash
docker run -p 8000:3000 \
  -e MILVUS_URL=localhost:19530 \
  zilliz/attu:latest
```

Open `http://localhost:8000`:

- **Collections** tab - browse `dnd_characters`, `dnd_npcs`, etc.
- **Data** tab - inspect individual embedding records and their metadata
- **Search** tab - run manual vector searches with a paste-in vector

Attu also supports management operations (drop collections, import/export).

---

## Incremental Sync

When the CLI saves a character or NPC JSON file, `src/ai/index_sync.py`
automatically deletes the old embeddings for that file and inserts fresh
ones. No manual `--reindex` needed for routine edits.

Only run `--reindex` when:

- Setting up for the first time
- After bulk-importing many files outside the CLI
- After changing `MILVUS_EMBEDDING_MODEL` (vectors become incompatible)

---

## Configuration Reference

| Key | Default | Description |
|-----|---------|-------------|
| `enabled` | `false` | Master switch; `false` = keyword fallback |
| `host` | `""` | Milvus hostname |
| `port` | `19530` | Milvus gRPC port |
| `collection_prefix` | `"dnd"` | Prepended to every collection name |
| `embedding_model` | `""` | Model name for `AIClient.embed()` calls |
| `embedding_dim` | `1536` | Vector dimension (must match model) |
| `top_k` | `5` | Results returned per search |
| `similarity_threshold` | `0.7` | Minimum cosine score to keep a result |

### Common embedding models and dimensions

| Model | `embedding_dim` |
|-------|----------------|
| `text-embedding-3-small` (OpenAI) | 1536 |
| `text-embedding-3-large` (OpenAI) | 3072 |
| `nomic-embed-text` (Ollama) | 768 |
| `mxbai-embed-large` (Ollama) | 1024 |

If you change `embedding_model` after initial indexing, run `--reindex` to
regenerate all vectors with the new model.

---

## Troubleshooting

### `pymilvus not installed`

```bash
pip install pymilvus>=2.4.0
```

Milvus integration is disabled silently when the library is absent.

### `Could not connect to Milvus`

- Verify DDEV is running: `ddev status` from `drupal-cms/`
- Check the Milvus container: `docker ps | grep milvus`
- Milvus standalone takes up to 90 seconds to become healthy after first start
- Restart the service: `ddev restart`

### `collection_name already exists with different schema`

Drop all collections with:

```python
from src.ai.milvus_client import MilvusClient
client = MilvusClient()
client.connect()
client.delete_collections()
client.disconnect()
```

Then re-run `--reindex`.

### Zero results from semantic search

- Check `similarity_threshold` - try lowering to `0.5`
- Verify the index is populated (`--milvus-status` should show non-zero counts)
- Ensure `MILVUS_EMBEDDING_MODEL` matches the model used during reindex

### Milvus container exits immediately on `ddev restart`

This is caused by a corrupt or missing `.ddev/embedEtcd.yaml`. The file must
exist and the `initial-cluster` URL must match `advertise-peer-urls`:

```yaml
listen-peer-urls: http://0.0.0.0:2380
advertise-peer-urls: http://localhost:2380
listen-client-urls: http://0.0.0.0:2379
advertise-client-urls: http://localhost:2379
initial-cluster: default=http://localhost:2380
initial-cluster-state: new
initial-cluster-token: mvector
```

Re-create the file at `.ddev/embedEtcd.yaml` with the contents above, then
run `ddev restart`.
