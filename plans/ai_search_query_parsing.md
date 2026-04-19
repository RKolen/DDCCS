# AI-Powered Search Query Parsing

## Status: Pending

## Problem

Milvus performs whole-document vector similarity search. Every character gets
compressed into a single embedding vector covering personality, backstory,
bonds, flaws, abilities, and equipment. A search for "find character who has a
backpack" places "backpack" as one word against hundreds — the signal is
indistinguishable from noise. Characters with no equipment at all score nearly
the same as Alina, who is the only character actually carrying a Backpack.

Milvus is the right tool for narrative queries ("brooding ranger with a dark
past"). Solr is the right tool for keyword/exact-text queries ("Fireball spell",
"cold damage"). EntityQuery is the right tool for structured attribute lookups
("has a Backpack", "is a Wizard class"). The solution is to intercept every
query with an LLM (Ollama is already running), decompose it into structured
filters, the appropriate backend(s) to invoke, and a semantic/keyword remainder.

---

## Architecture

```mermaid
User query: "find character who has a backpack"
          |
          v
  [Ollama — query decomposition + backend routing]
          |
          v
  {
    "backends": ["entity_query", "milvus"],
    "entity_types": ["character"],
    "filters": {
      "equipment": ["Backpack"],
      "species": [],
      "class": [],
      "campaign": []
    },
    "semantic_query": "adventurer character",   <- Milvus
    "keyword_query":  ""                        <- Solr (empty here)
  }
          |
     _____|___________
    |        |        |
    v        v        v
EntityQuery  Milvus  Solr
(exact attr) (semantic) (keyword)
    |        |        |
    v        v        v
 [nid set] [scored] [scored]
          |
          v
  [Merge + rank]
    1. EntityQuery nids  → relevance = 1.0, match_type = "exact"
    2. Solr results       → relevance = BM25 score (normalised), match_type = "keyword"
    3. Milvus results     → relevance = cosine score, match_type = "semantic"
    Deduplicate by nid (first occurrence wins — higher-confidence source)
    Slice to requested limit
          |
          v
  JSON response to Gatsby
```

---

## Backend routing rules (taught to the LLM via examples)

| Query | Backends | Reasoning |
| ----- | -------- | --------- |
| "find character who has a backpack" | entity_query + milvus | Attribute filter + narrative context |
| "brooding ranger with a dark past" | milvus | Pure narrative/semantic |
| "Fireball spell" | solr | Exact name lookup |
| "list all Wizards" | entity_query | Pure attribute, no narrative |
| "spells that deal cold damage" | solr + milvus | Keyword "cold damage" + semantic intent |
| "Elvish wizard who carries a torch and has a tragic past" | entity_query + milvus | Attribute filters + narrative |
| "NPCs in the Silverpine campaign" | entity_query | Structured filter only |
| "characters similar to Aragorn" | milvus | Similarity/narrative only |

The LLM should never route to a backend unnecessarily — Milvus embedding
generation has latency cost and should be skipped for pure keyword or attribute
queries.

---

## Components

### 1. Ollama query decomposition service

**File:** `drupal-cms/web/modules/custom/dnd_search/src/Service/QueryDecomposer.php`

Sends the raw user query to Ollama and returns a structured decomposition.

Prompt template (system):

