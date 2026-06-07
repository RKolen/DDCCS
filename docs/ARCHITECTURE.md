# Architecture

The D&D Character Consultant System is a three-tier application. A user drives
everything from the **Gatsby frontend**; the **Python engine** does the heavy
lifting (AI, RAG, validation, indexing); and **Drupal CMS** is the single source
of truth where all content lives.

```text
        +--------------------------+
        |     Gatsby frontend      |
        |  (React 18 + TS, SSG)    |
        +------------+-------------+
                     |
     +---------------+----------------+----------------------+
     | 1. GraphQL    | 2. Serverless  | (browser)            |
     |    reads      |    functions   |                      |
     v               v                v                      |
+----------+   +-----------------------------+        +-------------+
|  Drupal  |<--|  frontend/src/api/*.ts      |------->|   Ollama    |
|   CMS    |   |  (Gatsby Functions)         |        | (LLM, chat) |
| (truth/  |   +--------------+--------------+        +-------------+
|   DB)    |                  | 3. sidecar HTTP
+----+-----+                  v
     ^               +-------------------+        +-------------------+
     |               |  FastAPI sidecar  |------->| Python engine     |
     | drupal_sync   |  (search/spotlight)|       | (src/, imported)  |
     | (push/build)  +-------------------+        +-------------------+
     |                                                     |
+----+-----------------------------------------------------+
|                  Python engine (src/)                    |
|  validation - RAG/Milvus - calendar - spotlight - sync   |
+----------------------------------------------------------+
```

All of Drupal, Ollama, Milvus, and Solr run as **DDEV** containers. The sidecar
and Gatsby dev server run on the host (see `start.sh`).

---

## The three tiers

### 1. Gatsby frontend (`frontend/`)

Static-site generator + dev server (React 18, TypeScript 6). Reads content from
Drupal at build/dev time via `gatsby-source-graphql` and renders character,
story, item, monster, NPC, party, and search pages. It also ships **Gatsby
serverless functions** (`frontend/src/api/`) that handle every write and every
live-AI call, so the user never logs into Drupal directly.

See [frontend/README.md](../frontend/README.md) for the full component and page
layout.

### 2. Drupal CMS (`drupal-cms/`) — source of truth

Headless Drupal holds every content entity (characters, stories, items,
monsters, spells, sessions) and exposes them over GraphQL via
`graphql_compose`. **Drupal is authoritative for all field names and GraphQL
type names** — never guess them.

See [docs/DRUPAL.md](DRUPAL.md) for content types and GraphQL exposure, and
[drupal-cms/AGENTS.md](../drupal-cms/AGENTS.md) for DDEV/PHP rules.

### 3. Python engine (`src/`)

The original system, now repositioned as a reusable engine. It powers:

- **Validation** of all JSON data (`src/validation/`).
- **RAG + semantic search** over a Milvus vector index (`src/ai/`).
- **Drupal sync** — pushing engine-side content into Drupal
  (`src/integration/drupal_sync.py`).
- **The sidecar** FastAPI service (`src/sidecar/`).
- **Spotlight** scoring, **calendar**, **timeline**, **character arc**, and
  more (see [src/README.md](../src/README.md)).

> The interactive Python CLI (`dnd_consultant.py`) is the **legacy `v1.0.0`
> path** and is deprecated. The engine changed enough that it likely no longer
> runs end to end. New work targets the frontend.

---

## How the frontend reaches the backend

The frontend uses three distinct channels.

### Channel 1 — GraphQL reads (Drupal)

`gatsby-source-graphql` stitches Drupal's `graphql_compose` schema into Gatsby
under the `drupal` field. Page queries in `frontend/src/pages/` and
`frontend/src/templates/` read all content this way. The endpoint is
`${DRUPAL_BASE_URL}/graphql` (configured in `frontend/gatsby-config.ts`), **not**
the Gatsby dev server at `localhost:$GATSBY_PORT`, whose `___graphql` explorer is
only a local IDE over the stitched schema.

### Channel 2 — Gatsby serverless functions (`frontend/src/api/`)

