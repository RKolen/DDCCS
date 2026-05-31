# RAG (Retrieval-Augmented Generation) Integration Guide

## Overview

The D&D Character Consultant System includes RAG support, allowing AI to
fetch and integrate accurate campaign-setting lore from wiki sources when
generating stories and handling History checks.

**Architecture:** Python = engine, Drupal = truth, Gatsby/React = looks.

- Wiki pages are fetched by the Python engine and **cached in Drupal** as
  `wiki_cache` nodes (JSON:API). No local SQLite or JSON files.
- Taxonomy terms (locations, factions, creature types, lore tags) carry
  `field_lore_context` (pre-written lore) and `field_source_url` (wiki URL for
  auto-fetch). These are indexed by Milvus for semantic RAG injection.

## Features

### 1. Wiki Integration for Story Generation

- AI automatically searches campaign wikis for relevant lore
- Enriches narratives with accurate location descriptions, history, and context
- Maintains consistency with official campaign settings

### 2. History Check Enhancement

- Characters who make successful History checks receive wiki-sourced information
- Detail level scales with check result (10-14: basic, 15-19: detailed, 20+: comprehensive)
- DMs can look up lore instantly

### 3. Drupal-backed Wiki Cache

Wiki HTTP responses are cached as `wiki_cache` Drupal nodes via JSON:API.
The cache degrades gracefully when Drupal is not reachable — the Python engine
falls through to live HTTP fetches with no data loss.

Fields on `wiki_cache` nodes:

| Field                   | Type      | Description                             |
| ----------------------- | --------- | --------------------------------------- |
| `title`                 | string    | MD5 hash of the URL (cache key)         |
| `field_wiki_url`        | string    | Original source URL                     |
| `field_wiki_fetched_at` | decimal   | Unix timestamp of last fetch            |
| `field_wiki_content`    | text_long | Serialized JSON of parsed page sections |

Cache TTL is enforced at read time via `field_wiki_fetched_at`. Expired entries
are deleted and re-fetched on next access.

### 4. Taxonomy Term Lore Fields

Every taxonomy vocabulary used in RAG (locations, factions, creature_types,
lore_tags) has two shared fields:

| Field                 | Type      | Description                                |
| --------------------- | --------- | ------------------------------------------ |
| `field_lore_context`  | text_long | Pre-written lore injected into AI prompts  |
| `field_source_url`    | string    | Wiki URL; triggers auto-fetch when set     |

These fields are indexed by Milvus for semantic lore retrieval. The
`field_lore_context` value is used directly when Milvus returns the term
as a relevant result.

### 5. Multiple Campaign Setting Support

- **Critical Role (Exandria)**: `https://criticalrole.fandom.com/wiki`
- **Forgotten Realms**: `https://forgottenrealms.fandom.com/wiki`
- **Custom wikis**: Any MediaWiki or Fandom.com wiki
- **Homebrew**: Point to your own wiki

## Requirements

### Python Packages

```bash
pip install -r requirements.txt
```

Required packages: `requests`, `beautifulsoup4` (web scraping and HTML parsing).

### Drupal CMS

Wiki cache requires the Drupal CMS component (`drupal-cms/`) running via DDEV.
Configure `DRUPAL_BASE_URL`, `DRUPAL_USER`, and `DRUPAL_PASSWORD` in `.env`.

When Drupal is not configured or not reachable, wiki pages are fetched live
on every request (no caching — degrades gracefully).

## Configuration

### 1. Enable RAG in `.env`

```properties
# Enable RAG system
RAG_ENABLED=true

# Wiki base URL for your campaign setting (lore: locations, NPCs, history)
RAG_WIKI_BASE_URL=https://criticalrole.fandom.com/wiki

# Rules wiki URL (game mechanics: spells, abilities, items)
RAG_RULES_BASE_URL=https://5thsrd.org

# Cache TTL in seconds (default: 7 days). Enforced in Drupal wiki_cache nodes.
RAG_CACHE_TTL=604800

# Search settings
RAG_SEARCH_DEPTH=3       # How many wiki links to follow (1-5)
RAG_MIN_RELEVANCE=0.5    # Minimum relevance score (0.0-1.0)
```