```text
You are a D&D database query parser. Given a natural language search query,
extract structured filters, choose which search backends to use, and produce
search strings for each active backend.

Available backends:
- "entity_query": exact structured attribute matching (equipment carried,
  species/race, class, campaign). Use when the query references specific
  attributes an entity must have.
- "milvus": semantic/vector search for narrative intent, personality,
  backstory, vibe, similarity. Use when the query describes a character
  concept, feeling, or asks for similarity.
- "solr": full-text keyword search. Use when the query contains specific
  names, game terms, or exact phrases that should match text literally
  (spell names, ability names, item names used as search terms not filters).

Return ONLY valid JSON in this exact shape — no prose, no markdown:
{
  "backends": [],           // non-empty subset of: entity_query, milvus, solr
  "entity_types": [],       // subset of: character, npc, spell, item, feat, monster — empty means all
  "filters": {
    "equipment": [],        // item names the entity must carry
    "species": [],          // species/race names
    "class": [],            // D&D class names (Wizard, Fighter, etc.)
    "campaign": []          // campaign names
  },
  "semantic_query": "",     // narrative intent for Milvus — empty string if milvus not in backends
  "keyword_query": ""       // keyword string for Solr — empty string if solr not in backends
}

Examples:
  Input:  "find character who has a backpack"
  Output: {"backends":["entity_query","milvus"],"entity_types":["character"],"filters":{"equipment":["Backpack"],"species":[],"class":[],"campaign":[]},"semantic_query":"adventurer character","keyword_query":""}

  Input:  "brooding ranger with a dark past"
  Output: {"backends":["milvus"],"entity_types":[],"filters":{"equipment":[],"species":[],"class":[],"campaign":[]},"semantic_query":"brooding dark troubled past ranger","keyword_query":""}

  Input:  "Fireball spell"
  Output: {"backends":["solr"],"entity_types":["spell"],"filters":{"equipment":[],"species":[],"class":[],"campaign":[]},"semantic_query":"","keyword_query":"Fireball"}

  Input:  "list all Wizards"
  Output: {"backends":["entity_query"],"entity_types":[],"filters":{"equipment":[],"species":[],"class":["Wizard"],"campaign":[]},"semantic_query":"","keyword_query":""}

  Input:  "spells that deal cold damage"
  Output: {"backends":["solr","milvus"],"entity_types":["spell"],"filters":{"equipment":[],"species":[],"class":[],"campaign":[]},"semantic_query":"cold damage spells ice frost","keyword_query":"cold damage"}

  Input:  "Elvish wizard with a tragic past who carries a torch"
  Output: {"backends":["entity_query","milvus"],"entity_types":[],"filters":{"equipment":[],"species":["Elf"],"class":["Wizard"],"campaign":[]},"semantic_query":"tragic past mysterious dark","keyword_query":""}
```

Implementation notes:

- Call the Drupal AI module's provider API (already configured for Ollama) so
  model selection is driven by config, not hardcoded.
- Set temperature = 0 for deterministic JSON output.
- If Ollama is unavailable or returns malformed JSON, fall back gracefully:
  pass the raw query to Milvus only, return results without structured
  filtering or routing.
- Response must be parsed with `json_decode`. Validate that `backends` is a
  non-empty array and all keys are present before proceeding.

### 2. Structured filter resolver (EntityQuery)

**File:** `drupal-cms/web/modules/custom/dnd_search/src/Service/StructuredFilterResolver.php`

Takes the decomposed filters and runs Drupal EntityQuery to get a set of nids.

Resolution rules per filter type:

| Filter | Entity field | Match strategy |
| ------ | ------------ | -------------- |
| equipment | `field_equipment_items → node:title` | case-insensitive LIKE |
| species | `field_species → taxonomy_term:name` | case-insensitive LIKE |
| class | `field_class → paragraph → field_character_class → taxonomy_term:name` | case-insensitive LIKE |
| campaign | `field_campaign → node:title` | case-insensitive LIKE |

If multiple filters are present all must match (AND logic).

Returns `null` when no filters are present (EntityQuery backend skipped).

### 3. Solr resolver

**File:** `drupal-cms/web/modules/custom/dnd_search/src/Service/SolrResolver.php`

Queries the existing Solr Search API server with the `keyword_query` string.
Returns a list of `['nid' => int, 'score' => float]` pairs sorted by BM25
score.

Normalise BM25 scores to [0.0, 1.0] by dividing by the highest score in the
result set before returning, so they are comparable to cosine similarity scores
from Milvus.

The Solr Search API index to use must be read from Drupal config (not
hardcoded). If the index is unavailable or Solr is down, log a warning and
return an empty result set.

Note: a dedicated Solr index for keyword search will need to be configured
alongside the existing Milvus index. The Solr index should cover the same
content fields as Milvus. This is a separate Search API index pointing at
the existing Solr server (`search_api.server.solr` or equivalent).

### 4. Updated SearchController

**File:** `drupal-cms/web/modules/custom/dnd_search/src/Controller/SearchController.php`

Orchestration:

```text
1. Decompose query → QueryDecomposer::decompose($raw_query)
   Returns: DecomposedQuery value object (backends[], entity_types[],
            filters{}, semantic_query, keyword_query)

2. Run selected backends in parallel where possible:
   - "entity_query" in backends → StructuredFilterResolver::resolve($decomposition)
     Returns: nid[] (exact matches) or null
   - "solr" in backends AND keyword_query non-empty → SolrResolver::search($keyword_query, $limit * 5)
     Returns: [['nid'=>int, 'score'=>float], ...]
   - "milvus" in backends AND semantic_query non-empty → Milvus index query
     Returns: Search API result items

3. Merge results (priority order):
   a. EntityQuery nids  → relevance = 1.0, match_type = "exact"
   b. Solr results       → relevance = normalised BM25, match_type = "keyword"
      (skip nids already in set)
   c. Milvus results     → relevance = cosine score, match_type = "semantic"
      (skip nids already in set)

4. Apply entity_types filter post-merge (same PHP-side bundle check as today)

5. Slice to requested limit

6. Return JSON with decomposition metadata included
```