Each `.ts` file under `frontend/src/api/` is a Gatsby Function (an HTTP endpoint
served by the dev server / build). They handle writes and live AI:

| Function | Method | Talks to | Purpose |
| -------- | ------ | -------- | ------- |
| `campaigns.ts` | POST | Drupal (`createCampaign` mutation) | Create a campaign term |
| `campaign-party.ts` | POST | Drupal (`addCharacterToCampaign`) | Add a character to a campaign |
| `create-story.ts` | POST | Drupal (`createStory` mutation) | Persist a finished story |
| `update-character.ts` | POST | Drupal (`updateCharacter` mutation) | PATCH optional character fields |
| `generate-story.ts` | POST | Ollama-compatible endpoint | Stream an AI-generated story (SSE) |
| `spotlight.ts` | POST | Sidecar | Get spotlight scores for a party |

Drupal mutations come from custom GraphQL resolvers in the Drupal layer. The AI
call streams directly from `AI_CREATIVE_BASE_URL` (an Ollama-compatible
`/chat/completions` endpoint).

### Channel 3 — FastAPI sidecar (`src/sidecar/`, `$SIDECAR_PORT`)

A small Python service that imports the engine in-process. It normalises search
queries and computes spotlight scores. Routes:

- `GET /health`
- `POST /search/parse-query` — natural-language query normalisation
- `POST /eval/spotlight` — spotlight scoring via `SpotlightEngine`

See [src/sidecar/README.md](../src/sidecar/README.md).

### Engine to Drupal — `drupal_sync`

The engine writes into Drupal through `src/integration/drupal_sync.py`:
`push_character`, `push_story`, `push_item`, `push_monster`, and
`trigger_gatsby_build`. This is the bulk/seed path; per-action user edits go
through the Gatsby serverless functions above.

---

## Capability map (CLI feature -> where it lives now)

Everything the legacy CLI did is now reachable from the frontend, backed by the
engine and Drupal.

| Capability | Frontend entry | Backend |
| ---------- | -------------- | ------- |
| Browse characters / NPCs | `pages/characters.tsx`, `pages/npcs.tsx` | Drupal GraphQL |
| Character sheet | `templates/character.tsx` | Drupal GraphQL |
| Edit character (optional fields) | character edit screen | `api/update-character.ts` -> Drupal |
| Create / AI-generate a story | story forge screens | `api/generate-story.ts` (AI), `api/create-story.ts` (save) |
| Read stories | `pages/stories.tsx`, `templates/story.tsx`, `pages/campaign-reader.tsx` | Drupal GraphQL |
| Items / monsters / spells | `pages/items.tsx`, `pages/monsters.tsx`, `templates/*` | Drupal GraphQL |
| Manage party / campaigns | `pages/party.tsx` | `api/campaigns.ts`, `api/campaign-party.ts` -> Drupal |
| Search | `pages/search.tsx` | sidecar `/search/parse-query` + Milvus |
| Spotlight scoring | console screens | `api/spotlight.ts` -> sidecar `/eval/spotlight` |
| NPC profile validation | NPC validator screen | Drupal GraphQL + engine |
| RAG / semantic retrieval | implicit in AI flows | `src/ai/` + Milvus |

---

## Runtime services and ports

Started by `start.sh` (values are `.env`-driven; defaults shown):

```bash
./start.sh --no-cli     # bring up Drupal + sidecar + Gatsby (no legacy CLI)
```

---

## Source-of-truth rules

- **Drupal owns field and GraphQL type names.** Verify against
  `drupal-cms/config/sync/field.field.node.<bundle>.<field>.yml` or by
  introspecting `${DRUPAL_BASE_URL}/graphql`. Never guess.
- **NPCs are character nodes**, distinguished by `field_character_type` — there
  is no separate NPC bundle. (A legacy `nodeNpcs` GraphQL type is deprecated.)
- After changing Drupal config, run
  `ddev drush config:import -y && ddev drush cache:rebuild`, then `npm run clean`
  in `frontend/`.

Full detail: [docs/DRUPAL.md](DRUPAL.md) and
[drupal-cms/AGENTS.md](../drupal-cms/AGENTS.md).