### 2. Configure Drupal Wiki Cache

```properties
DRUPAL_BASE_URL=https://drupal-cms.ddev.site
DRUPAL_USER=admin
DRUPAL_PASSWORD=your-password
```

The `wiki_cache` content type and all required fields are shipped with the
Drupal config in `drupal-cms/config/sync/`. Import with:

```bash
ddev drush config:import -y
```

### 3. Choose Your Campaign Setting

The system uses **two separate wikis**:

- **RAG_WIKI_BASE_URL**: Campaign lore (locations, NPCs, history)
- **RAG_RULES_BASE_URL**: Game mechanics (spells, abilities, rules)

```properties
# Your custom lore wiki
RAG_WIKI_BASE_URL=https://your-wiki.com/wiki

# D&D 5e SRD rules wiki (recommended)
RAG_RULES_BASE_URL=https://5thsrd.org
```

## Usage

### In Story Generation

RAG works automatically when generating stories:

```python
from src.dm.dungeon_master import DMConsultant
from src.ai.ai_client import AIClient

ai_client = AIClient()
dm = DMConsultant(workspace_path=".", ai_client=ai_client)

narrative = dm.generate_narrative_content(
    story_prompt="The party arrives in Whitestone, seeking the de Rolo family.",
    characters_present=["Theron", "Mira", "Garrick"],
    style="immersive"
)
```

**What happens behind the scenes:**

1. RAG extracts location names ("Whitestone", "de Rolo")
2. Fetches wiki pages (from Drupal cache, or live if cache miss)
3. Includes relevant lore context in AI prompt
4. AI generates narrative using accurate campaign lore

### For Character History Checks

```python
from src.dm.history_check_helper import handle_history_check

result = handle_history_check(
    topic="Tal'Dorei",
    check_result=18,
    character_name="Elara"
)

if result['success']:
    print(result['information'])
```

### Direct Lore Lookup

```python
from src.dm.history_check_helper import search_lore

lore = search_lore("Whitestone", pages_to_search=["Whitestone", "Tal'Dorei"])
print(lore)
```

### In CLI (Interactive Mode)

```bash
python dnd_consultant.py
```

1. Choose **"2. DM Consultation"**
2. Select **"Generate Story Narrative"**
3. Enter your prompt mentioning locations — RAG enriches the narrative

## File Structure

```text
project/
|-- .env                          # RAG + Drupal configuration
|-- src/
|   |-- ai/
|   |   `-- rag_system.py         # RAGSystem, WikiClient, DrupalWikiCache
|   |-- integration/
|   |   `-- drupal_sync.py        # DrupalSync: get/set/delete wiki_cache nodes
|   `-- dm/
|       |-- dungeon_master.py     # Story generation with RAG
|       `-- history_check_helper.py
|-- drupal-cms/config/sync/
|   |-- node.type.wiki_cache.yml  # wiki_cache content type
|   |-- field.storage.node.field_wiki_url.yml
|   |-- field.storage.node.field_wiki_fetched_at.yml
|   |-- field.storage.node.field_wiki_content.yml
|   |-- field.storage.taxonomy_term.field_lore_context.yml
|   `-- field.storage.taxonomy_term.field_source_url.yml
`-- dnd_consultant.py             # CLI entry point
```

## Cache Management

Wiki cache is stored in Drupal. Manage it via:

### Inspect cache stats via DrupalSync

```python
from src.config.config_loader import load_config
from src.integration.drupal_sync import DrupalSync

config = load_config()
sync = DrupalSync(config.drupal)
count = sync.count_wiki_page_cache()
print(f"Cached pages: {count}")
```

### Delete a single cached page

```python
import hashlib

url = "https://criticalrole.fandom.com/wiki/Whitestone"
url_hash = hashlib.md5(url.encode()).hexdigest()
sync.delete_wiki_page_cache(url_hash)
```

### Force refresh a specific page