### 5. DecomposedQuery value object

**File:** `drupal-cms/web/modules/custom/dnd_search/src/ValueObject/DecomposedQuery.php`

A simple immutable value object holding the LLM output, so services pass
structured data rather than raw arrays.

### 6. Response shape

```json
{
  "query": "find character who has a backpack",
  "count": 3,
  "decomposition": {
    "backends": ["entity_query", "milvus"],
    "entity_types": ["character"],
    "filters": { "equipment": ["Backpack"], "species": [], "class": [], "campaign": [] },
    "semantic_query": "adventurer character",
    "keyword_query": ""
  },
  "results": [
    { "nid": 33, "title": "Alina Gristvale",  "type": "character", "relevance": 1.0,  "match_type": "exact" },
    { "nid": 26, "title": "Gorak Tidewalker", "type": "character", "relevance": 0.51, "match_type": "semantic" }
  ]
}
```

`match_type` values: `exact` | `keyword` | `semantic`

---

## Frontend changes (Gatsby)

### SearchResult type

Update `frontend/src/types/search.ts`:

```typescript
export interface SearchResult {
  id: string;
  nid: number;
  title: string;
  type: string;
  relevance: number;
  match_type: 'exact' | 'keyword' | 'semantic';
}

export interface SearchDecomposition {
  backends: string[];
  entity_types: string[];
  filters: {
    equipment: string[];
    species: string[];
    class: string[];
    campaign: string[];
  };
  semantic_query: string;
  keyword_query: string;
}

export interface SearchResponse {
  query: string;
  count: number;
  decomposition?: SearchDecomposition;
  results: SearchResult[];
}
```

### SearchResultItem molecule

Visual distinction by match_type:

- `exact` — gold left border, "Exact match" label
- `keyword` — silver left border, relevance % displayed
- `semantic` — existing styling, relevance % displayed

### Search page

Show a decomposition panel beneath the form when a response is present:

```text
Backends used: EntityQuery, Milvus
Filters applied: equipment = Backpack  |  type = character
Semantic query:  "adventurer character"
```

Collapsed by default, expandable — useful for debugging and power users.

---

## Implementation order

| Step | Task | File(s) |
| ---- | ---- | ------- |
| 1 | `DecomposedQuery` value object | `dnd_search/src/ValueObject/DecomposedQuery.php` |
| 2 | `QueryDecomposer` service | `dnd_search/src/Service/QueryDecomposer.php` |
| 3 | `StructuredFilterResolver` service | `dnd_search/src/Service/StructuredFilterResolver.php` |
| 4 | Configure a Solr Search API index for keyword search | Drupal UI + config export |
| 5 | `SolrResolver` service | `dnd_search/src/Service/SolrResolver.php` |
| 6 | Wire all services into `SearchController` | `dnd_search/src/Controller/SearchController.php` |
| 7 | Register services in `dnd_search.services.yml` | `dnd_search/dnd_search.services.yml` |
| 8 | Update `SearchResponse` / `SearchResult` types | `frontend/src/types/search.ts` |
| 9 | Update `SearchResultItem` molecule | `frontend/src/components/molecules/SearchResultItem.tsx` |
| 10 | Add decomposition panel to search page | `frontend/src/pages/search.tsx` |
| 11 | PHPCS + PHPStan level 6 pass on all PHP | — |
| 12 | TypeScript strict pass (`npm run type-check`) | — |

---

## Failure modes and fallbacks

| Failure | Fallback |
| ------- | -------- |
| Ollama unreachable | Skip decomposition, pass raw query to Milvus as-is |
| Ollama returns invalid JSON | Same as above |
| Ollama returns valid JSON, no filters, milvus only | Normal Milvus flow |
| EntityQuery returns 0 hits | Continue with Solr + Milvus results |
| Solr unreachable | Log warning, skip Solr results |
| Milvus unreachable | Continue with EntityQuery + Solr results |
| All three unavailable | Return 503 |

---

## Code quality requirements

- All PHP: PHPCS Drupal standard, PHPStan level 6, zero errors
- No hardcoded model names — use Drupal AI module's configured provider
- No hardcoded server/index IDs — read from Drupal config
- Services injected via constructor (dependency injection), not `\Drupal::service()`
- All public methods have PHPDoc with `@param`, `@return`, `@throws`
- `DecomposedQuery` is immutable (readonly properties, PHP 8.2+)