Deleting the cache node for a URL causes the next fetch to hit the live wiki
and re-cache the result. Alternatively, use `WikiClient.fetch_page()` with
`force_refresh=True` when available via the RAG system singleton:

```python
from src.ai.rag_system import get_rag_system

rag = get_rag_system()
page = rag.wiki_client.fetch_page("Whitestone", force_refresh=True)
```

## Milvus Semantic Search

When Milvus is enabled, taxonomy term `field_lore_context` values are indexed
and injected into prompts via semantic similarity. This replaces keyword-only
matching for RAG context selection.

Taxonomy terms with `field_source_url` set will have their wiki content
fetched, parsed, and indexed automatically during the reindex run.

### Enable Milvus

```env
MILVUS_ENABLED=true
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_EMBEDDING_MODEL=text-embedding-3-small
MILVUS_EMBEDDING_DIM=1536
```

### Build or rebuild the index

```bash
python3 dnd_consultant.py --reindex
```

Or via DDEV:

```bash
ddev milvus-reindex
```

## Advanced Configuration

### Custom Search Relevance

Adjust relevance scoring weights in `src/ai/rag_system.py`:

```python
# In WikiClient.search_sections()
if query_lower in title:
    score += 2.0   # Title match weight

title_matches = len(query_words & title_words)
score += title_matches * 0.5  # Title word weight

content_matches = len(query_words & content_words)
score += content_matches * 0.1  # Content word weight
```

These magic numbers are candidates for extraction to module-level constants
(deferred from the Step 1 review).

### Taxonomy Term Lore

Pre-written lore on taxonomy terms is the fastest path to accurate RAG context
without live wiki fetches. In Drupal, edit a location, faction, or creature
type term and fill in `field_lore_context`. That text is indexed by Milvus
and injected into prompts when the term is relevant.

## Troubleshooting

### RAG enabled but no lore appearing

Check:

1. `RAG_ENABLED=true` in `.env`
2. `RAG_WIKI_BASE_URL` is set and reachable
3. Drupal is running and credentials are correct (`DRUPAL_BASE_URL` etc.)

### Cache not updating

The cache TTL is set per entry. To force a refresh, delete the `wiki_cache`
node in Drupal admin (`/admin/content`) for the URL you want refreshed.

### "RAG enabled but RAG_WIKI_BASE_URL not set"

Add to `.env`:

```properties
RAG_ENABLED=true
RAG_WIKI_BASE_URL=https://criticalrole.fandom.com/wiki
```

### Wiki pages not being found

1. **Page name spelling** — Wiki page titles are case-sensitive
2. **URL encoding** — Spaces become underscores in wiki URLs
3. **Network issues** — Check internet connectivity

### Slow performance

- Increase `RAG_CACHE_TTL` to cache pages longer
- Pre-write lore in `field_lore_context` on taxonomy terms (avoids live fetches)
- Enable Milvus for semantic pre-selection (avoids scoring all fetched pages)
- Reduce `RAG_SEARCH_DEPTH` to limit pages fetched per request

## Performance Considerations

- **Cache hit** (Drupal): Negligible — JSON:API read from local DB
- **Cache miss** (live fetch): 2-5 seconds per page
- **Milvus lookup**: ~50ms per query for semantic context selection
- **Batch embedding**: `AIClient.embed(list_of_texts)` indexes a full
  collection in one API call instead of N calls

## Best Practices

1. **Pre-fill `field_lore_context`** on taxonomy terms — fastest, most reliable
2. **Use `field_source_url`** for auto-fetch when pre-writing is impractical
3. **Pre-cache session locations** before play with `--reindex`
4. **Use full proper names** in story prompts ("Whitestone in Tal'Dorei")
5. **Homebrew wikis** — Create a Fandom/MediaWiki, set `RAG_WIKI_BASE_URL`

## Privacy & Git

### What's Git-Ignored

- `.rag_cache/` (legacy local cache directory, no longer used)
- `*.rag.json` and `rag_*.db`

Wiki cache content now lives in Drupal — it is not committed to the Python
repository.

---

**Questions or issues?** Check the troubleshooting section above or file an
issue in the repository.
